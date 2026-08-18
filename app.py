# Monkey patching for gevent must be done before importing socket/flask modules
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

from flask import Flask, render_template
from flask_socketio import join_room, leave_room

from config import Config
from database import db
from home.home import home_bp
from host.host import host_bp
from models import Player, Room
from player.player import player_bp
from websock import socketio

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

with app.app_context():
    db.create_all()
    # Ensure newly added columns exist in existing sqlite db
    with db.engine.connect() as conn:
        for col, col_type, default in [
            ("phase", "VARCHAR(32)", "'day'"),
            ("day_number", "INTEGER", "1"),
            ("custom_roles", "JSON", "'[]'"),
            ("started_at", "DATETIME", "NULL")
        ]:
            try:
                conn.execute(db.text(f"ALTER TABLE rooms ADD COLUMN {col} {col_type} DEFAULT {default}"))
                conn.commit()
            except Exception:
                pass
        for col, col_type, default in [
            ("role_info", "JSON", "'{}'")
        ]:
            try:
                conn.execute(db.text(f"ALTER TABLE players ADD COLUMN {col} {col_type} DEFAULT {default}"))
                conn.commit()
            except Exception:
                pass


app.register_blueprint(home_bp)
app.register_blueprint(host_bp)
app.register_blueprint(player_bp)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# In-memory Live Voting Sessions: room_code -> { "candidates": [...], "votes": { voter_id: target_id }, "open": bool }
active_voting_sessions = {}
# In-memory Live Night Actions: room_code -> { "mafia_target": target_id, "votes": { voter_id: target_id } }
active_night_actions = {}


@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("mafia_select_target")
def handle_mafia_select_target(data):
    room = str(data.get("room", ""))
    voter_id = data.get("voter_id")
    target_id = data.get("target_id")
    if not room:
        return

    if voter_id is not None:
        try:
            voter_id = int(voter_id)
        except (ValueError, TypeError):
            pass

    if target_id is not None:
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            pass

    if room not in active_night_actions:
        active_night_actions[room] = {"mafia_target": None, "don_target": None, "votes": {}}

    voter = db.session.get(Player, voter_id) if voter_id else None
    room_players = Player.query.filter_by(room_code=room, is_alive=True).all()
    living_don = next((p for p in room_players if (p.role or "").lower() == "don"), None)

    active_night_actions[room]["votes"][voter_id] = target_id

    is_don_decision = False
    if living_don:
        if voter and voter.id == living_don.id:
            # Don makes the final, authoritative choice
            active_night_actions[room]["don_target"] = target_id
            active_night_actions[room]["mafia_target"] = target_id
            is_don_decision = True
        else:
            # Regular mafia voted; if Don already voted, Don's choice overrides
            if active_night_actions[room].get("don_target"):
                target_id = active_night_actions[room]["don_target"]
                is_don_decision = True
            else:
                active_night_actions[room]["mafia_target"] = target_id
                is_don_decision = False
    else:
        active_night_actions[room]["mafia_target"] = target_id
        is_don_decision = False

    final_target_id = active_night_actions[room]["mafia_target"]
    target_name = None
    if final_target_id:
        p = db.session.get(Player, final_target_id)
        if p:
            target_name = p.name

    socketio.emit(
        "mafia_target_updated",
        {
            "target_id": final_target_id,
            "target_name": target_name,
            "voter_id": voter_id,
            "voter_name": voter.name if voter else "",
            "is_don_decision": is_don_decision,
            "has_living_don": bool(living_don),
            "don_id": living_don.id if living_don else None
        },
        room=room
    )


@socketio.on("join_room")
def handle_join_room(data):
    room = str(data.get("room", ""))
    if room:
        join_room(room)


@socketio.on("leave_room")
def handle_leave_room(data):
    room = str(data.get("room", ""))
    if room:
        leave_room(room)


@socketio.on("start_voting")
def handle_start_voting(data):
    room = str(data.get("room", ""))
    candidates = data.get("candidates", [])
    duration = int(data.get("duration", 30))
    if room:
        active_voting_sessions[room] = {
            "candidates": candidates,
            "votes": {},
            "open": True
        }
        socketio.emit(
            "voting_started",
            {"candidates": candidates, "duration": duration},
            room=room
        )


@socketio.on("submit_vote")
def handle_submit_vote(data):
    room = str(data.get("room", ""))
    voter_id = data.get("voter_id")
    target_id = data.get("target_id")
    
    # Self-voting is not allowed in Mafia rules
    if voter_id and target_id and voter_id == target_id:
        return

    if room and room in active_voting_sessions and active_voting_sessions[room]["open"]:
        active_voting_sessions[room]["votes"][voter_id] = target_id
        
        # Build live tally
        tally = {c["id"]: 0 for c in active_voting_sessions[room]["candidates"]}
        tally[0] = 0  # Abstain
        for t_id in active_voting_sessions[room]["votes"].values():
            if t_id is not None:
                tally[t_id] = tally.get(t_id, 0) + 1

        socketio.emit(
            "vote_update",
            {
                "tally": tally,
                "voters_count": len(active_voting_sessions[room]["votes"])
            },
            room=room
        )


@socketio.on("close_voting")
def handle_close_voting(data):
    room = str(data.get("room", ""))
    if room and room in active_voting_sessions:
        active_voting_sessions[room]["open"] = False
        votes = active_voting_sessions[room]["votes"]
        candidates = active_voting_sessions[room]["candidates"]
        
        tally = {c["id"]: 0 for c in candidates}
        tally[0] = 0
        for t_id in votes.values():
            if t_id is not None:
                tally[t_id] = tally.get(t_id, 0) + 1

        cand_tally = {c["id"]: tally[c["id"]] for c in candidates}
        if not cand_tally or max(cand_tally.values(), default=0) == 0:
            winner_id = None
            winner_name = None
            max_votes = 0
            is_tie = True
        else:
            max_votes = max(cand_tally.values())
            top_cands = [cid for cid, count in cand_tally.items() if count == max_votes]
            if len(top_cands) == 1:
                winner_id = top_cands[0]
                winner_obj = next((c for c in candidates if c["id"] == winner_id), None)
                winner_name = winner_obj["name"] if winner_obj else None
                is_tie = False
            else:
                winner_id = None
                winner_name = None
                is_tie = True

        socketio.emit(
            "voting_ended",
            {
                "winner_id": winner_id,
                "winner_name": winner_name,
                "max_votes": max_votes,
                "is_tie": is_tie,
                "tally": tally
            },
            room=room
        )


if __name__ == "__main__":
    print("Starting Mafia Game on http://0.0.0.0:8000 ...")
    socketio.run(app, host="0.0.0.0", port=8000, debug=Config.DEBUG, use_reloader=False)

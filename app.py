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
# In-memory live night actions. Singular target fields are kept for simple
# consumers, while per-actor maps support games with multiple Doctors,
# Sheriffs, or Maniacs.
active_night_actions = {}


def create_night_action_state(previous_doctor_targets=None):
    return {
        "mafia_target": None,
        "don_target": None,
        "doctor_target": None,
        "sheriff_target": None,
        "maniac_target": None,
        "don_check_target": None,
        "votes": {},
        "doctor_targets": {},
        "sheriff_targets": {},
        "maniac_targets": {},
        "don_check_targets": {},
        "previous_doctor_targets": dict(previous_doctor_targets or {})
    }


def get_night_action_state(room_code):
    state = active_night_actions.setdefault(room_code, create_night_action_state())
    defaults = create_night_action_state(state.get("previous_doctor_targets"))
    for key, value in defaults.items():
        state.setdefault(key, value)
    return state


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _role_key(player):
    return (player.role or "").strip().lower() if player else ""


def _is_mafia_member(player):
    if not player:
        return False
    team = (player.role_info or {}).get("team", "") if isinstance(player.role_info, dict) else ""
    return team == "mafia" or _role_key(player) in ("mafia", "don")


def _night_context(data, role_check, allow_self=False):
    room_code = str(data.get("room", "")).strip()
    actor_id = _as_int(data.get("voter_id", data.get("player_id")))
    target_id = _as_int(data.get("target_id"))
    if not room_code or actor_id is None or target_id is None:
        return None, {"success": False, "error_key": "invalid_night_action"}

    room = Room.query.filter_by(host_code=room_code).first()
    if not room or room.status != "started" or room.phase != "night":
        return None, {"success": False, "error_key": "night_action_wrong_phase"}

    actor = Player.query.filter_by(id=actor_id, room_code=room_code, is_alive=True).first()
    target = Player.query.filter_by(id=target_id, room_code=room_code, is_alive=True).first()
    if not actor or not role_check(actor):
        return None, {"success": False, "error_key": "night_action_forbidden"}
    if not target:
        return None, {"success": False, "error_key": "night_action_invalid_target"}
    if not allow_self and actor.id == target.id:
        return None, {"success": False, "error_key": "night_action_self_forbidden"}

    return (room_code, actor, target, get_night_action_state(room_code)), None


def get_night_action_summary(room_code):
    state = get_night_action_state(room_code)
    living = Player.query.filter_by(room_code=room_code, is_alive=True).all()
    mafia_members = [p for p in living if _is_mafia_member(p)]
    dons = [p for p in living if _role_key(p) == "don"]
    doctors = [p for p in living if _role_key(p) == "doctor"]
    sheriffs = [p for p in living if _role_key(p) == "sheriff"]
    maniacs = [p for p in living if _role_key(p) == "maniac"]

    mafia_done = bool(state.get("don_target")) if dons else bool(state.get("mafia_target"))
    actions = {
        "mafia": {
            "required": 1 if mafia_members else 0,
            "completed": 1 if mafia_members and mafia_done else 0
        },
        "doctor": {
            "required": len(doctors),
            "completed": sum(1 for p in doctors if p.id in state["doctor_targets"])
        },
        "sheriff": {
            "required": len(sheriffs),
            "completed": sum(1 for p in sheriffs if p.id in state["sheriff_targets"])
        },
        "maniac": {
            "required": len(maniacs),
            "completed": sum(1 for p in maniacs if p.id in state["maniac_targets"])
        },
        "don_check": {
            "required": len(dons),
            "completed": sum(1 for p in dons if p.id in state["don_check_targets"])
        }
    }
    required_total = sum(item["required"] for item in actions.values())
    completed_total = sum(min(item["completed"], item["required"]) for item in actions.values())
    return {
        "actions": actions,
        "required_total": required_total,
        "completed_total": completed_total,
        "all_complete": completed_total >= required_total,
        "pending_roles": [key for key, item in actions.items() if item["completed"] < item["required"]]
    }


def get_night_monitor_payload(room_code):
    state = get_night_action_state(room_code)
    player_by_id = {
        player.id: player
        for player in Player.query.filter_by(room_code=room_code).all()
    }

    def targets_for(ids):
        result = []
        for target_id in dict.fromkeys(target_id for target_id in ids if target_id):
            player = player_by_id.get(target_id)
            if player:
                result.append({"id": player.id, "name": player.name})
        return result

    return {
        "targets": {
            "mafia": targets_for([state.get("mafia_target")]),
            "doctor": targets_for(state["doctor_targets"].values()),
            "sheriff": targets_for(state["sheriff_targets"].values()),
            "maniac": targets_for(state["maniac_targets"].values()),
            "don_check": targets_for(state["don_check_targets"].values())
        },
        "summary": get_night_action_summary(room_code)
    }


def _emit_night_action_update(room_code, action, actor, target):
    payload = {
        "action": action,
        "actor_id": actor.id,
        "actor_name": actor.name,
        "target_id": target.id,
        "target_name": target.name,
        **get_night_monitor_payload(room_code)
    }
    # Night choices are moderator-only information. Investigation results are
    # returned privately through the Socket.IO acknowledgement.
    socketio.emit("night_action_updated", payload, room=f"host:{room_code}")
    return payload


@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("mafia_select_target")
def handle_mafia_select_target(data):
    context, error = _night_context(data, _is_mafia_member)
    if error:
        return error
    room, voter, target, state = context
    if _is_mafia_member(target):
        return {"success": False, "error_key": "mafia_friendly_fire_forbidden"}

    room_players = Player.query.filter_by(room_code=room, is_alive=True).all()
    living_don = next((p for p in room_players if (p.role or "").lower() == "don"), None)
    state["votes"][voter.id] = target.id

    is_don_decision = False
    if living_don:
        if voter and voter.id == living_don.id:
            # Don makes the final, authoritative choice
            state["don_target"] = target.id
            state["mafia_target"] = target.id
            is_don_decision = True
        else:
            # Regular mafia voted; if Don already voted, Don's choice overrides
            if state.get("don_target"):
                is_don_decision = True
            else:
                state["mafia_target"] = target.id
                is_don_decision = False
    else:
        state["mafia_target"] = target.id
        is_don_decision = False

    final_target_id = state["mafia_target"]
    target_name = None
    if final_target_id:
        p = db.session.get(Player, final_target_id)
        if p:
            target_name = p.name

    mafia_payload = {
            "target_id": final_target_id,
            "target_name": target_name,
            "voter_id": voter.id,
            "voter_name": voter.name if voter else "",
            "is_don_decision": is_don_decision,
            "has_living_don": bool(living_don),
            "don_id": living_don.id if living_don else None
        }
    socketio.emit("mafia_target_updated", mafia_payload, room=f"mafia:{room}")
    socketio.emit("mafia_target_updated", mafia_payload, room=f"host:{room}")
    _emit_night_action_update(room, "mafia", voter, db.session.get(Player, final_target_id))
    return {"success": True, "target_id": final_target_id, "is_don_decision": is_don_decision}


@socketio.on("doctor_select_target")
def handle_doctor_select_target(data):
    context, error = _night_context(data, lambda p: _role_key(p) == "doctor", allow_self=True)
    if error:
        return error
    room, doctor, target, state = context
    previous_target = state["previous_doctor_targets"].get(doctor.id)
    if target.id == doctor.id and previous_target == doctor.id:
        return {"success": False, "error_key": "doctor_self_consecutive_error"}

    state["doctor_target"] = target.id
    state["doctor_targets"][doctor.id] = target.id
    _emit_night_action_update(room, "doctor", doctor, target)
    return {"success": True, "target_id": target.id, "target_name": target.name}


@socketio.on("sheriff_check_target")
def handle_sheriff_check_target(data):
    context, error = _night_context(data, lambda p: _role_key(p) == "sheriff")
    if error:
        return error
    room, sheriff, target, state = context
    locked_target = state["sheriff_targets"].get(sheriff.id)
    if locked_target and locked_target != target.id:
        return {"success": False, "error_key": "night_investigation_locked"}

    state["sheriff_target"] = target.id
    state["sheriff_targets"][sheriff.id] = target.id
    is_mafia = _is_mafia_member(target)
    _emit_night_action_update(room, "sheriff", sheriff, target)
    return {
        "success": True,
        "target_id": target.id,
        "target_name": target.name,
        "is_mafia": is_mafia
    }


@socketio.on("maniac_select_target")
def handle_maniac_select_target(data):
    context, error = _night_context(data, lambda p: _role_key(p) == "maniac")
    if error:
        return error
    room, maniac, target, state = context
    state["maniac_target"] = target.id
    state["maniac_targets"][maniac.id] = target.id
    _emit_night_action_update(room, "maniac", maniac, target)
    return {"success": True, "target_id": target.id, "target_name": target.name}


@socketio.on("don_check_sheriff")
def handle_don_check_sheriff(data):
    context, error = _night_context(data, lambda p: _role_key(p) == "don")
    if error:
        return error
    room, don, target, state = context
    locked_target = state["don_check_targets"].get(don.id)
    if locked_target and locked_target != target.id:
        return {"success": False, "error_key": "night_investigation_locked"}

    state["don_check_target"] = target.id
    state["don_check_targets"][don.id] = target.id
    is_sheriff = _role_key(target) == "sheriff"
    _emit_night_action_update(room, "don_check", don, target)
    return {
        "success": True,
        "target_id": target.id,
        "target_name": target.name,
        "is_sheriff": is_sheriff
    }


@socketio.on("get_night_action_state")
def handle_get_night_action_state(data):
    room = str(data.get("room", "")).strip()
    player_id = _as_int(data.get("player_id"))
    player = Player.query.filter_by(id=player_id, room_code=room, is_alive=True).first()
    room_obj = Room.query.filter_by(host_code=room, status="started", phase="night").first()
    if not player or not room_obj:
        return {"success": False, "error_key": "night_action_wrong_phase"}

    state = get_night_action_state(room)
    role = _role_key(player)
    selected_target_id = None
    result = None
    if role == "doctor":
        selected_target_id = state["doctor_targets"].get(player.id)
    elif role == "sheriff":
        selected_target_id = state["sheriff_targets"].get(player.id)
        target = db.session.get(Player, selected_target_id) if selected_target_id else None
        if target:
            result = {"target_name": target.name, "is_mafia": _is_mafia_member(target)}
    elif role == "maniac":
        selected_target_id = state["maniac_targets"].get(player.id)
    elif role == "don":
        selected_target_id = state["don_check_targets"].get(player.id)
        target = db.session.get(Player, selected_target_id) if selected_target_id else None
        if target:
            result = {"target_name": target.name, "is_sheriff": _role_key(target) == "sheriff"}

    return {
        "success": True,
        "selected_target_id": selected_target_id,
        "mafia_target_id": state.get("mafia_target") if _is_mafia_member(player) else None,
        "doctor_self_blocked": role == "doctor" and state["previous_doctor_targets"].get(player.id) == player.id,
        "result": result
    }


@socketio.on("join_room")
def handle_join_room(data):
    room = str(data.get("room", ""))
    if room:
        join_room(room)
        if data.get("client_type") == "host":
            join_room(f"host:{room}")
        player_id = _as_int(data.get("player_id"))
        if player_id is not None:
            player = Player.query.filter_by(id=player_id, room_code=room).first()
            if player:
                join_room(f"player:{player.id}")
                if _is_mafia_member(player):
                    join_room(f"mafia:{room}")


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

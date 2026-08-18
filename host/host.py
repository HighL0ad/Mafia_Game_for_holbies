from datetime import datetime
import uuid
from flask import jsonify, redirect, render_template, request, url_for
from flask.blueprints import Blueprint

from database import db
from models import Player, Room, get_default_roles_config
from utils.role import assign_roles
from websock import socketio

host_bp = Blueprint(
    "host_bp", __name__, url_prefix="/host", template_folder="templates"
)


def _is_mafia_player(player):
    role = (player.role or "").strip().lower()
    role_info = player.role_info if isinstance(player.role_info, dict) else {}
    return role in ("mafia", "don") or role_info.get("team") == "mafia"


def serialize_public_players(players):
    return [
        {"id": player.id, "name": player.name, "is_alive": player.is_alive}
        for player in players
    ]


def serialize_player_view(players, viewer):
    if not viewer.is_alive:
        return [player.to_dict() for player in players]

    viewer_is_mafia = _is_mafia_player(viewer)
    result = []
    for player in players:
        item = {"id": player.id, "name": player.name, "is_alive": player.is_alive}
        if player.id == viewer.id or (viewer_is_mafia and _is_mafia_player(player)):
            item["role"] = player.role
            item["role_info"] = player.role_info or {}
        result.append(item)
    return result


def emit_private_player_rosters(players):
    for viewer in players:
        socketio.emit(
            "player_roster_updated",
            {"players": serialize_player_view(players, viewer)},
            room=f"player:{viewer.id}",
        )


def calculate_game_stats(players):
    mafia_count = 0
    town_count = 0
    maniac_count = 0
    alive_players = [p for p in players if p.is_alive]

    for p in alive_players:
        role = (p.role or "").lower()
        team = ""
        if hasattr(p, "role_info") and isinstance(p.role_info, dict):
            team = p.role_info.get("team", "")

        if team == "mafia" or role in ("mafia", "don"):
            mafia_count += 1
        elif team == "neutral" or role == "maniac":
            maniac_count += 1
        else:
            town_count += 1

    winner = None
    if len(alive_players) > 0:
        if mafia_count == 0 and maniac_count == 0:
            winner = "town"
        elif mafia_count >= (town_count + maniac_count) and mafia_count > 0:
            winner = "mafia"
        elif maniac_count == 1 and mafia_count == 0 and town_count <= 1:
            winner = "maniac"

    return {
        "alive_total": len(alive_players),
        "alive_mafia": mafia_count,
        "alive_town": town_count,
        "alive_maniac": maniac_count,
        "winner": winner
    }


def check_and_trigger_game_end(room, stats):
    if not stats or not stats.get("winner"):
        return False
    winner = stats["winner"]
    started = room.started_at or room.created_at or datetime.utcnow()
    duration_seconds = max(0, int((datetime.utcnow() - started).total_seconds()))
    stats["duration_seconds"] = duration_seconds

    fresh_players = Player.query.filter_by(room_code=room.host_code).all()
    roster = [{
        "id": p.id,
        "name": p.name,
        "role": p.role,
        "role_info": p.role_info or {},
        "is_alive": p.is_alive
    } for p in fresh_players]

    room.status = "finished"
    db.session.commit()

    from app import active_night_actions, active_voting_sessions
    active_night_actions.pop(room.host_code, None)
    active_voting_sessions.pop(room.host_code, None)

    socketio.emit(
        "game_ended",
        {
            "winner": winner,
            "stats": stats,
            "duration_seconds": duration_seconds,
            "roster": roster
        },
        room=room.host_code
    )
    return True


@host_bp.route("/<code>")
def host(code: str):
    room = Room.query.filter_by(host_code=code).first()
    if not room:
        return redirect(url_for("home_bp.index"))

    player_count = len(room.players)

    roles_config = room.roles_config or {}
    if not roles_config:
        roles_config = get_default_roles_config(player_count)
        room.roles_config = roles_config
        db.session.commit()
    else:
        total_special = sum(int(v) for k, v in roles_config.items() if k != "villager")
        roles_config["villager"] = max(0, player_count - total_special)
        room.roles_config = roles_config
        db.session.commit()

    total_special = sum(int(v) for k, v in roles_config.items() if k != "villager")
    stats = calculate_game_stats(room.players)
    from app import get_night_monitor_payload
    night_monitor = get_night_monitor_payload(code)

    return render_template(
        "host.html",
        code=code,
        room=room,
        players=room.players,
        status=room.status,
        phase=room.phase or "day",
        day_number=room.day_number or 1,
        player_count=player_count,
        roles_config=roles_config,
        custom_roles=room.custom_roles or [],
        total_roles=total_special,
        stats=stats,
        night_monitor=night_monitor
    )


@host_bp.post("/create-custom-role/<code>")
def create_custom_role(code: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
    data = request.get_json(force=True) if request.is_json else request.form.to_dict()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Role name is required"}), 400

    role_id = f"custom_{uuid.uuid4().hex[:8]}"
    new_role = {
        "id": role_id,
        "name": name,
        "team": data.get("team", "town"),
        "icon": data.get("icon", "fa-mask"),
        "color": data.get("color", "#3a86ff"),
        "desc": (data.get("desc") or "").strip(),
        "count": 0
    }

    current_custom = list(room.custom_roles or [])
    current_custom.append(new_role)
    room.custom_roles = current_custom

    cfg = dict(room.roles_config or {})
    cfg[role_id] = 0
    room.roles_config = cfg

    db.session.commit()
    return jsonify({"success": True, "role": new_role, "roles_config": room.roles_config})


@host_bp.post("/delete-custom-role/<code>/<role_id>")
def delete_custom_role(code: str, role_id: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
    current_custom = [r for r in (room.custom_roles or []) if r.get("id") != role_id]
    room.custom_roles = current_custom

    cfg = dict(room.roles_config or {})
    if role_id in cfg:
        del cfg[role_id]
    room.roles_config = cfg

    db.session.commit()
    return jsonify({"success": True, "roles_config": room.roles_config})


@host_bp.post("/start-game/<code>")
def start_game(code: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
    players = room.players

    if len(players) < 3:
        return "Для начала игры необходимо минимум 3 игрока", 400

    roles_config = {
        "mafia": int(request.form.get("mafia", 0)),
        "don": int(request.form.get("don", 0)),
        "doctor": int(request.form.get("doctor", 0)),
        "sheriff": int(request.form.get("sheriff", 0)),
        "maniac": int(request.form.get("maniac", 0)),
        "kamikaze": int(request.form.get("kamikaze", 0)),
        "villager": int(request.form.get("villager", 0))
    }

    for cr in (room.custom_roles or []):
        if "id" in cr:
            roles_config[cr["id"]] = int(request.form.get(cr["id"], 0))

    total_roles = sum(roles_config.values())
    if total_roles != len(players):
        return f"Количество ролей ({total_roles}) должно равняться количеству игроков ({len(players)})", 400

    players_dict_list = [{"id": p.id, "name": p.name, "role": None} for p in players]
    assign_roles(players_dict_list, roles_config, room.custom_roles)

    for p_dict in players_dict_list:
        p = db.session.get(Player, p_dict["id"])
        if p:
            p.role = p_dict["role"]
            p.role_info = p_dict.get("role_info", {})
            p.is_alive = True

    room.status = "started"
    room.phase = "day"
    room.day_number = 1
    room.started_at = datetime.utcnow()
    room.roles_config = roles_config
    db.session.commit()

    from app import active_night_actions, active_voting_sessions, create_night_action_state
    active_night_actions[code] = create_night_action_state()
    active_voting_sessions.pop(code, None)

    public_players = serialize_public_players(room.players)
    socketio.emit(
        "update_roles",
        {
            "players": public_players,
            "status": "started",
            "phase": "day",
            "day_number": 1
        },
        room=code
    )
    for player in room.players:
        socketio.emit(
            "update_roles",
            {
                "players": serialize_player_view(room.players, player),
                "status": "started",
                "phase": "day",
                "day_number": 1,
            },
            room=f"player:{player.id}",
        )

    return redirect(url_for("host_bp.host", code=code))


@host_bp.post("/set-phase/<code>/<phase>")
def set_phase(code: str, phase: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
    if phase not in ("day", "voting", "night"):
        return jsonify({"error": "Invalid phase"}), 400

    prev_phase = room.phase
    victim_eliminated = None
    victims_eliminated = []
    players_saved = []
    from app import (
        active_night_actions,
        active_voting_sessions,
        create_night_action_state,
        get_night_action_state,
        get_night_monitor_payload,
    )

    if prev_phase == "voting" and phase != "voting":
        active_voting_sessions.pop(code, None)
        socketio.emit("voting_cancelled", {"phase": phase}, room=code)

    # Resolve all attacks simultaneously. Every Doctor protects one target;
    # duplicate attacks still produce a single casualty.
    if phase == "day" and prev_phase == "night":
        room.day_number = (room.day_number or 1) + 1
        night_data = get_night_action_state(code)
        protected_ids = set(night_data["doctor_targets"].values())
        if not protected_ids and night_data.get("doctor_target"):
            protected_ids.add(night_data["doctor_target"])

        attacks = {}
        mafia_target = night_data.get("mafia_target")
        if mafia_target:
            attacks.setdefault(mafia_target, set()).add("mafia")

        maniac_targets = set(night_data["maniac_targets"].values())
        if not maniac_targets and night_data.get("maniac_target"):
            maniac_targets.add(night_data["maniac_target"])
        for target_id in maniac_targets:
            attacks.setdefault(target_id, set()).add("maniac")

        for target_id, sources in attacks.items():
            target = Player.query.filter_by(id=target_id, room_code=code, is_alive=True).first()
            if not target:
                continue
            result = {
                "id": target.id,
                "name": target.name,
                "sources": sorted(sources),
            }
            if target.id in protected_ids:
                players_saved.append(result)
            else:
                target.is_alive = False
                victims_eliminated.append(result)

        previous_doctor_targets = dict(night_data["doctor_targets"])
        active_night_actions[code] = create_night_action_state(previous_doctor_targets)
        victim_eliminated = victims_eliminated[0] if victims_eliminated else None

    elif phase == "night" and prev_phase != "night":
        previous_targets = get_night_action_state(code).get("previous_doctor_targets", {})
        active_night_actions[code] = create_night_action_state(previous_targets)

    room.phase = phase
    db.session.commit()

    players = Player.query.filter_by(room_code=code).all()
    stats = calculate_game_stats(players)
    started = room.started_at or room.created_at or datetime.utcnow()
    duration_seconds = max(0, int((datetime.utcnow() - started).total_seconds()))
    stats["duration_seconds"] = duration_seconds

    night_result = {
        "victims": victims_eliminated,
        "saved": players_saved,
        "no_victims": phase == "day" and prev_phase == "night" and not victims_eliminated,
    } if phase == "day" and prev_phase == "night" else None
    night_monitor = get_night_monitor_payload(code) if phase == "night" else None
    public_victims = [{"id": item["id"], "name": item["name"]} for item in victims_eliminated]
    public_saved = [{"id": item["id"], "name": item["name"]} for item in players_saved]
    public_night_result = {
        "victims": public_victims,
        "saved": public_saved,
        "no_victims": night_result["no_victims"],
    } if night_result else None

    public_players = serialize_public_players(players)
    socketio.emit(
        "phase_changed",
        {
            "phase": phase,
            "day_number": room.day_number,
            "stats": stats,
            "victim_eliminated": public_victims[0] if public_victims else None,
            "victims_eliminated": public_victims,
            "players_saved": public_saved,
            "night_result": public_night_result,
            "night_monitor": night_monitor,
            "all_players": public_players
        },
        room=code
    )
    emit_private_player_rosters(players)

    if stats.get("winner"):
        check_and_trigger_game_end(room, stats)

    return jsonify({
        "success": True, 
        "phase": phase, 
        "day_number": room.day_number, 
        "victim_eliminated": victim_eliminated,
        "victims_eliminated": victims_eliminated,
        "players_saved": players_saved,
        "night_result": night_result,
        "night_monitor": night_monitor,
        "stats": stats
    })


@host_bp.post("/toggle-player-status/<code>/<int:player_id>")
def toggle_player_status(code: str, player_id: int):
    room = Room.query.filter_by(host_code=code).first_or_404()
    player = Player.query.filter_by(id=player_id, room_code=code).first_or_404()

    player.is_alive = not player.is_alive
    db.session.commit()

    players = Player.query.filter_by(room_code=code).all()
    stats = calculate_game_stats(players)
    started = room.started_at or room.created_at or datetime.utcnow()
    duration_seconds = max(0, int((datetime.utcnow() - started).total_seconds()))
    stats["duration_seconds"] = duration_seconds

    public_players = serialize_public_players(players)
    socketio.emit(
        "update_player_status",
        {
            "player_id": player.id,
            "player_name": player.name,
            "is_alive": player.is_alive,
            "stats": stats,
            "all_players": public_players
        },
        room=code
    )
    emit_private_player_rosters(players)

    if stats.get("winner"):
        check_and_trigger_game_end(room, stats)

    return jsonify({"success": True, "player_id": player.id, "is_alive": player.is_alive, "stats": stats, "all_players": public_players})


@host_bp.post("/end-game/<code>")
def end_game(code: str):
    room = Room.query.filter_by(host_code=code).first()
    if room:
        stats = calculate_game_stats(room.players)
        started = room.started_at or room.created_at or datetime.utcnow()
        duration_seconds = max(0, int((datetime.utcnow() - started).total_seconds()))
        stats["duration_seconds"] = duration_seconds

        roster = []
        for p in room.players:
            roster.append({
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "role_info": p.role_info or {},
                "is_alive": p.is_alive
            })

        socketio.emit(
            "game_ended",
            {
                "winner": stats.get("winner"),
                "stats": stats,
                "roster": roster,
                "duration_seconds": duration_seconds,
                "message": "Игра завершена"
            },
            room=code
        )
        socketio.emit(
            "room_closed",
            {
                "message": "Otaq bağlandı"
            },
            room=code
        )
        db.session.delete(room)
        db.session.commit()

        from app import active_night_actions, active_voting_sessions
        active_night_actions.pop(code, None)
        active_voting_sessions.pop(code, None)

    return redirect(url_for("home_bp.index"))

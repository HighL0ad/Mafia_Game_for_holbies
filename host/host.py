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


@host_bp.route("/<code>")
def host(code: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
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
        stats=stats
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
        p = Player.query.get(p_dict["id"])
        if p:
            p.role = p_dict["role"]
            p.role_info = p_dict.get("role_info", {})
            p.is_alive = True

    room.status = "started"
    room.phase = "day"
    room.day_number = 1
    room.roles_config = roles_config
    db.session.commit()

    socketio.emit(
        "update_roles",
        {
            "players": [p.to_dict() for p in room.players],
            "status": "started",
            "phase": "day",
            "day_number": 1
        },
        room=code
    )

    return redirect(url_for("host_bp.host", code=code))


@host_bp.post("/set-phase/<code>/<phase>")
def set_phase(code: str, phase: str):
    room = Room.query.filter_by(host_code=code).first_or_404()
    if phase not in ("day", "voting", "night"):
        return jsonify({"error": "Invalid phase"}), 400

    if phase == "day" and room.phase == "night":
        room.day_number = (room.day_number or 1) + 1

    room.phase = phase
    db.session.commit()

    socketio.emit(
        "phase_changed",
        {
            "phase": phase,
            "day_number": room.day_number
        },
        room=code
    )

    return jsonify({"success": True, "phase": phase, "day_number": room.day_number})


@host_bp.post("/toggle-player-status/<code>/<int:player_id>")
def toggle_player_status(code: str, player_id: int):
    room = Room.query.filter_by(host_code=code).first_or_404()
    player = Player.query.filter_by(id=player_id, room_code=code).first_or_404()

    player.is_alive = not player.is_alive
    db.session.commit()

    stats = calculate_game_stats(room.players)

    socketio.emit(
        "update_player_status",
        {
            "player_id": player.id,
            "player_name": player.name,
            "is_alive": player.is_alive,
            "stats": stats,
            "all_players": [p.to_dict() for p in room.players]
        },
        room=code
    )

    return jsonify({"success": True, "player_id": player.id, "is_alive": player.is_alive, "stats": stats, "all_players": [p.to_dict() for p in room.players]})


@host_bp.post("/end-game/<code>")
def end_game(code: str):
    room = Room.query.filter_by(host_code=code).first()
    if room:
        socketio.emit("game_ended", {"message": "Игра завершена ведущим"}, room=code)
        db.session.delete(room)
        db.session.commit()

    return redirect(url_for("home_bp.index"))
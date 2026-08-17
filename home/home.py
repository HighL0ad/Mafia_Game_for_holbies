from flask import flash, redirect, render_template, request, url_for
from flask.blueprints import Blueprint

from database import db
from models import Player, Room, get_default_roles_config
from utils.room_code import generate_room_code
from websock import socketio

home_bp = Blueprint("home_bp", __name__, url_prefix="/", template_folder="templates")


@home_bp.route("/")
def index():
    return render_template("index.html")


@home_bp.post("/create_game")
def create_game():
    code = str(generate_room_code())
    # Ensure code uniqueness
    while Room.query.filter_by(host_code=code).first() is not None:
        code = str(generate_room_code())

    default_config = get_default_roles_config(0)
    room = Room(host_code=code, status="waiting", roles_config=default_config)
    db.session.add(room)
    db.session.commit()

    return redirect(url_for("host_bp.host", code=code))


@home_bp.post("/join_game")
def join_game():
    code = request.form.get("room-code", "").strip()
    name = request.form.get("player-name", "").strip()

    if not code or not name:
        return redirect(url_for("home_bp.index"))

    room = Room.query.filter_by(host_code=code).first()
    if not room:
        return render_template("404.html", message=f"Комната {code} не найдена"), 404

    # Look for existing player in THIS room with the same name
    player = Player.query.filter_by(name=name, room_code=code).first()
    if not player:
        player = Player(name=name, room_code=code, role=None, is_alive=True)
        db.session.add(player)
        db.session.commit()

        # Update default roles config for host if game hasn't started
        if room.status == "waiting":
            player_count = len(room.players)
            # update auto-calculated config
            cfg = room.roles_config or {}
            special_count = sum(v for k, v in cfg.items() if k != "villager")
            if not cfg or special_count == 0:
                room.roles_config = get_default_roles_config(player_count)
            else:
                cfg["villager"] = max(0, player_count - special_count)
                room.roles_config = cfg
            db.session.commit()

    players_data = [p.to_dict() for p in room.players]
    socketio.emit(
        "update_player_list",
        {"players": players_data, "player_count": len(players_data)},
        room=code
    )

    return redirect(url_for("player_bp.player", id=player.id))

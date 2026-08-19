import re
import unicodedata
from threading import Lock

from flask import redirect, render_template, request, session, url_for
from flask.blueprints import Blueprint

from database import db
from models import Player, Room, get_default_roles_config
from utils.room_code import generate_room_code
from websock import socketio

home_bp = Blueprint("home_bp", __name__, url_prefix="/", template_folder="templates")
_join_game_lock = Lock()


def clean_player_name(value):
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", normalized).strip()


def player_name_key(value):
    return clean_player_name(value).casefold()


def _as_player_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _remember_player(room_code, player_id):
    stored_players = session.get("mafia_players", {})
    remembered = dict(stored_players) if isinstance(stored_players, dict) else {}
    remembered[str(room_code)] = int(player_id)
    if len(remembered) > 20:
        remembered = dict(list(remembered.items())[-20:])
    session["mafia_players"] = remembered


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
    name = clean_player_name(request.form.get("player-name", ""))

    if not code or not name:
        return redirect(url_for("home_bp.index"))

    room = Room.query.filter_by(host_code=code).first()
    if not room:
        return render_template("404.html", message=f"Комната {code} не найдена"), 404

    with _join_game_lock:
        room_players = Player.query.filter_by(room_code=code).order_by(Player.id).all()
        requested_id = _as_player_id(request.form.get("player-id"))
        stored_players = session.get("mafia_players", {})
        if not isinstance(stored_players, dict):
            stored_players = {}
        remembered_id = _as_player_id(
            stored_players.get(code)
        )
        reconnect_ids = [player_id for player_id in (requested_id, remembered_id) if player_id]
        name_key = player_name_key(name)

        player = next(
            (
                candidate
                for candidate in room_players
                if candidate.id in reconnect_ids
                and player_name_key(candidate.name) == name_key
            ),
            None,
        )
        if player is None:
            player = next(
                (
                    candidate
                    for candidate in room_players
                    if player_name_key(candidate.name) == name_key
                ),
                None,
            )

        if player is None and room.status != "waiting":
            error_key = (
                "game_finished_join_error"
                if room.status == "finished"
                else "game_started_join_error"
            )
            return render_template(
                "index.html",
                join_error_key=error_key,
                entered_name=name,
                entered_code=code,
            ), 409

        if player is None:
            player = Player(name=name, room_code=code, role=None, is_alive=True)
            db.session.add(player)
            db.session.commit()

            player_count = len(room_players) + 1
            cfg = room.roles_config or {}
            special_count = sum(v for k, v in cfg.items() if k != "villager")
            if not cfg or special_count == 0:
                room.roles_config = get_default_roles_config(player_count)
            else:
                cfg["villager"] = max(0, player_count - special_count)
                room.roles_config = cfg
            db.session.commit()

        _remember_player(code, player.id)

    players_data = [
        {"id": room_player.id, "name": room_player.name, "is_alive": room_player.is_alive}
        for room_player in Player.query.filter_by(room_code=code).order_by(Player.id).all()
    ]
    socketio.emit(
        "update_player_list",
        {"players": players_data, "player_count": len(players_data)},
        room=f"host:{code}"
    )

    return redirect(url_for("player_bp.player", id=player.id))

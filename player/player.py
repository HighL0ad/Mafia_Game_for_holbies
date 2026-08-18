from flask import redirect, render_template, url_for
from flask.blueprints import Blueprint

from database import db
from models import Player

player_bp = Blueprint(
    "player_bp", __name__, url_prefix="/player", template_folder="templates"
)


@player_bp.route("/<int:id>")
def player(id: int):
    player_obj = db.session.get(Player, id)
    if not player_obj or not player_obj.room:
        return redirect(url_for("home_bp.index"))

    # If player is dead, they get access to spectator mode with all players' revealed roles
    all_players = [p.to_dict() for p in player_obj.room.players] if not player_obj.is_alive else []
    player_team = (player_obj.role_info or {}).get("team", "") if isinstance(player_obj.role_info, dict) else ""
    is_mafia = player_team == "mafia" or (player_obj.role or "").lower() in ("mafia", "don")
    night_players = []
    for room_player in player_obj.room.players:
        public_player = {
            "id": room_player.id,
            "name": room_player.name,
            "is_alive": room_player.is_alive,
        }
        teammate_info = room_player.role_info or {}
        teammate_is_mafia = (
            (isinstance(teammate_info, dict) and teammate_info.get("team") == "mafia")
            or (room_player.role or "").lower() in ("mafia", "don")
        )
        if is_mafia and teammate_is_mafia:
            public_player["role"] = room_player.role
            public_player["role_info"] = {"team": "mafia"}
        night_players.append(public_player)
    return render_template(
        "player.html",
        player=player_obj,
        room_code=player_obj.room_code,
        all_players=all_players,
        night_players=night_players,
        initial_phase=player_obj.room.phase or "day",
    )

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
    return render_template(
        "player.html",
        player=player_obj,
        room_code=player_obj.room_code,
        all_players=all_players
    )

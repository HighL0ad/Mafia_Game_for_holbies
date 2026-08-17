from flask import render_template
from flask.blueprints import Blueprint

from models import Player

player_bp = Blueprint(
    "player_bp", __name__, url_prefix="/player", template_folder="templates"
)


@player_bp.route("/<int:id>")
def player(id: int):
    player_obj = Player.query.get_or_404(id)
    return render_template("player.html", player=player_obj, room_code=player_obj.room_code)

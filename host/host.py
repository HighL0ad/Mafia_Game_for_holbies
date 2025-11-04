from typing import Dict

from bson import ObjectId
from flask import redirect, render_template, url_for, request
from flask.blueprints import Blueprint

from database import mongo
from utils.role import assign_roles
from websock import socketio

host_bp = Blueprint(
    "host_bp", __name__, url_prefix="/host", template_folder="templates"
)


def get_default_roles_config(num_players):
    roles_config = {
        range(1, 6): {"mafia": 1, "don": 0, "doctor": 1, "sheriff": 1, "maniac": 0, "kamikaze": 0},
        range(6, 11): {"mafia": 2, "don": 0, "doctor": 1, "sheriff": 1, "maniac": 0, "kamikaze": 0},
        range(11, 16): {"mafia": 3, "don": 1, "doctor": 1, "sheriff": 1, "maniac": 1, "kamikaze": 1},
        range(16, 21): {"mafia": 4, "don": 1, "doctor": 2, "sheriff": 1, "maniac": 1, "kamikaze": 1},
        range(21, 26): {"mafia": 5, "don": 1, "doctor": 2, "sheriff": 2, "maniac": 1, "kamikaze": 1},
        range(26, 31): {"mafia": 6, "don": 1, "doctor": 2, "sheriff": 2, "maniac": 2, "kamikaze": 1},
    }

    for player_range, config in roles_config.items():
        if num_players in player_range:
            total_special = sum(config.values())
            config["villager"] = num_players - total_special
            return config

    return {"mafia": 1, "don": 0, "doctor": 1, "sheriff": 1, "maniac": 0, "kamikaze": 0,
            "villager": max(0, num_players - 3)}


@host_bp.route("/<code>")
def host(code: str):
    context: Dict = mongo.db.rooms.find_one_or_404({"host_code": code})

    player_count = len(context["players"])

    if "roles_config" not in context:
        roles_config = get_default_roles_config(player_count)
        mongo.db.rooms.update_one(
            {"host_code": code},
            {"$set": {"roles_config": roles_config}}
        )
    else:
        roles_config = context["roles_config"]
        total_special = sum(v for k, v in roles_config.items() if k != "villager")
        roles_config["villager"] = max(0, player_count - total_special)

    total_roles = sum(v for k, v in roles_config.items() if k != "villager")

    return render_template(
        "host.html",
        code=code,
        context=context["players"],
        status=context["status"],
        player_count=player_count,
        roles_config=roles_config,
        total_roles=total_roles
    )


@host_bp.post("/start-game/<code>")
def start_game(code: str):
    room = mongo.db.rooms.find_one_or_404({"host_code": code})

    if len(room["players"]) < 6:
        return "Need at least 6 players to start the game", 400

    roles_config = {
        "mafia": int(request.form.get("mafia", 0)),
        "don": int(request.form.get("don", 0)),
        "doctor": int(request.form.get("doctor", 0)),
        "sheriff": int(request.form.get("sheriff", 0)),
        "maniac": int(request.form.get("maniac", 0)),
        "kamikaze": int(request.form.get("kamikaze", 0)),
        "villager": int(request.form.get("villager", 0))
    }

    total_roles = sum(roles_config.values())
    if total_roles != len(room["players"]):
        return "Total roles must equal number of players", 400

    players = room["players"]
    assign_roles(players, roles_config)

    for player in players:
        mongo.db.players.update_one(
            {"name": player["name"]}, {"$set": {"role": player["role"]}}
        )
        mongo.db.rooms.update_one(
            {"host_code": code, "players.player_id": player["player_id"]},
            {"$set": {"players.$.role": player["role"]}},
        )

    mongo.db.rooms.update_one(
        {"host_code": code},
        {"$set": {"status": "started", "roles_config": roles_config}}
    )

    for player in players:
        if isinstance(player["player_id"], ObjectId):
            player["player_id"] = str(player["player_id"])

    socketio.emit("update_roles", {"players": players}, room=code)

    return redirect(url_for("host_bp.host", code=code))


@host_bp.post("/end-game/<code>")
def end_game(code: str):
    mongo.db.players.delete_many({"room_code": code})
    mongo.db.rooms.delete_many({"host_code": code})

    return redirect(url_for("home_bp.index"))
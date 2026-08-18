from datetime import datetime
from database import db


def get_default_roles_config(num_players: int) -> dict:
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
            cfg = config.copy()
            total_special = sum(cfg.values())
            cfg["villager"] = max(0, num_players - total_special)
            return cfg

    return {
        "mafia": 1 if num_players >= 3 else 0,
        "don": 0,
        "doctor": 1 if num_players >= 4 else 0,
        "sheriff": 1 if num_players >= 5 else 0,
        "maniac": 0,
        "kamikaze": 0,
        "villager": max(0, num_players - (3 if num_players >= 5 else (2 if num_players >= 4 else (1 if num_players >= 3 else 0))))
    }


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    host_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    status = db.Column(db.String(32), default="waiting")  # waiting, started, ended
    phase = db.Column(db.String(32), default="day")  # day, voting, night
    day_number = db.Column(db.Integer, default=1)
    roles_config = db.Column(db.JSON, default=dict)
    custom_roles = db.Column(db.JSON, default=list)
    started_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    players = db.relationship(
        "Player",
        backref="room",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Player.id"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "host_code": self.host_code,
            "status": self.status,
            "phase": self.phase or "day",
            "day_number": self.day_number or 1,
            "roles_config": self.roles_config or {},
            "custom_roles": self.custom_roles or [],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "players": [p.to_dict() for p in self.players],
            "player_count": len(self.players)
        }


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(32), db.ForeignKey("rooms.host_code"), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(64), nullable=True)
    role_info = db.Column(db.JSON, default=dict)
    is_alive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "player_id": str(self.id),
            "name": self.name,
            "role": self.role,
            "role_info": self.role_info or {},
            "is_alive": self.is_alive,
            "room_code": self.room_code
        }

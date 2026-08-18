import pytest
from app import app
from database import db
from models import Player, Room, get_default_roles_config
from host.host import calculate_game_stats
from utils.role import assign_roles


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"MAFIA" in response.data or b"MAFIYA" in response.data


def test_roles_assignment():
    players = [
        {"id": 1, "name": "Alice", "role": None},
        {"id": 2, "name": "Bob", "role": None},
        {"id": 3, "name": "Charlie", "role": None},
        {"id": 4, "name": "David", "role": None},
    ]
    roles_config = {"mafia": 1, "doctor": 1, "sheriff": 1, "villager": 1}
    assign_roles(players, roles_config)

    assigned_roles = [p["role"].lower() for p in players]
    assert "mafia" in assigned_roles
    assert "doctor" in assigned_roles
    assert "sheriff" in assigned_roles
    assert "villager" in assigned_roles
    assert len(assigned_roles) == 4


def test_default_roles_config():
    cfg = get_default_roles_config(6)
    assert cfg["mafia"] == 2
    assert cfg["doctor"] == 1
    assert cfg["sheriff"] == 1
    assert cfg["villager"] == 2


def test_custom_roles_assignment():
    players = [
        {"id": 1, "name": "Alice", "role": None},
        {"id": 2, "name": "Bob", "role": None},
        {"id": 3, "name": "Charlie", "role": None},
    ]
    custom_roles = [
        {
            "id": "custom_1",
            "name": "Bodyguard",
            "team": "town",
            "icon": "fa-shield-halved",
            "color": "#06d6a0",
            "desc": "Protects one person every night"
        }
    ]
    roles_config = {"mafia": 1, "custom_1": 1, "villager": 1}
    assign_roles(players, roles_config, custom_roles=custom_roles)

    roles = [p["role"] for p in players]
    assert "Mafia" in roles
    assert "Bodyguard" in roles
    assert "Villager" in roles

    bodyguard_player = next(p for p in players if p["role"] == "Bodyguard")
    assert bodyguard_player["role_info"]["team"] == "town"
    assert bodyguard_player["role_info"]["is_custom"] is True


def test_custom_roles_stats_balance(client):
    with app.app_context():
        p1 = Player(room_code="TEST", name="P1", role="Mafia", is_alive=True, role_info={"team": "mafia"})
        p2 = Player(room_code="TEST", name="P2", role="Bodyguard", is_alive=True, role_info={"team": "town", "is_custom": True})
        p3 = Player(room_code="TEST", name="P3", role="Assassin", is_alive=True, role_info={"team": "neutral", "is_custom": True})

        stats = calculate_game_stats([p1, p2, p3])
        assert stats["alive_total"] == 3
        assert stats["alive_mafia"] == 1
        assert stats["alive_town"] == 1
        assert stats["alive_maniac"] == 1
        assert stats["winner"] is None


def test_custom_role_create_and_delete_endpoints(client):
    with app.app_context():
        room = Room(host_code="ROOM123", status="waiting")
        db.session.add(room)
        db.session.commit()

    # Create Custom Role
    res = client.post("/host/create-custom-role/ROOM123", json={
        "name": "Spy",
        "team": "town",
        "icon": "fa-user-secret",
        "color": "#3a86ff",
        "desc": "Can check roles at night"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["role"]["name"] == "Spy"
    role_id = data["role"]["id"]

    with app.app_context():
        r = Room.query.filter_by(host_code="ROOM123").first()
        assert len(r.custom_roles) == 1
        assert r.custom_roles[0]["name"] == "Spy"
        assert r.roles_config.get(role_id) == 0

    # Delete Custom Role
    del_res = client.post(f"/host/delete-custom-role/ROOM123/{role_id}")
    assert del_res.status_code == 200
    del_data = del_res.get_json()
    assert del_data["success"] is True

    with app.app_context():
        r = Room.query.filter_by(host_code="ROOM123").first()
        assert len(r.custom_roles) == 0
        assert role_id not in r.roles_config


def test_full_game_lifecycle_start_phase_toggle_end(client):
    with app.app_context():
        room = Room(host_code="GAME999", status="waiting")
        p1 = Player(room_code="GAME999", name="Player 1")
        p2 = Player(room_code="GAME999", name="Player 2")
        p3 = Player(room_code="GAME999", name="Player 3")
        room.players = [p1, p2, p3]
        db.session.add(room)
        db.session.commit()

    # 1. Start Game
    res = client.post("/host/start-game/GAME999", data={
        "mafia": 1,
        "don": 0,
        "doctor": 1,
        "sheriff": 0,
        "maniac": 0,
        "kamikaze": 0,
        "villager": 1
    }, follow_redirects=False)
    assert res.status_code == 302

    with app.app_context():
        r = Room.query.filter_by(host_code="GAME999").first()
        assert r.status == "started"
        assert r.started_at is not None

    # 2. Toggle Phase to Night
    res = client.post("/host/set-phase/GAME999/night")
    assert res.status_code == 200
    assert res.get_json()["phase"] == "night"

    # 3. Toggle Phase to Day
    res = client.post("/host/set-phase/GAME999/day")
    assert res.status_code == 200
    assert res.get_json()["phase"] == "day"

    # 4. Toggle Player Status
    with app.app_context():
        p = Player.query.filter_by(room_code="GAME999").first()
        p_id = p.id

    res = client.post(f"/host/toggle-player-status/GAME999/{p_id}")
    assert res.status_code == 200
    assert res.get_json()["is_alive"] is False

    # 5. End Game
    res = client.post("/host/end-game/GAME999", follow_redirects=False)
    assert res.status_code == 302

    with app.app_context():
        r = Room.query.filter_by(host_code="GAME999").first()
        assert r is None

import pytest
from app import app
from database import db
from models import get_default_roles_config
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

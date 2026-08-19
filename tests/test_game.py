import os

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import active_night_actions, active_voting_sessions, app
from database import db
from models import Player, Room, get_default_roles_config
from host.host import (
    calculate_game_stats,
    serialize_player_view,
    serialize_public_players,
    validate_initial_role_balance,
)
from utils.role import assign_roles


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        active_night_actions.clear()
        active_voting_sessions.clear()
        yield app.test_client()
        active_night_actions.clear()
        active_voting_sessions.clear()
        db.session.remove()
        db.drop_all()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"MAFIA" in response.data or b"MAFIYA" in response.data


def test_rejoining_player_uses_normalized_name_without_creating_duplicate(client):
    with app.app_context():
        db.session.add(Room(host_code="REJOIN1", status="waiting"))
        db.session.commit()

    first_response = client.post("/join_game", data={
        "room-code": "REJOIN1",
        "player-name": "  ALICE\u00a0\u00a0Smith  ",
    })
    assert first_response.status_code == 302
    first_location = first_response.headers["Location"]

    with client.session_transaction() as browser_session:
        browser_session.clear()

    second_response = client.post("/join_game", data={
        "room-code": "REJOIN1",
        "player-name": "alice smith",
    })

    assert second_response.status_code == 302
    assert second_response.headers["Location"] == first_location
    with app.app_context():
        players = Player.query.filter_by(room_code="REJOIN1").all()
        assert len(players) == 1
        assert players[0].name == "ALICE Smith"


def test_existing_player_can_rejoin_started_game_with_role_preserved(client):
    with app.app_context():
        room = Room(host_code="REJOIN2", status="started", phase="night")
        player = Player(
            room_code="REJOIN2",
            name="Alice",
            role="Doctor",
            role_info={"team": "town"},
            is_alive=False,
        )
        room.players = [player]
        db.session.add(room)
        db.session.commit()
        player_id = player.id

    response = client.post("/join_game", data={
        "room-code": "REJOIN2",
        "player-name": " alice ",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/player/{player_id}")
    with app.app_context():
        players = Player.query.filter_by(room_code="REJOIN2").all()
        assert len(players) == 1
        assert players[0].role == "Doctor"
        assert players[0].is_alive is False


def test_new_player_cannot_join_after_game_has_started(client):
    with app.app_context():
        room = Room(host_code="LOCKED1", status="started")
        room.players = [Player(room_code="LOCKED1", name="Alice", role="Mafia")]
        db.session.add(room)
        db.session.commit()

    response = client.post("/join_game", data={
        "room-code": "LOCKED1",
        "player-name": "Bob",
    })

    assert response.status_code == 409
    assert b"game_started_join_error" in response.data
    with app.app_context():
        assert Player.query.filter_by(room_code="LOCKED1").count() == 1


def test_socket_reconnect_sends_private_role_state(client):
    from websock import socketio

    with app.app_context():
        room = Room(host_code="ROLESYNC", status="started", phase="night", day_number=2)
        player = Player(
            room_code="ROLESYNC",
            name="Alice",
            role="Sheriff",
            role_info={"team": "town"},
        )
        other = Player(
            room_code="ROLESYNC",
            name="Bob",
            role="Mafia",
            role_info={"team": "mafia"},
        )
        room.players = [player, other]
        db.session.add(room)
        db.session.commit()
        player_id = player.id

    socket_client = socketio.test_client(app)
    socket_client.get_received()
    socket_client.emit("join_room", {"room": "ROLESYNC", "player_id": player_id})
    role_updates = [
        event["args"][0]
        for event in socket_client.get_received()
        if event["name"] == "update_roles"
    ]
    socket_client.disconnect()

    assert len(role_updates) == 1
    assert role_updates[0]["sync"] is True
    assert role_updates[0]["phase"] == "night"
    assert role_updates[0]["day_number"] == 2
    current_player = next(item for item in role_updates[0]["players"] if item["id"] == player_id)
    assert current_player["role"] == "Sheriff"
    assert current_player["role_info"]["team"] == "town"
    other_player = next(item for item in role_updates[0]["players"] if item["id"] != player_id)
    assert "role" not in other_player


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

    # 5. End Game
    res = client.post("/host/end-game/GAME999", follow_redirects=False)
    assert res.status_code == 302

    with app.app_context():
        r = Room.query.filter_by(host_code="GAME999").first()
        assert r is None


def test_start_game_rejects_composition_that_already_gives_mafia_the_win(client):
    with app.app_context():
        room = Room(host_code="BADBAL", status="waiting")
        room.players = [
            Player(room_code="BADBAL", name="Doctor"),
            Player(room_code="BADBAL", name="Don"),
            Player(room_code="BADBAL", name="Mafia"),
        ]
        db.session.add(room)
        db.session.commit()

    host_page = client.get("/host/BADBAL")
    assert host_page.status_code == 200
    assert b'composition-warning' in host_page.data

    response = client.post("/host/start-game/BADBAL", data={
        "mafia": 1,
        "don": 1,
        "doctor": 1,
        "sheriff": 0,
        "maniac": 0,
        "kamikaze": 0,
        "villager": 0,
    })

    assert response.status_code == 400
    assert response.get_json()["error_key"] == "invalid_initial_balance_mafia"
    with app.app_context():
        room = Room.query.filter_by(host_code="BADBAL").first()
        assert room.status == "waiting"
        assert all(player.role is None for player in room.players)


def test_initial_balance_uses_custom_role_teams():
    balance = validate_initial_role_balance(
        {"mafia": 1, "custom_don": 1, "doctor": 1},
        [{"id": "custom_don", "name": "Consigliere", "team": "mafia"}],
    )

    assert balance["valid"] is False
    assert balance["winner"] == "mafia"
    assert balance["mafia"] == 2


@pytest.mark.parametrize(
    ("roles_config", "winner"),
    [
        ({"doctor": 1, "sheriff": 1, "villager": 1}, "town"),
        ({"maniac": 1, "villager": 1}, "maniac"),
        ({"mafia": 1, "doctor": 1, "villager": 1}, None),
    ],
)
def test_initial_balance_matches_game_win_conditions(roles_config, winner):
    balance = validate_initial_role_balance(roles_config)

    assert balance["winner"] == winner
    assert balance["valid"] is (winner is None)


def test_mafia_night_target_and_auto_win_condition(client):
    from app import handle_mafia_select_target, active_night_actions
    with app.app_context():
        room = Room(host_code="WIN123", status="started", phase="night")
        m1 = Player(room_code="WIN123", name="Mafia Boss", role="Mafia", role_info={"team": "mafia"}, is_alive=True)
        v1 = Player(room_code="WIN123", name="Villager 1", role="Villager", role_info={"team": "town"}, is_alive=True)
        v2 = Player(room_code="WIN123", name="Villager 2", role="Villager", role_info={"team": "town"}, is_alive=True)
        room.players = [m1, v1, v2]
        db.session.add(room)
        db.session.commit()
        m1_id, v1_id, v2_id = m1.id, v1.id, v2.id

    # 1. Test Mafia selects target
    handle_mafia_select_target({
        "room": "WIN123",
        "voter_id": m1_id,
        "target_id": v1_id
    })
    assert active_night_actions["WIN123"]["mafia_target"] == v1_id

    # 2. Host transitions from night to day -> v1 eliminated
    with app.app_context():
        r = Room.query.filter_by(host_code="WIN123").first()
        r.phase = "night"
        db.session.commit()

    res = client.post("/host/set-phase/WIN123/day")
    assert res.status_code == 200
    data = res.get_json()
    assert data["victim_eliminated"]["id"] == v1_id

    # Now alive: 1 Mafia, 1 Villager -> Mafia count >= Town count -> winner is mafia!
    assert data["stats"]["alive_mafia"] == 1
    assert data["stats"]["alive_town"] == 1
    assert data["stats"]["winner"] == "mafia"


def test_don_priority_override_over_mafia(client):
    from app import handle_mafia_select_target, active_night_actions
    with app.app_context():
        room = Room(host_code="DON999", status="started", phase="night")
        don = Player(room_code="DON999", name="The Don", role="Don", role_info={"team": "mafia"}, is_alive=True)
        mafia = Player(room_code="DON999", name="Regular Mafia", role="Mafia", role_info={"team": "mafia"}, is_alive=True)
        v1 = Player(room_code="DON999", name="Target 1", role="Villager", role_info={"team": "town"}, is_alive=True)
        v2 = Player(room_code="DON999", name="Target 2", role="Villager", role_info={"team": "town"}, is_alive=True)
        room.players = [don, mafia, v1, v2]
        db.session.add(room)
        db.session.commit()
        don_id, mafia_id, v1_id, v2_id = don.id, mafia.id, v1.id, v2.id

    # 1. Regular Mafia votes for Target 1
    handle_mafia_select_target({
        "room": "DON999",
        "voter_id": mafia_id,
        "target_id": v1_id
    })
    assert active_night_actions["DON999"]["mafia_target"] == v1_id

    # 2. Don votes for Target 2 -> Overrides Target 1!
    handle_mafia_select_target({
        "room": "DON999",
        "voter_id": don_id,
        "target_id": v2_id
    })
    assert active_night_actions["DON999"]["mafia_target"] == v2_id
    assert active_night_actions["DON999"]["don_target"] == v2_id

    # 3. Regular Mafia tries to vote for Target 1 again -> Don's Target 2 remains final!
    handle_mafia_select_target({
        "room": "DON999",
        "voter_id": mafia_id,
        "target_id": v1_id
    })
    assert active_night_actions["DON999"]["mafia_target"] == v2_id


def test_all_night_roles_and_doctor_resolution(client):
    from app import (
        get_night_action_summary,
        handle_doctor_select_target,
        handle_don_check_sheriff,
        handle_mafia_select_target,
        handle_maniac_select_target,
        handle_sheriff_check_target,
    )
    with app.app_context():
        room = Room(host_code="NIGHT1", status="started", phase="night", day_number=1)
        players = [
            Player(room_code="NIGHT1", name="Don", role="Don", role_info={"team": "mafia"}),
            Player(room_code="NIGHT1", name="Doctor", role="Doctor", role_info={"team": "town"}),
            Player(room_code="NIGHT1", name="Sheriff", role="Sheriff", role_info={"team": "town"}),
            Player(room_code="NIGHT1", name="Maniac", role="Maniac", role_info={"team": "neutral"}),
            Player(room_code="NIGHT1", name="Saved", role="Villager", role_info={"team": "town"}),
            Player(room_code="NIGHT1", name="Victim", role="Villager", role_info={"team": "town"}),
            Player(room_code="NIGHT1", name="Witness", role="Villager", role_info={"team": "town"}),
        ]
        room.players = players
        db.session.add(room)
        db.session.commit()
        don, doctor, sheriff, maniac, saved, victim, _ = players

        assert handle_mafia_select_target({"room": "NIGHT1", "player_id": don.id, "target_id": saved.id})["success"]
        assert handle_doctor_select_target({"room": "NIGHT1", "player_id": doctor.id, "target_id": saved.id})["success"]
        sheriff_result = handle_sheriff_check_target({"room": "NIGHT1", "player_id": sheriff.id, "target_id": don.id})
        assert sheriff_result["is_mafia"] is True
        assert handle_maniac_select_target({"room": "NIGHT1", "player_id": maniac.id, "target_id": victim.id})["success"]
        don_result = handle_don_check_sheriff({"room": "NIGHT1", "player_id": don.id, "target_id": sheriff.id})
        assert don_result["is_sheriff"] is True
        summary = get_night_action_summary("NIGHT1")
        assert summary["all_complete"] is True
        assert summary["completed_total"] == summary["required_total"] == 5
        saved_id, victim_id, sheriff_id = saved.id, victim.id, sheriff.id

    host_page = client.get("/host/NIGHT1")
    player_page = client.get(f"/player/{sheriff_id}")
    assert host_page.status_code == 200
    assert b"host-doctor-target-display" in host_page.data
    assert player_page.status_code == 200
    assert b"sheriff-investigation-result" in player_page.data

    response = client.post("/host/set-phase/NIGHT1/day")
    result = response.get_json()
    assert [p["id"] for p in result["players_saved"]] == [saved_id]
    assert [p["id"] for p in result["victims_eliminated"]] == [victim_id]
    with app.app_context():
        assert db.session.get(Player, saved_id).is_alive is True
        assert db.session.get(Player, victim_id).is_alive is False


def test_doctor_cannot_self_protect_two_nights_in_a_row(client):
    from app import handle_doctor_select_target
    with app.app_context():
        room = Room(host_code="DOC2", status="started", phase="night", day_number=1)
        doctor = Player(room_code="DOC2", name="Doctor", role="Doctor", role_info={"team": "town"})
        mafia = Player(room_code="DOC2", name="Mafia", role="Mafia", role_info={"team": "mafia"})
        villager = Player(room_code="DOC2", name="Villager", role="Villager", role_info={"team": "town"})
        room.players = [doctor, mafia, villager]
        db.session.add(room)
        db.session.commit()
        doctor_id = doctor.id
        first = handle_doctor_select_target({"room": "DOC2", "player_id": doctor_id, "target_id": doctor_id})
        assert first["success"] is True

    assert client.post("/host/set-phase/DOC2/day").status_code == 200
    assert client.post("/host/set-phase/DOC2/night").status_code == 200
    with app.app_context():
        blocked = handle_doctor_select_target({"room": "DOC2", "player_id": doctor_id, "target_id": doctor_id})
        assert blocked["success"] is False
        assert blocked["error_key"] == "doctor_self_consecutive_error"


def test_player_rosters_do_not_reveal_living_roles(client):
    with app.app_context():
        mafia = Player(id=101, name="Mafia", role="Mafia", role_info={"team": "mafia"}, is_alive=True)
        don = Player(id=102, name="Don", role="Don", role_info={"team": "mafia"}, is_alive=True)
        sheriff = Player(id=103, name="Sheriff", role="Sheriff", role_info={"team": "town"}, is_alive=True)
        ghost = Player(id=104, name="Ghost", role="Doctor", role_info={"team": "town"}, is_alive=False)
        players = [mafia, don, sheriff, ghost]

        public = serialize_public_players(players)
        assert all("role" not in player for player in public)

        mafia_view = serialize_player_view(players, mafia)
        assert {player["id"] for player in mafia_view if "role" in player} == {mafia.id, don.id}

        sheriff_view = serialize_player_view(players, sheriff)
        assert {player["id"] for player in sheriff_view if "role" in player} == {sheriff.id}

        ghost_view = serialize_player_view(players, ghost)
        assert all("role" in player for player in ghost_view)


def test_night_action_events_are_routed_only_to_allowed_rooms(client):
    from websock import socketio
    with app.app_context():
        room = Room(host_code="PRIVATE1", status="started", phase="night")
        mafia = Player(room_code="PRIVATE1", name="Mafia", role="Mafia", role_info={"team": "mafia"})
        target = Player(room_code="PRIVATE1", name="Target", role="Villager", role_info={"team": "town"})
        observer = Player(room_code="PRIVATE1", name="Observer", role="Villager", role_info={"team": "town"})
        room.players = [mafia, target, observer]
        db.session.add(room)
        db.session.commit()
        mafia_id, target_id, observer_id = mafia.id, target.id, observer.id

    host_socket = socketio.test_client(app)
    mafia_socket = socketio.test_client(app)
    observer_socket = socketio.test_client(app)
    try:
        host_socket.emit("join_room", {"room": "PRIVATE1", "client_type": "host"})
        mafia_socket.emit("join_room", {"room": "PRIVATE1", "player_id": mafia_id})
        observer_socket.emit("join_room", {"room": "PRIVATE1", "player_id": observer_id})
        host_socket.get_received()
        mafia_socket.get_received()
        observer_socket.get_received()

        result = mafia_socket.emit(
            "mafia_select_target",
            {"room": "PRIVATE1", "player_id": mafia_id, "target_id": target_id},
            callback=True,
        )
        assert result["success"] is True

        host_events = {event["name"] for event in host_socket.get_received()}
        mafia_events = {event["name"] for event in mafia_socket.get_received()}
        observer_events = {event["name"] for event in observer_socket.get_received()}
        assert {"mafia_target_updated", "night_action_updated"} <= host_events
        assert "mafia_target_updated" in mafia_events
        assert "night_action_updated" not in mafia_events
        assert "mafia_target_updated" not in observer_events
        assert "night_action_updated" not in observer_events
    finally:
        host_socket.disconnect()
        mafia_socket.disconnect()
        observer_socket.disconnect()


def test_duplicate_mafia_and_maniac_attack_is_one_death(client):
    from app import handle_mafia_select_target, handle_maniac_select_target
    with app.app_context():
        room = Room(host_code="DUPE1", status="started", phase="night", day_number=1)
        mafia = Player(room_code="DUPE1", name="Mafia", role="Mafia", role_info={"team": "mafia"})
        maniac = Player(room_code="DUPE1", name="Maniac", role="Maniac", role_info={"team": "neutral"})
        victim = Player(room_code="DUPE1", name="Victim", role="Villager", role_info={"team": "town"})
        witness = Player(room_code="DUPE1", name="Witness", role="Villager", role_info={"team": "town"})
        room.players = [mafia, maniac, victim, witness]
        db.session.add(room)
        db.session.commit()
        victim_id = victim.id

        assert handle_mafia_select_target({"room": "DUPE1", "player_id": mafia.id, "target_id": victim_id})["success"]
        assert handle_maniac_select_target({"room": "DUPE1", "player_id": maniac.id, "target_id": victim_id})["success"]

    result = client.post("/host/set-phase/DUPE1/day").get_json()
    assert len(result["victims_eliminated"]) == 1
    assert result["victims_eliminated"][0]["id"] == victim_id
    assert result["victims_eliminated"][0]["sources"] == ["mafia", "maniac"]


def test_leaving_voting_phase_closes_stale_voting_session(client):
    with app.app_context():
        room = Room(host_code="VOTEEND", status="started", phase="voting", day_number=1)
        room.players = [
            Player(room_code="VOTEEND", name="P1", role="Mafia", role_info={"team": "mafia"}),
            Player(room_code="VOTEEND", name="P2", role="Villager", role_info={"team": "town"}),
            Player(room_code="VOTEEND", name="P3", role="Villager", role_info={"team": "town"}),
        ]
        db.session.add(room)
        db.session.commit()
        active_voting_sessions["VOTEEND"] = {"candidates": [], "votes": {}, "open": True}

    response = client.post("/host/set-phase/VOTEEND/night")
    assert response.status_code == 200
    assert "VOTEEND" not in active_voting_sessions

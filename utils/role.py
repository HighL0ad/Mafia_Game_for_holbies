import random


def assign_roles(players):
    num_players = len(players)

    roles_config = {
        range(1, 6): [("Mafia", 1), ("Doctor", 1), ("Sheriff", 1)],
        range(6, 11): [
            ("Mafia", 2),
            ("Doctor", 1),
            ("Sheriff", 1),
        ],
        range(11, 16): [
            ("Mafia", 3),
            ("Don", 1),
            ("Doctor", 1),
            ("Sheriff", 1),
            ("Maniac", 1),
            ("Kamikaze", 1),
        ],
        range(16, 21): [
            ("Mafia", 4),
            ("Don", 1),
            ("Doctor", 2),
            ("Sheriff", 1),
            ("Maniac", 1),
            ("Kamikaze", 1),
        ],
        range(21, 26): [
            ("Mafia", 5),
            ("Don", 1),
            ("Doctor", 2),
            ("Sheriff", 2),
            ("Maniac", 1),
            ("Kamikaze", 1),
        ],
        range(26, 31): [
            ("Mafia", 6),
            ("Don", 1),
            ("Doctor", 2),
            ("Sheriff", 2),
            ("Maniac", 2),
            ("Kamikaze", 1),
        ],
    }

    for player_range, config in roles_config.items():
        if num_players in player_range:
            roles = [role for role, count in config for _ in range(count)]
            break
    else:
        roles = []

    num_villagers = num_players - len(roles)
    roles += ["Villager"] * num_villagers

    random.shuffle(roles)

    for i, player in enumerate(players):
        player["role"] = roles[i]

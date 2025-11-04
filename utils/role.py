import random


def assign_roles(players, roles_config):
    roles = []

    role_names = {
        "mafia": "Mafia",
        "don": "Don",
        "doctor": "Doctor",
        "sheriff": "Sheriff",
        "maniac": "Maniac",
        "kamikaze": "Kamikaze",
        "villager": "Villager"
    }

    for role_key, count in roles_config.items():
        role_name = role_names.get(role_key, role_key.capitalize())
        roles.extend([role_name] * count)

    random.shuffle(roles)

    for i, player in enumerate(players):
        if i < len(roles):
            player["role"] = roles[i]
        else:
            player["role"] = "Villager"
import random

STANDARD_ROLES = {
    "mafia": {"name": "Mafia", "team": "mafia", "icon": "fa-gun", "color": "#e63946"},
    "don": {"name": "Don", "team": "mafia", "icon": "fa-crown", "color": "#f4a261"},
    "doctor": {"name": "Doctor", "team": "town", "icon": "fa-user-doctor", "color": "#06d6a0"},
    "sheriff": {"name": "Sheriff", "team": "town", "icon": "fa-shield-halved", "color": "#3a86ff"},
    "maniac": {"name": "Maniac", "team": "neutral", "icon": "fa-skull-crossbones", "color": "#9b5de5"},
    "kamikaze": {"name": "Kamikaze", "team": "town", "icon": "fa-bomb", "color": "#fb5607"},
    "villager": {"name": "Villager", "team": "town", "icon": "fa-users", "color": "#8d99ae"}
}


def assign_roles(players, roles_config, custom_roles=None):
    roles = []
    custom_map = {}
    if custom_roles:
        for cr in custom_roles:
            if isinstance(cr, dict) and "id" in cr:
                custom_map[cr["id"]] = cr

    for role_key, count in roles_config.items():
        if count <= 0:
            continue
        if role_key in STANDARD_ROLES:
            info = STANDARD_ROLES[role_key]
            for _ in range(count):
                roles.append({
                    "role": info["name"],
                    "role_info": info
                })
        elif role_key in custom_map:
            cr = custom_map[role_key]
            for _ in range(count):
                roles.append({
                    "role": cr.get("name", "Custom"),
                    "role_info": {
                        "name": cr.get("name", "Custom"),
                        "team": cr.get("team", "town"),
                        "icon": cr.get("icon", "fa-mask"),
                        "color": cr.get("color", "#3a86ff"),
                        "desc": cr.get("desc", ""),
                        "is_custom": True
                    }
                })

    random.shuffle(roles)

    for i, player in enumerate(players):
        if i < len(roles):
            player["role"] = roles[i]["role"]
            player["role_info"] = roles[i]["role_info"]
        else:
            player["role"] = "Villager"
            player["role_info"] = STANDARD_ROLES["villager"]
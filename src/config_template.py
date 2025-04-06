import numpy as np

from src.bots.abyss.player_ship import PlayerShip


#######################################
# DO NOT ADD PERSONAL DATA HERE!!!    #
# COPY THIS AND RENAME TO "config.py" #
#######################################


# General:
LOG_FILENAME = "out/log_default.txt"
CHARACTER_NAME = "Character Name"
DISCORD_NOTIFICATION_WEBHOOK_URL = "https://discord.com/api/webhooks/123/ABC"
DISCORD_NOTIFICATION_ROLE_ID = "123"


# Memory reader config:
MEMORY_READER_DLL_PATH = r"D:\Projects\Python\eve-memory-2\src\utils\eve-memory-reader.dll"
WINDOW_HEADER_OFFSET = 32
HORIZONTAL_OFFSET = 8  # don't know where it comes from


# Hauler config:
HAULER_LOG_FILE_PATH = "out/log_hauler.txt"
HAULER_AGENT_NAME = "Hauler Agent"
HAULER_MAX_ROUTE_LENGTHS = [
    # (min_standing, max_route_length)
    (6, 3),
    (7, 2),
    (8, 1)
]
HAULER_SHIP_MAX_CAPACITY = 4095


# Abyssal config:
ABYSSAL_LOG_FILE_PATH = "out/log_abyssal.txt"
ABYSSAL_ITEM_DATA_PATH = "data/item_data.json"
ABYSSAL_SHIP_DATA_PATH = "data/ships_data.json"
ABYSSAL_SHIP_CORRECTIONS_DATA_PATH = "data/ships_data_corrections.json"
ABYSSAL_BASE_LOCATION = "Personal Locations/Abyss/base station"
ABYSSAL_SAFE_SPOT_LOCATION = "Personal Locations/Abyss/safe spot"
ABYSSAL_DIFFICULTY = "Calm"  # Tranquil/Calm/Agitated/Fierce/Raging/Chaotic/Cataclysmic
ABYSSAL_WEATHER = "Gamma"  # Dark/Electrical/Exotic/Firestorm/Gamma
ABYSSAL_SUPPLIES = {
    # INCLUDING FILAMENTS!
    # "item_name": (min_amount, max_amount)
    "Nanite Repair Paste": (20, 50),
    "Calm Gamma Filament": (1, 3),
    "Nova Fury Light Missile": (500, 1500),
}
ABYSSAL_DRONES = {
    # "item_name": amount,
    # "Warrior I": 2,
    # "Hornet I": 2,
    "Republic Fleet Warrior": 2,
}
ABYSSAL_MAX_DRONES_IN_SPACE = 2
ABYSSAL_WEAPON_MODULE_INDICES = [0]
ABYSSAL_AMMO_PER_WEAPON = [20]
ABYSSAL_HARDENER_MODULE_INDICES = [4]
ABYSSAL_SPEED_MODULE_INDICES = [3]
ABYSSAL_WEB_MODULE_INDICES = [2]
ABYSSAL_WEB_RANGE = 10_000
ABYSSAL_SHIELD_BOOSTER_INDICES = [0]
ABYSSAL_SHIELD_BOOSTER_DURATION = 3
ABYSSAL_SHIELD_BOOSTER_AMOUNT = 104
ABYSSAL_IS_SHIELD_TANK = True
ABYSSAL_IS_ARMOR_TANK = False
ABYSSAL_IS_STRUCTURE_TANK = False
ABYSSAL_PLAYER_SHIP = PlayerShip(
    shield_max_hp=1955,
    shield_hp=1955,
    armor_max_hp=1440,
    armor_hp=1440,
    structure_max_hp=1610,
    structure_hp=1610,
    resist_matrix=np.array([
        [0.52, 0.56, 0.42, 0.35],
        [0.50, 0.55, 0.75, 0.90],
        [0.67, 0.67, 0.67, 0.67],
    ]),
    max_velocity=587.1,
    signature_radius=158.0,
    turret_damage_profile=np.array([0.0, 0.0, 0.0, 0.0]),
    turret_falloff=0,
    turret_optimal_range=0,
    turret_rate_of_fire=0,
    turret_tracking=0,
    dmg_multiplier_bonus_per_second=0,
    dmg_multiplier_bonus_max=0,
    missile_damage_profile=np.array([0.0, 0.0, 0.0, 725.0]),
    missile_explosion_radius=64,
    missile_explosion_velocity=197,
    missile_damage_reduction_factor=0.604,
    missile_rate_of_fire=0.3077,
    missile_range=24_000,
    drone_range=35_000,
    drone_max_in_space=2,
    drone_rate_of_fire=0.25,
    drone_damage_modifier=2.434,
    drone_damage_profile=np.array([0.0, 0.0, 0.0, 20.0]),
)

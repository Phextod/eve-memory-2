from dataclasses import dataclass
from typing import Dict

from src.bots.abyss.ship_attributes import Tank, DamageType


@dataclass
class Ship:
    shield: Tank
    armor: Tank
    structure: Tank

    # Weapon
    # Turret
    turret_damage_profile: Dict[DamageType, float]
    turret_falloff: int
    turret_optimal_range: int
    turret_rate_of_fire: float
    turret_tracking: int

    # Missile
    missile_damage_profile: Dict[DamageType, float]
    missile_explosion_radius: float
    missile_explosion_velocity: float
    missile_damage_reduction_factor: float
    missile_rate_of_fire: float

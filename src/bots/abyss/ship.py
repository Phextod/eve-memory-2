from dataclasses import dataclass
from enum import Enum
from typing import Dict


class DamageType(Enum):
    thermal = 0
    em = 1
    kinetic = 2
    explosion = 3


class Tank:
    def __init__(self, hp: int, resist_profile: Dict[DamageType, float]):
        self.hp = hp
        self.resist_profile = resist_profile

    def get_effective_dmg_from(self, damage_profile: Dict[DamageType, int]):
        effective_dmg = dict()
        for damage_type, damage in damage_profile.items():
            resist_multiplier = self.resist_profile[damage_type]
            effective_dmg.update({damage_type: damage * resist_multiplier})


@dataclass
class Ship:
    type_name: str
    shield: Tank
    armor: Tank
    structure: Tank
    signature_radius: int
    max_velocity: int

    # Weapon
    damage_modifier: float
    falloff: int
    optimal_range: int
    rate_of_fire: float
    tracking: int

    # Ammunition
    damage_profile: Dict[DamageType, int]

    # Additional info
    primary_ewar: str
    secondary_ewar: int
    neut_per_second: int
    orbit_velocity: int
    npc_orbit_range: int

    @staticmethod
    def from_json(in_data: dict):
        decode_dict = {
            "type_name": "type_name",
            "shield": "shield",
            "armor": "armor",
            "structure": "structure",
            "signature_radius": "signature_radius",
            "max_velocity": "max_velocity",
            "damage_modifier": "damage_modifier",
            "falloff": "falloff",
            "optimal_range": "optimal_range",
            "rate_of_fire": "rate_of_fire",
            "tracking": "tracking",
            "damage_profile": "damage_profile",
            "primary_ewar": "primary_ewar",
            "secondary_ewar": "secondary_ewar",
            "neut_per_second": "neut_per_second",
            "orbit_velocity": "orbit_velocity",
            "npc_orbit_range": "npc_orbit_range",
        }

        ship_data = dict()
        for out_key in decode_dict:
            in_key = decode_dict[out_key]
            ship_data.update({out_key: in_data.get(in_key, None)})

        return Ship(**ship_data)

    def get_average_dps_to(self, target: "Ship", distance: int, angular=0.0):
        # https://wiki.eveuniversity.org/Turret_mechanics
        tracking_terms = ((angular * 40_000) / (self.tracking * target.signature_radius)) ** 2
        range_terms = (max(0, distance - self.optimal_range) / self.falloff) ** 2
        hit_chance = 0.5 ** (tracking_terms + range_terms)
        normalised_dps_multiplier = 0.5 * min(hit_chance ** 2 + 0.98 * hit_chance + 0.0501, 6 * hit_chance)
        return normalised_dps_multiplier

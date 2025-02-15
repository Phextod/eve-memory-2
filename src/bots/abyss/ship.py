from dataclasses import dataclass
from typing import Dict

from src.bots.abyss.ship_attributes import Tank, DamageType


@dataclass
class Ship:
    shield: Tank
    armor: Tank
    structure: Tank

    max_velocity: float
    signature_radius: float

    # Weapon
    dmg_multiplier_bonus_per_second: float
    dmg_multiplier_bonus_max: float
    # Turret
    turret_damage_profile: Dict[DamageType, float]
    turret_falloff: int
    turret_optimal_range: int
    turret_time_between_shots: float
    turret_tracking: int

    # Missile
    missile_damage_profile: Dict[DamageType, float]
    missile_explosion_radius: float
    missile_explosion_velocity: float
    missile_damage_reduction_factor: float
    missile_time_between_shots: float

    def get_dps_to(
            self,
            target: "Ship",
            time_from_start=0.0,
            target_velocity=0.0,
            target_angular=0.0,
            target_distance=0.0
    ):
        applied_dps = None
        if self.turret_time_between_shots > 0:
            applied_dps = self.get_turret_applied_dps_to(target.signature_radius, target_distance, target_angular)
            spooling = 1 + min(self.dmg_multiplier_bonus_per_second * time_from_start, self.dmg_multiplier_bonus_max)
            applied_dps *= spooling
        elif self.turret_time_between_shots > 0:
            applied_dps = self.get_missile_applied_dps_to(target.signature_radius, target_velocity)
        return target.apply_resists_to_dps(applied_dps)

    def apply_resists_to_dps(self, incoming_dps: Dict[DamageType, float]):
        shield_dps = \
            sum([(1 - self.shield.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        armor_dps = \
            sum([(1 - self.armor.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        structure_dps = \
            sum([(1 - self.structure.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        ttk_sum = self.shield.hp / shield_dps + self.armor.hp / armor_dps + self.structure.hp / structure_dps
        return (self.shield.hp + self.armor.hp + self.structure.hp) / ttk_sum

    def get_turret_applied_dps_to(self, target_signature_radius, target_distance, target_angular):
        # https://wiki.eveuniversity.org/Turret_mechanics
        tracking_terms = ((target_angular * 40_000) / (self.turret_tracking * target_signature_radius)) ** 2
        range_terms = (max(0, target_distance - self.turret_optimal_range) / self.turret_falloff) ** 2
        hit_chance = 0.5 ** (tracking_terms + range_terms)
        normalised_dmg_multiplier = 0.5 * min(hit_chance ** 2 + 0.98 * hit_chance + 0.0501, 6 * hit_chance)

        applied_dmg = {}
        for dmg_type, dmg in self.turret_damage_profile.items():
            rate_of_fire_multiplier = 1 / self.turret_time_between_shots
            applied_dmg.update({dmg_type: dmg * rate_of_fire_multiplier * normalised_dmg_multiplier})
        return applied_dmg

    def get_missile_applied_dps_to(self, target_signature_radius, target_velocity):
        # https://wiki.eveuniversity.org/Missile_mechanics
        term1 = target_signature_radius / self.missile_explosion_radius
        term2 = ((target_signature_radius * self.missile_explosion_velocity)
                 / (self.missile_explosion_radius * target_velocity)) ** self.missile_damage_reduction_factor
        dmg_multiplier = min(1, term1, term2)

        applied_dmg = {}
        for dmg_type, dmg in self.missile_damage_profile.items():
            rate_of_fire_multiplier = 1 / self.missile_time_between_shots
            applied_dmg.update({dmg_type: dmg * rate_of_fire_multiplier * dmg_multiplier})
        return applied_dmg

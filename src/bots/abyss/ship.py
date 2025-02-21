from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from line_profiler_pycharm import profile


@dataclass
class Ship:
    # shield[em, thermal, kinetic, explosive]
    # armor[em, thermal, kinetic, explosive]
    # structure[em, thermal, kinetic, explosive]
    # RESONANCE values!!! (eg.: 0.2 resist => 0.8 resonance)
    resist_matrix: np.ndarray

    shield_max_hp: int
    shield_hp: int

    armor_max_hp: int
    armor_hp: int

    structure_max_hp: int
    structure_hp: int

    max_velocity: float
    signature_radius: float

    # Weapon
    # Turret
    # [em, thermal, kinetic, explosive]
    turret_damage_profile: np.ndarray
    turret_falloff: int
    turret_optimal_range: int
    turret_rate_of_fire: float
    turret_tracking: int
    dmg_multiplier_bonus_per_second: float
    dmg_multiplier_bonus_max: float

    # Missile
    # [em, thermal, kinetic, explosive]
    missile_damage_profile: np.ndarray
    missile_explosion_radius: float
    missile_explosion_velocity: float
    missile_damage_reduction_factor: float
    missile_rate_of_fire: float
    missile_range: int

    def get_dps_to(
            self,
            target: "Ship",
            time_from_start,
            target_distance,
            target_velocity,
            target_angular,
    ):
        applied_dps = np.zeros(4)
        if self.turret_rate_of_fire > 0:
            spooling = 1.0 + min(self.dmg_multiplier_bonus_per_second * time_from_start, self.dmg_multiplier_bonus_max)
            applied_dps = self.get_turret_applied_dps_to(
                target.signature_radius,
                target_distance,
                target_angular,
                spooling,
            )
        elif self.missile_rate_of_fire > 0 and target_distance <= self.missile_range:
            applied_dps = self.get_missile_applied_dps_to(target.signature_radius, target_velocity)

        return target.apply_resists_to_dps(applied_dps)

    def apply_resists_to_dps(self, incoming_dps: Optional[np.ndarray]):
        incoming_dps.reshape(4, 1)
        dps_values = self.resist_matrix @ incoming_dps  # (3×4) @ (4×1) -> (3×1)

        if not np.any(dps_values):
            return 0.0

        ttk_sum = self.shield_hp / dps_values[0] \
            + self.armor_hp / dps_values[1] \
            + self.structure_hp / dps_values[2]
        return (self.shield_hp + self.armor_hp + self.structure_hp) / ttk_sum

    def get_turret_applied_dps_to(
            self,
            target_signature_radius,
            target_distance,
            target_angular,
            spooling_multiplier=1.0
    ):
        """
        :param target_distance: in meters
        :param target_signature_radius: aka target size
        :param target_angular: angular velocity in radian per second
        :param spooling_multiplier: multiplier used for spooling damage (>1.0)
        """
        # https://wiki.eveuniversity.org/Turret_mechanics
        tracking_terms = ((target_angular * 40_000) / (self.turret_tracking * target_signature_radius)) ** 2
        range_terms = (max(0, target_distance - self.turret_optimal_range) / (self.turret_falloff or 1)) ** 2
        hit_chance = 0.5 ** (tracking_terms + range_terms)
        normalised_dmg_multiplier = 0.5 * min(hit_chance ** 2 + 0.98 * hit_chance + 0.0501, 6 * hit_chance)

        effective_dmg_multiplier = self.turret_rate_of_fire * normalised_dmg_multiplier * spooling_multiplier

        return self.turret_damage_profile * effective_dmg_multiplier

    def get_missile_applied_dps_to(self, target_signature_radius, target_velocity):
        # https://wiki.eveuniversity.org/Missile_mechanics
        term1 = target_signature_radius / self.missile_explosion_radius
        term2 = ((target_signature_radius * self.missile_explosion_velocity)
                 / (self.missile_explosion_radius * target_velocity)) ** self.missile_damage_reduction_factor
        dmg_multiplier = min(1, term1, term2)

        return self.missile_damage_profile * (self.missile_rate_of_fire * dmg_multiplier)

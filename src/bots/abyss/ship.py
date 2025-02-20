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
    # Turret
    turret_damage_profile: Dict[DamageType, float]
    turret_falloff: int
    turret_optimal_range: int
    turret_time_between_shots: float
    turret_tracking: int
    dmg_multiplier_bonus_per_second: float
    dmg_multiplier_bonus_max: float

    # Missile
    missile_damage_profile: Dict[DamageType, float]
    missile_explosion_radius: float
    missile_explosion_velocity: float
    missile_damage_reduction_factor: float
    missile_time_between_shots: float
    missile_range: int

    def get_dps_to(
            self,
            target: "Ship",
            time_from_start,
            target_distance,
            target_velocity,
            target_angular,
    ):
        applied_dps = {DamageType.em: 0.0, DamageType.thermal: 0.0, DamageType.kinetic: 0.0, DamageType.explosive: 0.0}
        if self.turret_time_between_shots > 0:
            spooling = 1.0 + min(self.dmg_multiplier_bonus_per_second * time_from_start, self.dmg_multiplier_bonus_max)
            applied_dps = self.get_turret_applied_dps_to(
                target.signature_radius,
                target_distance,
                target_angular,
                spooling,
            )
        elif self.missile_time_between_shots > 0 and target_distance <= self.missile_range:
            applied_dps = self.get_missile_applied_dps_to(target.signature_radius, target_velocity)
        return target.apply_resists_to_dps(applied_dps)

    def apply_resists_to_dps(self, incoming_dps: Dict[DamageType, float]):
        for _, dmg_value in incoming_dps.items():
            if dmg_value > 0:
                break
        else:
            return 0.0

        shield_dps = \
            sum([(1 - self.shield.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        armor_dps = \
            sum([(1 - self.armor.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        structure_dps = \
            sum([(1 - self.structure.resist_profile[dmg_type]) * dmg for dmg_type, dmg in incoming_dps.items()])
        ttk_sum = self.shield.current_hp / shield_dps \
            + self.armor.current_hp / armor_dps \
            + self.structure.current_hp / structure_dps
        return (self.shield.current_hp + self.armor.current_hp + self.structure.current_hp) / ttk_sum

    def get_turret_applied_dps_to(
            self,
            target_signature_radius,
            target_distance,
            target_angular,
            multiplier=1.0
    ):
        """
        :param target_distance: in meters
        :param target_signature_radius: aka target size
        :param target_angular: angular velocity in radian per second
        :param multiplier: multiplier used for spooling damage (>1.0)
        """
        # https://wiki.eveuniversity.org/Turret_mechanics
        tracking_terms = ((target_angular * 40_000) / (self.turret_tracking * target_signature_radius)) ** 2
        range_terms = (max(0, target_distance - self.turret_optimal_range) / (self.turret_falloff or 1)) ** 2
        hit_chance = 0.5 ** (tracking_terms + range_terms)
        normalised_dmg_multiplier = 0.5 * min(hit_chance ** 2 + 0.98 * hit_chance + 0.0501, 6 * hit_chance)

        applied_dmg = {}
        for dmg_type, dmg in self.turret_damage_profile.items():
            rate_of_fire_multiplier = 1 / self.turret_time_between_shots
            applied_dmg.update({dmg_type: dmg * rate_of_fire_multiplier * normalised_dmg_multiplier * multiplier})
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

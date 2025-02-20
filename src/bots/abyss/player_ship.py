from dataclasses import dataclass
from typing import Dict

from src.bots.abyss.ship import Ship
from src.bots.abyss.ship_attributes import DamageType


@dataclass
class PlayerShip(Ship):
    drone_range: int
    drone_max_in_space: int
    drone_time_between_shots: float
    drone_damage_modifier: float
    drone_damage_profile: Dict[DamageType, float]

    def get_drone_applied_dps_to(self):
        applied_dmg = {}
        for dmg_type, dmg in self.drone_damage_profile.items():
            rate_of_fire_multiplier = 1 / self.drone_time_between_shots
            applied_dmg.update(
                {dmg_type: dmg * rate_of_fire_multiplier * self.drone_damage_modifier * self.drone_max_in_space}
            )
        return applied_dmg

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

        if self.drone_time_between_shots > 0 and target_distance <= self.drone_range:
            drone_dps = self.get_drone_applied_dps_to()
            applied_dps = {
                k: applied_dps.get(k) + drone_dps.get(k) for k in applied_dps.keys()
            }

        return target.apply_resists_to_dps(applied_dps)

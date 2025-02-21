from dataclasses import dataclass

import numpy as np

from src.bots.abyss.ship import Ship


@dataclass
class PlayerShip(Ship):
    drone_range: int
    drone_max_in_space: int
    drone_rate_of_fire: float
    drone_damage_modifier: float
    drone_damage_profile: np.ndarray

    def get_drone_applied_dps_to(self):
        effective_dmg_multiplier = self.drone_rate_of_fire * self.drone_damage_modifier * self.drone_max_in_space
        return self.drone_damage_profile * effective_dmg_multiplier

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

        if self.drone_rate_of_fire > 0 and target_distance <= self.drone_range:
            applied_dps += self.get_drone_applied_dps_to()

        return target.apply_resists_to_dps(applied_dps)

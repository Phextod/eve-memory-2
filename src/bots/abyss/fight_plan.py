from typing import List

from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.player_ship import PlayerShip


class Stage:
    def __init__(self, enemies, target, orbit_target):
        self.enemies: List[AbyssShip] = enemies
        self.target: AbyssShip = target
        self.orbit_target: AbyssShip = orbit_target

        self.duration = 0.0

    def update_stage_duration(self, player: PlayerShip, time_from_start, same_orbit_target_duration):
        # https://wiki.eveuniversity.org/Velocity#Angular_Velocity
        target_angular = (self.target.orbit_velocity or self.target.max_velocity) \
                         / (self.target.npc_orbit_range or 10_000)
        target_hp = self.target.shield.current_hp + self.target.armor.current_hp + self.target.structure.current_hp

        if self.target == self.orbit_target:
            orbit_range = 2_500
            target_distance = self.target.npc_orbit_range
            velocity_diff = player.max_velocity - self.target.max_velocity
            time_to_drones = max(
                0.0,
                (target_distance - player.drone_range) / velocity_diff - same_orbit_target_duration
            )

            time_to_weapons = 0.0
            if player.turret_time_between_shots > 0.0:
                time_to_weapons = max(
                    0.0,
                    (target_distance - (player.turret_optimal_range + player.turret_falloff)) / velocity_diff
                )
            elif player.missile_time_between_shots > 0.0:
                time_to_weapons = max(
                    0.0,
                    (target_distance - player.missile_range) / velocity_diff
                )

            no_dps_duration = min(time_to_drones, time_to_weapons)
            half_dps_duration = max(time_to_drones, time_to_weapons) - no_dps_duration
            half_dps_distance = max(
                player.drone_range,
                player.missile_range,
                player.turret_optimal_range + player.turret_falloff
            )

            half_dps_to_target = player.get_dps_to(
                self.target,
                time_from_start=time_from_start,
                target_distance=half_dps_distance,
                target_velocity=self.target.orbit_velocity or self.target.max_velocity,
                target_angular=target_angular
            )
            if half_dps_to_target * half_dps_duration >= target_hp:
                self.duration = no_dps_duration + (target_hp / half_dps_to_target)
                return

            full_dps_to_target = player.get_dps_to(
                self.target,
                time_from_start=time_from_start,
                target_distance=orbit_range,
                target_velocity=self.target.orbit_velocity or self.target.max_velocity,
                target_angular=target_angular
            )

            self.duration = no_dps_duration + (target_hp - half_dps_to_target * half_dps_duration) / full_dps_to_target

        else:
            dps_to_target = player.get_dps_to(
                self.target,
                time_from_start=time_from_start,
                target_distance=self.target.npc_orbit_range,
                target_velocity=self.target.orbit_velocity or self.target.max_velocity,
                target_angular=target_angular
            )

            self.duration = target_hp / dps_to_target

    def get_dmg_taken_by_player(self, player: PlayerShip, time_from_start, same_orbit_target_duration):
        total_dmg_to_player = 0

        for enemy in self.enemies:
            if enemy == self.orbit_target:
                orbit_range = 2_500
                target_distance = self.target.npc_orbit_range
                velocity_diff = player.max_velocity - self.target.max_velocity
                time_to_orbit = max(0.0, (target_distance - orbit_range) / velocity_diff - same_orbit_target_duration)

                orbit_duration = max(0.0, self.duration - time_to_orbit)

                if time_to_orbit > 0.0:
                    total_dmg_to_player += time_to_orbit * enemy.get_dps_to(
                        player,
                        time_from_start=time_from_start,
                        target_distance=orbit_range,
                        target_velocity=player.max_velocity,
                        target_angular=0.0
                    )
                if orbit_duration > 0.0:
                    total_dmg_to_player += orbit_duration * enemy.get_dps_to(
                        player,
                        time_from_start=time_from_start,
                        target_distance=orbit_range,
                        target_velocity=player.max_velocity * 0.8,
                        target_angular=(player.max_velocity * 0.8) / orbit_range  # todo try different multipliers
                    )

            else:
                distance_from_player = enemy.npc_orbit_range
                if not distance_from_player:
                    print(f"Unknown orbit range for {enemy.name}, using 10_000")
                    distance_from_player = 10_000

                total_dmg_to_player += self.duration * enemy.get_dps_to(
                    player,
                    time_from_start=time_from_start,
                    target_distance=distance_from_player,
                    target_velocity=player.max_velocity,
                    target_angular=(player.max_velocity / distance_from_player) * 0.25  # todo try different multipliers
                )

        return total_dmg_to_player


class FightPlan:
    def __init__(self, player: PlayerShip, enemies: List[AbyssShip]):
        self.player = player

        # todo: filter ewar enemies
        ewar_enemies = []
        not_ewar_enemies = [e for e in enemies if e not in ewar_enemies]
        self.ordered_enemies = not_ewar_enemies + ewar_enemies

    def evaluate_stage_order(self, stages: List[Stage]):
        total_dmg_taken = 0
        total_time = 0

        previous_orbit_target = None
        same_orbit_target_duration = 0.0

        for stage in stages:
            if stage.orbit_target != previous_orbit_target:
                previous_orbit_target = stage.orbit_target
                same_orbit_target_duration = 0.0

            stage.update_stage_duration(self.player, total_time, same_orbit_target_duration)
            total_time += stage.duration
            total_dmg_taken += stage.get_dmg_taken_by_player(self.player, total_time, same_orbit_target_duration)

            same_orbit_target_duration += stage.duration

        return total_dmg_taken

    def build_stage_order(self, target_order, orbit_order):
        stages = []
        remaining_enemies = self.ordered_enemies.copy()

        orbit_order_iter = iter(orbit_order)
        orbit_target = next(orbit_order_iter, None)

        for target in target_order:
            while orbit_target and orbit_target not in remaining_enemies:
                orbit_target = next(orbit_order_iter, None)

            stages.append(Stage(remaining_enemies.copy(), target, orbit_target))
            remaining_enemies.remove(target)

        return stages

    def find_best_target_order(self, orbit_target_order=None):
        if orbit_target_order is None:
            orbit_target_order = []

        best_stage_order = []
        best_target_order = []
        dmg_taken = float("inf")

        for enemy in self.ordered_enemies:
            previous_target_order = best_target_order.copy()
            least_dmg_taken = float("inf")
            for i in range(len(previous_target_order) + 1):
                target_order = previous_target_order.copy()
                target_order.insert(i, enemy)

                stages = self.build_stage_order(target_order, orbit_target_order)
                total_dmg_taken = self.evaluate_stage_order(stages)

                if total_dmg_taken < least_dmg_taken:
                    least_dmg_taken = total_dmg_taken
                    dmg_taken = total_dmg_taken
                    best_target_order = target_order.copy()
                    best_stage_order = stages.copy()

        return best_stage_order, dmg_taken

    def find_best_plan(self):
        best_stage_order, least_dmg_taken = self.find_best_target_order()

        orbit_target_order = []

        for enemy in self.ordered_enemies:
            found_improvement = False

            previous_orbit_order = orbit_target_order.copy()
            for i in range(len(previous_orbit_order) + 1):
                orbit_order = previous_orbit_order.copy()
                orbit_order.insert(i, enemy)

                stages, dmg_taken = self.find_best_target_order(orbit_target_order)

                if dmg_taken < least_dmg_taken:
                    least_dmg_taken = dmg_taken
                    best_stage_order = stages.copy()
                    found_improvement = True

            if not found_improvement:
                break

        return best_stage_order

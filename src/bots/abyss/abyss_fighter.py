import copy
import json
import math
from collections import Counter
from typing import Dict, List

import numpy as np

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import Stage, FightPlan
from src.bots.abyss.player_ship import PlayerShip
from src.bots.abyss.ship import Ship
from src.eve_ui.drones import DroneStatus
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.overview import OverviewEntry
from src.eve_ui.ship_ui import ShipModule
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, wait_for_truthy, move_cursor, click


class AbyssFighter:
    def __init__(self):  # , ui: EveUI):
        self.ui_tree: UITree = None  # UITree.instance()
        self.ui = None  # ui
        self.player: PlayerShip = copy.deepcopy(config.ABYSSAL_PLAYER_SHIP)

        self.enemy_ship_data: List[AbyssShip] = []

        self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH)
        )
        self.precompute_enemy_ship_attributes()

    def get_weather_modifiers(self):
        move_cursor(self.ui.ship_ui.buff_buttons[0].get_center())
        tooltip_panel = wait_for_truthy(lambda: self.ui_tree.find_node(node_type="TooltipPanel", refresh=True), 5)

        percentage_container_1 = self.ui_tree.find_node({"_name": "Row1_Col0"}, root=tooltip_panel)
        penalty_text = self.ui_tree.find_node(node_type="EveLabelMedium", root=percentage_container_1).attrs["_setText"]
        penalty_multiplier = float(penalty_text.split(" ")[0]) / 100

        percentage_container_2 = self.ui_tree.find_node({"_name": "Row2_Col0"}, root=tooltip_panel)
        bonus_text = self.ui_tree.find_node(node_type="EveLabelMedium", root=percentage_container_2).attrs["_setText"]
        bonus_multiplier = float(bonus_text.split(" ")[0]) / 100
        return penalty_multiplier, bonus_multiplier

    def init_room(self):
        self.enemy_ship_data.clear()
        self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH)
        )

        self.player = copy.deepcopy(config.ABYSSAL_PLAYER_SHIP)

        penalty_multiplier, bonus_multiplier = self.get_weather_modifiers()

        for enemy in self.enemy_ship_data:
            if config.ABYSSAL_WEATHER == "Electrical":
                enemy.resist_matrix[0][0] *= penalty_multiplier
                enemy.resist_matrix[1][0] *= penalty_multiplier
                enemy.resist_matrix[2][0] *= penalty_multiplier
            elif config.ABYSSAL_WEATHER == "Exotic":
                enemy.resist_matrix[0][2] *= penalty_multiplier
                enemy.resist_matrix[1][2] *= penalty_multiplier
                enemy.resist_matrix[2][2] *= penalty_multiplier
            elif config.ABYSSAL_WEATHER == "Firestorm":
                enemy.resist_matrix[0][1] *= penalty_multiplier
                enemy.resist_matrix[1][1] *= penalty_multiplier
                enemy.resist_matrix[2][1] *= penalty_multiplier
                armor_damage = enemy.armor_max_hp - enemy.armor_hp
                enemy.armor_max_hp *= bonus_multiplier
                enemy.armor_hp = enemy.armor_max_hp - armor_damage
            elif config.ABYSSAL_WEATHER == "Gamma":
                enemy.resist_matrix[0][3] *= penalty_multiplier
                enemy.resist_matrix[1][3] *= penalty_multiplier
                enemy.resist_matrix[2][3] *= penalty_multiplier
                enemy.shield_max_hp *= bonus_multiplier
            elif config.ABYSSAL_WEATHER == "Dark":
                enemy.turret_optimal_range *= penalty_multiplier
                enemy.turret_falloff *= penalty_multiplier
                enemy.max_velocity *= bonus_multiplier

        self.precompute_enemy_ship_attributes()

    def enemies_on_overview(self):
        enemy_entries = []
        for entry in self.ui.overview.entries:
            enemy = next((ship for ship in self.enemy_ship_data if ship.name == entry.type), None)
            if enemy:
                enemy_entries.append(entry)
        return enemy_entries

    def load_enemy_ships(self, ship_filepath, item_filepath):
        self.enemy_ship_data.clear()
        with open(ship_filepath) as file:
            ships_data = json.load(file)
        with open(item_filepath) as file:
            item_data = json.load(file)
        for key, ship_data in ships_data.items():
            self.enemy_ship_data.append(AbyssShip.from_json(ship_data, item_data))

    def precompute_enemy_ship_attributes(self):
        far_orbit_distance = 15_000
        close_orbit_distance = 2_500

        for enemy in self.enemy_ship_data:
            no_orbit_stage = Stage([enemy], enemy, None)
            no_orbit_stage.update_stage_duration(config.ABYSSAL_PLAYER_SHIP, 0.0, 0.0)
            no_orbit_dmg = no_orbit_stage.get_dmg_taken_by_player(
                config.ABYSSAL_PLAYER_SHIP,
                no_orbit_stage.duration,
                0.0
            )

            enemy.optimal_orbit_range = close_orbit_distance
            close_orbit_stage = Stage([enemy], enemy, enemy)
            close_orbit_stage.update_stage_duration(config.ABYSSAL_PLAYER_SHIP, 0.0, 0.0)
            close_orbit_dmg = close_orbit_stage.get_dmg_taken_by_player(
                config.ABYSSAL_PLAYER_SHIP,
                close_orbit_stage.duration,
                600.0
            )

            enemy.optimal_orbit_range = far_orbit_distance
            far_orbit_stage = Stage([enemy], enemy, enemy)
            far_orbit_stage.update_stage_duration(config.ABYSSAL_PLAYER_SHIP, 0.0, 0.0)
            far_orbit_dmg = far_orbit_stage.get_dmg_taken_by_player(
                config.ABYSSAL_PLAYER_SHIP,
                far_orbit_stage.duration,
                600.0
            )

            enemy.dmg_without_orbit = no_orbit_dmg if no_orbit_stage.duration < np.float64("inf") else np.float64("inf")

            if far_orbit_dmg > close_orbit_dmg:
                enemy.optimal_orbit_range = close_orbit_distance
                enemy.dmg_with_orbit = close_orbit_dmg
            else:
                enemy.optimal_orbit_range = far_orbit_distance
                enemy.dmg_with_orbit = far_orbit_dmg

    def get_current_and_next_stage(self, clear_order):
        enemy_entries = self.enemies_on_overview()
        enemy_amounts_on_overview = Counter([e.type for e in enemy_entries])
        enemy_amounts_required = {}
        clear_order_iter = iter(clear_order[::-1])
        while stage := next(clear_order_iter, None):
            enemy_amount = enemy_amounts_required.get(stage.target.name, 0)
            enemy_amounts_required.update({stage.target.name: enemy_amount + 1})

            if enemy_amounts_on_overview == enemy_amounts_required:
                active_stage: Stage = stage
                next_stage = next(clear_order_iter, None)
                break
        else:
            return None, None

        return active_stage, next_stage

    def manage_navigation(self, clear_order):
        current_stage, _ = self.get_current_and_next_stage(clear_order)
        # todo to be continued

        self.ui.ship_ui.update()
        if "Orbiting" not in self.ui.ship_ui.indication_text or "Bioadaptive" not in self.ui.ship_ui.indication_text:
            self.ui.overview.update()
            bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            bio_cache_entry.orbit(5000)

    def target_current_stage_orbit_target(self, current_stage: Stage):
        if not self.ui.overview.entries:
            if current_stage.orbit_target is None:
                current_orbit_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            else:
                current_orbit_entry = next(
                    e for e in self.ui.overview.entries
                    if current_stage.orbit_target.name == e.type
                )
            current_orbit_entry.target()
            wait_for_truthy(lambda: not [e for e in self.ui.overview.update().entries if e.is_being_targeted], 10)
            self.ui.target_bar.update()

    def target_current_stage_target(self, current_stage: Stage):
        if current_stage.target != current_stage.orbit_target and len(self.ui.overview.entries) < 2:
            current_target_entry = next(
                e for e in self.ui.overview.entries
                if current_stage.target.name == e.type
                and not e.is_targeted_by_me
            )
            current_target_entry.target()
            wait_for_truthy(lambda: not [e for e in self.ui.overview.update().entries if e.is_being_targeted], 10)
            self.ui.target_bar.update()

    def target_next_stage_orbit_target(self, current_stage: Stage, next_stage: Stage):
        if (
            next_stage.orbit_target != current_stage.orbit_target
            and (
                (next_stage.target != next_stage.orbit_target and len(self.ui.overview.entries) < 3)
                or (next_stage.target == next_stage.orbit_target and len(self.ui.overview.entries) < 2)
            )
        ):
            if next_stage.orbit_target is None:
                next_orbit_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            else:
                next_orbit_entry = next(
                    e for e in self.ui.overview.entries
                    if next_stage.orbit_target.name == e.type
                    and not e.is_targeted_by_me
                )
            next_orbit_entry.target()
            wait_for_truthy(lambda: not [e for e in self.ui.overview.update().entries if e.is_being_targeted], 10)
            self.ui.target_bar.update()

    def target_next_stage_target(self, current_stage: Stage, next_stage: Stage):
        if (
            next_stage.target != next_stage.orbit_target
            and next_stage.target != next_stage.orbit_target and len(self.ui.overview.entries) < 3
        ):
            next_target_entry = next(
                e for e in self.ui.overview.entries
                if next_stage.target.name == e.type
                and not e.is_targeted_by_me
            )
            next_target_entry.target()
            wait_for_truthy(lambda: not [e for e in self.ui.overview.update().entries if e.is_being_targeted], 10)
            self.ui.target_bar.update()

    def manage_targeting(self, clear_order):
        self.ui.overview.update()
        self.ui.target_bar.update()

        current_stage, next_stage = self.get_current_and_next_stage(clear_order)
        if current_stage is None:
            return

        self.target_current_stage_orbit_target(current_stage)
        self.target_current_stage_target(current_stage)
        self.target_next_stage_orbit_target(current_stage, next_stage)
        self.target_next_stage_target(current_stage, next_stage)

        # Select current target
        if current_stage.target != current_stage.orbit_target:
            current_target = self.ui.target_bar.targets[1]
        else:
            current_target = self.ui.target_bar.targets[0]
        if not current_target.is_active_target:
            click(current_target.node, pos_y=0.3)

    def manage_modules(self, manage_weapons=True):
        if manage_weapons:
            # Deactivate weapons on non-primary targets
            self.ui.target_bar.update()
            non_active_targets = [t for t in self.ui.target_bar.targets if not t.is_active_target]
            for non_active_target in non_active_targets:
                for weapon_icon in non_active_target.active_weapon_icons:
                    click(weapon_icon)

            # Activate weapons on primary target
            self.ui.ship_ui.update()
            weapon_modules = [self.ui.ship_ui.high_modules[i] for i in config.ABYSSAL_WEAPON_MODULE_INDICES]
            for weapon_module in weapon_modules:
                if weapon_module.active_status != ShipModule.ActiveStatus.not_active:
                    continue
                weapon_module.set_active(True)

        # Activate hardeners
        for i in config.ABYSSAL_HARDENER_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > 0.3)

        # Activate speed modules
        for i in config.ABYSSAL_SPEED_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > 0.5)

    def manage_drones(self):
        self.ui.drones.update()
        drones_to_launch = min(
            len(self.ui.drones.in_bay),
            config.ABYSSAL_MAX_DRONES_IN_SPACE - len(self.ui.drones.in_space)
        )
        if drones_to_launch:
            drones_with_shield = [d for d in self.ui.drones.in_bay if d.shield_percent > 0.9]
            self.ui.drones.launch_drones(drones_with_shield[:drones_to_launch])

        for drone in self.ui.drones.in_space:
            if drone.shield_percent > 0.8:
                continue
            self.ui.drones.recall(drone)

        if not any(d.status == DroneStatus.returning for d in self.ui.drones.in_space):
            self.ui.drones.attack_target()

    def deactivate_modules(self):
        self.ui.ship_ui.update_modules()
        for i, m in self.ui.ship_ui.high_modules.items():
            if i in config.ABYSSAL_WEAPON_MODULE_INDICES:
                continue
            m.set_active(False)
        for _, m in self.ui.ship_ui.medium_modules.items():
            m.set_active(False)
        for _, m in self.ui.ship_ui.low_modules.items():
            m.set_active(False)

    def calculate_clear_order(self) -> List[Stage]:
        enemy_entries = self.enemies_on_overview()

        enemies = [e.type for e in enemy_entries]

        fight_plan = FightPlan(config.ABYSSAL_PLAYER_SHIP, enemies)
        return fight_plan.find_best_plan()

    def open_bio_cache(self):
        potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]
        if len(potential_caches) > 1 or "largeCollidableStructure" not in potential_caches[0].icon:
            return

        bio_cache = potential_caches[0]

        bio_cache.generic_action(OverviewEntry.Action.approach)

        bio_cache.target()
        wait_for_truthy(lambda: self.ui.target_bar.update().targets, 20)

        while len(potential_caches) == 1 and "largeCollidableStructure" in potential_caches[0].icon:
            self.manage_drones()
            active_drones_in_space = any(d.status != DroneStatus.returning for d in self.ui.drones.update().in_space)
            self.manage_modules(manage_weapons=not active_drones_in_space)

            self.ui.overview.update()
            potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]

    def clear_room(self):
        self.ui.overview.update()
        clear_order = self.calculate_clear_order()
        while self.enemies_on_overview():
            self.manage_navigation(clear_order)
            self.manage_targeting(clear_order)
            self.manage_modules()
            self.manage_drones()

            self.ui.overview.update()

        self.open_bio_cache()
        self.deactivate_modules()

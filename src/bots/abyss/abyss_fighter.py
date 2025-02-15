import copy
import json
import math
from typing import Dict, List

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.ship import Ship
from src.bots.abyss.ship_attributes import DamageType
from src.eve_ui.drones import DroneStatus
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.overview import OverviewEntry
from src.eve_ui.ship_ui import ShipModule
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, wait_for_truthy, move_cursor, click


class Stage:
    def __init__(self, enemies, _target, _player):
        self.enemies: List[AbyssShip] = enemies
        self.target: Ship = _target
        self.duration: float = _target.hp / (_player.turret + _player.missile)

    def get_dmg_taken(self, time_from_start, player: Ship):
        total_dmg_to_player = 0

        for enemy in self.enemies:
            total_dmg_to_player += enemy.get_dps_to(player, time_from_start) * self.duration

    @staticmethod
    def calc_total_dmg_to_player(stages: List["Stage"], player: Ship):
        total_dmg_taken = 0
        total_time = 0
        for stage in stages:
            total_time += stage.duration
            total_dmg_taken += stage.get_dmg_taken(total_time, player)
        return total_dmg_taken


class AbyssFighter:
    def __init__(self, ui: EveUI):
        self.ui_tree: UITree = UITree.instance()
        self.ui = ui
        # exported from: https://caldarijoans.streamlit.app/Abyssal_Enemies_Database
        self.enemy_ship_data = []
        self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH)
        )

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

    def manage_navigation(self):
        self.ui.ship_ui.update()
        if "Orbiting" not in self.ui.ship_ui.indication_text or "Bioadaptive" not in self.ui.ship_ui.indication_text:
            self.ui.overview.update()
            bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            bio_cache_entry.orbit(5000)

    def manage_targeting(self, clear_order):
        self.ui.overview.update()
        self.ui.target_bar.update()
        active_targets = 0
        for target_type in clear_order:
            targets = [e for e in self.ui.overview.entries if e.type == target_type]
            for target in targets:
                if active_targets >= config.ABYSSAL_MAX_TARGET_COUNT:
                    return
                active_targets += 1
                if target.is_being_targeted or target.is_targeted_by_me:
                    continue
                target.target()

        self.ui.target_bar.update()
        if not self.ui.target_bar.targets:
            return

        for target_type in clear_order:
            target_to_set_active = next((t for t in self.ui.target_bar.targets if target_type in t.name), None)
            if not target_to_set_active:
                continue
            click(target_to_set_active.node, pos_y=0.3)
            break

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

    def calculate_clear_order(self):
        enemy_entries = self.enemies_on_overview()
        clear_order = []
        for e in enemy_entries:
            if e.type in clear_order:
                continue
            clear_order.append(e.type)
        return clear_order

    def calculate_clear_stages(self, enemy_types, player_ship):
        best_stage_order = []
        best_target_order = []

        enemies = [self.enemy_ship_data[enemy_type] for enemy_type in enemy_types]

        ewar_enemies = [e for e in enemies if e.target_resist_multi or e.missile_multi or e.turret_multi]
        not_ewar_enemies = [e for e in enemies if e not in ewar_enemies]
        ordered_enemies = not_ewar_enemies + ewar_enemies

        for i in range(len(ordered_enemies)):
            previous_target_order = best_target_order.copy()
            least_dmg_taken = float("inf")
            for j in range(len(previous_target_order) + 1):
                target_order = previous_target_order.copy()
                target_order.insert(j, ordered_enemies[i])
                stages = []
                temp_enemies = ordered_enemies.copy()

                for target in target_order:
                    stages.append(Stage(temp_enemies.copy(), target, player_ship))
                    temp_enemies.remove(target)
                dmg_taken = Stage.calc_total_dmg_to_player(stages, player_ship)

                if dmg_taken < least_dmg_taken:
                    least_dmg_taken = dmg_taken
                    best_target_order = target_order.copy()
                    best_stage_order = stages.copy()

        return best_stage_order

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
            self.manage_navigation()
            self.manage_targeting(clear_order)
            self.manage_modules()
            self.manage_drones()

            self.ui.overview.update()

        self.open_bio_cache()
        self.deactivate_modules()

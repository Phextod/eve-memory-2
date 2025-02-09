import json
import time
from typing import Dict

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.ship import Ship
from src.bots.abyss.ship_attributes import DamageType
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.ship_ui import ShipModule
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, wait_for_truthy, move_cursor


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
        enemies = []
        enemy_entries = []
        for entry in self.ui.overview.entries:
            enemy = next((ship for ship in self.enemy_ship_data if ship.name == entry.type), None)
            if enemy:
                enemies.append(enemy)
                enemy_entries.append(entry)
        return enemies, enemy_entries

    def load_enemy_ships(self, ship_filepath, item_filepath):
        self.enemy_ship_data.clear()
        with open(ship_filepath) as file:
            ships_data = json.load(file)
        with open(item_filepath) as file:
            item_data = json.load(file)
        for key, ship_data in ships_data.items():
            self.enemy_ship_data.append(AbyssShip.from_json(ship_data, item_data))

    @staticmethod
    def get_missile_applied_dps(ship: Ship, target_signature_radius, target_velocity):
        # https://wiki.eveuniversity.org/Missile_mechanics
        term1 = target_signature_radius / ship.missile_explosion_radius
        term2 = ((target_signature_radius * ship.missile_explosion_velocity)
                 / (ship.missile_explosion_radius * target_velocity)) ** ship.missile_damage_reduction_factor
        dmg_multiplier = min(1, term1, term2)

        dps = dict()
        for dmg_type, dmg in ship.missile_damage_profile.items():
            rate_of_fire_multiplier = 1 / ship.missile_rate_of_fire
            dps.update({dmg_type: dmg * rate_of_fire_multiplier * dmg_multiplier})
        return dps

    @staticmethod
    def get_turret_applied_dps(ship: Ship, target_signature_radius, target_distance, target_angular=0.0):
        # https://wiki.eveuniversity.org/Turret_mechanics
        tracking_terms = ((target_angular * 40_000) / (ship.turret_tracking * target_signature_radius)) ** 2
        range_terms = (max(0, target_distance - ship.turret_optimal_range) / ship.turret_falloff) ** 2
        hit_chance = 0.5 ** (tracking_terms + range_terms)
        normalised_dmg_multiplier = 0.5 * min(hit_chance ** 2 + 0.98 * hit_chance + 0.0501, 6 * hit_chance)

        dps = dict()
        for dmg_type, dmg in ship.turret_damage_profile.items():
            rate_of_fire_multiplier = 1 / ship.turret_rate_of_fire
            dps.update({dmg_type: dmg * rate_of_fire_multiplier * normalised_dmg_multiplier})
        return dps

    @staticmethod
    def get_time_to_kill(ship: Ship, applied_dps: Dict[DamageType, float]):
        time_to_kill = 0.0
        real_dps_to_shield = 0.0
        for dmg_type, dmg_value in applied_dps.items():
            real_dps_to_shield += dmg_value * ship.shield.resist_profile[dmg_type]
        time_to_kill += ship.shield.hp / real_dps_to_shield

        real_dps_to_armor = 0.0
        for dmg_type, dmg_value in applied_dps.items():
            real_dps_to_armor += dmg_value * ship.armor.resist_profile[dmg_type]
        time_to_kill += ship.armor.hp / real_dps_to_armor

        real_dps_to_structure = 0.0
        for dmg_type, dmg_value in applied_dps.items():
            real_dps_to_structure += dmg_value * ship.structure.resist_profile[dmg_type]
        time_to_kill += ship.structure.hp / real_dps_to_structure

        return time_to_kill

    def clear_room(self):
        self.ui.overview.update_entries()
        bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
        bio_cache_entry.orbit(5000)
        _, enemy_entries = self.enemies_on_overview()
        enemy_count = len(enemy_entries)
        while enemy_count > 0:
            while not sum(1 for e in self.ui.overview.entries if e.is_targeted_by_me):
                enemy_entries[0].target()
                self.ui.overview.update_entries()
                _, enemy_entries = self.enemies_on_overview()
                time.sleep(1)

            print("enemy targeted")

            if self.ui.ship_ui.update().high_modules[0].active_status != ShipModule.ActiveStatus.active:
                self.ui.ship_ui.high_modules[0].set_active(True)

            print("weapons active")

            time.sleep(2)

            self.ui.overview.update_entries()
            _, enemy_entries = self.enemies_on_overview()
            enemy_count = len(enemy_entries)

        bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
        while "largeCollidableStructure" in bio_cache_entry.icon:
            while not bio_cache_entry.is_targeted_by_me:
                bio_cache_entry.target()
                self.ui.overview.update_entries()
                bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
                time.sleep(1)

            print("cache targeted")

            if self.ui.ship_ui.update().high_modules[0].active_status != ShipModule.ActiveStatus.active:
                self.ui.ship_ui.high_modules[0].set_active(True)

            print("weapons active")

            time.sleep(2)

            self.ui.overview.update_entries()
            bio_cache_entry = next(
                (e for e in self.ui.overview.entries if "Cache" in e.type),
                None
            )




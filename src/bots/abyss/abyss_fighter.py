import json
from typing import Dict

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.ship import Ship
from src.bots.abyss.ship_attributes import DamageType
from src.eve_ui.drones import DroneStatus
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.ship_ui import ShipModule
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, wait_for_truthy, move_cursor, click


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

    def manage_navigation(self):
        self.ui.ship_ui.update()
        if "Orbiting" not in self.ui.ship_ui.indication_text or "Bioadaptive" not in self.ui.ship_ui.indication_text:
            self.ui.overview.update_entries()
            bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            bio_cache_entry.orbit(5000)

    def manage_targeting(self, clear_order):
        self.ui.overview.update_entries()
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

        for target_type in clear_order:
            active_target_to_set = next((t for t in self.ui.target_bar.targets if target_type in t.label_texts), None)
            if active_target_to_set:
                click(active_target_to_set.node, pos_y=0.3)
                break

        # while len(self.ui.target_bar.targets) < 2 and len(self.ui.target_bar.targets) < len(enemy_entries):
        #     for enemy_entry in enemy_entries[:2]:
        #         if enemy_entry.is_being_targeted:
        #             continue
        #         enemy_entry.target()
        #     self.ui.overview.update_entries()
        #     self.ui.target_bar.update()
        #     enemy_entries = self.enemies_on_overview()
        #
        # if self.ui.target_bar.targets and not self.ui.target_bar.targets[0].is_active_target:
        #     click(self.ui.target_bar.targets[0].node, pos_y=0.3)
        #
        # if not enemy_entries:
        #     potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]
        #     if len(potential_caches) == 1 and "largeCollidableStructure" in potential_caches[0].icon:
        #         potential_caches[0].target()

    def manage_modules(self):
        self.ui.ship_ui.update()
        weapon_modules = [self.ui.ship_ui.high_modules[i] for i in config.ABYSSAL_WEAPON_MODULE_INDICES]
        for weapon_module in weapon_modules:
            if weapon_module.active_status != ShipModule.ActiveStatus.not_active:
                continue
            weapon_module.set_active(True)

        for i in config.ABYSSAL_HARDENER_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > 0.4)

        for i in config.ABYSSAL_SPEED_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > 0.6)

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

        if any(d.status == DroneStatus.idle for d in self.ui.drones.in_space) \
                and not any(d.status == DroneStatus.returning for d in self.ui.drones.in_space):
            self.ui.drones.attack_target()

    def deactivate_modules(self):
        self.ui.ship_ui.update_modules()
        for _, m in self.ui.ship_ui.high_modules.items():
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
        bio_cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
        clear_order.append(bio_cache_entry.type)
        return clear_order

    def clear_room(self):
        self.ui.overview.update_entries()
        clear_order = self.calculate_clear_order()
        potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]
        while len(potential_caches) == 1 and "largeCollidableStructure" in potential_caches[0].icon:
            self.manage_navigation()
            self.manage_targeting(clear_order)
            self.manage_modules()
            self.manage_drones()

            self.ui.overview.update_entries()
            potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]

        self.deactivate_modules()

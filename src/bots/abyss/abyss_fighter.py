import copy
import json
import time
from collections import Counter
from typing import List

import numpy as np

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import Stage, FightPlan
from src.bots.abyss.player_ship import PlayerShip
from src.eve_ui.context_menu import DistancePresets
from src.eve_ui.drones import DroneStatus
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.ship_ui import ShipModule
from src.utils.ui_tree import UITree
from src.utils.utils import get_path, wait_for_truthy, move_cursor, click, MOUSE_RIGHT


class AbyssFighter:
    def __init__(self, ui: EveUI):
        self.ui_tree: UITree = UITree.instance()
        self.ui = ui
        self.player: PlayerShip = copy.deepcopy(config.ABYSSAL_PLAYER_SHIP)

        self.enemy_ship_data: List[AbyssShip] = []
        self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH),
            get_path(config.ABYSSAL_SHIP_CORRECTIONS_DATA_PATH)
        )
        # self.precompute_enemy_ship_attributes()

    def get_weather_modifiers(self):
        weather_btn = wait_for_truthy(
            lambda: next((b for b in self.ui.ship_ui.update().buff_buttons if "weather" in b.attrs["_name"]), None),
            10
        )
        move_cursor(weather_btn.get_center())
        tooltip_panel = wait_for_truthy(lambda: self.ui_tree.find_node(node_type="TooltipPanel", refresh=True), 5)
        time.sleep(1)
        while True:
            try:
                percentage_container_1 = self.ui_tree.find_node({"_name": "Row1_Col0"}, root=tooltip_panel)
                penalty_text = self.ui_tree.find_node(
                    node_type="EveLabelMedium",
                    root=percentage_container_1
                ).attrs["_setText"]
                penalty_multiplier = 1.0 + float(penalty_text.split(" ")[0]) / 100

                percentage_container_2 = self.ui_tree.find_node({"_name": "Row2_Col0"}, root=tooltip_panel)
                bonus_text = self.ui_tree.find_node(
                    node_type="EveLabelMedium",
                    root=percentage_container_2
                ).attrs["_setText"]
                bonus_multiplier = 1.0 + float(bonus_text.split(" ")[0]) / 100

                return penalty_multiplier, bonus_multiplier
            except AttributeError:
                pass

    def init_room(self):
        self.enemy_ship_data.clear()
        self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH),
            get_path(config.ABYSSAL_SHIP_CORRECTIONS_DATA_PATH)
        )

        self.player = copy.deepcopy(config.ABYSSAL_PLAYER_SHIP)

        penalty_multiplier, bonus_multiplier = self.get_weather_modifiers()

        for enemy in self.enemies_on_overview():
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

    def enemy_entries_on_overview(self):
        enemy_entries = []
        for entry in self.ui.overview.entries:
            enemy = next((ship for ship in self.enemy_ship_data if ship.name == entry.type), None)
            if enemy:
                enemy_entries.append(entry)
        return enemy_entries

    def enemies_on_overview(self):
        enemies = []
        for entry in self.ui.overview.entries:
            enemy = next((ship for ship in self.enemy_ship_data if ship.name == entry.type), None)
            if enemy:
                enemies.append(enemy)
        return enemies

    def load_enemy_ships(self, ship_filepath, item_filepath, ship_corrections_filepath):
        self.enemy_ship_data.clear()
        with open(ship_filepath) as file:
            ships_data = json.load(file)
        with open(ship_corrections_filepath) as file:
            ships_corrections_data = json.load(file)
        with open(item_filepath) as file:
            item_data = json.load(file)

        for key, ship_data in ships_data.items():
            corrections = next((c for k, c in ships_corrections_data.items() if k == key), None)
            if corrections:
                for name, value in corrections.items():
                    ship_data[name] = value
            self.enemy_ship_data.append(AbyssShip.from_json(ship_data, item_data))

    def precompute_enemy_ship_attributes(self):
        far_orbit_distance = 15_000
        close_orbit_distance = 2_500

        for enemy in self.enemies_on_overview():
            no_orbit_stage = Stage([enemy], enemy, None)
            no_orbit_stage.update_stage_duration(self.player, 0.0, 0.0)
            no_orbit_dmg = no_orbit_stage.get_dmg_taken_by_player(
                self.player,
                no_orbit_stage.duration,
                0.0
            )

            enemy.optimal_orbit_range = close_orbit_distance
            close_orbit_stage = Stage([enemy], enemy, enemy)
            close_orbit_stage.update_stage_duration(self.player, 0.0, 0.0)
            close_orbit_dmg = close_orbit_stage.get_dmg_taken_by_player(
                self.player,
                close_orbit_stage.duration,
                30.0
            )

            enemy.optimal_orbit_range = far_orbit_distance
            far_orbit_stage = Stage([enemy], enemy, enemy)
            far_orbit_stage.update_stage_duration(self.player, 0.0, 0.0)
            far_orbit_dmg = far_orbit_stage.get_dmg_taken_by_player(
                self.player,
                far_orbit_stage.duration,
                30.0
            )

            enemy.dmg_without_orbit = no_orbit_dmg if no_orbit_stage.duration < np.float64("inf") else np.float64("inf")

            if far_orbit_dmg > close_orbit_dmg:
                enemy.optimal_orbit_range = close_orbit_distance
                enemy.dmg_with_orbit = close_orbit_dmg
            else:
                enemy.optimal_orbit_range = far_orbit_distance
                enemy.dmg_with_orbit = far_orbit_dmg

    def get_current_and_next_stage(self, clear_order):
        enemies = self.enemies_on_overview()
        enemy_amounts_on_overview = Counter([e.name for e in enemies])
        enemy_amounts_required = {}

        next_stage = None
        for i in range(len(clear_order) - 1, -1, -1):
            active_stage = clear_order[i]
            enemy_amount = enemy_amounts_required.get(active_stage.target.name, 0)
            enemy_amounts_required.update({active_stage.target.name: enemy_amount + 1})

            if enemy_amounts_on_overview == enemy_amounts_required:
                if active_stage.orbit_target is not None and next(
                    (
                        e for e in self.ui.overview.entries
                        if e.tag is not None and e.type == active_stage.orbit_target.name
                    ),
                    None
                ) is None:
                    break
                return active_stage, next_stage

            next_stage = active_stage

        return None, None

    def manage_navigation(self, clear_order):
        self.ui.ship_ui.update_alert()
        cache_distance = next(e for e in self.ui.overview.entries if "Cache" in e.type).distance_in_meters()
        if cache_distance > 55_000:
            if "Approaching" not in self.ui.ship_ui.indication_text:
                self.ui.overview.lock_order()
                self.ui.overview.update()
                cache_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
                self.ui.overview.unlock_order()
                click(cache_entry.node, button=MOUSE_RIGHT)
                self.ui.context_menu.click_safe("Approach")
            return

        if "Orbiting" in self.ui.ship_ui.indication_text or not self.ui.target_bar.targets:
            return

        current_stage: Stage
        self.ui.overview.update()
        current_stage, _ = self.get_current_and_next_stage(clear_order)
        if current_stage is None:
            return

        self.ui.target_bar.update()
        overview_min_tag = min([int(e.tag) if e.tag else 10 for e in self.ui.overview.entries])
        target_bar_min_tag_target = min(self.ui.target_bar.targets, key=lambda x: int(x.tag) if x.tag else 10)

        if target_bar_min_tag_target.tag is not None and int(target_bar_min_tag_target.tag) == overview_min_tag:
            click(target_bar_min_tag_target.node, button=MOUSE_RIGHT, pos_y=0.3)
        else:
            self.ui.overview.lock_order()
            self.ui.overview.update()
            if current_stage.orbit_target is None:
                orbit_target_entry = next(e for e in self.ui.overview.entries if "Cache" in e.type)
            else:
                possible_orbit_targets = [
                    e for e in self.ui.overview.entries
                    if e.type == current_stage.orbit_target.name
                    and e.tag is not None
                ]
                if not possible_orbit_targets:
                    self.ui.overview.unlock_order()
                    return
                orbit_target_entry = min(possible_orbit_targets, key=lambda x: x.tag)

            self.ui.overview.unlock_order()
            click(orbit_target_entry.node, button=MOUSE_RIGHT)

        self.ui.context_menu.click_safe("Orbit", contains=True)
        orbit_distance = 1_000 if current_stage.orbit_target is None else current_stage.orbit_target.optimal_orbit_range
        self.ui.context_menu.click_safe(DistancePresets.closest(orbit_distance)["text"])

    def select_current_target(self, current_stage):
        self.ui.overview.update()
        self.ui.target_bar.update()

        if len(self.ui.target_bar.targets) < 1:
            return False

        if current_stage.target == current_stage.orbit_target:
            min_tag_target = min(
                self.ui.target_bar.targets,
                key=lambda x: int(x.tag) if x.tag else 10
            )
            if min_tag_target.tag == 10:
                return False
            if min_tag_target.is_active_target:
                return True

            click(min_tag_target.node, pos_y=0.3)
            return True
        else:
            target_to_set = next((t for t in self.ui.target_bar.targets if t.tag is None), None)
            if target_to_set is None:
                return False

            if target_to_set.is_active_target:
                return True

            click(target_to_set.node, pos_y=0.3)
            return True

    def target_current_orbit_target(self, current_stage: Stage):
        if current_stage.orbit_target is None:
            return True

        tags = [int(e.tag) for e in self.ui.overview.entries if e.tag is not None]
        if not tags:
            return False
        smallest_tag = min(tags)
        starting_targets = [e for e in self.ui.overview.entries if e.is_targeted_by_me]

        if next((t for t in starting_targets if t.tag == str(smallest_tag)), None) is not None:
            return True

        self.ui.overview.lock_order()
        self.ui.overview.update()
        current_stage_orbit_target_entry = next(t for t in self.ui.overview.entries if t.tag == str(smallest_tag))
        self.ui.overview.unlock_order()
        current_stage_orbit_target_entry.target()
        wait_for_truthy(
            lambda: next((e for e in self.ui.overview.update().entries if e.is_being_targeted), None) is None,
            10
        )

        final_target = next((t for t in self.ui.overview.entries if t.tag == str(smallest_tag)), None)
        return final_target is not None and final_target.is_targeted_by_me

    def target_current_target(self, current_stage: Stage):
        if current_stage.target == current_stage.orbit_target:
            return True

        starting_targets = [e for e in self.ui.overview.entries if e.is_targeted_by_me]

        if current_stage.target.name in [t.name for t in starting_targets if t.tag is None]:
            return True

        self.ui.overview.lock_order()
        self.ui.overview.update()
        current_stage_target_entry = next(
            (t for t in self.ui.overview.entries if t.type == current_stage.target.name and t.tag is None),
            None
        )
        self.ui.overview.unlock_order()
        if current_stage_target_entry is None:
            return False
        current_stage_target_entry.target()
        wait_for_truthy(
            lambda: next((e for e in self.ui.overview.update().entries if e.is_being_targeted), None) is None,
            10
        )

        return next(
            (
                t for t in self.ui.overview.entries
                if t.type == current_stage.target.name
                and t.tag is None
                and t.is_targeted_by_me
            ),
            None
        ) is not None

    def target_next_orbit_target(self, current_stage: Stage, next_stage: Stage):
        if (
            next_stage is None
            or next_stage.orbit_target is None
            or next_stage.orbit_target == current_stage.orbit_target
        ):
            return True

        tags = [int(e.tag) for e in self.ui.overview.entries if e.tag is not None]
        if not tags:
            return False
        smallest_tag = min(tags)
        starting_targets = [e for e in self.ui.overview.entries if e.is_targeted_by_me]

        if next((t for t in starting_targets if t.tag == str(smallest_tag + 1)), None) is not None:
            return True

        self.ui.overview.lock_order()
        self.ui.overview.update()
        next_stage_orbit_target_entry = next(t for t in self.ui.overview.entries if t.tag == str(smallest_tag + 1))
        self.ui.overview.unlock_order()
        next_stage_orbit_target_entry.target()
        wait_for_truthy(
            lambda: next((e for e in self.ui.overview.update().entries if e.is_being_targeted), None) is None,
            10
        )

        return next(t for t in self.ui.overview.entries if t.tag == str(smallest_tag + 1)).is_targeted_by_me

    def target_next_target(self, current_stage: Stage, next_stage: Stage):
        if next_stage is None or next_stage.orbit_target == next_stage.target:
            return True

        starting_targets = [e for e in self.ui.overview.entries if e.is_targeted_by_me]

        if next_stage.target.name != current_stage.target.name:
            if next((t for t in starting_targets if t.type == next_stage.target.name), None) is not None:
                return True
        else:
            if current_stage.target == current_stage.orbit_target:
                if next(
                    (t for t in starting_targets if t.type == next_stage.target.name and t.tag is None), None
                ) is not None:
                    return True
            else:
                if len([e for e in starting_targets if e.name == next_stage.target.name]) == 2:
                    return True

        self.ui.overview.lock_order()
        self.ui.overview.update()
        next_stage_target_entry = next(
            t for t in self.ui.overview.entries
            if t.type == next_stage.target.name
            and t.tag is None
            and not t.is_targeted_by_me
        )
        self.ui.overview.unlock_order()
        next_stage_target_entry.target()
        wait_for_truthy(
            lambda: next((e for e in self.ui.overview.update().entries if e.is_being_targeted), None) is None,
            10
        )

        desired_len = 2 \
            if current_stage.target.name == next_stage.target.name \
            and current_stage.target != current_stage.orbit_target \
            else 1

        return len([
            t for t in self.ui.overview.entries
            if t.type == next_stage.target.name
            and t.tag is None
            and t.is_targeted_by_me
        ]) == desired_len

    def manage_targeting(self, current_stage: Stage, next_stage: Stage):
        """
        Returns True if targeting was successful
        """
        if current_stage is None:
            return True

        self.ui.overview.update()

        if not self.target_current_orbit_target(current_stage):
            return False

        if not self.target_current_target(current_stage):
            return False

        if not self.target_next_orbit_target(current_stage, next_stage):
            return True

        if not self.target_next_target(current_stage, next_stage):
            return True

        self.select_current_target(current_stage)

        return True

    def manage_weapons(self):
        changed_module_status = False

        # Deactivate weapons on non-primary targets
        self.ui.target_bar.update()
        non_active_targets = [t for t in self.ui.target_bar.targets if not t.is_active_target]
        for non_active_target in non_active_targets:
            for weapon_icon in non_active_target.active_weapon_icons:
                # '12_64_6.png' == Web icon
                if '12_64_6.png' in weapon_icon.attrs["_texturePath"]:
                    continue
                click(weapon_icon)

        weapon_modules = [self.ui.ship_ui.high_modules[i] for i in config.ABYSSAL_WEAPON_MODULE_INDICES]
        for weapon_module in weapon_modules:
            if weapon_module.ammo_count == 0:
                click(weapon_module.node, MOUSE_RIGHT)
                self.ui.context_menu.click_safe("Reload all")
                weapon_module.set_state_change_time()
                changed_module_status = True

        self.ui.ship_ui.update_high_slots()

        # Activate weapons on primary target
        weapon_range = max(config.ABYSSAL_PLAYER_SHIP.missile_range,
                           config.ABYSSAL_PLAYER_SHIP.turret_optimal_range)
        if (
            self.ui.target_bar.get_active_target() is not None
            and self.ui.target_bar.get_active_target().distance <= weapon_range
        ):
            for weapon_module in weapon_modules:
                if weapon_module.active_status == ShipModule.ActiveStatus.not_active:
                    if weapon_module.set_active(True):
                        changed_module_status = True

        return changed_module_status

    def manage_hardeners(self, capacitor_limit):
        changed_module_status = False
        for i in config.ABYSSAL_HARDENER_MODULE_INDICES:
            if self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > capacitor_limit):
                changed_module_status = True
        return changed_module_status

    def manage_propulsion(self, capacitor_limit):
        changed_module_status = False
        for i in config.ABYSSAL_SPEED_MODULE_INDICES:
            if self.ui.ship_ui.medium_modules[i].set_active(self.ui.ship_ui.capacitor_percent > capacitor_limit):
                changed_module_status = True
        return changed_module_status

    def select_orbit_target(self):
        self.ui.overview.update()
        min_tag_target_entry = min(
            self.ui.overview.entries,
            key=lambda x: int(x.tag) if x.tag is not None and x.is_targeted_by_me else 10
        )
        if min_tag_target_entry.tag == 10:
            return False

        if min_tag_target_entry.is_active_target:
            return True

        self.ui.overview.lock_order()
        self.ui.overview.update()
        orbit_target_entry = next(e for e in self.ui.overview.entries if e.tag == min_tag_target_entry.tag)
        self.ui.overview.unlock_order()
        orbit_target_entry.target()

        return True

    def manage_webs(self, capacitor_limit, current_stage: Stage):
        if not current_stage or not self.ui.target_bar.targets:
            return False

        web_module_statuses = [
            self.ui.ship_ui.medium_modules[i].active_status == ShipModule.ActiveStatus.active
            for i in config.ABYSSAL_WEB_MODULE_INDICES
        ]
        if all(web_module_statuses):
            return False

        changed_module_status = False

        for i in config.ABYSSAL_WEB_MODULE_INDICES:
            if config.ABYSSAL_WEB_RANGE < self.ui.target_bar.targets[0].distance:
                continue

            if self.ui.ship_ui.capacitor_percent < capacitor_limit:
                if self.ui.ship_ui.medium_modules[i].set_active(False):
                    changed_module_status = True
                continue

            if current_stage.orbit_target:
                if current_stage.target != current_stage.orbit_target:
                    self.select_orbit_target()
                if self.ui.ship_ui.medium_modules[i].set_active(True):
                    changed_module_status = True
                if current_stage.target != current_stage.orbit_target:
                    self.select_current_target(current_stage)

        return changed_module_status

    def manage_shield(self, capacitor_limit):
        missing_shield_hp = (1 - self.ui.ship_ui.shield_percent) * config.ABYSSAL_PLAYER_SHIP.shield_max_hp
        should_turn_off = (
            missing_shield_hp < config.ABYSSAL_SHIELD_BOOSTER_AMOUNT
            or self.ui.ship_ui.capacitor_percent < capacitor_limit
        )
        for i in config.ABYSSAL_SHIELD_BOOSTER_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(not should_turn_off)

    def manage_modules(self, clear_order, targeting_successful):
        self.ui.ship_ui.update_modules()
        self.ui.ship_ui.update_capacitor_percent()
        self.ui.ship_ui.update_hp()

        current_stage, _ = self.get_current_and_next_stage(clear_order)

        if not targeting_successful:
            self.manage_propulsion(0.4)
        else:
            self.manage_weapons()
            self.manage_hardeners(0.25)
            self.manage_propulsion(0.4)
            self.manage_webs(0.3, current_stage)
            self.manage_shield(0.25)

    def manage_drones(self, targeting_successful):
        self.ui.drones.update()

        enemies = self.enemies_on_overview()
        drone_danger = (
                len([e for e in enemies if "Skybreaker" in e.name]) > 0
                or len([e for e in self.ui.overview.entries if e.is_only_targeting]) > 0
                or not targeting_successful
        )
        if drone_danger and self.ui.drones.in_space:
            self.ui.drones.recall_all()
            return

        drones_to_launch = min(
            len(self.ui.drones.in_bay),
            config.ABYSSAL_MAX_DRONES_IN_SPACE - len(self.ui.drones.in_space)
        )
        if drones_to_launch:
            drones_with_shield = [d for d in self.ui.drones.in_bay if d.shield_percent > 0.9]
            self.ui.drones.launch_drones(drones_with_shield[:drones_to_launch])

        drone_recalled = False
        for drone in self.ui.drones.in_space:
            if drone.shield_percent > 0.8:
                continue
            self.ui.drones.recall(drone)
            drone_recalled = True

        self.ui.target_bar.update()
        if (
            not drone_recalled
            and not any(d.status == DroneStatus.returning for d in self.ui.drones.in_space)
            and self.ui.target_bar.get_active_target() is not None
            and self.ui.target_bar.get_active_target().distance < config.ABYSSAL_PLAYER_SHIP.drone_range
        ):
            self.ui.drones.attack_target()

    def set_orbit_tags(self, clear_order: List[Stage]):
        orbit_targets = []
        for stage in clear_order:
            if stage.orbit_target is not None and stage.orbit_target not in orbit_targets:
                orbit_targets.append(stage.orbit_target)

        if not clear_order:
            return

        self.ui.overview.lock_order()
        self.ui.overview.update()
        self.ui.overview.unlock_order()
        for i, target in enumerate(orbit_targets):
            target_entry = next(e for e in self.ui.overview.entries if target.name == e.type and e.tag is None)
            target_entry.set_tag(str(i))

        wait_for_truthy(
            lambda: max(
                [int(e.tag) if e.tag else -1 for e in self.ui.overview.update().entries]
            ) == len(orbit_targets) - 1,
            10
        )

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
        enemies = self.enemies_on_overview()

        fight_plan = FightPlan(config.ABYSSAL_PLAYER_SHIP, enemies)
        return fight_plan.find_best_plan()

    def open_bio_cache(self):
        self.ui.overview.lock_order()
        self.ui.overview.update()
        potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]
        if len(potential_caches) > 1 or "largeCollidableStructure" not in potential_caches[0].icon:
            return

        bio_cache = potential_caches[0]

        self.ui.overview.unlock_order()
        bio_cache.target()
        wait_for_truthy(lambda: self.ui.target_bar.update().targets, 20)

        self.ui.target_bar.update()
        click(self.ui.target_bar.targets[0].node, button=MOUSE_RIGHT, pos_y=0.3)
        self.ui.context_menu.click("Approach")

        weapon_max_range = max(
            config.ABYSSAL_PLAYER_SHIP.missile_range,
            config.ABYSSAL_PLAYER_SHIP.turret_optimal_range
        )

        while len(potential_caches) == 1 and "largeCollidableStructure" in potential_caches[0].icon:
            self.ui.target_bar.update()
            self.ui.ship_ui.update_modules()
            self.ui.ship_ui.update_capacitor_percent()

            self.manage_drones(True)
            self.manage_propulsion(0.5)
            if self.ui.target_bar.targets and self.ui.target_bar.targets[0].distance < weapon_max_range / 2:
                self.manage_weapons()

            self.ui.overview.update()
            potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]

    def clear_room(self):
        self.ui.overview.update()
        self.init_room()

        clear_order = self.calculate_clear_order()
        for stage in clear_order:
            print(f"target:{stage.target.name}({id(stage.target)},"
                  f" orbit: {stage.orbit_target.name if stage.orbit_target else 'None'}"
                  f"({id(stage.orbit_target) if stage.orbit_target else ''})")

        self.set_orbit_tags(clear_order)

        temp_e = self.enemies_on_overview()
        while temp_e:
            self.ui.overview.update()
            current_stage, next_stage = self.get_current_and_next_stage(clear_order)
            if current_stage is None:
                if self.enemies_on_overview():
                    clear_order = self.calculate_clear_order()
                else:
                    break

            targeting_successful = self.manage_targeting(current_stage, next_stage)

            self.ui.target_bar.update()

            self.manage_navigation(clear_order)
            self.manage_modules(clear_order, targeting_successful)
            self.manage_drones(targeting_successful)
            temp_e = self.enemies_on_overview()

        self.deactivate_modules()
        self.open_bio_cache()
        self.deactivate_modules()

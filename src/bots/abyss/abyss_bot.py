import time

import pyautogui

from src import config
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.overview import OverviewEntry
from src.eve_ui.timers import TimerNames
from src.utils.ui_tree import UITree
from src.utils.utils import wait_for_truthy, click, MOUSE_RIGHT, move_cursor


class AbyssBot:
    def __init__(self, ui: EveUI):
        self.ui = ui
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.ui_tree: UITree = UITree.instance()
        self.abyss_fighter = AbyssFighter(ui)

    def clear_room(self):
        self.abyss_fighter.clear_room()

    def loot(self):
        """
        :return: True if there is loot to be taken, False if looting is done
        """
        self.ui.overview.update_entries()
        potential_caches = [e for e in self.ui.overview.entries if "Cache" in e.type]
        if len(potential_caches) != 1:
            return True

        if "Looted" in potential_caches[0].icon:
            return False

        potential_caches[0].generic_action(OverviewEntry.Action.open_cargo)
        return not self.ui.inventory.loot_all()

    def approach_jump_gate(self):
        jump_gate_entry = next(e for e in self.ui.overview.entries if "Conduit" in e.type)
        jump_gate_entry.generic_action(OverviewEntry.Action.approach)

        self.ui.ship_ui.update()
        should_speed = self.ui.ship_ui.capacitor_percent > 0.8
        for i in config.ABYSSAL_SPEED_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(should_speed)

    def prepare_for_next_room(self, current_room):
        is_prepared = True

        # reload weapons
        for i, high_module in self.ui.ship_ui.high_modules.items():
            if high_module.ammo_count == config.ABYSSAL_AMMO_PER_WEAPON[i]:
                continue
            click(high_module.node, MOUSE_RIGHT)
            self.context_menu.click_safe("Reload all", 5)
            is_prepared = False

        # repair
        # todo later

        # recall drones
        self.ui.drones.update()
        if self.ui.drones.in_space:
            is_prepared = False
            self.ui.drones.recall_all()

        # wait for cap
        self.ui.ship_ui.update()
        if self.ui.ship_ui.capacitor_percent < 0.8 and current_room < 3:
            is_prepared = False

        return is_prepared

    def jump_to_next_room(self):
        jump_gate_entry = next(e for e in self.ui.overview.entries if "Conduit" in e.type)
        jump_gate_entry.generic_action(OverviewEntry.Action.activate_gate)

        self.ui.ship_ui.update()
        should_speed = self.ui.ship_ui.capacitor_percent > 0.8
        for i in config.ABYSSAL_SPEED_MODULE_INDICES:
            self.ui.ship_ui.medium_modules[i].set_active(should_speed)

        wait_for_truthy(
            lambda: (
                (self.ui.overview.update_entries() and self.abyss_fighter.enemies_on_overview())
                or TimerNames.abyssal.value not in self.ui.timers.update().timers
            ),
            60
        )

    def do_abyss(self):
        # self.clear_room()
        # while self.loot():
        #     self.prepare_for_next_room(0)
        # self.approach_jump_gate()
        # wait_for_truthy(lambda: self.prepare_for_next_room(0), 30)
        # self.jump_to_next_room()

        current_room = 1
        while current_room <= 3:
            self.clear_room()
            while self.loot():
                self.prepare_for_next_room(current_room)
            self.approach_jump_gate()
            wait_for_truthy(lambda: self.prepare_for_next_room(current_room), 30)
            self.jump_to_next_room()
            current_room += 1
            time.sleep(5)

    def undock(self):
        self.ui.station_window.undock()
        wait_for_truthy(lambda: TimerNames.invulnerable in self.ui.timers.update().timers, 10)

    def use_filament(self):
        self.ui.inventory.search_for(f"{config.ABYSSAL_DIFFICULTY} {config.ABYSSAL_WEATHER}")
        self.ui.inventory.update_items()

        click(self.ui.inventory.items[0].node, MOUSE_RIGHT)
        self.context_menu.click_safe(f"Use {config.ABYSSAL_DIFFICULTY} {config.ABYSSAL_WEATHER}", 5, contains=True)

        activation_window = self.ui_tree.find_node(node_type="KeyActivationWindow")
        activate_btn = self.ui_tree.find_node(node_type="ActivateButton", root=activation_window)
        click(activate_btn)

        wait_for_truthy(lambda: TimerNames.abyssal.value in self.ui.timers.update().timers, 30)
        wait_for_truthy(lambda: self.ui.overview.update_entries() and self.abyss_fighter.enemies_on_overview(), 30)

    def warp_to_safe_spot(self):
        safe_spot_entry = self.ui.locations.get_entry(config.ABYSSAL_SAFE_SPOT_LOCATION)
        click(safe_spot_entry, MOUSE_RIGHT)

        destination_set = False
        warping = False
        while not destination_set and not warping:
            destination_set = self.context_menu.click("Set Destination")
            warping = self.context_menu.click("Warp to Within", contains=True)

        if destination_set:
            self.ui.route.autopilot(self.ui.ship_ui, self.ui.timers)
            click(safe_spot_entry, MOUSE_RIGHT)
            self.context_menu.click_safe("Warp to Within", 5, contains=True)

        wait_for_truthy(lambda: not self.ui.ship_ui.update().is_warping and self.ui.ship_ui.speed < 10, 60)

    def dock_home_base(self):
        base_entry = self.ui.locations.get_entry(config.ABYSSAL_BASE_LOCATION)
        click(base_entry, MOUSE_RIGHT)
        if self.context_menu.click_safe("Set Destination", 5):
            self.ui.route.autopilot(self.ui.ship_ui, self.ui.timers)

    def drop_off_loot(self):
        click(self.ui.inventory.active_ship_hangar)
        self.ui.inventory.stack_all()
        self.ui.inventory.update()

        pyautogui.keyDown("ctrl")
        item_to_move = None
        for item in self.ui.inventory.items:
            if item.name in config.ABYSSAL_SUPPLIES.keys():
                continue
            click(item.node, pos_y=0.1)
            if item_to_move is None:
                item_to_move = item.node
        pyautogui.keyUp("ctrl")

        if item_to_move:
            target_hangar = self.ui.inventory.main_station_hangar
            self.ui.inventory.move_item(item_to_move, target_hangar)

        for item_name in config.ABYSSAL_SUPPLIES.keys():
            item_in_ship = next((i for i in self.ui.inventory.items if i.name == item_name), None)
            if not item_in_ship:
                continue

            amount_to_drop_off = item_in_ship.quantity - config.ABYSSAL_SUPPLIES[item_name][1]
            if amount_to_drop_off <= 0:
                continue

            target_hangar = self.ui.inventory.main_station_hangar
            self.ui.inventory.move_item(item_in_ship.node, target_hangar, amount_to_drop_off)

    def pick_up_supplies(self):
        click(self.ui.inventory.active_ship_hangar)
        self.ui.inventory.stack_all()
        self.ui.inventory.update()

        supplies_in_ship = dict()
        for item_name in config.ABYSSAL_SUPPLIES.keys():
            amount_in_ship = next((i.quantity for i in self.ui.inventory.items if i.name == item_name), 0)
            supplies_in_ship.update({item_name: amount_in_ship})

        click(self.ui.inventory.main_station_hangar)
        self.ui.inventory.stack_all()

        for item_name, amount_in_ship in supplies_in_ship.items():
            amount_for_max = config.ABYSSAL_SUPPLIES[item_name][1] - amount_in_ship
            if amount_for_max <= 0:
                continue
            amount_for_min = config.ABYSSAL_SUPPLIES[item_name][0] - amount_in_ship

            self.ui.inventory.search_for(item_name)
            self.ui.inventory.update()

            amount_in_hangar = next((i.quantity for i in self.ui.inventory.items if i.name == item_name), 0)

            if amount_in_hangar < amount_for_min:
                raise Exception("Not enough supply")

            amount_to_move = min(amount_for_max, amount_in_hangar)
            if amount_to_move > 0:
                self.ui.inventory.move_item(
                    self.ui.inventory.items[0].node,
                    self.ui.inventory.active_ship_hangar,
                    amount_to_move,
                )

    def pick_up_drones(self):
        click(self.ui.inventory.active_ship_drone_bay)
        self.ui.inventory.update_items()

        drones_to_pick_up = dict()
        for drone_type, required_quantity in config.ABYSSAL_DRONES.items():
            quantity_in_bay = sum([i.quantity for i in self.ui.inventory.items if i.name == drone_type])
            drones_to_pick_up.update({drone_type: required_quantity - quantity_in_bay})

        click(self.ui.inventory.main_station_hangar)
        self.ui.inventory.stack_all()
        self.ui.inventory.update_items()

        for drone_type, pick_up_quantity in drones_to_pick_up.items():
            if pick_up_quantity <= 0:
                continue

            self.ui.inventory.search_for(drone_type)
            self.ui.inventory.update_items()

            if not self.ui.inventory.items:
                raise Exception("Not enough drones")

            item_node = self.ui.inventory.items[0].node
            self.ui.inventory.move_item(item_node, self.ui.inventory.active_ship_drone_bay, pick_up_quantity)

    def repair(self):
        self.ui.inventory.repair_active_ship()

    def is_reset_needed(self):
        # Drones
        self.ui.drones.update()
        for drone_name, drone_amount in config.ABYSSAL_DRONES:
            drone_amount_in_bay = sum(1 for d in self.ui.drones.in_bay if d.name == drone_name)
            if drone_amount_in_bay < drone_amount:
                return True
        for drone in self.ui.drones.in_bay:
            if drone.armor_percent < 0.9 or drone.structure_percent < 1:
                return True

        # Ship
        self.ui.ship_ui.update()
        shield = self.ui.ship_ui.shield_percent
        armor = self.ui.ship_ui.armor_percent
        structure = self.ui.ship_ui.structure_percent
        if (
            (config.ABYSSAL_IS_SHIELD_TANK and (shield < 0.7 or armor < 0.9))
            or (config.ABYSSAL_IS_ARMOR_TANK and (armor < 0.7 or structure < 0.9))
            or (config.ABYSSAL_IS_STRUCTURE_TANK and structure < 0.7)
        ):
            return True

        # Inventory
        self.ui.inventory.stack_all()
        self.ui.inventory.update()
        if self.ui.inventory.capacity_max / self.ui.inventory.capacity_filled > 0.8:
            return True

        for supply_name, supply_amounts in config.ABYSSAL_SUPPLIES:
            self.ui.inventory.search_for(supply_name)
            self.ui.inventory.update_items()
            if not self.ui.inventory.items:
                return True
            if self.ui.inventory.items[0].quantity < supply_amounts[0]:
                return True

        return False

    def move_a_bit(self):
        # todo
        self.ui.ship_ui.full_speed()
        time.sleep(40)

    def run(self):
        self.drop_off_loot()
        self.pick_up_supplies()
        self.pick_up_drones()
        self.repair()
        self.undock()
        self.warp_to_safe_spot()
        while True:
            self.use_filament()
            self.do_abyss()
            if self.is_reset_needed():
                self.dock_home_base()
                self.drop_off_loot()
                self.pick_up_supplies()
                self.pick_up_drones()
                self.repair()
                self.undock()
                self.warp_to_safe_spot()
            else:
                self.move_a_bit()


if __name__ == "__main__":
    eve_ui = EveUI()
    bot = AbyssBot(eve_ui)
    print("ready")
    bot.run()

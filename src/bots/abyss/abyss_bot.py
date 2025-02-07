import pyautogui

from src import config
from src.eve_ui.context_menu import ContextMenu
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.overview import OverviewEntry
from src.eve_ui.timers import TimerNames
from src.utils.ui_tree import UITree
from src.utils.utils import wait_for_truthy, click, MOUSE_RIGHT


class AbyssBot:
    def __init__(self, ui: EveUI):
        self.ui = ui
        self.context_menu: ContextMenu = ContextMenu.instance()
        self.ui_tree: UITree = UITree.instance()

    def clear_room(self):
        # TODO: FML
        pass

    def loot(self):
        bio_cache_entry = next(e for e in self.ui.overview.entries if e.type == "Triglavian Bioadaptive Cache")
        bio_cache_entry.generic_action(OverviewEntry.Action.open_cargo)
        wait_for_truthy(lambda: self.ui.inventory.loot_all(), 30)

    def prepare_for_next_room(self, room_count):
        # approach gate
        jump_gate_entry = next(e for e in self.ui.overview.entries if "Conduit (Triglavian)" in e.type)
        jump_gate_entry.generic_action(OverviewEntry.Action.approach)

        # reload weapons
        for high_module in self.ui.ship_ui.high_modules:
            click(high_module.node, MOUSE_RIGHT)
            self.context_menu.click_safe("Reload all", 5)

        # repair
        # todo later

        # recall drones
        self.ui.drones.update()
        if self.ui.drones.in_space:
            self.ui.drones.safe_recall_all()

        # wait for cap (based on time)
        # todo later

    def jump_to_next_room(self):
        jump_gate_entry = next(e for e in self.ui.overview.entries if "Conduit (Triglavian)" in e.type)
        jump_gate_entry.generic_action(OverviewEntry.Action.activate_gate)

    def do_abyss(self):
        room_count = 1
        while room_count <= 3:
            self.clear_room()
            self.loot()
            self.prepare_for_next_room(room_count)
            self.jump_to_next_room()
            room_count += 1

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

    def warp_to_safe_spot(self):
        safe_spot_entry = self.ui.locations.get_entry(config.ABYSSAL_SAFE_SPOT_LOCATION)
        click(safe_spot_entry, MOUSE_RIGHT)
        if self.context_menu.click_safe("Set Destination", 5):
            self.ui.route.autopilot(self.ui.ship_ui, self.ui.timers)
            click(safe_spot_entry, MOUSE_RIGHT)
        self.context_menu.click_safe("Warp to Within", 5, contains=True)

        wait_for_truthy(lambda: not self.ui.ship_ui.update().is_warping, 60)

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
            item_in_ship = next(i for i in self.ui.inventory.items if i.name == item_name)
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

        for item_name, amount_in_ship in supplies_in_ship:
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
            self.ui.inventory.move_item(
                self.ui.inventory.items[0],
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

    def run(self):
        self.undock()
        self.warp_to_safe_spot()
        self.use_filament()

        # do abyss
        self.do_abyss()

        self.dock_home_base()
        self.drop_off_loot()
        self.pick_up_supplies()
        self.pick_up_drones()
        self.repair()


if __name__ == "__main__":
    eve_ui = EveUI()
    bot = AbyssBot(eve_ui)
    print("ready")
    bot.run()

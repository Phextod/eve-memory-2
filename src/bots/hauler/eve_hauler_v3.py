import time

import pyautogui

from src import config
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.timers import TimerNames
from src.utils.ui_tree import UITree
from src.utils.utils import log, click, drag_and_drop, wait_for_truthy, get_path, init_logger, \
    start_inactivity_watchdog, reset_inactivity_timer


class Hauler:
    def __init__(self, ui: EveUI):
        self.ui = ui
        self.ui_tree: UITree = UITree.instance()

    def get_mission(self):
        btn_request = None
        btn_view = None
        while not (btn_request or btn_view):
            self.ui.agent_window.update_buttons()
            if btn_request := self.ui.agent_window.get_button("Request Mission"):
                continue
            btn_view = self.ui.agent_window.get_button("View Mission")

        while not self.ui.agent_window.update_buttons().get_button("Accept"):
            if btn_request:
                click(btn_request)
            else:
                click(btn_view)

        while True:
            self.ui.route.update()
            self.ui.route.clear()
            while len(self.ui.route.update().route_sprites) == 0:
                self.ui.agent_window.add_drop_off_waypoint()

            mission_route_length = len(self.ui.route.route_sprites)

            standing = self.ui.agent_window.update_html_content().get_effective_standing()
            min_standing = min(config.HAULER_MAX_ROUTE_LENGTHS, key=lambda x: x[0])[0]
            max_route_length = max(
                [(s, l) for s, l in config.HAULER_MAX_ROUTE_LENGTHS if s <= max(min_standing, standing)],
                key=lambda x: x[0]
            )[1]

            if mission_route_length > max_route_length:
                click(self.ui.agent_window.update_buttons().get_button("Decline"))
                time.sleep(1)
                while self.ui_tree.find_node(node_type="MessageBox"):
                    pyautogui.press("enter")
                    time.sleep(1)
                click(self.ui.agent_window.update_buttons().get_button("Request Mission"))
                continue

            while len(self.ui.route.update().route_sprites) != mission_route_length * 2:
                self.ui.agent_window.add_pickup_waypoint()
            break

        log(f"Mission length: {len(self.ui.route.route_sprites)}")

        is_mission_accepted = False
        while not is_mission_accepted:
            btn_accept = self.ui.agent_window.update_buttons().get_button("Accept")
            if btn_accept:
                click(btn_accept, wait_after=0.5)
            click(self.ui.inventory.main_station_hangar, wait_after=0.5)
            self.ui.inventory.update_items()
            is_mission_accepted = len(self.ui.inventory.items) > 0

    def is_item_in_ship(self):
        is_ship_hangar_open = self.ui.inventory.update_capacity().capacity_max == config.HAULER_SHIP_MAX_CAPACITY
        while not is_ship_hangar_open:
            click(self.ui.inventory.active_ship_hangar)
            is_ship_hangar_open = self.ui.inventory.update_capacity().capacity_max == config.HAULER_SHIP_MAX_CAPACITY

        self.ui.inventory.update_items()
        return len(self.ui.inventory.items) > 0 and self.ui.inventory.capacity_filled != 0

    def move_item_to_ship(self):
        should_move = True
        tried_moving_once = False
        while should_move:
            click(self.ui.inventory.main_station_hangar)
            self.ui.inventory.update_items()
            if not self.ui.inventory.items:
                should_move = not self.is_item_in_ship() or not tried_moving_once
                continue
            drag_and_drop(
                self.ui.inventory.items[0].node.get_center(),
                self.ui.inventory.active_ship_hangar.get_center()
            )
            tried_moving_once = True

            should_move = not self.is_item_in_ship()

    def do_mission(self):
        while self.ui.station_window.is_docked():
            self.ui.station_window.undock()
            time.sleep(1)
        wait_for_truthy(lambda: TimerNames.invulnerable.value in self.ui.timers.update().timers, 30)
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)
        while self.is_item_in_ship():
            btn_complete = self.ui.agent_window.update_buttons().get_button("Complete Mission")
            if btn_complete:
                click(btn_complete)
            time.sleep(1)

    def return_to_origin(self):
        self.ui.station_window.undock()
        wait_for_truthy(lambda: TimerNames.invulnerable.value in self.ui.timers.update().timers, 30)
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)

    def run(self):
        self.get_mission()
        self.move_item_to_ship()
        self.do_mission()
        self.return_to_origin()


if __name__ == "__main__":
    init_logger(config.HAULER_LOG_FILE_PATH)
    hauler = Hauler(EveUI(do_setup=False))
    timer_dict, lock = start_inactivity_watchdog(max_inactivity_time=60 * 10)
    mission_counter = 0
    while True:
        reset_inactivity_timer(timer_dict, lock)
        mission_counter += 1
        start = time.time()

        hauler.run()

        log(f"Mission {mission_counter} completed in {time.time() - start:.0f}s")

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
        btn_accept = None
        while not (btn_request or btn_view or btn_accept):
            self.ui.agent_window.update_buttons()
            if btn_request := self.ui.agent_window.get_button("Request Mission"):
                continue
            if btn_view := self.ui.agent_window.get_button("View Mission"):
                continue
            btn_accept = self.ui.agent_window.get_button("Accept")

        while not (btn_accept or self.ui.agent_window.update_buttons().get_button("Accept")):
            if btn_request:
                click(btn_request)
            else:
                click(btn_view)

        while True:
            self.ui.route.clear()

            self.ui.agent_window.update_html_content()
            mission_title = self.ui.agent_window.get_mission_title()
            while not mission_title:
                self.ui.agent_window.update_html_content()
                mission_title = self.ui.agent_window.get_mission_title()

            mission_route_length = 0
            max_route_length = -1

            if mission_title not in config.HAULER_EXCLUDED_MISSION_TITLES:
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

                while not self.ui.agent_window.update_buttons().get_button("Request Mission"):
                    message_box = self.ui_tree.find_node(node_type="MessageBox")
                    if message_box:
                        checkbox = self.ui_tree.find_node(node_type="Checkbox", root=message_box, refresh=False)
                        if checkbox:
                            click(checkbox)
                        pyautogui.press("enter")

                wait_for_truthy(lambda: not self.ui.agent_window.update_buttons().get_button("Request Mission"), 10)

                while not self.ui.agent_window.update_buttons().get_button("Accept"):
                    btn_request = self.ui.agent_window.get_button("Request Mission")
                    if btn_request:
                        click(btn_request)
                        wait_for_truthy(lambda: self.ui.agent_window.update_buttons().get_button("Accept"), 1)

                continue

            while len(self.ui.route.update().route_sprites) != mission_route_length * 2:
                self.ui.agent_window.add_pickup_waypoint()
            break

        log(f"Mission length: {len(self.ui.route.route_sprites)}")

        self.ui.agent_window.update_buttons()
        while not self.ui.inventory.items or not self.ui.agent_window.get_button("Complete Mission"):
            btn_accept = self.ui.agent_window.get_button("Accept")
            if btn_accept:
                click(btn_accept, wait_after=0.5)
            click(self.ui.inventory.main_station_hangar, wait_after=0.5)
            self.ui.inventory.update()
            self.ui.agent_window.update_buttons()

        return self.ui.agent_window.get_mission_rewards()

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
        wait_for_truthy(lambda: TimerNames.invulnerable.value in self.ui.timers.update().timers, 30)
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)
        while self.is_item_in_ship():
            btn_complete = self.ui.agent_window.update_buttons().get_button("Complete Mission")
            if btn_complete:
                click(btn_complete)
            wait_for_truthy(lambda: not self.is_item_in_ship(), 1)

    def return_to_origin(self):
        while self.ui.station_window.is_docked():
            self.ui.station_window.undock()
        wait_for_truthy(lambda: TimerNames.invulnerable.value in self.ui.timers.update().timers, 30)
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)

    def run(self):
        rewards = self.get_mission()
        self.move_item_to_ship()
        self.do_mission()
        self.return_to_origin()

        return rewards


if __name__ == "__main__":
    init_logger(config.HAULER_LOG_FILE_PATH)
    hauler = Hauler(EveUI(do_setup=False))
    timer_dict, lock = start_inactivity_watchdog(max_inactivity_time=60 * 10)
    mission_counter = 0
    total_mission_time = 0
    total_reward_value = 0

    while True:
        reset_inactivity_timer(timer_dict, lock)
        mission_counter += 1
        start = time.time()

        reward_isk, reward_loyalty_points = hauler.run()

        reward_isk_value = reward_isk + reward_loyalty_points * config.HAULER_ISK_PER_LP
        mission_time = time.time() - start
        log(f"Mission {mission_counter} completed in {mission_time:.0f}s, "
            f"for {'{:,}'.format(reward_isk_value).replace(',', ' ')} ISK reward value")

        total_reward_value += reward_isk_value
        total_mission_time += mission_time
        isk_per_hour = int(total_reward_value / (total_mission_time / (60 * 60)))
        log(f"Current total rewards: {'{:,}'.format(total_reward_value).replace(',', ' ')} ISK")
        log(f"Current ISK/Hour: {'{:,}'.format(isk_per_hour).replace(',', ' ')}")


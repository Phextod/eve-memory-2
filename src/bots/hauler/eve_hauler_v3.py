import time

from src import config
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.timers import TimerNames
from src.utils.utils import log, click, drag_and_drop, wait_for_truthy, get_path


class Hauler:
    def __init__(self, ui: EveUI):
        self.ui = ui

    def get_mission(self):
        btn_request = None
        btn_view = None
        while not (btn_request or btn_view):
            if btn_request := self.ui.agent_window.get_button(get_path('images/btn_request_mission.png'), 0.7):
                continue
            btn_view = self.ui.agent_window.get_button(get_path('images/btn_view_mission.png'), 0.7)

        if btn_request:
            click(btn_request)
        else:
            click(btn_view)

        self.ui.route.update()
        self.ui.route.clear()
        wait_for_truthy(lambda: self.ui.agent_window.get_button(get_path('images/btn_accept.png'), 0.7), 5)
        self.ui.agent_window.add_drop_off_waypoint()
        self.ui.route.update()
        while len(self.ui.route.route_sprites) > config.HAULER_MAX_ROUTE_LENGTH:
            click(self.ui.agent_window.get_button(get_path('images/btn_decline.png'), 0.7))

            click(self.ui.agent_window.get_button(get_path('images/btn_request_mission.png'), 0.7))
            self.ui.route.clear()
            self.ui.agent_window.add_drop_off_waypoint()

        print(f"Mission length: {len(self.ui.route.route_sprites)}")
        self.ui.agent_window.add_pickup_waypoint()
        click(self.ui.agent_window.get_button(get_path('images/btn_accept.png'), 0.7))

    def is_item_in_ship(self):
        click(self.ui.inventory.active_ship_hangar)
        self.ui.inventory.update_items()
        if self.ui.inventory.items:
            return True
        return False

    def move_item_to_ship(self):
        should_move = True
        while should_move:
            click(self.ui.inventory.main_station_hangar)
            self.ui.inventory.update_items()
            if not self.ui.inventory.items:
                continue
            drag_and_drop(
                self.ui.inventory.items[0].node.get_center(),
                self.ui.inventory.active_ship_hangar.get_center()
            )

            should_move = not self.is_item_in_ship()

    def do_mission(self):
        self.ui.station_window.undock()
        wait_for_truthy(lambda: TimerNames.invulnerable.value in self.ui.timers.update().timers, 30)
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)
        btn_complete = wait_for_truthy(
            lambda: self.ui.agent_window.get_button(get_path('images/btn_complete_mission.png'), 0.7),
            5
        )
        click(btn_complete)

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
    hauler = Hauler(EveUI())
    mission_counter = 0
    while True:
        mission_counter += 1
        start = time.time()

        hauler.run()

        print(f"Mission {mission_counter} completed in {time.time() - start:.0f}s")

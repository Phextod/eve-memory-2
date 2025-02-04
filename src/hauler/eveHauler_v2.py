import time
from datetime import datetime, timedelta

import pyautogui

from src import config
from src.utils import utils
from src.autopilot.autopilot import Autopilot
from src.utils.interface import UITree
from src.utils.utils import log_console, left_click, drag_and_drop, log, start_failsafe, right_click, failsafe, \
    wait_for_truthy, get_path


class Hauler:
    def __init__(self):
        self.autopilot = Autopilot()

        self.inSpace = False
        self.canComplete = False
        self.waypointCount = 0
        self.missionStart = datetime.now()
        self.connectionFailedChecker = 0
        self.missionCounter = 0

    @staticmethod
    def move_item_to_ship():
        left_click(UITree.instance().find_node({'_name': 'ItemHangar'}, refresh=True).get_center())
        time.sleep(0.5)
        item = UITree.instance().find_node(node_type="InvItemIconContainer", refresh=True)
        ship = UITree.instance().find_node({'_name': 'topCont_ShipHangar'}, refresh=True)
        drag_and_drop(item.get_center(), ship.get_center())

        left_click(ship.get_center())
        wait_for_truthy(lambda: UITree.instance().find_node(node_type="InvItemIconContainer", refresh=True), 5)

        log_console("Moved item to ship")

    @staticmethod
    def wait_for_location_change_timer():
        log_console("Waiting for location change timer")
        waiting_counter = 0
        while not UITree.instance().find_node({'_name': 'invulnTimer'}, refresh=True):
            time.sleep(1)
            waiting_counter += 1
            if waiting_counter >= 60:
                log_console("Error waiting for locationChangeTimer")
                raise Exception("Can't find locationChangeTimer")
        time.sleep(5)

    def get_new_mission(self, max_route_length):
        decline_count = 0
        start_failsafe("1")
        while True:
            failsafe(300, msg="Getting mission", timer_name="1")

            # Clear all waypoints
            if self.route_waypoint_count() != 0:
                route_markers = UITree.instance().find_node(
                    node_type="AutopilotDestinationIcon",
                    select_many=True,
                    refresh=True
                )

                right_click(route_markers[0].get_center())
                btn_set_destination = UITree.instance().find_node(
                    {'_name': 'context_menu_Set Destination'},
                    refresh=True,
                )
                if btn_set_destination:
                    left_click(btn_set_destination)
                    right_click(route_markers[0].get_center())

                left_click(UITree.instance().find_node({'_name': 'context_menu_Remove Waypoint'}, refresh=True))

            # Add destination waypoint
            location_link_1 = UITree.instance().find_node({'_name': 'tablecell 1-3'}, refresh=True)
            right_click(location_link_1.get_center(pos_y=0.3))
            btn_add_waypoint = wait_for_truthy(
                lambda: UITree.instance().find_node({'_name': 'context_menu_Add Waypoint'}, refresh=True),
                5
            )
            left_click(btn_add_waypoint)

            start_failsafe("waypoint_update")
            while self.route_waypoint_count() != 1:
                failsafe(10, "Waypoints fail to update", "waypoint_update")
                time.sleep(1)

            wait_for_truthy(self.autopilot.get_route, 10)
            route_length = self.autopilot.get_route_length()
            if route_length <= max_route_length:
                break
            else:
                decline_count += 1
                dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
                btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
                btn_decline = btn_group.find_image(get_path("images/btn_decline.png"))
                left_click(btn_decline.get_center())
                time.sleep(5)
                log("Mission decline: jumps: " + str(route_length))
                log_console("Mission decline: jumps: " + str(route_length))
                start_failsafe()
                while not self.can_accept():
                    dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
                    btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
                    btn_request = btn_group.find_image(get_path('images/btn_request_mission.png'), confidence=0.99)
                    left_click(btn_request.get_center())
                    time.sleep(2)
                    failsafe(30)
            if decline_count > 10:
                raise Exception("To many declines")

        # Add origin station waypoint
        location_link_center_2 = UITree.instance().find_node({'_name': 'tablecell 0-3'}, refresh=True).get_center()
        right_click((location_link_center_2[0] - 20, location_link_center_2[1]))
        time.sleep(1)
        left_click(UITree.instance().find_node({'_name': 'context_menu_Add Waypoint'}, refresh=True))

        dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
        btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
        btn_accept = btn_group.find_image(get_path('images/btn_accept.png'), confidence=0.7)
        left_click(btn_accept)

        start_failsafe("waypoint_update")
        while self.route_waypoint_count() != 2:
            failsafe(10, "Waypoints fail to update after getting mission", "waypoint_update")
            time.sleep(1)

    def route_waypoint_count(self):
        return self.autopilot.get_route().count(1)

    @staticmethod
    def can_find_complete_button():
        dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
        btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
        btn_complete = btn_group.find_image(get_path('images/btn_complete_mission.png'))

        return btn_complete is not None

    @staticmethod
    def item_is_in_ship():
        log_console("Testing if item is in ship")
        ship = UITree.instance().find_node({'_name': 'topCont_ShipHangar'}, refresh=True)
        left_click(ship.get_center())
        item = UITree.instance().find_node(node_type="InvItemIconContainer", refresh=True)
        return not not item

    @staticmethod
    def can_accept():
        dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
        btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
        btn_accept = btn_group.find_image(get_path('images/btn_accept.png'), confidence=0.7)

        return btn_accept is not None

    def test_stage_criteria(self, reset_connection_failed_checker=True):
        self.inSpace = self.autopilot.is_in_space()

        if not self.inSpace:
            dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
            btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
            btn_view_request = wait_for_truthy(
                lambda:
                btn_group.find_image(get_path('images/btn_request_mission.png'), confidence=0.95)
                or btn_group.find_image(get_path('images/btn_view_mission.png'), confidence=0.95),
                10
            )
            if btn_view_request:
                left_click(btn_view_request)
                time.sleep(3)

        self.canComplete = self.can_find_complete_button()

        self.waypointCount = self.route_waypoint_count()
        if reset_connection_failed_checker:
            self.connectionFailedChecker = 0
        else:
            time.sleep(1)

        if datetime.now() - self.missionStart > timedelta(seconds=900):
            raise Exception("Something takes way too long")

    def print_state(self, i):
        log_console(
            f"Check {i} inSpace:{self.inSpace}, waypointCount:{self.waypointCount}, canComplete:{self.canComplete}, "
            f"canAccept:{self.can_accept()}")

    def main_loop(self):
        self.missionStart = datetime.now()
        while True:
            self.test_stage_criteria(False)
            while not self.inSpace and self.can_accept():
                log_console("stage 1: getting mission")
                self.get_new_mission(4)
                time.sleep(2)
                self.test_stage_criteria()
            self.missionStart = datetime.now()
            self.print_state(1)
            while not self.inSpace and self.waypointCount == 2 and not self.item_is_in_ship():
                log_console("stage 2: moving item")
                self.move_item_to_ship()
                self.test_stage_criteria()
            self.print_state(2)
            while not self.inSpace and self.waypointCount == 2 and self.item_is_in_ship():
                log_console("stage 3: undocking from origin")
                btn_undock = UITree.instance().find_node(node_type="UndockButton", refresh=True)
                left_click(btn_undock.get_center())
                self.wait_for_location_change_timer()
                self.test_stage_criteria()
            self.print_state(3)
            while self.inSpace and self.waypointCount == 2:
                log_console("stage 4: following route to drop-off")
                route_length = self.autopilot.get_route_length()
                start_failsafe(2)
                while route_length == 99:
                    time.sleep(1)
                    route_length = self.autopilot.get_route_length()
                    failsafe(delta=15, timer_name="2", msg="route length 99")
                self.autopilot.warp_through_route()
                self.test_stage_criteria()
            self.print_state(4)
            while not self.inSpace and self.canComplete and self.waypointCount == 1:
                log_console("stage 5: completing mission")
                dialog_window = UITree.instance().find_node(node_type="AgentDialogueWindow", refresh=True)
                btn_group = UITree.instance().find_node(node_type="ButtonGroup", root=dialog_window, refresh=True)
                btn_complete = btn_group.find_image(get_path('images/btn_complete_mission.png'))
                left_click(btn_complete.get_center())
                self.missionCounter += 1
                minute = (datetime.now() - self.missionStart).seconds // 60
                completion_time = (str(minute) + ":" + str((datetime.now() - self.missionStart).seconds % 60))
                log_console("Mission Complete,", self.missionCounter, "completion time:", completion_time)
                log("Mission complete: jumps: " + str(self.autopilot.get_route_length()) + ", time: " + completion_time)
                time.sleep(2)
                self.test_stage_criteria()
            self.print_state(5)
            while not self.inSpace and not self.canComplete and self.waypointCount == 1:
                log_console("stage 6: undocking from drop-off")
                btn_undock = UITree.instance().find_node(node_type="UndockButton", refresh=True)
                left_click(btn_undock.get_center())
                self.wait_for_location_change_timer()
                self.test_stage_criteria()
            self.print_state(6)
            while self.inSpace and not self.canComplete and self.waypointCount == 1:
                log_console("stage 7: following route to origin")
                route_length = self.autopilot.get_route_length()
                start_failsafe(2)
                while route_length == 99:
                    time.sleep(1)
                    route_length = self.autopilot.get_route_length()
                    failsafe(delta=15, timer_name="2", msg="route length 99")
                self.autopilot.warp_through_route()
                self.test_stage_criteria()
            self.print_state(7)

            time.sleep(2)

            self.connectionFailedChecker += 1
            if self.connectionFailedChecker > 3:
                raise Exception("Main loop can't do anything")

    @staticmethod
    def open_agent_window():
        log_console("Opening agent window")

        btn_character_sheet = UITree.instance().find_node({'_name': 'charSheetBtn'}, refresh=True)
        window_character_sheet = UITree.instance().find_node(node_type="CharacterSheetWindow", refresh=True)
        if not window_character_sheet:
            left_click(btn_character_sheet.get_center())

        btn_interactions = UITree.instance().find_node({'_name': 'interactions'}, node_type="Tab", refresh=True)
        left_click(btn_interactions.get_center())

        search_bar = UITree.instance().find_node({'_name': 'searchBar'}, refresh=True)
        left_click(search_bar.get_center())
        pyautogui.hotkey('ctrl', 'a', interval=0.2)
        pyautogui.write(config.AGENT_NAME, interval=0.25)

        time.sleep(1)
        window_character_sheet = UITree.instance().find_node(node_type="CharacterSheetWindow", refresh=True)
        btn_conversation = UITree.instance().find_node(
            node_type="AgentConversationIcon",
            root=window_character_sheet,
            refresh=True
        )
        left_click(btn_conversation.get_center())

        left_click(btn_character_sheet)
        left_click(btn_character_sheet)


if __name__ == "__main__":
    UITree.instance()
    hauler = Hauler()
    time.sleep(1)
    log("")
    while utils.fatalErrorCount < 2:
        try:
            hauler.main_loop()
        except Exception as e:
            utils.fatalErrorCount += 1
            log_console("Fatal error occurred")
            log_console("Error: " + str(e))
            img = pyautogui.screenshot()
            img.save(get_path(f"out/FatalError_{utils.fatalErrorCount}.png"))
            # close_client(config.CHARACTER_NAME)
        # if utils.fatalErrorCount < 4:
        #     start_game(config.CHARACTER_NAME)
        #     hauler.open_agent_window(config.AGENT_NAME)

    # os.system("shutdown /s /t 1")

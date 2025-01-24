import time
from datetime import datetime, timedelta

import pyautogui

import utils
from autopilot import Autopilot
from interface import UITree
from utils import log_console, left_click, drag_and_drop, log, start_failsafe, right_click, failsafe, close_client, \
    start_game, wait_for_not_falsy


class Hauler:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree
        self.autopilot = Autopilot(ui_tree)

        self.inSpace = False
        self.canComplete = False
        self.waypointCount = 0
        self.missionStart = datetime.now()
        self.connectionFailedChecker = 0
        self.missionCounter = 0

    def move_item_to_ship(self):
        left_click(self.ui_tree.find_node({'_name': 'ItemHangar'}).get_center())
        time.sleep(0.5)
        item = self.ui_tree.find_node(node_type="InvItemIconContainer")
        ship = self.ui_tree.find_node({'_name': 'topCont_ShipHangar'})
        drag_and_drop(item.get_center(), ship.get_center())
        log_console("Moved item to ship")

    def wait_for_location_change_timer(self):
        log_console("Waiting for location change timer")
        waiting_counter = 0
        while not self.ui_tree.find_node({'_name': 'invulnTimer'}):
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
            # clear all waypoints
            if self.route_waypoint_count() != 0:
                route_markers = self.ui_tree.find_node(node_type="AutopilotDestinationIcon", select_many=True)

                right_click(route_markers[0].get_center())
                btn_set_destination = self.ui_tree.find_node({'_name': 'context_menu_Set Destination'})
                if btn_set_destination:
                    left_click(btn_set_destination)
                    right_click(route_markers[0].get_center())

                left_click(self.ui_tree.find_node({'_name': 'context_menu_Remove Waypoint'}))

            location_link_center_1 = self.ui_tree.find_node({'_name': 'tablecell 1-3'}).get_center()
            right_click((location_link_center_1[0] - 20, location_link_center_1[1]))
            time.sleep(1)
            left_click(self.ui_tree.find_node({'_name': 'context_menu_Add Waypoint'}))

            wait_for_not_falsy(self.autopilot.get_route, 10, 0.5)
            route = self.autopilot.get_route()
            route_length = self.autopilot.get_route_length()
            if route_length <= max_route_length:
                break
            else:
                decline_count += 1
                dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
                btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
                btn_decline = btn_group.find_image('images/btn_decline.png')
                left_click(btn_decline.get_center())
                time.sleep(5)
                log("Mission decline: jumps: " + str(route_length))
                log_console("Mission decline: jumps: " + str(route_length))
                start_failsafe()
                while not self.can_accept():
                    dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
                    btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
                    btn_request = btn_group.find_image('images/btn_request_mission.png')
                    left_click(btn_request.get_center())
                    time.sleep(2)
                    failsafe(30)
            if decline_count > 10:
                raise Exception("To many declines")
            failsafe(300, msg="Getting mission", timer_name="1")

        location_link_center_2 = self.ui_tree.find_node({'_name': 'tablecell 0-3'}).get_center()
        right_click((location_link_center_2[0] - 20, location_link_center_2[1]))
        time.sleep(1)
        left_click(self.ui_tree.find_node({'_name': 'context_menu_Add Waypoint'}))

        dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
        btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
        btn_accept = btn_group.find_image('images/btn_accept.png')
        left_click(btn_accept)

    def route_waypoint_count(self):
        return self.autopilot.get_route().count(1)

    def can_find_complete_button(self):
        dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
        btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
        btn_complete = btn_group.find_image('images/btn_complete_mission.png')

        return btn_complete is not None

    def item_is_in_ship(self):
        log_console("Testing if item is in ship")
        ship = self.ui_tree.find_node({'_name': 'topCont_ShipHangar'})
        left_click(ship.get_center())
        item = self.ui_tree.find_node(node_type="InvItemIconContainer")
        return not not item

    def can_accept(self):
        dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
        btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
        btn_accept = btn_group.find_image('images/btn_accept.png')

        return btn_accept is not None

    def test_stage_criteria(self, reset_connection_failed_checker=True):
        self.inSpace = self.autopilot.is_in_space()
        if not self.inSpace:
            dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
            btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
            btn_request = btn_group.find_image('images/btn_request_mission.png', confidence=0.95)
            if btn_request:
                left_click(btn_request.get_center())
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
            f"Check {i} inSpace:{self.inSpace}, waypointCount:{self.waypointCount}, canComplete:{self.canComplete}")

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
                btn_undock = self.ui_tree.find_node(node_type="UndockButton")
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
                dialog_window = self.ui_tree.find_node(node_type="AgentDialogueWindow")
                btn_group = self.ui_tree.find_node(node_type="ButtonGroup", root=dialog_window)
                btn_complete = btn_group.find_image('images/btn_complete_mission.png')
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
                btn_undock = self.ui_tree.find_node(node_type="UndockButton")
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

    def open_agent_window(self, agent_name):
        log_console("Opening agent window")

        btn_character_sheet = self.ui_tree.find_node({'_name': 'charSheetBtn'})
        window_character_sheet = self.ui_tree.find_node(node_type="CharacterSheetWindow")
        if not window_character_sheet:
            left_click(btn_character_sheet.get_center())

        btn_interactions = self.ui_tree.find_node({'_name': 'interactions'}, node_type="Tab")
        left_click(btn_interactions.get_center())

        search_bar = self.ui_tree.find_node({'_name': 'searchBar'})
        left_click(search_bar.get_center())
        pyautogui.hotkey('ctrl', 'a', interval=0.2)
        pyautogui.write(agent_name, interval=0.25)

        time.sleep(1)
        window_character_sheet = self.ui_tree.find_node(node_type="CharacterSheetWindow")
        btn_conversation = self.ui_tree.find_node(node_type="AgentConversationIcon", root=window_character_sheet)
        left_click(btn_conversation.get_center())

        left_click(btn_character_sheet)
        left_click(btn_character_sheet)


if __name__ == "__main__":
    _ui_tree = UITree(utils.CHARACTER_NAME)
    hauler = Hauler(_ui_tree)
    time.sleep(1)
    log("")
    while True:
        try:
            hauler.main_loop()
        except Exception as e:
            utils.fatalErrorCount += 1
            log_console("Fatal error occurred")
            log_console("Error: " + str(e))
            img = pyautogui.screenshot()
            img.save(fr"data/FatalError_{utils.fatalErrorCount}.png")
            close_client(utils.CHARACTER_NAME)
            start_game(utils.CHARACTER_NAME)
            hauler.open_agent_window(utils.AGENT_NAME)
        if utils.fatalErrorCount > 4:
            close_client(utils.CHARACTER_NAME)
            break

    # os.system("shutdown /s /t 1")

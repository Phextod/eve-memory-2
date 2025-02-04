import time

import pyautogui

from src.utils.ui_tree import UITree
from src.utils.utils import log_console, start_failsafe, failsafe, left_click, right_click, \
    wait_for_truthy


class Autopilot:

    @staticmethod
    def is_in_warp():
        if UITree.instance().find_node({'_setText': 'Warp Drive Active'}, refresh=True):
            return True
        return False

    def wait_until_warp_end(self, warp_timer=10, check_interval=5):
        time.sleep(warp_timer)
        log_console("Waiting for warp end")
        while self.is_in_warp():
            if warp_timer > 300:
                raise Exception("Warping doesn't end")
            warp_timer += check_interval
            time.sleep(check_interval)

    def warp_through_route(self):
        start_failsafe("warp_through_route_1")
        while True:
            failsafe(10 * 60, "Warping through route timeout", "warp_through_route_1")
            start_failsafe("warp_through_route_2")
            while not UITree.instance().find_node({'_setText': 'Establishing Warp Vector'}, refresh=True) \
                    or UITree.instance().find_node({'_setText': 'Jumping '}, refresh=True)\
                    or UITree.instance().find_node({'_setText': 'Warp Drive Active'}, refresh=True):

                failsafe(60, "Warp start timeout", "warp_through_route_2")

                route_markers = UITree.instance().find_node(
                    node_type="AutopilotDestinationIcon",
                    select_many=True,
                    refresh=True
                )
                if not route_markers:
                    time.sleep(1)
                    continue
                route_marker = route_markers[0]
                right_click(route_marker)
                time.sleep(1)

                btn_next_action = wait_for_truthy(
                    lambda:
                        UITree.instance().find_node({'_name': 'context_menu_DockInStation'}, refresh=True)
                        or UITree.instance().find_node({'_name': 'context_menu_Jump'}, refresh=True),
                    10
                )
                if not btn_next_action:
                    continue

                if "dock" in btn_next_action.attrs.get("_name").lower():
                    self.dock()
                    return

                left_click(btn_next_action)

            self.wait_until_warp_end()
            time.sleep(2)
            self.wait_until_jump_end()

    @staticmethod
    def toggle_mwd():
        log_console("Toggle MWD")
        pyautogui.hotkey('alt', 'f1', interval=0.2)

    @staticmethod
    def toggle_hardeners():
        log_console("Toggle Hardeners")
        pyautogui.hotkey('alt', 'f2', 'f3', interval=0.2)

    def dock(self):
        log_console("Docking")
        start_failsafe()
        while self.is_in_space() and not self.is_in_warp():
            failsafe(60, msg="Docking")
            route_marker = UITree.instance().find_node(node_type="AutopilotDestinationIcon", refresh=True)
            if not route_marker:
                time.sleep(0.5)
                continue

            right_click(route_marker)

            btn_dock = wait_for_truthy(
                lambda: UITree.instance().find_node(
                    {'_name': 'context_menu_DockInStation'},
                    refresh=True),
                5
            )
            if not btn_dock:
                continue
            left_click(btn_dock)
            time.sleep(1)

        self.wait_until_warp_end()
        self.toggle_mwd()
        self.wait_until_docked()

    @staticmethod
    def get_route():
        route_markers = UITree.instance().find_node(
            node_type="AutopilotDestinationIcon",
            select_many=True,
            refresh=True,
        )
        try:
            icon_textures = []
            for m in route_markers:
                children_node = UITree.instance().nodes.get(m.children[0])
                icon_textures.append(children_node.attrs.get("_texturePath"))
            route = [1 if "stationMarker" in texture_path else 0 for texture_path in icon_textures]
            route.index(1)
        except (ValueError, IndexError, TypeError):
            return []
        return route

    def get_route_length(self):
        route = self.get_route()
        try:
            route_len = route.index(1)
        except ValueError:
            log_console("valueError")
            log_console(route)
            return 99
        return route_len + 1

    @staticmethod
    def is_in_space():
        return not UITree.instance().find_node(node_type="UndockButton", refresh=True)

    def wait_until_docked(self, waiting_counter=0, checking_interval=1):
        log_console("Waiting for dock")
        while self.is_in_space():
            time.sleep(checking_interval)
            waiting_counter += checking_interval
            if waiting_counter >= 300:
                log_console("Error waiting for docking")
                raise Exception("Can't dock")
        time.sleep(4)
        log_console("Docking complete")

    @staticmethod
    def wait_until_jump_end(waiting_counter=0):
        log_console("Waiting for jump cloak")
        # todo maybe i don't need the timer_container
        timer_container = UITree.instance().find_node(node_type="TimerContainer", refresh=True)
        cloak_icon = UITree.instance().find_node(
            {'_name': 'jumpCloakTimer'},
            root=timer_container,
            refresh=True
        )
        window_overview = UITree.instance().find_node(node_type="OverviewWindow", refresh=True)

        while cloak_icon is None or not window_overview:
            time.sleep(1)
            waiting_counter += 1
            if waiting_counter >= 120:
                log_console("Error waiting for jump end")
                raise Exception("Can't find jumpCloak or overview window")

            timer_container = UITree.instance().find_node(node_type="TimerContainer", refresh=True)
            cloak_icon = UITree.instance().find_node(
                {'texturePath': 'res:/UI/Texture/classes/war/atWar_64.png'},
                root=timer_container,
                refresh=True
            )
            window_overview = UITree.instance().find_node(node_type="OverviewWindow", refresh=True)
        time.sleep(5)


if __name__ == "__main__":
    autopilot = Autopilot()
    autopilot.warp_through_route()

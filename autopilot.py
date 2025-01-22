import time

from interface import UITree
from utils import log_console, start_failsafe, failsafe, CHARACTER_NAME, left_click


class Autopilot:

    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

    def is_in_warp(self):
        if self.ui_tree.find_node({'_setText': 'Warp Drive Active'}):
            return True
        return False

    def wait_until_warp_end(self, warp_timer=10, check_interval=5):
        time.sleep(warp_timer)
        log_console("Warping")
        while self.is_in_warp():
            if warp_timer > 300:
                raise Exception("Warping doesn't end")
            warp_timer += check_interval
            time.sleep(check_interval)

    def warp_through_route(self):
        jumps_to_fin = self.get_route_length()
        log_console("Warping through route")
        jumps_count = 0
        failed_jumps = 0
        hardeners_active = False
        while jumps_count < jumps_to_fin:
            failsafe_counter = 0
            while not self.is_in_warp():
                failsafe_counter += 1
                if failsafe_counter > 60:
                    raise Exception("Can't start warping")
                if jumps_to_fin == 1:  # 0 jumps route
                    left_click(self.ui_tree.find_node(node_type="OverviewScrollEntry"))
                    time.sleep(0.2)
                    if self.ui_tree.find_node({'_name': 'selectedItemDock'}):
                        self.toggle_hardeners()
                        self.dock()
                        return
                left_click(self.ui_tree.find_node(node_type="OverviewScrollEntry"))
                time.sleep(0.3)
                left_click(self.ui_tree.find_node({'_name': 'selectedItemJump'}))
                if jumps_count == 0 and not hardeners_active:
                    self.toggle_hardeners()
                    hardeners_active = True
                time.sleep(1)
            jumps_count += 1
            log_console("Jumping: " + str(jumps_count) + "/" + str(jumps_to_fin))
            try:
                self.wait_until_warp_end()
                time.sleep(2)
                self.wait_until_jump_end()
                hardeners_active = False
            except Exception:
                jumps_count -= 1
                failed_jumps += 1
            if failed_jumps > 3:
                raise Exception(f"{failed_jumps} failed jumps attempts")
            time.sleep(1)
        self.dock()

    def toggle_mwd(self):
        pass
        # customPrint("Toggle MWD")
        # pyautogui.hotkey('alt', 'f1', interval=0.2)

    def toggle_hardeners(self):
        pass
        # customPrint("Toggle Hardeners")
        # pyautogui.hotkey('alt', 'f2', 'f3', interval=0.2)

    def dock(self):
        log_console("Docking")
        start_failsafe()
        while True:
            left_click(self.ui_tree.find_node(node_type="OverviewScrollEntry"))
            time.sleep(0.2)
            left_click(self.ui_tree.find_node({'_name': 'selectedItemDock'}))
            time.sleep(1)
            if not self.is_in_space() or self.is_in_warp():
                break
            failsafe(40, msg="Docking")
        self.wait_until_warp_end()
        # self.toggleMWD()
        self.wait_until_docked()

    def get_route(self):
        route_markers = self.ui_tree.find_node(node_type="AutopilotDestinationIcon", select_many=True)
        icon_textures = [self.ui_tree.nodes.get(m.children[0]).attrs.get("_texturePath") for m in route_markers]
        route = [1 if "stationMarker" in texture_path else 0 for texture_path in icon_textures]
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

    def is_in_space(self):
        return not self.ui_tree.find_node(node_type="UndockButton")

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

    def wait_until_jump_end(self, waiting_counter=0):
        log_console("Waiting for jump cloak")
        # todo maybe i don't need the timer_container
        timer_container = self.ui_tree.find_node(node_type="TimerContainer")
        cloak_icon = self.ui_tree.find_node(
            {'_name': 'jumpCloakTimer'},
            root=timer_container
        )
        window_overview = self.ui_tree.find_node(node_type="OverviewScrollEntry")

        while cloak_icon is None or not window_overview:
            time.sleep(1)
            waiting_counter += 1
            if waiting_counter >= 120:
                log_console("Error waiting for jump end")
                raise Exception("Can't find jumpCloak or overview window")

            timer_container = self.ui_tree.find_node(node_type="TimerContainer")
            cloak_icon = self.ui_tree.find_node(
                {'texturePath': 'res:/UI/Texture/classes/war/atWar_64.png'},
                root=timer_container
            )
            window_overview = self.ui_tree.find_node(node_type="OverviewScrollEntry")


if __name__ == "__main__":
    autopilot = Autopilot(UITree(CHARACTER_NAME))
    autopilot.warp_through_route()

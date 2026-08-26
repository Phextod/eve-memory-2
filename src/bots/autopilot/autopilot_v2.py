from src.eve_ui.eve_ui import EveUI
from src.utils.ui_tree import UITree


class Autopilot:
    def __init__(self, ui):
        self.ui: EveUI = ui

    def run(self):
        self.ui.route.autopilot(self.ui.station_window, self.ui.timers)


if __name__ == '__main__':
    autopilot = Autopilot(EveUI(UITree(), do_setup=False))
    autopilot.run()

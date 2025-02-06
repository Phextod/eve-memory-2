from src.eve_ui.eve_ui import EveUI


class Autopilot:
    def __init__(self, ui: EveUI):
        self.ui = ui

    def run(self):
        B
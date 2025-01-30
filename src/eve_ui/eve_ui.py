from src.eve_ui.overview import Overview
from src.eve_ui.target_bar import TargetBar
from src.utils.interface import UITree


class EveUI:
    def __init__(self, character_name):
        self.ui_tree = UITree(character_name)

        self.overview = Overview(self.ui_tree)
        self.target_bar = TargetBar(self.ui_tree)


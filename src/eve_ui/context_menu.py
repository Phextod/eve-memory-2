from enum import Enum

from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree
from src.utils.utils import click, wait_for_truthy, move_cursor


class DistancePresets:
    presets = [
        {"value": 500, "text": "500 m"},
        {"value": 1_000, "text": "1 000 m"},
        {"value": 2_500, "text": "2 500 m"},
        {"value": 5_000, "text": "5 000 m"},
        {"value": 7_500, "text": "7 500 m"},
        {"value": 10_000, "text": "10 km"},
        {"value": 15_000, "text": "15 km"},
        {"value": 20_000, "text": "20 km"},
        {"value": 25_000, "text": "25 km"},
        {"value": 30_000, "text": "30 km"},
    ]

    @staticmethod
    def closest(value):
        closest = min(DistancePresets.presets, key=lambda p: abs(p["value"] - value))
        return closest["text"]

    @staticmethod
    def closest_smaller(value):
        closest = max(
            (p for p in DistancePresets.presets if p["value"] <= value),
            key=lambda p: p["value"], default=DistancePresets.presets[0]
        )
        return closest["text"]

    @staticmethod
    def closest_larger(value):
        closest = min(
            (p for p in DistancePresets.presets if p["value"] >= value),
            key=lambda p: p["value"], default=DistancePresets.presets[-1]
        )
        return closest["text"]


class ContextMenu:
    instance = None

    def __new__(cls, ui_tree: UITree, refresh_on_init=False):
        if not cls.instance:
            cls.instance = super(ContextMenu, cls).__new__(cls)
        return cls.instance

    def __init__(self, ui_tree: UITree, refresh_on_init=False):
        self.ui_tree = ui_tree

        self.menu_container_query = BubblingQuery({'_name': 'l_menu'}, ui_tree=ui_tree, refresh_on_init=refresh_on_init)

    def click(self, entry_text, contains=False):
        target = BubblingQuery(
            {'_setText': entry_text},
            self.menu_container_query,
            contains=contains,
        ).result

        if target:
            click(target)
            return True
        return False

    def open_submenu(self, entry_text, contains=False):
        target = BubblingQuery(
            {'_setText': entry_text},
            self.menu_container_query,
            contains=contains,
        ).result

        if target:
            move_cursor(target.get_center())
            return True
        return False

    def click_safe(self, entry_text, timeout):
        return wait_for_truthy(lambda: self.click(entry_text), timeout) is not None

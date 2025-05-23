from typing import Dict, Tuple, List

from src.utils.bubbling_query import BubblingQuery
from src.utils.singleton import Singleton
from src.utils.ui_tree import UITreeNode
from src.utils.utils import click, wait_for_truthy, move_cursor


# This is so garbage. It should be an enum
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
        return closest

    @staticmethod
    def closest_smaller(value):
        closest = max(
            (p for p in DistancePresets.presets if p["value"] <= value),
            key=lambda p: p["value"], default=DistancePresets.presets[0]
        )
        return closest

    @staticmethod
    def closest_larger(value):
        closest = min(
            (p for p in DistancePresets.presets if p["value"] >= value),
            key=lambda p: p["value"], default=DistancePresets.presets[-1]
        )
        return closest["text"]


@Singleton
class ContextMenu:
    def __init__(self, refresh_on_init=False):
        self.menu_container_query = BubblingQuery({'_name': 'l_menu'}, refresh_on_init=refresh_on_init)
        self.menu_entries_query = BubblingQuery(
            node_type="TextBody",
            parent_query=self.menu_container_query,
            select_many=True
        )

        self.entries_list: List[Tuple[str, UITreeNode]] = []  # (entry_text, entry_node)

    def update(self, refresh=True):
        self.menu_entries_query.run(refresh)

        self.entries_list.clear()
        for entry_node in self.menu_entries_query.result:
            entry_text = entry_node.attrs.get("_setText", "")
            if entry_text:
                self.entries_list.append((entry_text, entry_node))

        return self

    def get_menu_btn(self, entry_text, contains=False, timeout=2, refresh=True):
        return wait_for_truthy(
            lambda: next(
                (
                    e[1] for e in self.update(refresh).entries_list
                    if (entry_text in e[0] if contains else entry_text == e[0])
                ),
                None
            ),
            timeout
        )

    def click(self, entry_text, contains=False, refresh=True):
        if refresh:
            self.update()

        target = next(
            (e[1] for e in self.entries_list if (entry_text in e[0] if contains else entry_text == e[0])),
            None
        )

        if target:
            click(target)
            return True
        return False

    def open_submenu(self, entry_text, contains=False):
        target = next(
            (e[1] for e in self.entries_list if (entry_text in e[0] if contains else entry_text == e[0])),
            None
        )

        if target:
            move_cursor(target.get_center())
            return True
        return False

    def click_safe(self, entry_text, timeout=2, contains=False):
        return wait_for_truthy(lambda: self.click(entry_text, contains=contains), timeout) is not None

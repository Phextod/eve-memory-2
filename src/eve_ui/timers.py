from enum import Enum
from typing import TYPE_CHECKING

from src.utils.bubbling_query import BubblingQuery

if TYPE_CHECKING:
    # Only imported during static type checking, ignored at runtime
    from src.eve_ui.eve_ui import EveUI


class TimerNames(Enum):
    invulnerable = "invulnTimer"
    jumpCloak = "jumpCloakTimer"
    abyssal = "abyssalContentExpirationTimer"


class Timers:
    def __init__(self, eve_ui: 'EveUI', refresh_on_init=False):
        self.eve_ui: EveUI = eve_ui

        self.main_container_query = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="TimerContainer",
            refresh_on_init=refresh_on_init
        )

        self.timers = []
        self.update(refresh_on_init)

    def update(self, refresh=True):
        self.timers.clear()

        timer_nodes = BubblingQuery(
            ui_tree=self.eve_ui.ui_tree,
            node_type="Timer",
            parent_query=self.main_container_query,
            select_many=True,
            refresh_on_init=refresh,
        ).result

        for timer_node in timer_nodes:
            self.timers.append(timer_node.attrs["_name"])

        return self

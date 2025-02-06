from enum import Enum

from src.utils.bubbling_query import BubblingQuery


class TimerNames(Enum):
    invulnerable = "invulnTimer"
    jumpCloak = "jumpCloakTimer"
    abyssal = "abyssalContentExpirationTimer"


class Timers:
    def __init__(self, refresh_on_init=False):
        self.main_container_query = BubblingQuery(node_type="TimerContainer", refresh_on_init=refresh_on_init)

        self.timers = []
        self.update(refresh_on_init)

    def update(self, refresh=True):
        self.timers.clear()

        timer_nodes = BubblingQuery(
            node_type="Timer",
            parent_query=self.main_container_query,
            select_many=True,
            refresh_on_init=refresh,
        ).result

        for timer_node in timer_nodes:
            self.timers.append(timer_node.attrs["_name"])

        return self

import json
import time
from typing import List

from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.timers import TimerNames
from src.utils.ui_tree import UITree
from src.utils.utils import get_path


class AbyssHelper:
    def __init__(self, ui):
        self.ui: EveUI = ui
        self.ui_tree: UITree = UITree.instance()
        self.abyss_fighter = AbyssFighter(ui)
        self.abyss_rooms = dict()
        with open(get_path("data/abyss_rooms.json")) as f:
            self.abyss_rooms = json.load(f)

    def get_current_room(self):
        ship_names = [e.name for e in self.abyss_fighter.enemy_entries_on_overview()]
        print(ship_names)
        print([e.type for e in self.abyss_fighter.enemy_entries_on_overview()])
        for _, room in self.abyss_rooms.items():
            room_ships = room["ship_names"]
            for ship in ship_names:
                if ship not in room_ships:
                    break
            else:
                return room["name"]
        return None

    def run(self):
        while True:
            print("Waiting for abyss")
            self.wait_for_abyss()
            while TimerNames.abyssal.value in self.ui.timers.update().timers:
                print("Analyzing room")
                self.analyze_current_room()
                print("Waiting for next room")
                self.wait_for_next_room()

    def wait_for_abyss(self):
        while (
            TimerNames.abyssal.value not in self.ui.timers.timers
            or not self.abyss_fighter.enemies_on_overview()
        ):
            time.sleep(5)
            self.ui.overview.update()
            self.ui.timers.update()

    def analyze_current_room(self):
        enemies_on_overview = self.abyss_fighter.enemies_on_overview()
        self.abyss_fighter.precompute_enemy_ship_attributes(enemies_on_overview)

        print(f"Room: {self.get_current_room()}")

        enemy_types: List[AbyssShip] = []
        for enemy in enemies_on_overview:
            if enemy not in enemy_types:
                enemy_types.append(enemy)
        enemy_types.sort(key=lambda x: x.dmg_without_orbit, reverse=True)

        for enemy in enemy_types:
            weapon_range = enemy.missile_range if enemy.missile_rate_of_fire \
                else enemy.turret_optimal_range + enemy.turret_falloff if enemy.turret_rate_of_fire \
                else 0
            print(
                f"{enemy.name:{' '}<30}: "
                f"tracking:{enemy.turret_tracking:5.0f}, "
                f"range:{weapon_range:7.0f}, "
                f"dmg_without_orbit:{enemy.dmg_without_orbit:7.0f} "
                f"dmg_with_orbit:{enemy.dmg_with_orbit:7.0f}, "
                f"optimal_orbit:{enemy.optimal_orbit_range:5.0f} "
            )

        clear_order = self.abyss_fighter.calculate_clear_order(enemies_on_overview)
        print("Recommended clear order:")
        for stage in clear_order:
            print(f"target:{stage.target.name}({id(stage.target)},"
                  f" orbit: {stage.orbit_target.name if stage.orbit_target else 'Bio Cache'}"
                  f"{f'({id(stage.orbit_target)})' if stage.orbit_target else ''}")

    def wait_for_next_room(self):
        self.ui.overview.update()
        while self.abyss_fighter.enemies_on_overview():
            time.sleep(5)
            self.ui.overview.update()

        while not self.abyss_fighter.enemies_on_overview():
            time.sleep(5)
            self.ui.overview.update()

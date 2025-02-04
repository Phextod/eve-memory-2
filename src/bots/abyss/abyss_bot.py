import json
import math

import keyboard

from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import get_pid, get_path


class AbyssBot:
    def __init__(self):
        self.pid = get_pid()
        self.ui = EveUI()
        # exported from: https://caldarijoans.streamlit.app/Abyssal_Enemies_Database
        self.ships = self.load_ships(get_path("data/abyss_ships.json"))

    @staticmethod
    def load_ships(filepath):
        ships = []
        with open(filepath) as file:
            for ship_data in (json.load(file, object_hook=AbyssShip.decode)):
                ships.append(AbyssShip(**ship_data))
        return ships

    def enemies_and_others_on_overview(self):
        enemies = []
        other_entries = []
        for entry in self.ui.overview.entries:
            enemy = next((ship for ship in self.ships if ship.name == entry.get("Name")), None)
            if enemy:
                enemies.append(enemy)
            else:
                other_entries.append(entry)
        return enemies, other_entries

    @staticmethod
    def simulate_fight(enemies=None, player_ship=None):
        enemy_dps_ehp_received_dps = [[50, 100, 10], [50, 100, 10], [100, 100, 10]]
        received_dmg = 0
        fight_time = 0
        for enemy in enemy_dps_ehp_received_dps:
            enemy_dps = enemy[0]
            enemy_ehp = enemy[1]
            enemy_received_dps = enemy[2]
            time_to_kill = math.ceil(enemy_ehp / enemy_received_dps)
            enemy_total_dmg = (time_to_kill + fight_time) * enemy_dps

            fight_time += time_to_kill
            received_dmg += enemy_total_dmg
        print("done")

    def run(self):
        while True:
            if keyboard.read_key() == "enter":
                self.ui.ship_ui.update_modules()
                # print(self.ui.ship_ui)


if __name__ == "__main__":
    # bot = AbyssBot(CHARACTER_NAME)
    # print("ready")
    # bot.run()
    AbyssBot.simulate_fight()

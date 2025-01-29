import json
import keyboard

from src.abyss.abyss_ship import AbyssShip
from src.eve_ui.overview import Overview
from src.utils.utils import wait_for_truthy, get_pid, CHARACTER_NAME
from src.utils.interface import UITree


class AbyssBot:
    def __init__(self, character_name):
        self.pid = get_pid()
        self.ui_tree = UITree(character_name)
        self.overview = Overview(self.ui_tree)

        # exported from: https://caldarijoans.streamlit.app/Abyssal_Enemies_Database
        self.ships = self.load_ships(r"../../data/abyss_ships.json")

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
        for entry in self.overview.entries:
            enemy = next((ship for ship in self.ships if ship.name == entry.get("name")), None)
            if enemy:
                enemies.append(enemy)
            else:
                other_entries.append(entry)
        return enemies, other_entries

    def run(self):
        while True:
            if keyboard.read_key() == "enter":
                self.overview.update()
                current_enemies, others = self.enemies_and_others_on_overview()
                for enemy in current_enemies:
                    print(enemy.name, enemy.weapon_tracking)
                print("***********************************************************")
                print(others)
                print("-----------------------------------------------------------")


if __name__ == "__main__":
    bot = AbyssBot(CHARACTER_NAME)
    bot.run()

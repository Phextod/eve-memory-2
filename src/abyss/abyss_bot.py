import json

import keyboard

from src.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import get_pid, CHARACTER_NAME, get_path


class AbyssBot:
    def __init__(self, character_name):
        self.pid = get_pid()
        self.ui = EveUI(character_name)
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

    def run(self):
        while True:
            if keyboard.read_key() == "pagedown":
                self.ui.inventory.update_items()
                print(self.ui.inventory)


if __name__ == "__main__":
    bot = AbyssBot(CHARACTER_NAME)
    print("ready")
    # bot.run()

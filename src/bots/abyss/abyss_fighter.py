import json

from src.bots.abyss.ship import Ship
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import get_path


class AbyssFighter:
    def __init__(self, ui: EveUI):
        self.ui = ui
        # exported from: https://caldarijoans.streamlit.app/Abyssal_Enemies_Database
        self.enemy_ships = self.load_enemy_ships(get_path("data/ships_data.json"))

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
    def load_enemy_ships(filepath):
        ships = []
        with open(filepath) as file:
            ships_data = json.load(file)
        for key, ship_data in ships_data.items():
            ships.append(Ship.from_json(ship_data))
        return ships

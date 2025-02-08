import json

from src import config
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import get_path


class AbyssFighter:
    def __init__(self, ui: EveUI):
        self.ui = ui
        # exported from: https://caldarijoans.streamlit.app/Abyssal_Enemies_Database
        self.enemy_ships = self.load_enemy_ships(
            get_path(config.ABYSSAL_SHIP_DATA_PATH),
            get_path(config.ABYSSAL_ITEM_DATA_PATH)
        )

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
    def load_enemy_ships(ship_filepath, item_filepath):
        ships = []
        with open(ship_filepath) as file:
            ships_data = json.load(file)
        with open(item_filepath) as file:
            item_data = json.load(file)
        for key, ship_data in ships_data.items():
            ships.append(AbyssShip.from_json(ship_data, item_data))
        return ships

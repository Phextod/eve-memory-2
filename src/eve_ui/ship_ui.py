from src.utils.bubbling_query import BubblingQuery
from src.utils.interface import UITree


class ShipUI:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

        self.main_container_query = BubblingQuery(node_type="ShipUI", ui_tree=ui_tree)

        self.capacitor_percent = 0.0
        self.update_capacitor_percent()

    def update_capacitor_percent(self):
        capacitor_sprites = BubblingQuery(
            {"_texturePath": "capacitorCell_2"},
            self.main_container_query,
            contains=True,
            select_many=True,
        ).result

        sprite_alphas = [c.attrs["_color"]["aPercent"] for c in capacitor_sprites]
        count_0 = sprite_alphas.count(0)

        if sprite_alphas:
            self.capacitor_percent = count_0 / len(sprite_alphas)
        else:
            self.capacitor_percent = 0.0

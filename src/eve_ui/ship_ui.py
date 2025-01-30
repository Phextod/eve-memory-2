from src.utils.interface import UITree


class ShipUI:
    def __init__(self, ui_tree: UITree):
        self.ui_tree = ui_tree

        self.main_container = None
        self.update_main_container()

        self.capacitor_container = None
        self.update_capacitor_container()

        self.capacitor_percent = 0.0
        self.update_capacitor_percent()

    def update_main_container(self):
        self.main_container = self.ui_tree.find_node(
            node_type="ShipUI",
        )

    def update_capacitor_container(self):
        self.capacitor_container = self.ui_tree.find_node(
            node_type="CapacitorContainer",
            root=self.main_container,
            refresh=True,
        )

    def update_capacitor_percent(self):
        capacitor_sprites = self.ui_tree.find_node(
            {"_texturePath": "capacitorCell_2"},
            contains=True,
            select_many=True,
            root=self.capacitor_container,
            refresh=True,
        )

        sprite_alphas = [c.attrs["_color"]["aPercent"] for c in capacitor_sprites]
        count_0 = sprite_alphas.count(0)
        self.capacitor_percent = count_0 / len(sprite_alphas)

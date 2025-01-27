from eveHauler_v2 import Hauler
from interface import UITree
from utils import CHARACTER_NAME, right_click


if __name__ == '__main__':
    ui_tree = UITree(CHARACTER_NAME)
    hauler = Hauler(ui_tree)
    hauler.main_loop()


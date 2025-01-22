import utils
from eveHauler_v2 import Hauler
from interface import UITree

if __name__ == '__main__':
    ui_tree = UITree(utils.CHARACTER_NAME)
    hauler = Hauler(ui_tree)
    hauler.main_loop()

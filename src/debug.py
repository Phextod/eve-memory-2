import numpy as np

from src.bots.abyss.abyss_helper import AbyssHelper
from src.eve_ui.eve_ui import EveUI
from src.utils.ui_tree import UITree
from src.utils.utils import *

np.seterr(all='raise')

init_logger(config.ABYSSAL_LOG_FILE_PATH)
ui_tree: UITree = UITree()
ui = EveUI(ui_tree, do_setup=False)
# self = AbyssBot(ui)
self = AbyssHelper(ui)
# self = Hauler(ui)

while True:
    self.run()

# abyss_fighter = AbyssFighter(ui)
# abyss_fighter.init_room()
# abyss_fighter.clear_room()

# self.run()
# self.use_filament()
# self.do_abyss()

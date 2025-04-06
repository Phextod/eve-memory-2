import copy
import itertools
import math
import threading
from enum import Enum
from itertools import permutations
from typing import List

import numpy as np
from line_profiler_pycharm import profile

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_helper import AbyssHelper
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import FightPlan, Stage
from src.bots.abyss.ship import Ship
from src.bots.hauler.eve_hauler_v3 import Hauler
from src.eve_ui.eve_ui import EveUI
from src.eve_ui.fleet import Fleet
from src.utils.ui_tree import UITree
from src.utils.utils import *

np.seterr(all='raise')

init_logger(config.ABYSSAL_LOG_FILE_PATH)
ui = EveUI(do_setup=False)
ui_tree: UITree = UITree.instance()
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

import copy
import itertools
import math
from enum import Enum
from itertools import permutations
from typing import List

import numpy as np
from line_profiler_pycharm import profile

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import FightPlan, Stage
from src.bots.abyss.ship import Ship
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

np.seterr(all='raise')

ui = EveUI()
ui_tree: UITree = UITree.instance()
self = AbyssBot(ui)

# abyss_fighter = AbyssFighter(ui)
# abyss_fighter.init_room()
# abyss_fighter.clear_room()

# self.run()
# self.do_abyss()

# self.use_filament()
# self.do_abyss()



print("Done")



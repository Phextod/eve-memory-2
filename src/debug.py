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
from src.bots.abyss.abyss_ship import AbyssShip
from src.bots.abyss.fight_plan import FightPlan, Stage
from src.bots.abyss.ship import Ship
from src.bots.hauler.eve_hauler_v3 import Hauler
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *

np.seterr(all='raise')


# ui = EveUI()
# ui_tree: UITree = UITree.instance()
# self = AbyssBot(ui)
# self = Hauler(ui)

# abyss_fighter = AbyssFighter(ui)
# abyss_fighter.init_room()
# abyss_fighter.clear_room()

# self.run()
# self.use_filament()
# self.do_abyss()


def a(end_event: threading.Event):
    while not end_event.is_set():
        print("a")
        time.sleep(0.1)


e = threading.Event()
t1 = threading.Thread(target=a, args=[e])

# t1.start()
time.sleep(1)
e.set()
print(t1.is_alive())
t1.join()

print("Done")

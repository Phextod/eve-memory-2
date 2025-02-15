import copy
import math
from enum import Enum
from itertools import permutations
from typing import List

from line_profiler_pycharm import profile

from src.bots.abyss.abyss_bot import AbyssBot
from src.bots.abyss.abyss_fighter import AbyssFighter
from src.bots.abyss.abyss_ship import AbyssShip
from src.eve_ui.eve_ui import EveUI
from src.utils.utils import *


# ui = EveUI()
# ui_tree: UITree = UITree.instance()
# self = AbyssBot(ui)
#
# self.run()
# self.do_abyss()

# self.use_filament()
# self.do_abyss()


class Ship:
    def __init__(self, hp, missile=0.0, turret=0.0, dmg_multi=0.0, max_dmg_multi=0.0, target_resist_multi=None,
                 resist=0.0, missile_multi=None, turret_multi=None):
        self.hp = float(hp)
        self.missile = missile
        self.turret = turret
        self.ttk = 0.0
        self.dmg_multi = dmg_multi
        self.max_dmg_multi = max_dmg_multi
        self.target_resist_multi = target_resist_multi
        self.resist = resist
        self.missile_multi = missile_multi
        self.turret_multi = turret_multi

    def get_dps(self, time_in_fight, _target: "Ship", total_turret_multi, total_missile_multi):
        dmg_multi = min(self.max_dmg_multi, self.dmg_multi * time_in_fight) + 1
        return (self.missile * total_missile_multi + self.turret * total_turret_multi) * dmg_multi * (
                    1 - _target.resist)

    def set_ttk(self, _player):
        self.ttk = self.hp / (_player.turret + _player.missile)

    def __eq__(self, other):
        return self.hp == other.hp \
            and self.missile == other.missile \
            and self.turret == other.turret \
            and self.dmg_multi == other.dmg_multi \
            and self.max_dmg_multi == other.max_dmg_multi \
            and self.target_resist_multi == other.target_resist_multi \
            and self.resist == other.resist \
            and self.missile_multi == other.missile_multi \
            and self.turret_multi == other.turret_multi

    def __str__(self):
        return f"{self.hp}, {self.turret}, {self.missile}, {self.dmg_multi}, {self.max_dmg_multi}, {self.target_resist_multi}, {self.turret_multi}, {self.missile_multi}"


class Stage:
    def __init__(self, ships, _target, _player):
        self.ships: List[Ship] = ships
        self.target: Ship = _target
        self.duration: float = _target.hp / (_player.turret + _player.missile)
        # self.dmg_taken = sum(s.dps * self.duration for s in self.ships)

    def get_dmg_taken(self, previous_stages_time):
        target_resist_multi = math.prod(
            [s.target_resist_multi for s in self.ships if s.target_resist_multi is not None])
        _target = copy.deepcopy(self.target)
        _target.resist *= target_resist_multi
        total_turret_multi = math.prod([s.turret_multi for s in self.ships if s.turret_multi is not None])
        total_missile_multi = math.prod([s.missile_multi for s in self.ships if s.missile_multi is not None])
        return sum(
            s.get_dps(previous_stages_time, _target, total_turret_multi, total_missile_multi) * self.duration for s in
            self.ships)

    @staticmethod
    def calc_total_dmg_taken(stages: List["Stage"]):
        total_dmg_taken = 0
        total_time = 0
        for stage in stages:
            total_time += stage.duration
            total_dmg_taken += stage.get_dmg_taken(total_time)
        return total_dmg_taken


def calc_order(_player, _enemies):
    tried_targets = []
    enemies_remaining = [e for e in _enemies]
    best_order = None
    least_dmg_taken = None
    order = []
    depth = 0

    while True:
        for i in range(len(enemies_remaining)):
            target = enemies_remaining[i]
            if len(tried_targets) < depth + 1:
                tried_targets.append([])
            if target in tried_targets[depth]:
                continue

            order.append(Stage(enemies_remaining.copy(), target, _player))
            tried_targets[depth].append(target)
            if least_dmg_taken and sum(s.dmg_taken for s in order) > least_dmg_taken:
                del order[-1]
                continue

            enemies_remaining.remove(target)
            depth += 1
            break
        else:
            if len(order) == len(_enemies):
                dmg_taken = sum(s.dmg_taken for s in order)
                if least_dmg_taken is None or least_dmg_taken > dmg_taken:
                    least_dmg_taken = dmg_taken
                    best_order = order.copy()
            else:
                del tried_targets[depth]
            depth -= 1
            if depth < 0:
                break
            enemies_remaining.append(order[depth].target)
            del order[depth]

    return best_order


player = Ship(100, turret=5, resist=0.5)
enemies = [
    Ship(10, turret=10, missile_multi=1.9),
    Ship(10, turret=10, turret_multi=1.9),
    Ship(30, turret=100, dmg_multi=0.05, max_dmg_multi=1.5),
    Ship(40, missile=20, target_resist_multi=0.9),
    Ship(20, missile=200),
    Ship(30, turret=30),
]

for enemy in enemies:
    enemy.set_ttk(player)

_player = player
_best_order = []
_least_dmg_taken = float("inf")
_dmg_taken = 0


# _max_dps = sum(map(lambda e: e.dps, enemies))


@profile
def calc_order_recursive(_enemies, _order):
    global _player
    global _best_order
    global _least_dmg_taken
    global _dmg_taken

    if not _enemies:
        if _least_dmg_taken > _dmg_taken:
            _best_order = _order.copy()
            _least_dmg_taken = _dmg_taken
        return

    for target in _enemies:
        _order.append(Stage(_enemies.copy(), target, _player))
        _dmg_taken = Stage.calc_total_dmg_taken(_order)
        if _dmg_taken < _least_dmg_taken:
            _enemies.remove(target)
            calc_order_recursive(_enemies, _order)
            _enemies.append(target)
        del _order[-1]


# @profile
def calc_order_itertools(_player, _enemies):
    least_dmg_taken = float("inf")
    best_permutation = None
    max_dps = sum(map(lambda e: e.dps, enemies))
    for permutation in permutations(_enemies):
        dmg_taken = 0
        remaining_dps = max_dps
        for target in permutation:
            dmg_taken += remaining_dps * (target.hp / _player.dps)
            if dmg_taken > least_dmg_taken:
                break
            remaining_dps -= target.dps
        else:
            if least_dmg_taken is None or dmg_taken < least_dmg_taken:
                least_dmg_taken = dmg_taken
                best_permutation = permutation

    order = []
    for i, _enemy in enumerate(best_permutation):
        order.append(Stage(best_permutation[i:], _enemy, _player))

    return order


@profile
def calc_order_insert(_player, _enemies):
    best_stage_order = []
    best_target_order = []
    ewar_enemies = [e for e in _enemies if e.target_resist_multi or e.missile_multi or e.turret_multi]
    not_ewar_enemies = [e for e in _enemies if e not in ewar_enemies]
    ordered_enemies = not_ewar_enemies + ewar_enemies
    for i in range(len(ordered_enemies)):
        previous_target_order = best_target_order.copy()
        least_dmg_taken = float("inf")
        for j in range(len(previous_target_order) + 1):
            target_order = previous_target_order.copy()
            target_order.insert(j, ordered_enemies[i])
            stages = []
            __enemies = ordered_enemies.copy()
            for target in target_order:
                stages.append(Stage(__enemies.copy(), target, _player))
                __enemies.remove(target)
            dmg_taken = Stage.calc_total_dmg_taken(stages)
            if dmg_taken < least_dmg_taken:
                least_dmg_taken = dmg_taken
                best_target_order = target_order.copy()
                best_stage_order = stages.copy()

    return best_stage_order


def is_same_order(stages1: List[Stage], stages2: List[Stage]):
    if len(stages2) != len(stages1):
        return False
    for i in range(len(stages1)):
        if stages1[i].target != stages2[i].target:
            return False
    return True


a = None
b = None
c = None

start = time.time()
for _ in range(5):
    a = calc_order_insert(player, enemies)
print((time.time() - start) / 5)

# start = time.time()
# for _ in range(5):
#     b = calc_order_itertools(player, enemies)
# print((time.time() - start) / 5)

start = time.time()
for _ in range(5):
    calc_order_recursive(enemies, [])
    # ___enemies = enemies.copy()
    # c = _best_order
    # for _target in _best_order:
    #     c.append(Stage(___enemies, _target, _player))
    #     ___enemies.remove(_target)
print((time.time() - start) / 5)

print(Stage.calc_total_dmg_taken(a))
print(Stage.calc_total_dmg_taken(_best_order))
print(is_same_order(a, _best_order))

for x in a:
    print(x.target)
print("-----------------")
for x in _best_order:
    print(x.target)

# start = time.time()
# for _ in range(5):
#     c = calc_order(player, enemies)
# print((time.time() - start) / 5)

print("asd")

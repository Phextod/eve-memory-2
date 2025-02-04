from enum import Enum


class DamageType(Enum):
    Explosive = 0
    Kinetic = 1
    EM = 2
    Fire = 3


class PlayerShip:
    def __init__(self):
        self.resists = [
            {DamageType.Fire: 0.1, DamageType.EM: 0.2, DamageType.Kinetic: 0.3, DamageType.Explosive: 0.4},
            {DamageType.Fire: 0.2, DamageType.EM: 0.3, DamageType.Kinetic: 0.4, DamageType.Explosive: 0.5},
            {DamageType.Fire: 0.3, DamageType.EM: 0.4, DamageType.Kinetic: 0.5, DamageType.Explosive: 0.6},
        ]
        self.base_hps = [300, 200, 100]
        self.idk = 0

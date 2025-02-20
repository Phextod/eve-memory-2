from enum import Enum
from typing import Dict, Optional


class DamageType(Enum):
    em = 0
    thermal = 1
    kinetic = 2
    explosive = 3


class Tank:
    def __init__(self, max_hp: int, resist_profile: Dict[DamageType, float], current_hp: Optional[int] = None):
        self.max_hp = max_hp
        self.resist_profile = resist_profile

        if current_hp is None:
            current_hp = max_hp
        self.current_hp = current_hp

    def get_effective_dmg_from(self, damage_profile: Dict[DamageType, int]):
        effective_dmg = dict()
        for damage_type, damage in damage_profile.items():
            resist_multiplier = self.resist_profile[damage_type]
            effective_dmg.update({damage_type: damage * resist_multiplier})

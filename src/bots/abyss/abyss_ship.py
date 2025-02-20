from dataclasses import dataclass
from enum import Enum
from typing import Dict

from src.bots.abyss.ship import Ship
from src.bots.abyss.ship_attributes import Tank, DamageType


@dataclass
class AbyssShip(Ship):
    name: str

    # Additional info
    # primary_ewar: str
    # secondary_ewar: int
    # neut_per_second: int
    orbit_velocity: int
    npc_orbit_range: int

    @staticmethod
    def from_json(in_data: dict, item_data: dict):
        ship_data = dict()

        # General
        ship_data.update({"name": in_data.get("name", None)})

        signature_radius_bonus = in_data.get("signatureRadiusBonus", 0.0) / 100
        ship_data.update({"signature_radius": in_data.get("signatureRadius", 0.0) * (1 + signature_radius_bonus)})

        maximum_velocity_bonus = in_data.get("speedFactor", 0.0) / 100
        ship_data.update({"max_velocity": in_data.get("maxVelocity", 0.0) * (1 + maximum_velocity_bonus)})
        ship_data.update({"orbit_velocity": in_data.get("entityCruiseSpeed", None)})
        ship_data.update({"npc_orbit_range": in_data.get("npcBehaviorMaximumCombatOrbitRange", 0)})

        # Tanks
        # Shield
        shield_max_hp = in_data.get("shieldCapacity", 0)
        shield_resists = {
            DamageType.em: in_data.get("shieldEmDamageResonance", 0.0),
            DamageType.thermal: in_data.get("shieldThermalDamageResonance", 0.0),
            DamageType.kinetic: in_data.get("shieldKineticDamageResonance", 0.0),
            DamageType.explosive: in_data.get("shieldExplosiveDamageResonance", 0.0),
        }
        shield_current_hp = in_data.get("shieldCharge", None)
        ship_data.update({"shield": Tank(shield_max_hp, shield_resists, shield_current_hp)})

        # Armor
        armor_max_hp = in_data.get("armorHP", 0)
        armor_resists = {
            DamageType.em: in_data.get("armorEmDamageResonance", 0),
            DamageType.thermal: in_data.get("armorThermalDamageResonance", 0),
            DamageType.kinetic: in_data.get("armorKineticDamageResonance", 0),
            DamageType.explosive: in_data.get("armorExplosiveDamageResonance", 0),
        }
        current_armor_hp = armor_max_hp - in_data.get("armorDamage", 0.0)
        ship_data.update({"armor": Tank(armor_max_hp, armor_resists, current_armor_hp)})

        # Structure
        structure_max_hp = in_data.get("hp", 0)
        structure_resists = {
            DamageType.em: in_data.get("emDamageResonance", 0.0),
            DamageType.thermal: in_data.get("thermalDamageResonance", 0.0),
            DamageType.kinetic: in_data.get("kineticDamageResonance", 0.0),
            DamageType.explosive: in_data.get("explosiveDamageResonance", 0.0),
        }
        current_structure_hp = structure_max_hp - in_data.get("damage", 0.0)
        ship_data.update({"structure": Tank(structure_max_hp, structure_resists, current_structure_hp)})

        # Offensive
        # Turret
        turret_damage_multiplier = in_data.get("damageMultiplier", 1.0)
        turret_damage_profile = {
            DamageType.em: in_data.get("emDamage", 0.0 * turret_damage_multiplier),
            DamageType.thermal: in_data.get("thermalDamage", 0.0) * turret_damage_multiplier,
            DamageType.kinetic: in_data.get("kineticDamage", 0.0) * turret_damage_multiplier,
            DamageType.explosive: in_data.get("explosiveDamage", 0.0) * turret_damage_multiplier,
        }
        ship_data.update({"turret_damage_profile": turret_damage_profile})
        ship_data.update({"turret_falloff": in_data.get("falloff")})
        ship_data.update({"turret_optimal_range": in_data.get("maxRange")})
        ship_data.update({"turret_tracking": in_data.get("trackingSpeed", 10_000)})

        time_between_shots = in_data.get("speed", 0) / 1000
        ship_data.update({"turret_time_between_shots": time_between_shots})
        damage_multiplier_bonus_per_cycle = in_data.get("damageMultiplierBonusPerCycle", 0.0)
        ship_data.update(
            {"dmg_multiplier_bonus_per_second": damage_multiplier_bonus_per_cycle / (time_between_shots or 1)}
        )
        ship_data.update({"dmg_multiplier_bonus_max": in_data.get("damageMultiplierBonusMax", 0.0)})

        # Missile
        missile_damage_multiplier = in_data.get("missileDamageMultiplier", 1.0)
        missile_type_id = str(in_data.get("entityMissileTypeID", ""))
        missile_data = item_data.get(missile_type_id, dict())
        missile_damage_profile = {
            DamageType.em: missile_data.get("emDamage", 0.0) * missile_damage_multiplier,
            DamageType.thermal: missile_data.get("thermalDamage", 0.0) * missile_damage_multiplier,
            DamageType.kinetic: missile_data.get("kineticDamage", 0.0) * missile_damage_multiplier,
            DamageType.explosive: missile_data.get("explosiveDamage", 0.0) * missile_damage_multiplier,
        }
        ship_data.update({"missile_damage_profile": missile_damage_profile})
        missile_explosion_radius_multiplier = in_data.get("missileEntityAoeCloudSizeMultiplier", 1.0)
        ship_data.update(
            {"missile_explosion_radius": missile_data.get("aoeCloudSize", 0) * missile_explosion_radius_multiplier}
        )
        missile_explosion_velocity_bonus = in_data.get("missileEntityAoeVelocityMultiplier", 1.0)
        ship_data.update(
            {"missile_explosion_velocity": missile_data.get("aoeVelocity", 0) * missile_explosion_velocity_bonus}
        )
        ship_data.update({"missile_damage_reduction_factor": missile_data.get("aoeDamageReductionFactor", 0.0)})
        ship_data.update({"missile_time_between_shots": in_data.get("missileLaunchDuration", 0) / 1000})
        ship_data.update(
            {"missile_range": int((missile_data.get("explosionDelay") / 1000) * missile_data.get("maxVelocity"))}
        )

        return AbyssShip(**ship_data)





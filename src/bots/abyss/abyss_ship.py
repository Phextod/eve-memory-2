from dataclasses import dataclass, field

import numpy as np

from src.bots.abyss.ship import Ship


@dataclass
class AbyssShip(Ship):
    name: str

    # NPC navigation
    orbit_velocity: int
    npc_orbit_range: int

    # EWAR
    web_speed_multiplier: float
    energy_neut_amount: int
    painter_signature_radius_multiplier: float

    optimal_orbit_range: int = field(default=2_500)

    dmg_without_orbit: np.float64 = field(default=np.float64("inf"))
    dmg_with_orbit: np.float64 = field(default=np.float64("inf"))

    def __eq__(self, other: "AbyssShip"):
        return (
            other is not None and
            id(self) == id(other)
        )

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
        ship_data.update({
            "resist_matrix":
                np.array([
                    [
                        in_data.get("shieldEmDamageResonance", 1.0),
                        in_data.get("shieldThermalDamageResonance", 1.0),
                        in_data.get("shieldKineticDamageResonance", 1.0),
                        in_data.get("shieldExplosiveDamageResonance", 1.0),
                    ],
                    [
                        in_data.get("armorEmDamageResonance", 1.0),
                        in_data.get("armorThermalDamageResonance", 1.0),
                        in_data.get("armorKineticDamageResonance", 1.0),
                        in_data.get("armorExplosiveDamageResonance", 1.0),
                    ],
                    [
                        in_data.get("emDamageResonance", 1.0),
                        in_data.get("thermalDamageResonance", 1.0),
                        in_data.get("kineticDamageResonance", 1.0),
                        in_data.get("explosiveDamageResonance", 1.0),
                    ]
                ])
        })

        # Shield
        shield_max_hp = in_data.get("shieldCapacity", 0)
        ship_data.update({"shield_max_hp": shield_max_hp})
        ship_data.update({"shield_hp": in_data.get("shieldCharge", shield_max_hp)})

        # Armor
        armor_max_hp = in_data.get("armorHP", 0)
        ship_data.update({"armor_max_hp": armor_max_hp})
        ship_data.update({"armor_hp": armor_max_hp - in_data.get("armorDamage", 0.0)})

        # Structure
        structure_max_hp = in_data.get("hp", 0)
        ship_data.update({"structure_max_hp": structure_max_hp})
        ship_data.update({"structure_hp": structure_max_hp - in_data.get("damage", 0.0)})

        # Offensive
        # Turret
        turret_damage_multiplier = in_data.get("damageMultiplier", 1.0)
        ship_data.update({
            "turret_damage_profile":
            np.array([
                in_data.get("emDamage", 0.0) * turret_damage_multiplier,
                in_data.get("thermalDamage", 0.0) * turret_damage_multiplier,
                in_data.get("kineticDamage", 0.0) * turret_damage_multiplier,
                in_data.get("explosiveDamage", 0.0) * turret_damage_multiplier,
            ])
        })
        falloff = in_data.get("falloff")
        ship_data.update({"turret_falloff": falloff if falloff is not None and falloff > 0 else 1})
        ship_data.update({"turret_optimal_range": in_data.get("maxRange", 0)})
        ship_data.update({"turret_tracking": in_data.get("trackingSpeed", 10_000)})

        turret_time_between_shots = in_data.get("speed", 0) / 1000
        ship_data.update({"turret_rate_of_fire": 1 / turret_time_between_shots if turret_time_between_shots else 0.0})
        damage_multiplier_bonus_per_cycle = in_data.get("damageMultiplierBonusPerCycle", 0.0)
        ship_data.update(
            {"dmg_multiplier_bonus_per_second": damage_multiplier_bonus_per_cycle / (turret_time_between_shots or 1)}
        )
        ship_data.update({"dmg_multiplier_bonus_max": in_data.get("damageMultiplierBonusMax", 0.0)})

        # Missile
        missile_damage_multiplier = in_data.get("missileDamageMultiplier", 1.0)
        missile_type_id = str(in_data.get("entityMissileTypeID", ""))
        missile_data = item_data.get(missile_type_id, dict())
        ship_data.update({
            "missile_damage_profile":
            np.array([
                missile_data.get("emDamage", 0.0) * missile_damage_multiplier,
                missile_data.get("thermalDamage", 0.0) * missile_damage_multiplier,
                missile_data.get("kineticDamage", 0.0) * missile_damage_multiplier,
                missile_data.get("explosiveDamage", 0.0) * missile_damage_multiplier,
            ])
        })
        missile_explosion_radius_multiplier = in_data.get("missileEntityAoeCloudSizeMultiplier", 1.0)
        ship_data.update(
            {"missile_explosion_radius": missile_data.get("aoeCloudSize", 0) * missile_explosion_radius_multiplier}
        )
        missile_explosion_velocity_bonus = in_data.get("missileEntityAoeVelocityMultiplier", 1.0)
        ship_data.update(
            {"missile_explosion_velocity": missile_data.get("aoeVelocity", 0) * missile_explosion_velocity_bonus}
        )
        ship_data.update({"missile_damage_reduction_factor": missile_data.get("aoeDamageReductionFactor", 0.0)})
        missile_time_between_shots = in_data.get("missileLaunchDuration", 0) / 1000
        ship_data.update(
            {"missile_rate_of_fire": 1 / missile_time_between_shots if missile_time_between_shots else 0.0}
        )
        ship_data.update(
            {"missile_range": int(
                (missile_data.get("explosionDelay", 0) / 1000) *
                missile_data.get("maxVelocity", 0) *
                in_data.get("missileEntityVelocityMultiplier", 1.0) *
                in_data.get("missileEntityFlightTimeMultiplier", 1.0)
            )}
        )

        # EWAR
        ship_data.update({"web_speed_multiplier": in_data.get("speedFactor", 0.0) / 100 + 1})
        ship_data.update({"energy_neut_amount": in_data.get("energyNeutralizerAmount", 0)})
        ship_data.update({"painter_signature_radius_multiplier": in_data.get("signatureRadiusBonus", 0.0) / 100 + 1})

        return AbyssShip(**ship_data)

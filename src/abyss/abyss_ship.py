from dataclasses import dataclass


@dataclass
class AbyssShip:
    name: str
    primary_ewar: str
    neut_per_second: float
    secondary_ewar: str
    total_base_hp: float
    dps: float
    weapon_dps: float
    weapon_optimal: float
    weapon_falloff: float
    weapon_tracking: float
    missile_dps: float
    approximate_missile_range: float
    max_velocity: float
    orbit_velocity: float
    remote_repair_per_second: float
    local_repair_per_second: float

    @staticmethod
    def decode(in_data: dict):
        decode_dict = {
            "type": "name",
            "Primary EWAR": "primary_ewar",
            "GJ Neutralized Per Second": "neut_per_second",
            "Secondary EWAR": "secondary_ewar",
            "Total Base HP": "total_base_hp",
            "Total DPS": "dps",
            "Weapon DPS": "weapon_dps",
            "Weapon Optimal": "weapon_optimal",
            "Weapon Falloff": "weapon_falloff",
            "Weapon Tracking": "weapon_tracking",
            "Missile DPS": "missile_dps",
            "Approximate Missile Range": "approximate_missile_range",
            "Enemy Max Velocity": "max_velocity",
            "Enemy Orbit Velocity": "orbit_velocity",
            "Remote Repair Per Second": "remote_repair_per_second",
            "Local Repair Per Second": "local_repair_per_second",
        }

        out_data = dict()
        for in_key in in_data:
            out_key = decode_dict.get(in_key)
            out_data.update({out_key: in_data.get(in_key)})

        return out_data


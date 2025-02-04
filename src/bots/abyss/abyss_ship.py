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
            "name": "type",
            "primary_ewar": "Primary EWAR",
            "neut_per_second": "GJ Neutralized Per Second",
            "secondary_ewar": "Secondary EWAR",
            "total_base_hp": "Total Base HP",
            "dps": "Total DPS",
            "weapon_dps": "Weapon DPS",
            "weapon_optimal": "Weapon Optimal",
            "weapon_falloff": "Weapon Falloff",
            "weapon_tracking": "Weapon Tracking",
            "missile_dps": "Missile DPS",
            "approximate_missile_range": "Approximate Missile Range",
            "max_velocity": "Enemy Max Velocity",
            "orbit_velocity": "Enemy Orbit Velocity",
            "remote_repair_per_second": "Remote Repair Per Second",
            "local_repair_per_second": "Local Repair Per Second",
        }

        out_data = dict()
        for out_key in decode_dict:
            in_key = decode_dict[out_key]
            out_data.update({out_key: in_data.get(in_key, None)})

        return out_data


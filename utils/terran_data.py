"""
Terran unit and structure data for StarCraft II bot development.
Contains static information about unit costs, build times, and production structures.
"""

from sc2.ids.unit_typeid import UnitTypeId

# Global production structures mapping
PRODUCTION_STRUCTURES = {
    UnitTypeId.SCV: [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS],
    UnitTypeId.MARINE: [UnitTypeId.BARRACKS],
    UnitTypeId.REAPER: [UnitTypeId.BARRACKS],
    UnitTypeId.MARAUDER: [UnitTypeId.BARRACKS],
    UnitTypeId.GHOST: [UnitTypeId.BARRACKS],
    UnitTypeId.HELLION: [UnitTypeId.FACTORY],
    UnitTypeId.HELLIONTANK: [UnitTypeId.FACTORY],
    UnitTypeId.WIDOWMINE: [UnitTypeId.FACTORY],
    UnitTypeId.SIEGETANK: [UnitTypeId.FACTORY],
    UnitTypeId.CYCLONE: [UnitTypeId.FACTORY],
    UnitTypeId.THOR: [UnitTypeId.FACTORY],
    UnitTypeId.VIKINGFIGHTER: [UnitTypeId.STARPORT],
    UnitTypeId.MEDIVAC: [UnitTypeId.STARPORT],
    UnitTypeId.BANSHEE: [UnitTypeId.STARPORT],
    UnitTypeId.RAVEN: [UnitTypeId.STARPORT],
    UnitTypeId.BATTLECRUISER: [UnitTypeId.STARPORT],
    UnitTypeId.LIBERATOR: [UnitTypeId.STARPORT],
}

# Global Terran unit information map
TERRAN_UNIT_INFO = {
    UnitTypeId.SCV: {
        "structure": UnitTypeId.COMMANDCENTER,
        "mineral_cost": 50,
        "gas_cost": 0,
        "supply_cost": 1,
        "build_time": 17.0
    },
    UnitTypeId.MARINE: {
        "structure": UnitTypeId.BARRACKS,
        "mineral_cost": 50,
        "gas_cost": 0,
        "supply_cost": 1,
        "build_time": 25.0
    },
    UnitTypeId.REAPER: {
        "structure": UnitTypeId.BARRACKS,
        "mineral_cost": 50,
        "gas_cost": 50,
        "supply_cost": 1,
        "build_time": 32.0
    },
    UnitTypeId.MARAUDER: {
        "structure": UnitTypeId.BARRACKS,
        "mineral_cost": 100,
        "gas_cost": 25,
        "supply_cost": 2,
        "build_time": 30.0
    },
    UnitTypeId.GHOST: {
        "structure": UnitTypeId.BARRACKS,
        "mineral_cost": 150,
        "gas_cost": 125,
        "supply_cost": 2,
        "build_time": 40.0
    },
    UnitTypeId.HELLION: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 100,
        "gas_cost": 0,
        "supply_cost": 2,
        "build_time": 30.0
    },
    UnitTypeId.HELLIONTANK: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 100,
        "gas_cost": 0,
        "supply_cost": 2,
        "build_time": 30.0
    },
    UnitTypeId.WIDOWMINE: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 75,
        "gas_cost": 25,
        "supply_cost": 2,
        "build_time": 40.0
    },
    UnitTypeId.SIEGETANK: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 150,
        "gas_cost": 125,
        "supply_cost": 3,
        "build_time": 45.0
    },
    UnitTypeId.CYCLONE: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 150,
        "gas_cost": 100,
        "supply_cost": 3,
        "build_time": 32.0
    },
    UnitTypeId.THOR: {
        "structure": UnitTypeId.FACTORY,
        "mineral_cost": 300,
        "gas_cost": 200,
        "supply_cost": 6,
        "build_time": 60.0
    },
    UnitTypeId.VIKINGFIGHTER: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 150,
        "gas_cost": 75,
        "supply_cost": 2,
        "build_time": 42.0
    },
    UnitTypeId.MEDIVAC: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 100,
        "gas_cost": 100,
        "supply_cost": 2,
        "build_time": 42.0
    },
    UnitTypeId.BANSHEE: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 150,
        "gas_cost": 100,
        "supply_cost": 3,
        "build_time": 60.0
    },
    UnitTypeId.RAVEN: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 100,
        "gas_cost": 200,
        "supply_cost": 2,
        "build_time": 60.0
    },
    UnitTypeId.BATTLECRUISER: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 400,
        "gas_cost": 300,
        "supply_cost": 6,
        "build_time": 90.0
    },
    UnitTypeId.LIBERATOR: {
        "structure": UnitTypeId.STARPORT,
        "mineral_cost": 150,
        "gas_cost": 150,
        "supply_cost": 3,
        "build_time": 60.0
    },
}


def get_terran_unit_info(bot=None):
    """Returns the static Terran unit info map."""
    return TERRAN_UNIT_INFO


if __name__ == "__main__":
    # Test the global unit info map
    print("Terran Unit Information:")
    for unit, info in TERRAN_UNIT_INFO.items():
        print(f"{unit.name}: {info['mineral_cost']} minerals, {info['gas_cost']} gas, {info['supply_cost']} supply, {info['build_time']} build time, produced by {info['structure'].name}")

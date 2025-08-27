import math
import sc2reader

# Terran supply costs (add more as needed)
SUPPLY_COST = {
    "SCV": 1,
    "Marine": 1,
    "Marauder": 2,
    "Reaper": 1,
    "Hellion": 2,
    "SiegeTank": 2,
    "Medivac": 2
}

UPGRADE_TIME = {
    # Barracks Tech
    "Stimpack": 140,
    "ShieldWall": 110,  # Combat Shield
    "PunisherGrenades": 110,  # Concussive Shells
    # Factory Tech
    "InfernalPreIgniter": 121,  # Blue Flame
    "DrillClaws": 100,  # Drilling Claws (Widow Mine)
    "CycloneLockOnDamageUpgrade": 79,  # Mag-Field Accelerator
    "HighCapacityBarrels": 100,  # Hellion/Hellbat Infernal Pre-Igniter (duplicate, legacy)
    "SmartServos": 100,
    "TransformationServos": 100,  # Legacy name for Smart Servos
    "RapidFireLaunchers": 100,  # Cyclone Rapid Fire Launchers (Co-op)
    # Starport Tech
    "MedivacBoost": 110,
    "BansheeCloak": 121,
    "RavenCorvidReactor": 79,  # Corvid Reactor (Raven energy)
    "RavenRecalibratedExplosives": 100,  # Raven anti-armor missile (Co-op)
    "LiberatorAGRangeUpgrade": 79,  # Advanced Ballistics
    "CloakingField": 121,  # Banshee Cloak (duplicate, legacy)
    "HyperflightRotors": 121,  # Banshee Speed
    "BattlecruiserEnableSpecializations": 100,  # Tactical Jump (Co-op)
    # Armory Upgrades
    "TerranInfantryWeaponsLevel1": 114,
    "TerranInfantryWeaponsLevel2": 136,
    "TerranInfantryWeaponsLevel3": 157,
    "TerranInfantryArmorsLevel1": 114,
    "TerranInfantryArmorsLevel2": 136,
    "TerranInfantryArmorsLevel3": 157,
    "TerranVehicleWeaponsLevel1": 114,
    "TerranVehicleWeaponsLevel2": 136,
    "TerranVehicleWeaponsLevel3": 157,
    "TerranShipWeaponsLevel1": 114,
    "TerranShipWeaponsLevel2": 136,
    "TerranShipWeaponsLevel3": 157,
    "TerranVehicleAndShipArmorsLevel1": 114,
    "TerranVehicleAndShipArmorsLevel2": 136,
    "TerranVehicleAndShipArmorsLevel3": 157,
    # Engineering Bay
    "HiSecAutoTracking": 79,  # Building Armor
    "TerranBuildingArmor": 100,
    "NeosteelFrame": 100,
    # Ghost Academy
    "MoebiusReactor": 79,  # Ghost energy
    "PersonalCloaking": 79,  # Ghost Cloak
    # Fusion Core
    "BattlecruiserEnableSpecializations": 100,  # Tactical Jump (Co-op)
    # Miscellaneous
    "DrillingClaws": 100,
    "EnhancedShockwaves": 79,  # Ghost EMP
    # Legacy/Co-op/Unused (for completeness)
    "SprayTerran": 0,  # Cosmetic
}

# Load the replay
path = "C:\\Users\\Alex\\Downloads\\BGE Stara Zagora 2025 Replays\\1. Upper Round of 16\\Clem vs Spirit\\1. Ultralove.SC2Replay"
path = "C:\\Users\\Alex\\Downloads\\BGE Stara Zagora 2025 Replays\\1. Upper Round of 16\\Ryung vs Gerald\\2. Pylon LE.SC2Replay"
replay = sc2reader.load_replay(path)

# Get the first player
player = replay.players[1]
base_position = []
building = {}
supply = 0  # Terran starts with 12 supply (can adjust if needed)
build_order = []

for event in replay.events:
    millis = int((event.frame / 16) * 1000)
    if event.name == "UnitBornEvent" and event.control_pid == player.pid:
        unit_name = event.unit_type_name
        cost = SUPPLY_COST.get(unit_name, 0)
        if unit_name == "KD8Charge":
            continue
        if not len(base_position) and unit_name == "SCV":
            base_position.append(event.location)
            building[event.location] = "CommandCenter"
        if event.second > 0:
            build_order.append((millis, supply , "U", unit_name, event.location))
        if cost > 0:
            supply += cost
    elif event.name == "UnitTypeChangeEvent" and event.unit.owner == player:
        build_order.append((millis, supply, "C", event.unit_type_name))
    elif event.name == "UnitInitEvent" and event.control_pid == player.pid:
        unit_name = event.unit_type_name
        if unit_name == "CommandCenter":
            base_position.append(event.location)
        building[event.location] = unit_name
        build_order.append((millis, supply, "B", unit_name, event.location))
    elif event.name == "UpgradeCompleteEvent" and event.player == player:
        upgrade_name = getattr(event, "upgrade_type_name", None)
        start_time = millis - UPGRADE_TIME.get(upgrade_name, 0) * 1000
        if event.second > 0:
            build_order.append((start_time, -1, "G", upgrade_name))

build_order = sorted(build_order, key=lambda x: x[0])

# Save to CSV
import csv

csv_file = "build_order.csv"
with open(csv_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    # Write header
    writer.writerow(["time_ms", "supply", "type", "name", "location"])
    last_supply = 0
    for entry in build_order:
        if entry[2] == "G":
            entry = (entry[0], last_supply, entry[2], entry[3])
        last_supply = entry[1]
        # Some entries may not have a 5th element (location/label)
        row = list(entry)
        while len(row) < 5:
            row.append("")
        writer.writerow(row)
        print(entry)

print(f"Build order saved to {csv_file}")

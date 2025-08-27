from typing import Union
from sc2.bot_ai import BotAI
from sc2.unit import Unit
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId

from .terran_data import PRODUCTION_STRUCTURES, TERRAN_UNIT_INFO

def natural_location(bot: BotAI) -> Point2:
    ramp_pos = bot.main_base_ramp.top_center

    expansion_locations = bot.expansion_locations_list
    expansion_locations = [loc for loc in expansion_locations if loc.distance_to(bot.start_location) > 2]

    return min(expansion_locations, key=lambda mf: mf.distance_to(ramp_pos)).position

def count_planned_structures(bot: BotAI, structure_type: UnitTypeId) -> int:
    """
    Count structures that workers are en route to build.
    """
    planned_count = 0
    
    # Count planned structures (workers en route)
    for worker in bot.workers:
        if worker.orders:
            for order in worker.orders:
                # Check if worker is going to build this structure type
                creation_ability = bot.game_data.units[structure_type.value].creation_ability
                if creation_ability and order.ability.id == creation_ability.id:
                    planned_count += 1
    
    return planned_count

def count_structures(bot: BotAI, structure_type: UnitTypeId) -> int:
    """
    Count structures in ALL states including workers en route, upgrades, etc.
    """
    total_count = 0
    
    # 1. Count completed structures
    total_count += bot.structures(structure_type).amount
    
    # 2. Count planned structures (workers en route)
    total_count += count_planned_structures(bot, structure_type)

    # 3. Remove the double counting of planned/being built structures
    total_count -= bot.structures(structure_type).not_ready.amount

    # 4. Count structures being upgraded/morphed TO this type
    upgrade_mappings = {
        UnitTypeId.ORBITALCOMMAND: UnitTypeId.COMMANDCENTER,
        UnitTypeId.PLANETARYFORTRESS: UnitTypeId.COMMANDCENTER,
        UnitTypeId.SUPPLYDEPOTLOWERED: UnitTypeId.SUPPLYDEPOT,
        # Add more upgrade mappings as needed
    }
    
    if structure_type in upgrade_mappings:
        source_type = upgrade_mappings[structure_type]
        for structure in bot.structures(source_type):
            if structure.orders:
                for order in structure.orders:
                    creation_ability = bot.game_data.units[structure_type.value].creation_ability
                    if creation_ability and order.ability.id == creation_ability.id:
                        total_count += 1
    
    return total_count

def count_units(bot: BotAI, unit_type: UnitTypeId) -> int:
    """
    Count all units of a specific type including:
    - Completed units on the map
    - Units currently in production
    - Units loaded in transports (Medivacs, Bunkers, Command Centers)
    - Units being morphed/transformed
    """
    total_count = 0
    
    # 1. Count completed units on the map
    total_count += bot.units(unit_type).amount
    
    # 2. Count units in production queues
    if unit_type in PRODUCTION_STRUCTURES:
        for structure_type in PRODUCTION_STRUCTURES[unit_type]:
            for structure in bot.structures(structure_type):
                # Count units in production queue
                for order in structure.orders:
                    creation_ability = bot.game_data.units[unit_type.value].creation_ability
                    if creation_ability and order.ability.id == creation_ability.id:
                        total_count += 1
    
    # 3. Count units loaded in transports and bunkers
    # Check Medivacs
    for medivac in bot.units(UnitTypeId.MEDIVAC):
        if hasattr(medivac, 'passengers') and medivac.passengers:
            for passenger in medivac.passengers:
                if passenger.type_id == unit_type:
                    total_count += 1

    # Check Bunkers
    for bunker in bot.structures(UnitTypeId.BUNKER):
        if hasattr(bunker, 'passengers') and bunker.passengers:
            for passenger in bunker.passengers:
                if passenger.type_id == unit_type:
                    total_count += 1

    # Check Command Centers (SCVs can be inside)
    if unit_type == UnitTypeId.SCV:
        for cc in bot.structures({UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS}):
            if hasattr(cc, 'passengers') and cc.passengers:
                for passenger in cc.passengers:
                    if passenger.type_id == unit_type:
                        total_count += 1
    
    # 4. Count units being morphed/transformed (e.g., Hellion -> Hellbat)
    if unit_type == UnitTypeId.HELLIONTANK:
        # Count Hellions that are morphing to Hellbats
        for hellion in bot.units(UnitTypeId.HELLION):
            if hellion.orders and any(order.ability.id == bot.game_data.abilities[UnitTypeId.HELLIONTANK.value].id for order in hellion.orders):
                total_count += 1
    
    return total_count

async def create_unit(bot: BotAI, unit_type: UnitTypeId, count: int = None, target: Union[Unit, Point2] = None):
    """
    Generic unit creation function.
    
    Args:
        bot: The bot instance
        unit_type: The type of unit to create
        count: Maximum number of units to have (optional, if None creates continuously)
        target: Optional specific production structure unit or position to look for closest structure
    """
    # Check count limit if specified
    if count is not None:
        if count_units(bot, unit_type) >= count:
            return
    
    # Get unit info to determine production structure and supply cost
    if unit_type not in TERRAN_UNIT_INFO:
        return  # Unknown unit type
        
    unit_info = TERRAN_UNIT_INFO[unit_type]
    supply_cost = unit_info["supply_cost"]
    
    # Get possible production structures for this unit type
    if unit_type not in PRODUCTION_STRUCTURES:
        return  # No production structures defined
        
    structure_types = PRODUCTION_STRUCTURES[unit_type]
    
    # Find production structures
    production_structures = []
    for structure_type in structure_types:
        production_structures.extend(bot.structures(structure_type).ready.idle)
    
    if not production_structures:
        return  # No available production structures
    
    # Choose which structure to use
    chosen_structure = None
    if target is not None:
        # If target is a unit, use it directly if it's a valid production structure
        if hasattr(target, 'type_id') and target.type_id in structure_types and target.is_ready and target.is_idle:
            chosen_structure = target
        # If target is a position, find closest production structure
        elif hasattr(target, 'position') or hasattr(target, 'x'):
            target_pos = target.position if hasattr(target, 'position') else target
            chosen_structure = min(production_structures, key=lambda s: s.distance_to(target_pos))
        else:
            # Target is probably a position tuple/point
            chosen_structure = min(production_structures, key=lambda s: s.distance_to(target))
    else:
        # No target specified, use first available structure
        chosen_structure = production_structures[0]
    
    # Train the unit if we can afford it and have supply
    if chosen_structure and bot.can_afford(unit_type) and bot.supply_left >= supply_cost:
        chosen_structure.train(unit_type)

async def maintain_supply(bot: BotAI, supply_threshold: int = 12, max_simultaneous: int = 2):
    """Maintain supply by building depots when needed."""
    count_planned = count_planned_structures(bot, UnitTypeId.SUPPLYDEPOT)
    if bot.supply_left < supply_threshold and count_planned < max_simultaneous:
        if bot.can_afford(UnitTypeId.SUPPLYDEPOT):
            await create_supply(bot, near=bot.start_location.towards(bot.enemy_start_locations[0], -7))

async def create_supply(bot_instance: BotAI, near=None):
    """Create a supply depot at a given location (default: near first townhall)."""
    if near is None:
        near = bot_instance.townhalls.first
    await bot_instance.build(UnitTypeId.SUPPLYDEPOT, near=near)

async def next_expansion(bot_instance: BotAI):
    """
    Find the best next expansion location:
    1. Closest mineral field to the main ramp, if space is free.
    2. Otherwise, the next closest to all existing CCs combined.
    Returns the Point2 where a CC should be built, or None if none found.
    """
    from sc2.unit import UnitTypeId
    from sc2.position import Point2
    import math

    # Get all possible expansion locations (mineral fields)
    mineral_fields = bot_instance.mineral_field
    if not mineral_fields:
        return None

    # Get all current CCs and planned CCs
    cc_types = {UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS}
    ccs = bot_instance.structures(cc_types)
    planned_ccs = set()
    if hasattr(bot_instance, "_structure_type_build_commanders"):
        for bc in bot_instance._structure_type_build_commanders.get(UnitTypeId.COMMANDCENTER, []):
            if hasattr(bc, "target_position"):
                planned_ccs.add(bc.target_position)

    # Get all expansion locations (from the map)
    if hasattr(bot_instance, "expansion_locations_list"):
        expansion_locations = bot_instance.expansion_locations_list
    else:
        # fallback: use mineral field clusters
        expansion_locations = [mf.position for mf in mineral_fields]

    # Helper: is a location free?
    def is_location_free(loc):
        for cc in ccs:
            if cc.position.distance_to(loc) < 5:
                return False
        for planned in planned_ccs:
            if planned.distance_to(loc) < 5:
                return False
        return True

    # 1. Closest to main ramp
    ramp = bot_instance.main_base_ramp
    if hasattr(ramp, "top_center"):
        ramp_pos = ramp.top_center
    else:
        ramp_pos = bot_instance.start_location

    # Sort expansion locations by distance to ramp
    sorted_by_ramp = sorted(expansion_locations, key=lambda p: ramp_pos.distance_to(p))
    for loc in sorted_by_ramp:
        if is_location_free(loc):
            return loc

    # 2. Otherwise, pick the one closest to all CCs combined
    if ccs:
        def total_cc_distance(loc):
            return sum(cc.position.distance_to(loc) for cc in ccs)
        sorted_by_ccs = sorted(expansion_locations, key=total_cc_distance)
        for loc in sorted_by_ccs:
            if is_location_free(loc):
                return loc

    return None

async def create_expansion(bot: BotAI, worker: Unit=None):
    """
    Create expansion command centers using custom next_expansion logic.
    Optionally use a specific worker for the build.
    Args:
        bot_instance: The bot instance
        worker: (Optional) The worker unit to use for building
    """
    if bot.can_afford(UnitTypeId.COMMANDCENTER):
        expansion_location = await next_expansion(bot)

        if expansion_location:
            if worker is not None:
                await bot.build(UnitTypeId.COMMANDCENTER, near=expansion_location, build_worker=worker, max_distance=1)
            else:
                await bot.build(UnitTypeId.COMMANDCENTER, near=expansion_location, max_distance=1)

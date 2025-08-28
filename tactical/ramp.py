from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

# Global dictionary to track depot command timestamps
_depot_command_times = {}

async def rally_on_ramp(bot: BotAI):
    """Set all structure rally points to the ramp (except cc)."""
    for structure in bot.structures:
        excluded = [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS]
        if structure.is_ready and not structure.type_id in excluded:
            structure(AbilityId.RALLY_UNITS, bot.main_base_ramp.top_center)


async def handle_ramp_depots(bot: BotAI, distance: float = 7, cooldown: float = 5.0):
    """Raise depots when ground enemies are nearby, lower when safe."""
    global _depot_command_times
    
    # Get all ground enemies (filter out flying units)
    ground_enemies = bot.enemy_units.filter(lambda u: not u.is_flying)

    # Handle lowered depots - raise them if ground enemies are nearby
    for depot in bot.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
        # Check if depot is on cooldown
        if depot.tag in _depot_command_times:
            if bot.time - _depot_command_times[depot.tag] < cooldown:
                continue
        
        # Check if depot should be raised
        should_raise = False
        for unit in ground_enemies:
            if unit.distance_to(depot) < distance:
                should_raise = True
                break
        
        if should_raise:
            depot(AbilityId.MORPH_SUPPLYDEPOT_RAISE)
            _depot_command_times[depot.tag] = bot.time

    # Handle raised depots - lower them if no ground enemies are nearby
    for depot in bot.structures(UnitTypeId.SUPPLYDEPOT).ready:
        # Check if depot is on cooldown
        if depot.tag in _depot_command_times:
            if bot.time - _depot_command_times[depot.tag] < cooldown:
                continue
        
        # Check if any enemies are nearby
        enemy_nearby = False
        for unit in ground_enemies:
            if unit.distance_to(depot) < distance:
                enemy_nearby = True
                break
        
        if not enemy_nearby:
            depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
            _depot_command_times[depot.tag] = bot.time
    
    # Clean up old entries from the command times dictionary
    current_depot_tags = {depot.tag for depot in bot.structures.of_type({UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED})}
    _depot_command_times = {tag: time for tag, time in _depot_command_times.items() if tag in current_depot_tags}

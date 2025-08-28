from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


async def bunker_micro(bot: BotAI):
    """Manage units entering and exiting bunkers."""
    bunkers = bot.structures(UnitTypeId.BUNKER).ready
    marines = bot.units(UnitTypeId.MARINE).idle
    
    for bunker in bunkers:
        # Load marines into bunker if enemies are nearby
        if bunker.cargo_used < bunker.cargo_max:
            enemies_nearby = bot.enemy_units.closer_than(10, bunker)
            if enemies_nearby and marines:
                marine = marines.closest_to(bunker)
                marine.smart(bunker)
        
        # Unload marines if no enemies nearby
        elif bunker.cargo_used > 0:
            enemies_nearby = bot.enemy_units.closer_than(15, bunker)
            if not enemies_nearby:
                bunker(AbilityId.UNLOADALL_BUNKER)

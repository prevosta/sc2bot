from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

async def scout_with_reaper(bot: BotAI):
    """Use reaper for scouting enemy positions."""
    reapers = bot.units(UnitTypeId.REAPER)
    if reapers:
        reaper = reapers.first
        if reaper.is_idle:
            # Send reaper to scout enemy start locations
            enemy_start_locations = bot.enemy_start_locations
            if enemy_start_locations:
                target = enemy_start_locations[0]
                reaper.attack(target)

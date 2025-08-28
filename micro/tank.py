from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


async def siege_on_enemy(bot: BotAI):
    """Siege tanks when enemies are in range, unsiege when no enemies."""
    # Siege tanks if any enemy is in range
    for tank in bot.units(UnitTypeId.SIEGETANK).ready:
        enemies_in_range = bot.enemy_units.in_attack_range_of(tank)
        if enemies_in_range:
            tank(AbilityId.SIEGEMODE_SIEGEMODE)

    # Unsiege tanks if no enemy is in range
    for tank in bot.units(UnitTypeId.SIEGETANKSIEGED).ready:
        enemies_in_range = bot.enemy_units.in_attack_range_of(tank)
        if not enemies_in_range:
            tank(AbilityId.UNSIEGE_UNSIEGE)

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


async def back_to_mining(bot_instance: BotAI):
    """Send idle workers back to mining."""
    for scv in bot_instance.workers.idle:
        scv.gather(bot_instance.mineral_field.closest_to(scv))

async def mule_drop(bot_instance: BotAI):
    """Drop MULEs on mineral patches."""
    for oc in bot_instance.structures(UnitTypeId.ORBITALCOMMAND).ready:
        if oc.energy >= 50:
            mfs = bot_instance.mineral_field.closer_than(10, oc)
            if mfs:
                oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mfs.random)

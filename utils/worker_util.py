from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


async def saturate_gas(bot_instance: BotAI):
    """Saturate refineries with workers."""
    for refinery in bot_instance.gas_buildings:
        if refinery.assigned_harvesters < refinery.ideal_harvesters:
            workers = bot_instance.workers.closer_than(20, refinery)
            for worker in workers:
                if worker.is_gathering and not worker.is_carrying_minerals:
                    worker.gather(refinery)
                    break


async def back_to_mining(bot_instance: BotAI):
    """Send idle workers back to mining."""
    for scv in bot_instance.workers.idle:
        scv.gather(bot_instance.mineral_field.closest_to(scv))


async def balance_workers(bot_instance: BotAI):
    """Balance workers between command centers."""
    ccs = [cc for cc in bot_instance.townhalls.ready if cc.ideal_harvesters > 0]
    if len(ccs) >= 2:
        # Find oversaturated and undersaturated bases
        oversaturated = [cc for cc in ccs if cc.assigned_harvesters > cc.ideal_harvesters]
        undersaturated = [cc for cc in ccs if cc.assigned_harvesters < cc.ideal_harvesters]
        
        for over_cc in oversaturated:
            if not undersaturated:
                break
            under_cc = undersaturated[0]
            
            # Move one worker from oversaturated to undersaturated
            workers_near_over = bot_instance.workers.closer_than(10, over_cc)
            if workers_near_over:
                worker = workers_near_over.first
                minerals_near_under = bot_instance.mineral_field.closer_than(10, under_cc)
                if minerals_near_under:
                    worker.gather(minerals_near_under.closest_to(under_cc))


async def mule_drop(bot_instance: BotAI):
    """Drop MULEs on mineral patches."""
    for oc in bot_instance.structures(UnitTypeId.ORBITALCOMMAND).ready:
        if oc.energy >= 50:
            mfs = bot_instance.mineral_field.closer_than(10, oc)
            if mfs:
                oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mfs.random)

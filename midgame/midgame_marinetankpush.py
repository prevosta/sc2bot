from sc2.ids.unit_typeid import UnitTypeId
from utils.worker_util import saturate_gas, back_to_mining, balance_workers, mule_drop
from utils.production_util import count_structures, create_unit, create_expansion, maintain_supply
from utils.tactical_util import manage_army_positioning, bunker_micro, siege_on_enemy, medivac_support_marine, marine_guard_tank, handle_ramp_depots, rally_on_ramp

async def midgame_build(self):
    # strategy
    await manage_army_positioning(self)

    # Workers
    await saturate_gas(self)
    await back_to_mining(self)
    await balance_workers(self)
    await mule_drop(self)

    # Supply
    await maintain_supply(self)

    # Units
    await rally_on_ramp(self)
    await create_unit(self, UnitTypeId.SCV, self.target_n_worker)
    await create_unit(self, UnitTypeId.SIEGETANK)
    await create_unit(self, UnitTypeId.MARINE, self.target_n_marine)
    await create_unit(self, UnitTypeId.MEDIVAC)

    # Rebuild Expansions
    n_cc = count_structures(self, UnitTypeId.COMMANDCENTER)
    if n_cc < 5:
        self.target_n_worker = n_cc * 22
        await create_expansion(self)

    # micro
    await bunker_micro(self)
    await handle_ramp_depots(self)
    await siege_on_enemy(self)
    await marine_guard_tank(self, support=4)
    await medivac_support_marine(self)

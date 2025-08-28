from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

from strategy.strategy import Strategy
from macro.two_base import MacroTwoBase
from tactical.worker import saturate_gas, balance_workers
from tactical.worker import saturate_gas, balance_workers
from micro.tank import siege_on_enemy
from micro.bunker import bunker_micro
from tactical.ramp import rally_on_ramp, handle_ramp_depots
from micro.worker import  back_to_mining

class PigGold(Strategy):
    async def on_start(self):
        await super().on_start()

        self.macro = MacroTwoBase(self, build_order=[
            # Negative:Non-blocking, None:Non-blocking&Unlimited
            {UnitTypeId.SCV: -19},
            {UnitTypeId.SUPPLYDEPOT: 1},
            {UnitTypeId.BARRACKS: 1},
            {UnitTypeId.REFINERY: 1},
            {UnitTypeId.ORBITALCOMMAND: 1},
            {UnitTypeId.MULE: None},
            {UnitTypeId.REAPER: -1},
            {UnitTypeId.COMMANDCENTER: 1},
            {UnitTypeId.REAPER: 0},  # Don't replace
            {UnitTypeId.SCV: -42},
            {UnitTypeId.SUPPLYDEPOT: 2},
            {UnitTypeId.MARINE: -4},
            {UnitTypeId.FACTORY: 1},
            {UnitTypeId.REFINERY: 2},
            {UnitTypeId.BUNKER: 1},
            {UnitTypeId.STARPORT: 1},
            {UnitTypeId.FACTORYTECHLAB: 1},
            {UnitTypeId.STARPORTTECHLAB: -1},
            {UnitTypeId.SIEGETANK: 1},
            {UnitTypeId.VIKING: 1},
            {UnitTypeId.BARRACKS: 5},
            {UnitTypeId.BARRACKSTECHLAB: 2},
            {UnitTypeId.BARRACKS: 5},
            # Build units till the end...
            {UnitTypeId.SIEGETANK: None},
            {UnitTypeId.MEDIVAC: -4},
            {UnitTypeId.MARINE: None},
            360, # stop muling at 6:00
            {UnitTypeId.MULE: 0},
        ], update = [
            AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK,
            AbilityId.RESEARCH_COMBATSHIELD,
            AbilityId.RESEARCH_TERRANINFANTRYWEAPONS,
            AbilityId.RESEARCH_TERRANINFANTRYARMOR,
            AbilityId.RESEARCH_TERRANINFANTRYWEAPONS,
            AbilityId.RESEARCH_TERRANINFANTRYARMOR,
            AbilityId.RESEARCH_TERRANINFANTRYWEAPONS,
            AbilityId.RESEARCH_TERRANINFANTRYARMOR,
        ])

    async def on_step(self, iteration: int):
        # Strategic
        # Fallback to one-base macro, fast defence if no expansion

        # Macro (Production)
        await self.macro.on_step(iteration)

        # Tactical (Positioning, action)
        await balance_workers(self)
        await saturate_gas(self)
        await rally_on_ramp(self)
        # await scv_scout(self, supply=17)
        # await reaper_scout(self)  # base, proxy, exp
        # await viking_mineral_drop(self)  # if zerg (viking_airspace_cleanup)
        # await tank_defensive_spread(self)
        # await doom_drop(self, army_supply={UnitTypeId.MARINE: 8})
        # await marine_map_vision(self, time=460)
        # await timing_attack(self, time=480, army_supply=75)
        # await seek_and_destroy(self)  # endgame

        # Micro (Unit level interactions)
        await handle_ramp_depots(self)  # raise + scv repair
        await bunker_micro(self)  # fill + scv repair
        await back_to_mining(self)
        await siege_on_enemy(self)
        # await pull_back_damaged_units(self)
        # await stim_on_contact(self, health_threshold=80)

        

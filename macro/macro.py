from sc2.bot_ai import BotAI
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

from micro.production import count_units, create_unit, count_structure
from strategy.map_analysis import MapAnalysis

PRODUCTION_STRUCTURES = {
    UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT,
    UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND,
    UnitTypeId.REFINERY, UnitTypeId.BUNKER,
    UnitTypeId.BARRACKSTECHLAB, UnitTypeId.FACTORYTECHLAB, UnitTypeId.STARPORTTECHLAB
}

BUILD_ORDER = [
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
            {UnitTypeId.FACTORYTECHLAB: -1},
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
        ]

UPGRADE_ORDER = []

class Macro():
    registry: dict[str, type['Macro']] = {}

    def __init__(self, bot: BotAI, build_order = BUILD_ORDER, update_order = UPGRADE_ORDER) -> None:
        self.bot = bot
        self.build_order = build_order
        self.update_order = update_order

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Macro.registry[cls.__name__] = cls

    async def on_step(self, iteration: int) -> None:
        await self.produce()
        await self.upgrade()

    async def produce(self):
        for i, order in enumerate(self.build_order):
            if isinstance(order, int):
                # Wait until game time (in game seconds)
                if self.bot.time < order:
                    break  # Stop processing if we haven't reached this time yet
                continue

            elif isinstance(order, dict):
                unit_type, target = next(iter(order.items()))

                if target == 0:
                    continue  # skip

                # if unit is a structure
                if unit_type in {UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED} | PRODUCTION_STRUCTURES:
                    if target is None:  # Unlimited production
                        await self.produce_structure(unit_type)
                        continue
                    elif count_structure(self.bot, unit_type) < abs(target):
                        await self.produce_structure(unit_type)
                        if target > 0:
                            break

                else:  # Regular units
                    if target is None:  # Unlimited production
                        await create_unit(self.bot, unit_type)
                        continue
                    elif count_units(self.bot, unit_type) < abs(target):
                        await create_unit(self.bot, unit_type)
                        if target > 0:
                            break

    async def produce_structure(self, unit_type: UnitTypeId):
        townhall = self.bot.townhalls.first

        if not self.bot.can_afford(unit_type):
            return

        if unit_type is UnitTypeId.REFINERY:
            vespene = self.bot.vespene_geyser.closest_to(townhall)
            await self.bot.build(UnitTypeId.REFINERY, vespene)
        elif unit_type is UnitTypeId.ORBITALCOMMAND:
             townhall.build(UnitTypeId.ORBITALCOMMAND)
        elif unit_type is UnitTypeId.FACTORYTECHLAB:
            if self.bot.structures(UnitTypeId.FACTORY).ready:
                starport = self.bot.structures(UnitTypeId.FACTORY).ready.first
                if starport and starport.is_idle and starport.add_on_tag == 0:
                    starport(AbilityId.BUILD_TECHLAB_FACTORY)
        elif unit_type is UnitTypeId.STARPORTTECHLAB:
            if self.bot.structures(UnitTypeId.STARPORT).ready:
                starport = self.bot.structures(UnitTypeId.STARPORT).ready.first
                if starport and starport.is_idle and starport.add_on_tag == 0:
                    starport(AbilityId.BUILD_TECHLAB_STARPORT)
        else:
            location = townhall
            if hasattr(self.bot, 'map_analysis'):
                if unit_type in PRODUCTION_STRUCTURES:
                    map_analysis: MapAnalysis = self.bot.map_analysis
                    location = self.valid_location(map_analysis.unit_placement.get("barracks", []))
                if unit_type in {UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED}:
                    map_analysis: MapAnalysis = self.bot.map_analysis
                    location = self.valid_location(map_analysis.unit_placement.get("supply", []))
            await self.bot.build(unit_type, near=location)

    async def produce_unit(self, unit_type: UnitTypeId):
        townhall = self.bot.townhalls.first

        if not self.bot.can_afford(unit_type):
            return

        if unit_type is UnitTypeId.MULE:
            for oc in self.bot.structures(UnitTypeId.ORBITALCOMMAND).ready:
                if oc.energy >= 50:
                    mfs = self.bot.mineral_field.closer_than(10, oc)
                    if mfs:
                        oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mfs.random)
        else:
            self.bot.build(unit_type, near=townhall)
    
    def valid_location(self, locations):
        if locations:
            for loc in locations:
                # Check if location is free (no structures nearby)
                if not self.bot.structures.closer_than(3, loc):
                    return Point2((loc[0], loc[1]))
                
        return self.bot.townhalls.first.position
    
    async def upgrade(self):
        pass

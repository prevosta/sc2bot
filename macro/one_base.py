from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit

from macro.macro import Macro
from micro.worker import saturate_gas, back_to_mining, balance_workers, mule_drop
from micro.production import count_structure, count_units, create_unit
from tactical.tactical import bunker_micro, handle_ramp_depots, siege_on_enemy, rally_on_ramp


class MacroOneBase(Macro):
    def __init__(self, bot: BotAI) -> None:
        self.bot: BotAI = bot

        self.target_n_worker: int = 19
        self.target_n_marine: int = 0
        self.target_n_barracks: int = 0

        self.early_build_order: bool = True
        self.early_worker_spray: bool = True
        self.early_rallypoint: bool = True
        self.early_worker: Unit = None
        self.early_vespene: Unit = None
        self.early_vespene_worker: Unit = None
        self.early_time_to_vespene: float = None
        self.early_vespene_workers: list[Unit] = []
        self.early_factory_worker: Unit = None

    async def on_step(self, iteration: int) -> None:
        townhall = self.bot.townhalls.closest_to(self.bot.start_location)
        depots = self.bot.structures.of_type({UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED})

        if not townhall:
            return

        await handle_ramp_depots(self.bot)
        await rally_on_ramp(self.bot)
        await bunker_micro(self.bot)
        await siege_on_enemy(self.bot)

        # Base production
        await create_unit(self.bot, UnitTypeId.SCV, count=self.target_n_worker)
        await saturate_gas(self.bot)
        await back_to_mining(self.bot)
        # await balance_workers(self)
        await mule_drop(self.bot)
        await create_unit(self.bot, UnitTypeId.MARINE, count=self.target_n_marine)

        #0- Assign each worker to its mineral patch
        if self.early_worker_spray:
            print("0- Assigning workers to mineral patches")
            self.early_worker_spray = False
            for worker in self.bot.workers:
                mineral_patch = self.bot.mineral_field.closest_to(worker)
                worker.gather(mineral_patch)

        #1- Send next worker to ramp
        if self.bot.supply_workers == 12 and self.early_rallypoint:
            if self.bot.townhalls.ready and len(depots) == 0:
                print("1- Sending next worker to ramp")
                townhall(AbilityId.RALLY_COMMANDCENTER, self.bot.corner_depots[0])
                self.early_rallypoint = False

        #2- Send next workers to mineral
        if self.bot.supply_workers == 13:
            if self.bot.townhalls.ready and self.early_worker is None:
                print("2- Sending next worker to minerals")
                townhall(AbilityId.RALLY_COMMANDCENTER, self.bot.mineral_field.closest_to(townhall))
                self.early_worker = self.bot.workers.sorted(lambda w: w.tag)[-1]

        #3- Build Ramp Depot#1
        if self.early_worker and len(depots) == 0:
            if self.bot.can_afford(UnitTypeId.SUPPLYDEPOT):
                print("3- Building Depot#1")
                self.early_worker.build(UnitTypeId.SUPPLYDEPOT, self.bot.corner_depots[0])
                self.early_worker.move(self.bot.main_base_ramp.barracks_correct_placement, queue=True)

        #4- Build Ramp Barrack
        if self.early_worker and len(depots.ready) > 0 and count_structure(self.bot, UnitTypeId.BARRACKS) == 0:
            if self.bot.can_afford(UnitTypeId.BARRACKS) and not self.early_worker.is_constructing_scv:
                print("4- Building Barracks")
                self.early_worker.build(UnitTypeId.BARRACKS, self.bot.main_base_ramp.barracks_correct_placement)
                self.early_worker.gather(self.bot.mineral_field.closest_to(townhall), queue=True)

        #5- Build Refinery
        if self.bot.structures(UnitTypeId.BARRACKS) and count_structure(self.bot, UnitTypeId.REFINERY) == 0:
            if self.early_vespene is None:
                self.early_vespene = self.bot.vespene_geyser.closest_to(townhall)
            if self.early_vespene and self.early_vespene_worker is None:
                available_workers = self.bot.workers.filter(lambda w: not w.is_carrying_minerals and not w.is_constructing_scv)
                self.early_vespene_worker = available_workers.closest_to(self.early_vespene) if available_workers else None
            if self.early_vespene and self.early_vespene_worker and self.bot.can_afford(UnitTypeId.REFINERY):
                print("5- Building Refinery")
                self.early_vespene_worker.build(UnitTypeId.REFINERY, self.early_vespene)
                self.early_time_to_vespene = self.bot.time + 20
                self.early_vespene_worker.move(self.early_vespene.position.towards(townhall, 2), queue=True)

        #6- Pre-saturate the Refinery
        if self.early_time_to_vespene is not None and self.early_time_to_vespene < self.bot.time:
            self.early_time_to_vespene = None
            print("6- Sending 2 workers to vespene")
            available_workers = self.bot.workers.filter(lambda w: w.is_gathering and not w.is_carrying_minerals and not w.is_constructing_scv)
            for _ in range(2):
                worker = available_workers.closest_to(self.early_vespene) if available_workers else None
                available_workers.remove(worker)
                if worker:
                    worker.move(self.early_vespene.position.towards(townhall, 1), queue=True)
                    self.early_vespene_workers.append(worker)

        #7- Saturate the Refinery
        if self.bot.structures(UnitTypeId.REFINERY) and len(self.early_vespene_workers) > 0:
            print("7- Saturating Refinery")
            refinery = self.bot.structures(UnitTypeId.REFINERY).first
            self.early_vespene_worker.move(self.early_vespene.position.towards(townhall, 2))
            self.early_vespene_worker.gather(refinery, queue=True)
            for worker in self.early_vespene_workers:
                worker.gather(refinery)
            del self.early_vespene_workers[:]

        #8- Build Scout Reaper
        if self.bot.structures(UnitTypeId.BARRACKS).ready and count_units(self.bot, UnitTypeId.REAPER) == 0:
            barrack = self.bot.structures(UnitTypeId.BARRACKS).ready.first
            if self.bot.can_afford(UnitTypeId.REAPER) and barrack.is_idle and self.target_n_marine == 0:
                print("8- Building Reaper")
                barrack.train(UnitTypeId.REAPER)
                barrack(AbilityId.RALLY_UNITS, self.bot.main_base_ramp.top_center)
                self.target_n_marine = 2

        #9- Convert to Orbital
        if self.bot.structures(UnitTypeId.BARRACKS).ready and self.bot.target_n_worker == 19:
            if self.bot.can_afford(UnitTypeId.ORBITALCOMMAND) and townhall.is_idle: 
                print("9- Building Orbital Command")
                if townhall.build(UnitTypeId.ORBITALCOMMAND):
                    self.target_n_worker = 42

        #10- Build Ramp Depot#2
        if len(depots) < 2:
            if self.bot.can_afford(UnitTypeId.SUPPLYDEPOT):
                print("Building Depot#2")
                available_workers = self.bot.workers.filter(lambda w: not w.is_carrying_minerals and not w.is_constructing_scv)
                self.early_worker = available_workers.closest_to(self.bot.corner_depots[1]) if available_workers else None
                if self.early_worker:
                    self.early_worker.build(UnitTypeId.SUPPLYDEPOT, self.bot.corner_depots[1])

        #11- Build Ramp Barrack Reactor
        if self.bot.structures(UnitTypeId.BARRACKS).ready:
            barrack = self.bot.structures(UnitTypeId.BARRACKS).ready.first
            if self.bot.can_afford(UnitTypeId.REACTOR) and barrack.is_idle and barrack.add_on_tag == 0:
                print("Building Reactor")
                barrack(AbilityId.BUILD_REACTOR_BARRACKS)

        #12- Build Safety Bunker
        if count_structure(self.bot, UnitTypeId.BUNKER) == 0 and len(depots.ready) >= 2:
            if self.bot.can_afford(UnitTypeId.BUNKER) and not self.early_worker.is_constructing_scv:
                print("Building Safety Bunker")
                # on ramp
                if self.early_worker.build(UnitTypeId.BUNKER, self.bot.main_base_ramp.corner_depots[0]):
                    mineral_position = self.bot.mineral_field.closest_to(townhall)
                    self.early_worker.gather(mineral_position, queue=True)
                    self.target_n_marine = 4

        #13- Build Factory
        if self.bot.structures(UnitTypeId.BARRACKS).ready and not self.bot.structures(UnitTypeId.FACTORY).exists:
            if self.bot.can_afford(UnitTypeId.FACTORY):
                print("Building Factory")
                available_workers = self.bot.workers.filter(lambda w: not w.is_carrying_minerals and not w.is_constructing_scv)
                self.early_factory_worker = available_workers.closest_to(self.bot.start_location) if available_workers else None
                if self.early_factory_worker:
                    self.early_factory_worker.build(UnitTypeId.FACTORY, self.bot.start_location.towards(self.bot.enemy_start_locations[0], 8))

        #14- Build Refinery
        if self.bot.structures(UnitTypeId.FACTORY) and count_structure(self.bot, UnitTypeId.REFINERY) == 1:
            geysers = self.bot.vespene_geyser.closer_than(10, townhall)
            taken_geysers = {ref.position for ref in self.bot.structures(UnitTypeId.REFINERY)}
            free_geysers = [g for g in geysers if g.position not in taken_geysers]
            self.early_vespene = free_geysers[0] if free_geysers else None
            available_workers = self.bot.workers.filter(lambda w: not w.is_carrying_minerals and not w.is_constructing_scv)
            self.early_vespene_worker = available_workers.closest_to(self.early_vespene) if available_workers else None
            if self.early_vespene and self.early_vespene_worker and self.bot.can_afford(UnitTypeId.REFINERY):
                print("Building Refinery")
                self.early_vespene_worker.build(UnitTypeId.REFINERY, self.early_vespene)

        #15- Build Starport
        if self.bot.structures(UnitTypeId.FACTORY).ready and not self.bot.structures(UnitTypeId.STARPORT).exists:
            if self.bot.can_afford(UnitTypeId.STARPORT):
                print("Building Starport")
                factory = self.bot.structures(UnitTypeId.FACTORY).ready.first
                await self.bot.build(UnitTypeId.STARPORT, near=factory)

        #16- Build Factory Tech Lab
        if self.bot.structures(UnitTypeId.STARPORT):
            factory = self.bot.structures(UnitTypeId.FACTORY).ready.first
            if self.bot.can_afford(UnitTypeId.TECHLAB) and factory.is_idle and factory.add_on_tag == 0:
                print("Building Tech Lab")
                factory(AbilityId.BUILD_TECHLAB_FACTORY)

        #17- Build Starport Reactor
        if self.bot.structures(UnitTypeId.STARPORT).ready:
            starport = self.bot.structures(UnitTypeId.STARPORT).ready.first
            if self.bot.can_afford(UnitTypeId.REACTOR) and starport.is_idle and starport.add_on_tag == 0:
                print("Building Reactor")
                starport(AbilityId.BUILD_REACTOR_STARPORT)

        #19- Build a engineering bay
        if (
            self.bot.structures(UnitTypeId.STARPORT).ready
            and count_structure(self.bot, UnitTypeId.ENGINEERINGBAY) == 0
        ):
            if self.bot.can_afford(UnitTypeId.ENGINEERINGBAY):
                print("Building Engineering Bay")
                await self.bot.build(UnitTypeId.ENGINEERINGBAY, near=townhall.position.towards(self.bot.enemy_start_locations[0], -10))

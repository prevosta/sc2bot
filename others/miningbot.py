from __future__ import annotations

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


class FastMiningBot(BotAI):
    def __init__(self):
        super().__init__()
        self.last_step_time = 0
        self.target_worker_count = 0
        self.requested_workers = 15
        self.worker_assignment = {}
        self.start_time = None
        self.first_run = True

    async def on_step(self, iteration):
        # elapse = self.time - self.last_step_time
        # print(f"{iteration} {self.time - self.last_step_time:.2f}ms {1 / elapse if elapse > 0 else 0:.2f}fps")
        # self.last_step_time = self.time

        # Execute all mining tasks
        await self.build_workers()
        await self.distribute_workers()
        await self.micro_workers()
        # await self.build_workers()
        # await self.build_supply()
        # await self.build_refineries()
        # await self.expand_when_needed()
        # await self.manage_orbitals()

        # Stop after 10 seconds
        if self.start_time is None:
            self.start_time = self.time
        if self.time - self.start_time >= 60:
            print(f"Minerals mined in 60 seconds: {self.minerals - 50}")
            await self._client.leave()  # Ends the game
            return
        
        self.first_run = False

    async def build_workers(self):
        # Update worker saturation count
        self.target_worker_count = 0
        for cc in self.townhalls:
            self.target_worker_count += 20
            self.target_worker_count += sum(4 for g in self.gas_buildings if g.distance_to(cc) < 10)
        self.target_worker_count = min(self.target_worker_count, self.requested_workers)

        # build workers
        if self.can_afford(UnitTypeId.SCV) :
            for cc in self.townhalls.ready.idle:
                if self.units(UnitTypeId.SCV).amount < self.target_worker_count:
                    cc.train(UnitTypeId.SCV)

    async def distribute_workers(self):
        nearby_mineral = []
        nearby_gas = []

        # list nearby mineral patches and gas
        for cc in self.townhalls:
            nearby_mineral.extend([m for m in self.mineral_field if m.distance_to(cc) < 10])
            nearby_gas.extend([g for g in self.gas_buildings if g.distance_to(cc) < 10])

        # assign (unassigned) workers
        for worker in self.units(UnitTypeId.SCV):
            if worker.tag in self.worker_assignment:
                continue

            def assigned_harvesters(resource):
                return sum(1 for w in self.units(UnitTypeId.SCV) if w.tag in self.worker_assignment and self.worker_assignment[w.tag] == resource)

            # Prioritize gas (up to 3 workers per geyser)
            available_gas = [g for g in nearby_gas if assigned_harvesters(g) < 3]
            if available_gas:
                available_gas.sort(key=lambda g: (assigned_harvesters(g), g.distance_to(worker)))
                self.worker_assignment[worker.tag] = available_gas[0]
                worker.gather(available_gas[0])
                continue

            # Then assign to minerals (up to 3 workers per patch)
            available_minerals = [m for m in nearby_mineral if assigned_harvesters(m) < 3]
            if available_minerals:
                # available_minerals.sort(key=lambda m: (assigned_harvesters(m), -getattr(m, "mineral_contents", 0), m.distance_to(worker)))
                available_minerals.sort(key=lambda m: (assigned_harvesters(m), m.distance_to(worker)))
                self.worker_assignment[worker.tag] = available_minerals[0]
                worker.gather(available_minerals[0])

        # print({m.tag: sum(1 for w in self.units(UnitTypeId.SCV) if w in self.worker_assignment and self.worker_assignment[w.tag] == m) for m in nearby_mineral})

    async def micro_workers(self):
        # send idle workers to gather resources
        for worker_tag in self.worker_assignment:
            worker = self.units.find_by_tag(worker_tag)
            assigned_resource = self.worker_assignment[worker_tag]
            if worker.is_idle:
                worker.gather(assigned_resource)

def main():
    run_game(maps.get("PylonAIE_v4"), [Bot(Race.Terran, FastMiningBot()), Computer(Race.Zerg, Difficulty.Hard)], realtime=True)

if __name__ == "__main__":
    main()

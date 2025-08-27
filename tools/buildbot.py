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
import csv
import time
import ast

def run_build_order(csv_path):
    build_order = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            loc = row["location"].strip()
            if loc:
                row["location"] = ast.literal_eval(loc)
            else:
                row["location"] = None
            build_order.append(row)
           
    return build_order

class BuildBot(BotAI):
    def __init__(self):
        super().__init__()

        self.build_order = run_build_order("build_order.csv")
        self.townhall = None

    async def on_start(self):
        self.townhall = self.townhalls.first.position
        first_action_location = Point2(self.build_order[0]['location'])
        if self.townhall.distance_to(first_action_location) > 8:
            for x in self.build_order:
                x['location'] = None

    async def on_step(self, iteration):
        supply = self.supply_used

        if not self.build_order:
            await self._client.leave()
            return

        # check if next action is ready to execute
        next_action = self.build_order[0]
        if supply >= int(next_action['supply']):
            name = next_action['name']
            location = Point2(next_action['location']) if next_action['location'] else self.townhall.towards(self.enemy_start_locations[0], 10)

            if next_action['type'] == 'U':
                unit_type = UnitTypeId[name.upper()]
                if unit_type == UnitTypeId.MULE:
                    if await self.build_mule(location):
                        self.build_order.pop(0)
                        print(f"Executing action: {next_action}")
                elif self.can_afford(unit_type):
                    if self.train(unit_type):
                        self.build_order.pop(0)
                        print(f"Executing action: {next_action}")

            if next_action['type'] == 'B':
                building_type = UnitTypeId[name.upper()]
                if building_type == UnitTypeId.REFINERY:
                    if await self.build_refinery(location):
                        self.build_order.pop(0)
                        print(f"Executing action: {next_action}")
                elif building_type == UnitTypeId.COMMANDCENTER:
                    if await self.build_command_center(location):
                        self.build_order.pop(0)
                        print(f"Executing action: {next_action}")
                elif name == "BarracksTechLab":
                    # Build Tech Lab add-on for Barracks near the location
                    for barracks in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        # Only build if no add-on is present
                        if not barracks.has_add_on and barracks.position.distance_to(location) < 25:
                            if self.can_afford(UnitTypeId.TECHLAB):
                                barracks.build(UnitTypeId.TECHLAB)
                                self.build_order.pop(0)
                                print(f"Executing action: {next_action}")
                                break
                elif name == "FactoryTechLab":
                    # Build Tech Lab add-on for Factory near the location
                    for factory in self.structures(UnitTypeId.FACTORY).ready.idle:
                        # Only build if no add-on is present
                        if not factory.has_add_on and factory.position.distance_to(location) < 25:
                            if self.can_afford(UnitTypeId.TECHLAB):
                                factory.build(UnitTypeId.TECHLAB)
                                self.build_order.pop(0)
                                print(f"Executing action: {next_action}")
                                break
                elif self.can_afford(building_type) and self.tech_requirement_progress(building_type) == 1.0:
                    if await self.build(building_type, location):
                        self.build_order.pop(0)
                        print(f"Executing action: {next_action}")

            if next_action['type'] == 'C':
                change_type = UnitTypeId[name.upper()]
                if change_type == UnitTypeId.ORBITALCOMMAND:
                    for cc in self.structures(UnitTypeId.COMMANDCENTER).ready.idle:
                        if self.can_afford(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND):
                            cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
                            self.build_order.pop(0)
                            print(f"Executing action: {next_action}")
                            break
                elif change_type == UnitTypeId.SUPPLYDEPOTLOWERED:
                    # Lower all ready Supply Depots
                    for depot in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
                        depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
                    self.build_order.pop(0)
                    print(f"Executing action: {next_action}")
                else:
                    self.build_order.pop(0)
                    print(f"Skipping action: {next_action}")

            if next_action['type'] == 'G':
                self.build_order.pop(0)
                print(f"Skipping action: {next_action}")

        # Saturate refineries
        for refinery in self.gas_buildings:
            if refinery.assigned_harvesters < refinery.ideal_harvesters:
                worker: Units = self.workers.closer_than(10, refinery)
                if worker:
                    worker.random.gather(refinery)

        # Send workers back to mine if they are idle
        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(self.townhall))

    async def build_mule(self, location):
        # Only call down MULE if we have an OrbitalCommand with energy
        for oc in self.structures(UnitTypeId.ORBITALCOMMAND).ready:
            if oc.energy >= 50:
                mineral_field = self.mineral_field.closest_to(oc)
                return oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mineral_field)

    async def build_refinery(self, location):
        result = None
        geysers = self.vespene_geyser.closer_than(20, location)
        target_geyser = None
        for geyser in geysers:
            # Check if geyser is already taken
            if not self.gas_buildings.closer_than(1.0, geyser):
                target_geyser = geyser
                break
        if target_geyser and self.can_afford(UnitTypeId.REFINERY):
            result = await self.build(UnitTypeId.REFINERY, target_geyser)

        return result

    async def build_command_center(self, location):
        result = None
        if location == self.townhall:
            location = self.mineral_field.closest_to(self.townhall)
        if self.can_afford(UnitTypeId.COMMANDCENTER):
            result = await self.build(UnitTypeId.COMMANDCENTER, location)
        return result

def main():
    run_game(maps.get("PylonAIE_v4"), [
        Bot(Race.Terran, BuildBot()),
        Computer(Race.Zerg, Difficulty.Hard)
    ], realtime=False)

if __name__ == "__main__":
    main()

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


class BCRushBot(BotAI):
    def __init__(self):
        super().__init__()

    def select_target(self, unit: Unit) -> tuple[Point2, bool]:
        """Select an enemy target the units should attack."""
        enemy_start = self.enemy_start_locations[0]

        targets: Units = self.enemy_structures
        if targets:
            return targets.random.position, True

        targets: Units = self.enemy_units
        if targets:
            return targets.random.position, True

        # Find all BCs at enemy_start and idle
        bcs_at_enemy_start = [
            u for u in self.units(UnitTypeId.BATTLECRUISER)
            if u.position.distance_to(enemy_start) < 5 and u.is_idle
        ]

        # If this BC is the "guard" (the one that should stay at enemy_start)
        if bcs_at_enemy_start:
            # If this unit is one of the idle BCs at enemy_start, keep it idle there
            if any(u.tag == unit.tag for u in bcs_at_enemy_start):
                return unit.position, False
        else:
            # If no BC is at enemy_start, send the closest BC there
            all_bcs = self.units(UnitTypeId.BATTLECRUISER)
            if all_bcs:
                closest_bc = all_bcs.closest_to(enemy_start)
                if unit.tag == closest_bc.tag:
                    return enemy_start.position, False

        # All other BCs go to a random mineral field
        return self.mineral_field.random.position, False
    
    def get_proxy_location(self) -> Point2:
        """Returns a proxy location between our base and the enemy start location."""
        my_base = self.start_location
        enemy_base = self.enemy_start_locations[0]
        # Place proxy 3/4 of the way from our base to enemy base
        return my_base.towards(enemy_base, my_base.distance_to(enemy_base) * 0.75)

    async def on_step(self, iteration):
        ccs: Units = self.townhalls
        # If we no longer have townhalls, attack with all workers
        if not ccs:
            for unit in self.workers | self.units(UnitTypeId.BATTLECRUISER):
                target, target_is_enemy_unit = self.select_target(unit)
                if not unit.is_attacking:
                    unit.attack(target)
            return

        cc: Unit = ccs.random
        barracks: Units = self.structures(UnitTypeId.BARRACKS).ready
        bunkers: Units = self.structures(UnitTypeId.BUNKER).ready

        # Send all BCs to attack a target.
        bcs: Units = self.units(UnitTypeId.BATTLECRUISER)
        if bcs:
            bc: Unit
            for bc in bcs:
                target, target_is_enemy_unit = self.select_target(bc)
                # Order the BC to attack-move the target
                if target_is_enemy_unit and (bc.is_idle or bc.is_moving):
                    bc.attack(target)
                # Order the BC to move to the target, and once the select_target returns an attack-target, change it to attack-move
                elif bc.is_idle:
                    bc.move(target)

        # Put Idle Marine in bunker (if any)
        if bunkers:
            for marine in self.units(UnitTypeId.MARINE):
                if marine.is_idle:
                    bunker = bunkers.closest_to(marine)
                    marine(AbilityId.SMART, bunker)

        # Build more SCVs until 22
        if self.can_afford(UnitTypeId.SCV) and self.supply_workers < 22 and cc.is_idle:
            cc.train(UnitTypeId.SCV)

        # Build more Marine until 4
        if self.can_afford(UnitTypeId.MARINE) and barracks.ready.idle and len(self.units(UnitTypeId.MARINE)) < 4:
            barrack = next(iter(barracks.ready.idle))
            if barrack:
                barrack.train(UnitTypeId.MARINE)

        # Build more BCs
        if self.structures(UnitTypeId.FUSIONCORE) and self.can_afford(UnitTypeId.BATTLECRUISER):
            for sp in self.structures(UnitTypeId.STARPORT).idle:
                if sp.has_add_on:
                    if not self.can_afford(UnitTypeId.BATTLECRUISER):
                        break
                    sp.train(UnitTypeId.BATTLECRUISER)

        # Build more supply depots
        if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            await self.build_manager.smart_build(
                UnitTypeId.SUPPLYDEPOT,
                near=cc.position.towards(self.game_info.map_center, 8)
            )

        # Build barracks if we have none
        if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
            if not self.structures(UnitTypeId.BARRACKS):
                await self.build_manager.smart_build(
                    UnitTypeId.BARRACKS,
                    near=cc.position.towards(self.game_info.map_center, 8)
                )

            # Build refineries
            elif self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 2:
                if self.can_afford(UnitTypeId.REFINERY):
                    vgs: Units = self.vespene_geyser.closer_than(20, cc)
                    for vg in vgs:
                        if self.gas_buildings.filter(lambda unit: unit.distance_to(vg) < 1):
                            break

                        worker: Unit = self.select_build_worker(vg.position)
                        if worker is None:
                            break

                        worker.build_gas(vg)
                        break

            # Build a Bunker
            if self.structures(UnitTypeId.BUNKER).amount < 1 and not self.already_pending(UnitTypeId.BUNKER):
                await self.build_manager.smart_build(
                    UnitTypeId.BUNKER,
                    near=cc.position.towards(self.game_info.map_center, 11)
                )

            # Build factory if we dont have one
            if self.tech_requirement_progress(UnitTypeId.FACTORY) == 1:
                factories: Units = self.structures(UnitTypeId.FACTORY)
                if not factories:
                    await self.build_manager.smart_build(
                        UnitTypeId.FACTORY,
                        near=cc.position.towards(self.game_info.map_center, 8)
                    )
                # Build starport once we can build starports, up to 2
                elif (
                    factories.ready
                    and self.structures.of_type({UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING}).ready.amount
                    + self.already_pending(UnitTypeId.STARPORT)
                    < 2
                ):
                    await self.build_manager.smart_build(
                        UnitTypeId.STARPORT,
                        near=self.get_proxy_location(),
                    )

        def starport_points_to_build_addon(sp_position: Point2) -> list[Point2]:
            """Return all points that need to be checked when trying to build an addon. Returns 4 points."""
            addon_offset: Point2 = Point2((2.5, -0.5))
            addon_position: Point2 = sp_position + addon_offset
            addon_points = [
                (addon_position + Point2((x - 0.5, y - 0.5))).rounded for x in range(0, 2) for y in range(0, 2)
            ]
            return addon_points

        # Build starport techlab or lift if no room to build techlab
        sp: Unit
        for sp in self.structures(UnitTypeId.STARPORT).ready.idle:
            if not sp.has_add_on and self.can_afford(UnitTypeId.STARPORTTECHLAB):
                addon_points = starport_points_to_build_addon(sp.position)
                if all(
                    self.in_map_bounds(addon_point)
                    and self.in_placement_grid(addon_point)
                    and self.in_pathing_grid(addon_point)
                    for addon_point in addon_points
                ):
                    sp.build(UnitTypeId.STARPORTTECHLAB)
                else:
                    sp(AbilityId.LIFT)

        def starport_land_positions(sp_position: Point2) -> list[Point2]:
            """Return all points that need to be checked when trying to land at a location where there is enough space to build an addon. Returns 13 points."""
            land_positions = [(sp_position + Point2((x, y))).rounded for x in range(-1, 2) for y in range(-1, 2)]
            return land_positions + starport_points_to_build_addon(sp_position)

        # Find a position to land for a flying starport so that it can build an addon
        for sp in self.structures(UnitTypeId.STARPORTFLYING).idle:
            possible_land_positions_offset = sorted(
                (Point2((x, y)) for x in range(-10, 10) for y in range(-10, 10)),
                key=lambda point: point.x**2 + point.y**2,
            )
            offset_point: Point2 = Point2((-0.5, -0.5))
            possible_land_positions = (sp.position.rounded + offset_point + p for p in possible_land_positions_offset)
            for target_land_position in possible_land_positions:
                land_and_addon_points: list[Point2] = starport_land_positions(target_land_position)
                if all(
                    self.in_map_bounds(land_pos) and self.in_placement_grid(land_pos) and self.in_pathing_grid(land_pos)
                    for land_pos in land_and_addon_points
                ):
                    sp(AbilityId.LAND, target_land_position)
                    break

        # Show where it is flying to and show grid
        unit: Unit
        for sp in self.structures(UnitTypeId.STARPORTFLYING).filter(lambda unit: not unit.is_idle):
            if isinstance(sp.order_target, Point2):
                p: Point3 = Point3((*sp.order_target, self.get_terrain_z_height(sp.order_target)))
                self.client.debug_box2_out(p, color=Point3((255, 0, 0)))

        # Build fusion core
        if self.structures(UnitTypeId.STARPORT).ready: 
            if not self.structures(UnitTypeId.FUSIONCORE) and not self.already_pending(UnitTypeId.FUSIONCORE):
                await self.build_manager.smart_build(
                    UnitTypeId.FUSIONCORE,
                    near=cc.position.towards(self.game_info.map_center, 8)
                )

        # Saturate refineries
        for refinery in self.gas_buildings:
            if refinery.assigned_harvesters < refinery.ideal_harvesters:
                worker: Units = self.workers.closer_than(10, refinery)
                if worker:
                    worker.random.gather(refinery)

        # Send workers back to mine if they are idle
        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(cc))


def main():
    run_game(
        maps.get("PylonAIE_v4"),
        [
            # Human(Race.Terran),
            Bot(Race.Terran, BCRushBot()),
            Computer(Race.Zerg, Difficulty.Hard),
        ],
        realtime=False,
    )

if __name__ == "__main__":
    main()

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


async def manage_army_positioning(bot: BotAI):
    """Basic army positioning and movement."""
    army_units = bot.units.of_type(
        {UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.REAPER, UnitTypeId.HELLION, UnitTypeId.SIEGETANK, UnitTypeId.MEDIVAC}
    )
    
    if army_units and bot.supply_army > 75:
        units_at_enemy = bot.units.closer_than(15, bot.enemy_start_locations[0])
        enemies_at_enemy = bot.enemy_units.closer_than(15, bot.enemy_start_locations[0])

        if units_at_enemy and not enemies_at_enemy:
            locations = bot.expansion_locations_list[1:] if len(bot.enemy_units) == 0 else [bot.enemy_start_locations[0]]
            for i, unit in enumerate(army_units):
                target_loc = locations[i % len(locations)]
                unit.attack(target_loc)

        else:
            for unit in army_units:
                unit.attack(bot.enemy_start_locations[0])

    for structure in bot.structures:
        if structure.health > 0:
            enemies_nearby = bot.enemy_units.closer_than(10, structure)
            if len(enemies_nearby) > 1:
                for unit in army_units:
                    unit.attack(enemies_nearby.closest_to(unit))
                break

async def medivac_support_marine(bot: BotAI):
    """Make medivacs follow marines and heal them when needed."""
    medivacs = bot.units(UnitTypeId.MEDIVAC).ready
    marines = bot.units(UnitTypeId.MARINE).ready
    
    if not medivacs or not marines:
        return
    
    for medivac in medivacs:
        # Find the closest marine to this medivac
        closest_marine = marines.closest_to(medivac)
        
        # Check if any marines need healing (below 80% health)
        injured_marines = marines.filter(lambda m: m.health_percentage < 0.8)
        
        if injured_marines:
            # Heal the closest injured marine
            injured_marine = injured_marines.closest_to(medivac)
            if medivac.distance_to(injured_marine) > 4:
                # Move closer to heal
                medivac.move(injured_marine.position)
            else:
                # Heal the injured marine
                medivac(AbilityId.HEAL_MEDICHEAL, injured_marine)
        else:
            # No injured marines, follow the closest marine
            if medivac.distance_to(closest_marine) > 6:
                # Stay close but not too close (6 range)
                follow_position = closest_marine.position.towards(medivac.position, 4)
                medivac.move(follow_position)
            elif medivac.distance_to(closest_marine) < 3:
                # Too close, back away a bit
                back_position = closest_marine.position.towards(medivac.position, -2)
                medivac.move(back_position)

async def marine_guard_tank(bot: BotAI, support: int = 4):
    """Assign marines to guard each tank, ensuring proper positioning around tanks."""
    # Get all tanks (both regular and sieged)
    tanks = bot.units.of_type({UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED}).ready
    marines = bot.units(UnitTypeId.MARINE).ready
    
    if not tanks or not marines:
        return
    
    # Dictionary to track which marines are assigned to which tank
    assigned_marines = {}
    
    for tank in tanks:
        # Find marines within reasonable distance of this tank
        nearby_marines = marines.closer_than(15, tank)
        
        # Sort marines by distance to tank
        nearby_marines = nearby_marines.sorted(lambda m: m.distance_to(tank))
        
        # Assign up to 'support' number of marines to this tank
        tank_marines = nearby_marines[:support]
        assigned_marines[tank.tag] = tank_marines
        
        # Position marines around the tank in a defensive formation
        for i, marine in enumerate(tank_marines):
            # Calculate position around the tank (spread marines in a circle)
            angle = (i * 360 / support) if support > 0 else 0
            import math
            angle_rad = math.radians(angle)
            
            # Position marines 3-4 units away from tank in a circular formation
            guard_distance = 3.5
            target_x = tank.position.x + guard_distance * math.cos(angle_rad)
            target_y = tank.position.y + guard_distance * math.sin(angle_rad)
            
            from sc2.position import Point2
            guard_position = Point2((target_x, target_y))
            
            # Only move if marine is not already in position or under attack
            if marine.distance_to(guard_position) > 2 and not marine.is_attacking:
                # Check for enemies nearby - if enemies present, marines should engage
                enemies_nearby = bot.enemy_units.closer_than(8, marine)
                if enemies_nearby:
                    # Attack closest enemy
                    marine.attack(enemies_nearby.closest_to(marine))
                else:
                    # Move to guard position
                    marine.move(guard_position)
    
    # Handle unassigned marines - make them guard the closest tank
    all_assigned = set()
    for tank_marines in assigned_marines.values():
        for marine in tank_marines:
            all_assigned.add(marine.tag)
    
    unassigned_marines = marines.filter(lambda m: m.tag not in all_assigned)
    
    for marine in unassigned_marines:
        if tanks:
            closest_tank = tanks.closest_to(marine)
            # Move towards the closest tank that needs more support
            if marine.distance_to(closest_tank) > 5:
                marine.move(closest_tank.position.towards(marine.position, 3))

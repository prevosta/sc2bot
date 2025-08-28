import numpy as np
import cv2
from sc2.bot_ai import BotAI

class MapAnalysis:
    """
    Simplified map analysis module that generates obstruction and unobstructed masks.
    """
    
    # Obstruction type indices
    TERRAIN = 0
    PATHING = 1
    RESOURCES = 2  # Mineral & Vespene
    EXPANSION = 3  # 5x5 expansion locations
    RAMP_STRUCTURES = 4  # Ramp depot/barracks locations
    
    NUM_OBSTRUCTION_TYPES = 5
    
    def __init__(self, bot: BotAI):
        self.bot = bot
        self.width = bot.game_info.placement_grid.width
        self.height = bot.game_info.placement_grid.height
        
        # Initialize the 3D mask [x, y, obstruction_type]
        self.obstruction_mask = np.zeros((self.width, self.height, self.NUM_OBSTRUCTION_TYPES), dtype=bool)
        
        # Initialize unobstructed mask [x, y, expansion_id] - each expansion gets its own layer
        self.expansion_locations_list = list(self.bot.expansion_locations)
        self.num_expansions = len(self.expansion_locations_list)
        self.unobstructed_mask = np.zeros((self.width, self.height, self.num_expansions), dtype=bool)

        # Initialize unit placement
        self.unit_placement = {}
        
    def analyze_map(self):
        """
        Perform complete map analysis and populate obstruction masks.
        """
        print("Starting map analysis...")
        
        # Analyze different obstruction types
        self._analyze_terrain_obstructions()
        self._analyze_pathing_obstructions()
        self._analyze_resource_obstructions()
        self._analyze_expansion_obstructions()
        self._analyze_ramp_structure_obstructions()
        
        # Analyze unobstructed areas for each expansion
        self._analyze_unobstructed_areas()

        # Analyze structure placement
        self._analyze_production_placement()
        self._analyze_supply_placement()
        
        print("Map analysis complete!")
        
    def _analyze_terrain_obstructions(self):
        """Mark terrain obstructions (unbuildable terrain)."""
        for x in range(self.width):
            for y in range(self.height):
                if not self.bot.game_info.placement_grid[x, y]:
                    self.obstruction_mask[x, y, self.TERRAIN] = True
    
    def _analyze_pathing_obstructions(self):
        """Mark pathing obstructions (unwalkable terrain)."""
        for x in range(self.width):
            for y in range(self.height):
                if not self.bot.game_info.pathing_grid[x, y]:
                    self.obstruction_mask[x, y, self.PATHING] = True
    
    def _analyze_resource_obstructions(self):
        """Mark mineral fields and vespene geysers as obstructions."""
        # Mineral field obstructions (2x1 size)
        for mineral in self.bot.mineral_field:
            mx, my = int(mineral.position.x), int(mineral.position.y)
            for dx in range(-1, 1):  # 2 tiles wide
                for dy in range(0, 1):   # 1 tile tall
                    ox, oy = mx + dx, my + dy
                    if 0 <= ox < self.width and 0 <= oy < self.height:
                        self.obstruction_mask[ox, oy, self.RESOURCES] = True
        
        # Vespene geyser obstructions (3x3 size)
        for geyser in self.bot.vespene_geyser:
            gx, gy = int(geyser.position.x), int(geyser.position.y)
            for dx in range(-1, 2):  # 3x3 around center
                for dy in range(-1, 2):
                    ox, oy = gx + dx, gy + dy
                    if 0 <= ox < self.width and 0 <= oy < self.height:
                        self.obstruction_mask[ox, oy, self.RESOURCES] = True
    
    def _analyze_expansion_obstructions(self):
        """Mark 5x5 expansion locations as obstructions."""
        for expansion in self.bot.expansion_locations:
            ex, ey = int(expansion.x), int(expansion.y)
            # 5x5 area around expansion center
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    ox, oy = ex + dx, ey + dy
                    if 0 <= ox < self.width and 0 <= oy < self.height:
                        self.obstruction_mask[ox, oy, self.EXPANSION] = True
    
    def _analyze_ramp_structure_obstructions(self):
        """Mark ramp depot and barracks locations as obstructions."""
        for ramp in self.bot.game_info.map_ramps:
            # Depot positions (2x2 size)
            for depot_pos in getattr(ramp, "corner_depots", []):
                dx, dy = int(depot_pos.x), int(depot_pos.y)
                for ox in range(dx - 1, dx + 1):  # 2x2
                    for oy in range(dy - 1, dy + 1):
                        if 0 <= ox < self.width and 0 <= oy < self.height:
                            self.obstruction_mask[ox, oy, self.RAMP_STRUCTURES] = True
            
            # Barracks positions (3x3 size) - handle potential assertion errors
            barracks_positions = []
            try:
                if hasattr(ramp, 'barracks_correct_placement'):
                    barracks_pos = ramp.barracks_correct_placement
                    if barracks_pos is not None:
                        barracks_positions.append(barracks_pos)
            except (AssertionError, Exception):
                pass
            
            try:
                if hasattr(ramp, 'barracks_in_middle'):
                    barracks_pos = ramp.barracks_in_middle
                    if barracks_pos is not None:
                        barracks_positions.append(barracks_pos)
            except (AssertionError, Exception):
                pass
            
            for barracks_pos in barracks_positions:
                bx, by = int(barracks_pos.x), int(barracks_pos.y)
                for ox in range(bx - 1, bx + 2):  # 3x3
                    for oy in range(by - 1, by + 2):
                        if 0 <= ox < self.width and 0 <= oy < self.height:
                            self.obstruction_mask[ox, oy, self.RAMP_STRUCTURES] = True
    
    def _analyze_unobstructed_areas(self):
        """Analyze unobstructed areas for each expansion location using connected components."""
        print(f"Analyzing unobstructed areas for {self.num_expansions} expansions...")

        for expansion_id, expansion in enumerate(self.expansion_locations_list):
            ex, ey = int(expansion.x), int(expansion.y)

            # Create a mask for potential unobstructed positions within 15 tiles radius
            radius = 25 if expansion.position.distance_to(self.bot.start_location) < 5 else 15
            mask_size = radius * 2 + 1  # 31x31 mask
            temp_mask = np.zeros((mask_size, mask_size), dtype=np.uint8)
            
            # Fill mask with unobstructed positions (inverse of TERRAIN obstruction)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    map_x, map_y = ex + dx, ey + dy
                    mask_x, mask_y = dx + radius, dy + radius  # Convert to mask coordinates
                    
                    # Check if position is within map bounds and within radius
                    if (0 <= map_x < self.width and 
                        0 <= map_y < self.height and
                        dx * dx + dy * dy <= radius * radius):
                        
                        # Mark as unobstructed if not a TERRAIN obstruction
                        if not self.obstruction_mask[map_x, map_y, self.TERRAIN]:
                            temp_mask[mask_y, mask_x] = 255
            
            # Find connected components (blobs)
            num_labels, labels = cv2.connectedComponents(temp_mask, connectivity=8)
            
            # Find which blob contains the expansion location (center of mask)
            expansion_mask_x, expansion_mask_y = radius, radius  # Expansion is at center of mask
            expansion_blob_label = labels[expansion_mask_y, expansion_mask_x]
            
            # Only add positions from the expansion's blob to the unobstructed mask
            if expansion_blob_label > 0:  # 0 is background
                for mask_y in range(mask_size):
                    for mask_x in range(mask_size):
                        if labels[mask_y, mask_x] == expansion_blob_label:
                            # Convert back to world coordinates
                            dx, dy = mask_x - radius, mask_y - radius
                            map_x, map_y = ex + dx, ey + dy
                            
                            # Double check bounds and mark in unobstructed mask
                            if 0 <= map_x < self.width and 0 <= map_y < self.height:
                                self.unobstructed_mask[map_x, map_y, expansion_id] = True
                
                # Remove all other obstruction types from the unobstructed mask
                # Check each position in the blob and remove if it has any obstruction
                positions_to_remove = []
                for x in range(self.width):
                    for y in range(self.height):
                        if self.unobstructed_mask[x, y, expansion_id]:
                            # Check if this position has ANY obstruction type
                            has_obstruction = False
                            for obstruction_type in range(self.NUM_OBSTRUCTION_TYPES):
                                if self.obstruction_mask[x, y, obstruction_type]:
                                    has_obstruction = True
                                    break
                            
                            if has_obstruction:
                                positions_to_remove.append((x, y))
                
                # Remove obstructed positions from the unobstructed mask
                for x, y in positions_to_remove:
                    self.unobstructed_mask[x, y, expansion_id] = False
                
                blob_size = np.sum(self.unobstructed_mask[:, :, expansion_id])
                removed_count = len(positions_to_remove)
                print(f"  Expansion {expansion_id} at ({ex}, {ey}): {blob_size} unobstructed tiles (removed {removed_count} obstructed positions)")
            else:
                print(f"  Expansion {expansion_id} at ({ex}, {ey}): No unobstructed area found")
    
    def _analyze_production_placement(self):
        self.unit_placement["barracks"] = []
        
        # Find the start position expansion ID
        start_expansion_id = None
        for expansion_id, expansion in enumerate(self.expansion_locations_list):
            if expansion.distance_to(self.bot.start_location) < 5:
                start_expansion_id = expansion_id
                break
        
        if start_expansion_id is None:
            print("Warning: Could not find start position expansion")
            return []
        
        start_mask = self.unobstructed_mask[:, :, start_expansion_id].copy()
        
        # Erode the mask by 1 pixel
        start_mask_uint8 = (start_mask * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)  # 3x3 kernel for erosion by 1
        eroded_mask = cv2.erode(start_mask_uint8, kernel, iterations=1)
        working_mask = eroded_mask > 0

        # Greedy algorithm to find blocks
        block_heights = [12, 9, 6]  # Try largest first for better packing
        block_width = 6
        placed_blocks = []
        
        def can_place_block(mask, x, y, w, h):
            """Check if a block of size w x h can be placed at position (x, y)"""
            if x + w > self.width or y + h > self.height:
                return False
            
            for dx in range(w):
                for dy in range(h):
                    if not mask[x + dx, y + dy]:
                        return False
            return True
        
        def place_block(mask, x, y, w, h):
            """Mark the block area as occupied in the mask"""
            for dx in range(w):
                for dy in range(h):
                    mask[x + dx, y + dy] = False
        
        # Keep placing blocks until no more can be placed
        blocks_placed = True
        while blocks_placed:
            blocks_placed = False
            
            # Try each block height in order (largest first)
            for block_height in block_heights:
                best_position = None
                
                # Find the best position for this block height
                for y in range(self.height - block_height + 1):
                    for x in range(self.width - block_width + 1):
                        if can_place_block(working_mask, x, y, block_width, block_height):
                            best_position = (x, y)
                            break
                    if best_position:
                        break
                
                # If we found a position, place the block
                if best_position:
                    x, y = best_position
                    place_block(working_mask, x, y, block_width, block_height)
                    placed_blocks.append([x, y, block_width, block_height])
                    blocks_placed = True
                    break  # Start over with largest blocks again

        # Split blocks into 3-height sub-blocks
        split_blocks = []
        for block in placed_blocks:
            x, y, w, h = block
            
            # Split block into 3-height sub-blocks
            for sub_y in range(y, y + h, 3):
                sub_height = min(3, y + h - sub_y)  # Handle remainder
                split_blocks.append([x, sub_y, 3, 3])

        # sort farthest from the ramp
        start_position = self.bot.start_location
        split_blocks.sort(key=lambda depot: ((depot[0] + 1 - start_position.x) ** 2 + (depot[1] + 1 - start_position.y) ** 2) ** 0.5, reverse=False)

        # Store the blocks found
        self.unit_placement["barracks"] = split_blocks
        
        total_area = sum(block[2] * block[3] for block in split_blocks)
        print(f"Found optimal barracks layout with {len(split_blocks)} blocks covering {total_area} tiles:")
        for i, block in enumerate(split_blocks):
            x, y, w, h = block
            print(f"  Block {i+1}: [{x}, {y}, {w}, {h}] (area: {w*h})")

    def _analyze_supply_placement(self):
        self.unit_placement["supply"] = []
        num_depots = 22  # 24 needed for 200 supply, minus 2 for ramp
        depot_size = 2
    
        # Find the start position expansion ID
        start_expansion_id = None
        for expansion_id, expansion in enumerate(self.expansion_locations_list):
            if expansion.distance_to(self.bot.start_location) < 5:
                start_expansion_id = expansion_id
                break
    
        if start_expansion_id is None:
            print("Warning: Could not find start position expansion")
            return []
    
        # Get the unobstructed mask for the start position
        mask = self.unobstructed_mask[:, :, start_expansion_id].copy()
        
        # Debug: Check if mask has any True values
        total_unobstructed = np.sum(mask)
        print(f"Debug: Total unobstructed tiles in mask: {total_unobstructed}")
        
        if total_unobstructed == 0:
            print("Warning: No unobstructed tiles found for start expansion")
            return []

        # Find all edge pixels of the eroded mask
        edges = find_outer_edge(mask)
            
        # Generate all possible 2x2 depot positions that contain each edge point
        depot_candidates = []
        for edge_x, edge_y in edges:
            possible_depot_positions = [
                (edge_x, edge_y),           # Edge point at top-left (0,0)
                (edge_x - 1, edge_y),       # Edge point at top-right (1,0)
                (edge_x, edge_y - 1),       # Edge point at bottom-left (0,1)
                (edge_x - 1, edge_y - 1)    # Edge point at bottom-right (1,1)
            ]
            
            for depot_x, depot_y in possible_depot_positions:
                # Check if this 2x2 depot position is valid
                if (depot_x >= 0 and depot_y >= 0 and 
                    depot_x + depot_size <= self.width and 
                    depot_y + depot_size <= self.height):
                    
                    # Check if all 4 tiles of the depot are in unobstructed area
                    valid_depot = True
                    for dx in range(depot_size):
                        for dy in range(depot_size):
                            if not mask[depot_x + dx, depot_y + dy]:
                                valid_depot = False
                                break
                        if not valid_depot:
                            break
                    
                    if valid_depot:
                        depot_candidates.append((depot_x, depot_y, edge_x, edge_y))
        
        print(f"Debug: Generated {len(depot_candidates)} valid depot candidates from {len(edges)} edge points")
        
        # Now select non-overlapping depots from candidates
        depot_positions = []
        used_tiles = set()
        
        for depot_x, depot_y, edge_x, edge_y in depot_candidates:
            # Check if this depot overlaps with any already placed depot
            depot_tiles = [(depot_x + dx, depot_y + dy) 
                        for dx in range(depot_size) 
                        for dy in range(depot_size)]
            
            if not any(tile in used_tiles for tile in depot_tiles):
                # Place this depot
                depot_positions.append([depot_x, depot_y, depot_size, depot_size])
                used_tiles.update(depot_tiles)

        # sort farthest from the ramp
        ramp_position = self.bot.main_base_ramp.top_center
        depot_positions.sort(key=lambda depot: ((depot[0] + 1 - ramp_position.x) ** 2 + (depot[1] + 1 - ramp_position.y) ** 2) ** 0.5, reverse=True)

        self.unit_placement["supply"] = depot_positions

        print(f"Found optimal supply depot layout with {len(depot_positions)}")

    def _analyze_turret_placement(self):
        self.unit_placement["turret"] = []
        # mineral
        # at ramp
        # full mineral
        # near edge
        # circonferential
        pass

def find_outer_edge(mask: np.ndarray) -> list:
    # OpenCV expects image format [height, width] or [y, x]
    # Our mask is [x, y], so we need to transpose it to [y, x]
    mask_for_cv = mask.T
    mask_uint8 = (mask_for_cv * 255).astype(np.uint8)
    
    # Find the outer contour only (no holes)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    edge_points = []
    for contour in contours:
        for point in contour:
            # OpenCV returns points as [x, y] in the image coordinate system
            # Since we transposed our mask, these coordinates are already correct
            cv_x, cv_y = point[0]
            x, y = cv_x, cv_y  # These are the correct coordinates in our original [x, y] system
            edge_points.append((x, y))
    
    return edge_points

import cv2
import numpy as np
from sc2.bot_ai import BotAI
from sc2.position import Point2, Point3
from strategy.map_analysis import MapAnalysis

class BaseLimit(BotAI):
    def __init__(self):
        super().__init__()

    async def on_start(self):
        self.map_analysis = MapAnalysis(self)
        self.map_analysis.analyze_map()

        # Create 2D arrays for min and max terrain heights
        self.terrain_min = [[0 for _ in range(self.game_info.placement_grid.height)] for _ in range(self.game_info.placement_grid.width)]
        self.terrain_max = [[0 for _ in range(self.game_info.placement_grid.height)] for _ in range(self.game_info.placement_grid.width)]
        
        # Calculate min/max terrain heights for each grid square
        for x in range(self.game_info.placement_grid.width):
            for y in range(self.game_info.placement_grid.height):
                heights = []
                
                # Sample 3x3 area around each grid position
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        sample_x = max(0, min(self.game_info.placement_grid.width - 1, x + dx))
                        sample_y = max(0, min(self.game_info.placement_grid.height - 1, y + dy))
                        height = self.get_terrain_z_height(Point2((sample_x, sample_y)))
                        heights.append(height)
                
                self.terrain_min[x][y] = min(heights)
                self.terrain_max[x][y] = max(heights)

        # Precompute debug boxes for all unobstructed areas
        self.debug_boxes = []
        for expansion_id in range(self.map_analysis.num_expansions):
            # Get positions where unobstructed_mask is True for this expansion
            unobstructed_positions = np.where(self.map_analysis.unobstructed_mask[:, :, expansion_id])
            for i in range(len(unobstructed_positions[0])):
                x = unobstructed_positions[0][i]
                y = unobstructed_positions[1][i]
                min_height = self.terrain_min[x][y]
                max_height = self.terrain_max[x][y]
                
                p_min = Point3((x, y, min_height - 0.5))
                p_max = Point3((x + 1, y + 1, max_height + 0.5))
                self.debug_boxes.append((p_min, p_max, expansion_id))

        # Precompute barracks debug boxes
        self.barracks_boxes = []
        for unit_name, unit_placement in self.map_analysis.unit_placement.items():
            print(f"Debug: {unit_name} has {len(unit_placement)} placement blocks")
            for i, block in enumerate(unit_placement):
                bx, by, bw, bh = block  # Extract x, y, width, height from block
                
                # Get terrain height at block center
                center_x = bx + bw / 2
                center_y = by + bh / 2
                terrain_height = self.get_terrain_z_height(Point2((center_x, center_y)))

                # Block boundary - blue (shows the entire block area)
                block_min = Point3((bx, by, terrain_height))
                block_max = Point3((bx + bw, by + bh, terrain_height + 2))

                # Text position at center of block
                text_pos = Point3((center_x, center_y, terrain_height + 6))
                
                self.barracks_boxes.append((block_min, block_max, text_pos, unit_name, i))

    async def on_step(self, iteration):
        # Define colors for different expansions
        # for p_min, p_max, expansion_id in self.debug_boxes:
        #     angle = (expansion_id * 360 // max(1, self.map_analysis.num_expansions)) * 3.14159 / 180
        #     r = int(127 * (1 + np.cos(angle)))
        #     g = int(127 * (1 + np.cos(angle + 2.094)))  # 120 degrees offset
        #     b = int(127 * (1 + np.cos(angle + 4.189)))  # 240 degrees offset
        #     self.client.debug_box_out(p_min, p_max, color=(r, g, b))

        # Show barracks placement blocks
        for block_min, block_max, text_pos, unit_name, i in self.barracks_boxes:
            block_text = f"{unit_name}-{i+1}"
            self.client.debug_box_out(block_min, block_max, color=(0, 0, 255))
            self.client.debug_text_world(block_text, text_pos, color=(255, 255, 255), size=14)

def main():
    import random

    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    _map = random.choice(["IncorporealAIE_v4", "PersephoneAIE_v4", "TorchesAIE_v4",  "PylonAIE_v4"])
    run_game(maps.get(_map), [Bot(Race.Terran, BaseLimit()), Computer(Race.Zerg, Difficulty.Hard)], realtime=True)

if __name__ == "__main__":
    main()
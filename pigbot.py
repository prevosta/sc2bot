from sc2.bot_ai import BotAI
from sc2.unit import Unit

from earlygame.earlygame_pig_gold import earlygame_build
from midgame.midgame_marinetankpush import midgame_build

from utils.tactical_util import handle_ramp_depots, siege_on_enemy


class PigBot(BotAI):
    def __init__(self):
        super().__init__()

        self.target_n_worker = 19
        self.target_n_marine = 0
        self.target_n_barracks = 0

        self.early_build_order = True
        self.early_worker_spray = True
        self.early_rallypoint = True
        self.early_worker: Unit = None
        self.early_vespene: Unit = None
        self.early_vespene_worker: Unit = None
        self.early_time_to_vespene = None
        self.early_vespene_workers = []
        self.early_factory_worker: Unit = None

    def on_start(self):
        self.corner_depots = list(self.main_base_ramp.corner_depots)

        return super().on_start()

    async def on_step(self, iteration: int):
        # try:
        await handle_ramp_depots(self)
        await siege_on_enemy(self)

        if self.early_build_order:
            await earlygame_build(self)
        else:
            await midgame_build(self)
        # except Exception as e:
        #     print(f"Exception: {e}")

def main():
    import random

    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    _map = random.choice(["IncorporealAIE_v4", "PersephoneAIE_v4", "TorchesAIE_v4",  "PylonAIE_v4"])
    run_game(maps.get(_map), [Bot(Race.Terran, PigBot()), Computer(Race.Zerg, Difficulty.Hard)], realtime=False)

if __name__ == "__main__":
    main()

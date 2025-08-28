from strategy.pig_gold import PigGold
from strategy.strategy import Strategy

def main():
    import random

    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    _map = random.choice(["IncorporealAIE_v4", "PersephoneAIE_v4", "TorchesAIE_v4",  "PylonAIE_v4"])
    run_game(maps.get(_map), [Bot(Race.Terran, PigGold()), Computer(Race.Zerg, Difficulty.Hard)], realtime=False)

if __name__ == "__main__":
    main()

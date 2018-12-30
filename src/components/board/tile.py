from src.helper.Misc.constants import Terrain


class Tile:
    def __init__(self, terrain):
        self.terrain = terrain
        self.monster = None

    def has_tower(self):
        return self.terrain == Terrain.TOWER


class TileModifier:
    def __init__(self, pos, board):
        self.pos = pos
        self.board = board

    def set_terrain_to(self, terrain):
        self.board.set_terrain_to(self.pos, terrain)

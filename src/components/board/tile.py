from src.helper.Misc.constants import Terrain


class Tile:
    def __init__(self, terrain):
        self.terrain = terrain
        self.monster = None
        self.owner = None

    def has_tower(self):
        return self.terrain == Terrain.TOWER

    def get_terrain_ownership(self):
        if self.has_tower():
            return self.owner


class TileModifier:
    """Decorator class that changes properties of the tile"""

    def __init__(self, tile):
        self.tile = tile

    def set_terrain_to(self, terrain):
        self.tile.terrain = terrain

    def set_monster_to(self, monster):
        self.tile.monster = monster

    # don't use, use the capture terrain method in Board instead
    # def set_terrain_owner_to(self, player_id):
    #     self.tile.owner = player_id

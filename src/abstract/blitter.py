from src.helper.Misc.posconverter import PosConverter

CAPTURED_TOWER_SPRITE = 13


class TileBlitter:
    """Reads the board and blits using the information there"""

    def __init__(self, view, board, camera):
        self.view = view
        self.camera = camera
        self.board = board
        self.pos_converter = PosConverter(camera, self.board.x_max,
                                          self.board.y_max)
        self.terrain_sprites = None

    def blit_surface_at_board_pos(self, sprite, pos):
        """Describe how to draw sprite of board pos to surface"""
        pass

    def blit_all_tiles(self):
        pass

    def blit_terrain_tile_at(self, pos):
        terrain_id = self.board.terrain_at(pos)
        if self._has_owned_tower_at(pos):
            terrain_sprite = self.terrain_sprites.get_sprite(
                CAPTURED_TOWER_SPRITE + self.board.tower_owner_at(pos).id_ + 2)
        else:
            terrain_sprite = self.terrain_sprites.get_sprite(terrain_id)
        self.blit_surface_at_board_pos(terrain_sprite, pos)

    def _has_owned_tower_at(self, pos):
        return (self.board.has_tower_at(pos)
                and self.board.tower_owner_at(pos) is not None)

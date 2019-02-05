import logging

from src.abstract.blitter import TileBlitter
from src.helper.Misc.constants import Color
from src.helper.Misc.options_game import Options
from src.helper.Misc.spritesheet import SpriteSheetFactory

FOG_SPRITE_INDEX = 14


class BoardBlitter(TileBlitter):
    """Used to blit the background of the board view

    Maybe blit this once? Only reblit when terrain changes. Then use a rect
    to say which part of the background should be displayed.
    """
    def __init__(self, view, board, camera):
        super().__init__(view, board, camera)
        self.terrain_sprites = (SpriteSheetFactory()
                                .get_terrain_spritesheet())

    def blit_all_tiles(self):
        logging.info(f'blitting all tiles on {self.view}')
        self.view.background.fill(Color.WHITE)
        self.blit_all_terrain()
        self.blit_all_fog()

    def blit_all_terrain(self):
        """Only blit tiles that are visible on the viewport"""
        if Options.headless:
            return
        x_min, x_max, y_min, y_max = self.view.get_dimensions_of_viewport()
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                self.blit_terrain_tile_at((x, y))

    def blit_surface_at_board_pos(self, sprite, pos):
        surface_pos = self.pos_converter.board_to_surface_pos(pos)
        self.view.background.blit(sprite, surface_pos)

    def blit_all_fog(self):
        if self.view.tiles_to_highlight is None:
            return
        x_min, x_max, y_min, y_max = self.view.get_dimensions_of_viewport()
        fog_sprite = self._get_fog_sprite()
        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                self._blit_tile_transparantly(fog_sprite, (x, y))

    def _get_fog_sprite(self):
        return self.terrain_sprites.get_sprite(FOG_SPRITE_INDEX)

    def _blit_tile_transparantly(self, fog_sprite, pos):
        if pos not in self.view.tiles_to_highlight:
            self.transparent_blit_at_board_pos(fog_sprite, pos)

    def transparent_blit_at_board_pos(self, sprite, pos):
        """todo make sprite in spritesheet transparent instead"""
        sprite.convert_alpha()
        sprite.set_alpha(127)
        self.blit_surface_at_board_pos(sprite, pos)


class MinimapBlitter(TileBlitter):
    """Used to blit dots on the minimap, from the board"""
    def __init__(self, view, board, camera):
        super().__init__(view, board, camera)
        self.size = 6
        self.terrain_sprites = (SpriteSheetFactory()
                                .get_minimap_terrain(self.size))
        self.monster_sprites = (SpriteSheetFactory()
                                .get_minimap_monsters(self.size))

    def blit_all_tiles(self):
        logging.info(f'blitting all tiles on {self.view}')
        self.blit_all_terrain()

    def blit_all_terrain(self):
        """This blits the entire map instead of a viewport"""
        x_max = self.board.x_max
        y_max = self.board.y_max
        for y in range(y_max):
            for x in range(x_max):
                self.blit_terrain_tile_at((x, y))

    def blit_surface_at_board_pos(self, sprite, pos):
        x, y = pos
        right_shift = (y % 2) * (self.size * 0.5)
        surface_pos = (x * self.size + right_shift, y * self.size)
        self.view.background.blit(sprite, surface_pos)

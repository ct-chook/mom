import logging

import pygame

from src.helper.Misc.constants import Terrain
from src.helper.Misc.posconverter import PosConverter
from src.helper.Misc.spritesheet import SpriteSheetFactory

CAPTURED_TOWER_SPRITE = 13
FOG_SPRITE = 14


class TileBlitter:
    def __init__(self, view, board, camera, mode=0):
        self.path = None
        self.monster = None
        self.animated_monster = None
        self.path_index = None
        self.current_pos_on_path = None
        self.surface = None
        self.animation_timer = None

        self.surface: pygame.Surface = None
        self.view = view
        self.camera = camera
        self.board = board
        self.pos_converter = PosConverter(
            camera, self.board.x_max, self.board.y_max)
        self.mode = mode
        self.size = 6  # for minimap

        if mode == 0:
            self.terrain_sprites = \
                SpriteSheetFactory().get_terrain_spritesheet()
            self.monster_sprites = \
                SpriteSheetFactory().get_monster_spritesheets()
        else:
            self.terrain_sprites = \
                SpriteSheetFactory().get_minimap_terrain(self.size)
            self.monster_sprites = \
                SpriteSheetFactory().get_minimap_monsters(self.size)

    def blit_all_tiles(self):
        self.surface = self.view.background
        logging.info(f'blitting all tiles on {self.view}')
        self.blit_all_terrain()
        self.blit_monsters()
        self.blit_all_fog()

    def blit_all_terrain(self):
        x_max = self.__adjust_x_max_for_camera()
        y_max = self.__adjust_y_max_for_camera()
        for y in range(self.camera.y, y_max):
            for x in range(self.camera.x, x_max):
                self.blit_terrain_tile((x, y))

    def blit_terrain_tile(self, pos):
        terrain_id = self.board.terrain_at(pos)
        if terrain_id is None:
            return  # terrain outside bounds
        if (terrain_id == Terrain.TOWER
                and self.board.tower_owner_at(pos) is not None):
            terrain_sprite = self.terrain_sprites.get_sprite(
                CAPTURED_TOWER_SPRITE + self.board.tower_owner_at(pos) + 2)
        else:
            terrain_sprite = self.terrain_sprites.get_sprite(terrain_id)
        self.blit_surface_at_board_pos(terrain_sprite, pos)

    def blit_all_fog(self):
        if self.mode == 1 or self.view.tiles_to_highlight is None:
            return
        x_max = self.__adjust_x_max_for_camera()
        y_max = self.__adjust_y_max_for_camera()
        fog_sprite = self.terrain_sprites.get_sprite(FOG_SPRITE)
        for y in range(self.camera.y, y_max):
            for x in range(self.camera.x, x_max):
                self._blit_transparent_tile(fog_sprite, x, y)

    def _blit_transparent_tile(self, fog_sprite, x, y):
        pos = (x, y)
        if pos not in self.view.tiles_to_highlight:
            self.transparent_blit_at_board_pos(fog_sprite, pos)

    def __adjust_y_max_for_camera(self):
        y_max = self.camera.y + self.camera.height
        if y_max > self.board.y_max:
            y_max = self.board.y_max
        return y_max

    def __adjust_x_max_for_camera(self):
        x_max = self.camera.x + self.camera.width
        if x_max > self.board.x_max:
            x_max = self.board.x_max
        return x_max

    def blit_monsters(self):
        return  # monsters should be sprites

    def transparent_blit_at_board_pos(self, sprite, pos):
        # todo make sprite in spritesheet transparent instead
        sprite.convert_alpha()
        sprite.set_alpha(127)
        self.blit_surface_at_board_pos(sprite, pos)

    def blit_surface_at_board_pos(self, sprite, pos):
        if self.mode == 0:
            surface_pos = self.pos_converter.board_to_surface_pos(pos)
        else:
            right_shift = (pos[1] % 2) * (self.size * 0.5)
            surface_pos = (pos[0] * self.size + right_shift, pos[1] * self.size)
        self.surface.blit(sprite, surface_pos)

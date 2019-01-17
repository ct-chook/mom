import logging

import pygame
from pygame.rect import Rect

from src.abstract.view import View, Sprite
from src.helper.logging_functions import log_time


class MainDisplay:
    def __init__(self, width, height):
        logging.info('Initializing main display')
        self.rectangle = pygame.rect.Rect((0, 0, width, height))
        self.backgrounds_to_update = set()
        self.sprites_to_update = set()
        self.screen = None
        self.top_view: View = None
        self.changed_rects = []

        self._add_self_reference_to_modules()

    def _add_self_reference_to_modules(self):
        View.main_display = self
        Sprite.main_display = self

    def set_pygame_display(self):
        assert not self.screen
        self.screen = pygame.display.set_mode(
            (self.rectangle.width, self.rectangle.height),
            pygame.RESIZABLE)
        View.display_surface = self.screen  # important, cannot blit without
        pass

    def set_top_view(self, view):
        self.top_view = view

    def add_view_to_update_queue(self, view):
        # logging.info(f'added {view} to background update queue')
        self.backgrounds_to_update.add(view)
        # logging.info(
        #     f'right now the background update queue is: '
        #     f'{self.backgrounds_to_update}')

    def add_sprites_to_update_queue(self, view):
        # logging.info(f'added {view} to sprite update queue')
        self.sprites_to_update.add(view)
        # logging.info(
        #     f'right now the sprite update queue is: {self.sprites_to_update}')

    def blit_frame(self):
        updated = False
        if self.backgrounds_to_update:
            # logging.info(f'views to update: {self.backgrounds_to_update}')
            self._update_views_in_queue()
            # debug(self, 'clearing views to update')
            self.backgrounds_to_update.clear()
            updated = True
        if self.sprites_to_update:
            # logging.info(f'sprites to update: {self.sprites_to_update}')
            self._update_sprites_in_queue()
            self.sprites_to_update.clear()
            updated = True
        if updated:
            self._redraw_screen()

    def _update_views_in_queue(self):
        for view in self.backgrounds_to_update:
            # logging.info(f'{self}: updating background of {view}')
            view.update_background()
            self.changed_rects.append(view.get_absolute_rectangle())

    def _update_sprites_in_queue(self):
        for view in self.sprites_to_update:
            # logging.info(f'{self}: updating sprites of view {view}')
            rects = view.update_sprites()
            self.changed_rects.extend(rects)

    def _redraw_screen(self):
        if not self.changed_rects:
            # logging.info('Tried to redraw screen but no rects provided')
            return
        # logging.info(f'Redrawing screen using {len(self.changed_rects)} rects')
        self.top_view.blit_to_display(0, 0)
        #log_time(pygame.display.flip)  # doesn't work for software displays
        # for rect in self.changed_rects:
            # logging.info(
            #     f'Updating with rect: '
            #     f'{rect.x}:{rect.y} {rect.width}x{rect.height}')
        # pygame.display.update()
        # log_time(pygame.display.update, self.changed_rects)
        pygame.display.update(self.changed_rects)
        self.changed_rects = []

    def blit(self, surface, pos):
        self.screen.blit(surface, pos)

    def add_sprite_movement(self, sprite, old_pos, parent):
        self.sprites_to_update.add((sprite, old_pos, parent))

    def __repr__(self):
        return 'maindisplay'

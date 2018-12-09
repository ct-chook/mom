import logging

from src.abstract.window import Window
from pygame.rect import Rect
from src.helper.Misc.constants import Color
from src.helper.Misc.options_game import Options
from src.helper.Misc.tileblitter import TileBlitter
from src.abstract.view import View


class MinimapController(Window):
    def __init__(self, board):
        super().__init__(700, 0, 120, 120)
        self.view: MinimapView = self.add_view(MinimapView, board)


class MinimapView(View):
    def __init__(self, rectangle, board):
        super().__init__(rectangle)
        self.add_text('MinimapView')
        self.set_bg_color(Color.BLACK)
        camera = Rect(0, 0, 100, 100)
        if Options.headless:
            return
        self.tile_blitter = TileBlitter(self, board, camera, 1)
        self.update_background()
        # self.tile_blitter.blit_all_tiles()

    def update_background(self):
        if Options.headless:
            return
        super().update_background()
        self.tile_blitter.blit_all_tiles()
        logging.info('Updated surface of minimapview.')


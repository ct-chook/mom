from pygame.rect import Rect

from src.abstract.view import View
from src.abstract.window import Window
from src.helper.Misc.constants import Color
from src.helper.Misc.options_game import Options
from src.helper.Misc.tileblitter import MinimapBlitter


class MinimapController(Window):
    def __init__(self, board):
        super().__init__(700, 0, 100, 120)
        self.view: MinimapView = self.add_view(MinimapView, board)
        self.view.queue_for_background_update()


class MinimapView(View):
    def __init__(self, rectangle, board):
        super().__init__(rectangle)
        self.set_bg_color(Color.BLACK)
        camera = Rect(0, 0, 100, 100)
        if Options.headless:
            return
        self.tile_blitter = MinimapBlitter(self, board, camera)
        self.queue_for_background_update()

    def update_background(self):
        if Options.headless:
            return
        self.tile_blitter.blit_all_tiles()
        super().update_background()


from src.abstract.window import Window, ButtonMatrix
from math import floor

from src.helper.Misc.constants import TERRAIN_COUNT, is_even, Color
from src.helper.Misc.spritesheet import SpriteSheetFactory
from src.abstract.view import View


class TileEditorWindow(Window):
    def __init__(self):
        super().__init__(1000, 50, 100, 450)
        self.view = self.add_view(TileEditorView)
        self.selected_terrain = None
        self.buttons = self.attach_controller(
            TileEditorButtons(
                0, 100, 50, 50,
                7, 2, self.select_terrain_button))

    def select_terrain_button(self, terrain_id):
        if terrain_id == self.selected_terrain:
            self.selected_terrain = None
        else:
            self.selected_terrain = terrain_id


class TileEditorButtons(ButtonMatrix):
    def __init__(self, x, y, button_width, button_height, rows, cols,
                 callbacks):
        super().__init__(
            x, y, button_width, button_height, rows, cols, callbacks)
        self.add_view(TileEditorButtonsView)


class TileEditorView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('TileEditor')
        self.set_bg_color(Color.GREEN)


class TileEditorButtonsView(View):
    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('TileEditorButtons')
        self.set_bg_color(Color.RED)
        terrain_sprites = SpriteSheetFactory().get_terrain_spritesheet()
        for terrain_id in range(TERRAIN_COUNT):
            surface = terrain_sprites.get_sprite(terrain_id)
            if is_even(terrain_id):
                x = 0
            else:
                x = 50
            y = floor(terrain_id / 2) * 50
            self.add_sprite(surface, (x, y))

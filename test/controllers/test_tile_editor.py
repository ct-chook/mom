import pytest

from src.components.board.board import Board
from src.controller.board_controller import BoardController
from src.controller.tile_editor_controller import TileEditorWindow, \
    TileEditorButtons
from src.helper.Misc.constants import Terrain
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        self.board_controller = BoardController(0, 0, 500, 500)
        self.model = self.board_controller.model
        self.board: Board = self.model.board
        self.before_more()

    def click_on(self, pos):
        self.board_controller.handle_tile_selection(pos)

    def before_more(self):
        pass

    def test(self):
        # for pycharm to recognize this as a testing class
        pass


class TestTileEditor(TestCase):
    def before_more(self):
        self.tile_editor: TileEditorWindow = \
            self.board_controller.tile_editor_window
        self.buttons: TileEditorButtons = self.tile_editor.buttons
        self.tile_pos = (0, 0)

    def test_set_main_fortress(self, before):
        assert self.tile_editor.selected_terrain is None
        self.buttons._handle_button_click(0)
        assert self.tile_editor.selected_terrain == Terrain.CASTLE
        assert self.board.terrain_at(self.tile_pos) == Terrain.GRASS
        self.click_on(self.tile_pos)
        assert self.board.terrain_at(self.tile_pos) == Terrain.CASTLE

    def test_button_off(self, before):
        assert self.tile_editor.selected_terrain is None
        self.buttons._handle_button_click(0)
        assert self.tile_editor.selected_terrain == Terrain.CASTLE
        # now turn button off
        self.buttons._handle_button_click(0)
        assert self.tile_editor.selected_terrain is None
        assert self.board.terrain_at(self.tile_pos) == Terrain.GRASS
        self.click_on(self.tile_pos)
        assert self.board.terrain_at(self.tile_pos) == Terrain.GRASS

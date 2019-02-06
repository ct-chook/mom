import pytest
from pygame.rect import Rect

from src.helper.Misc.posconverter import PosConverter


class Dummy:
    def __init__(self, camera):
        self.camera = camera


tile_size = 2


class TestBoardToSurface:
    @pytest.fixture
    def before(self):
        self.camera = Rect(0, 0, 15, 15)
        self.view = Dummy(self.camera)
        self.converter = PosConverter(self.camera, 15, 15, tile_size, tile_size)

    def test_first_tile_first_row(self, before):
        self.assert_surface_pos((0, 0), 0, 0, 0, 0)
        # def test_second_tile_first_row(self, before_zigzag):
        self.assert_surface_pos((1, 0), 0, 0, tile_size, 0)
        # def test_first_tile_second_row(self, before_zigzag):
        self.assert_surface_pos((0, 1), 0, 0,
                                tile_size * 0.5, self.converter.row_height)
        # def test_second_tile_second_row(self, before_zigzag):
        self.assert_surface_pos(
            (1, 1), 0, 0, tile_size * 1.5, self.converter.row_height)

    def test_camera_x_first_tile_first_row(self, before):
        self.assert_surface_pos((1, 0), 1, 0, 0, 0)
        # def test_camera_x_first_tile_second_row(self, before_zigzag):
        self.assert_surface_pos(
            (1, 1), 1, 0, tile_size * 0.5, self.converter.row_height)
        # def test_CameraXSecondTileFirstRow(self, before_zigzag):
        pos = (2, 0)
        self.camera.x = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == tile_size
        assert surface_y == 0
        # def test_CameraXSecondTileSecondRow(self, before_zigzag):
        pos = (2, 1)
        self.camera.x = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == tile_size * 1.5
        assert surface_y == self.converter.row_height

    def test_camera_y_first_tile_first_row(self, before):
        pos = (0, 1)
        self.camera.y = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == tile_size * 0.5
        assert surface_y == 0
        # def test_CameraYFirstTileSecondRow(self, before_zigzag):
        pos = (0, 2)
        self.camera.y = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == 0
        assert surface_y == self.converter.row_height
        # def test_CameraYSecondTileFirstRow(self, before_zigzag):
        pos = (1, 1)
        self.camera.y = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == tile_size * 1.5
        assert surface_y == 0
        # def test_CameraYSecondTileSecondRow(self, before_zigzag):
        pos = (1, 2)
        self.camera.y = 1
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == tile_size
        assert surface_y == self.converter.row_height

    def assert_surface_pos(self, pos, camera_x, camera_y, x, y):
        self.camera.x = camera_x
        self.camera.y = camera_y
        surface_x, surface_y = self.converter.board_to_surface_pos(pos)
        assert surface_x == x
        assert surface_y == y


class TestBoardToScreen:
    @pytest.fixture
    def before(self):
        self.camera = Rect(0, 0, 15, 15)
        self.view = Dummy(self.camera)
        self.converter = PosConverter(self.camera, 15, 15, 10, 10)
        self.x = 50
        self.y = 50

    def test_if_x_and_y_are_added(self, before):
        pos = (0, 0)
        screen_x, screen_y = self.converter.board_to_screen(
            pos, self.x, self.y)
        assert screen_x == self.x
        assert screen_y == self.y


class TestMouseToBoard:
    @pytest.fixture
    def before(self):
        self.camera = Rect(0, 0, 15, 15)
        self.view = Dummy(self.camera)
        self.x_max = 20
        self.y_max = 16
        self.converter = PosConverter(self.camera, self.x_max, self.y_max,
                                      10, 10)

    def test_top_left(self, before):
        pos = (0, 0)
        board_pos = self.converter.mouse_to_board(pos)
        assert board_pos is None

    def test_left_of_second_row(self, before):
        pos = (0, self.converter.row_height + 1)
        board_pos = self.converter.mouse_to_board(pos)
        assert board_pos is None

import pytest

from src.helper.Misc.options_game import Options
from src.helper.events.events import EventQueue, EventList
from src.controller.board_controller import BoardController


Options.headless = True


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        Options.camera_width = 16
        Options.camera_height = 16

        self.board_controller = BoardController(0, 0, 500, 500)
        self.view = self.board_controller.view


class TestCenterCamera(TestCase):
    def test_center_camera(self, before):
        pos = (0, 0)
        self.view.center_camera_on(pos)
        assert self.view.camera.x == -8
        assert self.view.camera.y == -8

    def test_bottom_right(self, before):
        pos = (4, 4)
        self.view.center_camera_on(pos)
        assert self.view.camera.x == -4
        assert self.view.camera.y == -4

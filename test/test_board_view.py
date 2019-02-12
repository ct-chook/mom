import pytest

from src.abstract.controller import ControllerInfoFactory
from src.controller.board_controller import BoardController
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        info = ControllerInfoFactory().make()
        self.board_controller = BoardController(0, 0, 500, 500, info, None)
        self.view = self.board_controller.view


class TestCenterCamera(TestCase):
    def test_center_camera(self, before):
        pos = (0, 0)
        self.view.center_camera_on(pos)
        assert self.view.camera.x == -7
        assert self.view.camera.y == -7

    def test_bottom_right(self, before):
        pos = (4, 4)
        self.view.center_camera_on(pos)
        assert self.view.camera.x == -3
        assert self.view.camera.y == -3

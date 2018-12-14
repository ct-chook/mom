import pytest

from src.helper.Misc.options_game import Options
from src.helper.events.events import Publisher, EventQueue
from src.controller.board_controller import BoardController

roman_x = 1
roman_y = 19
chim_x = 1
chim_y = 17
crusader_x = 5
crusader_y = 5

roman_start_pos = (roman_x, roman_y)
chim_start_pos = (chim_x, chim_y)
crusader_start_pos = (crusader_x, crusader_y)

left_of_roman_start_pos = (roman_x - 1, roman_y)
next_to_chimera_pos = (roman_x - 1, roman_y - 2)
chimera_pos = (roman_x, roman_y - 2)

daimyou_pos = (9, 11)
left_of_daimyou_pos = (8, 11)
right_of_daimyou_pos = (10, 11)
far_left_of_daimyou_pos = (7, 11)
tower_pos = (4, 4)

top_left = (0, 0)

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        Options.camera_width = 16
        Options.camera_height = 16

        self.board_controller = BoardController(0, 0, 500, 500)
        self.view = self.board_controller.view
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)

    def test(self):
        # for pycharm to recognize this as a testing class
        pass

    def tick_events(self):
        self.publisher.tick_events()



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

import pytest

from src.controller.mom_controller import MomController
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        self.mom_controller = MomController(500, 500)
        self.menu = self.mom_controller.main_menu
        self.menu.start_button.handle_mouseclick()

    def test_set_two_players(self, before):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.menu.mapoptions_window.set_number_of_players(2)
        self.assert_player_count(2)

    def test_set_three_players(self, before):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.menu.mapoptions_window.set_number_of_players(3)
        self.assert_player_count(3)

    def test_set_four_players(self, before):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.menu.mapoptions_window.set_number_of_players(4)
        self.assert_player_count(4)

    def assert_player_count(self, count):
        self.fetch_model()
        assert len(self.model.players) == count

    def fetch_model(self):
        board_controller = self.mom_controller.board_controller
        self.model = board_controller.model

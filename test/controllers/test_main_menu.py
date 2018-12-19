import pytest

from src.components.board.monster import Monster
from src.controller.mainmenu_controller import MainMenuController, \
    MapOptionsWindow
from src.controller.mom_controller import MomController
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        self.mom_controller = MomController(500, 500)
        self.menu: MainMenuController = self.mom_controller.main_menu
        self.options: MapOptionsWindow = self.menu.mapoptions_window
        self.menu.start_button.handle_mouseclick()

    def test_set_two_players(self, before):
        self.assert_player_count(2)

    def test_set_three_players(self, before):
        self.assert_player_count(3)

    def test_set_four_players(self, before):
        self.assert_player_count(4)

    def assert_player_count(self, count):
        self.set_players_and_start(count)
        self.fetch_model()
        assert len(self.model.players) == count

    def test_set_to_darklord(self, before):
        lord_type = Monster.Type.DARKLORD
        self.check_change_summoner_to(lord_type)

    def test_set_to_summoner(self, before):
        lord_type = Monster.Type.SUMMONER
        self.check_change_summoner_to(lord_type)

    def check_change_summoner_to(self, lord_type):
        self.options.set_lord(lord_type)
        self.start()
        self.fetch_model()
        assert self.model.board.lords[0].type == lord_type

    def set_players_and_start(self, n):
        self.options.set_number_of_players(n)
        self.start()

    def start(self):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.options.finish()

    def fetch_model(self):
        board_controller = self.mom_controller.board_controller
        assert board_controller
        self.model = board_controller.model

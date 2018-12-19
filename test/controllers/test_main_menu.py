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
        self.create_new_controllers()

    def create_new_controllers(self):
        self.mom_controller = MomController(500, 500)
        self.menu: MainMenuController = self.mom_controller.main_menu
        self.options: MapOptionsWindow = self.menu.mapoptions_window
        self.menu.start_button.handle_mouseclick()

    def test_check_set_player_count(self):
        self.check_player_count(2)
        self.check_player_count(3)
        self.check_player_count(4)

    def check_player_count(self, count):
        self.create_new_controllers()
        self.set_players_and_start(count)
        self.fetch_model()
        assert len(self.model.players) == count

    def test_change_summoner_to_sixthlord(self, before):
        self.click_summon_button_x_times(0, 5)
        self.start()
        self.fetch_model()
        assert self.model.board.lords[0].type == Monster.Type.SIXTHLORD

    def test_change_summoner_to_daimyou(self, before):
        self.click_summon_button_x_times(0, 6)
        self.start()
        self.fetch_model()
        self.check_lord_type_for_player(Monster.Type.DAIMYOU, 0)

    def test_change_all_summoners(self, before):
        self.click_summon_button_x_times(0, 1)
        self.click_summon_button_x_times(1, 4)
        self.click_summon_button_x_times(2, 0)
        self.click_summon_button_x_times(3, 8)
        self.start()
        self.fetch_model()
        self.check_lord_type_for_player(Monster.Type.WIZARD, 0)
        self.check_lord_type_for_player(Monster.Type.SIXTHLORD, 1)
        self.check_lord_type_for_player(Monster.Type.SORCERER, 2)
        self.check_lord_type_for_player(Monster.Type.SIXTHLORD, 3)

    def check_lord_type_for_player(self, type_, player):
        assert self.model.board.lords[player].type == type_

    def click_summon_button_x_times(self, a, n):
        for _ in range(n):
            self.options.summoner_type_buttons[a].click()

    def set_players_and_start(self, n):
        self.options.player_count_buttons[n - 2].click()
        self.start()

    def start(self):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.options.finish_button.click()

    def fetch_model(self):
        board_controller = self.mom_controller.board_controller
        assert board_controller
        self.model = board_controller.model

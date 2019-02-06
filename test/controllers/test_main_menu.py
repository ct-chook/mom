import pytest

from src.abstract.controller import ControllerInfoFactory
from src.components.board.monster import Monster
from src.controller.mainmenu_controller import MainMenuController, \
    MapOptionsWindow
from src.controller.mom_controller import MomController
from src.helper.Misc.constants import AiType
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        self.create_new_controllers()

    # noinspection PyAttributeOutsideInit
    def create_new_controllers(self):
        info = ControllerInfoFactory().make()
        self.mom_controller = MomController(info, 500, 500)
        self.menu: MainMenuController = self.mom_controller.main_menu
        self.options: MapOptionsWindow = self.menu.mapoptions_window
        self.menu.start_button.handle_mouseclick()

    def set_players_and_start(self, n):
        self.options.player_count_buttons[n - 2].click()
        self.start()

    def start(self):
        self.menu.map_selection_window.pick_map('testempty.map')
        self.options.finish_button.click()
        self.fetch_model()

    # noinspection PyAttributeOutsideInit
    def fetch_model(self):
        board_controller = self.mom_controller.board_controller
        assert board_controller
        self.model = board_controller.model


class TestPlayerCount(TestCase):
    def test_check_set_player_count(self):
        self.check_player_count(2)
        self.check_player_count(3)
        self.check_player_count(4)

    def check_player_count(self, count):
        self.create_new_controllers()
        self.set_players_and_start(count)
        assert len(self.model.players) == count


class TestChangeSummoner(TestCase):
    def test_change_summoner_to_summoner(self, before):
        self.click_summon_button_x_times(0, 4)
        self.start()
        player = self.model.get_current_player()
        lord = self.model.board.lords.get_for(player)
        assert lord.type == Monster.Type.SUMMONER

    def test_change_summoner_to_daimyou(self, before):
        self.click_summon_button_x_times(0, 5)
        self.start()
        self.check_lord_type_for_player(Monster.Type.DAIMYOU, 0)

    def test_change_all_summoners(self, before):
        self.click_summon_button_x_times(0, 1)
        self.click_summon_button_x_times(1, 4)
        self.click_summon_button_x_times(2, 0)
        self.click_summon_button_x_times(3, 6)
        self.start()
        self.check_lord_type_for_player(Monster.Type.WIZARD, 0)
        self.check_lord_type_for_player(Monster.Type.DAIMYOU, 1)
        self.check_lord_type_for_player(Monster.Type.SORCERER, 2)
        self.check_lord_type_for_player(Monster.Type.SUMMONER, 3)

    def check_lord_type_for_player(self, type_, player_id):
        player = self.model.get_player_of_number(player_id)
        lord = self.model.board.lords.get_for(player)
        assert lord.type == type_
        assert self.model.board.monster_at(lord.pos) == lord

    def click_summon_button_x_times(self, a, n):
        for _ in range(n):
            self.options.summoner_type_buttons[a].click()


class TestChangeHumanOrComputer(TestCase):
    def test_default_settings(self, before):
        self.start()
        ai_types = (AiType.human, AiType.default, AiType.default,
                    AiType.default)
        for n in range(4):
            player = self.model.get_player_of_number(n)
            assert player.ai_type == ai_types[n]

    def test_change_player_one_to_computer(self, before):
        self.click_x_times(1)
        assert (self.options.player_type_buttons[0].get_value()
                == AiType.default)
        self.start()
        player = self.model.get_current_player()
        assert player.ai_type == AiType.default, (
            f'Player type was {player.ai_type}')

    def click_x_times(self, x):
        for _ in range(x):
            self.options.player_type_buttons[0].click()


class TestTeams(TestCase):
    def test_no_teams(self, before):
        self.click_team_button_x_times(1, 0)
        self.start()
        player_1 = self.model.board.players[0]
        player_2 = self.model.board.players[1]
        assert player_1.team == 1
        assert player_2.team == 0

    def click_team_button_x_times(self, x, row):
        for _ in range(x):
            self.options.team_buttons[row].click()

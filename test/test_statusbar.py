import pytest

from src.abstract.controller import ControllerInfoFactory
from src.controller.statusbar_controller import StatusbarController, \
    PlayerstatsView
from src.model.board_model import BoardModel
from src.helper.Misc.options_game import Options

Options.headless = True


class TestCase:
    @pytest.fixture
    def before(self):
        model = BoardModel()
        info = ControllerInfoFactory().make()
        self.bar = StatusbarController(0, 0, info, model)

    def test_statusbar(self, before):
        self.bar.update_stats()
        player_1: PlayerstatsView = self.bar.stats[0].view
        assert player_1.color.text == 'BLUE'
        assert player_1.monsters.text == '1/7'
        assert player_1.mp.text == '100 MP'
        player_2: PlayerstatsView = self.bar.stats[1].view
        assert player_2.color.text == 'RED'

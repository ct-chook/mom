import pytest

from src.helper.Misc.options_game import Options
from src.controller.board_controller import BoardController

from src.helper.Misc.constants import Terrain, DayTime, MonsterType
from src.components.combat.attack import AttackFactory
from src.components.board.monster import Monster
from src.helper.events.events import Publisher, EventQueue

Options.headless = True
PLAYER, OPPONENT = range(2)


class TestCase:
    window = None
    view = None
    publisher = None

    @pytest.fixture
    def before(self):
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)
        self.board_window = BoardController(0, 0, 1000, 1000)
        self.window = self.board_window.combat_window
        self.view = self.window.view
        attack_range = 0
        sun_stance = DayTime.NOON
        monsters = (
            Monster(MonsterType.HYDRA, (0, 0), PLAYER, Terrain.GRASS),
            Monster(MonsterType.SIRENE, (1, 0), OPPONENT, Terrain.GRASS))
        # monsters[0].tile = Tile(Terrain.DUNE)
        # monsters[1].tile = Tile(Terrain.SWAMP)
        attacks = AttackFactory().get_all_attacks_between_monsters(
            monsters, sun_stance)
        self.window.on_combat(attacks, attack_range)
        self.tick(1)

    def test_round_numbers(self, before):
        self.tick(115)
        assert 0 == self.view.round_number
        self.tick(10)
        assert 1 == self.view.round_number
        self.tick(110)
        assert 1 == self.view.round_number
        self.tick(10)
        assert 2 == self.view.round_number

    def tick(self, count):
        for _ in range(count):
            self.publisher.tick_events()

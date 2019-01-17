import pytest

from controller.combat_controller import CombatView
from src.helper.Misc.options_game import Options
from src.controller.board_controller import BoardController

from src.helper.Misc.constants import Terrain, DayTime, MonsterType
from src.components.combat.attack import AttackFactory
from src.components.board.monster import Monster
from src.helper.events.events import EventQueue, EventList

Options.headless = True
PLAYER, OPPONENT = range(2)


class TestCase:
    @pytest.fixture
    def before(self):
        self.publisher = EventQueue()
        EventList.set_publisher(self.publisher)
        self.board_window = BoardController(0, 0, 1000, 1000)
        self.window = self.board_window.combat_window
        self.view = self.window.view
        self.delay = CombatView.COMBAT_DELAY
        attack_range = 0
        sun_stance = DayTime.NOON
        monsters = (
            Monster(MonsterType.HYDRA, (0, 0), PLAYER, Terrain.GRASS),
            Monster(MonsterType.SIRENE, (1, 0), OPPONENT, Terrain.GRASS))
        attacks = AttackFactory().get_all_attacks_between_monsters(
            monsters, sun_stance)
        self.window.on_combat(attacks, attack_range)
        self.tick(1)

    def test_round_numbers(self, before):
        self.tick(self.delay - 1)
        assert self.view.round_number == 0
        self.tick(1)
        assert self.view.round_number == 1
        self.tick(self.delay - 1)
        assert self.view.round_number == 1
        self.tick(1)
        assert self.view.round_number == 2

    def tick(self, count):
        for _ in range(count):
            self.publisher.tick_events()

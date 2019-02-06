import pytest

from src.abstract.controller import ControllerInfoFactory
from src.components.board.monster import Monster
from src.components.board.players import Player
from src.components.combat.attack import AttackFactory
from src.components.combat.combat import Combat
from src.components.combat.combatlog import CombatRound
from src.controller.combat_controller import CombatWindow
from src.helper.Misc.constants import Terrain, DayTime, MonsterType
from src.helper.Misc.options_game import Options

Options.headless = True
Combat.perfect_accuracy = True


class Dummy:
    def __init__(self):
        self.view = DummyView()

    def unfreeze_events(self):
        pass


class DummyView:
    def clear_highlighted_tiles(self):
        pass


class TestCase:
    @pytest.fixture
    def before(self):
        info = ControllerInfoFactory().make()
        self.window = CombatWindow(info)
        # needed since combat window makes callbacks to parent
        self.window.parent = Dummy()
        self.publisher = info.publisher
        self.view = self.window.view
        self.delay = self.view.COMBAT_DELAY
        self.round = 0
        self.player_1 = Player(0)
        self.player_2 = Player(1)
        self.left_monster = Monster(MonsterType.HYDRA, (0, 0), self.player_1,
                                    Terrain.GRASS)
        self.right_monster = Monster(MonsterType.SIRENE, (1, 0), self.player_2,
                                     Terrain.GRASS)
        self.hp_left = self.left_monster.hp
        self.hp_right = self.right_monster.hp
        monsters = (self.left_monster, self.right_monster)
        sun_stance = DayTime.NOON
        self.attacks = AttackFactory().get_all_attacks_between_monsters(
            monsters, sun_stance)
        attack_range = 0
        self.window.on_combat(self.attacks, attack_range)
        self.tick(1)

    def test_round_numbers(self, before):
        assert self.view
        self.apply_round_damage()
        self.check_round()
        self.check_round()
        self.check_hp()
        assert self.view.round_number == self.round

    def check_round(self):
        self.check_hp()
        self.tick(self.delay - 1)
        self.check_hp()
        assert self.view.round_number == self.round
        self.tick(1)
        self.round += 1
        self.apply_round_damage()

    def check_hp(self):
        assert self.view.hp_left_text.text == (
            f'{self.hp_left}/{self.left_monster.stats.max_hp}'),\
            'left hp wrong'
        assert self.view.hp_right_text.text == (
            f'{self.hp_right}/{self.right_monster.stats.max_hp}'), \
            'right hp wrong'

    def apply_round_damage(self):
        combat_log = self.window.combat_log
        combat_round: CombatRound = combat_log.rounds[self.round]
        if combat_round.damage > -1:
            if combat_round.side == 1:
                self.hp_left -= combat_round.damage
            else:
                self.hp_right -= combat_round.damage

    def tick(self, count):
        for _ in range(count):
            self.publisher.tick_events()
            # skipped in headless mode
            self.view.update_sprites()

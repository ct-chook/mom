import pytest

from src.components.board.monster import Monster
from src.components.board.players import Player
from src.helper.Misc.constants import MonsterType, Terrain
from src.components.combat.combat import Combat
from src.components.combat.attack import Attack
from src.controller.board_controller import BoardModel


DAY, SUNSET, NIGHT, SUNRISE = range(4)
CLOSE_RANGE, LONG_RANGE = range(2)


class CombatTest:
    combat_result = None

    @pytest.fixture
    def before(self):
        self.player_1 = Player(0)
        self.attack = Attack
        self.monster = Monster(Monster.Type.TROLL, (0, 0), self.player_1,
                               Terrain.GRASS)

    def assert_no_promotions(self):
        for promotion in self.combat_result.promotions:
            assert not promotion


class TestDamageCalculationSimple(CombatTest):
    def test_different_settings(self, before):
        self.assert_damage(10, 0, 0, 0, 10)
        # ali plus
        self.assert_damage(10, 0.25, 0, 0, 12)
        # ali minus
        self.assert_damage(10, -0.25, 0, 0, 7)
        # exp
        self.assert_damage(10, 0, 30, 0, 11)
        # exp just below
        self.assert_damage(10, 0, 29, 0, 10)
        # sixty exp
        self.assert_damage(10, 0, 60, 0, 12)
        # resistance half
        self.assert_damage(10, 0, 0, 50, 5)
        # resistance large
        self.assert_damage(10, 0, 0, 90, 1)

    def assert_damage(self, base, ali, exp, res, expected):
        damage = Attack(base, ali, exp, res, 0, 0, self.monster).damage
        assert damage == expected


class TestDamageCalculationCombined(CombatTest):
    def test_ali_and_exp(self, before):
        self.assert_damage(10, 0.25, 60, 0, 14)
        # ali and resistance
        self.assert_damage(10, 0.25, 0, 50, 6)
        # exp and resistance
        self.assert_damage(10, 0, 120, 50, 7)
        # all three
        self.assert_damage(10, 0.25, 120, 50, 8)

    def assert_damage(self, base, ali, exp, res, expected):
        damage = Attack(base, ali, exp, res, 0, 0, self.monster).damage
        assert damage == expected


class TestRomanCombat(CombatTest):
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board = self.model.board
        self.combat = Combat()
        self.roman_a = self.board.place_new_monster(
            Monster.Type.ROMAN, (4, 4), self.model.players[0])
        self.roman_b = self.board.place_new_monster(
            Monster.Type.ROMAN, (4, 5), self.model.players[1])
        Combat.perfect_accuracy = True
        self.more()

    def more(self):
        pass


class TestAttacksBetweenRomans(TestRomanCombat):
    def more(self):
        self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)
        self.attack0 = self.combat._attacks.get_attack(0, CLOSE_RANGE)
        self.attack1 = self.combat._attacks.get_attack(1, CLOSE_RANGE)

    def test_attacks(self, before):
        assert self.attack0.damage == 4
        assert self.attack1.damage == 4
        assert self.attack0.hits == 3
        assert self.attack1.hits == 3
        assert self.attack0.accuracy == 60
        assert self.attack1.accuracy == 60


class TestInvalidAttacksBetweenRomans(TestRomanCombat):
    def more(self):
        self.combat.monster_combat(
            (self.roman_a, self.roman_b), LONG_RANGE, SUNRISE)
        self.attack0 = self.combat._attacks.get_attack(0, LONG_RANGE)
        self.attack1 = self.combat._attacks.get_attack(1, LONG_RANGE)

    def test_attacks(self, before):
        assert self.attack0.damage == 0
        assert self.attack1.damage == 0
        assert self.attack0.hits == 0
        assert self.attack1.hits == 0


class TestAligmentMultiplier(TestRomanCombat):
    def test_multipliers(self, before):
        self.assert_damage(DAY, 4)
        self.assert_damage(SUNSET, 4)
        self.assert_damage(NIGHT, 3)
        self.assert_damage(SUNRISE, 4)

    def assert_damage(self, sun_stance, expect):
        self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, sun_stance)
        self.attack0 = self.combat._attacks.get_attack(0, CLOSE_RANGE)
        self.attack1 = self.combat._attacks.get_attack(1, CLOSE_RANGE)
        assert self.attack0.damage == expect
        assert self.attack1.damage == expect


class TestOneRoundOfCombat(TestRomanCombat):
    def more(self):
        self.combat_result = self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)
        self.model.process_combat_log(self.combat_result)

    def test_end_of_round_results(self, before):
        assert self.combat_result
        assert len(self.combat_result.rounds) == 6
        # base hp is 33, 33 - 3 * 3 = 24
        assert self.combat_result.hp_end[0] == 21
        self.assert_no_promotions()
        assert not self.combat_result.winner
        assert self.roman_a.exp == 1
        assert self.roman_a.hp == 21


class TestMultipleRoundsOfCombat(TestRomanCombat):
    def test_combat_result_exists(self, before):
        self.combat_rounds(2)
        assert self.combat_result

    def test_three_rounds(self, before):
        # attacker just barely survives this, since he attacks first
        self.combat_rounds(3)
        assert self.combat_result.hp_end[0] == 1
        self.assert_no_promotions()
        assert self.combat_result.hp_end[1] == 0
        assert self.combat_result.winner == self.roman_a
        assert self.combat_result.loser == self.roman_b
        assert self.combat_result.winner.exp == 18

    def combat_round(self):
        self.combat_result = self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)
        self.model.process_combat_log(self.combat_result)

    def combat_rounds(self, max_):
        for n in range(max_):
            self.combat_round()


class TestPromotionFromWinning(TestRomanCombat):
    def more(self):
        self.roman_a.award_exp(15)
        self.roman_b.hp = 3
        self.combat_result = self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)

    def test_promotion_in_result(self, before):
        assert MonsterType.CARTHAGO == self.combat_result.promotions[0]
        assert self.combat_result.hp_end[0] == 44

    def test_no_promotion_outside_result(self, before):
        assert self.roman_a.type == MonsterType.ROMAN
        assert self.roman_a.hp == 33


class TestPromotionFromSurviving(TestRomanCombat):
    def more(self):
        self.roman_a.award_exp(25)
        self.roman_b.award_exp(25)
        self.combat_result = self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)

    def test_combat_result(self, before):
        assert MonsterType.CARTHAGO == self.combat_result.promotions[0]
        assert MonsterType.CARTHAGO == self.combat_result.promotions[1]
        assert self.combat_result.hp_end[0] == 44
        assert self.combat_result.hp_end[1] == 44

    def test_outside_combat_result(self, before):
        assert MonsterType.ROMAN == self.roman_a.type
        assert MonsterType.ROMAN == self.roman_b.type
        assert self.roman_a.hp == 33
        assert self.roman_b.hp == 33


class TestPromotionFromMultipleRounds(TestRomanCombat):
    def more(self):
        self.roman_a.award_exp(20)

    def test_monster_promotion_after_three(self, before):
        self.combat_rounds(3)
        assert self.combat_result.promotions[0] == MonsterType.CARTHAGO
        assert self.roman_a.type == MonsterType.CARTHAGO

    def combat_round(self):
        self.combat_result = self.combat.monster_combat(
            (self.roman_a, self.roman_b), CLOSE_RANGE, SUNRISE)
        self.model.process_combat_log(self.combat_result)

    def combat_rounds(self, _max):
        for n in range(_max):
            self.combat_round()

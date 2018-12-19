import pytest

from src.components.board.monster import Monster
from src.helper.Misc.constants import MonsterType, Terrain, Range
from src.controller.board_controller import BoardModel


class TestCase:
    model = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()

    def test_on_end_turn(self, before):
        first_player = self.model.players.get_current_player()
        first_player_starting_mana = first_player.mana
        self.model.on_end_turn()
        assert self.model.turn == 1
        next_player = self.model.players.get_current_player()
        assert next_player is not first_player
        assert first_player.mana_gain != 0
        assert (first_player.mana ==
                first_player.mana_gain + first_player_starting_mana)

    def test_get_short_and_long_attacks(self, before):
        monsters = (Monster(MonsterType.SPHINX, (0,0), 0, Terrain.GRASS),
                    Monster(MonsterType.HYDRA, (0,0), 1, Terrain.DUNE))
        attacks = self.model.get_short_and_long_attacks(monsters)
        attacks_left = attacks.get_all_ranges(0)
        attacks_right = attacks.get_all_ranges(1)
        assert 10 == attacks_left[Range.CLOSE].damage
        assert 6 == attacks_left[Range.LONG].damage
        assert 6 == attacks_right[Range.CLOSE].damage
        assert 8 == attacks_right[Range.LONG].damage

    def test_lose_lord_self(self, before):
        blue_lord = self.model.get_lord_of_player(0)
        assert blue_lord.type == Monster.Type.DAIMYOU
        self.model.kill_monster(blue_lord)
        assert self.model.game_over is True


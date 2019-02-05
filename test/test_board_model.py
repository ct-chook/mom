import pytest

from src.components.board.monster import Monster
from src.helper.Misc.constants import MonsterType, Terrain, Range
from src.controller.board_controller import BoardModel


class TestCase:
    model = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.player_1 = self.model.players[0]
        self.player_2 = self.model.players[1]

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
        sphinx = Monster(MonsterType.SPHINX, (0, 0), self.player_1,
                         Terrain.GRASS)
        hydra = Monster(MonsterType.HYDRA, (0, 0), self.player_2, Terrain.DUNE)
        monsters = (sphinx, hydra)
        attacks = self.model.get_short_and_long_attacks(monsters)
        attacks_left = attacks.get_all_ranges(0)
        attacks_right = attacks.get_all_ranges(1)
        assert attacks_left[Range.CLOSE].damage == 10
        assert attacks_left[Range.LONG].damage == 6
        assert attacks_right[Range.CLOSE].damage == 6
        assert attacks_right[Range.LONG].damage == 8

    def test_lose_monster(self, before):
        pos = (0, 0)
        soldier = self.model.summon_monster_at(Monster.Type.SOLDIER, pos)
        assert self.player_1.monster_count == 2
        self.model.kill_monster(soldier)
        assert self.player_1.monster_count == 1
        assert self.model.board.monster_at(pos) is None

    def test_lose_lord_self(self, before):
        blue_lord = self.model.get_lord_of_player(self.player_1)
        assert blue_lord.type == Monster.Type.DAIMYOU
        self.model.kill_monster(blue_lord)
        assert self.model.game_over is True

    @pytest.mark.skip
    def test_one_out_of_three_players_loses(self, before):
        """todo Need to decide what to happens when someone loses"""
        green_lord = self.model.get_lord_of_player(2)
        blue_player = self.model.get_current_player()
        assert green_lord.type == Monster.Type.SORCERER
        self.model.on_end_turn()  # red
        self.model.on_end_turn()  # green
        self.model.kill_monster(green_lord)
        assert self.model.game_over is False
        assert self.model.get_current_player() == blue_player

    def test_capturing_tower_increases_counter(self, before):
        towers = self.model.get_current_player().tower_count
        pos = (4, 4)
        self.model.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        self.model.board.capture_terrain_at(pos, self.model.players[0])
        assert self.model.get_current_player().tower_count == towers + 1

    def test_monster_gets_healed_on_tower(self, before):
        pos = (0, 0)
        pos2 = (5, 5)
        board = self.model.board
        tower_monster = board.place_new_monster(Monster.Type.GOLEM, pos)
        grass_monster = board.place_new_monster(Monster.Type.MUSHA, pos2)
        assert grass_monster.terrain == Terrain.GRASS
        board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        assert board.get_current_player() == self.player_1
        board.capture_terrain_at(pos, self.player_1)
        tower_monster.hp = 1
        grass_monster.hp = 1
        self.model.on_end_turn()
        assert tower_monster.hp > 1
        assert grass_monster.hp == 1
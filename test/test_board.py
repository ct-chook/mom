import pytest

from components.board.monster import Monster
from helper.Misc.constants import Terrain
from src.components.board.board import Board, BoardFactory


class TestBoard:
    @pytest.fixture
    def before(self):
        factory = BoardFactory()
        self.board = factory.load_map()
        self.player_1 = self.board.players[0]

    def test_is_valid_board_pos(self, before):
        assert not self.board.is_valid_board_pos((-1, 0))
        assert not self.board.is_valid_board_pos((0, -1))
        assert self.board.is_valid_board_pos((0, 0))
        assert not self.board.is_valid_board_pos((255, 0))
        assert not self.board.is_valid_board_pos((0, 255))

    @pytest.mark.skip
    def test_tower_bookkeeping(self, before):
        assert self.board.towers
        player_0 = self.board.players[0]
        towers = self.board.get_capturable_towers_for_player(player_0)
        assert towers
        for pos in towers:
            self.board.capture_terrain_at(pos, player_0)
        towers = self.board.get_capturable_towers_for_player(player_0)
        assert not towers

    def test_monster_gets_healed_on_tower(self, before):
        pos = (0, 0)
        pos2 = (5, 5)
        tower_monster = self.board.place_new_monster(Monster.Type.GOLEM, pos)
        grass_monster = self.board.place_new_monster(Monster.Type.MUSHA, pos2)
        assert grass_monster.terrain == Terrain.GRASS
        self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
        assert self.board.get_current_player() == self.player_1
        self.board.capture_terrain_at(pos, self.player_1)
        tower_monster.hp = 1
        grass_monster.hp = 1
        self.board.on_end_of_turn()
        assert tower_monster.hp > 1
        assert grass_monster.hp == 1
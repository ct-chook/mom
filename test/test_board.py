import pytest

from helper.Misc.constants import Terrain
from src.components.board.board import Board, MapLoader


class TestBoard:
    @pytest.fixture
    def before(self):
        self.board = Board()
        loader = MapLoader(self.board)
        loader.load_map()

    def test_is_valid_board_pos(self, before):
        assert not self.board.is_valid_board_pos((-1, 0))
        assert not self.board.is_valid_board_pos((0, -1))
        assert self.board.is_valid_board_pos((0, 0))
        assert not self.board.is_valid_board_pos((255, 0))
        assert not self.board.is_valid_board_pos((0, 255))

    def test_tower_bookkeeping(self, before):
        assert self.board.towers
        towers = self.board.get_capturable_towers_for_player(0)
        assert towers
        for pos in towers:
            self.board.capture_terrain_at(pos, 0)
        towers = self.board.get_capturable_towers_for_player(0)
        assert not towers

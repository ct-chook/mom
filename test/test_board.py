import pytest

from src.components.board.board import Board, MapLoader


class TestBoard:
    @pytest.fixture
    def before(self):
        self.board = Board()
        loader = MapLoader(self.board)
        loader.load_map('test')

    def test_is_valid_board_pos(self, before):
        assert not self.board.is_valid_board_pos((-1, 0))
        assert not self.board.is_valid_board_pos((0, -1))
        assert self.board.is_valid_board_pos((0, 0))
        assert not self.board.is_valid_board_pos((255, 0))
        assert not self.board.is_valid_board_pos((0, 255))

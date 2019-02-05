import pytest

from src.components.board.board import BoardFactory


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
        """Method doesn't exist anymore"""
        assert self.board.towers
        player_0 = self.board.players[0]
        towers = self.board.get_capturable_towers_for_player(player_0)
        assert towers
        for pos in towers:
            self.board.capture_terrain_at(pos, player_0)
        towers = self.board.get_capturable_towers_for_player(player_0)
        assert not towers

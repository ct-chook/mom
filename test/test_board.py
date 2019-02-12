import pytest

from src.components.board.board import BoardBuilder


class TestBoard:
    @pytest.fixture
    def before(self):
        builder = BoardBuilder()
        self.board = builder.load_default_map()
        self.player_1 = self.board.players[0]

    def test_is_valid_board_pos(self, before):
        assert not self.board.is_valid_board_pos((-1, 0))
        assert not self.board.is_valid_board_pos((0, -1))
        assert self.board.is_valid_board_pos((0, 0))
        assert not self.board.is_valid_board_pos((255, 0))
        assert not self.board.is_valid_board_pos((0, 255))

    def test_no_mapoptions_gives_default_settings(self, before):
        assert len(self.board.players) == 4

    def test_towerlist(self, before):
        towerlist = self.board.towers
        assert towerlist
        player_0 = self.board.players[0]
        towers = towerlist.get_capturable_towers_for_player(player_0)
        assert towers
        for pos in towers:
            self.board.capture_terrain_at(pos, player_0)
        towers = towerlist.get_capturable_towers_for_player(player_0)
        assert not towers

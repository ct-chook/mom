import pytest

from src.components.board.players import PlayerList
from src.helper.Misc.constants import AiType


class TestPlayers:
    lord_types = (0, 1, 2)
    ai_types = (AiType.human, AiType.idle, AiType.default)
    mana_gains = (50, 60, 70)

    @pytest.fixture
    def before(self):
        self.playerlist = PlayerList()
        self.add_three_players()
        self.player_0 = self.playerlist[0]
        self.player_1 = self.playerlist[1]
        self.player_2 = self.playerlist[2]

    def add_three_players(self):
        for n in range(3):
            self.playerlist.add_player(
                self.lord_types[n], self.ai_types[n], self.mana_gains[n])

    def test_add_players(self, before):
        assert len(self.playerlist) == 3
        for n in range(3):
            self.check_player_at_id(n)

    def check_player_at_id(self, id_):
        first_player = self.playerlist.get_player_by_id(id_)
        assert first_player.ai_type == self.ai_types[id_]
        assert first_player.lord_type == self.lord_types[id_]
        assert first_player.mana_gain == self.mana_gains[id_]

    def test_remove_players(self, before):
        self.playerlist.remove_player(self.player_0)
        assert len(self.playerlist) == 2
        assert self.playerlist.get_player_by_id(0) is not None
        assert self.playerlist.get_player_by_id(1) is not None

    def test_next_players_after_removal(self, before):
        self.playerlist.remove_player(self.player_1)
        self.check_if_next_player_is(2)
        self.check_if_next_player_is(0)

    def test_next_players_after_removal_of_current(self, before):
        self.playerlist.remove_player(self.player_0)
        player = self.playerlist.get_current_player()
        assert player.mana_gain == self.mana_gains[1]
        self.check_if_next_player_is(2)

    def test_get_current_player(self, before):
        player = self.playerlist.get_current_player()
        assert player.mana_gain == self.mana_gains[0]

    def test_get_current_player_id(self, before):
        assert self.playerlist.get_current_player().id_ == 0
        self.playerlist.goto_next_player()
        assert self.playerlist.get_current_player().id_ == 1

    def test_goto_next_player(self, before):
        self.check_if_next_player_is(1)
        self.check_if_next_player_is(2)
        self.check_if_next_player_is(0)  # next round

    def check_if_next_player_is(self, player_id):
        self.playerlist.goto_next_player()
        player = self.playerlist.get_current_player()
        assert player.mana_gain == self.mana_gains[player_id]

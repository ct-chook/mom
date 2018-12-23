import src.components.board.brain as brain
from src.helper.Misc.constants import AiType


class Player:
    def __init__(self, id_, ai_type, lord_type, initial_mana, mana_gain):
        self.id_ = id_
        self.ai_type = ai_type
        self.lord_type = lord_type
        self.mana = initial_mana
        self.mana_gain = mana_gain
        self.tower_count = 0

    def regenerate_mana(self):
        self.mana += self.mana_gain

    def decrease_mana_by(self, amount):
        self.mana -= amount


class PlayerList:
    def __init__(self):
        self.players = []
        self.current_player = 0

    def add_player(self, lord_type, ai_type, mana_gain):
        player = Player(len(self.players), ai_type, lord_type, 100, mana_gain)
        self.players.append(player)
        return player

    def remove_player(self, player_id):
        self.players.pop(player_id)
        # if this was a current player, then index doesn't need to change
        # unless this was the last player, in that case the max index decreases
        # and the current index should be set to zero
        if player_id == len(self.players):
            self.current_player = 0

    def get_player_by_id(self, id_) -> Player:
        return self.players[id_]

    def goto_next_player(self) -> Player:
        self.current_player = (self.current_player + 1) % len(self.players)
        return self.get_current_player()

    def get_current_player(self) -> Player:
        return self.players[self.current_player]

    def get_current_player_id(self):
        return self.current_player

    def __len__(self):
        return len(self.players)

    def __iter__(self):
        return iter(self.players)


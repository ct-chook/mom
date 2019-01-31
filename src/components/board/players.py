from helper.Misc.constants import AiType


class Player:
    def __init__(self, id_):
        self.id_ = id_

        self.ai_type = AiType.human
        self.lord_type = None
        self.mana = 100
        self.mana_gain = 50
        self.team = 0
        self.tower_count = 0

    def regenerate_mana(self):
        self.mana += self.mana_gain

    def decrease_mana_by(self, amount):
        self.mana -= amount

    def is_friendly_with(self, player):
        if player is self:
            return True
        if self.team is 0 or player is 0:
            return False
        return self.team == player.team

    def is_enemy_of(self, player):
        if player is self:
            return False
        if self.team is 0 or player is 0:
            return True
        return self.team != player.team


class PlayerBuilder:
    def __init__(self):
        self.player = None

    def build_player(self, id_, lord_type, ai_type, mana_gain):
        self.player = Player(id_)
        self.player.lord_type = lord_type
        self.player.ai_type = ai_type
        self.player.mana_gain = mana_gain

    def set_team(self, team):
        self.player.team = team


class PlayerList:
    def __init__(self):
        self.players = []
        self.current_index = 0

    def add_player(self, lord_type, ai_type, mana_gain):
        builder = PlayerBuilder()
        builder.build_player(len(self.players), lord_type, ai_type, mana_gain)
        player = builder.player
        self.players.append(player)
        return player

    def remove_player(self, player):
        index = self.players.index(player)
        self.players.pop(index)
        # if this was a current player, then index doesn't need to change
        # unless this was the last player, in that case the max index decreases
        # and the current index should be set to zero
        if self.current_index == len(self.players):
            self.current_index = 0
        assert len(self.players) > self.current_index, (
                f'current player index {self.current_index} but only '
                f'{len(self.players)} players')

    def get_player_by_id(self, id_) -> Player:
        return self.players[id_]

    def goto_next_player(self) -> Player:
        self.current_index = (self.current_index + 1) % len(self.players)
        return self.get_current_player()

    def get_current_player(self) -> Player:
        return self.players[self.current_index]

    def __len__(self):
        return len(self.players)

    def __iter__(self):
        return iter(self.players)

    def __getitem__(self, item) -> Player:
        return self.players[item]
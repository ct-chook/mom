from src.helper.Misc.datatables import DataTables


class CombatLog:
    exp_table = ((16, 32, 64, 64),  # [winner level][loser level]
                 (8, 16, 32, 32),
                 (4, 8, 16, 16),
                 (4, 8, 16, 16))

    def __init__(self, monsters, attack_range, attacks, hp_start):
        self.rounds = []
        self.monsters = monsters
        self.attackType = attack_range
        self.attacks = attacks
        self.hp_start = hp_start

        self.promotions = None
        self.winner = None
        self.loser = None
        self.hp_end = None
        self.exp = None

    def add_round(self, side, damage):
        self.rounds.append(CombatRound(side, damage))

    def add_end_result(self, hp_end_1, hp_end_2, winner=None, loser=None):
        self.winner = winner
        self.loser = loser
        self.hp_end = [hp_end_1, hp_end_2]
        self._add_exp()
        self._add_promotions()

    def _add_exp(self):
        if self.winner:
            self._add_victory_exp()
        else:
            self.exp = [1, 1]

    def _add_victory_exp(self):
        self.exp = []
        for monster in self.monsters:
            if monster == self.winner:
                winner_level = self.winner.stats.level
                loser_level = self.loser.stats.level
                winner_exp = self.exp_table[winner_level][loser_level]
                self.exp.append(winner_exp)
            else:
                self.exp.append(0)

    def _add_promotions(self):
        self.promotions = []
        for n in range(2):
            self._add_promotion(n)

    def _add_promotion(self, n):
        monster = self.monsters[n]
        exp = self.exp[n]
        if monster.will_promote_with_exp(exp):
            self.promotions.append(monster.stats.promotion)
            data_promotion = DataTables.monster_stats[self.promotions[n]]
            self.hp_end[n] = data_promotion.max_hp
        else:
            self.promotions.append(None)


class CombatRound:
    def __init__(self, side, damage):
        self.side = side
        self.damage = damage

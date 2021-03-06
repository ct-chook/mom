import random
from src.components.combat.attack import AttackFactory, AttackCollection, Attack
from src.components.combat.combatlog import CombatLog


class CombatLogBuilder:
    perfect_accuracy = False  # testing purposes

    def __init__(self):
        self._attacks: AttackCollection = None
        self._attack_range = None
        self._monsters = None
        self._sun_stance = None
        self._combat_winner = None
        self._combat_loser = None
        self._hits = None
        self._result = None
        self._monster_a = None
        self._monster_b = None
        self._hp = None
        self._promotion = None
        self._attack_factory = AttackFactory()

    def build_from_monsters(self, monsters, attack_range, sun_stance) -> CombatLog:
        attacks = self._attack_factory.get_attacks_between_monsters(
            monsters, attack_range, sun_stance)
        return self.build_from_attacks(attacks, attack_range)

    def build_from_attacks(self, attacks, attack_range) -> CombatLog:
        self._attacks = attacks
        self._attack_range = attack_range
        self._monsters = (
            self.get_attack_for_side(0).monster,
            self.get_attack_for_side(1).monster)
        self._do_combat()
        return self._result

    def get_attack_for_side(self, side) -> Attack:
        return self._attacks.get_attack(side, self._attack_range)

    def _do_combat(self):
        self._setup_combat()
        while self._monsters_have_hits_left():
            self._do_attack()
        self._result.add_end_result(
            self._hp[0],
            self._hp[1],
            self._combat_winner,
            self._combat_loser)

    def _setup_combat(self):
        self._monster_a = 0
        self._monster_b = 1
        self._hits = [self.get_attack_for_side(0).hits,
                      self.get_attack_for_side(1).hits]
        monster_1, monster_2 = self._monsters
        self._hp = [monster_1.hp, monster_2.hp]
        self._result = CombatLog(
            self._monsters,
            self._attack_range,
            self._attacks,
            self._hp)

    def _monsters_have_hits_left(self):
        return self._hits[0] > 0 or self._hits[1] > 0

    def _do_attack(self):
        self._monster_a_attacks_b()
        self._switch_monster_a_and_b()

    def _monster_a_attacks_b(self):
        if self._monster_a_has_hits_left():
            if self._hit_is_successful():
                self._monster_a_hits_monster_b()
            else:
                self._monster_a_misses_monster_b()
            self._hits[self._monster_a] -= 1

    def _monster_a_has_hits_left(self):
        return self._hits[self._monster_a] > 0

    def _hit_is_successful(self):
        if self.perfect_accuracy:
            return True
        hit_roll = random.randint(0, 99)
        return hit_roll < self.get_attack_for_a().accuracy

    def get_attack_for_a(self) -> Attack:
        return self._attacks.get_attack(self._monster_a, self._attack_range)

    def _monster_a_hits_monster_b(self):
        if self._attack_is_fatal():
            self._monster_b_dies_to_attack()
        else:
            self._monster_b_survives_attack()
        self._result.add_round(
            self._monster_a, self.get_attack_for_a().damage)

    def _attack_is_fatal(self):
        return (self.get_attack_for_a().damage
                >= self._hp[self._monster_b])

    def _monster_b_dies_to_attack(self):
        self._hits = [0, 0]
        self._hp[self._monster_b] = 0
        self._combat_winner = self._monsters[self._monster_a]
        self._combat_loser = self._monsters[self._monster_b]

    def _monster_b_survives_attack(self):
        self._hp[self._monster_b] -= self.get_attack_for_a().damage

    def _monster_a_misses_monster_b(self):
        self._result.add_round(self._monster_a, -1)

    def _switch_monster_a_and_b(self):
        temp = self._monster_a
        self._monster_a = self._monster_b
        self._monster_b = temp

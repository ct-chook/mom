import random
from src.components.combat.attack import AttackFactory, AttackCollection, Attack
from src.components.combat.combatlog import CombatLog


class Combat:
    perfect_accuracy = False  # debug purposes

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

    def monster_combat(self, monsters, attack_range, sun_stance):
        self._monsters = monsters
        self._attack_range = attack_range
        self._sun_stance = sun_stance
        self._attacks = self._attack_factory.get_attacks_between_monsters(
            self._monsters, self._attack_range, self._sun_stance)
        return self._do_actual_combat(monsters)

    def monster_combat2(self, attacks, attack_range):
        # todo merge these methods
        self._attacks = attacks
        self._attack_range = attack_range
        self._monsters = (
            self.get_attack_for_side(0).monster,
            self.get_attack_for_side(1).monster)
        return self._do_actual_combat(self._monsters)

    def get_attack_for_side(self, side) -> Attack:
        return self._attacks.get_attack(side, self._attack_range)

    def get_attack_for_a(self) -> Attack:
        return self._attacks.get_attack(self._monster_a, self._attack_range)

    def _do_actual_combat(self, monsters):
        self._monster_a = 0
        self._monster_b = 1
        self._hits = [self.get_attack_for_side(0).hits,
                      self.get_attack_for_side(1).hits]
        self._hp = [monsters[0].hp, monsters[1].hp]
        self._result = CombatLog(
            self._monsters, self._attack_range, self._attacks, self._hp)
        while self._monsters_have_hits_left():
            self._monster_a_attacks_b()
            self._switch_monster_a_and_b()
        self._result.add_end_result(
            self._hp[0], self._hp[1], self._combat_winner, self._combat_loser)
        return self._result

    def _monsters_have_hits_left(self):
        return self._hits[0] > 0 or self._hits[1] > 0

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

    def _monster_a_hits_monster_b(self):
        if self._attack_is_fatal():
            self._monster_b_dies_to_attack()
        else:
            self._monster_b_survives_attack()
        self._result.add_round(
            self._monster_a, self.get_attack_for_a().damage)

    def _attack_is_fatal(self):
        return (self.get_attack_for_a().damage >=
                self._hp[self._monster_b])

    def _monster_b_dies_to_attack(self):
        self._hits = [0, 0]
        self._hp[self._monster_b] = 0
        self._combat_winner = self._monsters[self._monster_a]
        self._combat_loser = self._monsters[self._monster_b]

    def _monster_b_survives_attack(self):
        self._hp[self._monster_b] -= self.get_attack_for_a().damage

    def _monster_a_misses_monster_b(self):
        self._result.add_round(self._monster_a, -1)  # attack missed

    def _switch_monster_a_and_b(self):
        temp = self._monster_a
        self._monster_a = self._monster_b
        self._monster_b = temp

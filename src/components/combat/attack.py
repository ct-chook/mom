from math import floor

from src.helper.Misc.constants import AttackType, DayTime
from src.helper.Misc.datatables import DataTables


class Attack:
    def __init__(
            self, base_damage, ali_bonus, exp, resistance, hits, accuracy,
            monster):
        self.damage = self._get_final_damage(
            base_damage, ali_bonus, exp, resistance)
        self.hits = hits
        self.accuracy = accuracy
        self.monster = monster

    def _get_final_damage(self, base_damage, ali_bonus, exp, resistance):
        """Snippet from the FAQ:

        The fight conditions show the base damage. This is used to calculate the
        real damage per hit in a fight, this way:
        take the base damage and apply alignment bonus or penalty, if it’s the
        case, rounded down; add +1 for each 30 XP the monster has earned;
        subtract the % correspondent to the target resistance to that attack
        type, rounded down.
        Now you have the real damage per hit. When choosing a fight using the
        monster menu, this rule is automatically applied, and the real damage is
        displayed.
        """
        damage1 = base_damage + floor(base_damage * ali_bonus)
        damage2 = damage1 + floor(exp / 30)
        damage = damage2 - floor(damage2 * resistance / 100)
        return damage

    def get_expected_damage(self):
        return self.damage * self.accuracy * 0.01 * self.hits


class AttackCollection:
    def __init__(self):
        self.attacks_attacker = {}
        self.attacks_defender = {}

    def add_attack(self, attack, side, attack_range):
        container = self._get_container(side)
        container[attack_range] = attack

    def get_attack(self, side, attack_range) -> Attack:
        container = self._get_container(side)
        if attack_range in container:
            return container[attack_range]

    def get_all_ranges(self, side):
        return self._get_container(side)

    def _get_container(self, side):
        if side == 0:
            container = self.attacks_attacker
        else:
            container = self.attacks_defender
        return container


class AttackFactory:
    # ali multiplers are in the order of: [sunStance][alignment]
    _ali_multipliers = (
        (0.25, 0, -0.25), (0, 0, 0), (-0.25, 0, 0.25), (0, 0, 0))
    _ACCURACY_MAGIC = 65

    def __init__(self):
        self.attacks: AttackCollection = AttackCollection()

    def get_all_neutral_attacks_between_monsters(self, monsters):
        return self.get_all_attacks_between_monsters(monsters, DayTime.NOON)

    def get_all_attacks_between_monsters(self, monsters, sun_stance):
        for attack_range in range(2):
            self._add_attacks_for_sides(attack_range, monsters, sun_stance)
        return self.attacks

    def get_attacks_between_monsters(self, monsters, attack_range, sun_stance):
        self._add_attacks_for_sides(attack_range, monsters, sun_stance)
        return self.attacks

    def get_attacks_for_monster(self, monsters, side, sun_stance):
        for attack_range in range(2):
            self._add_attack_for_side(side, attack_range, monsters, sun_stance)
        return self.attacks

    def get_neutral_expected_damage_between(self, attacker, defender, range_):
        """This uses neutral sun stance"""
        return self.get_attack_between_monsters(
            (attacker, defender), 0, range_, DayTime.NOON).get_expected_damage()

    def get_attack_between_monsters(self, monsters, side, range_, sun_stance):
        return self._get_attack_against_monster(
            monsters, side, range_, sun_stance)

    def _add_attacks_for_sides(self, attack_range, monsters, sun_stance):
        for side in range(2):
            self._add_attack_for_side(side, attack_range, monsters, sun_stance)

    def _add_attack_for_side(self, side, attack_range, monsters, sun_stance):
        attack = self._get_attack_against_monster(
            monsters, side, attack_range, sun_stance)
        self.attacks.add_attack(attack, side, attack_range)

    def _get_attack_against_monster(
            self, monsters, a, attack_range, sun_stance):
        b = (a + 1) % 2
        base_damage = monsters[a].stats.damage[attack_range]
        ali_bonus = self._get_ali_bonus(monsters[a], sun_stance)
        exp = monsters[a].exp
        attack_element = monsters[a].stats.element[attack_range]
        resistance = monsters[b].stats.resistance[attack_element]
        hits = monsters[a].stats.hits[attack_range]
        accuracy = self._get_accuracy(monsters[b], attack_element)
        return Attack(base_damage, ali_bonus, exp, resistance, hits, accuracy,
                      monsters[a])

    def _get_ali_bonus(self, monster, sun_stance):
        alignment = monster.stats.alignment
        return self._ali_multipliers[sun_stance][alignment]

    def _get_accuracy(self, defending_monster, attack_element):
        # Magical attacks always have fixed accuracy
        if attack_element == AttackType.MAGICAL:
            accuracy = self._ACCURACY_MAGIC
        else:
            terrain = defending_monster.terrain
            terrain_defense = DataTables.terrain_defense[terrain]
            miss_chance = terrain_defense[defending_monster.stats.terrain_type]
            accuracy = 100 - miss_chance
        return accuracy

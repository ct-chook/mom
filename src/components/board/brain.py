import random
from math import ceil

from src.components.board.pathing import MovementFinder
from src.helper.Misc.constants import MonsterBehavior, Terrain
from src.helper.Misc.datatables import DataTables


class PlayerBrain:
    """Reads the board model and decides next action"""

    def __init__(self, controller, player):
        self.controller = controller
        self.model = controller.model
        self.player = player
        self.did_action = False

    def do_action(self):
        pass

    def _do_end_of_turn(self):
        self.controller.handle_end_of_turn()


class PlayerIdleBrain(PlayerBrain):
    def do_action(self):
        """Will always skip to the next turn"""
        self._do_end_of_turn()


class PlayerDefaultBrain(PlayerBrain):
    def __init__(self, controller, player):
        super().__init__(controller, player)
        self.monster_index = 0
        self.monsters = None
        self.monster_to_summon = None

    def do_action(self):
        """Checks the state of the game and then does a single action

        Moving and attacking should both be single actions.

        Generally, moves monsters, then summons if all monsters have moved.
        Then it ends turn.
        """
        self._handle_monsters()
        if self.did_action:
            return
        self._handle_summon()
        if self.did_action:
            return
        self._do_end_of_turn()

    def _handle_monsters(self):
        if not self.monsters:
            self._create_list_of_monsters()
            self._create_monster_brains()
        if self.monster_index < len(self.monsters):
            self._do_monster_action()

    def _create_list_of_monsters(self):
        self.monsters = self.model.get_current_player_monsters()
        self.monster_index = 0

    def _create_monster_brains(self):
        assert self.monsters
        for monster in self.monsters:
            self._create_brain_for_monster(monster)

    def _create_brain_for_monster(self, monster):
        monster.brain = MonsterBrain(
            self.controller, monster, MonsterBehavior.SCOUT)

    def _do_monster_action(self):
        monster_brain = self._get_next_monster().brain
        monster_brain.do_action()

    def _get_next_monster(self):
        return self.monsters[self.monster_index]

    def _handle_summon(self):
        if self.monster_to_summon is None:
            summon_options = DataTables.get_summon_options(
                self.player.lord_type)
            self.monster_to_summon = random.choice(summon_options)
        if self._have_enough_mana_to_summon():
            self.monster_to_summon = None

    def _have_enough_mana_to_summon(self):
        return self.player.mana >= \
               DataTables.get_monster_stats(self.monster_to_summon).summon_cost


class MonsterBrain:
    def __init__(self, controller, brain_owner, type):
        self.monster = brain_owner
        self.controller = controller
        self.model = controller.model
        self.movement_finder = MovementFinder(self.model.board)
        self.type = type

    def do_action(self):
        assert self.type is not None
        if self.type == MonsterBehavior.SCOUT:
            self._do_scout_action()
        if self.type == MonsterBehavior.ATTACKER:
            self._do_attacker_action()
        if self.type == MonsterBehavior.DEFENDER:
            self._do_defender_action()

    def _do_scout_action(self):
        pos_to_move = self.movement_finder.get_pos_to_terraintype(
            self.monster, Terrain.TOWER)
        self.controller.handle_move_monster(self.monster, pos_to_move)

    def _do_attacker_action(self):
        pos_to_move = self.movement_finder.get_pos_to_enemy_monster_or_tile(
            self.monster)
        if not pos_to_move:
            # could not find enemy, so do nothing?
            return
        self.controller.handle_move_monster(self.monster, pos_to_move)

        # now check if there is a monster to attack
        # somewhat duplicate since it checks this in matrix
        # enemies = self.model.get_enemies_adjacent_to(pos_to_move)
        # if not enemies:
        #     return
        # attack enemy that takes least number to turns to defeat
        # monster, range_ = self._get_optimal_attack(enemies)

    def _get_optimal_attack(self, enemies):
        min_turns_to_defeat = 1000
        monster_to_attack = None
        range_to_use = None
        for enemy in enemies:
            for attack_range in range(2):
                damage = self.model.get_expected_damage_between(
                    self.monster, enemy, attack_range)
                if damage <= 0:
                    continue
                turns_to_defeat = ceil(self.monster.hp / damage)
                if turns_to_defeat < min_turns_to_defeat:
                    min_turns_to_defeat = turns_to_defeat
                    monster_to_attack = enemy
                    range_to_use = attack_range
        return monster_to_attack, range_to_use

    def _do_defender_action(self):
        pos_to_move = self.movement_finder.get_pos_to_own_tile(self.monster)
        self.controller.handle_move_monster(self.monster, pos_to_move)

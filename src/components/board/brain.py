import random
from math import ceil

from src.components.board.monster import Monster
from src.components.board.pathing import MovementFinder
from src.helper.Misc.constants import Terrain, MonsterBehavior
from src.helper.Misc.datatables import DataTables


class PlayerBrain:
    """Reads the board model and decides next action"""

    def __init__(self, board_model_, player):
        self.model = board_model_
        self.action: BrainAction = None
        self.player = player

    def get_next_action(self):
        pass

    def get_end_of_turn_action(self):
        self.action = BrainAction()
        self.action.set_end_turn()
        return self.action


class PlayerIdleBrain(PlayerBrain):
    def get_next_action(self):
        """Will always skip to the next turn"""
        return self.get_end_of_turn_action()


class PlayerDefaultBrain(PlayerBrain):
    def __init__(self, board_model_, player):
        super().__init__(board_model_, player)
        self.index = 0
        self.monsters = None
        self.monster_to_summon = None

    def get_next_action(self):
        """Moves monsters, then summons one if all monsters have moved"""
        self.action = None
        self._handle_monsters()
        # moved all monsters
        if self.action:
            return self.action
        self._handle_summon()
        if self.action:
            return self.action
        # no monsters to move or summon
        return self.get_end_of_turn_action()

    def _handle_monsters(self):
        if not self.monsters:
            self._create_list_of_monsters()
            self._create_monster_brains()
        if self.index < len(self.monsters):
            self._set_action_for_monster()

    def _create_list_of_monsters(self):
        self.monsters = self.model.get_current_player_monsters()
        self.index = 0

    def _create_monster_brains(self):
        assert self.monsters
        for monster in self.monsters:
            self._create_brain_for_monster(monster)

    def _create_brain_for_monster(self, monster):
        monster.brain = MonsterBrain(monster, self.model.board, self.model)

    def _set_action_for_monster(self):
        monster_brain = self._get_next_monster().brain
        self.action = monster_brain.get_action()

    def _get_next_monster(self):
        return self.monsters[self.index]

    def _handle_summon(self):
        if self.monster_to_summon is None:
            summon_options = DataTables.get_summon_options(
                self.player.lord_type)
            self.monster_to_summon = random.choice(summon_options)
        if self._have_enough_mana_to_summon():
            self.action = BrainAction()
            self.action.monster_to_summon = self.monster_to_summon
            self.monster_to_summon = None

    def _have_enough_mana_to_summon(self):
        return self.player.mana >= \
               DataTables.get_monster_stats(self.monster_to_summon).summon_cost


class MonsterBrain:
    def __init__(self, owner, board, model):
        self.monster = owner
        self.action: BrainAction = None
        self.movement_finder = MovementFinder(board)
        self.type = None
        self.board = board
        self.model = model

    def get_action(self):
        self.action = BrainAction()
        self.action.monster_to_move = self.monster
        if self.type == MonsterBehavior.SCOUT:
            self._set_scout_action()
        if self.type == MonsterBehavior.ATTACKER:
            self._set_attacker_action()
        if self.type == MonsterBehavior.DEFENDER:
            self._set_defender_action()
        return self.action

    def _set_scout_action(self):
        self.action.pos_to_move = self.movement_finder. \
            get_pos_to_terraintype(self.monster, Terrain.TOWER)

    def _set_attacker_action(self):
        self.action.pos_to_move = self.movement_finder. \
            get_pos_to_enemy_monster_or_tile(self.monster)
        # now check if there is a monster to attack
        # somewhat duplicate since it checks this in matrix
        enemies = self.board.get_enemies_adjacent_to(self.action.pos_to_move)
        if not enemies:
            self.action.monster_to_attack = None
            return
        # attack enemy that takes least number to turns to defeat
        optimal_attack = self._get_optimal_attack(enemies)
        self.action.monster_to_attack = optimal_attack[0]
        self.action.range_to_use = optimal_attack[1]

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

    def _set_defender_action(self):
        self.action.pos_to_move = self.movement_finder. \
            get_pos_to_own_tile(self.monster)


class BrainAction:
    """Action log for decisions made by a brain

    Is passed to both the controller and the model. Used so the game can decide
    the order of the actions to display and process.

    Possible actions:
    * Move
    * Attack
    * Move and attack (can be provided in a single BrainAction)
    * Summon
    * Use spell (not implemented at the moment)
    * End turn
    """

    def __init__(self):
        self.end_turn = False
        self.monster_to_move = None
        self.pos_to_move = None
        self.monster_to_attack = None
        self.monster_to_summon = None
        self.range_to_use = None

    def set_end_turn(self, is_end=True):
        self.end_turn = is_end

    def print(self):
        monster_to_summon = DataTables.\
            get_monster_stats(self.monster_to_summon).name
        print('\n'
              'BrainAction:'
              f'end_turn: {self.end_turn}\n'
              f'monster_to_move: {self.monster_to_move}\n'
              f'pos_to_move: {self.pos_to_move}\n'
              f'monster_to_attack: {self.monster_to_attack}\n'
              f'monster_to_summon: {monster_to_summon}\n'
              f'range_to_use: {self.range_to_use}')

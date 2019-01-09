import logging
import random
from math import ceil

from src.components.board.pathing import MovementFinder, PathFinder, \
    PathMatrixFactory
from src.components.board.pathing_components import PathMatrix, \
    TowerSearchMatrixFactory
from src.helper.Misc.datatables import DataTables
from src.helper.events.events import EventList
from src.model import board_model


class PlayerBrain:
    """Reads the board model and decides next action"""

    def __init__(self, controller, player):
        self.controller = controller
        self.model: board_model.BoardModel = controller.model
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
        self.did_action = False
        self._handle_monsters()
        if self.did_action:
            return
        self._handle_summon()
        if self.did_action:
            return
        self._finish_turn()

    def _handle_monsters(self):
        if not self.monsters:
            self._create_list_of_monsters()
            self._create_monster_brains()
        # skip lord action for now
        if self.monster_index < len(self.monsters) and \
                self._get_current_monster().is_lord():
                self.monster_index += 1
        if self.monster_index < len(self.monsters):
            self._do_monster_action()

    def _create_list_of_monsters(self):
        self.monsters = tuple(self.model.get_current_player_monsters())
        assert self.monsters, \
            f'Player {self.model.get_current_player().id_} has no monsters'
        self.monster_index = 0

    def _create_monster_brains(self):
        for monster in self.monsters:
            self._create_brain_for_monster(monster)

    def _create_brain_for_monster(self, monster):
        monster.brain = MonsterBrain(
            self.controller, monster)

    def _do_monster_action(self):
        monster = self._get_current_monster()
        if not monster.moved:
            monster_brain = monster.brain
            assert monster_brain, f'{self._get_current_monster()} has no brain'
            do_another_monster_action = monster_brain.do_action()
            if do_another_monster_action:
                # ugly hack to make monster act again
                self.monster_index -= 1
        else:
            # make it queue up another AI action
            make_player_brain_act_again(self.controller)
        self.did_action = True
        self.monster_index += 1

    def _get_current_monster(self):
        return self.monsters[self.monster_index]

    def _handle_summon(self):
        if self.monster_to_summon is None:
            summon_options = DataTables.get_summon_options(
                self.player.lord_type)
            self.monster_to_summon = random.choice(summon_options)
        if self._possible_to_summon():
            pos = self._get_pos_to_summon()
            if pos:
                monster = self.controller.handle_summon_monster(
                    self.monster_to_summon, pos)
                self._create_brain_for_monster(monster)
                self.did_action = True
                self.monster_to_summon = None

    def _possible_to_summon(self):
        return self._have_enough_mana_to_summon_() \
               and self._have_enough_towers_to_summon()

    def _have_enough_mana_to_summon_(self):
        return self.player.mana >= \
               DataTables.get_monster_stats(self.monster_to_summon).summon_cost

    def _have_enough_towers_to_summon(self):
        return len(self.monsters) <= self.player.tower_count

    def _get_pos_to_summon(self):
        lord = self.model.get_lord_of_player()
        posses = self.model.board.get_posses_adjacent_to(lord.pos)
        for pos in posses:
            if self.model.is_valid_pos_for_summon(pos):
                return pos

    def _finish_turn(self):
        self.monster_index = 0
        self.monsters = None
        self._do_end_of_turn()


class MonsterBrain:
    def __init__(self, controller, brain_owner):
        self.monster = brain_owner
        self.controller = controller
        self.model = controller.model
        self.board = self.model.board
        self.path_finder = PathFinder(self.board)
        self.movement_finder = MovementFinder(self.board)
        self.matrix_generator = PathMatrixFactory(self.board)
        self.towersearch_matrix_factory = TowerSearchMatrixFactory(
            self.board)
        self.matrix: PathMatrix = None
        self.target_pos = None
        self.monster_to_attack = None
        self.range_to_attack_with = None

    def do_action(self):
        """Uses the board controller to execute a monster-related action

        How it works: it follows the following steps:
        1. If it has an adjacent monster to attack, attack it and stop
        2. Find target (tower or enemy lord). Save this target.
        3. Get an 1-turn matrix to see what's nearby.
        4. Check if destination is on it. If so, move to it and stop
        5. Get all possible monsters on matrix to attack. Check if attacking any
           of them has a high score. If so, move to them, store monster as
           target to attack and stop
        6. Otherwise, generate a-star matrix to destination, move toward it and
           stop.
        7. If the tile leading to destination is blocked, move to tile adjacent
           of it. If all those are blocked too, move to a tile adjacent to them.
           If those are also blocked, move to a random tile.
        """

        if self.monster_to_attack:
            self._attack_monster()
            self.monster_to_attack = None
            self.range_to_attack_with = None
            self.monster.moved = True
            return

        assert self.monster is not None
        self._find_target()
        if not self.target_pos:
            pass
            # this is possible, target is too far away
        self.matrix = self.matrix_generator.generate_path_matrix(
            self.monster.pos)
        if self.target_pos and self.target_pos in self.matrix:
            self._move_to_tile_inside_matrix(self.target_pos)
            return

        enemy, attack_range = self._get_best_enemy_to_attack()
        if enemy:
            tile_to_attack_from = self._get_tile_to_attack_from(enemy)
            if tile_to_attack_from:
                self._move_to_tile_inside_matrix(tile_to_attack_from)
                self.monster_to_attack = enemy
                self.range_to_attack_with = attack_range
                self.monster.moved = False  # so it can move again next time
                return True

        destination = self._get_tile_leading_to_destination()
        new_destination = None
        if self.board.monster_at(destination):
            new_destination = self._get_new_destination(destination)
            if not new_destination:
                return

        if new_destination:
            destination = new_destination
        self._move_to_tile_inside_matrix(destination)

    def _get_new_destination(self, destination):
        new_destination = None
        adjacents = self.board.get_posses_adjacent_to(destination)
        for pos in adjacents:
            monster = self.board.monster_at(pos)
            if not monster:
                new_destination = pos
                break
        return new_destination

    def _get_tile_leading_to_destination(self):
        assert len(self.target_pos) == 2
        path = self.movement_finder.get_simple_movement_to_tile(
            self.monster, self.target_pos)
        destination = path.get_destination()
        return destination

    def _move_to_tile_inside_matrix(self, tile):
        assert tile in self.matrix
        self.matrix.end = tile
        path = self.path_finder.get_path_on_matrix(self.matrix)
        self.controller.handle_move_monster(self.monster, path)

    def _get_tile_to_attack_from(self, enemy):
        adjacent_tiles = self.board.get_posses_adjacent_to(enemy.pos)
        for tile in adjacent_tiles:
            if self._is_valid_destination(tile):
                return tile

    def _is_valid_destination(self, tile):
        return (tile in self.matrix
                and self.matrix.get_distance_value_at(tile) < 99
                and self.board.monster_at(tile) is None)

    def _find_target(self):
        player_id = self.monster.owner
        towers = self.board.get_capturable_towers_for_player(player_id)
        self.target_pos = None  # make it recalculate every turn for now
        if not self.target_pos:
            if towers:
                self._set_destination_to_closest_tower()
            else:
                self._set_destination_to_enemy_lord(player_id)

    def _set_destination_to_closest_tower(self):
        tower_matrix = self.towersearch_matrix_factory \
            .generate_path_matrix(self.monster.pos)
        if tower_matrix.end:
            self.target_pos = tower_matrix.end

    def _set_destination_to_enemy_lord(self, player_id):
        # go to enemy lord
        enemy_lord = self.board.get_enemy_lord_for_player(player_id)
        self.target_pos = enemy_lord.pos

    def _get_best_enemy_to_attack(self):
        attack_finder = OptimalAttackFinder(self.model)
        return attack_finder.get_optimal_attack(
            self.monster, self.matrix.enemies)

    def _attack_monster(self):
        logging.info(f'{self.monster} is attacking {self.monster_to_attack}')
        monsters = (self.monster, self.monster_to_attack)
        range_ = self.range_to_attack_with
        self.controller.handle_attack_order(monsters, range_)

    def _move_monster(self, movement):
        """UNUSED"""
        destination = movement.get_destination()
        if destination:
            self.controller.handle_move_monster(self.monster, movement.path)
        else:
            make_player_brain_act_again(self.controller)


class OptimalAttackFinder:
    def __init__(self, model):
        self.monster = None
        self.model = model
        self.monster_to_attack = None
        self.range_to_use = None
        self.best_score = -1

    def get_optimal_attack(self, monster, enemies):
        self.monster = monster
        # the best_score we start with influences how agressive the monster is
        # if it's low, the monster will attack just anything
        # if it's high, the monster will only attack when it has a massive
        # advantage
        # if it's 0, the monster will be picky. keep it slightly below 0
        for enemy in enemies:
            for attack_range in range(2):
                self._update_best_score(attack_range, enemy)
        return self.monster_to_attack, self.range_to_use

    def _update_best_score(self, attack_range, enemy):
        damage1, damage2 = self.model.get_expected_damage_between(
            self.monster, enemy, attack_range)
        if damage1 <= 0:
            return
        # 1 turn defeats should always be attacked
        turns_to_defeat = ceil(enemy.hp / damage1)
        if turns_to_defeat == 1:
            score = 1
        # prioritize highest % of hp caused in damage
        else:
            damage_percent1 = damage1 / enemy.stats.max_hp
            damage_percent2 = damage2 / self.monster.stats.max_hp
            score = damage_percent1 - damage_percent2
        if score > self.best_score:
            self.best_score = score
            self.monster_to_attack = enemy
            self.range_to_use = attack_range


def make_player_brain_act_again(controller):
    EventList(controller.get_ai_action_event())
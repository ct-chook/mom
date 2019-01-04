import random
from math import ceil

from src.components.board.pathing import MovementFinder, PathFinder, \
    PathMatrixFactory
from src.components.board.pathing_components import PathMatrix, \
    TowerSearchMatrixFactory
from src.helper.Misc.datatables import DataTables
from src.helper.events.events import EventList
from src.helper.functions import get_hexagonal_manhattan_distance
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
            monster_brain.do_action()
        else:
            # make it queue up another AI action
            EventList(self.controller.get_ai_action_event())
        self.did_action = True
        self.monster_index += 1

    def _get_current_monster(self):
        return self.monsters[self.monster_index]

    def _handle_summon(self):
        if self.monster_to_summon is None:
            summon_options = DataTables.get_summon_options(
                self.player.lord_type)
            self.monster_to_summon = random.choice(summon_options)
        if self._have_enough_mana_to_summon():
            pos = self._get_pos_to_summon()
            if pos:
                monster = self.controller.handle_summon_monster(
                    self.monster_to_summon, pos)
                self._create_brain_for_monster(monster)
                self.did_action = True
                self.monster_to_summon = None

    def _have_enough_mana_to_summon(self):
        return self.player.mana >= \
               DataTables.get_monster_stats(self.monster_to_summon).summon_cost

    def _get_pos_to_summon(self):
        lord = self.model.get_lord_of_player()
        posses = self.model.board.get_posses_adjacent_to(lord.pos)
        for pos in posses:
            tile = self.model.board.tile_at(pos)
            if not tile.monster:
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

    def do_action(self):
        """Uses the board controller to execute a monster-related action

        How it works: it follows the following steps:
        0. Find target (tower or enemy lord). Save this target.
        1. Get an 1-turn matrix to see what's nearby.
        2. Check if destination is on it. If so, move to it.
        3. Get all possible monsters on matrix to attack. Check if attacking any
           of them has a high score. If so, move to them and attack.
        4. Otherwise, generate a-star matrix to destination and move toward it.
        5. If the tile leading to destination is blocked, move to tile adjacent
           of it. If all those are blocked too, move to a tile adjacent to them.
           If those are also blocked, move to a random tile.
        """

        assert self.monster is not None
        self._find_target()
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
                # todo: issue attack, chain these commands?
                self._attack_monster()
                return

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
        self.matrix.end = tile
        path = self.path_finder.get_path_on_matrix(self.matrix)
        self.controller.handle_move_monster(self.monster, path)

    def _get_tile_to_attack_from(self, enemy):
        adjacent_tiles = self.board.get_posses_adjacent_to(enemy.pos)
        tile_to_use = None
        for tile in adjacent_tiles:
            if tile in self.matrix.dist_values:
                tile_to_use = tile
        return tile_to_use

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
        assert self.target_pos, \
            f'{tower_matrix.get_printable_dist_values()}'

    def _set_destination_to_enemy_lord(self, player_id):
        # go to enemy lord
        enemy_lord = self.board.get_enemy_lord_for_player(player_id)
        self.target_pos = enemy_lord.pos

    def _move_monster(self, movement):
        destination = movement.get_destination()
        if destination:
            self.controller.handle_move_monster(self.monster, movement.path)
        else:
            # add callback for next turn, which normally comes with move monster
            EventList(self.controller.get_ai_action_event())

    def _get_best_enemy_to_attack(self):
        enemies = self._get_enemies_in_matrix()
        best_target, attack_range = self._get_optimal_attack(enemies)
        return best_target, attack_range

    def _get_enemies_in_matrix(self):
        enemies = []
        for pos in self.matrix:
            monster = self.model.board.monster_at(pos)
            if monster and self.model.is_enemy(monster):
                enemies.append(monster)
        return enemies

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

    def _get_pos_closest_to_target(self):
        # unused right now
        start = self.monster.pos
        closest_pos = None
        lowest_delta = 99999
        for pos in self.matrix:
            delta = get_hexagonal_manhattan_distance(start, pos)
            if delta < lowest_delta:
                lowest_delta = delta
                closest_pos = pos
        return closest_pos

    def _attack_monster(self):
        pass

import logging
import random
from math import ceil

from src.components.board.pathing import PathFactory, PathMatrixFactory
from src.components.board.pathing_components import PathMatrix, \
    TowerSearchMatrixFactory
from src.helper.Misc.datatables import DataTables
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
        logging.info('AI Handling monsters')
        self._handle_monsters()
        if self.did_action:
            return
        logging.info('AI Handling summon')
        self._handle_summon()
        if self.did_action:
            return
        logging.info('AI Ending turn')
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
            monster_brain: MonsterBrain = monster.brain
            assert monster_brain, f'{self._get_current_monster()} has no brain'
            monster_brain.do_action()
            if not monster.moved and monster_brain.monster_to_attack:
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
            logging.info(f'AI Setting monster to summon to '
                         f'{self.monster_to_summon}')
        if self._possible_to_summon():
            pos = self._get_pos_to_summon()
            logging.info(f'AI Pos to summon: {pos}')
            if pos:
                monster = self.controller.handle_summon_monster(
                    self.monster_to_summon, pos)
                if monster:
                    logging.info(f'AI Summoned monster')
                    self._create_brain_for_monster(monster)
                    self.monster_to_summon = None
                    self.did_action = True

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


class OptimalAttack:
    def __init__(self):
        self.monster_to_attack = None
        self.range_to_use = None


class OptimalAttackFinder:
    def __init__(self, model):
        self.monster = None
        self.model = model
        self.optimal_attack: OptimalAttack = None
        self.best_score = -1

    def get_optimal_attack(self, monster, enemies) -> OptimalAttack:
        self.monster = monster
        # the best_score we start with influences how agressive the monster is
        # if it's low, the monster will attack just anything
        # if it's high, the monster will only attack when it has a massive
        # advantage
        self.optimal_attack = OptimalAttack()
        for enemy in enemies:
            for attack_range in range(2):
                self._update_best_score(attack_range, enemy)
        return self.optimal_attack

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
            self.optimal_attack.monster_to_attack = enemy
            self.optimal_attack.range_to_use = attack_range


class MonsterBrain:
    def __init__(self, controller, brain_owner):
        self.monster = brain_owner
        self.controller = controller
        self.model = controller.model
        self.board = self.model.board
        self.path_finder = PathFactory(self.board)
        self.matrix_factory = PathMatrixFactory(self.board)
        self.towersearch_matrix_factory = TowerSearchMatrixFactory(self.board)
        self.matrix: PathMatrix = None
        self.destination_pos = None
        self.monster_to_attack = None
        self.range_to_attack_with = None
        self.optimal_attack: OptimalAttack = None

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
           of it. If those are also blocked, don't move.
        """
        assert self.monster is not None
        if self.monster_to_attack:
            self._handle_attack()
        else:
            self._handle_move()

    def _handle_attack(self):
        logging.info(f'{self.monster} is attacking {self.monster_to_attack}')
        monsters = (self.monster, self.monster_to_attack)
        range_ = self.range_to_attack_with
        self.controller.handle_attack_order(monsters, range_)
        self.monster_to_attack = None
        self.range_to_attack_with = None
        self.monster.moved = True

    def _handle_move(self):
        self._set_destination()
        self._make_path_matrix()
        self._set_pos_to_move_to()
        self._move_to_destination()

    def _set_destination(self):
        id_ = self.monster.owner
        # capturable_towers = self.board.get_capturable_towers_for_player(id_)
        # if capturable_towers:
        self._set_destination_to_closest_tower()
        if not self.destination_pos:
            self._set_destination_to_enemy_lord(id_)
        assert self.destination_pos

    def _set_destination_to_closest_tower(self):
        tower_matrix = self.towersearch_matrix_factory \
            .generate_path_matrix(self.monster.pos)
        if tower_matrix.end:
            self.destination_pos = tower_matrix.end

    def _set_destination_to_enemy_lord(self, player_id):
        # go to enemy lord
        enemy_lord = self.board.get_enemy_lord_for_player(player_id)
        assert enemy_lord
        self.destination_pos = enemy_lord.pos

    def _make_path_matrix(self):
        self.matrix = self.matrix_factory.generate_path_matrix(self.monster.pos)

    def _set_pos_to_move_to(self):
        self._find_best_enemy_to_attack()
        if self._enemy_is_nearby():
            self._set_pos_to_nearby_enemy()
        else:
            self._set_pos_towards_destination()

    def _find_best_enemy_to_attack(self):
        attack_finder = OptimalAttackFinder(self.model)
        self.optimal_attack = attack_finder.get_optimal_attack(
            self.monster, self.matrix.enemies)

    def _enemy_is_nearby(self):
        return self.optimal_attack.monster_to_attack

    def _set_pos_to_nearby_enemy(self):
        enemy = self.optimal_attack.monster_to_attack
        attack_range = self.optimal_attack.range_to_use
        tile_to_attack_from = self._get_tile_to_attack_from(enemy)
        if tile_to_attack_from:
            self._move_to_pos_inside_matrix(tile_to_attack_from)
            self.monster_to_attack = enemy
            self.range_to_attack_with = attack_range
            self.monster.moved = False  # so it can move again next time

    def _get_tile_to_attack_from(self, enemy):
        adjacent_tiles = self.board.get_posses_adjacent_to(enemy.pos)
        for tile in adjacent_tiles:
            if self._is_valid_destination(tile):
                return tile

    def _is_valid_destination(self, tile):
        return (tile in self.matrix
                and self.matrix.get_distance_value_at(tile) < 99
                and self.board.monster_at(tile) is None)

    def _set_pos_towards_destination(self):
        destination = self._get_tile_leading_to_destination()
        if not destination:
            self.destination_pos = self.monster.pos
            return
        new_destination = None
        if self._is_occupied(destination):
            new_destination = self._get_new_destination(destination)
            if new_destination is None:
                new_destination = self.monster.pos
            assert new_destination in self.matrix
        if new_destination:
            destination = new_destination
            assert destination in self.matrix
        assert destination is not None
        if destination not in self.matrix:
            self._skip_turn()
        self.destination_pos = destination

    def _is_occupied(self, pos):
        monster = self.board.monster_at(pos)
        return monster and monster is not self.monster

    def _get_tile_leading_to_destination(self):
        assert len(self.destination_pos) == 2
        path = self.path_finder.get_simple_path_between(self.monster.pos,
                                                        self.destination_pos)
        if not path:
            return None
        assert path.furthest_reachable
        return path.furthest_reachable

    def _get_new_destination(self, destination):
        new_destination = None
        adjacents = self.board.get_posses_adjacent_to(destination)
        for pos in adjacents:
            if pos in self.matrix:
                monster = self.board.monster_at(pos)
                if not monster:
                    new_destination = pos
                    break
        return new_destination

    def _skip_turn(self):
        make_player_brain_act_again(self.controller)

    def _move_to_destination(self):
        if self.destination_pos and self.destination_pos in self.matrix:
            self._move_to_pos_inside_matrix(self.destination_pos)
        else:
            self._skip_turn()

    def _move_to_pos_inside_matrix(self, pos):
        assert pos in self.matrix, f'{self.matrix.get_printable_dist_values()}'
        assert not self._is_occupied(pos)
        path = self.path_finder.get_path_on_matrix_to(self.matrix, pos)
        self.controller.handle_move_monster(self.monster, path)
        self.monster.moved = True


class DestinationFinder:
    def __init__(self):
        pass


def make_player_brain_act_again(controller):
    (controller.append_ai_callback())

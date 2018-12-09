import logging

from src.components.board.board import Board
from src.components.board.monster import Monster
from src.components.board.pathing import PathMatrix, PathMatrixFactory, \
    PathGenerator
from src.model import board_model


class SelectionHandler:
    """
    Accepts the board. Takes tile selection and converts them into actions.
    Executes these actions, and stores data that can be used for further actions
    by the controller, such as monster movement (for animation) or opening of
    summon windows.
    """

    def __init__(self, board, model):
        self.board: Board = board
        self.model: board_model.BoardModel = model

        self.previous_selected_monster: Monster = None
        self.selected_monster: Monster = None
        self.targeted_enemy: Monster = None
        self.actionlog: ActionLog = None
        self.adjacent_enemies = None
        self.path_matrix: PathMatrix = None

    def unselect_current_monster(self):
        self.board.matrix_monster = None
        self.selected_monster = None
        self.adjacent_enemies = None

    def unselect_enemy(self):
        self.targeted_enemy = None

    def select_tile(self, pos):
        if self._is_invalid_pos(pos):
            return None
        logging.info(f'Selected tile {pos}')
        self.actionlog = ActionLog()
        monster = self.board.monster_at(pos)
        if monster:
            self._click_monster(monster)
        else:
            self._click_terrain(pos)
        return self.actionlog

    def _is_invalid_pos(self, pos):
        return pos == (-1, -1)

    def _click_monster(self, monster):
        self.previous_selected_monster = self.selected_monster
        self.selected_monster = monster
        if self._monster_is_owned_by_player():
            if self._is_moveable():
                self._click_own_monster()
        else:
            self._click_enemy()

    def _monster_is_owned_by_player(self):
        return self.selected_monster.owner == self.get_current_player_id()

    def get_current_player_id(self):
        return self.board.get_current_player_id()

    def _is_moveable(self):
        return not self.selected_monster.moved

    def _click_own_monster(self):
        logging.info('Selected own monster')
        if self._selected_own_monster_then_selected_enemy():
            self._handle_attack_order()
        else:
            self._handle_own_monster_selection()

    def _selected_own_monster_then_selected_enemy(self):
        return (self.selected_monster != self.previous_selected_monster and
                not self._monster_has_moved_this_turn() and
                self.targeted_enemy)

    def _monster_has_moved_this_turn(self):
        return self.selected_monster.moved

    def _handle_attack_order(self):
        attacker = self.previous_selected_monster
        self.actionlog.next_action = ActionFlag.SHOW_PRE_COMBAT_SCREEN
        self.actionlog.combat_monsters = (attacker, self.targeted_enemy)
        attacker.moved = True
        logging.info(
            f'{attacker} is attacking monster '
            f'{self.targeted_enemy}')
        combat_log = self._get_combat_result()
        if combat_log.loser:
            logging.info(f'{combat_log.loser} was defeated!')
        self.actionlog.combat_log = combat_log
        self.unselect_enemy()
        self.unselect_current_monster()

    def _get_combat_result(self):
        combat_result = self.model.get_combat_result(
            self.selected_monster, self.targeted_enemy)
        return combat_result

    def _handle_own_monster_selection(self):
        self.actionlog.next_action = ActionFlag.SELECT_MONSTER
        self.actionlog.monster = self.selected_monster
        generator = PathMatrixFactory(self.board)
        self.path_matrix = generator.generate_path_matrix(
            self.selected_monster.pos)
        self.actionlog.tiles_to_highlight = self.path_matrix.dist_values
        self.adjacent_enemies = self.board.get_enemies_adjacent_to(
            self.selected_monster.pos)

    def _click_enemy(self):
        logging.info('Selected enemy')
        if self._adjacent_enemy_is_selected():
            self.targeted_enemy = self.selected_monster
            self._handle_attack_order()

    def _adjacent_enemy_is_selected(self):
        return (self.adjacent_enemies and
                self.selected_monster in self.adjacent_enemies)

    def _click_terrain(self, pos):
        logging.info('Selected terrain')
        if self._monster_can_be_moved_to(pos):
            self._handle_monster_movement(pos)
        elif self._lord_is_adjacent_to(pos):
            self.actionlog.next_action = ActionFlag.SUMMON_MONSTER
            self.actionlog.pos = pos

    def _monster_can_be_moved_to(self, pos):
        return (self.selected_monster and not self.selected_monster.moved and
                self.path_matrix.is_legal_destination(pos))

    def _lord_is_adjacent_to(self, tile):
        surrounding_tiles = self.board.get_tiles_adjacent_to(tile)
        for pos in surrounding_tiles:
            surrounding_monster = self.board.monster_at(pos)
            if surrounding_monster and surrounding_monster.is_lord():
                return True
        return False

    def _handle_monster_movement(self, pos):
        logging.info('Moving monster')
        self._add_path_to_action_log(pos)
        self._move_monster_to(pos)
        if self.board.tile_at(pos).has_tower():
            if self._selected_monster_does_not_own_tower_at(pos):
                self._handle_tower_capture(pos)
        if self.adjacent_enemies:
            self._handle_adjacent_enemies_after_moving()

    def _selected_monster_does_not_own_tower_at(self, pos):
        return self.board.terrain_owner_of(pos) != self.selected_monster.owner

    def _add_path_to_action_log(self, destination_tile):
        path_generator = PathGenerator(self.board)
        path_generator.set_path_matrix(self.path_matrix)
        path = path_generator.get_path_to(destination_tile)
        self.actionlog.path = path

    def _move_monster_to(self, destination):
        self.board.move_monster(self.selected_monster, destination)
        self.actionlog.next_action = ActionFlag.MOVE_MONSTER
        self.actionlog.monster = self.selected_monster
        self.adjacent_enemies = self.board.get_enemies_adjacent_to(destination)

    def _handle_tower_capture(self, pos):
        self.board.capture_terrain_at(pos, self.board.monster_at(pos).owner)
        self.actionlog.next_action = ActionFlag.CAPTURE_TOWER

    def _handle_adjacent_enemies_after_moving(self):
        self.actionlog.next_action = ActionFlag.SELECT_ENEMY
        # todo: display enemy highlights


class ActionLog:
    def __init__(self):
        self.event_queue = None
        self.combat_log = None
        self.current_action = None
        self.next_action = None
        self.attacks = None
        self.pos = None
        self.combat_monsters = None
        self.path = None
        self.move = None
        self.monster = None
        self.tiles_to_highlight = None


class ActionFlag:
    (SHOW_PRE_COMBAT_SCREEN, SHOW_COMBAT_SCREEN, SELECT_MONSTER, SELECT_ENEMY,
     MOVE_MONSTER, SUMMON_MONSTER, CAPTURE_TOWER) = range(7)

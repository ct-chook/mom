import logging

from src.components.board.board import Board
from src.components.board.monster import Monster
from src.controller import board_controller
from src.model import board_model


class SelectionHandler:
    """
    Takes tile selections from BoardController and uses them to make proper
    function calls for the BoardController

    Performs necessary actions using log retrieved from selector.

    From a mouseclick, the following can happen:
    - A monster moves, has event queue that needs to be added
    - A monster moves and attacks, has event queue that needs
    appending, controller has to open combat window and have event queue
    link to that and also display movement event. Movement event callback
    can be received from the view with repeats for length of path. The
    combat event can be retrieved from the combat log with callbacks to the
    combat window so the move event has to be made by the model first and
    then the combat event can be added to it by the controller so it needs
    to receive the combat log and the event queue so it can add to the
    event queue using its own function to open the combat window, and pass
    the combat log to the combat window.
    """

    def __init__(self, board, model, controller):
        self.board: Board = board
        self.model: board_model.BoardModel = model
        self.controller: board_controller.BoardController = controller

        self.pos = None
        self.previous_selected_monster: Monster = None
        self.selected_monster: Monster = None
        self.enemy_selection: Monster = None
        self.adjacent_enemies = None

    def click_tile(self, pos):
        self.pos = pos
        if not self.pos:
            return
        logging.info(f'Selected tile {self.pos}')
        monster_at_pos = self.board.monster_at(self.pos)
        if monster_at_pos:
            self._click_monster(monster_at_pos)
        else:
            self._click_terrain()

    def _click_monster(self, monster):
        if self._monster_is_owned_by_player(monster):
            self._click_own_monster(monster)
        else:
            self._click_enemy(monster)

    def _selected_monster_is_owned_by_player(self):
        return self.selected_monster.owner == self.get_current_player_id()

    def get_current_player_id(self):
        return self.board.get_current_player_id()

    def _click_own_monster(self, monster):
        logging.info('Selected own monster')
        self.selected_monster = monster
        if not self._selected_monster_may_move_this_turn():
            return
        self._handle_own_monster_selection()

    def _selected_monster_may_move_this_turn(self):
        return not self.selected_monster.moved

    def _handle_own_monster_selection(self):
        pos = self.selected_monster.pos
        self.model.generate_path_matrix_at(pos)
        posses = self.model.get_tiles_to_highlight()
        self.controller.highlight_tiles(posses)
        self.adjacent_enemies = self.model.get_adjacent_enemies_at(pos)

    def _click_enemy(self, monster):
        logging.info('Selected enemy')
        self.enemy_selection = monster
        if self._selection_is_adjacent_enemy():
            self._handle_target_enemy_for_attack(
                self.selected_monster, self.enemy_selection)

    def _selection_is_adjacent_enemy(self):
        return (self.adjacent_enemies and
                self.enemy_selection in self.adjacent_enemies)

    def _handle_target_enemy_for_attack(self, attacker, defender):
        self.controller.show_combat_window_for(attacker, defender)

    def _click_terrain(self):
        logging.info('Selected terrain')
        if self._selected_monster_can_be_moved_to_pos():
            self._handle_move_monster_to_pos()
        if self._monster_can_be_summoned_at_pos():
            self.controller.handle_summon_window_at(self.pos)

    def _selected_monster_can_be_moved_to_pos(self):
        return (self.selected_monster and
                self._selected_monster_may_move_this_turn() and
                self._is_valid_destination_for_selected_monster(self.pos))

    def _is_valid_destination_for_selected_monster(self, pos):
        return self.model.is_valid_destination(pos)

    def _monster_can_be_summoned_at_pos(self):
        return self.model.lord_is_adjacent_at(self.pos)

    def _handle_move_monster_to_pos(self):
        path = self.model.get_path_to(self.pos)
        self.adjacent_enemies = self.model.get_adjacent_enemies_at(self.pos)
        self.controller.handle_move_monster(self.selected_monster, path)

    def unselect_current_monster(self):
        self.board.matrix_monster = None
        self.selected_monster = None
        self.adjacent_enemies = None

    def unselect_enemy(self):
        self.enemy_selection = None

    def _monster_is_owned_by_player(self, monster):
        return monster.owner == self.get_current_player_id()

    def _lord_is_adjacent_to(self, tile):
        surrounding_tiles = self.board.get_tile_posses_adjacent_to(tile)
        for pos in surrounding_tiles:
            surrounding_monster = self.board.monster_at(pos)
            if surrounding_monster and surrounding_monster.is_lord():
                return True
        return False

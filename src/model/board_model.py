from src.components.board import players
from src.components.board.board import Board, MapLoader
from src.components.board.brain import BrainAction
from src.components.combat.attack import AttackFactory
from src.components.combat.combat import Combat
from src.components.combat.combatlog import CombatLog
from src.helper.Misc.constants import AiType, DayTime
from src.helper.selectionhandler import SelectionHandler


class BoardModel:
    """Holds everything related to the board and its rules"""

    def __init__(self, mapname='test'):
        self.selection_handler = None
        self.board = None
        self.players: players.PlayerList = None
        self.turn = 0
        self.sun_stance = 0
        self.board = Board()
        self.selection_handler = SelectionHandler(self.board, self)
        maploader = MapLoader(self.board)
        maploader.load_map(mapname)
        self.players = maploader.players
        self.players.create_brains_from_model(self)
        self.game_over = False  # jumps to true when no human players left

    def on_end_turn(self):
        self.selection_handler.unselect_current_monster()
        self.selection_handler.unselect_enemy()
        self.board.on_end_of_turn()
        self.turn += 1
        self.players.get_current_player().regenerate_mana()
        self.players.goto_next_player()
        if self._round_has_ended():
            self._on_end_round()

    def _round_has_ended(self):
        return self.turn % len(self.players) == 0

    def _on_end_round(self):
        self._progress_sun_stance()

    def _progress_sun_stance(self):
        self.sun_stance += 1
        if self.sun_stance >= 4:
            self.sun_stance = 0

    def get_combat_result(self, attacker, defender, range_=0):
        combat_result = Combat().monster_combat(
            (attacker, defender), range_, self.sun_stance)
        return combat_result

    def select_tile(self, tile_pos):
        self.selection_handler.select_tile(tile_pos)

    def process_combat_log(self, combatlog: CombatLog):
        for monster, hp in zip(combatlog.monsters, combatlog.hp_end):
            monster.hp = hp
        if combatlog.loser:
            self.kill_monster(combatlog.loser)
        for monster, exp in zip(combatlog.monsters, combatlog.exp):
            monster.award_exp(exp)
        for monster, promotion in zip(combatlog.monsters, combatlog.promotions):
            if promotion:
                monster.promote()

    def kill_monster(self, monster):
        self.board.remove_monster(monster)
        if monster.is_lord():
            self.remove_player_from_game(monster.owner)

    def remove_player_from_game(self, id_):
        self.players.remove_player(id_)
        if self._no_human_players_left() or len(self.players) < 2:
            self.game_over = True

    def _no_human_players_left(self):
        for id_ in range(len(self.players)):
            player = self.players.get_player_by_id(id_)
            if player.ai_type == AiType.human:
                return False
        return True

    def get_current_player_monsters(self):
        player_id = self.players.get_current_player_id()
        return self.board.monsters[player_id]

    def summon_monster_at(self, monster_type, pos):
        """Returns None if monster could not be summoned"""
        return self.board.summon_monster(
            monster_type, pos, self.get_current_player().number)

    def get_current_player(self):
        return self.players.get_current_player()

    def get_player_of_number(self, number):
        return self.players.get_player_by_id(number)

    def get_brain_action(self) -> BrainAction:
        """
        There are different AI types. Each of them use them can use unique data
        structures.
        """
        player = self.players.get_current_player()
        if player.ai_type == AiType.human:
            # humans must use their own intelligence
            raise AttributeError('Requested AI action from human player')
        action = player.get_next_ai_action()
        return action

    def execute_brain_action(self):
        action = self.get_brain_action()
        if action.monster_to_summon:
            self._handle_brain_monster_summon(action)
        elif action.monster_to_move:
            self._handle_brain_monster_move(action)
        elif action.end_turn:
            self._handle_brain_end_turn()

    def _handle_brain_monster_summon(self, action):
        pass

    def _handle_brain_monster_move(self, action):
        pass

    def _handle_brain_end_turn(self):
        pass

    def process_brain_action(self, action: BrainAction):
        if action.monster_to_move:
            self.board.move_monster(
                action.monster_to_move, action.pos_to_move)
        elif action.end_turn:
            self.on_end_turn()
        else:
            raise AttributeError(f'Unknown brain action {action}')

    def get_expected_damage_between(self, attacker, defender, attack_range):
        """This uses current sun stance"""
        attacks = self.get_short_and_long_attacks((attacker, defender))
        return attacks.get_attack(0, attack_range).get_expected_damage()

    def get_short_and_long_attacks(self, monsters):
        attack_factory = AttackFactory()
        return attack_factory.get_all_attacks_between_monsters(
            monsters, self.sun_stance)


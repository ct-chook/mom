from src.components.board import players
from src.components.board.board import Board, MapLoader
from src.components.board.brain import BrainAction
from src.components.board.pathing import PathMatrixFactory
from src.components.board.pathing_components import PathMatrix
from src.components.combat.attack import AttackFactory
from src.components.combat.combat import Combat
from src.components.combat.combatlog import CombatLog
from src.helper.Misc.constants import AiType, Terrain


class BoardModel:
    """Holds everything related to the board and its rules"""

    def __init__(self, mapname='test'):
        self.selection_handler = None
        self.board = None
        self.players: players.PlayerList = None
        self.turn = 0
        self.sun_stance = 0
        self.board = Board()
        maploader = MapLoader(self.board)
        maploader.load_map(mapname)
        self.players = maploader.players
        self.players.create_brains_from_model(self)
        self.game_over = False  # jumps to true when no human players left
        self.path_matrix: PathMatrix = None
        self.matrix_factory = PathMatrixFactory(self.board)

    def on_end_turn(self):
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

    def get_combat_result(self, attacker, defender, attack_range):
        combat_result = Combat().monster_combat(
            (attacker, defender), attack_range, self.sun_stance)
        return combat_result

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
            monster_type, pos, self.get_current_player().id_)

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

    def get_expected_damage_between(self, attacker, defender, attack_range):
        """This uses current sun stance"""
        attacks = self.get_short_and_long_attacks((attacker, defender))
        return attacks.get_attack(0, attack_range).get_expected_damage()

    def get_short_and_long_attacks(self, monsters):
        attack_factory = AttackFactory()
        return attack_factory.get_all_attacks_between_monsters(
            monsters, self.sun_stance)

    def has_capturable_tower_at(self, pos):
        return (self.board.tile_at(pos).terrain == Terrain.TOWER and
                self.board.tile_at(pos).is_hostile_terrain(
                    self.players.get_current_player()))

    def move_monster_to(self, monster, pos):
        self.board.move_monster(monster, pos)

    def capture_tower_at(self, pos):
        self.board.capture_terrain_at(pos, self.get_current_player().id_)

    def get_adjacent_enemies_at(self, pos):
        return self.board.get_enemies_adjacent_to(pos)

    def generate_path_matrix_at(self, pos):
        self.path_matrix = self.matrix_factory.generate_path_matrix(pos)

    def is_valid_destination(self, pos):
        return self.path_matrix.is_legal_destination(pos)

    def lord_is_adjacent_at(self, pos):
        posses = self.board.get_tile_posses_adjacent_to(pos)
        for pos in posses:
            monster = self.board.monster_at(pos)
            if (monster and monster.is_lord() and
                    self._current_player_owns(monster)):
                return True

    def _current_player_owns(self, monster):
        return monster.owner == self.get_current_player().id_

    def get_tiles_to_highlight(self):
        """Returns a list of posses that should be highlighted by the view

        Highlighted tiles should be whatever the monster can move to, and also
        any monsters that are within attack range.
        """
        return self.path_matrix.accessible_positions

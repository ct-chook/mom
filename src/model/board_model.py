import logging

from src.components.board import players
from src.components.board.board import BoardBuilder
from src.components.board.pathing import PathMatrixFactory, PathFactory
from src.components.board.pathing_components import PathMatrix
from src.components.combat.attack import AttackFactory, AttackCollection
from src.components.combat.combatlog import CombatLog
from src.controller.mainmenu_controller import CappedCounter
from src.helper.Misc.constants import AiType, Terrain
from src.helper.Misc.datatables import DataTables


class BoardModel:
    """Holds everything related to the board and its rules"""

    def __init__(self, mapoptions=None):
        self.path_matrix: PathMatrix = None
        self.game_over = False
        self.turn = 0
        self.sun_stance = CappedCounter(0, 4)

        self.board = BoardBuilder().load_map(mapoptions)
        self.players: players.PlayerList = self.board.players
        self.matrix_factory = PathMatrixFactory(self.board)

        # check if there are any human players, if so the game ends when
        # all of them lose, otherwise it keeps going until one team wins
        self.ai_only_match = True
        self._set_ai_only_status()

    def _set_ai_only_status(self):
        for player in self.players:
            if player.ai_type == AiType.human:
                self.ai_only_match = False
                break

    def on_end_turn(self):
        current_player = self.get_current_player()
        for monster in self.board.monsters.get_for(current_player):
            monster.moved = False
            if self._is_on_terrain_that_heals(monster):
                monster.tower_heal()
        logging.info(f'Ending turn of {current_player}')
        self.turn += 1
        self.players.get_current_player().regenerate_mana()
        self.players.goto_next_player()
        if self._round_has_ended():
            self._on_end_round()

    def _is_on_terrain_that_heals(self, monster):
        """ todo check what terrain heals in-game

        Seems to be tower, not sure about castle. not fortress.
        """
        terrain = monster.terrain
        return terrain == Terrain.TOWER or terrain == Terrain.CASTLE

    def _round_has_ended(self):
        return self.turn == len(self.players)

    def _on_end_round(self):
        self._progress_sun_stance()

    def _progress_sun_stance(self):
        self.sun_stance.flip()

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
        logging.info(f'Removing monster {monster}')
        self.board.remove_monster(monster)
        if monster.is_lord():
            self.remove_player_from_game(monster.owner)

    def remove_player_from_game(self, id_):
        self.players.remove_player(id_)
        if self._no_human_players_left() or self._only_one_team_left():
            self.game_over = True
            # assert False, 'game over'

    def _no_human_players_left(self):
        if self.ai_only_match:
            return False
        for player in self.players:
            if player.ai_type == AiType.human:
                return False
        return True

    def _only_one_team_left(self):
        teams = set()
        for player in self.players:
            teams.add(player.team)
        if len(teams) == 1 and 0 not in teams:
            return True
        else:
            return False

    def get_current_player_monsters(self):
        player = self.players.get_current_player()
        return self.get_monsters_of_player(player)

    def get_monsters_of_player(self, player):
        return self.board.get_monsters_for(player)

    def summon_monster_at(self, monster_type, pos):
        """Returns None if monster could not be summoned"""
        return self.summon_monster(
            monster_type, pos, self.get_current_player())

    def summon_monster(self, monster_type, pos, owner):
        """Adds a monster and checks/reduces mana and flags it"""
        assert not self.board.tile_at(pos).monster, (
            f'{self.board.print()}\n'
            f'Tried to summon {DataTables.get_monster_stats(monster_type).name}'
            f'at location occupied by {self.board.monster_at(pos).name} ')
        if owner.max_monsters_reached():
            return None
        summon_cost = DataTables.get_monster_stats(monster_type).summon_cost
        if owner.mana < summon_cost:
            logging.info('Not enough mana to summon monster')
            return None
        monster = self.board.place_new_monster(monster_type, pos, owner)
        owner.decrease_mana_by(summon_cost)
        monster.moved = True
        return monster

    def get_current_player(self):
        return self.players.get_current_player()

    def get_player_of_number(self, number):
        return self.players.get_player_by_id(number)

    def get_expected_damage_between(self, attacker, defender, attack_range):
        """This uses current sun stance"""
        attacks = self.get_short_and_long_attacks((attacker, defender))
        return (attacks.get_attack(0, attack_range).get_expected_damage(),
                attacks.get_attack(1, attack_range).get_expected_damage())

    def get_short_and_long_attacks(self, monsters) -> AttackCollection:
        attack_factory = AttackFactory()
        return attack_factory.get_all_attacks_between_monsters(
            monsters,
            self.sun_stance.value)

    def has_capturable_tower_at(self, pos):
        return (self.board.has_tower_at(pos)
                and self.get_current_player().is_enemy_of(
                    self.board.tower_owner_at(pos)))

    def move_monster_to(self, monster, pos):
        self.board.move_monster(monster, pos)

    def capture_tower_at(self, pos):
        self.board.capture_terrain_at(pos, self.get_current_player())

    def get_adjacent_enemies_at(self, pos):
        return self.board.get_enemies_adjacent_to(pos)

    def generate_path_matrix_at(self, pos):
        self.path_matrix = self.matrix_factory.generate_path_matrix(pos)

    def is_valid_destination(self, pos):
        return self.path_matrix.is_legal_destination(pos)

    def lord_is_adjacent_at(self, pos):
        posses = self.board.get_posses_adjacent_to(pos)
        for pos in posses:
            monster = self.board.monster_at(pos)
            if (monster and monster.is_lord() and
                    self._current_player_owns(monster)):
                return True

    def _current_player_owns(self, monster):
        return monster.owner is self.get_current_player()

    def get_tiles_to_highlight(self):
        """Returns a list of posses that should be highlighted by the view

        Highlighted tiles should be whatever the monster can move to, and also
        any monsters that are within attack range.
        """
        return self.path_matrix.accessible_positions

    def get_path_to(self, pos):
        assert self.path_matrix
        pathfinder = PathFactory(self.board)
        return pathfinder.get_path_on_matrix_to(self.path_matrix, pos)

    def get_lord_of_player(self, player=None):
        # todo include direct link to lord
        if player is None:
            player = self.get_current_player()
        return self.board.get_lord_of(player)

    def is_valid_pos_for_summon(self, pos):
        return (self.board.monster_at(pos) is None
                and self._is_valid_terrain_for_summon(pos))

    def _is_valid_terrain_for_summon(self, pos):
        terrain = self.board.terrain_at(pos)
        return (terrain == Terrain.TOWER
                or terrain == Terrain.FORTRESS
                or terrain == Terrain.CASTLE)

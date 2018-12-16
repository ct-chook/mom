import logging
import random

from src.components.board import players
from src.components.board.monster import Monster
from src.components.board.tile import TileModifier, Tile
from src.helper.Misc import constants
from src.helper.Misc.constants import ROOT, MonsterType, Terrain, AiType, is_odd
from src.helper.Misc.datatables import DataTables


class Board:
    """Represent the board and everything on it, including monsters.

    Holds limited information about the game state. Rules and game state are
    stored by the board wrapper. It should only hold information about the
    pieces and terrain.
    """

    def __init__(self):
        self.y_max = None
        self.x_max = None
        self.tiles = []
        self.monsters = {}
        # list of players is used to check for enemies
        self._players: players.PlayerList = None

    def set_players(self, players_):
        self._players = players_
        for n in range(len(players_)):
            self.monsters[n] = []

    def on_end_of_turn(self):
        current_player = self.get_current_player_id()
        if current_player in self.monsters:
            for monster in self.monsters[self.get_current_player_id()]:
                monster.moved = False
        logging.info(
            f'Ending turn of {self._players.get_current_player().id_}')

    def tile_at(self, pos) -> Tile:
        return self.tiles[pos[0]][pos[1]]

    def on_tile(self, pos) -> TileModifier:
        return TileModifier(self.tile_at(pos))

    def terrain_at(self, pos):
        if not self.is_valid_board_pos(pos):
            return None
        return self.tile_at(pos).terrain

    def monster_at(self, pos) -> Monster:
        return self.tile_at(pos).monster

    def terrain_owner_of(self, pos):
        return self.tile_at(pos).owner

    def summon_monster(self, monster_type, pos, owner):
        """Adds a monster and checks/reduces mana and flags it"""
        if self.tile_at(pos).monster:
            logging.info('Tried to summon monster at occupied location')
            return None
        summon_cost = DataTables.get_monster_stats(monster_type).summon_cost
        if self._get_current_player().mana < summon_cost:
            logging.info('Not enough mana to summon monster')
            return None
        monster = self.place_new_monster(monster_type, pos, owner)
        self._players.get_current_player().decrease_mana_by(summon_cost)
        monster.moved = True
        return monster

    def place_new_monster(self, monster_type, pos=(0, 0), owner=0) -> Monster:
        """Places a new monster without checking/reducing mana or flagging it"""
        if self.monster_at(pos):
            raise AttributeError(
                f'Tried to summon monster at {pos} but it is already occupied')
        new_monster = Monster(monster_type, pos, owner, self.terrain_at(pos))
        self.monsters[owner].append(new_monster)
        self.tile_at(new_monster.pos).monster = new_monster
        return new_monster

    def remove_monster_at(self, pos):
        monster = self.monster_at(pos)
        self.remove_monster(monster)

    def remove_monster(self, monster):
        assert monster
        logging.info(f'removing {monster.name}')
        owner = monster.owner
        assert monster in self.monsters[owner]
        self.monsters[owner].remove(monster)
        self.tile_at(monster.pos).monster = None

    def get_enemies_adjacent_to(self, pos):
        enemies = []
        adjacent_tiles = self.get_tile_posses_adjacent_to(pos)
        for adj_pos in adjacent_tiles:
            adj_tile = self.tile_at(adj_pos)
            if (adj_tile.monster and
                    adj_tile.monster.owner != self.get_current_player_id()):
                enemies.append(adj_tile.monster)
        return enemies

    def get_tile_posses_adjacent_to(self, pos):
        """Boring but important stuff to retrieve all adjacent tiles

          @ | @
        @ | @ | @  <-- we are at the middle tile
          @ | @
        """
        x, y = pos
        adjacent_posses = []
        self._add_left_and_right_tiles(adjacent_posses, x, y)
        # add top left, top right, bot left, bot right
        row_is_odd = is_odd(y)
        if row_is_odd:
            self._add_odd_row_tiles(adjacent_posses, x, y)
        else:
            self._add_even_row_tiles(adjacent_posses, x, y)
        for pos in adjacent_posses:
            assert pos[0] >= 0, f'could not get adj posses of {pos}'
            assert pos[1] >= 0, f'could not get adj posses of {pos}'

        return adjacent_posses

    def _add_left_and_right_tiles(self, adjacent_posses, x, y):
        # left
        if x - 1 >= 0:
            adjacent_posses.append((x - 1, y))
        # right
        if x + 1 < self.x_max:
            adjacent_posses.append((x + 1, y))

    def _add_odd_row_tiles(self, adjacent_posses, x, y):
        if y - 1 >= 0:
            adjacent_posses.append((x, y - 1))
        if y - 1 >= 0 and x + 1 < self.x_max:
            adjacent_posses.append((x + 1, y - 1))
        if y + 1 < self.y_max:
            adjacent_posses.append((x, y + 1))
        if y + 1 < self.y_max and x + 1 < self.x_max:
            adjacent_posses.append((x + 1, y + 1))

    def _add_even_row_tiles(self, adjacent_posses, x, y):
        if y - 1 >= 0 and x - 1 >= 0:
            adjacent_posses.append((x - 1, y - 1))
        if y - 1 >= 0:
            adjacent_posses.append((x, y - 1))
        if y + 1 < self.y_max and x - 1 >= 0:
            adjacent_posses.append((x - 1, y + 1))
        if y + 1 < self.y_max:
            adjacent_posses.append((x, y + 1))

    def is_valid_board_pos(self, pos):
        return self.x_max > pos[0] >= 0 and 0 <= pos[1] < self.y_max

    def get_current_player_id(self):
        return self._players.get_current_player_id()

    def _get_current_player(self):
        return self._players.get_current_player()

    def move_monster(self, monster, destination):
        """Changes the monster position on the board and flags it as moved"""
        if monster.moved:
            logging.info(
                f'Tried to move monster {monster} but it already moved')
            return
        self.set_monster_pos(monster, destination)
        monster.moved = True

    def set_monster_pos(self, monster, new_pos):
        """Ignores movement check, useful for spell effects, or testing"""
        self.on_tile(monster.pos).set_monster_to(None)
        self.on_tile(new_pos).set_monster_to(monster)
        monster.pos = new_pos
        monster.terrain = self.terrain_at(new_pos)

    def capture_terrain_at(self, pos, player_id):
        """Change tower count if a tower was captured, and change tile owner"""
        tile = self.tile_at(pos)
        old_owner = tile.owner
        if tile.terrain == Terrain.TOWER and old_owner is not None:
            self._players.get_player_by_id(old_owner).tower_count -= 1
        tile.owner = player_id
        self._players.get_player_by_id(player_id).tower_count += 1

    def pos_is_enemy_terrain(self, pos):
        return self.is_enemy_id(self.tile_at(pos).owner)

    def is_enemy_id(self, id_):
        return id_ is not None and id_ != self.get_current_player_id()

    def debug_print(self):
        BoardPrinter(self).debug_print()


class BoardPrinter:
    def __init__(self, board):
        self.board = board

    def debug_print(self):
        for y in range(self.board.y_max):
            row = []
            for x in range(self.board.x_max):
                tile = self.board.tile_at((x, y))
                if tile.monster:
                    row.append(self.monster_to_char(tile.monster))
                else:
                    row.append(self.terrain_to_char(tile.terrain))
            if y % 2 == 0:
                print(' '.join(row))
            else:
                print(' ' + ' '.join(row))
        row = []
        for n in range(self.board.x_max):
            p = str(n)
            row.append(p[-1])
        print(' '.join(row))

    def monster_to_char(self, monster):
        return monster.name[0]

    def terrain_to_char(self, terrain):
        if terrain == Terrain.TOWER:
            return 'l'
        elif terrain == Terrain.DUNE:
            return ':'
        elif terrain == Terrain.FOREST:
            return 't'
        elif terrain == Terrain.FORTRESS:
            return '='
        elif terrain == Terrain.GRASS:
            return '.'
        elif terrain == Terrain.MAIN_FORTRESS:
            return '@'
        elif terrain == Terrain.MOUNTAIN:
            return 'm'
        elif terrain == Terrain.OCEAN:
            return '~'
        elif terrain == Terrain.RIVER:
            return '-'
        elif terrain == Terrain.ROCKY:
            return 'n'
        elif terrain == Terrain.SWAMP:
            return 'o'
        elif terrain == Terrain.TUNDRA:
            return '#'
        elif terrain == Terrain.VOLCANO:
            return '^'
        else:
            return '?'


class MapLoader:
    def __init__(self, board):
        self.board: Board = board
        self.mapname = None
        self.x_max = None
        self.y_max = None
        self.players: players.PlayerList = None

    def load_map(self, mapoptions=None):
        if not mapoptions:
            mapname = 'test'
        else:
            mapname = mapoptions.mapname
        self.mapname = mapname
        if self.mapname == 'random':
            self._fill_with_grass_tiles()
            self._randomize_terrain()
            self._initialize_random_monsters()
        else:
            self._create_players(mapoptions)
            if self.mapname == 'test':
                layout = constants.TEST_LAYOUT
                self.set_terrain_using_layout(layout)
                self.board.set_players(self.players)
                self.set_test_monsters()
            else:
                layout = self._get_layout_from_map_file()
                self.set_terrain_using_layout(layout)
                self.board.set_players(self.players)

    def _create_players(self, mapoptions):
        if mapoptions and mapoptions.players:
            self.players = mapoptions.players
            return
        self.players = players.PlayerList()
        self.players.add_player(0, AiType.human, 50)
        self.players.add_player(1, AiType.idle, 50)
        self.players.add_player(2, AiType.idle, 50)
        self.players.add_player(3, AiType.idle, 50)

    def _get_layout_from_map_file(self):
        with open(f'{ROOT}/src/data/maps/{self.mapname}', 'r') as fd:
            content = fd.read()
            layout_strings = content.split(', ')
            layout = []
            for layout_string in layout_strings:
                layout.append(int(layout_string))
        return layout

    def set_test_monsters(self):
        # todo: monsters should be part of save data
        # inside volcano: 1,6
        # left of mountain: 2, 19
        blue, red = range(2)
        self.board.place_new_monster(MonsterType.ROMAN, (1, 6), blue)
        self.board.place_new_monster(MonsterType.ROMAN, (1, 19), blue)
        self.board.place_new_monster(MonsterType.PHOENIX, (1, 18), blue)
        self.board.place_new_monster(MonsterType.CHIMERA, (1, 17), red)
        self.board.place_new_monster(MonsterType.FIGHTER, (5, 5), blue)
        # lords
        self.board.place_new_monster(MonsterType.DAIMYOU, (9, 11), blue)
        self.board.place_new_monster(MonsterType.WIZARD, (11, 11), red)
        # water
        self.board.place_new_monster(MonsterType.MARMAID, (12, 16), blue)
        self.board.place_new_monster(MonsterType.KRAKEN, (13, 16), red)
        # pool
        self.board.place_new_monster(MonsterType.OCTOPUS, (12, 7), blue)
        self.board.place_new_monster(MonsterType.SIRENE, (12, 8), blue)
        # random
        self.board.place_new_monster(random.randint(1, 82), (8, 8), blue)
        self.board.place_new_monster(random.randint(1, 82), (8, 9), red)

    def _add_random_monsters(self, player):
        # add lord
        self.board.place_new_monster(
            MonsterType.DAIMYOU + player,
            (self._get_random_x(), self._get_random_y()),
            player)
        # adds phoenix for testing purposes
        self.board.place_new_monster(
            MonsterType.PHOENIX,
            (self._get_random_x(), self._get_random_y()),
            player)
        for _ in range(5):
            self.board.place_new_monster(
                random.randint(10, 82),
                (self._get_random_x(), self._get_random_y()),
                player)

    def _get_random_y(self):
        return random.randint(0, self.y_max - 1)

    def _get_random_x(self):
        return random.randint(0, self.x_max - 1)

    def set_terrain_using_layout(self, layout, mode=0):
        self.x_max = layout[0]
        self.y_max = layout[1]
        self.board.x_max = self.x_max
        self.board.y_max = self.y_max
        self._fill_with_grass_tiles()
        if len(layout) - 2 != self.x_max * self.y_max:
            raise IndexError(
                f'Error setting terrain layout, {self.x_max}:{self.y_max} but '
                f'only {len(layout) - 2} tiles')
        if mode == 0:
            n = 2
            for x in range(self.x_max):
                for y in range(self.y_max):
                    self.board.tile_at((x, y)).terrain = layout[n]
                    n += 1
        else:
            for x in range(self.x_max):
                for y in range(self.y_max):
                    self.board.tile_at((x, y)).terrain = \
                        layout[2 + x + y * self.x_max]

    def _fill_with_grass_tiles(self):
        for x in range(self.x_max):
            self.board.tiles.append([])
            for y in range(self.y_max):
                self.board.tiles[x].append(Tile(Terrain.GRASS))

    def _randomize_terrain(self):
        pos = (1, 1)
        for terrain in range(13):
            for i in range(round(self.x_max * self.y_max * 0.05)):
                while self.board.terrain_at(pos) != Terrain.GRASS:
                    pos = (self._get_random_x(), self._get_random_y())
                    self.board.tile_at(pos).terrain = terrain

    def _initialize_random_monsters(self):
        for player_id in range(len(self.board._players)):
            self._add_random_monsters(player_id)

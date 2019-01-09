import logging
import random

from src.components.board import players
from src.components.board.monster import Monster
from src.components.board.tile import Tile, TileModifier
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
        self.towers = {}
        self.lords = {}
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

    def terrain_at(self, pos):
        if not self.is_valid_board_pos(pos):
            return None
        return self.tile_at(pos).terrain

    def monster_at(self, pos) -> Monster:
        return self.tile_at(pos).monster

    def set_terrain_to(self, pos, terrain):
        """Change terrain type of tile at pos and check tower bookkeeping"""
        if pos in self.towers:
            self.towers.pop(pos)
        self.tile_at(pos).terrain = terrain
        if terrain == Terrain.TOWER:
            if pos not in self.towers:
                self.towers[pos] = None

    def summon_monster(self, monster_type, pos, owner):
        """Adds a monster and checks/reduces mana and flags it"""
        assert not self.tile_at(pos).monster, f'{self.debug_print()}' \
            f'Tried to summon ' \
            f'{DataTables.get_monster_stats(monster_type).name} at ' \
            f'location occupied by {self.monster_at(pos).name} '
        summon_cost = DataTables.get_monster_stats(monster_type).summon_cost
        if self._get_current_player().mana < summon_cost:
            logging.info('Not enough mana to summon monster')
            return None
        assert (self._get_current_player().tower_count + 1
                >= len(self.monsters[self.get_current_player_id()])), (
            f'Not enough towers, only have '
            f'{self._get_current_player().tower_count}')
        monster = self.place_new_monster(monster_type, pos, owner)
        self._players.get_current_player().decrease_mana_by(summon_cost)
        monster.moved = True
        return monster

    def place_new_monster(self, monster_type, pos=(0, 0), owner=0) -> Monster:
        """Places a new monster without checking/reducing mana or flagging it"""
        assert not self.monster_at(pos), \
            f'Tried to summon a ' \
            f'{DataTables.get_monster_stats(monster_type).name} at {pos} ' \
            f'but it is already occupied by a {self.monster_at(pos)} '
        new_monster = Monster(monster_type, pos, owner, self.terrain_at(pos))
        self.monsters[owner].append(new_monster)
        self.tile_at(new_monster.pos).monster = new_monster
        return new_monster

    def has_tower_at(self, pos):
        return pos in self.towers

    def tower_owner_at(self, pos):
        assert pos in self.towers
        return self.towers[pos]

    def set_tower_owner_at(self, pos, player_id):
        assert pos in self.towers
        self.towers[pos] = player_id

    def tower_is_capturable_by(self, pos, player_id):
        return not self.is_friendly_player(
                    self.tower_owner_at(pos), player_id)

    def get_capturable_towers_for_player(self, player_id):
        towers = {}
        for pos in self.towers:
            if not self.is_friendly_player(self.towers[pos], player_id):
                towers[pos] = player_id
        return towers

    def is_friendly_player(self, id1, id2):
        return id1 == id2

    def get_enemy_lord_for_player(self, player):
        for player_id in self.lords:
            if not self.is_friendly_player(self.lords[player_id], player):
                return self.lords[player_id]
        assert False, f'Could not find enemy lord for player {player}'

    def on_tile(self, pos):
        return TileModifier(pos, self)

    def remove_monster(self, monster):
        assert monster
        logging.info(f'removing {monster.name}')
        owner = monster.owner
        assert monster in self.monsters[owner]
        self.monsters[owner].remove(monster)
        self.tile_at(monster.pos).monster = None

    def get_enemies_adjacent_to(self, pos):
        enemies = []
        adjacent_tiles = self.get_posses_adjacent_to(pos)
        for adj_pos in adjacent_tiles:
            adj_tile = self.tile_at(adj_pos)
            if (adj_tile.monster
                    and not self.is_friendly_player(
                        adj_tile.monster.owner, self.get_current_player_id())):
                enemies.append(adj_tile.monster)
        return enemies

    def get_lord_of_player(self, player_id):
        assert player_id in self.lords, f'Player {player_id} has no lord set'
        return self.lords[player_id]

    def get_posses_adjacent_to(self, pos):
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
        assert not monster.moved, f'{self.debug_print()}' \
            f'Tried to move monster {monster} but it already moved'
        self.set_monster_pos(monster, destination)
        monster.moved = True

    def set_monster_pos(self, monster, new_pos):
        """Ignores movement check, useful for spell effects, or testing"""
        self.tile_at(monster.pos).monster = None
        self.tile_at(new_pos).monster = monster
        monster.pos = new_pos
        monster.terrain = self.terrain_at(new_pos)

    def capture_terrain_at(self, pos, player_id):
        """Change tower count if a tower was captured, and change tile owner"""
        tile = self.tile_at(pos)
        old_owner = self.tower_owner_at(pos)
        if tile.terrain == Terrain.TOWER and old_owner is not None:
            self._players.get_player_by_id(old_owner).tower_count -= 1
        self.set_tower_owner_at(pos, player_id)
        self._players.get_player_by_id(player_id).tower_count += 1

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
            return '🌲'
        elif terrain == Terrain.FORTRESS:
            return '='
        elif terrain == Terrain.GRASS:
            return '.'
        elif terrain == Terrain.MAIN_FORTRESS:
            return '@'
        elif terrain == Terrain.MOUNTAIN:
            return '⛰'
        elif terrain == Terrain.OCEAN:
            return '🌊'
        elif terrain == Terrain.RIVER:
            return '-'
        elif terrain == Terrain.ROCKY:
            return 'n'
        elif terrain == Terrain.SWAMP:
            return 'o'
        elif terrain == Terrain.TUNDRA:
            return '#'
        elif terrain == Terrain.VOLCANO:
            return '🌋'
        else:
            return '?'


class MapLoader:
    def __init__(self, board):
        self.board: Board = board
        self.mapname = None
        self.x_max = None
        self.y_max = None
        self.players: players.PlayerList = None
        self.start_posses = []
        self.mapoptions = None

    def load_map(self, mapoptions=None):
        self.mapoptions = mapoptions
        if not mapoptions:
            mapname = 'test'
        else:
            mapname = mapoptions.mapname
        self.mapname = mapname
        if self.mapname == 'random':
            # todo below is ugly and bad
            self.x_max = 20
            self.y_max = 20
            self.board.x_max = self.x_max
            self.board.y_max = self.y_max
            self._fill_with_grass_tiles()
            self._randomize_terrain()
            self._create_players(mapoptions)
            self.board.set_players(self.players)
        else:
            self._create_players(mapoptions)
            if self.mapname == 'test':
                test = True
                self.mapname = 'test.map'
            else:
                test = False
            layout = self._get_layout_from_map_file()
            self.set_map_using_layout(layout)
            self.board.set_players(self.players)
            self._add_lords()
            if test:
                self.set_test_monsters()

    def _create_players(self, mapoptions):
        if mapoptions and mapoptions.players:
            self.players = mapoptions.players
            return
        self.players = players.PlayerList()
        self.players.add_player(1, AiType.human, 50)
        self.players.add_player(2, AiType.idle, 50)
        self.players.add_player(3, AiType.idle, 50)
        self.players.add_player(4, AiType.idle, 50)

    def _get_layout_from_map_file(self):
        assert self.mapname, 'No mapname set'
        with open(f'{ROOT}/src/data/maps/{self.mapname}', 'r') as fd:
            content = fd.read()
        return self._get_layout_from_content(content)

    def _get_layout_from_content(self, content):
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
        # water
        self.board.place_new_monster(MonsterType.MARMAID, (12, 16), blue)
        self.board.place_new_monster(MonsterType.KRAKEN, (13, 16), red)
        # pool
        self.board.place_new_monster(MonsterType.OCTOPUS, (12, 7), blue)
        self.board.place_new_monster(MonsterType.SIRENE, (12, 8), blue)
        # random
        self.board.place_new_monster(random.randint(1, 82), (8, 8), blue)
        self.board.place_new_monster(random.randint(1, 82), (8, 9), red)

    def _get_random_y(self):
        return random.randint(0, self.y_max - 1)

    def _get_random_x(self):
        return random.randint(0, self.x_max - 1)

    def set_map_using_layout(self, layout, mode=0):
        """Parses the layout to set up the terrain

        How it works: the first two integers are the width and height,
        respectively. Next are a series of integer representing the terrain for
        each row. Lastly there are eight integers representing the starting
        positions for each player.
        """
        self.x_max = layout[0]
        self.y_max = layout[1]
        self.board.x_max = self.x_max
        self.board.y_max = self.y_max
        self._fill_with_grass_tiles()
        if len(layout) - 10 != self.x_max * self.y_max:
            raise IndexError(
                f'Error setting terrain layout, {self.x_max}:{self.y_max} but '
                f'{len(layout) - 10} tiles')
        # mode should be unified to just one, right now it transposes the layout
        if mode == 0:
            n = 2
            for x in range(self.x_max):
                for y in range(self.y_max):
                    self.board.set_terrain_to((x, y), layout[n])
                    n += 1
        else:
            for x in range(self.x_max):
                for y in range(self.y_max):
                    self.board.set_terrain_to(
                        (x, y), layout[2 + x + y * self.x_max])
        # grab the starting positions
        n = len(layout) - 8
        for _ in range(4):
            self.start_posses.append((layout[n], layout[n + 1]))
            n += 2

    def _add_lords(self):
        n = 0
        for player in self.players.players:
            pos = self.start_posses[n]
            lord = self.board.place_new_monster(player.lord_type, pos, n)
            self.board.lords[n] = lord
            n += 1

    def _fill_with_grass_tiles(self):
        assert self.x_max
        assert self.y_max
        for x in range(self.x_max):
            self.board.tiles.append([])
            for y in range(self.y_max):
                self.board.tiles[x].append(Tile(Terrain.GRASS))

    def _randomize_terrain(self):
        pos = (self._get_random_x(), self._get_random_y())
        for terrain in range(13):
            for i in range(round(self.x_max * self.y_max * 0.05)):
                while self.board.terrain_at(pos) != Terrain.GRASS:
                    pos = (self._get_random_x(), self._get_random_y())
                self.board.on_tile(pos).set_terrain_to(terrain)

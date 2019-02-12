import logging
import random
import re
from math import floor

from src.components.board.players import Player, PlayerList
from src.components.board import players
from src.components.board.monster import Monster
from src.components.board.tile import Tile, TileModifier
from src.helper.Misc.constants import ROOT, Terrain, AiType, is_odd
from src.helper.Misc.datatables import DataTables


class TowerList:
    def __init__(self):
        self.towers = {}

    def add_at(self, pos):
        assert pos not in self.towers
        self.towers[pos] = None

    def remove_at(self, pos):
        assert pos in self.towers
        self.towers.pop(pos)

    def exist_at(self, pos):
        return pos in self.towers

    def owner_at(self, pos) -> Player:
        assert pos in self.towers, f'could not find {pos} in {self.towers}'
        return self.towers[pos]

    def set_owner_at_pos(self, pos, owner):
        assert pos in self.towers
        self.towers[pos] = owner

    def get_capturable_towers_for_player(self, player) -> dict:
        towers = {}
        for pos in self.towers:
            if player.is_enemy_of(self.owner_at(pos)):
                towers[pos] = player
        return towers

    def __iter__(self):
        return iter(self.towers)


class LordList:
    def __init__(self):
        self.lords = {}

    def add(self, lord: Monster):
        assert lord is not None
        self.lords[lord.owner] = lord

    def remove(self, player):
        self.lords.pop(player)

    def get_for(self, player) -> Monster:
        assert type(player) is not int, 'Must pass player object, not integer'
        assert player in self.lords, f'Player "{player}" has no lord set'
        return self.lords[player]

    def __iter__(self):
        return iter(self.lords.values())

    def __repr__(self):
        lords = []
        for lord in self.lords.values():
            lords.append(str(lord))
        return ', '.join(lords)


class MonsterList:
    def __init__(self):
        self.monsters = {}

    def add(self, monster):
        self.get_for_owner_of(monster).add(monster)

    def remove(self, monster):
        self.get_for_owner_of(monster).remove(monster)

    def get_for(self, player) -> [Monster]:
        return self.monsters[player]

    def get_for_owner_of(self, monster):
        return self.monsters[monster.owner]

    def load_from_players(self, _players):
        for player in _players:
            self.monsters[player] = player.monsters


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
        self.monsters = MonsterList()
        self.towers = TowerList()
        self.lords = LordList()
        self.players = PlayerList()

    def set_players(self, players_):
        self.players = players_
        self.monsters.load_from_players(players_)

    def on_tile(self, pos):
        return TileModifier(pos, self)

    def tile_at(self, pos) -> Tile:
        assert self.is_valid_board_pos(pos), f'Invalid pos {pos}'
        return self.tiles[pos[0]][pos[1]]

    def terrain_at(self, pos):
        return self.tile_at(pos).terrain

    def monster_at(self, pos) -> Monster:
        return self.tile_at(pos).monster

    def set_terrain_to(self, pos, terrain):
        """Change terrain type of tile at pos and update tower bookkeeping"""
        if self.towers.exist_at(pos):
            self.towers.remove_at(pos)
        self.tile_at(pos).terrain = terrain
        if terrain == Terrain.TOWER:
            if not self.towers.exist_at(pos):
                self.towers.add_at(pos)
        if self.monster_at(pos):
            self.monster_at(pos).terrain = terrain

    def place_new_monster(self, monster_type, pos=(0, 0),
                          owner=None) -> Monster:
        """Places a new monster without checking/reducing mana or flagging it"""
        assert not self.monster_at(pos), (
            f'Tried to summon a '
            f'{DataTables.get_monster_stats(monster_type).name} at {pos} '
            f'but it is already occupied by a {self.monster_at(pos)}')
        if owner is None:
            owner = self.get_current_player()
        new_monster = Monster(monster_type, pos, owner, self.terrain_at(pos))
        self.monsters.add(new_monster)
        self.tile_at(new_monster.pos).monster = new_monster
        owner.monster_count += 1
        return new_monster

    def remove_monster(self, monster):
        assert monster is not None
        logging.info(f'removing {monster.name}')
        self.monsters.remove(monster)
        self.tile_at(monster.pos).monster = None
        monster.owner.monster_count -= 1

    def has_tower_at(self, pos):
        return pos in self.towers

    def tower_owner_at(self, pos):
        return self.towers.owner_at(pos)

    def set_tower_owner_at(self, pos, player_id):
        self.towers.set_owner_at_pos(pos, player_id)

    def tower_is_capturable_by(self, pos, player):
        owner = self.tower_owner_at(pos)
        if owner is None:
            return True
        return not owner.is_friendly_with(player)

    def get_enemies_adjacent_to(self, pos):
        enemies = []
        adjacent_tiles = self.get_posses_adjacent_to(pos)
        for adj_pos in adjacent_tiles:
            adj_tile = self.tile_at(adj_pos)
            if (adj_tile.monster
                    and adj_tile.monster.is_enemy_of(
                        self.get_current_player())):
                enemies.append(adj_tile.monster)
        return enemies

    def get_lord_of(self, player):
        return self.lords.get_for(player)

    def get_monsters_for(self, player):
        return self.monsters.get_for(player)

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
        x, y = pos
        return self.x_max > x >= 0 and 0 <= y < self.y_max

    def get_current_player(self):
        return self.players.get_current_player()

    def move_monster(self, monster, destination):
        """Changes the monster position on the board and flags it as moved"""
        assert not monster.moved, f'{self.print()}' \
            f'Tried to move monster {monster} but it already moved'
        self.set_monster_pos(monster, destination)
        monster.moved = True

    def set_monster_pos(self, monster, new_pos):
        """Ignores movement check, useful for spell effects, or testing"""
        self.tile_at(monster.pos).monster = None
        self.tile_at(new_pos).monster = monster
        monster.pos = new_pos
        monster.terrain = self.terrain_at(new_pos)

    def capture_terrain_at(self, pos, player):
        """Change tower count if a tower was captured, and change tile owner"""
        terrain = self.terrain_at(pos)
        if terrain == Terrain.TOWER:
            old_owner = self.tower_owner_at(pos)
            if old_owner is not None:
                old_owner.tower_count -= 1
            player.tower_count += 1
            self.set_tower_owner_at(pos, player)

    def get_enemy_lord_for_player(self, player):
        """todo messy, should find better method

        perhaps find lord closest to a certain pos
        or strongest lord?
        """
        for lord in self.lords:
            if player.is_enemy_of(lord.owner):
                return lord
        assert False, (f'Could not find enemy lord for player {player}\n' 
                       f'{self.lords}')

    def print(self):
        BoardPrinter(self).print()


class BoardPrinter:
    terrain_to_char = {
        Terrain.TOWER: 't', Terrain.DUNE: ':', Terrain.FOREST: 'f',
        Terrain.FORTRESS: '=', Terrain.GRASS: '.', Terrain.CASTLE: '@',
        Terrain.MOUNTAIN: 'm', Terrain.OCEAN: '~', Terrain.RIVER: '-',
        Terrain.ROCKY: 'n',  Terrain.SWAMP: 'o', Terrain.TUNDRA: '#',
        Terrain.VOLCANO: 'v'}

    def __init__(self, board):
        self.board = board

    def print(self):
        for y in range(self.board.y_max):
            row = []
            for x in range(self.board.x_max):
                tile = self.board.tile_at((x, y))
                if tile.monster:
                    row.append(self.monster_to_char(tile.monster))
                else:
                    row.append(self.terrain_to_char[tile.terrain])
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


class AbstractBoardBuilder:
    """Creates the board and sets up the tiles and players and such"""
    def __init__(self):
        self.board = Board()
        self.players = players.PlayerList()
        self.mapoptions: MapOptions = None
        self.layout = None
        self.x_max = None
        self.y_max = None
        self.start_posses = []

    def set_map_using_layout(self):
        """Parses the layout to set up the terrain

        How it works: the first two integers are the width and height,
        respectively. Next are a series of integer representing the terrain for
        each row. Lastly there are eight integers representing the starting
        positions for each player.
        """
        layout = self.layout
        self.x_max = layout[0]
        self.y_max = layout[1]
        self.board.x_max = self.x_max
        self.board.y_max = self.y_max
        self._fill_with_grass_tiles()
        assert len(layout) - 10 == self.x_max * self.y_max, (
                f'Error setting terrain layout, {self.x_max}:{self.y_max} but '
                f'{len(layout) - 10} tiles')
        self._set_terrain_from_layout(layout)
        for n in range(len(layout) - 8, len(layout), 2):
            self.start_posses.append((layout[n], layout[n + 1]))

    def _fill_with_grass_tiles(self):
        assert self.x_max
        assert self.y_max
        for x in range(self.x_max):
            self.board.tiles.append([])
            for y in range(self.y_max):
                self.board.tiles[x].append(Tile(Terrain.GRASS))

    def _set_terrain_from_layout(self, layout):
        n = 2
        for x in range(self.x_max):
            for y in range(self.y_max):
                self.board.set_terrain_to((x, y), layout[n])
                n += 1

    def _create_players(self):
        for id_ in range(self.mapoptions.number_of_players):
            self._create_player_from_mapoptions(id_)
        self.board.set_players(self.players)

    def _set_default_mapoption_values_if_not_specified(self):
        """Sets default options for every option not specified by mapoptions

        By default, 4 players, first is human, rest is computer,
        DAIMYOU-WIZARD-SORCERER-DARKLORD, no teams and 50 mp recovery per turn
        """
        if not self.mapoptions:
            self.mapoptions = MapOptions()
        if not self.mapoptions.mapname:
            self.mapoptions.mapname = 'test'
        if not self.mapoptions.number_of_players:
            self._set_default_player_count()
        if not self.mapoptions.lord_types:
            self._set_default_lord_type()
        if not self.mapoptions.ai_types:
            self._set_default_ai_type()
        if not self.mapoptions.teams:
            self._set_default_teams()
        if not self.mapoptions.starting_mp:
            self._set_default_mp()

    def _set_default_player_count(self):
        self.mapoptions.number_of_players = 4

    def _set_default_lord_type(self):
        for n in range(self.mapoptions.number_of_players):
            self.mapoptions.lord_types[n] = Monster.Type.DAIMYOU + n

    def _set_default_ai_type(self):
        for n in range(self.mapoptions.number_of_players):
            if n == 0:
                self.mapoptions.ai_types[n] = AiType.human
            else:
                self.mapoptions.ai_types[n] = AiType.default

    def _set_default_teams(self):
        for n in range(self.mapoptions.number_of_players):
            self.mapoptions.teams[n] = 0

    def _set_default_mp(self):
        for n in range(self.mapoptions.number_of_players):
            self.mapoptions.starting_mp[n] = 50

    def _create_player_from_mapoptions(self, id_):
        new_player = self.players.add_player(
            self.mapoptions.lord_types[id_],
            self.mapoptions.ai_types[id_],
            self.mapoptions.starting_mp[id_])
        new_player.team = self.mapoptions.teams[id_]


class BoardBuilder(AbstractBoardBuilder):
    def load_default_map(self) -> Board:
        mapoptions = MapOptions()
        mapoptions.mapname = 'test'
        self.load_map(mapoptions)
        return self.board

    def load_map(self, mapoptions) -> Board:
        self.mapoptions = mapoptions
        self._set_default_mapoption_values_if_not_specified()
        self._create_players()
        if self.mapoptions.mapname == 'test':
            test = True
            self.mapoptions.mapname = 'test.map'
        else:
            test = False
        self._get_layout_from_map_file()
        self.set_map_using_layout()
        self._add_lords()
        if test:
            self._generate_towers_around_lords()
        return self.board

    def _get_layout_from_map_file(self):
        assert self.mapoptions.mapname, 'No mapname set'
        with open(f'{ROOT}/src/data/maps/{self.mapoptions.mapname}', 'r') as fd:
            content = fd.read()
        self._get_layout_from_content(content)

    def _get_layout_from_content(self, content):
        layout_strings = content.split(', ')
        layout = []
        for layout_string in layout_strings:
            layout.append(int(layout_string))
        self.layout = layout

    def _add_lords(self):
        for n in range(len(self.players)):
            player = self.players.get_player_by_id(n)
            pos = self.start_posses[n]
            lord = self.board.place_new_monster(player.lord_type, pos, player)
            self.board.lords.add(lord)

    def _generate_towers_around_lords(self):
        for lord in self.board.lords:
            self.board.set_terrain_to(lord.pos, Terrain.CASTLE)
            posses = []
            posses += self.board.get_posses_adjacent_to(lord.pos)
            for pos in posses:
                terrain = self.board.terrain_at(pos)
                if terrain == Terrain.GRASS:
                    self.board.on_tile(pos).set_terrain_to(Terrain.TOWER)
                    self.board.capture_terrain_at(pos, lord.owner)


class BoardTextBuilder(AbstractBoardBuilder):
    def __init__(self):
        super().__init__()
        self.monsters_to_add = None
        self.legend = None

    def make_board_from_text(self, text, legend) -> Board:
        self.legend = legend
        self._parse_text_to_layout(text)
        self._make_board_from_layout()
        self._set_default_mapoption_values_if_not_specified()
        self._create_players()
        self._add_monsters(self.monsters_to_add)
        return self.board

    def _parse_text_to_layout(self, input_layout):
        chars = re.sub('[\\s]+', ' ', input_layout).split(' ')
        self.layout = []
        self.monsters_to_add = []
        for char in chars:
            self._process_char(char)
        # start pos (unused, but needed)
        # might want to use this later or in a different method
        for _ in range(8):
            self.layout.append(0)

    def _process_char(self, char):
        if char.isnumeric():
            self.layout.append(int(char))
        elif char == '':
            return
        elif char not in self.legend:
            raise AttributeError(f'Char "{char}" missing from legend')
        else:
            self._convert_char_to_info(char)

    def _convert_char_to_info(self, char):
        data = self.legend[char]
        if self._is_monster_data(data):
            data += (len(self.layout) - 2,)
            self.monsters_to_add.append(data)
            self.layout.append(Terrain.GRASS)
        else:
            self.layout.append(data)

    def _is_monster_data(self, data):
        return isinstance(data, tuple)

    def _make_board_from_layout(self):
        self.set_map_using_layout()

    def _add_monsters(self, monsters):
        assert self.players is not None
        for monster_data in monsters:
            monster_type, owner_id, index = monster_data
            x = index % self.x_max
            y = floor(index / self.x_max)
            owner = self.players.get_player_by_id(owner_id)
            self.board.place_new_monster(monster_type, (x, y), owner)

    # override
    def _set_terrain_from_layout(self, layout):
        for x in range(self.x_max):
            for y in range(self.y_max):
                self.board.set_terrain_to(
                    (x, y), layout[2 + x + y * self.x_max])


class RandomBoardBuilder(AbstractBoardBuilder):
    def load_map(self, x_max, y_max, mapoptions) -> Board:
        self.mapoptions = mapoptions
        self.x_max = x_max
        self.y_max = y_max
        self.board.x_max = self.x_max
        self.board.y_max = self.y_max
        self._fill_with_grass_tiles()
        self._randomize_terrain()
        self._set_default_mapoption_values_if_not_specified()
        self._create_players()
        return self.board

    def _randomize_terrain(self):
        pos = (self._get_random_x(), self._get_random_y())
        for terrain in range(13):
            for i in range(round(self.x_max * self.y_max * 0.05)):
                while self.board.terrain_at(pos) != Terrain.GRASS:
                    pos = (self._get_random_x(), self._get_random_y())
                self.board.on_tile(pos).set_terrain_to(terrain)

    def _get_random_y(self):
        return random.randint(0, self.y_max - 1)

    def _get_random_x(self):
        return random.randint(0, self.x_max - 1)


class MapOptions:
    def __init__(self):
        self.players: PlayerList = PlayerList()
        self.number_of_players = None
        self.mapname = None
        self.lord_types = {}
        self.ai_types = {}
        self.teams = {}
        self.starting_mp = {}

    def set_number_of_players(self, number):
        self.number_of_players = number

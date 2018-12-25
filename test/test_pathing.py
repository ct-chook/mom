import re
import pytest

from src.components.board.board import Board, MapLoader
from src.components.board.monster import Monster
from src.components.board.pathing import PathGenerator, PathFinder
from src.components.board.pathing_components import AStarMatrixFactory, \
    TerrainTypeSearchMatrixFactory
from src.components.board.players import PlayerList
from src.helper.Misc.constants import MonsterType, Terrain, UNEXPLORED, \
    IMPASSIBLE
from src.controller.board_controller import BoardModel
from src.components.board.pathing import PathMatrixFactory

blocked_x = 1
blocked_y = 6

roman_x = 1
roman_y = 19

octopus_x = 12
octopus_y = 7

sirene_x = 12
sirene_y = 8

phoenix_x = 1
phoenix_y = 18

roman_pos = (roman_x, roman_y)
phoenix_pos = (phoenix_x, phoenix_y)
octopus_pos = (octopus_x, octopus_y)
sirene_pos = (sirene_x, sirene_y)


class Layouts:
    zigzag = None
    cross = None

    @staticmethod
    def get_zigzag():
        if not Layouts.zigzag:
            legend = {'o': Terrain.GRASS, 'X': Terrain.VOLCANO}
            layout = """18 10
                      o  o  o  o  o  o  o  o  o  o  X  o  o  o  o  o  o  o 
                        o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                      o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  X  o  o 
                        o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                      o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                        o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                      o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                        o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                      o  o  o  o  o  o  o  o  o  o  X  o  o  o  X  o  o  o 
                        o  o  o  o  o  o  o  o  o  o  o  o  o  o  X  o  o  o"""
            Layouts.zigzag = Layouts._parse_layout(layout, legend)
        return Layouts.zigzag

    @staticmethod
    def get_cross():
        if not Layouts.cross:
            legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                      '=': Terrain.RIVER}
            #          1   2   3   4   5   6   7   8   9  10  11  12  13  14
            layout = """14 12
                      #  .   .   .   .   .   .   .   .   .   .   .   .   . 
                        #   .   .   .   .   .   .   .   #   .   .   =   =   . 
                      .   #   .   .   .   #   .   .   #   .   .   =   =   . 
                        .   #   .   .   .   #   .   #   .   .   =   =   .   . 
                      .   .   #   .   .   .   #   #   .   .   .   =   =   . 
                        .   .   #   .   .   .   #   .   .   .   .   =   =   = 
                      .   .   .   #   .   .   #   #   .   .   .   =   =   . 
                        .   .   .   .   .   #   .   .   .   .   .   =   =   . 
                      .   .   .   .   .   #   .   .   .   .   .   =   =   . 
                        .   .   .   .   #   .   .   .   .   .   =   =   .   . 
                      .   .   .   .   .   .   .   .   .   .   =   =   .   . 
                        .   .   .   .   .   .   .   .   .   .   .   .   .   ."""
            Layouts.cross = Layouts._parse_layout(layout, legend)
        return Layouts.cross

    @staticmethod
    def _parse_layout(input_layout, legend):
        chars = re.sub('[\\s]+', ' ', input_layout).split(' ')
        new_list = []
        for char in chars:
            if char.isnumeric():
                new_list.append(int(char))
            elif char == '':
                pass
            elif char not in legend:
                raise AttributeError(f'Char "{char}" missing from legend')
            else:
                new_list.append(legend[char])
        # start pos (unused, but needed)
        for _ in range(8):
            new_list.append(0)
        return new_list


# class TestLayouts:
#     def test_parse_layout(self):
#         legend = {'#': 1, '.': 0, 'x': 2, 'o': 3}
#         input_layout = """
#                 4 4
#                 # . o #
#                 . . # #
#                 . . . #
#                 # # . x"""
#         result = self.parse_layout(input_layout, legend)
#         assert [4, 4, 1, 0, 3, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 2, 0, 0, 0,
#                 0, 0, 0, 0, 0] == result


class TestCase:
    # noinspection PyAttributeOutsideInit
    def make_board_from_layout(self, layout, start_pos):
        self.board = Board()
        maploader = MapLoader(self.board)
        maploader.set_map_using_layout(layout, 1)
        players = PlayerList()
        players.add_player(0, 0, 0)
        self.board.set_players(players)
        self.start_pos = start_pos
        self.board.place_new_monster(MonsterType.ROMAN, self.start_pos)
        self.matrix_generator = AStarMatrixFactory(self.board)
        self.path_generator = PathGenerator(self.board)

    # noinspection PyAttributeOutsideInit
    def get_a_star_matrix(self, destination):
        self.matrix = self.matrix_generator.generate_path_matrix(
            self.start_pos, destination)
        assert self.matrix

    def get_path_to(self, destination):
        self.path_generator.set_path_matrix(self.matrix)
        path = self.path_generator.get_path_to(destination)
        return path

    def check(self, value, pos):
        assert self.matrix.get_distance_value_at(pos) == value, (
            f'\n{self.matrix.print_dist_values()}')


class TestAStarZigZag(TestCase):
    @pytest.fixture
    def before(self):
        self.make_board_from_layout(Layouts.get_zigzag(), (4, 0))

    def test_very_short(self, before):
        destination = (4, 1)
        self.get_a_star_matrix(destination)
        self.check(0, (4, 0))
        self.check(1, (4, 1))
        self.check(1, (5, 0))
        self.check(UNEXPLORED, (5, 1))
        self.check(UNEXPLORED, (4, 2))
        self.check(UNEXPLORED, (6, 1))
        path = self.get_path_to(destination)
        assert len(path) == 2

    def test_short(self, before):
        destination = (4, 9)
        self.get_a_star_matrix(destination)
        path = self.get_path_to(destination)
        assert len(path) == 10

    def test_left_of_east_mountain(self, before):
        destination = (13, 9)
        self.get_a_star_matrix(destination)
        self.check(14, (13, 9))
        path = self.get_path_to(destination)
        assert len(path) == 15

    def test_pass_mountain(self, before):
        destination = (11, 0)
        self.get_a_star_matrix(destination)
        self.check(5, (9, 0))
        self.check(IMPASSIBLE, (10, 0))
        self.check(20, (11, 0))
        path = self.get_path_to(destination)
        assert len(path) == 21

    def test_rightmost_corner(self, before):
        destination = (17, 9)
        self.get_a_star_matrix(destination)
        self.check(30, (17, 9))
        path = self.get_path_to(destination)
        assert len(path) == 31


class TestAStarCross(TestCase):
    @pytest.fixture
    def before(self):
        self.make_board_from_layout(Layouts.get_cross(), (6, 3))

    def test_cross_goto_opposite(self, before):
        destination = (6, 7)
        self.get_a_star_matrix(destination)
        path = self.get_path_to(destination)
        assert len(path) == 13

    def test_funnel(self, before):
        destination = (0, 3)
        self.get_a_star_matrix(destination)
        path = self.get_path_to(destination)
        assert len(path) == 15

    def test_pass_ocean(self, before):
        destination = (13, 11)
        self.get_a_star_matrix(destination)
        path = self.get_path_to(destination)
        assert len(path) == 20


class TestMatrix:
    model = None
    board = None
    generator = None
    matrix = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board = self.model.board
        self.generator = PathMatrixFactory(self.board)

    def generate_matrix_at(self, pos):
        self.matrix = self.generator.generate_path_matrix(pos)

    def check(self, value, pos):
        assert value == self.matrix.get_distance_value_at(pos)

    def test_roman(self, before):
        self.generate_matrix_at(roman_pos)
        assert self.generator
        self.check(0, roman_pos)
        left_grass = (roman_x - 1, roman_y)
        mountain = (roman_x + 1, roman_y)
        chim = (roman_x, roman_y - 2)
        left_of_chim = (roman_x - 1, roman_y - 2)
        past_chim = (roman_x - 1, roman_y - 3)
        self.check(1, left_grass)
        self.check(IMPASSIBLE, mountain)
        self.check(UNEXPLORED, chim)
        self.check(3, left_of_chim)
        self.check(UNEXPLORED, past_chim)

    def test_phoenix(self, before):
        # move darklord out of the way
        self.board.set_monster_pos(self.board.lords[3], (0, 0))
        self.generate_matrix_at(phoenix_pos)
        self.check(0, phoenix_pos)
        self.check(1, (phoenix_x + 1, phoenix_y))
        self.check(8, (phoenix_x, phoenix_y - 2))

    def test_octopus(self, before):
        octopus_northeast = (octopus_x + 1, octopus_y - 1)
        ocean_tip = (octopus_x - 1, octopus_y - 5)
        west_of_ocean_tip = (octopus_x - 2, octopus_y - 4)
        coast = (octopus_x, octopus_y + 1)
        north_of_ocean = (octopus_x - 1, octopus_y - 6)
        self.generate_matrix_at(octopus_pos)
        self.check(0, octopus_pos)
        self.check(1, octopus_northeast)
        self.check(6, ocean_tip)
        self.check(4, coast)
        self.check(UNEXPLORED, west_of_ocean_tip)
        self.check(UNEXPLORED, north_of_ocean)

    def test_sirene(self, before):
        self.generate_matrix_at(sirene_pos)
        # start
        assert 0 == self.matrix.get_distance_value_at(sirene_pos)
        # northeast
        assert 5 == self.matrix.get_distance_value_at(
            (sirene_x + 1, sirene_y - 1))
        # ocean tip
        assert 6 == self.matrix.get_distance_value_at(
            (sirene_x - 1, sirene_y - 6))
        # land
        assert 4 == self.matrix.get_distance_value_at(
            (sirene_x, sirene_y + 1))


class TestPaths:
    model = None
    board = None
    generator = None
    path = None
    path_generator = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board: Board = self.model.board
        self.generator = PathMatrixFactory(self.board)
        self.path_generator = PathGenerator(self.board)

    def get_path_between(self, start, end):
        path_matrix = self.generator.generate_path_matrix(start)
        self.path_generator.set_path_matrix(path_matrix)
        self.path = self.path_generator.get_path_to(end)

    def test_roman_path(self, before):
        self.get_path_between(roman_pos, (roman_x - 1, roman_y - 2))
        assert self.path
        assert 4 == len(self.path), f'path wrong: {self.path}'
        assert roman_pos == self.path[0]
        assert (roman_x - 1, roman_y) == self.path[1]
        assert (roman_x - 1, roman_y - 2) == self.path[-1]

    def test_octopus_ocean_path(self, before):
        end_pos = (octopus_x - 1, octopus_y - 5)
        self.get_path_between(octopus_pos, end_pos)
        assert self.path
        assert 7 == len(self.path)
        # start
        start_pos = (octopus_x - 1, octopus_y - 2)
        assert start_pos == self.path[3]
        # end
        assert end_pos == self.path[6]

    def test_octopus_land_path(self, before):
        self.get_path_between(octopus_pos, (octopus_x, octopus_y - 3))
        assert self.path
        assert 4 == len(self.path)
        # FirstPathTile
        assert (octopus_x + 1, octopus_y - 1) == self.path[1]
        # LastPathTile
        assert (octopus_x, octopus_y - 3) == self.path[3]

    def test_sirene(self, before):
        self.get_path_between(sirene_pos, (sirene_x - 1, sirene_y - 6))
        assert self.path
        assert self.path and len(self.path) == 7
        # first
        assert self.path and self.path[1] == (sirene_x - 1, sirene_y - 1)
        # last
        assert self.path and self.path[6] == (sirene_x - 1, sirene_y - 6)

    def test_no_path_was_made(self, before):
        with pytest.raises(AssertionError):
            self.get_path_between(roman_pos, (roman_x, roman_y - 6))


class TestAStar:
    model = None
    board = None
    generator = None
    path = None
    path_generator = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board = self.model.board
        self.generator = AStarMatrixFactory(self.board)
        self.path_generator = PathGenerator(self.board)

    def get_path_between(self, start, end):
        path_matrix = self.generator.generate_path_matrix(start, end)
        assert path_matrix, 'Could not generate path matrix'
        self.path_generator.set_path_matrix(path_matrix)
        self.path = self.path_generator.get_path_to(end)

    def test_short_path(self, before):
        start_pos = (0, 0)
        end_pos = (2, 0)
        self.board.place_new_monster(MonsterType.ROMAN, start_pos, 0)
        self.assert_path(end_pos, start_pos)

    def test_long_path(self, before):
        start_pos = (0, 0)
        end_pos = (10, 0)
        self.board.place_new_monster(MonsterType.ROMAN, start_pos, 0)
        self.assert_path(end_pos, start_pos)

    def assert_path(self, end_pos, start_pos):
        self.get_path_between(start_pos, end_pos)
        expected = []
        for n in range(end_pos[0] + 1):
            expected.append((n, 0))
        assert expected == self.path


class TestTerrainSearch:
    model = None
    board = None
    generator = None
    path = None
    path_generator = None

    @pytest.fixture
    def before(self):
        self.model = BoardModel()
        self.board = self.model.board
        self.pathfinder = PathFinder(self.board)
        self.path_generator = PathGenerator(self.board)

    def test_short_path(self, before):
        start_pos = (0, 0)
        end_pos = (2, 0)
        self.board.place_new_monster(MonsterType.ROMAN, start_pos, 0)
        self.board.on_tile(end_pos).set_terrain_to(Terrain.TOWER)
        self.assert_path(end_pos, start_pos)

    def test_long_path(self, before):
        start_pos = (0, 0)
        end_pos = (10, 0)
        self.board.place_new_monster(MonsterType.ROMAN, start_pos, 0)
        # this tile contains a tower by default
        self.board.on_tile((7, 4)).set_terrain_to(Terrain.GRASS)
        self.board.on_tile(end_pos).set_terrain_to(Terrain.TOWER)
        self.assert_path(end_pos, start_pos)

    def assert_path(self, end_pos, start_pos):
        self.get_path_to_tower(start_pos)
        expected = []
        for n in range(end_pos[0] + 1):
            expected.append((n, 0))
        assert expected == self.path

    def get_path_to_tower(self, start):
        self.path = self.pathfinder.get_path_to_terraintype(
            start, Terrain.TOWER)
        assert self.path


class TestValidPath(TestCase):
    @pytest.fixture
    def before(self):
        self.make_board_from_layout(Layouts.get_zigzag(), (0, 0))

    def tower_found_on_first_turn(self, before):
        self.start_pos = (0, 0)
        destination = (5, 0)
        self.board.on_tile(destination).set_terrain_to(Terrain.TOWER)
        # troll can move only 4 tiles per turn. it must move 2 tiles on the
        # second turn to move to 5,0, so total move cost will be 6
        matrix_generator = TerrainTypeSearchMatrixFactory(self.board)
        matrix = matrix_generator.generate_path_matrix(
            self.start_pos, Terrain.TOWER)
        assert matrix.get_distance_value_at(destination) == 5

    def test_tower_behind_own_monster(self, before):
        self.start_pos = (0, 0)
        self.board.monster_at(self.start_pos).set_monster_type(
            Monster.Type.TROLL)
        self.board.place_new_monster(Monster.Type.ROMAN, (4, 0))
        # there's a monster at (4, 0)
        # lets see if we can move past it
        destination = (5, 0)
        self.board.on_tile(destination).set_terrain_to(Terrain.TOWER)
        # troll can move only 4 tiles per turn. it must move 2 tiles on the
        # second turn to move to 5,0, so total move cost will be 6
        matrix_generator = TerrainTypeSearchMatrixFactory(self.board)
        matrix = matrix_generator.generate_path_matrix(
            self.start_pos, Terrain.TOWER)
        matrix.print_dist_values()
        assert matrix.get_distance_value_at(destination) == 6

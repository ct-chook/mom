import pytest

from src.components.board.board import BoardTextBuilder
from src.components.board.monster import Monster
from src.components.board.pathing import PathFinder, PathFactory
from src.components.board.pathing import PathMatrixFactory
from src.components.board.pathing_components import AStarMatrixFactory
from src.helper.Misc.constants import MonsterType, Terrain, UNEXPLORED, \
    IMPASSIBLE

Type = Monster.Type


class Boards:
    @staticmethod
    def get_zigzag():
        legend = {'.': Terrain.GRASS, 'X': Terrain.VOLCANO}
        layout = """18 10
                  .  .  .  .  .  .  .  .  .  .  X  .  .  .  .  .  .  . 
                    .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                  .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  X  .  . 
                    .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                  .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                    .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                  .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                    .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                  .  .  .  .  .  .  .  .  .  .  X  .  .  .  X  .  .  . 
                    .  .  .  .  .  .  .  .  .  .  .  .  .  .  X  .  .  ."""
        builder = BoardTextBuilder()
        return builder.make_board_from_text(layout, legend)

    @staticmethod
    def get_cross():
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
        builder = BoardTextBuilder()
        return builder.make_board_from_text(layout, legend)

    @staticmethod
    def get_gauntlet():
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO}
        #          1   2   3   4   5   6   7   8   9  10  11  12  13  14
        layout = """14 5
                  #   #   #   #   #   #   #   #   #   #   #   #   #   #        
                    #   .   .   .   .   .   .   .   .   .   .   .   .   #   
                  #   #   #   #   #   #   #   #   #   #   #   #   #   .      
                    #   .   .   .   .   .   .   .   .   .   .   .   .   # 
                  #   #   #   #   #   #   #   #   #   #   #   #   #   #     
                  """
        builder = BoardTextBuilder()
        return builder.make_board_from_text(layout, legend)

    @staticmethod
    def get_square():
        legend = {'.': Terrain.GRASS}
        #          1   2   3   4   5   6   7   8   9  10  11  12  13  14
        layout = """9 9
                      .   .   .   .   .   .   .   .   .
                        .   .   .   .   .   .   .   .   .
                      .   .   .   .   .   .   .   .   .
                        .   .   .   .   .   .   .   .   .
                      .   .   .   .   .   .   .   .   .
                        .   .   .   .   .   .   .   .   .
                      .   .   .   .   .   .   .   .   .
                        .   .   .   .   .   .   .   .   .
                      .   .   .   .   .   .   .   .   ."""
        builder = BoardTextBuilder()
        return builder.make_board_from_text(layout, legend)


class TestCase:
    # noinspection PyAttributeOutsideInit
    def make_board_from_layout(self, function, start_pos,
                               monster_type=MonsterType.ROMAN):
        self.board = function()
        self.start_pos = start_pos
        self.board.place_new_monster(monster_type, self.start_pos)
        self.matrix_generator = AStarMatrixFactory(self.board)
        self.path_generator = PathFinder(self.board)

    # noinspection PyAttributeOutsideInit
    def make_board_from_layout2(self, layout, legend, start_pos):
        builder = BoardTextBuilder()
        self.board = builder.make_board_from_text(layout, legend)
        self.start_pos = start_pos
        assert self.board.monster_at(start_pos), 'No monster at start pos'

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
            f'\n{self.matrix.get_printable_dist_values()}')

    def compare(self, result, expected):
        assert len(result) == len(expected)
        for i in range(len(expected)):
            assert result[i] == expected[i], f'Mismatch at {i}'


class TestAStarZigZag(TestCase):
    @pytest.fixture
    def before(self):
        self.make_board_from_layout(Boards.get_zigzag, (4, 0))

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
        self.make_board_from_layout(Boards.get_cross, (6, 3))

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


class TestMatrix(TestCase):
    def test_matrix_with_enemy(self):
        map_ = """3 6
        .   .   #
          .   .   #
        .   .   #
          .   C   #
        .   .   #
          .   R   #"""
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  'C': (Type.CHIMERA, 1), 'R': (Type.ROMAN, 0)}

        roman_pos = (1, 5)
        roman_x, roman_y = roman_pos
        left_grass = (roman_x - 1, roman_y)
        volcano = (roman_x + 1, roman_y)
        chim = (roman_x, roman_y - 2)
        left_of_chim = (roman_x - 1, roman_y - 2)
        past_chim = (roman_x - 1, roman_y - 3)
        self.make_board_from_layout2(map_, legend, roman_pos)
        self.generate_matrix_at(roman_pos)

        self.check(0, roman_pos)
        self.check(1, left_grass)
        self.check(IMPASSIBLE, volcano)
        self.check(UNEXPLORED, chim)
        self.check(3, left_of_chim)
        self.check(UNEXPLORED, past_chim)

        self.get_path_between(roman_pos, left_of_chim)
        assert len(self.path) == 4
        assert self.path[1] == (0, 5)
        with pytest.raises(AssertionError):
            self.get_path_between(roman_pos, past_chim)

    def test_matrix_with_enemy_2(self):
        map_ = """3 6
        .   .   .
          .   .   .
        .   .   R
          C   .   .
        .   .   .
          .   .   ."""
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  'C': (Type.CHIMERA, 1), 'R': (Type.ROMAN, 0)}

        roman_pos = (2, 2)
        north_of_chim = (0, 1)
        south_of_roman = (2, 4)
        self.make_board_from_layout2(map_, legend, roman_pos)
        self.generate_matrix_at(roman_pos)

        self.check(0, roman_pos)
        self.check(2, north_of_chim)
        self.check(2, south_of_roman)

        self.get_path_between(roman_pos, north_of_chim)
        assert len(self.path) == 3
        assert self.path[1] == (1, 1)

        self.get_path_between(roman_pos, south_of_roman)
        assert len(self.path) == 3
        assert self.path[1] == (2, 3)

    def test_start_next_to_enemy(self):
        map_ = """3 4
                .   .   #
                  .   .   #
                .   .   #
                  R   C   #"""
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  'C': (Type.CHIMERA, 1), 'R': (Type.ROMAN, 0)}

        roman_pos = (0, 3)
        roman_x, roman_y = roman_pos
        north_of_chim = (roman_x + 1, roman_y - 1)
        two_north_of_chim = (roman_x + 1, roman_y - 2)
        self.make_board_from_layout2(map_, legend, roman_pos)
        self.generate_matrix_at(roman_pos)

        self.check(0, roman_pos)
        self.check(1, north_of_chim)
        self.check(3, two_north_of_chim)

        self.get_path_between(roman_pos, north_of_chim)
        assert len(self.path) == 2

        self.get_path_between(roman_pos, two_north_of_chim)
        assert len(self.path) == 4
        assert self.path[1] == (roman_x, roman_y - 1)

    def test_matrix_with_friendly(self):
        map_ = """3 6
                .   .   #
                  .   .   #
                .   .   #
                  .   .   #
                .   C   #
                  .   C   # """
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  'C': (Type.CHIMERA, 0), 'R': (Type.ROMAN, 0)}

        chim_pos = (1, 5)
        chim_x, chim_y = chim_pos
        north_of_chim = (chim_x, chim_y - 2)
        north = (chim_x, chim_y - 5)
        self.make_board_from_layout2(map_, legend, chim_pos)
        self.generate_matrix_at(chim_pos)

        self.check(0, chim_pos)
        self.check(2, north_of_chim)
        self.check(5, north)

        self.get_path_between(chim_pos, north_of_chim)
        assert len(self.path) == 3
        expected = ((chim_x, chim_y), (chim_x, chim_y - 1),
                    (chim_x, chim_y - 2))
        self.compare(self.path, expected)

        self.get_path_between(chim_pos, north)
        assert len(self.path) == 6
        assert self.path[1] == (chim_x, chim_y - 1)

    def test_terrain_for_octopus(self):
        map_ = """3 8
                ~   ~   ~
                  O   .   ~
                ~   ~   ~
                  ~   ~   ~
                ~   ~   .
                  ~   .   .
                ~   .   .
                  .   .   ."""
        legend = {'.': Terrain.GRASS, '~': Terrain.OCEAN,
                  'O': (Type.OCTOPUS, 0)}

        octopus_pos = (0, 1)
        octopus_x, octopus_y = octopus_pos
        island = (octopus_x + 1, octopus_y)
        east_of_island = (octopus_x + 2, octopus_y)
        land = (octopus_x + 1, octopus_y + 4)
        south_of_octopus = (octopus_x, octopus_y + 4)
        self.make_board_from_layout2(map_, legend, octopus_pos)
        self.generate_matrix_at(octopus_pos)

        self.check(0, octopus_pos)
        self.check(4, island)
        self.check(3, east_of_island)
        self.check(4, south_of_octopus)
        self.check(UNEXPLORED, land)

        self.get_path_between(octopus_pos, east_of_island)
        assert len(self.path) == 4

        self.get_path_between(octopus_pos, south_of_octopus)
        assert len(self.path) == 5

    def check(self, value, pos):
        assert self.matrix.get_distance_value_at(pos) == value, (
            f'{self.matrix.get_printable_dist_values()}')

    def generate_matrix_at(self, pos):
        self.generator = PathMatrixFactory(self.board)
        self.matrix = self.generator.generate_path_matrix(pos)

    def get_path_between(self, start, end):
        matrix_factory = PathMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(start)
        path_factory = PathFinder(self.board)
        path_factory.set_path_matrix(path_matrix)
        self.path = path_factory.get_path_to(end)


class TestTowerSearch(TestCase):
    @pytest.fixture
    def before(self):
        pass

    def test_find_tower(self, before):
        map_ = """3 6
                .   .   .
                  .   #   t
                .   #   .
                  .   .   #
                .   #   #
                  .   C   #"""
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  't': Terrain.TOWER, 'C': (Type.CHIMERA, 0)}

        chim_pos = (1, 5)
        tower_pos = (2, 1)
        self.make_board_from_layout2(map_, legend, chim_pos)
        self.get_path_to_tower(chim_pos)
        expected = (chim_pos, (0, 5), (0, 4), (0, 3), (1, 3), (2, 2), tower_pos)
        self.compare(self.path, expected)
        assert self.path.furthest_reachable == (2, 2)

    def test_find_closest_tower(self, before):
        map_ = """6 10
                .   .   .   .   .   t
                  .   #   .   .   .   .
                .   #   .   .   .   .
                  .   #   .   .   .   .
                .   #   .   .   .   .
                  .   #   .   .   .   .
                .   #   .   .   .   .
                  t   #   .   .   .   .
                #   #   .   .   .   .
                  .   C   .   .   .   ."""
        legend = {'.': Terrain.GRASS, '#': Terrain.VOLCANO,
                  't': Terrain.TOWER, 'C': (Type.CHIMERA, 0)}

        chim_pos = (1, 9)
        closest_tower_pos = (5, 0)
        self.make_board_from_layout2(map_, legend, chim_pos)
        self.get_path_to_tower(chim_pos)
        assert self.path[-1] == closest_tower_pos
        assert self.path.furthest_reachable[1] == 4

    def get_path_to_tower(self, start):
        self.pathfactory = PathFactory(self.board)
        self.path = self.pathfactory.get_path_to_tower(start)
        assert self.path, 'Could not generate path'

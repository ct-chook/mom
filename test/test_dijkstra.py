import random

import pytest

from src.components.board.board import BoardBuilder, RandomBoardBuilder, \
    MapOptions
from src.components.board.dijkstra import DijkstraGraph, DijkstraPrinter
from src.components.board.monster import Monster
from src.components.board.pathing import PathMatrixFactory
from src.components.board.pathing_components import AStarMatrixFactory
from src.helper.Misc.constants import IMPASSIBLE, UNEXPLORED


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        factory = RandomBoardBuilder()
        mapoptions = MapOptions()
        mapoptions.mapname = 'random'
        self.board = factory.load_map(20, 20, mapoptions)
        self.terrain_type = None
        self.generator = None

    def _place_monster(self, start):
        monster_type = random.randint(0, Monster.Type.TAITAN)
        player_1 = self.board.get_current_player()
        monster = self.board.place_new_monster(monster_type, start, player_1)
        return monster


class TestDijkstraWithPathingComparison(TestCase):
    def test_single_turn(self, before):
        self.generator = PathMatrixFactory(self.board)
        for _ in range(10):
            self.do_single_turn()

    def do_single_turn(self):
        """Make path matrix of board, compare dist values with dijkstra"""
        start = (9, 9)
        monster = self._place_monster(start)
        matrix = self.generator.generate_path_matrix(start)
        graph = DijkstraGraph(self.board, monster)
        dist, prev = graph.dijkstra(start)
        self.compare_dist_values(dist, matrix, monster)
        self.board.remove_monster(monster)

    def test_a_star(self, before):
        self.a_star_generator = AStarMatrixFactory(self.board)
        for _ in range(10):
            self.do_a_star()

    def do_a_star(self):
        start = (0, 0)
        end = (random.randint(0, self.board.x_max - 1),
               random.randint(0, self.board.y_max - 1))
        monster = self._place_monster(start)
        matrix = self.a_star_generator.generate_path_matrix(start, end)
        graph = DijkstraGraph(self.board, monster)
        dist, prev = graph.dijkstra(start)
        self.compare_dist_values(dist, matrix, monster, True)
        # only compare end
        # matrix_val = matrix.get_distance_value_at(end)
        # dijkstra_val = dist[end]
        # if matrix_val >= 99:
        #     assert dijkstra_val == DijkstraGraph.INFINITY, (
        #         f'{self._get_error(matrix, end, dist)}')
        # else:
        #     assert matrix_val == dijkstra_val, \
        #         f'{self._get_error(matrix, end, dist)}'
        self.board.remove_monster(monster)

    def compare_dist_values(self, dist, matrix, monster, is_a_star=False):
        for pos in dist:
            if is_a_star and pos not in matrix.explored_tiles:
                continue
            matrix_val = matrix.get_distance_value_at(pos)
            dijkstra_val = dist[pos]
            if matrix_val == UNEXPLORED:
                assert dijkstra_val > monster.stats.move_points, (
                    f'{self._get_error(matrix, pos, dist)}')
            elif matrix_val == IMPASSIBLE:
                assert dijkstra_val == DijkstraGraph.INFINITY, (
                    f'{self._get_error(matrix, pos, dist)}')
            else:
                assert matrix_val == dijkstra_val, (
                    f'{self._get_error(matrix, pos, dist)}')

    def _get_error(self, matrix, pos, dist):
        dijkstra_printer = DijkstraPrinter(dist)
        return (f'wrong val at pos {pos}\n'
                'Distance:\n'
                f'{matrix.get_printable_dist_values()}\n'
                'Terrain cost:\n'
                f'{matrix.get_printable_terrain_cost_values()}\n'
                'Heuristic:\n'
                f'{matrix.get_printable_heuristic_values()}\n'
                'Dijkstra:\n'
                f'{dijkstra_printer.get_printable_values()}')


class TestDijkstraAlgorithm(TestCase):
    def skip_test_if_dijkstra_algorithm_is_correct(self):
        """Test for the test above. Uses a very naive and slow algorithm

        only run this test if algoritm for dijkstra changes
        """
        for _ in range(10):
            self.run_algorithm()

    def run_algorithm(self):
        factory = BoardBuilder()
        mapoptions = MapOptions()
        self.board = factory.load_random_map(4, 4, mapoptions)
        self.terrain_type = None
        self.generator = None
        start = (0, 0)
        end = (3, 3)
        monster = self._place_monster(start)
        graph = DijkstraGraph(self.board, monster)
        dist, prev = graph.dijkstra(start)
        score = self.naive(graph, start, end)
        assert dist[end] == score, f'{self._get_error(end, dist)}'
        self.board.remove_monster(monster)

    def naive(self, graph, start, end):
        # recursively loop till end is found, save lowest score
        lowest_score = DijkstraGraph.INFINITY
        score = 0
        depth = 0
        edges_visited = {}
        lowest_score = self.get_score(
            graph, start, end, score, lowest_score, depth, edges_visited)
        return lowest_score

    def get_score(self, graph, node, end, score, lowest_score, depth,
                  edges_visited):
        if node in edges_visited or depth >= len(graph.edges):
            return lowest_score
        if node == end:
            if score < lowest_score:
                lowest_score = score
        elif node in graph.edges:
            edges = graph.edges[node]
            for key in edges:
                edge = edges[key]
                next_ = edge.to_node
                new_score = score + edge.length
                edges_visited = edges_visited.copy()
                edges_visited[node] = True
                lowest_score = self.get_score(
                    graph, next_, end, new_score, lowest_score, depth + 1,
                    edges_visited)
        return lowest_score

    def _get_error(self, pos, dist):
        dijkstra_printer = DijkstraPrinter(dist)
        return (f'wrong val at pos {pos}\n'
                'Dijkstra:\n'
                f'{dijkstra_printer.get_printable_values()}')

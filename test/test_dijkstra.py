import random
from decimal import Decimal
from math import floor

import pytest

from components.board.board import Board, MapLoader
from components.board.monster import Monster
from components.board.pathing import PathMatrixFactory
from components.board.pathing_components import AStarMatrixFactory
from controller.mainmenu_controller import MapOptions
from helper.Misc.constants import IMPASSIBLE, UNEXPLORED
from helper.Misc.datatables import DataTables
from helper.functions import get_hexagonal_manhattan_distance

INFINITY = Decimal('Infinity')


class Edge:
    def __init__(self, to_node, length):
        self.to_node = to_node
        self.length = length


class Graph:
    def __init__(self, node_count):
        self.node_count = node_count
        self.edges = {}

    def add_edge(self, from_node, to_node, length):
        edge = Edge(to_node, length)
        if from_node in self.edges:
            from_node_edges = self.edges[from_node]
        else:
            self.edges[from_node] = dict()
            from_node_edges = self.edges[from_node]
        from_node_edges[to_node] = edge

    def dijkstra(self, source):
        unvisited_nodes = set()
        dist = {}
        prev = {}

        for node in range(self.node_count):
            dist[node] = INFINITY
            prev[node] = INFINITY
            unvisited_nodes.add(node)

        # distance from source to source
        dist[source] = 0
        while unvisited_nodes:
            # node with the least distance selected first
            node = self._min_dist(unvisited_nodes, dist)
            unvisited_nodes.remove(node)
            if node in self.edges:
                for _, edge in self.edges[node].items():
                    alt = dist[node] + edge.length
                    if alt < dist[edge.to_node]:
                        # a shorter path to edge has been found
                        dist[edge.to_node] = alt
                        prev[edge.to_node] = node
        return dist, prev

    def _min_dist(self, q, dist):
        """
        Returns the node with the smallest distance in q.
        Implemented to keep the main algorithm clean.
        """
        min_node = None
        for node in q:
            if min_node is None:
                min_node = node
            elif dist[node] < dist[min_node]:
                min_node = node
        return min_node


class TestCase:
    @pytest.fixture
    def before(self):
        self.board = Board()
        mapload = MapLoader(self.board)
        mapoptions = MapOptions()
        mapoptions.mapname = 'random'
        mapload.load_map(mapoptions)
        self.terrain_type = None

    def test_single_turn(self, before):
        self.generator = PathMatrixFactory(self.board)
        for _ in range(10):
            self.do_single_turn()

    def do_single_turn(self):
        """Make path matrix of board, compare dist values with dijkstra"""
        start = (9, 9)
        monster = self._place_monster(start)
        matrix = self.generator.generate_path_matrix(start)
        graph = self.get_graph(self.board)
        dist, prev = graph.dijkstra(self.pos_to_index(start))
        for index in dist:
            pos = self.index_to_pos(index)
            # convert pos to node index
            index = self.pos_to_index(pos)
            matrix_val = matrix.get_distance_value_at(pos)
            dijkstra_val = dist[index]
            if matrix_val == UNEXPLORED:
                assert dijkstra_val > monster.stats.move_points, (
                    f'{self._get_error(matrix, pos)}')
            elif matrix_val == IMPASSIBLE:
                assert dijkstra_val == INFINITY, (
                    f'{self._get_error(matrix, pos)}')
            else:
                assert matrix_val == dijkstra_val, (
                    f'{self._get_error(matrix, pos)}')
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
        graph = self.get_graph(self.board)
        dist, prev = graph.dijkstra(self.pos_to_index(start))
        # only compare end
        matrix_val = matrix.get_distance_value_at(end)
        dijkstra_val = dist[self.pos_to_index(end)]
        if matrix_val >= 99:
            assert dijkstra_val == INFINITY, f'{self._get_error(matrix, end)}'
        else:
            assert matrix_val == dijkstra_val, f'{self._get_error(matrix, end)}'
        self.board.remove_monster(monster)

    def _get_error(self, matrix, pos):
        return (f'wrong val at pos {pos}\n'
                'Distance:\n'
                f'{matrix.get_printable_dist_values()}\n'
                'Terrain cost:\n'
                f'{matrix.get_printable_terrain_cost_values()}\n'
                'Heuristic:\n'
                f'{matrix.get_printable_heuristic_values()}\n')

    def _place_monster(self, start):
        monster_type = random.randint(0, Monster.Type.TAITAN)
        monster = self.board.place_new_monster(monster_type, start, 0)
        self.terrain_type = monster.terrain_type
        return monster

    def pos_to_index(self, pos):
        return pos[0] * self.board.x_max + pos[1]

    def index_to_pos(self, index):
        return index % self.board.x_max, floor(index / self.board.x_max)

    def get_graph(self, board):
        count = board.x_max * board.y_max
        graph = Graph(count)
        for x in range(self.board.x_max):
            for y in range(self.board.y_max):
                self._add_edges_starting_at((x, y), graph)
        return graph

    def _add_edges_starting_at(self, pos, graph):
        adj_posses = self.board.get_posses_adjacent_to(pos)
        for adj_pos in adj_posses:
            terrain = self.board.terrain_at(adj_pos)
            move_cost = DataTables.get_terrain_cost(terrain, self.terrain_type)
            if move_cost < 99:
                graph.add_edge(
                    self.pos_to_index(pos), self.pos_to_index(adj_pos),
                    move_cost)

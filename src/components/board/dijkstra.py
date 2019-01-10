from decimal import Decimal
from helper.Misc.datatables import DataTables
from helper.dictionaryprinter import DictionaryPrinter


class DijkstraPrinter(DictionaryPrinter):
    def get_printable_values(self):
        return self._get_values()

    def _get_value_representation_at(self, pos):
        val = self.dict[pos]
        if val < 10:
            return ' ' + str(val)
        else:
            return '' + str(val)


class Edge:
    def __init__(self, to_node, length):
        self.to_node = to_node
        self.length = length


class DijkstraGraph:
    """Copied and modified from someone on the internet"""
    INFINITY = Decimal('Infinity')

    def __init__(self, board, monster):
        self.board = board
        self.monster = monster
        self.terrain_type = monster.terrain_type
        self.edges = {}
        self._make_from_board()

    def _make_from_board(self):
        for x in range(self.board.x_max):
            for y in range(self.board.y_max):
                self._add_edges_starting_at((x, y))

    def _add_edges_starting_at(self, pos):
        adj_posses = self.board.get_posses_adjacent_to(pos)
        if pos != self.monster.pos:
            if self._cannot_move_from_pos(adj_posses):
                return
        for adj_pos in adj_posses:
            terrain = self.board.terrain_at(adj_pos)
            move_cost = DataTables.get_terrain_cost(
                terrain, self.terrain_type)
            if self._can_move_to(adj_pos, move_cost):
                self._add_edge(pos, adj_pos, move_cost)

    def _cannot_move_from_pos(self, adj_posses):
        for adj_pos in adj_posses:
            adj_monster = self.board.monster_at(adj_pos)
            if adj_monster and adj_monster.owner != self.monster.owner:
                return True
        return False

    def _can_move_to(self, pos, move_cost):
        monster_at_pos = self.board.monster_at(pos)
        if monster_at_pos and monster_at_pos.owner != self.monster.owner:
            return False
        return move_cost < 99

    def _add_edge(self, from_node, to_node, length):
        edge = Edge(to_node, length)
        if from_node not in self.edges:
            self.edges[from_node] = {}
        from_node_edges = self.edges[from_node]
        from_node_edges[to_node] = edge

    def dijkstra(self, source):
        unvisited_nodes = set()
        dist = {}
        prev = {}

        for x in range(self.board.x_max):
            for y in range(self.board.y_max):
                dist[(x, y)] = self.INFINITY
                prev[(x, y)] = self.INFINITY
                unvisited_nodes.add((x, y))

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

    def get_printable_values(self, dist):
        printer = DijkstraPrinter(dist)
        return printer.get_printable_values()

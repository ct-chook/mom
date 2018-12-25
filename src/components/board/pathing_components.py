import heapq
import copy
from math import floor

from src.helper import functions
from src.helper.Misc.constants import IMPASSIBLE, UNEXPLORED
from src.helper.Misc.datatables import DataTables


class MatrixProcessor:
    """Generates a distance value matrix using a move point limit given

    Used by the regular, 'wide' matrix that is shown when trying to move a
    monster. It will be blocked by enemy monsters present.
    """

    def __init__(self, matrix):
        self.board = matrix.board
        self.tiles_to_explore: [] = None
        self.matrix: PathMatrix = matrix
        self.accessible_positions = None
        self.monster = None
        self.move_points_base_tile = None
        self.move_points_next_tile = None
        self.pos = None
        self.cannot_move_from_pos = None
        self.max_dist_value = None

    def _process_tiles(self, start):
        self._setup_processing(start)
        self._explore_tiles()

    def _explore_tiles(self):
        n = 0
        while n < 1000:
            if self.matrix_is_finished():
                break
            self._explore_next_tile()
            n += 1
        assert n < 1000, 'Matrix took too long to process'

    def _setup_processing(self, start):
        self.monster = self.board.monster_at(start)
        # creating set with tuple doesn't work, add it separately
        self.accessible_positions = set()
        self.accessible_positions.add(start)
        self.matrix.accessible_positions = self.accessible_positions
        self.matrix.set_distance_value_at(start, 0)
        self.tiles_to_explore = [(0, start)]

    def matrix_is_finished(self):
        return not self.tiles_to_explore

    def _explore_next_tile(self):
        self.pos = heapq.heappop(self.tiles_to_explore)[1]
        assert self.pos[0] >= 0
        assert self.pos[1] >= 0
        self.cannot_move_from_pos = False
        adjacent_enemies = self.board.get_enemies_adjacent_to(self.pos)
        self._handle_adjacent_enemies(adjacent_enemies)
        if self.cannot_move_from_pos:
            return
        if self._found_tile_to_search_for():
            self.tile_found = True
            self.matrix.end = self.pos
            return
        self.move_points_base_tile = self.matrix.get_distance_value_at(self.pos)
        self._process_adjacent_tiles()

    def _found_tile_to_search_for(self):
        return False

    def _handle_adjacent_enemies(self, adjacent_enemies):
        # if tile has enemies adjacent, you cannot move from it, unless
        # this is the tile the moving monster starts on
        if adjacent_enemies and self.monster.pos != self.pos:
            self.cannot_move_from_pos = True
            self._highlight_tiles_with_enemies(adjacent_enemies)

    def _highlight_tiles_with_enemies(self, adjacent_enemies):
        for adjacent_enemy in adjacent_enemies:
            self.accessible_positions.add(adjacent_enemy.pos)

    def _process_adjacent_tiles(self):
        adjacent_posses = self.board.get_tile_posses_adjacent_to(self.pos)
        for adj_pos in adjacent_posses:
            self._process_adjacent_tile(adj_pos)

    def _process_adjacent_tile(self, adj_pos):
        if self._tile_is_not_passable(adj_pos):
            return
        move_cost = self._get_move_cost_for(adj_pos)
        if move_cost == 99:
            self.matrix.set_distance_value_at(adj_pos, IMPASSIBLE)
            return
        self.move_points_next_tile = self.move_points_base_tile + move_cost
        if self._move_is_valid_and_better(adj_pos):
            self.matrix.set_distance_value_at(
                adj_pos, self.move_points_next_tile)
            self.accessible_positions.add(adj_pos)
            self._push_tile_at(adj_pos)

    def _tile_is_not_passable(self, pos):
        tile_monster = self.board.monster_at(pos)
        if tile_monster and tile_monster.owner != self.monster.owner:
            return True

    def _get_move_cost_for(self, pos):
        return DataTables.get_terrain_cost(self.board.terrain_at(pos),
                                           self.monster.terrain_type)

    def _move_is_valid_and_better(self, pos):
        # Returns true only if this move is within the move point budget and
        # has a lower distance value
        if self.move_points_next_tile > self.max_dist_value:
            return False
        dist_value = self.matrix.get_distance_value_at(pos)
        return dist_value > self.move_points_next_tile

    def _push_tile_at(self, pos):
        heapq.heappush(self.tiles_to_explore, (self._get_heuristic(pos), pos))

    def _get_heuristic(self, pos):
        heuristic = self.matrix.get_heuristic_value_at(pos)
        if heuristic == UNEXPLORED:
            heuristic = self.move_points_next_tile
            self.matrix.set_heuristic_value_at(pos, heuristic)
        return heuristic


class FullMatrixProcessor(MatrixProcessor):
    def __init__(self, matrix):
        super().__init__(matrix)

    def fill_distance_values(self, start, max_dist_value):
        self.max_dist_value = max_dist_value
        self._process_tiles(start)


class SearchMatrixProcessor(MatrixProcessor):
    """Abstract class that checks for properties of tiles

    It should have its _found_tile_to_search_for overridden by inheritance.
    Have it return true when the tile at pos fulfills the requirements.

    What this really does is create two matrices. The regular matrix, which
    is needed to create valid destinations for the first move, and a second
    matrix which has no hard restrictions of movement points to draw a path to
    the final destination of a path. Otherwise the path may not be valid if the
    first move ends at a spot occupied by a monster, but it should ignore
    monsters on the rest of the path, otherwise it may create strange routes
    to circumvent potential blockades from far away.
    """

    def __init__(self, matrix):
        super().__init__(matrix)
        self.tile_found = False

    def _setup_processing(self, start):
        super()._setup_processing(start)
        self.player_id = self.monster.owner

    def _expand_matrix(self, matrix):
        self.matrix = matrix

        self.monster = self.board.monster_at(start)
        # creating set with tuple doesn't work, add it separately
        self.accessible_positions = set()
        self.accessible_positions.add(start)
        self.matrix.accessible_positions = self.accessible_positions
        self.matrix.set_distance_value_at(start, 0)
        self.tiles_to_explore = [(0, start)]

        n = 0
        while n < 1000:
            if self.matrix_is_finished():
                break
            self._explore_next_tile()
            n += 1
        if n == 1000:
            raise AttributeError('Matrix took too long to process')

    def matrix_is_finished(self):
        if not self.tiles_to_explore:
            return True
        return self.tile_found

    def _move_is_valid_and_better(self, pos):
        """Checks to see if the tile at pos should be updated

        Returns true only if this move is within the move point budget and
        has a lower distance value
        """
        if self.move_points_next_tile > self.max_dist_value:
            return False
        dist_value = self.matrix.get_distance_value_at(pos)
        return dist_value > self.move_points_next_tile


class TerrainTypeSearchMatrixProcessor(SearchMatrixProcessor):
    """Like regular MatrixProcessor, except this one searches a specific tile"""
    def __init__(self, matrix):
        super().__init__(matrix)
        self.terrain_to_search_for = None

    def fill_distance_values(self, start, terrain_type, max_dist_value):
        self.terrain_to_search_for = terrain_type
        self.max_dist_value = max_dist_value
        self._process_tiles(start)

    def expand_matrix(self, matrix, start_move_points,
                      max_dist_value):
        for pos in self.matrix.dist_values:
            self.matrix.dist_values[pos] = start_move_points
            heapq.heappush(self.tiles_to_explore,
                           (start_move_points, pos))
        self.max_dist_value = max_dist_value
        self._explore_tiles()

    def _found_tile_to_search_for(self):
        return (self.board.tile_at(self.pos).terrain ==
                self.terrain_to_search_for)


class EnemyTerrainSearchMatrixProcessor(SearchMatrixProcessor):
    """Searches for the nearest tile owned by the enemy"""
    def fill_distance_values(self, start, max_dist_value):
        self.max_dist_value = max_dist_value
        self._process_tiles(start)

    def _found_tile_to_search_for(self):
        return (self.board.tile_at(self.pos).owner is not None and
                self.board.tile_at(self.pos).owner != self.player_id)


class OwnTerrainSearchMatrixProcessor(SearchMatrixProcessor):
    """Searches for the nearest tile owned by self"""
    def fill_distance_values(self, start, max_dist_value):
        self.max_dist_value = max_dist_value
        self._process_tiles(start)

    def _found_tile_to_search_for(self):
        return (self.board.tile_at(self.pos).owner ==
                self.player_id)


class EnemySearchMatrixProcessor(SearchMatrixProcessor):
    """Searches for the nearest tile or monster owned by the enemy"""
    def fill_distance_values(self, start, max_dist_value):
        self.max_dist_value = max_dist_value
        self._process_tiles(start)

    def _found_tile_to_search_for(self):
        if self._tile_is_enemy_terrain() or self.tile_found:
            return True

    def _tile_is_enemy_terrain(self):
        return self.board.pos_is_enemy_terrain(self.pos)

    def _tile_has_adjacent_enemy(self):
        return self.board.get_enemies_adjacent_to(self.pos)

    def _handle_adjacent_enemies(self, adjacent_enemies):
        if adjacent_enemies:
            self.tile_found = True
            self._highlight_tiles_with_enemies(adjacent_enemies)


class AStarMatrixProcessor(MatrixProcessor):
    """Processes a matrix using the a* algorithm.

    This is faster but will only work when given a specific pos that it should
    search for. It will stop building the matrix once that pos is reached.
    """

    def __init__(self, matrix):
        super().__init__(matrix)
        self.destination_reached = False
        self.destination = None

    def fill_distance_values(self, start, destination):
        self.monster = self.board.monster_at(start)
        self.matrix.monster = self.monster
        assert self.monster
        self.destination = destination
        self._process_tiles(start)

    def matrix_is_finished(self):
        if not self.tiles_to_explore:
            return True
        return self.destination_reached

    def _explore_next_tile(self):
        self.pos = heapq.heappop(self.tiles_to_explore)[1]
        if self.pos == self.destination:
            self.destination_reached = True
            self.matrix.end = self.pos
            return
        self.move_points_base_tile = self.matrix.get_distance_value_at(self.pos)
        self._process_adjacent_tiles()

    def _move_is_valid_and_better(self, pos):
        # Returns true if this tile hasn't been visited yet or has a lower
        # distance value
        if self.matrix.get_distance_value_at(pos) == UNEXPLORED:
            return True
        dist_value = self.matrix.get_distance_value_at(pos)
        return dist_value > self.move_points_next_tile

    def _get_heuristic(self, pos):
        heuristic = self.matrix.get_heuristic_value_at(pos)
        if heuristic == UNEXPLORED:
            dist_from_destination = \
                self._get_manhattan_distance_to_destination(pos)
            heuristic = self.matrix.get_distance_value_at(
                pos) + dist_from_destination
        self.matrix.set_heuristic_value_at(pos, heuristic)
        return heuristic

    def _get_manhattan_distance_to_destination(self, pos):
        return functions.get_hexagonal_manhattan_distance(pos, self.destination)


class PathGenerator:
    """ Generates shortest paths for monsters.

    Use the board's path matrix to generate the shortest path between monster
    location and a provided destination. Paths are constrained by the game's
    rules. Will return None if no path could be found or reached.
    """

    def __init__(self, board):
        self.board: board.Board = board
        self.path_matrix = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.path = None
        self.monster = None
        self.adj_found = None
        self.start = None
        self.end = None

    def set_path_matrix(self, matrix):
        self.path_matrix = matrix

    def get_path_to(self, pos):
        """Returns the shortest path to a pos in the path matrix"""
        assert self.path_matrix, 'No path matrix set'
        self.start = self.path_matrix.start
        self.end = pos
        if self._destination_not_reachable():
            return None
        self._setup_tracing()
        while self._path_not_fully_traced_yet():
            self._search_for_adjacent_tiles()
            assert self.adj_found, \
                (f'Could not retrace path to {self.start}. '
                 f'Stuck at {self.x0},{self.y0}. \n'
                 f'{self.path_matrix.get_dist_values()}')
        return self.path

    def get_path_on(self, matrix):
        self.path_matrix = matrix
        return self.get_path()

    def get_path(self):
        """Returns the shortest path to a pos in the path matrix"""
        assert self.path_matrix, 'No path matrix set'
        assert self.path_matrix.start
        if not self.path_matrix.end:
            return None
        assert self.path_matrix.end
        self.start = self.path_matrix.start
        self.end = self.path_matrix.end
        if self.end is None:
            return None
        if self._destination_not_reachable():
            return None
        self._setup_tracing()
        while self._path_not_fully_traced_yet():
            self._search_for_adjacent_tiles()
            assert self.adj_found, \
                (f'Could not retrace path to {self.x0},{self.y0}.\n'
                 f'Stuck at {self.x0}:{self.y0}\n'
                 f'Path so far: {self.path}\n'
                 f'{self.path_matrix.print_dist_values()}')
        return self.path

    def _destination_not_reachable(self):
        return self._get_distance_value(self.end) is None

    def _path_not_fully_traced_yet(self):
        return (self.x0, self.y0) != self.path_matrix.start

    def _setup_tracing(self):
        assert self.start, 'Start position not configured'
        assert self.end, 'End position not configured'
        self.x0, self.y0 = self.end
        self.monster = self.path_matrix.monster
        assert self.monster
        # append the ending point (starting pos for the algorithm)
        self.path = [self.end]

    def _search_for_adjacent_tiles(self):
        self.adj_found = False
        adjacent_tiles = self.board.get_tile_posses_adjacent_to(
            (self.x0, self.y0))
        for self.x1, self.y1 in adjacent_tiles:
            self._inspect_tile()

    def _inspect_tile(self):
        next_tile_found = False
        if self._tile_can_be_moved_to():
            # if tile isn't the last tile, it can't be adjacent to enemy
            self.path.insert(0, (self.x1, self.y1))
            self.x0 = self.x1
            self.y0 = self.y1
            next_tile_found = True
        if not self.adj_found:
            self.adj_found = next_tile_found

    def _tile_can_be_moved_to(self):
        return (self._move_cost_difference_is_correct()
                and self._next_tile_is_not_blocked())

    def _move_cost_difference_is_correct(self):
        path_cost_difference = (
                self._get_distance_value((self.x0, self.y0)) -
                self._get_distance_value((self.x1, self.y1)))
        terrain = self.board.terrain_at((self.x0, self.y0))
        move_cost = DataTables.get_terrain_cost(
            terrain, self.monster.terrain_type)
        return path_cost_difference == move_cost

    def _get_distance_value(self, pos):
        return self.path_matrix.get_distance_value_at(pos)

    def _next_tile_is_not_blocked(self):
        """Check if monster can move to this tile.

        If there are monsters adjacent to this tile, the tile is blocked
        (counts as a final move), unless this is the tile the monster starts on
        or the path is retraced from the monster's end position.
        """
        if (self.x1, self.y1) == self.start or (self.x0, self.y0) == self.end:
            return True
        else:
            return self._next_tile_has_no_adjacent_enemies()

    def _next_tile_has_no_adjacent_enemies(self):
        nearby_tiles = self.board.get_tile_posses_adjacent_to((self.x1, self.y1))
        for pos in nearby_tiles:
            nearby_monster = self.board.monster_at(pos)
            if (nearby_monster and nearby_monster.owner !=
                    self.board.get_current_player_id()):
                return False
        return True


class PathMatrix:
    """Holds distance values used for movement and path calculation

    Is created by PathMatrixFactory. Makes use of the board to refer to
    terrain types.
    """

    def __init__(self, board):
        self.board = board
        self.monster = None
        self.start = None
        self.end = None
        self.dist_values = {}
        self.heuristic = {}
        self.accessible_positions = set()

    def set_heuristic_value_at(self, pos, value):
        self.heuristic[pos] = value

    def set_distance_value_at(self, pos, value):
        self.dist_values[pos] = value

    def get_distance_value_at(self, pos):
        if pos in self.dist_values:
            return self.dist_values[pos]
        else:
            return UNEXPLORED

    def get_heuristic_value_at(self, pos):
        if pos in self.heuristic:
            return self.heuristic[pos]
        else:
            return UNEXPLORED

    def is_legal_destination(self, pos):
        if pos in self.accessible_positions:
            return True

    def set_monster(self, monster):
        self.monster = monster
        self.start = monster.pos

    def print_dist_values(self):
        print()
        print(self.get_dist_values())

    def get_dist_values(self, mode=0):
        min_x, min_y, max_x, max_y = self._get_row_and_col_count()
        row_count = (max_y - min_y + 1)
        col_count = max_x - min_x + 1
        to_print = []
        for _ in range(row_count):
            to_print.append([''] * col_count)

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                index_y = y - min_y
                index_x = x - min_x
                to_print[index_y][index_x] = \
                    self._get_dist_value_representation((x, y), mode)
        result = []
        for row in range(row_count):
            if row % 2 != 0:
                result += '  ' + '  '.join(to_print[row]) + '\n'
            else:
                result += '  '.join(to_print[row]) + '\n'
        return ''.join(result)

    def _get_row_and_col_count(self):
        min_x = 1000
        min_y = 1000
        max_x = 0
        max_y = 0
        for key in self.dist_values:
            x, y = key
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

        return min_x, min_y, max_x, max_y

    def _get_dist_value_representation(self, pos, mode):
        if mode == 0:
            val = self.get_distance_value_at(pos)
        else:
            val = self.get_heuristic_value_at(pos)
        if val is None:
            return '  '
        else:
            if val == IMPASSIBLE:
                return '. '
            if val == UNEXPLORED:
                return '  '
            if val < 10:
                return str(floor(val)) + ' '
            else:
                return str(floor(val))
        pass


class MatrixFactory:
    def __init__(self, board):
        self.matrix = None
        self.processor: FullMatrixProcessor = None
        self.terrain_cost = DataTables.terrain_cost
        self.board: board.Board = board

    def setup_matrix(self, start):
        self.matrix = PathMatrix(self.board)
        monster = self.board.monster_at(start)
        assert monster, f'No monster found at pos {start}'
        self.matrix.set_monster(monster)


class AStarMatrixFactory(MatrixFactory):
    def generate_path_matrix(self, start, destination):
        """Generates path matrix up until the destination"""
        self.setup_matrix(start)
        self.processor = AStarMatrixProcessor(self.matrix)
        self.processor.fill_distance_values(start, destination)
        return self.matrix


class TerrainTypeSearchMatrixFactory(MatrixFactory):
    def generate_path_matrix(self, start, terrain_type) -> PathMatrix:
        """Generates a path matrix to the nearest terrain type"""
        self.setup_matrix(start)
        self.processor = TerrainTypeSearchMatrixProcessor(self.matrix)
        move_points = self.board.monster_at(start).stats.move_points
        self.processor.fill_distance_values(start, terrain_type, move_points)
        # ok, so now we have the matrix for a single turn. if the terrain is
        # further than that, what we need to do is continue the matrix until we
        # find the terrain.
        # only restriction is that the first turn can't end on another monster,
        # so all dist values from the first turn that end on a monster must be
        # removed. then more dist values should be generated continuing from the
        # second turn, so they start with dist values equal to the monster's
        # move points per turn.
        # to do this, copy the matrix and replace dist values
        # with move point values, push them on the queue and fill remaining dist
        # values

        keys_to_remove = []
        for pos in self.matrix.dist_values:
            if self.board.monster_at(pos) and pos != start:
                keys_to_remove.append(pos)
        for key in keys_to_remove:
            self.matrix.dist_values.pop(key)
        # now we have a matrix that may need to expand, check if we found
        # something already
        if self.matrix.end and self.board.monster_at(self.matrix.end) is None:
            return self.matrix
        # otherwise we need to expand this matrix
        # save dist values since these are overwritten
        old_dist_values = copy.copy(self.matrix.dist_values)
        self.processor.expand_matrix(
            self.matrix, move_points, move_points * 11)

        # now we got a matrix that doesn't have a full path, so copy the saved
        # path over the expanded one to reconstruct the full path
        for pos in old_dist_values:
            self.matrix.dist_values[pos] = old_dist_values[pos]
        return self.matrix


class OwnTerrainSearchMatrixFactory(MatrixFactory):
    def generate_path_matrix(self, start):
        """Generates a path matrix to the nearest tile owned by self"""
        self.setup_matrix(start)
        self.processor = OwnTerrainSearchMatrixProcessor(self.matrix)
        self.processor.fill_distance_values(start, 100)
        return self.matrix


class EnemyTerrainSearchMatrixFactory(MatrixFactory):
    def generate_path_matrix(self, start):
        """Generates a path matrix to the nearest tile owned by enemy"""
        self.setup_matrix(start)
        self.processor = EnemyTerrainSearchMatrixProcessor(self.matrix)
        self.processor.fill_distance_values(start, 100)
        return self.matrix


class EnemySearchMatrixFactory(MatrixFactory):
    def generate_path_matrix(self, start):
        """Generates a path matrix to the nearest tile owned by enemy"""
        self.setup_matrix(start)
        self.processor = EnemySearchMatrixProcessor(self.matrix)
        self.processor.fill_distance_values(start, 100)
        return self.matrix

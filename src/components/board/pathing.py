from src.components.board.monster import Monster
from src.components.board.pathing_components import FullMatrixProcessor, \
    PathGenerator, PathMatrix, MatrixFactory, AStarMatrixFactory, \
    TowerSearchMatrixFactory


class PathMatrixFactory(MatrixFactory):
    """ This creates path matrices, used to calculate monster movement.
    A path matrix is an array of distance values which all fall within a
    certain movement budget.

    The interface allows different matrices to be made.
    * The regular matrix
    is used to get all possible end points a monster can move to in a single
    turn.
    * The a star matrix requires a destination, but will be quicker to
    make than the regular matrix and may return a path that spans over
    multiple turns.
    * The search matrix requires a target to search for. This
    target may be multiple turns away.
    """

    def generate_path_matrix(self, start) -> PathMatrix:
        """Gets all distance values starting with 1 turn of movement"""
        self.matrix = PathMatrix(self.board)
        monster = self.board.monster_at(start)
        self.matrix.set_monster(monster)
        assert monster
        self.processor = FullMatrixProcessor(self.matrix)
        max_move_points = monster.stats.move_points
        self.processor.fill_distance_values(start, max_move_points)
        return self.matrix


class PathFinder:
    """ Returns the shortest path between two points.

    Create a path matrix except it has to be heuristic, and should stop when
    the end point is found. It can then use the path generator to generate
    the path.

    The interface here can be used to retrieve a path from an existing matrix,
    but also generate a shortest path starting from a position containing a
    monster (using its movement properties) and an arbitrary end point.
    """

    def __init__(self, board):
        self.board = board
        self.path_generator = PathGenerator(board)

    def get_path_on_matrix_to(self, matrix, end):
        """Returns path to end on given matrix"""
        matrix.end = end
        return self.get_path_of_matrix(matrix)

    def get_path_of_matrix(self, matrix):
        """Returns path between start and end positions on given matrix"""
        self.path_generator.set_path_matrix(matrix)
        return self.path_generator.get_path_on(matrix)

    def get_path_between(self, beginning, end):
        """Returns path between given positions"""
        matrix_factory = AStarMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(
            beginning, end)
        path_matrix.print_dist_values()
        return self.path_generator.get_path_on(path_matrix)

    def get_simple_path_between(self, beginning, end):
        """Returns path between given positions"""
        matrix_factory = AStarMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(
            beginning, end)
        path_matrix.print_dist_values()
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_tower(self, beginning):
        """Returns path to nearest terrain type"""
        matrix_factory = TowerSearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(
            beginning)
        return self.path_generator.get_path_on(path_matrix)

    def get_matrix(self):
        return self.path_generator.path_matrix


class Movement:
    def __init__(self):
        self.path = None

    def get_destination(self):
        if self.path:
            return self.path[-1]


class MovementFinder:
    """ Returns a position a monster should move to reach something

    Useful for multi-turn movements, or simply when you need to decide where
    to move a monster to
    """

    def __init__(self, board):
        self.board = board
        self.pathfinder = PathFinder(board)

    def get_movement_to_tile(self, monster, destination) -> Movement:
        assert monster.pos
        path = self.pathfinder.get_path_between(monster.pos, destination)
        return self._get_movement(monster, path)

    def get_simple_movement_to_tile(self, monster, destination) -> Movement:
        assert monster.pos
        path = self.pathfinder.get_simple_path_between(monster.pos, destination)
        return self._get_simple_movement(monster, path)

    def get_movement_to_tower(self, monster: Monster) -> Movement:
        assert monster.pos
        path = self.pathfinder.get_path_to_tower(
            monster.pos)
        return self._get_movement(monster, path)

    def _get_movement(self, monster, path):
        movement = Movement()
        if path:
            movement.path = self._get_partial_path(monster, path)
        return movement

    def _get_simple_movement(self, monster, path):
        movement = Movement()
        if path:
            movement.path = self._get_partial_path(monster, path)
        return movement

    def _get_partial_path(self, monster: Monster, path):
        max_movement = monster.stats.move_points
        matrix: PathMatrix = self.pathfinder.get_matrix()
        new_path = []
        for pos in path:
            if matrix.dist_values[pos] <= max_movement:
                new_path.append(pos)
            else:
                break
        # the path itself may cross over own units, but it
        # cannot end on them. so if the final pos ends at a monster, this will
        # cause an error
        # for now this error should be handled by whatever calls this function
        # assert self.board.monster_at(new_path[-1]) is None, (
        #     f'Partial path is not valid, '
        #     f'{self.board.monster_at(new_path[-1])} is at the last pos')
        return new_path

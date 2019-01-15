from src.components.board.pathing_components import FullMatrixProcessor, \
    PathFinder, PathMatrix, MatrixFactory, AStarMatrixFactory, \
    TowerSearchMatrixFactory, SimplePathFinder


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


class PathFactory:
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
        self.path_generator = PathFinder(board)

    def get_path_on_matrix_to(self, matrix, end):
        """Returns path to end on given matrix"""
        matrix.end = end
        return self.get_path_on_matrix(matrix)

    def get_path_on_matrix(self, matrix):
        """Returns path between start and end positions on given matrix"""
        self.path_generator.set_path_matrix(matrix)
        return self.path_generator.get_path_on(matrix)

    def get_path_between(self, beginning, end):
        """Returns path between given positions"""
        matrix_factory = AStarMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(beginning, end)
        return self.path_generator.get_path_on(path_matrix)

    def get_simple_path_between(self, beginning, end):
        """Returns path between given positions"""
        matrix_factory = AStarMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(beginning, end)
        # we use simple path (ignores monster collision and zone of control
        # so we need to use a different path generator
        # todo: maybe put this in different class altogether?
        self.path_generator = SimplePathFinder(self.board)
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_tower(self, beginning):
        """Returns path to nearest tower type"""
        matrix_factory = TowerSearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(beginning)
        return self.path_generator.get_path_on(path_matrix)

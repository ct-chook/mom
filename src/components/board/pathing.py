from src.components.board.monster import Monster
from src.components.board.pathing_components import FullMatrixProcessor, \
    PathGenerator, PathMatrix, MatrixFactory, AStarMatrixFactory, \
    TerrainTypeSearchMatrixFactory, OwnTerrainSearchMatrixFactory, \
    EnemyTerrainSearchMatrixFactory, EnemySearchMatrixFactory


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

    def generate_path_matrix(self, start):
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
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_terraintype(self, beginning, terrain_type):
        """Returns path to nearest terrain type"""
        matrix_factory = TerrainTypeSearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(
            beginning, terrain_type)
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_enemy_terrain(self, beginning):
        """Returns path to nearest tile owned by enemy owner"""
        matrix_factory = EnemyTerrainSearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(beginning)
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_own_terrain(self, beginning):
        """Returns path to nearest tile owned by specified owner"""
        matrix_factory = OwnTerrainSearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(beginning)
        return self.path_generator.get_path_on(path_matrix)

    def get_path_to_enemy_monster_or_terrain(self, pos):
        """Returns path to nearest tile or monster owned by enemy"""
        matrix_factory = EnemySearchMatrixFactory(self.board)
        path_matrix = matrix_factory.generate_path_matrix(pos)
        if not path_matrix.end:
            # could not find an enemy
            return None
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

    def get_movement_to_terraintype(self, monster: Monster, terrain_type) \
            -> Movement:
        path = self.pathfinder.get_path_to_terraintype(
            monster.pos, terrain_type)
        return self._get_movement(monster, path)

    def get_movement_to_enemy_tile(self, monster: Monster) -> Movement:
        path = self.pathfinder.get_path_to_enemy_terrain(monster.pos)
        return self._get_movement(monster, path)

    def get_movement_to_enemy_monster_or_tile(self, monster: Monster) -> Movement:
        path = self.pathfinder.get_path_to_enemy_monster_or_terrain(monster.pos)
        return self._get_movement(monster, path)

    def get_movement_to_own_tile(self, monster: Monster) -> Movement:
        path = self.pathfinder.get_path_to_own_terrain(monster.pos)
        return self._get_movement(monster, path)

    def _get_movement(self, monster, path):
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
        return new_path

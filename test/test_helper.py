from math import floor

from src.helper.functions import get_hexagonal_manhattan_distance


class TestManhattanDistance:
    """
        0   1   2   3
    0  x   x   x   x
    1    x   x   x   x
    2  x   x   x   x
    3    x   x   x   x
    """
    def check(self, end, value):
        assert value == floor(get_hexagonal_manhattan_distance(self.start, end))

    def test_one_space(self):
        self.start = (0, 0)
        self.check((0, 0), 0)
        self.check((0, 1), 1)
        self.check((1, 0), 1)

    def test_two_spaces(self):
        self.start = (0, 0)
        self.check((1, 1), 2)
        self.check((0, 2), 2)
        """     0   1   2   3
            0  s   x   e   x
            1    x   x  x   x
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((2, 0), 2)
        self.check((1, 2), 2)

    def test_three_spaces(self):
        self.start = (0, 0)
        """     0   1   2   3
            0  s   x   x   x
            1    x   x  x   x
            2  x   x   e   x
            3    x   x   x   x"""
        self.check((2, 2), 3)
        self.check((0, 3), 3)
        self.check((3, 0), 3)
        """     0   1   2   3
            0  s   x   x   x
            1    x   x   e   x
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((2, 1), 3)
        """     0   1   2   3
            0  s   x   x   x
            1    x   x   x   x
            2  x   x   e   x
            3    x   x   x   x"""
        self.check((1, 3), 3)

    def test_start_one_right(self):
        self.start = (1, 0)
        """     0   1   2   3
            0  e   s   x   x
            1    x   x   x   x
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((0, 0), 1)
        self.check((2, 0), 1)
        self.check((1, 1), 1)
        """     0   1   2   3
            0  x   s   x   x
            1    e   x   x   x
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((0, 1), 1)
        self.check((1, 3), 3)

    def test_middle(self):
        self.start = (2, 2)
        """     0   1   2   3
            0  e   x   x   x
            1    x   x   x   x
            2  x   x   s   x
            3    x   x   x   x"""
        self.check((0, 0), 3)
        self.check((0, 4), 3)
        self.check((4, 0), 3)
        self.check((4, 3), 3)




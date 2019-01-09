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
        assert floor(get_hexagonal_manhattan_distance(self.start, end)) == value

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

    def test_start_from_odd_row_to_right(self):
        self.start = (0, 1)
        """     0   1   2   3
            0  x   x   x   x
            1    s   x   x   x
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((0, 0), 1)
        self.check((0, 1), 0)
        self.check((0, 2), 1)
        self.check((0, 3), 2)
        self.check((3, 0), 3)
        self.check((3, 1), 3)
        self.check((3, 2), 3)
        self.check((3, 3), 4)

    def test_start_from_odd_row_to_left(self):
        self.start = (3, 1)
        """     0   1   2   3
            0  x   x   x   x
            1    x   x   x   s
            2  x   x   x   x
            3    x   x   x   x"""
        self.check((0, 0), 4)
        self.check((0, 1), 3)
        self.check((0, 2), 4)
        self.check((0, 3), 4)
        self.check((3, 0), 1)
        self.check((3, 1), 0)
        self.check((3, 2), 1)
        self.check((3, 3), 2)

    def test_larger_top_left(self):
        self.start = (0, 0)
        """     0   1   2   3   4 
            0  s   x   x   x   x
            1    x   x   x   x   x
            2  x   x   x   x   x
            3    x   x   x   x   x
            4  x   x   x   x   x"""
        self.check((4, 0), 4)
        self.check((4, 1), 5)
        self.check((4, 2), 5)
        self.check((4, 3), 6)
        self.check((4, 4), 6)

    def test_larger_top_right(self):
        self.start = (4, 0)
        """     0   1   2   3   4 
            0  x   x   x   x   s
            1    x   x   x   x   x
            2  x   x   x   x   x
            3    x   x   x   x   x
            4  x   x   x   x   x"""
        self.check((0, 0), 4)
        self.check((0, 1), 4)
        self.check((0, 2), 5)
        self.check((0, 3), 5)
        self.check((0, 4), 6)

    def test_bottom_right(self):
        self.start = (4, 4)
        """     0   1   2   3   4 
            0  x   x   x   x   x
            1    x   x   x   x   x
            2  x   x   x   x   x
            3    x   x   x   x   x
            4  x   x   x   x   s"""
        self.check((0, 0), 6)
        self.check((0, 1), 5)
        self.check((0, 2), 5)
        self.check((0, 3), 4)
        self.check((0, 4), 4)

    def test_bottom_left(self):
        self.start = (0, 4)
        """     0   1   2   3   4 
            0  x   x   x   x   x
            1    x   x   x   x   x
            2  x   x   x   x   x
            3    x   x   x   x   x
            4  s   x   x   x   x"""
        self.check((4, 0), 6)
        self.check((4, 1), 6)
        self.check((4, 2), 5)
        self.check((4, 3), 5)
        self.check((4, 4), 4)

    def test_high_grid(self):
        self.start = (1, 0)
        """     0   1   2   3   4 
            0  x   x   x   x   x
            1    x   x   x   x   x
            2  x   x   x   x   x
            3    x   x   x   x   x
            ~~~~~~~~~~~~~~~~~~~~~~~
            98  x   x   x   x   x"""
        self.check((0, 98), 98)
        self.check((4, 98), 98)
        self.start = (4, 0)
        self.check((0, 98), 98)
        self.check((4, 98), 98)

    def test_wide_grid(self):
        """     0   1   2   3   4   5   6
            0  x   x   x   x   x   x   x
            1    x   x   x   x   x   x   x
            2  x   x   x   x   x   x   x
            3    x   x   x   x   x   x   x
            4  x   x   x   x   x   x   x"""
        self.start = (0, 1)
        self.check((6, 0), 6)
        self.check((6, 1), 6)
        self.check((6, 2), 6)
        self.check((6, 3), 7)
        self.start = (0, 2)
        self.check((6, 0), 7)
        self.check((6, 1), 7)
        self.check((6, 2), 6)
        self.check((6, 3), 7)
        self.check((6, 4), 7)

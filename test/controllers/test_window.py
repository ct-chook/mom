import pytest

from src.abstract.controller import ControllerInfoFactory
from src.components.button import ButtonMatrix

# Tests ButtonCluster

info = ControllerInfoFactory().make()


class TestCase:
    def make_button(self, rows, cols):
        self.button = ButtonMatrix(0, 0, 16, 16, rows, cols, info, None)

    # noinspection PyAttributeOutsideInit
    def check_pos(self, x, y, result):
        # noinspection PyUnresolvedReferences
        index = self.button.pos_to_index((x, y))
        assert index == result


class TestOneByTwo(TestCase):
    def test_pos_to_index_conversion(self):
        rows = 1
        cols = 2
        self.make_button(rows, cols)
        self.check_pos(0, 0, 0)
        self.check_pos(31, 0, 1)
        self.check_pos(8, 8, 0)
        self.check_pos(24, 8, 1)
        self.check_pos(0, 15, 0)
        self.check_pos(31, 15, 1)


class TestTwoByOne(TestCase):
    def test_pos_to_index_conversion(self):
        rows = 2
        cols = 1
        self.make_button(rows, cols)
        self.check_pos(0, 0, 0)
        self.check_pos(15, 0, 0)
        self.check_pos(0, 31, 1)
        self.check_pos(15, 31, 1)
        self.check_pos(8, 8, 0)
        self.check_pos(8, 24, 1)


class TestTwoByTwo(TestCase):
    @pytest.fixture
    def before(self):
        rows = 2
        cols = 2
        self.make_button(rows, cols)

    def test_pos_to_index_conversion(self, before):
        self.check_pos(0, 0, 0)
        self.check_pos(31, 0, 1)
        self.check_pos(0, 31, 2)
        self.check_pos(31, 31, 3)
        self.check_pos(8, 8, 0)
        self.check_pos(24, 8, 1)
        self.check_pos(8, 24, 2)
        self.check_pos(24, 24, 3)
        self.check_pos(15, 0, 0)
        self.check_pos(16, 0, 1)

    def test_corners(self, before):
        self.check_pos(0, 15, 0)
        self.check_pos(0, 16, 2)
        self.check_pos(15, 15, 0)
        self.check_pos(16, 16, 3)


class TestOneByThree(TestCase):
    def test_pos_to_index_conversion(self):
        rows = 1
        cols = 3
        self.make_button(rows, cols)
        self.check_pos(0, 0, 0)
        self.check_pos(24, 0, 1)
        self.check_pos(47, 0, 2)
        self.check_pos(0, 15, 0)
        self.check_pos(24, 15, 1)
        self.check_pos(47, 15, 2)


class TestThreeByOne(TestCase):
    def test_pos_to_index_conversion(self):
        rows = 3
        cols = 1
        self.make_button(rows, cols)
        self.check_pos(0, 0, 0)
        self.check_pos(0, 16, 1)
        self.check_pos(0, 32, 2)


class TestThreeByThree(TestCase):
    def test_pos_to_index_conversion(self):
        rows = 3
        cols = 3
        self.make_button(rows, cols)
        self.check_pos(0, 0, 0)
        self.check_pos(47, 0, 2)
        self.check_pos(0, 47, 6)
        self.check_pos(47, 47, 8)
        self.check_pos(8, 8, 0)
        self.check_pos(40, 8, 2)
        self.check_pos(8, 40, 6)
        self.check_pos(40, 40, 8)
        self.check_pos(8, 20, 3)
        self.check_pos(24, 20, 4)
        self.check_pos(36, 20, 5)

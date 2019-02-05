import pytest

from components.button import ButtonMatrix


# Tests ButtonCluster


class TestCase:
    def check_pos(self, x, y, result):
        # noinspection PyUnresolvedReferences
        index = self.button.pos_to_index((x, y))
        assert index == result


class TestOneByTwo(TestCase):
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 1
        cols = 2
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

    def test_pos_to_index_conversion(self, before):
        self.check_pos(0, 0, 0)
        self.check_pos(31, 0, 1)
        self.check_pos(8, 8, 0)
        self.check_pos(24, 8, 1)
        self.check_pos(0, 15, 0)
        self.check_pos(31, 15, 1)


class TestTwoByOne(TestCase):
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 2
        cols = 1
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

    def test_pos_to_index_conversion(self, before):
        self.check_pos(0, 0, 0)
        self.check_pos(15, 0, 0)
        self.check_pos(0, 31, 1)
        self.check_pos(15, 31, 1)
        self.check_pos(8, 8, 0)
        self.check_pos(8, 24, 1)


class TestTwoByTwo(TestCase):
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 2
        cols = 2
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

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
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 1
        cols = 3
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

    def test_pos_to_index_conversion(self, before):
        self.check_pos(0, 0, 0)
        self.check_pos(24, 0, 1)
        self.check_pos(47, 0, 2)
        self.check_pos(0, 15, 0)
        self.check_pos(24, 15, 1)
        self.check_pos(47, 15, 2)


class TestThreeByOne(TestCase):
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 3
        cols = 1
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

    def test_pos_to_index_conversion(self, before):
        self.check_pos(0, 0, 0)
        self.check_pos(0, 16, 1)
        self.check_pos(0, 32, 2)


class TestThreeByThree(TestCase):
    @pytest.fixture
    def before(self):
        width = 16
        height = 16
        rows = 3
        cols = 3
        self.button = ButtonMatrix(0, 0, width, height, rows, cols, None)

    def test_pos_to_index_conversion(self, before):
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

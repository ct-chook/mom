import pytest

from src.helper.textwrap.textwrapper import TextWrap


class TestTextWrap:
    w = None

    @pytest.fixture
    def before(self):
        self.w = TextWrap()

    def test_none(self, before):
        assert () is self.w.wrap(None, 1)

    def test_empty(self, before):
        assert () == self.w.wrap('', 1)

    def test_zero_length(self, before):
        assert ('this text does not get wrapped',) == self.w.wrap(
            'this text does not get wrapped', 0)

    def test_word(self, before):
        assert ('word',) == self.w.wrap('word', 8)

    def test_two_words(self, before):
        assert ('two words',) == self.w.wrap('two words', 9)

    def test_break_two_words(self, before):
        assert ('two', 'words') == self.w.wrap('two words', 5)

    def test_three_words_two_lines(self, before):
        assert ('three words', 'here') == self.w.wrap('three words here', 12)

    def test_break_three_words(self, before):
        assert ('three', 'words', 'here') == self.w.wrap('three words here', 6)

    def test_break_four_words(self, before):
        assert ('these are', 'four words') == self.w.wrap(
            'these are four words', 10)

    def test_word_edge_case_on(self, before):
        assert ('edge case', 'word') == self.w.wrap('edge case word', 9)

    def test_word_edge_case_off(self, before):
        assert ('edge', 'case', 'word') == self.w.wrap('edge case word', 8)

    def test_three_edge_cases(self, before):
        assert ('edge', 'case', 'word') == self.w.wrap('edge case word', 4)

    def test_multiple_edge_cases(self, before):
        assert ('edge', 'case', 'word', 'edge', 'case') == \
               self.w.wrap('edgecase word edge case', 4)

    def test_break_by_one(self, before):
        assert ('a', 'b', 'c') == self.w.wrap('abc', 1)

    def test_break_word(self, before):
        assert ('long', 'word') == self.w.wrap('longword', 4)

    def test_break_words(self, before):
        assert ('wor', 'd', 'wor', 'd') == self.w.wrap('word word', 3)

    def test_break_word_second_line(self, before):
        assert ('a', 'long', 'word') == self.w.wrap('a longword', 4)

    def test_short_sentence(self, before):
        expected = (
                'Return a list of',
                'the words of the',
                'string s.')
        result = self.w.wrap('Return a list of the words of the string s.', 16)
        assert expected == result

    def test_long_sentence(self, before):
        expected = (
            'Return a list of',
            'the words of the',
            'string s. If the',
            'optional second',
            'argument sep is',
            'absent or None,',
            'the words are',
            'separated by',
            'arbitrary',
            'strings of',
            'whitespace',
            'characters',
            '(space, tab,',
            'newline, return,',
            'formfeed).')
        result = self.w.wrap(
            'Return a list of the words of the string s. If the '
            'optional second argument sep is absent or None, the words '
            'are separated by arbitrary strings of whitespace '
            'characters (space, tab, newline, return, formfeed).', 16)
        assert expected == result

    def test_reuse_textwrap(self, before):
        self.w.wrap('words words words', 6)
        expected = (
            'this is a',
            'completely',
            'different',
            'type of',
            'sentence')
        result = self.w.wrap(
            'this is a completely different type of sentence', 10)
        assert expected == result

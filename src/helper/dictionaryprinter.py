class DictionaryPrinter:
    """Prints values in a dict mapped by x,y coordinates"""
    def __init__(self, dict_):
        self.dict = dict_

    def _get_values(self):
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
                    self._get_value_representation_at((x, y))
        result = []
        for row in range(row_count):
            if row % 2 == 1:
                prefix = '   '
            else:
                prefix = ''
            result.append('{:2d}  '.format(min_y + row) + prefix
                          + '    '.join(to_print[row]) + '\n')
        last_line = ['  ']
        for col in range(col_count):
            last_line.append('{:2d}'.format(col + min_x))
        result.append('    '.join(last_line))
        return '\n' + ''.join(result)

    def _get_row_and_col_count(self):
        min_x = 1000
        min_y = 1000
        max_x = 0
        max_y = 0
        for key in self.dict:
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

    def _get_value_representation_at(self, pos):
        """Override"""
        pass

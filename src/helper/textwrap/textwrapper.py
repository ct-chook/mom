class TextWrap:
    # Wraps 'text' around column length 'length', returns a tuple of lines
    def __init__(self):
        self.text = None
        self.length = None
        self.break_index = None
        self.start_index = None
        self.result = None

    def wrap(self, text, length):
        if not text:
            return ()
        if length < 1:
            return text,

        self.text = text
        self.length = int(length)
        self.start_index = 0
        self.result = []
        self._wrap_text()
        return tuple(self.result)

    def _wrap_text(self):
        if self.remaining_text_fits_on_line():
            self.result.append(self.text[self.start_index:])
            return
        self.break_index = self.text.rfind(
            ' ', self.start_index, self.start_index + self.length + 1)
        if self.no_space_found():
            self.break_index = self.start_index + self.length
            second_line_index = self.break_index
        else:
            second_line_index = self.break_index + 1
        self.result.append(self.text[self.start_index:self.break_index])
        self.start_index = second_line_index
        self._wrap_text()

    def no_space_found(self):
        return self.break_index == -1

    def remaining_text_fits_on_line(self):
        return len(self.text) - self.start_index <= self.length

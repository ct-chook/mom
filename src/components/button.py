import logging
from math import floor

from src.abstract.controller import Controller
from src.abstract.view import View
from src.helper.Misc.constants import Color


class Button(Controller):
    def __init__(self, x, y, width, height, info, callback, *args):
        super().__init__(x, y, width, height, info)
        self.callbacks = []
        self.arguments = []
        self.add_callback(callback, *args)
        self.name = 'Button'
        self.view = None

    def handle_mouseclick(self):
        logging.info(f'{self} was clicked')
        for callback, argument in zip(self.callbacks, self.arguments):
            logging.info(f'executing callback {callback}')
            callback(*argument)

    def add_callback(self, callback, *args):
        if callback is not None:
            logging.info(f'Adding callback {callback}')
            self.callbacks.append(callback)
            # strange workaround to avoid giving args to append()
            self.arguments.append(None)
            self.arguments[-1] = args


class TextButton(Button):
    def __init__(self, x, y, width, height, info, button_text, callback, *args):
        super().__init__(x, y, width, height, info, callback, *args)
        self.name = f'TextButton: {button_text}'
        self.view = self.add_view(TextButtonView, button_text)


class TextButtonView(View):
    def __init__(self, rectangle, text):
        super().__init__(rectangle)
        self.bg_color = Color.BLACK
        self.text = self.add_text(text, size=20, offset=(0, 0))

    def set_text(self, text):
        self.text.set_text(text)
        # todo is below needed?
        # self.text.set_new_text_to_surface()
        self.queue_for_sprite_update()


class ButtonMatrix(Button):
    """A block of buttons, that passes the index of the button to callback"""
    def __init__(self, x, y, button_width, button_height, rows, cols,
                 info, callback):
        super().__init__(x, y, button_width * cols, button_height * rows,
                         info, callback)
        self.rows = rows
        self.cols = cols
        self.button_width = button_width
        self.button_height = button_height

    def handle_mouseclick(self):
        logging.info('was clicked')
        index = self.pos_to_index(self.mouse_pos)
        self._handle_button_click(index)

    def add_button_sprite(self, sprite, index):
        """todo Should be part of background, instead of a sprite?"""
        offset = self.index_to_pos(index)
        return self.view.add_sprite(sprite, offset)

    def index_to_pos(self, index):
        if index == 0:
            return 0, 0
        row = self.rows % index
        col = floor(self.cols / index)
        pos = row * self.button_width, col * self.button_height
        return pos

    def pos_to_index(self, mouse_pos):
        x, y = mouse_pos
        index = floor(x / self.button_width)
        index += self.cols * floor(y / self.button_height)
        return index

    def _handle_button_click(self, index):
        for callback in self.callbacks:
            logging.info(f'executing callback {callback}({index})')
            callback(index)


class ButtonMatrixView(View):
    pass

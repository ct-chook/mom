import logging
import types
from math import floor

from src.helper.Misc.constants import Color
from src.abstract.controller import Controller
from src.abstract.view import View


class Button(Controller):
    def __init__(self, x, y, width, height, callbacks, *args):
        super().__init__(x, y, width, height)
        self.callbacks = []
        self.arguments = []
        self.add_callback(callbacks, *args)
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



class Window(Controller):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._buttons = []

    def add_button(self, input_button):
        self.attach_controller(input_button)
        self._buttons.append(input_button)
        input_button.show()
        return input_button

    def handle_mouseclick(self):
        for button in self._buttons:
            if button.overlaps_with(self.mouse_pos):
                button.handle_mouseclick(self.mouse_pos)
                break

    def handle_mouseover(self):
        for button in self._buttons:
            if button.overlaps_with(self.mouse_pos):
                button.handle_mouseover(self.mouse_pos)
                break


class TextButton(Button):
    def __init__(
            self, x, y, width, height, button_text, callbacks, *args):
        super().__init__(x, y, width, height, callbacks, *args)
        self.name = f'TextButton: {button_text}'
        self.view = self.add_view(TextButtonView, button_text)


class TextButtonView(View):
    def __init__(self, rectangle, text):
        super().__init__(rectangle)
        self.bg_color = Color.BLACK
        self.text = self.add_text(text, size=20, offset=(0, 0))

    def set_text(self, text):
        self.text.set_text(text)
        self.text.set_new_text_to_surface()
        self.queue_for_sprite_update()


class ButtonMatrix(Button):
    def __init__(self, x, y, button_width, button_height, rows, cols,
                 callbacks):
        super().__init__(
            x, y, button_width * cols, button_height * rows, callbacks)
        self.rows = rows
        self.cols = cols
        self.button_width = button_width
        self.button_height = button_height

    def handle_mouseclick(self):
        logging.info('was clicked')
        index = self.pos_to_index(self.mouse_pos)
        self._handle_button_click(index)

    def add_button_sprite(self, sprite, index):
        offset = self.index_to_pos(index)
        return self.view.add_sprite(sprite, offset)

    def index_to_pos(self, index):
        row = self.rows % index
        col = floor(self.cols / index)
        return row * self.button_width, col * self.button_height

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
    def __init__(self, rectangle):
        super().__init__(rectangle)


class YesNoWindow(Window):
    def __init__(self, window_text, yes_callback, no_callback):
        assert isinstance(yes_callback, types.MethodType), \
            f'Yes/no window {window_text} has no callback on yes'
        if no_callback:
            assert isinstance(no_callback, types.MethodType)

        text_width = 200
        text_height = 100
        text_height += 10  # extra room to space text out
        button_height = 25
        button_width = 50
        window_height = text_height + button_height
        window_width = text_width
        yes_x = int(window_width / 2 - button_width)
        no_x = int(window_width / 2)
        yes_button = TextButton(
            yes_x, text_height - 25, button_width, button_height,
            'Yes', yes_callback)
        no_button = TextButton(
            no_x, text_height - 25, button_width, button_height,
            'No', no_callback)
        yes_button.add_callback(self.hide)
        no_button.add_callback(self.hide)

        super().__init__(200, 200, window_width, window_height)
        self.view = self.add_view(YesNoWindowView, window_text)
        self.yes = self.add_button(yes_button)
        self.no = self.add_button(no_button)
        self.name = f'Yes/no window: {window_text}'
        self.update_view()


class YesNoWindowView(View):
    def __init__(self, rectangle, text):
        super().__init__(rectangle)
        self.bg_color = Color.GRAY
        font_size = 20
        offset = (10, 10)
        self.add_text(text, font_size, offset)

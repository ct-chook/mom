import types

from src.components.button import TextButton
from src.abstract.view import View
from src.abstract.window import Window
from src.helper.Misc.constants import Color


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
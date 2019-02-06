from src.abstract.controller import Controller


class Window(Controller):
    def __init__(self, x, y, width, height, info):
        super().__init__(x, y, width, height, info)
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

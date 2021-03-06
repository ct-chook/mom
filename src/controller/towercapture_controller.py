import logging

from src.abstract.window import Window
from src.helper.Misc.constants import is_even, Color
from src.abstract.view import View
from src.helper.events import EventCallback


class TowerCaptureWindow(Window):
    def __init__(self, info):
        super().__init__(200, 200, 200, 200, info)
        self.view: TowerCaptureView = self.add_view(TowerCaptureView)
        self.hide()

    def handle_mouseclick(self):
        self.view.halt_animation()
        self.hide()

    def show_capture(self):
        events = (EventCallback(self.show),
                  EventCallback(self.view.show_capture),
                  EventCallback(self.hide),
                  EventCallback(self.parent.unfreeze_events))
        for event in events:
            self.append_event(event)
        pass


class TowerCaptureView(View):
    verbose = 1

    def __init__(self, rectangle):
        super().__init__(rectangle)
        self.add_text('Tower captured', offset=(0, 80))

        # animation stuff
        self._frame = 0
        self._lightning_length = 6
        self._lightning_delay = 24
        self._number_of_flashes = 3

    def show_capture(self):
        logging.info('Playing tower capture event')
        if is_even(self._frame):
            self.bg_color = Color.WHITE
            delay = self._lightning_length
        else:
            self.bg_color = Color.GRAY
            delay = self._lightning_delay
        self.queue_for_background_update()
        self._frame += 1
        if self._frame > self._number_of_flashes * 2:
            self._frame = 0
            return
        else:
            return delay

    def halt_animation(self):
        self._frame = ((self._lightning_length + self._lightning_delay)
                       * self._number_of_flashes)

from src.abstract.game_handler import GameHandler
from src.handlers.mom_display import MomDisplay
from src.controller.mom_controller import MomController


class MomHandler(GameHandler):

    verbose = 1

    def __init__(self):
        super().__init__(1200, 600)
        self.turn_active = True

        self.top_controller = MomController(self.width, self.height)
        self.display.set_top_view(self.top_controller.view)
        self.display.top_view.queue_for_background_update()

    def create_display(self):
        self.display = MomDisplay(self.width, self.height)
        super().create_display()

    def is_running(self):
        return self.top_controller.running


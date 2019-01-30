from abstract.controller import PublisherInjector
from src.abstract.game_handler import GameHandler
from src.controller.mom_controller import MomController
from src.handlers.mom_display import MomDisplay


class MomHandler(GameHandler):
    def __init__(self):
        super().__init__(1125, 600)
        self.top_controller = MomController(self.width, self.height)
        assert self.publisher is not None
        PublisherInjector(self.top_controller).inject(self.publisher)
        self.display.top_view = self.top_controller.view
        self.display.top_view.queue_for_background_update()

    def _create_display(self):
        self.display = MomDisplay(self.width, self.height)

    def is_running(self):
        if (self.top_controller.board_controller
                and self.top_controller.board_controller.model.game_over):
            return True
        return self.top_controller.running


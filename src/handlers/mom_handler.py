from src.abstract.controller import ControllerInfo, ControllerConfig
from src.abstract.game_handler import GameHandler
from src.controller.mom_controller import MomController
from src.handlers.mom_display import MomDisplay


class MomHandler(GameHandler):
    def __init__(self):
        super().__init__(1125, 600)
        config = ControllerConfig()
        info = ControllerInfo(config, self.publisher)
        self.top_controller = MomController(info, self.width, self.height)
        self.display.top_view = self.top_controller.view
        self.display.top_view.queue_for_background_update()

    def _create_display(self):
        self.display = MomDisplay(self.width, self.height)

    def is_running(self):
        return self.top_controller.running

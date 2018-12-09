from src.controller.mainmenu_controller import MainMenuController
from src.abstract.controller_container import ControllerContainer

"""
Is the top controller, so it indirectly contains all controllers of the game
"""


class GameContainer(ControllerContainer):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.attach_controller(MainMenuController(0, 0, 500, 500, None))


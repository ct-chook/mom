import pygame

from src.controller.board_controller import BoardController
from src.abstract.view import View
from src.abstract.window import Window
from src.controller.mainmenu_controller import MainMenuController, \
    MapOptions


class MomController(Window):
    def __init__(self, width, height):
        super().__init__(0, 0, width, height)
        self.view = View(self.rectangle)
        self.running = True
        self.show()

        # Controllers
        self.main_menu: MainMenuController = self.attach_controller(
            MainMenuController(50, 0, 1100, 700, self))
        self.board_controller: BoardController = None

    def create_board(self, mapoptions: MapOptions):
        self.board_controller: BoardController = self.attach_controller(
            BoardController(50, 50, 1100, 700, mapoptions.mapname))

    def handle_keypress(self, key):
        if key == pygame.K_ESCAPE:
            self.handle_key_escape()

    def handle_key_escape(self):
        self.running = False

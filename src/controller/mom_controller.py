import pygame

from src.abstract.view import View
from src.abstract.window import Window
from src.controller.board_controller import BoardController
from src.controller.mainmenu_controller import MainMenuController
from src.components.board.board import MapOptions


class MomController(Window):
    def __init__(self, info, width, height):
        super().__init__(0, 0, width, height, info)
        self.view = View(self.rectangle)
        self.running = True
        self.show()

        # Controllers
        self.main_menu: MainMenuController = self.attach_controller(
            MainMenuController(10, 10, 1100, 700, info, self))
        self.board_controller: BoardController = None

    def create_board(self, info, mapoptions: MapOptions):
        self.board_controller: BoardController = self.attach_controller(
            BoardController(10, 10, 1100, 700, info, mapoptions))

    def handle_keypress(self, key):
        if key == pygame.K_ESCAPE:
            self.handle_key_escape()

    def handle_key_escape(self):
        self.running = False

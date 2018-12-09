import pygame

from src.abstract.maindisplay import MainDisplay


class MomDisplay(MainDisplay):
    def __init__(self, width, height):
        super().__init__(width, height)

    def set_pygame_display(self):
        super().set_pygame_display()
        pygame.display.set_caption('Master of Monsters')

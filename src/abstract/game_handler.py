import logging

import pygame

from src.abstract.maindisplay import MainDisplay
from src.helper.Misc.constants import MouseButton
from src.helper.events import Publisher

# logging.getLogger().setLevel(logging.INFO)


class GameHandler:
    """Class needed for the whole game; display, input, and logic

    This object itself should be instanced once per game running. The game
    handler can be set to run after it is created, and continues to run until
    it is given signal to stop.

    It contains one controller which should indirectly contain every controller
    of the game. It sends input to this controller and underlying controllers.

    The handler has a display object which is responsible for displaying stuff.
    All views should refer to this object to blit surfaces.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.publisher = Publisher()
        self.framerate = 60
        self.display: MainDisplay = None
        self.top_controller = None

        pygame.init()
        self.set_display()
        self.clock = pygame.time.Clock()

    def start(self):
        while self.is_running():  # the main loop
            self._do_game_frame()
        self._cleanup()

    def set_display(self):
        self._create_display()
        logging.info('Creating display')
        self.display.set_pygame_display()

    def _create_display(self):
        pass

    def is_running(self):
        pass

    def _cleanup(self):
        print('Game ended normally!')
        pygame.quit()

    def _do_game_frame(self):
        """As long as the game is active this method is executed repeatedly"""
        self._process_input_events()
        self._process_game_events()
        self._blit_frame()
        self._wait_until_next_frame()

    def _process_input_events(self):
        """get all mouse motions and process the last one only
               seems this never fetches more than one event
               """
        # mouseMotionEvents = pygame.event.get(MOUSEMOTION)
        # if len(mouseMotionEvents):
        #    self.onEvent(mouseMotionEvents[0]) # process first one
        input_events = pygame.event.get()
        for input_event in input_events:
            self._process_input_event(input_event)

    def _process_input_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == MouseButton.LEFT:
                logging.info(f'received mouseclick at {event.pos}')
                self.top_controller.receive_mouseclick(event.pos)
            elif event.button == MouseButton.RIGHT:
                self.top_controller.receive_right_mouseclick(event.pos)
        elif event.type == pygame.KEYDOWN:
            logging.info(f'received keypress {event.key}')
            self.top_controller.receive_keypress(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self.top_controller.receive_mouseover(event.pos)
        elif event.type == pygame.QUIT:
            self.running = False

    def _process_game_events(self):
        self.publisher.tick_events()

    def _blit_frame(self):
        self.display.blit_frame()

    def _wait_until_next_frame(self):
        self.clock.tick(self.framerate)

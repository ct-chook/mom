import logging

import pygame

from src.helper.Misc.constants import MouseButton
from src.helper.events.events import EventQueue
from src.abstract.controller import Controller
from src.abstract.maindisplay import MainDisplay
from src.abstract.view import View

logging.getLogger().setLevel(logging.INFO)


class GameHandler:
    """Is responsible for the whole game; display, input, sound, and logic

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
        self.events = []
        self.events_to_unsub = []
        self.framerate = 60
        self.display: MainDisplay = None
        self.top_controller = None

        pygame.init()
        self.create_display()
        self.clock = pygame.time.Clock()

        EventQueue.set_publisher(self)
        View.main_controller = self
        Controller.main_controller = self

    def start(self):
        while self.is_running():  # the main loop
            self._do_game_frame()
        self._cleanup()

    def create_display(self):
        logging.info('Creating display')
        self.display.set_pygame_display()

    def is_running(self):
        pass

    def _cleanup(self):
        pygame.quit()

    def _do_game_frame(self):
        """As long as the game is active this method is executed repeatedly"""
        self._process_input_and_timer_events()

    def _process_input_and_timer_events(self):
        self._process_input_events()
        self._process_game_events()
        self.display.blit_frame()
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

    def _process_game_events(self):
        for event in self.events:
            event.tick()
        self._unsubscribe_events_in_unsub_list()

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

    def _wait_until_next_frame(self):
        self.clock.tick(self.framerate)

    def subscribe_event(self, event):
        """Adds event to list to be executed"""
        self.events.append(event)

    def unsubscribe_event(self, event):
        """Removes an active event from the event list"""
        self.events_to_unsub.append(event)

    def _unsubscribe_events_in_unsub_list(self):
        if self.events_to_unsub:
            logging.info(f'unsub list: {self.events_to_unsub}')
            for event in self.events_to_unsub:
                if event in self.events:
                    logging.info(f'Removing event {event}')
                    self.events.remove(event)
                else:
                    raise AttributeError(
                        'attempted to unsubscribe event that does not exist')
            self.events_to_unsub.clear()

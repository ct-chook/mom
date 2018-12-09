# from src.handlers.mom_handler import *
#
#
# class MainControllerTest(MomHandler):
#     headless = False
#     verbose = 1
#
#     def __init__(self, is_headless):
#         if is_headless:
#             self.headless = True
#         super().__init__()
#         self.debug_events = []
#         self.user_inputs = []
#
#     def start(self):
#         self.headless = True
#         self.debug_events = [(5, (129, 689), 1), (5, (323, 377), 1),
#                              (5, (160, 710), 1), (5, (125, 552), 1),
#                              (5, (130, 296), 1), (5, (121, 561), 1),
#                              (5, (334, 381), 1), (2, 32),
#                              (5, (294, 283), 1)]
#         while self.running:  # the main loop
#             self._do_game_frame()
#
#     def record(self):
#         super().start()
#         print(self.debug_events)
#         print(self.user_inputs)
#
#     def create_display(self):
#         if not self.headless:
#             super().create_display()
#
#     def _cleanup(self):
#         if not self.headless:
#             super()._cleanup()
#
#     def _wait_until_next_frame(self):
#         if not self.headless:
#             super()._wait_until_next_frame()
#
#     def check_assertions(self):
#         pass
#
#     class ClickEvent:
#         def __init__(self, _type, pos, button):
#             self.type = _type
#             self.pos = pos
#             self.button = button
#
#     class KeyEvent:
#         def __init__(self, _type, key):
#             self.type = _type
#             self.key = key
#
#     def _get_input_events(self):
#         if self.headless:
#             return self.get_next_event_debug()
#         else:
#             return super()._get_input_events()
#
#     def get_next_event_debug(self):
#         if self.debug_events:
#             event = self.debug_events.pop(0)
#             event_type = event[0]
#             if event_type == pygame.MOUSEBUTTONDOWN:
#                 return self.ClickEvent(event[0], event[1], event[2]),
#             elif event_type == pygame.KEYDOWN:
#                 return self.KeyEvent(event[0], event[1]),
#         else:
#             self.running = False
#             return []
#
#     def receive_mouseclick(self, event):
#         if not self.headless:
#             print(event)
#             self.debug_events.append(
#                 (pygame.MOUSEBUTTONDOWN, event))
#         super().receive_mouseclick(event)
#
#     def receive_keypress(self, event):
#         if not self.headless:
#             self.debug_events.append(
#                 (pygame.KEYDOWN, event))
#         super().receive_keypress(event)
#
#     # triggered on keydown event
#     def handle_keypress(self, key):
#         super().handle_keypress(key)
#         if key == pygame.K_SEMICOLON:
#             user_input = input("Write comment or assertion:")
#             self.user_inputs.append((user_input, len(self.debug_events)))
#             print('Ok!')
#
#     def redraw_screen_on_next_frame(self):
#         if not self.headless:
#             self.display.redraw_screen_on_next_frame()

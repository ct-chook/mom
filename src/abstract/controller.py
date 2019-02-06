import logging

from pygame.rect import Rect

from src.helper.events.events import EventCallback, EventList, Publisher


class ControllerConfig:
    """Configuration for the controllers. Shared."""
    def __init__(self):
        self.scale = 2
        tile_size = 48
        self.tile_width = tile_size
        self.tile_height = tile_size
        self.camera_width = 14
        self.camera_height = 14
        self.speed = 1


class ControllerInfo:
    """Data structure that contains information that controllers need"""
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher


class ControllerInfoFactory:
    def make(self):
        config = ControllerConfig()
        publisher = Publisher()
        return ControllerInfo(config, publisher)


class Controller:
    """The object that represents the input processing, logic and visuals

    Should be fully modular. May be dependent on other controllers, but
    nothing else.

    Accepts rectangle parameters. Do not pass the rectangle directly.
    """

    def __init__(self, x, y, width, height, controller_info):
        self.rectangle = Rect(x, y, width, height)
        self.children = []
        self.view = None
        self.parent = None
        self.mouse_pos = None
        self.events: EventList = None
        self.visible = True

        self._unpack_controller_info(controller_info)

    def _unpack_controller_info(self, controllerinfo):
        assert controllerinfo.config
        assert controllerinfo.publisher
        self.config = controllerinfo.config
        self.publisher = controllerinfo.publisher
        self.create_event_list_from(self.publisher)

    def create_event_list_from(self, publisher):
        self.events = publisher.create_event_list()
        for child in self.children:
            child.create_event_list_from(publisher)

    def topmost_controller_at(self, pos):
        local_pos = self.get_local_pos(pos)
        # latest controllers have highest priority (overlap earlier ones)
        for controller in reversed(self.get_visible_controllers()):
            if controller.overlaps_with(local_pos):
                return controller.topmost_controller_at(local_pos)
        # overlap is by rectangle which has its own x and y
        # therefore, compare overlap with parent pos instead of local post
        assert local_pos[0] >= 0 and local_pos[1] >= 0
        self.mouse_pos = local_pos
        return self

    def get_local_pos(self, pos):
        x, y = pos
        return x - self.rectangle.x, y - self.rectangle.y

    def receive_mouseclick(self, mouse_pos):
        controller = self.topmost_controller_at(mouse_pos)
        if controller:
            controller.handle_mouseclick()

    def receive_right_mouseclick(self, mouse_pos):
        controller = self.topmost_controller_at(mouse_pos)
        if controller:
            controller.handle_right_mouseclick()

    def receive_mouseover(self, mouse_pos):
        controller = self.topmost_controller_at(mouse_pos)
        if controller:
            controller.handle_mouseover()

    def receive_keypress(self, key):
        if not self.visible:
            return
        for controller in self.children:
            # right now all controllers listen to a keypress
            # only one controller should handle a keypress
            controller.receive_keypress(key)
        self.handle_keypress(key)

    def overlaps_with(self, mouse_pos):
        x, y = mouse_pos
        return self.rectangle.collidepoint(x, y)

    def attach_controller(self, controller):
        assert self.view != controller.view
        self.children.append(controller)
        controller.parent = self
        controller.view.parent = self.view
        self.view.add_child_view(controller.view)
        return controller

    def add_view(self, view_class, *args):
        # if parameters:
        self.view = view_class(self.rectangle, *args)
        # else:
        #     self.view = view_class(self.rectangle)
        # assert self.view.rectangle
        self.view.initialize_background()
        return self.view

    def show(self):
        logging.info(f'Showing {self}')
        self._set_visibility(True)

    def hide(self):
        logging.info(f'Hiding {self}')
        self._set_visibility(False)

    def _set_visibility(self, visibility):
        self.visible = visibility
        if self.view:
            self.view.visible = visibility
            # for showing, just update view, for hiding, update parent view also
            if self.visible:
                self.view.queue_for_background_update()
            else:
                if self.parent and self.parent.view:
                    self.parent.view.queue_for_background_update()

    def update_view(self):
        if self.view:
            self.view.update_background()
        # for controller in self.get_visible_controllers():
        #     controller.update_view()

    def get_visible_controllers(self):
        visible_controllers = []
        for controller in self.children:
            if controller.visible:
                visible_controllers.append(controller)
        return visible_controllers

    def freeze_events(self):
        self.events.freeze()

    def unfreeze_events(self):
        self.events.unfreeze()

    def append_callback(self, callback, *args, name=None):
        assert callable(callback)
        self.events.subscribe()
        self.events.append(EventCallback(callback, *args, name=name))

    def append_event(self, event):
        assert self.events is not None
        self.events.subscribe()
        self.events.append(event)

    def click(self):
        """Shorthand, use in tests etc"""
        self.handle_mouseclick()

    def handle_keypress(self, key):
        """Actions a controller should do when key is pressed"""

    def handle_mouseclick(self):
        """Actions a controller should do on a left mouseclick"""

    def handle_right_mouseclick(self):
        """Actions a controller should do on a right mouseclick"""

    def handle_mouseover(self):
        """Actions a controller should do on a mouseover"""

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)

import logging

from pygame.rect import Rect


class Controller:
    """The object that represents the input processing, logic and visuals

    Should be fully modular. May be dependent on other controllers, but
    nothing else.

    Accepts rectangle parameters. Do not pass the rectangle directly.
    """
    main_controller = None
    verbose = 1

    def __init__(self, x, y, width, height):
        self.children = []
        self.view = None
        self.parent = None
        self.rectangle = Rect(x, y, width, height)
        self.visible = True
        self.mouse_pos = None

    def topmost_controller_at(self, pos):
        local_pos = self.get_local_pos(pos)
        # latest controllers have highest priority (overlap earlier ones)
        for controller in reversed(self.get_visible_controllers()):
            if controller.overlaps_with(local_pos):
                return controller.topmost_controller_at(local_pos)
        # overlap is by rectangle which has its own x and y
        # therefore, compare overlap with parent pos instead of local post
        assert local_pos[0] >=0 and local_pos[1] >= 0
        self.mouse_pos = local_pos
        return self

    def get_local_pos(self, pos):
        x, y = pos
        adjusted_pos = (x - self.rectangle.x, y - self.rectangle.y)
        return adjusted_pos

    def receive_mouseclick(self, mouse_pos):
        controller = self.topmost_controller_at(mouse_pos)
        if controller:
            controller.handle_mouseclick()

    def receive_right_mouseclick(self, mouse_pos):
        controller = self.topmost_controller_at(mouse_pos)
        if controller:
            controller.handle_right_mouseclick()

    def receive_mouseover(self, mouse_pos):
        #return
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
        return self.rectangle.collidepoint(mouse_pos)

    def attach_controller(self, controller):
        assert self.view != controller.view
        self.children.append(controller)
        controller.parent = self
        controller.view.parent = self.view
        self.view.add_child_view(controller.view)
        return controller

    def add_view(self, view_class, parameters=None):
        if parameters:
            self.view = view_class(self.rectangle, parameters)
        else:
            self.view = view_class(self.rectangle)
        assert self.view.rectangle
        self.view.initialize_background()
        return self.view

    def show(self):
        logging.info(f'Showing {self}')
        self._change_visibility(True)

    def hide(self):
        logging.info(f'Hiding {self}')
        self._change_visibility(False)

    def _change_visibility(self, visibility):
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

    # def set_parent_of_children(self):
    #     for controller in self.children:
    #         controller.parent = self
    #         controller.set_parent_of_children()

    def get_visible_controllers(self):
        visible_controllers = []
        for controller in self.children:
            if controller.visible:
                visible_controllers.append(controller)
        return visible_controllers

    def __str__(self):
        return self.__class__.__name__

    def handle_keypress(self, key):
        pass

    def handle_mouseclick(self):
        pass

    def handle_right_mouseclick(self):
        pass

    def handle_mouseover(self):
        pass

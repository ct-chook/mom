from src.helper.events.events import Event


class PathEventFactory:
    def __init__(self, path_animation):
        self.callback = path_animation

    def get_event(self, path):
        return Event(self.callback, path)

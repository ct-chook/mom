import logging


class EventCallback:
    """Runs callback using argument provided, and waits

    Wait time is equal to the return value in seconds.
    """
    def __init__(self, callback, *args, name=None):
        self.callback = callback
        self.args = args
        self.name = name

    def play(self):
        assert self.callback, f'Event {self} has no callback'
        logging.info(f'Playing event: {self.name}')
        return self.callback(*self.args)

    def __str__(self):
        return f'{self.name} {self.callback}, {self.args}'

    def __repr__(self):
        if self.name:
            return self.name
        return self.callback


class EventList:
    """Keeps a list of events, and the wait time after each event

    Events can be packed in tuples or lists
    Events subscribe_event to a a publisher as a visitor pattern which can
    trigger events every tick_events (e.g. frame)
    """
    publisher = None

    def __init__(self, events):
        self.events = []
        self.index = 0
        self.activation_time = None
        self.append(events)
        self.subscribe()  # need to check how to handle subscription (implicit?)

    def _unpack_events(self, events):
        if events is None:
            return
        if not self._event_is_packed(events):
            events = (events,)
        for event in events:
            self._unpack_event(event)

    def _unpack_event(self, event):
        try:
            if event is None:
                return
            elif self._event_is_packed(event):
                self._unpack_events(event)
            else:
                self.events.append(event)
        except AttributeError:
            print(f'Invalid event {event} given to EventQueue.')

    def append(self, events):
        self._unpack_events(events)

    def poll_events(self, timer):
        while self.activation_time <= timer and self.index < len(self.events):
            self._play_events()

    def _play_events(self):
        timer_returned = self._get_event().play()
        if timer_returned is None:
            self._switch_to_next_event()
        elif timer_returned <= 0:
            self._switch_to_next_event()
            self.activation_time += abs(timer_returned)
        else:
            self.activation_time += timer_returned

    def _switch_to_next_event(self):
        self.index += 1
        if self.index >= len(self.events):
            self.unsubscribe()

    def _get_event(self) -> EventCallback:
        return self.events[self.index]

    def skip(self):
        """Plays the rest of the events without regards for the timer"""
        while self.index < len(self.events):
            self._play_events()

    def subscribe(self):
        assert self.publisher
        self.publisher.subscribe_event(self)

    def unsubscribe(self):
        assert self.publisher
        logging.info(f'Request to unsub event queue {self}')
        self.publisher.unsubscribe_event(self)

    @staticmethod
    def _event_is_packed(event):
        try:
            iter(event)
        except TypeError:
            return False
        else:
            return True

    @staticmethod
    def set_publisher(publisher):
        EventList.publisher = publisher

    def __repr__(self):
        name = []
        for event in self.events:
            name.append(str(event))
        return ','.join(name)


class EventQueue:
    """Part of the subscription-publisher pattern.

    Receives events. 'Ticks' events down and executes callback when timer hits
    zero.
    """
    def __init__(self):
        self.events = []
        self.timer = 0

    def tick_events(self):
        for event in self.events:
            event.poll_events(self.timer)
        self.timer += 1

    def subscribe_event(self, event):
        self.events.append(event)
        event.activation_time = self.timer

    def unsubscribe_event(self, event):
        if event in self.events:
            self.events.remove(event)

import logging


class Event:
    """Runs callback using argument provided, and waits

    Wait time is equal to the return value in seconds.
    """
    def __init__(self, callback, *args, name='nameless event'):
        self.callback = callback
        self.args = args
        self.name = name

    def play(self):
        assert self.callback, f'Event {self} has no callback'
        logging.info(f'Playing event: {self.name}')
        if self.args:
            return self.callback(*self.args)
        else:
            return self.callback()

    def __str__(self):
        return f'{self.name} {self.callback}, {self.args}'

    def __repr__(self):
        return self.name


class EventQueue:
    """Keeps a list of events, and the wait time after each event

    Events can be packed in tuples or lists
    Events subscribe_event to a a publisher as a visitor pattern which can
    trigger events every tick_events (e.g. frame)
    """
    subscription_publisher = None

    def __init__(self, events):
        self.events = []
        self.index = 0
        self.timer = 1
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

    def tick(self):
        self.timer -= 1
        self._play_event()

    def _play_event(self):
        while self.timer <= 0 and self.index < len(self.events):
            timer_returned = self._get_event().play()
            if timer_returned is None:
                self._switch_to_next_event()
            elif timer_returned <= 0:
                self._switch_to_next_event()
                self.timer = abs(timer_returned)
            else:
                self.timer = timer_returned

    def _switch_to_next_event(self):
        self.index += 1
        if self.index >= len(self.events):
            self.unsubscribe()
        self.timer = 0

    def _get_event(self) -> Event:
        return self.events[self.index]

    def skip(self):
        self._switch_to_next_event()

    def subscribe(self):
        assert self.subscription_publisher
        self.subscription_publisher.subscribe_event(self)

    def unsubscribe(self):
        assert self.subscription_publisher
        logging.info(f'Request to unsub event queue {self}')
        self.subscription_publisher.unsubscribe_event(self)

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
        EventQueue.subscription_publisher = publisher


class Publisher:
    """Part of the subscription-publisher pattern.

    Receives events. 'Ticks' events down and executes callback when timer hits
    zero.
    """
    def __init__(self):
        self.events = []

    def tick_events(self):
        for event in self.events:
            event.tick()

    def subscribe_event(self, event):
        self.events.append(event)

    def unsubscribe_event(self, event):
        if event in self.events:
            self.events.remove(event)

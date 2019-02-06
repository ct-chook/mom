import logging
from collections import deque


class EventCallback:
    """Runs callback using argument provided, and waits

    Wait time is equal to the return value in frames.
    """

    def __init__(self, callback, *args, name=''):
        self.callback = callback
        self.args = args
        self.name = name

    def play(self):
        assert self.callback, f'Event {self} has no callback'
        text = f'Playing event: {self.name} {self.callback}'
        logging.info(text)
        return self.callback(*self.args)

    def __str__(self):
        return f'{self.callback}{self.args}'

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

    def __init__(self, events=None):
        self.events = deque()
        self.activation_time = None
        self.append(events)
        self.frozen = False
        self.publisher = None

    def append(self, event):
        if event:
            self.events.append(event)

    def poll_events(self, timer):
        assert self.publisher
        max = 0
        while (self.events and self.activation_time <= timer
               and not self.frozen and max < 1000):
            self._play_event()
            max += 1
        if not self.events:
            self.unsubscribe()
        if max == 1000:
            print(f'event {self._get_event()} is stuck, skipping')
            self._switch_to_next_event()

    def _play_event(self):
        """Return value of a callback controls if events should be repeated

        If callback returns None, this event is not repeated and the next event
        is run immediately after in the same frame
        If callback returns negative value, the event is not repeated, but the
        absolute returned value is waited in frames before the next event
        If callback returns a positive value, the event is repeated but with the
        return value in frames between the next event
        """
        timer_returned = self._get_event().play()
        if timer_returned is None:
            self._switch_to_next_event()
        elif timer_returned < 0:
            self._switch_to_next_event()
            self.activation_time += abs(timer_returned)
        else:
            self.activation_time += timer_returned

    def _switch_to_next_event(self):
        self.events.popleft()

    def _get_event(self) -> EventCallback:
        return self.events[0]

    def skip(self):
        """Plays the rest of the events without regards for the timer"""
        while self.events:
            self._play_event()

    def subscribe(self):
        assert self.publisher is not None
        self.publisher.subscribe_event(self)

    def unsubscribe(self):
        assert self.publisher is not None
        logging.info(f'Request to unsub event queue {self}')
        self.publisher.unsubscribe_event(self)

    def freeze(self):
        self.unsubscribe()
        self.frozen = True

    def unfreeze(self):
        self.subscribe()
        self.frozen = False

    def __len__(self):
        return len(self.events)

    def __repr__(self):
        name = []
        for event in self.events:
            name.append(str(event))
        return 'eventlist:\n' + '\n'.join(name)


class Publisher:
    """Part of the subscription-publisher pattern.

    Receives events. 'Ticks' events down and executes callback when timer hits
    zero.
    """

    def __init__(self):
        self.timer = 0
        self.events = set()
        self.to_unsubscribe = set()
        self.to_subscribe = set()
        self.is_reading_events = False

    def create_event_list(self, events=None) -> EventList:
        event_list = EventList(events)
        event_list.publisher = self
        return event_list

    def tick_events(self):
        self.is_reading_events = True
        for event in self.events:
            event.poll_events(self.timer)
        self.is_reading_events = False
        self._handle_subscriptions()
        self.timer += 1

    def _handle_subscriptions(self):
        """Remove subscriptions and add them

        Order is important, it may be possible for an eventlist to be renewed
        on the same frame it was removed, so subscribe after unsubscribing
        """
        if self.to_unsubscribe:
            for event in self.to_unsubscribe:
                self.events.remove(event)
            self.to_unsubscribe.clear()
        if self.to_subscribe:
            for event in self.to_subscribe:
                self.events.add(event)
                event.poll_events(self.timer)
            self.to_subscribe.clear()

    def subscribe_event(self, event):
        if self.is_reading_events:
            self.to_subscribe.add(event)
        else:
            self.events.add(event)
        event.activation_time = self.timer

    def unsubscribe_event(self, event):
        if self.is_reading_events:
            if event in self.events:
                self.to_unsubscribe.add(event)
        else:
            if event in self.events:
                self.events.remove(event)

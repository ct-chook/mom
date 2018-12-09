import pytest

from src.helper.events.events import EventQueue, Event, Publisher


class Dummy:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.counter = 0

    def increase_x(self):
        self.x += 1
        return 1

    def increase_x_long(self):
        self.x += 1
        return 5

    def increase_x_once(self):
        self.x += 1
        return 0

    def increase_x_once_delay(self):
        self.x += 1
        return -5

    def increase_x_no_return(self):
        self.x += 1

    def increase_x_then_wait_5(self):
        self.x += 1

    def increase_y(self):
        self.y += 1
        return 1

    def __repr__(self):
        return 'Dummy'


class EventTester:
    @pytest.fixture
    def before(self):
        self.publisher = Publisher()
        EventQueue.set_publisher(self.publisher)
        self.dummy = Dummy()
        self.queues: [EventQueue] = []

    def tick(self):
        self.publisher.tick_events()

    def set_queue(self, events):
        self.queue = EventQueue(events)

    def append_queue(self, events):
        self.queue.append(events)

    def add_queue_with_callback(self, callback):
        event = Event(callback)
        self.queues.append(EventQueue(event))

    def add_queue_with_callbacks(self, callbacks):
        events = []
        for callback in callbacks:
            events.append(Event(callback))
        self.queues.append(EventQueue(events))

    def assert_x_after_ticks(self, x, ticks):
        for tick in range(ticks):
            self.tick()
        assert x == self.dummy.x

    def assert_after_ticks(self, x_tick_tuples):
        for x_tick in x_tick_tuples:
            x, tick = x_tick
            for _ in range(tick):
                self.tick()
            assert x == self.dummy.x

    def assert_both_after_ticks(self, x, y, ticks):
        for tick in range(ticks):
            self.tick()
        assert x == self.dummy.x
        assert y == self.dummy.y

    def test_class(self):
        pass


class NoEvents(EventTester):
    def test_no_event(self, before):
        self.set_queue(None)
        self.tick()

    def test_packed_no_event(self, before):
        self.set_queue((None,))
        self.tick()


class TestOneEvent(EventTester):
    def test_callback(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        assert 1 == len(self.publisher.events)
        assert 0 == self.dummy.x
        self.assert_x_after_ticks(1, 1)
        self.assert_x_after_ticks(2, 1)

    def test_callback_with_delay(self, before):
        self.add_queue_with_callback(self.dummy.increase_x_long)
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)  # 1
        self.assert_x_after_ticks(1, 1)  # 1
        self.assert_x_after_ticks(1, 4)  # 4
        self.assert_x_after_ticks(2, 1)  # 5
        self.assert_x_after_ticks(2, 4)  # 9
        self.assert_x_after_ticks(3, 1)  # 10

    def test_callback_once(self, before):
        self.add_queue_with_callback(self.dummy.increase_x_once)
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(1, 1)
        assert 0 == len(self.publisher.events)
        self.assert_x_after_ticks(1, 10)

    def test_callback_no_return(self, before):
        self.add_queue_with_callback(self.dummy.increase_x_no_return)
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(1, 1)
        assert 0 == len(self.publisher.events)
        self.assert_x_after_ticks(1, 10)

    def test_multiple_no_return(self, before):
        self.add_queue_with_callbacks((
            self.dummy.increase_x_no_return,
            self.dummy.increase_x_no_return,
            self.dummy.increase_x_no_return))
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(3, 1)
        assert 0 == len(self.publisher.events)
        self.assert_x_after_ticks(3, 10)

    def test_callback_delay(self, before):
        self.add_queue_with_callbacks(
            (self.dummy.increase_x_once_delay,
             self.dummy.increase_x))
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(1, 1)
        self.assert_x_after_ticks(1, 4)
        self.assert_x_after_ticks(2, 1)
        self.assert_x_after_ticks(3, 1)
        assert 1 == len(self.publisher.events)

    def test_multiple_delays(self, before):
        self.add_queue_with_callbacks(
            (self.dummy.increase_x_once_delay,
             self.dummy.increase_x_once_delay,
             self.dummy.increase_x_once_delay))
        assert 1 == len(self.publisher.events)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(1, 1)
        self.assert_x_after_ticks(1, 4)
        self.assert_x_after_ticks(2, 1)
        self.assert_x_after_ticks(2, 4)
        self.assert_x_after_ticks(3, 1)
        assert 0 == len(self.publisher.events)


class TestTwoQueues(EventTester):
    def test_duplicate_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(2, 1)
        self.assert_x_after_ticks(4, 1)
        self.assert_x_after_ticks(6, 1)

    def test_single_and_repeated_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x_once)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(2, 1)
        self.assert_x_after_ticks(3, 1)
        self.assert_x_after_ticks(4, 1)

    def test_short_and_long_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x_long)
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(2, 1)
        self.assert_x_after_ticks(6, 4)
        self.assert_x_after_ticks(8, 1)
        self.assert_x_after_ticks(9, 1)

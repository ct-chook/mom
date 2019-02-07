import pytest

from src.helper.events import EventList, EventCallback, Publisher


class Dummy:
    def __init__(self):
        self.x = 0
        self.y = 0

    def increase_x(self):
        self.x += 1
        return 1

    def increase_y(self):
        self.y += 1
        return 1

    def increase_x_wait(self):
        self.x += 1
        return 5

    def increase_x_once_delay(self):
        self.x += 1
        return -5

    def increase_x_once(self):
        self.x += 1

    def __repr__(self):
        return 'Dummy'


class TestCase:
    # noinspection PyAttributeOutsideInit
    @pytest.fixture
    def before(self):
        self.publisher = Publisher()
        self.dummy = Dummy()

    def set_queue(self, events):
        self.queue = EventList(events)

    # noinspection PyAttributeOutsideInit
    def add_queue_with_callback(self, callback):
        event = EventCallback(callback)
        events = self.publisher.create_event_list(event)
        events.subscribe()
        return events

    def add_queue_with_callbacks(self, callbacks):
        events = self.publisher.create_event_list()
        for callback in callbacks:
            events.append(EventCallback(callback))
        events.subscribe()
        return events

    def tick(self):
        self.publisher.tick_events()

    def assert_x_after_ticks(self, x, ticks):
        for tick in range(ticks):
            self.tick()
        assert self.dummy.x == x

    def assert_xy_after_ticks(self, x, y, ticks):
        for tick in range(ticks):
            self.tick()
        assert self.dummy.x == x, 'x is wrong'
        assert self.dummy.y == y, 'y is wrong'


class TestNoEvents(TestCase):
    def test_no_event(self, before):
        self.set_queue(None)
        self.tick()

    def test_packed_no_event(self, before):
        self.set_queue((None,))
        self.tick()


class TestOneCallback(TestCase):
    def test_one_time_calback(self, before):
        self.add_queue_with_callback(self.dummy.increase_x_once)
        assert len(self.publisher.events) == 1
        self.assert_x_after_ticks(0, 0)
        self.assert_x_after_ticks(1, 1)
        self.assert_x_after_ticks(1, 1)

    def test_callback_with_delay(self, before):
        self.add_queue_with_callback(self.dummy.increase_x_wait)
        assert len(self.publisher.events) == 1
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(1, 1)  # 1
        self.assert_x_after_ticks(1, 4)  # 5
        self.assert_x_after_ticks(2, 1)  # 6
        self.assert_x_after_ticks(2, 4)  # 10
        self.assert_x_after_ticks(3, 1)  # 11


class TestMultipleCallbacks(TestCase):
    def test_callback_delay(self, before):
        self.add_queue_with_callbacks(
            (self.dummy.increase_x_once_delay,
             self.dummy.increase_x))
        assert len(self.publisher.events) == 1
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(1, 1)  # 1
        self.assert_x_after_ticks(1, 4)  # 5
        self.assert_x_after_ticks(2, 1)  # 6
        self.assert_x_after_ticks(3, 1)  # 7
        self.assert_x_after_ticks(4, 1)  # 8

    def test_multiple_no_return(self, before):
        self.add_queue_with_callbacks((
            self.dummy.increase_x_once,
            self.dummy.increase_x_once,
            self.dummy.increase_x_once))
        assert len(self.publisher.events) == 1
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(3, 1)  # 1
        self.assert_x_after_ticks(3, 10)  # 11

    def test_multiple_delays(self, before):
        self.add_queue_with_callbacks(
            (self.dummy.increase_x_once_delay,
             self.dummy.increase_x_once_delay,
             self.dummy.increase_x_once_delay))
        assert len(self.publisher.events) == 1
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(1, 1)  # 1
        self.assert_x_after_ticks(1, 4)  # 5
        self.assert_x_after_ticks(2, 1)  # 6
        self.assert_x_after_ticks(2, 4)  # 10
        self.assert_x_after_ticks(3, 1)  # 11


class TestTwoQueues(TestCase):
    def test_duplicate_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x)
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(2, 1)  # 1
        self.assert_x_after_ticks(4, 1)  # 2
        self.assert_x_after_ticks(6, 1)  # 3

    def test_single_and_repeated_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x_once)
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(2, 1)  # 1
        self.assert_x_after_ticks(3, 1)  # 2
        self.assert_x_after_ticks(4, 1)  # 3

    def test_short_and_long_events(self, before):
        self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x_wait)
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(2, 1)  # 1
        self.assert_x_after_ticks(6, 4)  # 5
        self.assert_x_after_ticks(8, 1)  # 6
        self.assert_x_after_ticks(9, 1)  # 7


class TestFreezing(TestCase):
    def test_freeze_and_unfreeze_one_queue(self, before):
        self.event = self.add_queue_with_callback(self.dummy.increase_x)
        self.add_queue_with_callback(self.dummy.increase_x)
        self.assert_x_after_ticks(0, 0)  # 0
        self.assert_x_after_ticks(2, 1)  # 1
        self.event.freeze()
        self.assert_x_after_ticks(3, 1)  # 2
        self.event.unfreeze()
        self.assert_x_after_ticks(5, 1)  # 3

    def test_event_freezes_self(self, before):
        self.event = self.add_queue_with_callbacks((
            self.dummy.increase_x_once_delay,
            self.freeze_event,
            self.dummy.increase_y))
        self.assert_xy_after_ticks(0, 0, 0)  # 0
        self.assert_xy_after_ticks(1, 0, 1)  # 1
        self.assert_xy_after_ticks(1, 0, 1)  # 2
        self.assert_xy_after_ticks(1, 0, 1)  # 3
        self.assert_xy_after_ticks(1, 0, 1)  # 4
        self.assert_xy_after_ticks(1, 0, 1)  # 5
        self.assert_xy_after_ticks(1, 0, 1)  # 6
        self.assert_xy_after_ticks(1, 0, 1)  # 7
        self.unfreeze_event()
        self.assert_xy_after_ticks(1, 1, 1)  # 8

    def test_events_unfreeze_each_other(self, before):
        self.event2 = self.add_queue_with_callbacks((
            self.dummy.increase_x_once_delay,
            self.unfreeze_event))
        self.event = self.add_queue_with_callbacks((
            self.dummy.increase_x_once_delay,
            self.dummy.increase_x_once_delay,
            self.event2.unfreeze,
            self.freeze_event,
            self.dummy.increase_y))
        self.event2.freeze()
        self.assert_xy_after_ticks(0, 0, 0)  # initial
        self.assert_xy_after_ticks(1, 0, 1)  # 0
        self.assert_xy_after_ticks(1, 0, 1)  # 1
        self.assert_xy_after_ticks(1, 0, 3)  # 4
        self.assert_xy_after_ticks(2, 0, 1)  # 5
        self.assert_xy_after_ticks(2, 0, 4)  # 9
        self.assert_xy_after_ticks(3, 0, 1)  # 10
        self.assert_xy_after_ticks(3, 0, 4)  # 14
        self.assert_xy_after_ticks(3, 1, 1)  # 15

    def freeze_event(self):
        self.event.freeze()

    def unfreeze_event(self):
        self.event.unfreeze()

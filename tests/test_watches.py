import asyncio

import pytest

from custom_components.vab.watches import WatchManager, watch_key


def run(coro):
    return asyncio.run(coro)


class FakeHass:
    def __init__(self):
        self.services = _FakeServices()


class _FakeServices:
    def has_service(self, domain, service):
        return False


@pytest.fixture
def manager():
    m = WatchManager(FakeHass())
    m._watches = []  # skip async_load() / Store round-trip
    return m


class TestAddRemove:
    def test_add_creates_watch(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2026-08-16T10:00:00", None, 2))
        assert manager.keys_for_entry("entry1") == [watch_key("10", "Innenstadt", "2026-08-16T10:00:00")]

    def test_add_is_idempotent(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2026-08-16T10:00:00", None, 2))
        run(manager.async_add("entry1", "10", "Innenstadt", "2026-08-16T10:00:00", None, 2))
        assert len(manager.keys_for_entry("entry1")) == 1

    def test_remove_deletes_watch(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2026-08-16T10:00:00", None, 2))
        run(manager.async_remove("entry1", "10", "Innenstadt", "2026-08-16T10:00:00"))
        assert manager.keys_for_entry("entry1") == []

    def test_remove_unknown_watch_is_noop(self, manager):
        run(manager.async_remove("entry1", "10", "Innenstadt", "2026-08-16T10:00:00"))
        assert manager.keys_for_entry("entry1") == []

    def test_keys_scoped_to_entry(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2026-08-16T10:00:00", None, 2))
        run(manager.async_add("entry2", "4", "Hbf", "2026-08-16T10:05:00", None, 2))
        assert manager.keys_for_entry("entry1") == [watch_key("10", "Innenstadt", "2026-08-16T10:00:00")]


class TestCheckLeave:
    def test_fires_once_when_due(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "planned1", None, 2))
        dep = {"line": "10", "direction": "Innenstadt", "planned": "planned1", "leave_in_minutes": 1, "delay_minutes": 0, "effective": None}
        run(manager.async_check("entry1", "Freihofsplatz", [dep]))
        assert manager._watches[0]["notified_leave"] is True

    def test_rearms_once_back_above_threshold(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "planned1", None, 2))
        due = {"line": "10", "direction": "Innenstadt", "planned": "planned1", "leave_in_minutes": 1, "delay_minutes": 0, "effective": None}
        not_due = {**due, "leave_in_minutes": 10}
        run(manager.async_check("entry1", "Freihofsplatz", [due]))
        assert manager._watches[0]["notified_leave"] is True
        run(manager.async_check("entry1", "Freihofsplatz", [not_due]))
        assert manager._watches[0]["notified_leave"] is False

    def test_falls_back_to_minutes_until_when_no_walk_time(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "planned1", None, 2))
        dep = {"line": "10", "direction": "Innenstadt", "planned": "planned1", "minutes_until": 0, "delay_minutes": 0, "effective": None}
        run(manager.async_check("entry1", "Freihofsplatz", [dep]))
        assert manager._watches[0]["notified_leave"] is True


class TestCheckDelay:
    def test_fires_on_new_delay(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "planned1", None, 2))
        dep = {"line": "10", "direction": "Innenstadt", "planned": "planned1", "delay_minutes": 3, "minutes_until": 10, "effective": None}
        run(manager.async_check("entry1", "Freihofsplatz", [dep]))
        assert manager._watches[0]["notified_delay"] == 3

    def test_rearms_on_return_to_on_time(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "planned1", None, 2))
        delayed = {"line": "10", "direction": "Innenstadt", "planned": "planned1", "delay_minutes": 3, "minutes_until": 10, "effective": None}
        on_time = {**delayed, "delay_minutes": 0}
        run(manager.async_check("entry1", "Freihofsplatz", [delayed]))
        assert manager._watches[0]["notified_delay"] == 3
        run(manager.async_check("entry1", "Freihofsplatz", [on_time]))
        assert manager._watches[0]["notified_delay"] == 0


class TestExpiry:
    def test_drops_watch_once_departure_missing_and_past(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2020-01-01T00:00:00", None, 2))
        run(manager.async_check("entry1", "Freihofsplatz", []))
        assert manager.keys_for_entry("entry1") == []

    def test_keeps_watch_when_departure_missing_but_not_past(self, manager):
        run(manager.async_add("entry1", "10", "Innenstadt", "2099-01-01T00:00:00", None, 2))
        run(manager.async_check("entry1", "Freihofsplatz", []))
        assert manager.keys_for_entry("entry1") == [watch_key("10", "Innenstadt", "2099-01-01T00:00:00")]

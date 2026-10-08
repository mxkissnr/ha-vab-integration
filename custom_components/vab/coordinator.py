from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import efa_fetch_raw
from .const import (
    CONF_DIRECTION_FILTER,
    CONF_LINE_FILTER,
    CONF_MAX_DEPARTURES,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_WALK_TIME,
    DEFAULT_DEPARTURES,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .utils import normalize_direction
from .watches import WatchManager

_LOGGER = logging.getLogger(__name__)


class VabCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, watch_manager: WatchManager) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.watch_manager = watch_manager
        self.stop_id: str = entry.data[CONF_STOP_ID]
        self.max_departures: int = entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES)
        self.line_filter: list[str] = entry.data.get(CONF_LINE_FILTER, [])
        self.direction_filter: list[str] = entry.data.get(CONF_DIRECTION_FILTER, [])
        self.walk_time: int = entry.data.get(CONF_WALK_TIME, 0)

    async def _async_update_data(self) -> list[dict[str, Any]]:
        raw = await self._fetch_efa()
        result = _apply_filters(raw, self.line_filter, self.direction_filter)[: self.max_departures]

        if self.walk_time:
            for dep in result:
                dep["leave_in_minutes"] = dep["minutes_until"] - self.walk_time

        await self.watch_manager.async_check(
            self.entry.entry_id, self.entry.data[CONF_STOP_NAME], result
        )

        if not result and raw:
            _LOGGER.warning(
                "Stop %s: %d departures fetched but all filtered out "
                "(line_filter=%s, direction_filter=%s). "
                "Available directions: %s",
                self.stop_id,
                len(raw),
                self.line_filter,
                self.direction_filter,
                sorted({d["direction"] for d in raw}),
            )

        return result

    async def _fetch_efa(self) -> list[dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        fetch_limit = max(self.max_departures * 4, 30)
        try:
            raw_list = await efa_fetch_raw(session, self.stop_id, fetch_limit)
        except Exception as err:
            raise UpdateFailed(f"EFA-Fehler: {err}") from err

        if not raw_list:
            tomorrow = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
            try:
                raw_list = await efa_fetch_raw(session, self.stop_id, 100, itd_date=tomorrow, itd_time="0000")
            except Exception as err:
                raise UpdateFailed(f"EFA-Fehler (overnight): {err}") from err

        if not raw_list:
            tomorrow = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
            try:
                raw_list = await efa_fetch_raw(session, self.stop_id, 100, itd_date=tomorrow, itd_time="0500")
            except Exception as err:
                raise UpdateFailed(f"EFA-Fehler (05:00 retry): {err}") from err

        return _parse_efa(raw_list)


def _apply_filters(
    departures: list[dict[str, Any]],
    line_filter: list[str],
    direction_filter: list[str],
) -> list[dict[str, Any]]:
    if line_filter:
        departures = [d for d in departures if d.get("line") in line_filter]
    if direction_filter:
        departures = [
            d
            for d in departures
            if any(f.lower() in d.get("direction", "").lower() for f in direction_filter)
        ]
    return departures


def _parse_efa(raw: list[dict]) -> list[dict[str, Any]]:
    """Parse EFA rapidJSON stopEvents into departure dicts (naive local times)."""
    now = datetime.now()
    departures: list[dict[str, Any]] = []

    for dep in raw:
        try:
            statuses = dep.get("realtimeStatus") or []
            if dep.get("isCancelled") or any("CANCELLED" in s for s in statuses):
                continue
            rt_status = "MONITORED" if "MONITORED" in statuses else (statuses[0] if statuses else "UNKNOWN")

            planned = _parse_efa_datetime(dep.get("departureTimePlanned"))
            realtime = _parse_efa_datetime(dep.get("departureTimeEstimated"))
            effective = realtime or planned
            if effective is None:
                continue

            line = dep.get("transportation", {})
            direction = normalize_direction(line.get("destination", {}).get("name", ""))

            if planned and realtime:
                delay = int((realtime - planned).total_seconds() / 60)
            else:
                delay = 0

            minutes_until = int((effective - now).total_seconds() / 60)

            departures.append({
                "line": line.get("number") or line.get("disassembledName", "?"),
                "direction": direction,
                "platform": dep.get("location", {}).get("properties", {}).get("platform", ""),
                "planned": planned.isoformat() if planned else None,
                "realtime": realtime.isoformat() if realtime else None,
                "effective": effective.isoformat(),
                "delay_minutes": delay,
                "minutes_until": minutes_until,
                "monitored": rt_status == "MONITORED",
                "rt_status": rt_status,
                "source": "efa",
            })
        except (KeyError, ValueError, TypeError):
            continue

    departures = [d for d in departures if d["minutes_until"] >= -1]
    departures.sort(key=lambda x: x["minutes_until"])
    return departures


def _parse_efa_datetime(value: str | None) -> datetime | None:
    """ISO UTC timestamp -> naive local datetime, comparable with datetime.now()
    (sensor attributes and stored watches stay naive, as before #33)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone().replace(tzinfo=None)
    except ValueError:
        return None

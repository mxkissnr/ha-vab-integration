from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DIRECTION_FILTER,
    CONF_LINE_FILTER,
    CONF_MAX_DEPARTURES,
    CONF_SOURCE,
    CONF_STOP_ID,
    DEFAULT_DEPARTURES,
    DOMAIN,
    EFA_BASE_URL,
    EFA_DM_ENDPOINT,
    MARUDOR_BASE_URL,
    MARUDOR_DEPARTURES_ENDPOINT,
    SOURCE_DB,
    SOURCE_EFA,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class VabCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.stop_id: str = entry.data[CONF_STOP_ID]
        self.source: str = entry.data.get(CONF_SOURCE, SOURCE_EFA)
        self.max_departures: int = entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES)
        # Leere Liste = kein Filter (alle zeigen)
        self.line_filter: list[str] = entry.data.get(CONF_LINE_FILTER, [])
        self.direction_filter: list[str] = entry.data.get(CONF_DIRECTION_FILTER, [])

    async def _async_update_data(self) -> list[dict[str, Any]]:
        if self.source == SOURCE_DB:
            raw = await self._fetch_db()
        else:
            raw = await self._fetch_efa()
        return _apply_filters(raw, self.line_filter, self.direction_filter)[: self.max_departures]

    # ------------------------------------------------------------------ #
    #  EFA (Bus / Tram)                                                   #
    # ------------------------------------------------------------------ #

    async def _fetch_efa(self) -> list[dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        # Mehr abrufen als benötigt, damit Filter genug übrig lässt
        fetch_limit = max(self.max_departures * 4, 30)
        params = {
            "outputFormat": "JSON",
            "language": "de",
            "type_dm": "stop",
            "name_dm": self.stop_id,
            "useRealtime": "1",
            "limit": str(fetch_limit),
            "mode": "direct",
            "deleteAssignedStops": "1",
            "ptOptionsActive": "1",
        }
        try:
            async with session.get(
                f"{EFA_BASE_URL}{EFA_DM_ENDPOINT}",
                params=params,
                timeout=_timeout(10),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"EFA-Fehler: {err}") from err

        return _parse_efa(data)

    # ------------------------------------------------------------------ #
    #  DB / IRIS (Züge)                                                   #
    # ------------------------------------------------------------------ #

    async def _fetch_db(self) -> list[dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{MARUDOR_BASE_URL}{MARUDOR_DEPARTURES_ENDPOINT}/{self.stop_id}",
                params={"lookahead": "120"},
                headers={"Accept": "application/json"},
                timeout=_timeout(10),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"DB/IRIS-Fehler: {err}") from err

        return _parse_db(data)


# ------------------------------------------------------------------ #
#  Filter                                                             #
# ------------------------------------------------------------------ #

def _apply_filters(
    departures: list[dict[str, Any]],
    line_filter: list[str],
    direction_filter: list[str],
) -> list[dict[str, Any]]:
    if line_filter:
        departures = [d for d in departures if d.get("line") in line_filter]
    if direction_filter:
        # Teilstring-Match (case-insensitiv) damit Varianten wie
        # "Aschaffenburg, Hauptbahnhof" auf "Hauptbahnhof" matchen
        departures = [
            d
            for d in departures
            if any(
                f.lower() in d.get("direction", "").lower()
                for f in direction_filter
            )
        ]
    return departures


# ------------------------------------------------------------------ #
#  Parser                                                             #
# ------------------------------------------------------------------ #

def _parse_efa(data: dict) -> list[dict[str, Any]]:
    raw = data.get("departureList", [])
    if isinstance(raw, dict):
        raw = [raw]

    now = datetime.now()
    departures: list[dict[str, Any]] = []

    for dep in raw:
        try:
            planned = _parse_efa_datetime(dep.get("dateTime", {}))
            realtime = _parse_efa_datetime(dep.get("realDateTime", {}))
            effective = realtime or planned
            if effective is None:
                continue

            line = dep.get("servingLine", {})

            # Delay: EFA liefert es direkt in servingLine.delay (Minuten als String),
            # als Fallback berechnen wir es aus planned vs realDateTime.
            raw_delay = line.get("delay")
            if raw_delay is not None:
                delay = int(raw_delay)
            elif planned and realtime:
                delay = int((realtime - planned).total_seconds() / 60)
            else:
                delay = 0

            # realtimeTripStatus: "MONITORED" = live getrackt, "PLANNED" = kein Signal
            rt_status = dep.get("realtimeTripStatus", "UNKNOWN")
            monitored = rt_status == "MONITORED"

            minutes_until = int((effective - now).total_seconds() / 60)

            departures.append(
                {
                    "line": line.get("number") or line.get("symbol", "?"),
                    "direction": line.get("direction", ""),
                    "platform": dep.get("platformName", dep.get("platform", "")),
                    "planned": planned.isoformat() if planned else None,
                    "realtime": realtime.isoformat() if realtime else None,
                    "effective": effective.isoformat(),
                    "delay_minutes": delay,
                    "minutes_until": minutes_until,
                    "monitored": monitored,
                    "rt_status": rt_status,
                    "source": SOURCE_EFA,
                }
            )
        except (KeyError, ValueError, TypeError):
            continue

    departures = [d for d in departures if d["minutes_until"] >= -1]
    departures.sort(key=lambda x: x["minutes_until"])
    return departures


def _parse_db(data: dict) -> list[dict[str, Any]]:
    now = datetime.now()
    departures: list[dict[str, Any]] = []

    for dep in data.get("departures", []):
        try:
            time_info = dep.get("departure", dep)
            planned = _parse_iso_ms(time_info.get("scheduledTime"))
            realtime = _parse_iso_ms(time_info.get("time"))
            effective = realtime or planned
            if effective is None:
                continue

            delay = 0
            if planned and realtime:
                delay = int((realtime - planned).total_seconds() / 60)

            minutes_until = int((effective - now).total_seconds() / 60)
            train = dep.get("train", {})

            departures.append(
                {
                    "line": train.get("number", "?"),
                    "direction": dep.get("destination", ""),
                    "planned": planned.isoformat() if planned else None,
                    "realtime": realtime.isoformat() if realtime else None,
                    "effective": effective.isoformat(),
                    "delay_minutes": delay,
                    "minutes_until": minutes_until,
                    "is_realtime": realtime is not None,
                    "source": SOURCE_DB,
                }
            )
        except (KeyError, ValueError, TypeError):
            continue

    departures = [d for d in departures if d["minutes_until"] >= -1]
    departures.sort(key=lambda x: x["minutes_until"])
    return departures


# ------------------------------------------------------------------ #
#  Zeithelfer                                                         #
# ------------------------------------------------------------------ #

def _parse_efa_datetime(dt: dict) -> datetime | None:
    if not dt or not dt.get("year"):
        return None
    try:
        return datetime(
            year=int(dt["year"]),
            month=int(dt["month"]),
            day=int(dt["day"]),
            hour=int(dt["hour"]),
            minute=int(dt["minute"]),
        )
    except (KeyError, ValueError, TypeError):
        return None


def _parse_iso_ms(value: str | int | None) -> datetime | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, OSError):
        return None


def _timeout(seconds: int):
    import aiohttp
    return aiohttp.ClientTimeout(total=seconds)

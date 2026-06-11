from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    EFA_BASE_URL,
    EFA_DM_ENDPOINT,
    EFA_SF_ENDPOINT,
    MARUDOR_BASE_URL,
    MARUDOR_DEPARTURES_ENDPOINT,
    USER_AGENT,
)
from .utils import normalize_direction

_LOGGER = logging.getLogger(__name__)
_HEADERS = {"User-Agent": USER_AGENT}
_TIMEOUT = aiohttp.ClientTimeout(total=10)


# ──────────────────────────────────────────────────────────────────────────────
#  Stop search
# ──────────────────────────────────────────────────────────────────────────────

async def efa_stop_search(
    session: aiohttp.ClientSession, query: str
) -> list[dict[str, str]]:
    params = {
        "outputFormat": "JSON",
        "language": "de",
        "type_sf": "any",
        "name_sf": query,
        "coordOutputFormat": "WGS84[dd.ddddd]",
        "anyObjFilter_sf": "2",
    }
    try:
        async with session.get(
            f"{EFA_BASE_URL}{EFA_SF_ENDPOINT}",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
    except Exception as err:
        _LOGGER.warning("EFA stop search failed: %s", err)
        return []

    sf = data.get("stopFinder", {})
    points = sf.get("points", {})
    if isinstance(points, dict):
        raw = points.get("point", [])
        point_list = [raw] if isinstance(raw, dict) else raw
    elif isinstance(points, list):
        point_list = points
    else:
        return []

    stops = []
    for p in point_list:
        ref = p.get("ref", {})
        stop_id = ref.get("id") or p.get("stateless") or p.get("id", "")
        name = p.get("name", "")
        place = ref.get("place", p.get("place", ""))
        if stop_id and name:
            stops.append({"id": stop_id, "name": name, "place": place})
    return stops


async def db_stop_search(
    session: aiohttp.ClientSession, query: str
) -> list[dict[str, str]]:
    try:
        async with session.get(
            "https://marudor.de/api/hafas/v3/stations",
            params={"searchTerm": query},
            headers={"Accept": "application/json", **_HEADERS},
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
    except Exception as err:
        _LOGGER.warning("DB station search failed: %s", err)
        return []

    stops = []
    for station in data if isinstance(data, list) else []:
        eva = str(station.get("evaNumber") or station.get("eva", ""))
        name = station.get("name", "")
        if eva and name:
            stops.append({"id": eva, "name": name, "place": ""})
    return stops


# ──────────────────────────────────────────────────────────────────────────────
#  Departure fetching (raw API response)
# ──────────────────────────────────────────────────────────────────────────────

async def efa_fetch_raw(
    session: aiohttp.ClientSession,
    stop_id: str,
    limit: int,
    itd_date: str | None = None,
    itd_time: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "outputFormat": "JSON",
        "language": "de",
        "type_dm": "stop",
        "name_dm": stop_id,
        "useRealtime": "1",
        "limit": str(limit),
        "mode": "direct",
        "deleteAssignedStops": "1",
        "ptOptionsActive": "1",
    }
    if itd_date:
        params["itdDate"] = itd_date
    if itd_time:
        params["itdTime"] = itd_time

    async with session.get(
        f"{EFA_BASE_URL}{EFA_DM_ENDPOINT}",
        params=params,
        headers=_HEADERS,
        timeout=_TIMEOUT,
    ) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)

    raw = data.get("departureList") or []
    if isinstance(raw, dict):
        raw = [raw]
    return raw


async def db_fetch_raw(
    session: aiohttp.ClientSession,
    stop_id: str,
    lookahead: int,
) -> list[dict[str, Any]]:
    async with session.get(
        f"{MARUDOR_BASE_URL}{MARUDOR_DEPARTURES_ENDPOINT}/{stop_id}",
        params={"lookahead": str(lookahead)},
        headers={"Accept": "application/json", **_HEADERS},
        timeout=_TIMEOUT,
    ) as resp:
        resp.raise_for_status()
        return (await resp.json(content_type=None)).get("departures", [])


# ──────────────────────────────────────────────────────────────────────────────
#  Filter options (line → directions mapping)
# ──────────────────────────────────────────────────────────────────────────────

async def efa_line_directions(
    session: aiohttp.ClientSession,
    stop_id: str,
    limit: int = 60,
) -> dict[str, list[str]]:
    """Return {line: [directions]} for building filter selectors."""
    params = {
        "outputFormat": "JSON",
        "language": "de",
        "type_dm": "stop",
        "name_dm": stop_id,
        "useRealtime": "0",
        "limit": str(limit),
        "mode": "direct",
        "deleteAssignedStops": "1",
        "ptOptionsActive": "1",
    }
    try:
        async with session.get(
            f"{EFA_BASE_URL}{EFA_DM_ENDPOINT}",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
    except Exception as err:
        _LOGGER.warning("Could not load filter options for stop %s: %s", stop_id, err)
        return {}

    raw = data.get("departureList") or []
    if isinstance(raw, dict):
        raw = [raw]

    line_dirs: dict[str, set[str]] = {}
    for dep in raw:
        info = dep.get("servingLine", {})
        ln = (info.get("number") or info.get("symbol", "")).strip()
        direction = normalize_direction(info.get("direction", ""))
        if ln:
            line_dirs.setdefault(ln, set())
            if direction:
                line_dirs[ln].add(direction)

    return {ln: sorted(dirs) for ln, dirs in sorted(
        line_dirs.items(), key=lambda kv: (not kv[0].isdigit(), kv[0].zfill(5) if kv[0].isdigit() else kv[0])
    )}

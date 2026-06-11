from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_DIRECTION_FILTER,
    CONF_LINE_FILTER,
    CONF_MAX_DEPARTURES,
    CONF_SOURCE,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_WALK_TIME,
    DEFAULT_DEPARTURES,
    DOMAIN,
    EFA_BASE_URL,
    EFA_DM_ENDPOINT,
    EFA_SF_ENDPOINT,
    SOURCE_DB,
    SOURCE_EFA,
    USER_AGENT,
)

_HEADERS = {"User-Agent": USER_AGENT}

_LOGGER = logging.getLogger(__name__)

_SOURCE_OPTIONS = [
    SelectOptionDict(value=SOURCE_EFA, label="Bus / Tram  (EFA Bahnland Bayern)"),
    SelectOptionDict(value=SOURCE_DB, label="Zug  (DB / IRIS Echtzeit)"),
]


class VabConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "VabOptionsFlow":
        return VabOptionsFlow(config_entry)

    def __init__(self) -> None:
        self._stops: list[dict[str, str]] = []
        self._source: str = SOURCE_EFA
        self._selected_stop_id: str = ""
        self._selected_stop_name: str = ""
        self._max_departures: int = DEFAULT_DEPARTURES
        self._available_lines: list[str] = []
        self._available_directions: list[str] = []

    # ------------------------------------------------------------------ #
    #  Schritt 1 – Datenquelle + Haltestellensuche                        #
    # ------------------------------------------------------------------ #

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._source = user_input[CONF_SOURCE]
            query = user_input["stop_search"].strip()

            if self._source == SOURCE_EFA:
                stops = await self._search_efa_stops(query)
            else:
                stops = await self._search_db_stops(query)

            if stops:
                self._stops = stops
                return await self.async_step_select_stop()
            errors["base"] = "no_stops_found"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE, default=SOURCE_EFA): SelectSelector(
                        SelectSelectorConfig(options=_SOURCE_OPTIONS)
                    ),
                    vol.Required("stop_search"): TextSelector(),
                }
            ),
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    #  Schritt 2 – Haltestelle auswählen + Anzahl Abfahrten               #
    # ------------------------------------------------------------------ #

    async def async_step_select_stop(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._selected_stop_id = user_input[CONF_STOP_ID]
            self._selected_stop_name = next(
                (s["name"] for s in self._stops if s["id"] == self._selected_stop_id),
                self._selected_stop_id,
            )
            self._max_departures = int(
                user_input.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES)
            )
            # Live-Abfahrten laden um Linien & Richtungen zu ermitteln
            await self._load_filter_options()
            return await self.async_step_filters()

        options = [
            SelectOptionDict(
                value=s["id"],
                label=s["name"] + (f" ({s['place']})" if s.get("place") else ""),
            )
            for s in self._stops
        ]

        return self.async_show_form(
            step_id="select_stop",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_ID): SelectSelector(
                        SelectSelectorConfig(options=options)
                    ),
                    vol.Optional(
                        CONF_MAX_DEPARTURES, default=DEFAULT_DEPARTURES
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1, max=20, step=1, mode=NumberSelectorMode.BOX
                        )
                    ),
                }
            ),
        )

    # ------------------------------------------------------------------ #
    #  Schritt 3 – Linien- und Richtungsfilter                            #
    # ------------------------------------------------------------------ #

    async def async_step_filters(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            line_filter: list[str] = user_input.get(CONF_LINE_FILTER, [])
            direction_filter: list[str] = user_input.get(CONF_DIRECTION_FILTER, [])
            walk_time: int = int(user_input.get(CONF_WALK_TIME, 0))

            title = _build_entry_title(
                self._selected_stop_name, line_filter, direction_filter
            )

            unique_id = "_".join(
                filter(
                    None,
                    [
                        self._source,
                        self._selected_stop_id,
                        ",".join(sorted(line_filter)),
                        ",".join(sorted(direction_filter)),
                    ],
                )
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=title,
                data={
                    CONF_STOP_ID: self._selected_stop_id,
                    CONF_STOP_NAME: self._selected_stop_name,
                    CONF_MAX_DEPARTURES: self._max_departures,
                    CONF_SOURCE: self._source,
                    CONF_LINE_FILTER: line_filter,
                    CONF_DIRECTION_FILTER: direction_filter,
                    CONF_WALK_TIME: walk_time,
                },
            )

        line_options = [
            SelectOptionDict(value=ln, label=f"Linie {ln}") for ln in self._available_lines
        ]
        direction_options = [
            SelectOptionDict(value=d, label=d) for d in self._available_directions
        ]

        schema: dict = {}
        if line_options:
            schema[vol.Optional(CONF_LINE_FILTER, default=[])] = SelectSelector(
                SelectSelectorConfig(
                    options=line_options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            )
        if direction_options:
            schema[vol.Optional(CONF_DIRECTION_FILTER, default=[])] = SelectSelector(
                SelectSelectorConfig(
                    options=direction_options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            )
        schema[vol.Optional(CONF_WALK_TIME, default=0)] = NumberSelector(
            NumberSelectorConfig(min=0, max=30, step=1, mode=NumberSelectorMode.BOX)
        )

        if not schema or list(schema.keys()) == [list(schema.keys())[-1]]:
            # Keine Live-Daten verfügbar – Sensor ohne Filter anlegen
            return await self.async_step_filters(user_input={})

        return self.async_show_form(
            step_id="filters",
            data_schema=vol.Schema(schema),
            description_placeholders={"stop_name": self._selected_stop_name},
        )

    # ------------------------------------------------------------------ #
    #  Hilfsmethoden                                                       #
    # ------------------------------------------------------------------ #

    async def _load_filter_options(self) -> None:
        """Lädt eine Batch-Abfahrtsliste um Linien+Richtungen zu extrahieren."""
        session = async_get_clientsession(self.hass)
        params = {
            "outputFormat": "JSON",
            "language": "de",
            "type_dm": "stop",
            "name_dm": self._selected_stop_id,
            "useRealtime": "0",
            "limit": "30",
            "mode": "direct",
            "deleteAssignedStops": "1",
            "ptOptionsActive": "1",
        }
        try:
            async with session.get(
                f"{EFA_BASE_URL}{EFA_DM_ENDPOINT}", params=params, headers=_HEADERS
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            _LOGGER.warning("Konnte Filteroptionen nicht laden: %s", err)
            return

        raw = data.get("departureList") or []
        if isinstance(raw, dict):
            raw = [raw]

        lines: set[str] = set()
        directions: set[str] = set()
        for dep in raw:
            line_info = dep.get("servingLine", {})
            ln = line_info.get("number") or line_info.get("symbol", "")
            direction = line_info.get("direction", "")
            if ln:
                lines.add(ln.strip())
            if direction:
                directions.add(direction.strip())

        self._available_lines = sorted(lines, key=lambda x: (not x.isdigit(), x))
        self._available_directions = sorted(directions)

    async def _search_efa_stops(self, query: str) -> list[dict[str, str]]:
        session = async_get_clientsession(self.hass)
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
                f"{EFA_BASE_URL}{EFA_SF_ENDPOINT}", params=params, headers=_HEADERS
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

    async def _search_db_stops(self, query: str) -> list[dict[str, str]]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                "https://marudor.de/api/hafas/v3/stations",
                params={"searchTerm": query},
                headers={"Accept": "application/json", **_HEADERS},
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


def _build_entry_title(
    stop_name: str,
    line_filter: list[str],
    direction_filter: list[str],
) -> str:
    parts = [stop_name]
    if direction_filter:
        parts.append("→ " + " / ".join(direction_filter))
    if line_filter:
        parts.append("(" + ", ".join(f"Linie {ln}" for ln in line_filter) + ")")
    return " ".join(parts)


class VabOptionsFlow(config_entries.OptionsFlow):
    """Erlaubt nachträgliches Ändern von Linien, Richtungen und Anzahl."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._available_lines: list[str] = []
        self._available_directions: list[str] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            line_filter: list[str] = user_input.get(CONF_LINE_FILTER, [])
            direction_filter: list[str] = user_input.get(CONF_DIRECTION_FILTER, [])
            max_dep = int(user_input.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES))
            walk_time = int(user_input.get(CONF_WALK_TIME, 0))

            new_title = _build_entry_title(
                self._entry.data[CONF_STOP_NAME], line_filter, direction_filter
            )
            self.hass.config_entries.async_update_entry(
                self._entry,
                title=new_title,
                data={**self._entry.data, CONF_LINE_FILTER: line_filter,
                      CONF_DIRECTION_FILTER: direction_filter,
                      CONF_MAX_DEPARTURES: max_dep,
                      CONF_WALK_TIME: walk_time},
            )
            return self.async_create_entry(title=new_title, data={})

        await self._load_filter_options()

        current_lines = self._entry.data.get(CONF_LINE_FILTER, [])
        current_directions = self._entry.data.get(CONF_DIRECTION_FILTER, [])
        current_max = self._entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES)
        current_walk = self._entry.data.get(CONF_WALK_TIME, 0)

        line_options = [
            SelectOptionDict(value=ln, label=f"Linie {ln}") for ln in self._available_lines
        ]
        direction_options = [
            SelectOptionDict(value=d, label=d) for d in self._available_directions
        ]

        schema: dict = {
            vol.Optional(CONF_MAX_DEPARTURES, default=current_max): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        }
        if line_options:
            schema[vol.Optional(CONF_LINE_FILTER, default=current_lines)] = SelectSelector(
                SelectSelectorConfig(
                    options=line_options, multiple=True, mode=SelectSelectorMode.LIST
                )
            )
        if direction_options:
            schema[vol.Optional(CONF_DIRECTION_FILTER, default=current_directions)] = (
                SelectSelector(
                    SelectSelectorConfig(
                        options=direction_options, multiple=True, mode=SelectSelectorMode.LIST
                    )
                )
            )
        schema[vol.Optional(CONF_WALK_TIME, default=current_walk)] = NumberSelector(
            NumberSelectorConfig(min=0, max=30, step=1, mode=NumberSelectorMode.BOX)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            description_placeholders={"stop_name": self._entry.data[CONF_STOP_NAME]},
        )

    async def _load_filter_options(self) -> None:
        session = async_get_clientsession(self.hass)
        params = {
            "outputFormat": "JSON",
            "language": "de",
            "type_dm": "stop",
            "name_dm": self._entry.data[CONF_STOP_ID],
            "useRealtime": "0",
            "limit": "30",
            "mode": "direct",
            "deleteAssignedStops": "1",
            "ptOptionsActive": "1",
        }
        try:
            async with session.get(
                f"{EFA_BASE_URL}{EFA_DM_ENDPOINT}", params=params, headers=_HEADERS
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            _LOGGER.warning("OptionsFlow: Filteroptionen nicht ladbar: %s", err)
            return

        raw = data.get("departureList") or []
        if isinstance(raw, dict):
            raw = [raw]

        lines: set[str] = set()
        directions: set[str] = set()
        for dep in raw:
            line_info = dep.get("servingLine", {})
            ln = line_info.get("number") or line_info.get("symbol", "")
            direction = line_info.get("direction", "")
            if ln:
                lines.add(ln.strip())
            if direction:
                directions.add(direction.strip())

        self._available_lines = sorted(lines, key=lambda x: (not x.isdigit(), x))
        self._available_directions = sorted(directions)

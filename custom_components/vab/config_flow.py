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

from .api import efa_line_directions, efa_stop_search
from .const import (
    CONF_DIRECTION_FILTER,
    CONF_LINE_FILTER,
    CONF_MAX_DEPARTURES,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_WALK_TIME,
    DEFAULT_DEPARTURES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class VabConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "VabOptionsFlow":
        return VabOptionsFlow(config_entry)

    def __init__(self) -> None:
        self._stops: list[dict[str, str]] = []
        self._selected_stop_id: str = ""
        self._selected_stop_name: str = ""
        self._max_departures: int = DEFAULT_DEPARTURES
        self._walk_time: int = 0
        self._available_lines: list[str] = []
        self._line_directions: dict[str, list[str]] = {}
        self._selected_lines: list[str] = []

    # ── Step 1: source + stop search ─────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            query = user_input["stop_search"].strip()
            session = async_get_clientsession(self.hass)
            stops = await efa_stop_search(session, query)

            if stops:
                self._stops = stops
                return await self.async_step_select_stop()
            errors["base"] = "no_stops_found"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("stop_search"): TextSelector(),
            }),
            errors=errors,
        )

    # ── Step 2: pick stop + max departures ───────────────────────────────────

    async def async_step_select_stop(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._selected_stop_id = user_input[CONF_STOP_ID]
            self._selected_stop_name = next(
                (s["name"] for s in self._stops if s["id"] == self._selected_stop_id),
                self._selected_stop_id,
            )
            self._max_departures = int(user_input.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES))
            await self._load_line_directions()
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
            data_schema=vol.Schema({
                vol.Required(CONF_STOP_ID): SelectSelector(
                    SelectSelectorConfig(options=options)
                ),
                vol.Optional(CONF_MAX_DEPARTURES, default=DEFAULT_DEPARTURES): NumberSelector(
                    NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
            }),
        )

    # ── Step 3: line filter + walk time ──────────────────────────────────────

    async def async_step_filters(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._selected_lines = user_input.get(CONF_LINE_FILTER, [])
            self._walk_time = int(user_input.get(CONF_WALK_TIME, 0))
            return await self.async_step_directions()

        if not self._available_lines:
            return await self.async_step_filters(user_input={})

        line_options = [SelectOptionDict(value=ln, label=f"Linie {ln}") for ln in self._available_lines]
        return self.async_show_form(
            step_id="filters",
            data_schema=vol.Schema({
                vol.Optional(CONF_LINE_FILTER, default=[]): SelectSelector(
                    SelectSelectorConfig(options=line_options, multiple=True, mode=SelectSelectorMode.LIST)
                ),
                vol.Optional(CONF_WALK_TIME, default=0): NumberSelector(
                    NumberSelectorConfig(min=0, max=30, step=1, mode=NumberSelectorMode.BOX)
                ),
            }),
            description_placeholders={"stop_name": self._selected_stop_name},
        )

    # ── Step 4: direction filter ──────────────────────────────────────────────

    async def async_step_directions(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            direction_filter: list[str] = user_input.get(CONF_DIRECTION_FILTER, [])
            line_filter = self._selected_lines

            title = _build_entry_title(self._selected_stop_name, line_filter, direction_filter)
            unique_id = "_".join(filter(None, [
                self._selected_stop_id,
                ",".join(sorted(line_filter)),
                ",".join(sorted(direction_filter)),
            ]))
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=title,
                data={
                    CONF_STOP_ID: self._selected_stop_id,
                    CONF_STOP_NAME: self._selected_stop_name,
                    CONF_MAX_DEPARTURES: self._max_departures,
                    CONF_LINE_FILTER: line_filter,
                    CONF_DIRECTION_FILTER: direction_filter,
                    CONF_WALK_TIME: self._walk_time,
                },
            )

        direction_list = _directions_for_lines(self._line_directions, self._selected_lines)
        if not direction_list:
            return await self.async_step_directions(user_input={})

        return self.async_show_form(
            step_id="directions",
            data_schema=vol.Schema({
                vol.Optional(CONF_DIRECTION_FILTER, default=[]): SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=d, label=d) for d in direction_list],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            description_placeholders={"stop_name": self._selected_stop_name},
        )

    async def _load_line_directions(self) -> None:
        session = async_get_clientsession(self.hass)
        self._line_directions = await efa_line_directions(session, self._selected_stop_id)
        self._available_lines = list(self._line_directions.keys())


# ──────────────────────────────────────────────────────────────────────────────
#  Options flow
# ──────────────────────────────────────────────────────────────────────────────

class VabOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._available_lines: list[str] = []
        self._line_directions: dict[str, list[str]] = {}
        self._selected_lines: list[str] = []
        self._max_dep: int = DEFAULT_DEPARTURES
        self._walk_time: int = 0

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._selected_lines = user_input.get(CONF_LINE_FILTER, [])
            self._max_dep = int(user_input.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES))
            self._walk_time = int(user_input.get(CONF_WALK_TIME, 0))
            return await self.async_step_directions()

        session = async_get_clientsession(self.hass)
        self._line_directions = await efa_line_directions(
            session, self._entry.data[CONF_STOP_ID]
        )
        self._available_lines = list(self._line_directions.keys())

        current_lines = self._entry.data.get(CONF_LINE_FILTER, [])
        current_max = self._entry.data.get(CONF_MAX_DEPARTURES, DEFAULT_DEPARTURES)
        current_walk = self._entry.data.get(CONF_WALK_TIME, 0)

        line_options = [SelectOptionDict(value=ln, label=f"Linie {ln}") for ln in self._available_lines]
        schema: dict = {
            vol.Optional(CONF_MAX_DEPARTURES, default=current_max): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        }
        if line_options:
            schema[vol.Optional(CONF_LINE_FILTER, default=current_lines)] = SelectSelector(
                SelectSelectorConfig(options=line_options, multiple=True, mode=SelectSelectorMode.LIST)
            )
        schema[vol.Optional(CONF_WALK_TIME, default=current_walk)] = NumberSelector(
            NumberSelectorConfig(min=0, max=30, step=1, mode=NumberSelectorMode.BOX)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            description_placeholders={"stop_name": self._entry.data[CONF_STOP_NAME]},
        )

    async def async_step_directions(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            direction_filter: list[str] = user_input.get(CONF_DIRECTION_FILTER, [])
            new_title = _build_entry_title(
                self._entry.data[CONF_STOP_NAME], self._selected_lines, direction_filter
            )
            self.hass.config_entries.async_update_entry(
                self._entry,
                title=new_title,
                data={
                    **self._entry.data,
                    CONF_LINE_FILTER: self._selected_lines,
                    CONF_DIRECTION_FILTER: direction_filter,
                    CONF_MAX_DEPARTURES: self._max_dep,
                    CONF_WALK_TIME: self._walk_time,
                },
            )
            return self.async_create_entry(title=new_title, data={})

        direction_list = _directions_for_lines(self._line_directions, self._selected_lines)
        if not direction_list:
            return await self.async_step_directions(user_input={})

        current_directions = self._entry.data.get(CONF_DIRECTION_FILTER, [])
        valid_current = [d for d in current_directions if d in direction_list]

        return self.async_show_form(
            step_id="directions",
            data_schema=vol.Schema({
                vol.Optional(CONF_DIRECTION_FILTER, default=valid_current): SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=d, label=d) for d in direction_list],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            description_placeholders={"stop_name": self._entry.data[CONF_STOP_NAME]},
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Shared helpers
# ──────────────────────────────────────────────────────────────────────────────

def _directions_for_lines(
    line_directions: dict[str, list[str]],
    selected_lines: list[str],
) -> list[str]:
    if selected_lines:
        dirs: set[str] = set()
        for ln in selected_lines:
            dirs.update(line_directions.get(ln, []))
        return sorted(dirs)
    return sorted({d for dirs in line_directions.values() for d in dirs})


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

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DIRECTION_FILTER,
    CONF_LINE_FILTER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_WALK_TIME,
    DOMAIN,
)
from .coordinator import VabCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VabCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VabDepartureSensor(coordinator, entry)])


class VabDepartureSensor(CoordinatorEntity[VabCoordinator], SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:bus-clock"

    def __init__(self, coordinator: VabCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

        stop_name = entry.data[CONF_STOP_NAME]
        line_filter: list[str] = entry.data.get(CONF_LINE_FILTER, [])
        direction_filter: list[str] = entry.data.get(CONF_DIRECTION_FILTER, [])

        self._attr_name = _build_sensor_name(stop_name, line_filter, direction_filter)
        self._attr_unique_id = (
            f"vab_{entry.data[CONF_STOP_ID]}"
            f"_l{'_'.join(sorted(line_filter))}"
            f"_d{'_'.join(sorted(direction_filter))}"
        )

    @property
    def native_value(self) -> int | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data[0]["minutes_until"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or []
        nxt = data[0] if data else None
        walk_time = self._entry.data.get(CONF_WALK_TIME, 0)
        return {
            "next_line": nxt["line"] if nxt else None,
            "next_direction": nxt["direction"] if nxt else None,
            "next_platform": nxt.get("platform") if nxt else None,
            "next_delay_minutes": nxt["delay_minutes"] if nxt else None,
            "next_monitored": nxt.get("monitored") if nxt else None,
            "next_rt_status": nxt.get("rt_status") if nxt else None,
            "leave_in_minutes": nxt.get("leave_in_minutes") if nxt else None,
            "departures": data,
            "stop_id": self._entry.data[CONF_STOP_ID],
            "stop_name": self._entry.data[CONF_STOP_NAME],
            "line_filter": self._entry.data.get(CONF_LINE_FILTER, []),
            "direction_filter": self._entry.data.get(CONF_DIRECTION_FILTER, []),
            "walk_time": walk_time,
            "source": "efa",
        }


def _build_sensor_name(
    stop_name: str,
    line_filter: list[str],
    direction_filter: list[str],
) -> str:
    parts = [f"Abfahrt {stop_name}"]
    if direction_filter:
        parts.append("→ " + " / ".join(direction_filter))
    if line_filter:
        parts.append("(" + ", ".join(line_filter) + ")")
    return " ".join(parts)

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import (
    DEFAULT_LEAVE_THRESHOLD,
    DOMAIN,
    SERVICE_UNWATCH_DEPARTURE,
    SERVICE_WATCH_DEPARTURE,
)
from .coordinator import VabCoordinator
from .watches import WatchManager

PLATFORMS: list[Platform] = [Platform.SENSOR]

WATCH_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("line"): str,
    vol.Required("direction"): str,
    vol.Required("planned"): str,
    vol.Optional("notify_service"): str,
    vol.Optional("leave_threshold", default=DEFAULT_LEAVE_THRESHOLD): vol.Coerce(int),
})

UNWATCH_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("line"): str,
    vol.Required("direction"): str,
    vol.Required("planned"): str,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})

    if "_watch_manager" not in domain_data:
        watch_manager = WatchManager(hass)
        await watch_manager.async_load()
        domain_data["_watch_manager"] = watch_manager
        _async_register_services(hass, watch_manager)

    coordinator = VabCoordinator(hass, entry, domain_data["_watch_manager"])
    await coordinator.async_config_entry_first_refresh()

    domain_data[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.add_update_listener(_async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not any(k != "_watch_manager" for k in hass.data[DOMAIN]):
            hass.data[DOMAIN].pop("_watch_manager")
            hass.services.async_remove(DOMAIN, SERVICE_WATCH_DEPARTURE)
            hass.services.async_remove(DOMAIN, SERVICE_UNWATCH_DEPARTURE)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant, watch_manager: WatchManager) -> None:
    def _resolve_entry_id(entity_id: str) -> str:
        entity = er.async_get(hass).async_get(entity_id)
        if entity is None or entity.config_entry_id is None:
            raise HomeAssistantError(f"Unknown vab entity: {entity_id}")
        return entity.config_entry_id

    async def _handle_watch(call: ServiceCall) -> None:
        entry_id = _resolve_entry_id(call.data["entity_id"])
        await watch_manager.async_add(
            entry_id,
            call.data["line"],
            call.data["direction"],
            call.data["planned"],
            call.data.get("notify_service"),
            call.data["leave_threshold"],
        )

    async def _handle_unwatch(call: ServiceCall) -> None:
        entry_id = _resolve_entry_id(call.data["entity_id"])
        await watch_manager.async_remove(
            entry_id,
            call.data["line"],
            call.data["direction"],
            call.data["planned"],
        )

    hass.services.async_register(DOMAIN, SERVICE_WATCH_DEPARTURE, _handle_watch, schema=WATCH_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNWATCH_DEPARTURE, _handle_unwatch, schema=UNWATCH_SCHEMA)

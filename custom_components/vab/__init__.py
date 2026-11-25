from __future__ import annotations

import os

import voluptuous as vol
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import (
    DEFAULT_LEAVE_THRESHOLD,
    DOMAIN,
    SERVICE_UNWATCH_DEPARTURE,
    SERVICE_WATCH_DEPARTURE,
)
from .coordinator import VabCoordinator
from .watches import WatchManager

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type VabConfigEntry = ConfigEntry[VabCoordinator]

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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up what is shared by all entries: watches, actions and the bundled card."""
    watch_manager = WatchManager(hass)
    await watch_manager.async_load()
    hass.data[DOMAIN] = watch_manager
    _async_register_services(hass, watch_manager)

    # The VAB Departures Card ships inside this repo instead of as a separate
    # HACS listing (see #27); the version query busts the browser cache.
    integration = await async_get_integration(hass, DOMAIN)
    www_path = os.path.join(os.path.dirname(__file__), "www")
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}/www", www_path, cache_headers=False)]
    )
    add_extra_js_url(hass, f"/{DOMAIN}/www/vab-departures-card.js?v={integration.version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VabConfigEntry) -> bool:
    coordinator = VabCoordinator(hass, entry, hass.data[DOMAIN])
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VabConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: VabConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant, watch_manager: WatchManager) -> None:
    def _resolve_entry_id(entity_id: str) -> str:
        entity = er.async_get(hass).async_get(entity_id)
        if entity is None or entity.config_entry_id is None or entity.platform != DOMAIN:
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

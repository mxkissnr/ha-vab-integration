"""Stub out homeassistant imports so pure-function tests run without a full HA install."""
import sys
from types import ModuleType
from unittest.mock import MagicMock


def _mock_module(*path_parts: str) -> None:
    """Register a MagicMock for a dotted module path and all its parents."""
    full = ""
    for part in path_parts:
        full = f"{full}.{part}" if full else part
        if full not in sys.modules:
            sys.modules[full] = MagicMock()


for mod in [
    "homeassistant",
    "homeassistant.components",
    "homeassistant.components.persistent_notification",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.config_validation",
    "homeassistant.helpers.entity_registry",
    "homeassistant.helpers.storage",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.selector",
    "voluptuous",
    "aiohttp",
]:
    _mock_module(*mod.split("."))

# Store needs to be a real class so watches.py can subscript it (Store[dict[str, Any]])
class _FakeStore:
    def __init__(self, hass, version, key) -> None:
        pass

    def __class_getitem__(cls, item):
        return cls

    async def async_load(self):
        return None

    async def async_save(self, data) -> None:
        pass

sys.modules["homeassistant.helpers.storage"].Store = _FakeStore
sys.modules["homeassistant.exceptions"].HomeAssistantError = type("HomeAssistantError", (Exception,), {})

# DataUpdateCoordinator needs to be a real base class so VabCoordinator can inherit from it
class _FakeCoordinator:
    def __init__(self, hass, logger, *, name, update_interval):
        pass

    def __class_getitem__(cls, item):
        return cls

_FakeCoordinator.__class_getitem__ = classmethod(lambda cls, item: cls)

sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = _FakeCoordinator
sys.modules["homeassistant.helpers.update_coordinator"].UpdateFailed = Exception

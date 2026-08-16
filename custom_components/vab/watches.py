"""Server-side departure watches with persistent storage and notifications."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DEFAULT_LEAVE_THRESHOLD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}_watches"
STORAGE_VERSION = 1


def watch_key(line: str, direction: str, planned: str) -> str:
    # Same key format the Lovelace card uses for its stars
    return f"{line}|{direction}|{planned}"


def _leave_urgency(leave_mins: int) -> str:
    if leave_mins <= 0:
        return "Sofort losrennen! Du verpasst sonst den Bus."
    if leave_mins == 1:
        return "In 1 Minute losgehen!"
    return f"Noch {leave_mins} Minuten — jetzt losgehen!"


def _fmt_time(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M")
    except ValueError:
        return ""


class WatchManager:
    """Holds all watches across config entries, persists them, sends notifications."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._watches: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        data = await self._store.async_load()
        self._watches = (data or {}).get("watches", [])

    async def _async_save(self) -> None:
        await self._store.async_save({"watches": self._watches})

    def keys_for_entry(self, entry_id: str) -> list[str]:
        return [
            watch_key(w["line"], w["direction"], w["planned"])
            for w in self._watches
            if w["entry_id"] == entry_id
        ]

    def _find(self, entry_id: str, line: str, direction: str, planned: str) -> dict[str, Any] | None:
        for w in self._watches:
            if (
                w["entry_id"] == entry_id
                and w["line"] == line
                and w["direction"] == direction
                and w["planned"] == planned
            ):
                return w
        return None

    async def async_add(
        self,
        entry_id: str,
        line: str,
        direction: str,
        planned: str,
        notify_service: str | None,
        leave_threshold: int,
    ) -> None:
        if self._find(entry_id, line, direction, planned):
            return
        self._watches.append(
            {
                "entry_id": entry_id,
                "line": line,
                "direction": direction,
                "planned": planned,
                "notify_service": notify_service,
                "leave_threshold": leave_threshold,
                "notified_leave": False,
                "notified_delay": 0,
            }
        )
        await self._async_save()

    async def async_remove(self, entry_id: str, line: str, direction: str, planned: str) -> None:
        watch = self._find(entry_id, line, direction, planned)
        if watch is None:
            return
        self._watches.remove(watch)
        await self._async_save()
        self._dismiss(watch)

    async def async_check(
        self,
        entry_id: str,
        stop_name: str,
        departures: list[dict[str, Any]],
    ) -> None:
        """Check all watches of one entry against fresh departure data."""
        changed = False
        for watch in [w for w in self._watches if w["entry_id"] == entry_id]:
            dep = next(
                (
                    d
                    for d in departures
                    if d.get("line") == watch["line"]
                    and d.get("direction") == watch["direction"]
                    and d.get("planned") == watch["planned"]
                ),
                None,
            )
            if dep is None:
                if self._expired(watch):
                    self._watches.remove(watch)
                    self._dismiss(watch)
                    changed = True
                continue

            changed |= await self._check_leave(watch, dep, stop_name)
            changed |= await self._check_delay(watch, dep, stop_name)

        if changed:
            await self._async_save()

    def _expired(self, watch: dict[str, Any]) -> bool:
        try:
            return datetime.fromisoformat(watch["planned"]) < datetime.now()
        except (ValueError, TypeError):
            # Unparseable planned time can never match again — drop it
            return True

    async def _check_leave(self, watch: dict[str, Any], dep: dict[str, Any], stop_name: str) -> bool:
        leave_mins = dep.get("leave_in_minutes")
        if leave_mins is None:
            leave_mins = dep.get("minutes_until")
        if leave_mins is None:
            return False

        due = leave_mins <= watch["leave_threshold"]
        if due and not watch["notified_leave"]:
            watch["notified_leave"] = True
            await self._notify(
                watch,
                notification_suffix="watch",
                title=f"Bus {watch['line']} → {watch['direction']}",
                bell_title_suffix=" — Jetzt losrennen!",
                message=(
                    f"{_leave_urgency(leave_mins)} "
                    f"Fährt um {_fmt_time(dep.get('effective'))} ab {stop_name}."
                ),
            )
            return True
        if not due and watch["notified_leave"]:
            watch["notified_leave"] = False
            self._dismiss(watch)
            return True
        return False

    async def _check_delay(self, watch: dict[str, Any], dep: dict[str, Any], stop_name: str) -> bool:
        delay = dep.get("delay_minutes") or 0
        if delay > 0 and watch["notified_delay"] != delay:
            watch["notified_delay"] = delay
            await self._notify(
                watch,
                notification_suffix="delay",
                title=f"Bus {watch['line']} → {watch['direction']}",
                bell_title_suffix=" — Verspätung!",
                message=(
                    f"+{delay} min Verspätung. "
                    f"Neue Abfahrt: {_fmt_time(dep.get('effective'))} ab {stop_name}."
                ),
            )
            return True
        if delay == 0 and watch["notified_delay"]:
            watch["notified_delay"] = 0
            return True
        return False

    def _notification_id(self, watch: dict[str, Any], suffix: str) -> str:
        key = watch_key(watch["line"], watch["direction"], watch["planned"])
        safe = "".join(c if c.isalnum() else "_" for c in key)
        return f"vab_{suffix}_{safe}"

    async def _notify(
        self,
        watch: dict[str, Any],
        notification_suffix: str,
        title: str,
        bell_title_suffix: str,
        message: str,
    ) -> None:
        service = watch.get("notify_service")
        if service and self._hass.services.has_service("notify", service):
            try:
                await self._hass.services.async_call(
                    "notify", service, {"title": title, "message": message}
                )
            except Exception:  # noqa: BLE001 — a broken notify target must not kill the update loop
                _LOGGER.exception("Notify service %s failed", service)
            return
        persistent_notification.async_create(
            self._hass,
            message,
            title=f"{title}{bell_title_suffix}",
            notification_id=self._notification_id(watch, notification_suffix),
        )

    def _dismiss(self, watch: dict[str, Any]) -> None:
        if watch.get("notify_service"):
            return
        for suffix in ("watch", "delay"):
            persistent_notification.async_dismiss(
                self._hass, self._notification_id(watch, suffix)
            )

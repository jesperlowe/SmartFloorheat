"""SmartFloorHeat integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ROOMS,
    DOMAIN,
    MODE_COMFORT,
    MODE_ECO,
    PLATFORMS,
    SERVICE_RECALCULATE,
    SERVICE_RESET_LEARNING,
    SERVICE_SET_MODE,
)
from .coordinator import SmartFloorHeatCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SmartFloorHeat from config entry."""
    rooms = entry.data.get(CONF_ROOMS, [])
    coordinator = SmartFloorHeatCoordinator(hass, rooms)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: SmartFloorHeatCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_unload()

    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECALCULATE):
        return

    async def _all_coordinators() -> list[SmartFloorHeatCoordinator]:
        return list(hass.data.get(DOMAIN, {}).values())

    async def handle_recalculate(call: ServiceCall) -> None:
        room = call.data.get("room")
        for coordinator in await _all_coordinators():
            if room:
                await coordinator.async_recalculate_room(room)
            else:
                await coordinator.async_request_refresh()

    async def handle_set_mode(call: ServiceCall) -> None:
        room = call.data["room"]
        mode = call.data["mode"]
        for coordinator in await _all_coordinators():
            ctrl = coordinator.controllers.get(room)
            if ctrl:
                ctrl.async_set_mode(mode)
                await coordinator.async_recalculate_room(room)

    async def handle_reset_learning(call: ServiceCall) -> None:
        room = call.data.get("room")
        for coordinator in await _all_coordinators():
            if room:
                ctrl = coordinator.controllers.get(room)
                if ctrl:
                    ctrl.reset_learning()
                    await coordinator.async_recalculate_room(room)
            else:
                for room_id, ctrl in coordinator.controllers.items():
                    ctrl.reset_learning()
                    await coordinator.async_recalculate_room(room_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALCULATE,
        handle_recalculate,
        schema=vol.Schema({vol.Optional("room"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MODE,
        handle_set_mode,
        schema=vol.Schema({
            vol.Required("room"): cv.string,
            vol.Required("mode"): vol.In([MODE_ECO, MODE_COMFORT]),
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_LEARNING,
        handle_reset_learning,
        schema=vol.Schema({vol.Optional("room"): cv.string}),
    )


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove entry."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

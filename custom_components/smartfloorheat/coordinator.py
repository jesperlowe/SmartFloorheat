"""Coordinator for SmartFloorHeat."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_ROOM_ID, CONF_UPDATE_INTERVAL_SECONDS, DOMAIN
from .controllers import RoomController


class SmartFloorHeatCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates room updates."""

    def __init__(self, hass: HomeAssistant, room_cfgs: list[dict[str, Any]]) -> None:
        min_interval = min(cfg[CONF_UPDATE_INTERVAL_SECONDS] for cfg in room_cfgs)
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=min_interval),
        )
        self.controllers: dict[str, RoomController] = {}
        for cfg in room_cfgs:
            room_id = cfg[CONF_ROOM_ID]
            self.controllers[room_id] = RoomController(hass, cfg, self.async_recalculate_room)

    async def async_setup(self) -> None:
        for ctrl in self.controllers.values():
            await ctrl.async_added()

    async def async_unload(self) -> None:
        for ctrl in self.controllers.values():
            await ctrl.async_will_remove()

    async def async_recalculate_room(self, room_id: str) -> None:
        ctrl = self.controllers.get(room_id)
        if ctrl is None:
            return
        await ctrl.async_recalculate_and_control()
        self.async_update_listeners()

    async def _async_update_data(self) -> dict[str, Any]:
        for ctrl in self.controllers.values():
            await ctrl.async_recalculate_and_control()
        return {
            room_id: {
                "final_setpoint": ctrl.computed_final_setpoint,
                "is_heating": ctrl.is_heating,
                "offsets": ctrl.current_offsets,
            }
            for room_id, ctrl in self.controllers.items()
        }

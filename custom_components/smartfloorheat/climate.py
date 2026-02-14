"""Climate entities for SmartFloorHeat."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HEATER_SWITCH, CONF_INDOOR_TEMP_SENSOR, CONF_ROOM_NAME, DOMAIN
from .coordinator import SmartFloorHeatCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartFloorHeatCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [SmartFloorHeatClimate(coordinator, room_id) for room_id in coordinator.controllers],
        update_before_add=True,
    )


class SmartFloorHeatClimate(CoordinatorEntity[SmartFloorHeatCoordinator], ClimateEntity):
    """Room climate entity."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: SmartFloorHeatCoordinator, room_id: str) -> None:
        super().__init__(coordinator)
        self.room_id = room_id
        self.controller = coordinator.controllers[room_id]
        self._attr_unique_id = f"smartfloorheat_{room_id}_climate"
        self._attr_name = f"SmartFloorHeat {self.controller.cfg[CONF_ROOM_NAME]}"

    @property
    def current_temperature(self) -> float | None:
        return self.controller._f(self.controller.cfg[CONF_INDOOR_TEMP_SENSOR])

    @property
    def target_temperature(self) -> float | None:
        return self.controller.base_setpoint

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        return HVACAction.HEATING if self.controller.is_heating else HVACAction.IDLE

    @property
    def extra_state_attributes(self):
        return self.controller.extra_attrs

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": self.controller.cfg[CONF_HEATER_SWITCH]},
                blocking=True,
            )
            self.controller.is_heating = False
        elif hvac_mode in (HVACMode.HEAT, HVACMode.AUTO):
            await self.coordinator.async_recalculate_room(self.room_id)
        self.async_write_ha_state()

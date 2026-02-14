"""Sensor entities for SmartFloorHeat."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ROOM_NAME, DOMAIN
from .coordinator import SmartFloorHeatCoordinator


@dataclass(frozen=True, kw_only=True)
class RoomSensorDescription(SensorEntityDescription):
    key_fn: str


DESCRIPTIONS = [
    RoomSensorDescription(key="dynamic_setpoint", key_fn="dynamic_setpoint", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    RoomSensorDescription(key="offset_solar", key_fn="offset_solar", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    RoomSensorDescription(key="offset_wind", key_fn="offset_wind", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    RoomSensorDescription(key="offset_outdoor", key_fn="offset_outdoor", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    RoomSensorDescription(key="offset_total", key_fn="offset_total", native_unit_of_measurement=UnitOfTemperature.CELSIUS),
    RoomSensorDescription(key="trend_cph", key_fn="trend_cph"),
    RoomSensorDescription(key="outdoor_drop_gain", key_fn="outdoor_drop_gain"),
    RoomSensorDescription(key="debug_json", key_fn="debug_json"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartFloorHeatCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SmartFloorHeatRoomSensor] = []
    for room_id in coordinator.controllers:
        for desc in DESCRIPTIONS:
            entities.append(SmartFloorHeatRoomSensor(coordinator, room_id, desc))
    async_add_entities(entities)


class SmartFloorHeatRoomSensor(CoordinatorEntity[SmartFloorHeatCoordinator], SensorEntity):
    """Simple room sensor."""

    def __init__(self, coordinator: SmartFloorHeatCoordinator, room_id: str, description: RoomSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.room_id = room_id
        self.controller = coordinator.controllers[room_id]
        self._attr_unique_id = f"smartfloorheat_{room_id}_{description.key}"
        self._attr_name = f"SmartFloorHeat {self.controller.cfg[CONF_ROOM_NAME]} {description.key}"

    @property
    def native_value(self):
        key = self.entity_description.key_fn
        if key == "dynamic_setpoint":
            return round(self.controller.computed_final_setpoint, 2)
        if key == "offset_solar":
            return round(self.controller.current_offsets["solar"], 3)
        if key == "offset_wind":
            return round(self.controller.current_offsets["wind"], 3)
        if key == "offset_outdoor":
            return round(self.controller.current_offsets["outdoor"], 3)
        if key == "offset_total":
            return round(self.controller.current_offsets["total"], 3)
        if key == "trend_cph":
            return round(self.controller.trend_cph, 3)
        if key == "outdoor_drop_gain":
            return round(self.controller.outdoor_drop_gain, 3)
        if key == "debug_json":
            return self.controller.debug_json
        return None

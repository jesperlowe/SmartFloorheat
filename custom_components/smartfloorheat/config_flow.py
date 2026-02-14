"""Config flow for SmartFloorHeat."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    BASE_SOURCE_CLIMATE,
    BASE_SOURCE_NUMBER,
    BASE_SOURCE_VIRTUAL,
    CONF_BASE_CLIMATE_ENTITY,
    CONF_BASE_NUMBER_ENTITY,
    CONF_BASE_SOURCE_TYPE,
    CONF_BASE_VIRTUAL_TEMPERATURE,
    CONF_COMFORT_GUARD_DELTA,
    CONF_ENABLE_FLOW_GUARD,
    CONF_ENABLE_OUTDOOR,
    CONF_ENABLE_SOLAR,
    CONF_ENABLE_WIND,
    CONF_FLOW_LOW_THRESHOLD,
    CONF_FLOW_TEMP_SENSOR,
    CONF_HEATER_SWITCH,
    CONF_HYSTERESIS_DEGC,
    CONF_INDOOR_TEMP_SENSOR,
    CONF_MAX_COOLING_DEGC,
    CONF_MAX_OUTDOOR_BOOST_DEGC,
    CONF_MAX_WIND_BOOST_DEGC,
    CONF_MIN_OFF_MINUTES,
    CONF_MIN_ON_MINUTES,
    CONF_ORIENTATION_DEGREES,
    CONF_ORIENTATION_FACTOR,
    CONF_ORIENTATION_MODE,
    CONF_OUTDOOR_BASE_C,
    CONF_OUTDOOR_NORM_C,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_ROOMS,
    CONF_SOLAR_CURRENT_HOUR,
    CONF_SOLAR_NEXT_HOUR,
    CONF_SOLAR_NORM_KWH,
    CONF_SOLAR_TODAY_REMAINING,
    CONF_SOLAR_TOMORROW,
    CONF_TAU_HOURS,
    CONF_UPDATE_INTERVAL_SECONDS,
    CONF_WIND_BASE_KMH,
    CONF_WIND_EFFECT_PERCENT,
    CONF_WIND_NORM_KMH,
    CONF_WEATHER_ENTITY,
    DEFAULTS,
    DOMAIN,
    ORIENTATION_AZIMUTH,
)


class SmartFloorHeatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._rooms: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self.async_step_room()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    async def async_step_room(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            room = dict(user_input)
            room[CONF_ROOM_ID] = slugify(room[CONF_ROOM_NAME])
            if room[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_CLIMATE:
                room.pop(CONF_BASE_NUMBER_ENTITY, None)
                room.pop(CONF_BASE_VIRTUAL_TEMPERATURE, None)
            elif room[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_NUMBER:
                room.pop(CONF_BASE_CLIMATE_ENTITY, None)
                room.pop(CONF_BASE_VIRTUAL_TEMPERATURE, None)
            else:
                room.pop(CONF_BASE_CLIMATE_ENTITY, None)
                room.pop(CONF_BASE_NUMBER_ENTITY, None)
            if room[CONF_ORIENTATION_MODE] != ORIENTATION_AZIMUTH:
                room.pop(CONF_ORIENTATION_DEGREES, None)
            self._rooms.append(room)
            return await self.async_step_add_another()

        schema = vol.Schema(
            {
                vol.Required(CONF_ROOM_NAME): selector.TextSelector(),
                vol.Required(CONF_INDOOR_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_WEATHER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["weather"])
                ),
                vol.Optional(CONF_OUTDOOR_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Optional(CONF_FLOW_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_BASE_SOURCE_TYPE, default=BASE_SOURCE_CLIMATE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[BASE_SOURCE_CLIMATE, BASE_SOURCE_NUMBER, BASE_SOURCE_VIRTUAL], mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(CONF_BASE_CLIMATE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["climate"])
                ),
                vol.Optional(CONF_BASE_NUMBER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["number", "input_number"])
                ),
                vol.Optional(CONF_BASE_VIRTUAL_TEMPERATURE, default=DEFAULTS[CONF_BASE_VIRTUAL_TEMPERATURE]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5.0, max=35.0, step=0.5)
                ),
                vol.Required(CONF_HEATER_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Required(CONF_SOLAR_CURRENT_HOUR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_SOLAR_NEXT_HOUR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_SOLAR_TODAY_REMAINING): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_SOLAR_TOMORROW): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_ORIENTATION_MODE, default=DEFAULTS[CONF_ORIENTATION_MODE]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["north", "south", "east", "west", "azimuth"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_ORIENTATION_DEGREES): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=359, step=1)
                ),
                vol.Optional(CONF_ORIENTATION_FACTOR, default=DEFAULTS[CONF_ORIENTATION_FACTOR]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=1.2, step=0.05)
                ),
                vol.Required(CONF_WIND_EFFECT_PERCENT, default=DEFAULTS[CONF_WIND_EFFECT_PERCENT]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1)
                ),
                vol.Required(CONF_MAX_COOLING_DEGC, default=DEFAULTS[CONF_MAX_COOLING_DEGC]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=3.0, step=0.05)
                ),
                vol.Required(CONF_MAX_WIND_BOOST_DEGC, default=DEFAULTS[CONF_MAX_WIND_BOOST_DEGC]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=3.0, step=0.05)
                ),
                vol.Required(CONF_MAX_OUTDOOR_BOOST_DEGC, default=DEFAULTS[CONF_MAX_OUTDOOR_BOOST_DEGC]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=3.0, step=0.05)
                ),
                vol.Required(CONF_WIND_BASE_KMH, default=DEFAULTS[CONF_WIND_BASE_KMH]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=60.0, step=0.5)
                ),
                vol.Required(CONF_WIND_NORM_KMH, default=DEFAULTS[CONF_WIND_NORM_KMH]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1.0, max=120.0, step=0.5)
                ),
                vol.Required(CONF_OUTDOOR_BASE_C, default=DEFAULTS[CONF_OUTDOOR_BASE_C]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-20.0, max=30.0, step=0.5)
                ),
                vol.Required(CONF_OUTDOOR_NORM_C, default=DEFAULTS[CONF_OUTDOOR_NORM_C]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-40.0, max=20.0, step=0.5)
                ),
                vol.Required(CONF_SOLAR_NORM_KWH, default=DEFAULTS[CONF_SOLAR_NORM_KWH]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.1, max=20.0, step=0.1)
                ),
                vol.Required(CONF_TAU_HOURS, default=DEFAULTS[CONF_TAU_HOURS]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.1, max=12.0, step=0.1)
                ),
                vol.Required(CONF_COMFORT_GUARD_DELTA, default=DEFAULTS[CONF_COMFORT_GUARD_DELTA]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.0, max=2.0, step=0.05)
                ),
                vol.Required(CONF_FLOW_LOW_THRESHOLD, default=DEFAULTS[CONF_FLOW_LOW_THRESHOLD]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=10.0, max=50.0, step=0.1)
                ),
                vol.Required(CONF_MIN_ON_MINUTES, default=DEFAULTS[CONF_MIN_ON_MINUTES]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=120, step=1)
                ),
                vol.Required(CONF_MIN_OFF_MINUTES, default=DEFAULTS[CONF_MIN_OFF_MINUTES]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=120, step=1)
                ),
                vol.Required(CONF_HYSTERESIS_DEGC, default=DEFAULTS[CONF_HYSTERESIS_DEGC]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.05, max=2.0, step=0.05)
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL_SECONDS,
                    default=DEFAULTS[CONF_UPDATE_INTERVAL_SECONDS],
                ): selector.NumberSelector(selector.NumberSelectorConfig(min=30, max=3600, step=10)),
                vol.Required(CONF_ENABLE_SOLAR, default=DEFAULTS[CONF_ENABLE_SOLAR]): selector.BooleanSelector(),
                vol.Required(CONF_ENABLE_WIND, default=DEFAULTS[CONF_ENABLE_WIND]): selector.BooleanSelector(),
                vol.Required(CONF_ENABLE_OUTDOOR, default=DEFAULTS[CONF_ENABLE_OUTDOOR]): selector.BooleanSelector(),
                vol.Required(CONF_ENABLE_FLOW_GUARD, default=DEFAULTS[CONF_ENABLE_FLOW_GUARD]): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="room", data_schema=schema, errors=errors)

    async def async_step_add_another(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            if user_input["action"] == "add_room":
                return await self.async_step_room()
            title = "SmartFloorHeat"
            return self.async_create_entry(title=title, data={CONF_ROOMS: self._rooms})

        return self.async_show_form(
            step_id="add_another",
            data_schema=vol.Schema(
                {
                    vol.Required("action", default="finish"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["add_room", "finish"],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            description_placeholders={"rooms": str(len(self._rooms))},
        )

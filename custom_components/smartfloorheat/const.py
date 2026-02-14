"""Constants for SmartFloorHeat."""

from __future__ import annotations

DOMAIN = "smartfloorheat"
PLATFORMS = ["climate", "sensor"]

CONF_ROOMS = "rooms"
CONF_ROOM_NAME = "room_name"
CONF_ROOM_ID = "room_id"
CONF_INDOOR_TEMP_SENSOR = "indoor_temp_sensor"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_OUTDOOR_TEMP_SENSOR = "outdoor_temp_sensor"
CONF_FLOW_TEMP_SENSOR = "flow_temp_sensor"
CONF_HEATER_SWITCH = "heater_switch"

CONF_BASE_SOURCE_TYPE = "base_source_type"
BASE_SOURCE_CLIMATE = "climate"
BASE_SOURCE_NUMBER = "number"
CONF_BASE_CLIMATE_ENTITY = "base_climate_entity"
CONF_BASE_NUMBER_ENTITY = "base_number_entity"

CONF_SOLAR_CURRENT_HOUR = "solar_energy_current_hour"
CONF_SOLAR_NEXT_HOUR = "solar_energy_next_hour"
CONF_SOLAR_TODAY_REMAINING = "solar_energy_today_remaining"
CONF_SOLAR_TOMORROW = "solar_energy_tomorrow"

CONF_ORIENTATION_MODE = "orientation_mode"
ORIENTATION_NORTH = "north"
ORIENTATION_SOUTH = "south"
ORIENTATION_EAST = "east"
ORIENTATION_WEST = "west"
ORIENTATION_AZIMUTH = "azimuth"
CONF_ORIENTATION_DEGREES = "orientation_degrees"
CONF_ORIENTATION_FACTOR = "orientation_factor"

CONF_WIND_EFFECT_PERCENT = "wind_effect_percent"
CONF_MAX_COOLING_DEGC = "max_cooling_degC"
CONF_MAX_WIND_BOOST_DEGC = "max_wind_boost_degC"
CONF_MAX_OUTDOOR_BOOST_DEGC = "max_outdoor_boost_degC"
CONF_WIND_BASE_KMH = "wind_base_kmh"
CONF_WIND_NORM_KMH = "wind_norm_kmh"
CONF_OUTDOOR_BASE_C = "outdoor_base_c"
CONF_OUTDOOR_NORM_C = "outdoor_norm_c"
CONF_SOLAR_NORM_KWH = "solar_norm_kwh"
CONF_TAU_HOURS = "tau_hours"
CONF_COMFORT_GUARD_DELTA = "comfort_guard_delta"
CONF_FLOW_LOW_THRESHOLD = "flow_low_threshold"
CONF_MIN_ON_MINUTES = "min_on_minutes"
CONF_MIN_OFF_MINUTES = "min_off_minutes"
CONF_HYSTERESIS_DEGC = "hysteresis_degC"
CONF_UPDATE_INTERVAL_SECONDS = "update_interval_seconds"

CONF_ENABLE_SOLAR = "enable_solar_correction"
CONF_ENABLE_WIND = "enable_wind_correction"
CONF_ENABLE_OUTDOOR = "enable_outdoor_correction"
CONF_ENABLE_FLOW_GUARD = "enable_flow_guard"

ATTR_BASE_SETPOINT = "base_setpoint"
ATTR_FINAL_SETPOINT = "final_setpoint"
ATTR_EFFECTIVE_TARGET = "effective_target"
ATTR_OFFSETS = "offsets"
ATTR_TREND_CPH = "trend_cph"
ATTR_OUTDOOR_DROP_GAIN = "outdoor_drop_gain"
ATTR_LAST_SWITCH_CHANGE_TS = "last_switch_change_ts"

SERVICE_RECALCULATE = "recalculate"
SERVICE_SET_MODE = "set_mode"
SERVICE_RESET_LEARNING = "reset_learning"

MODE_COMFORT = "comfort"
MODE_ECO = "eco"

DEFAULTS = {
    CONF_ORIENTATION_MODE: ORIENTATION_SOUTH,
    CONF_ORIENTATION_FACTOR: 1.0,
    CONF_WIND_EFFECT_PERCENT: 100,
    CONF_MAX_COOLING_DEGC: 0.6,
    CONF_MAX_WIND_BOOST_DEGC: 0.7,
    CONF_MAX_OUTDOOR_BOOST_DEGC: 0.6,
    CONF_WIND_BASE_KMH: 8.0,
    CONF_WIND_NORM_KMH: 35.0,
    CONF_OUTDOOR_BASE_C: 10.0,
    CONF_OUTDOOR_NORM_C: -5.0,
    CONF_SOLAR_NORM_KWH: 2.5,
    CONF_TAU_HOURS: 3.5,
    CONF_COMFORT_GUARD_DELTA: 0.2,
    CONF_FLOW_LOW_THRESHOLD: 29.0,
    CONF_MIN_ON_MINUTES: 8,
    CONF_MIN_OFF_MINUTES: 8,
    CONF_HYSTERESIS_DEGC: 0.2,
    CONF_UPDATE_INTERVAL_SECONDS: 600,
    CONF_ENABLE_SOLAR: True,
    CONF_ENABLE_WIND: True,
    CONF_ENABLE_OUTDOOR: True,
    CONF_ENABLE_FLOW_GUARD: True,
}

DEBUG_KEYS = (
    "base_setpoint",
    "indoor_temp",
    "outdoor_temp",
    "wind_speed",
    "wind_gust_speed",
    "solar_impulse",
    "solar_score",
    "wind_score",
    "outdoor_score",
    "solar_gain",
    "wind_gain",
    "outdoor_gain",
    "orientation_factor",
    "offset_solar",
    "offset_wind",
    "offset_outdoor",
    "offset_total",
    "raw_setpoint",
    "final_setpoint",
    "trend_cph",
    "outdoor_drop_gain",
    "heating_request",
)

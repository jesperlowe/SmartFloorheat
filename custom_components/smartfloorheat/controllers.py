"""Room control logic for SmartFloorHeat."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify
from homeassistant.util.dt import utcnow

from .const import (
    ATTR_BASE_SETPOINT,
    ATTR_EFFECTIVE_TARGET,
    ATTR_FINAL_SETPOINT,
    ATTR_LAST_SWITCH_CHANGE_TS,
    ATTR_OFFSETS,
    ATTR_OUTDOOR_DROP_GAIN,
    ATTR_TREND_CPH,
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
    CONF_ORIENTATION_FACTOR,
    CONF_ORIENTATION_MODE,
    CONF_OUTDOOR_BASE_C,
    CONF_OUTDOOR_NORM_C,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_SOLAR_CURRENT_HOUR,
    CONF_SOLAR_NEXT_HOUR,
    CONF_SOLAR_NORM_KWH,
    CONF_SOLAR_TODAY_REMAINING,
    CONF_SOLAR_TOMORROW,
    CONF_WIND_BASE_KMH,
    CONF_WIND_EFFECT_PERCENT,
    CONF_WIND_NORM_KMH,
    CONF_WEATHER_ENTITY,
    DEBUG_KEYS,
    MODE_COMFORT,
    MODE_ECO,
    ORIENTATION_EAST,
    ORIENTATION_NORTH,
    ORIENTATION_SOUTH,
    ORIENTATION_WEST,
)


@dataclass
class Offsets:
    solar: float = 0.0
    wind: float = 0.0
    outdoor: float = 0.0

    @property
    def total(self) -> float:
        return self.solar + self.wind + self.outdoor


class RoomController:
    """Controller for one room."""

    def __init__(self, hass: HomeAssistant, cfg: dict[str, Any], request_callback) -> None:
        self.hass = hass
        self.cfg = cfg
        self.request_callback = request_callback

        self.room_name = cfg[CONF_ROOM_NAME]
        self.room_id = cfg.get(CONF_ROOM_ID) or slugify(self.room_name)

        self.indoor_samples: deque[tuple[datetime, float]] = deque()
        self.outdoor_samples: deque[tuple[datetime, float]] = deque()

        self.last_setpoint_sent: float | None = None
        self.last_switch_change_ts: datetime | None = None
        self.is_heating = False
        self.computed_final_setpoint: float = 20.0
        self.current_offsets = {"solar": 0.0, "wind": 0.0, "outdoor": 0.0, "total": 0.0}
        self.trend_cph = 0.0
        self.outdoor_drop_gain = 1.0
        self.base_setpoint = 20.0
        self.mode = MODE_COMFORT
        self._comfort_tuning = {
            CONF_MAX_COOLING_DEGC: cfg[CONF_MAX_COOLING_DEGC],
            CONF_MAX_WIND_BOOST_DEGC: cfg[CONF_MAX_WIND_BOOST_DEGC],
            CONF_MAX_OUTDOOR_BOOST_DEGC: cfg[CONF_MAX_OUTDOOR_BOOST_DEGC],
            CONF_COMFORT_GUARD_DELTA: cfg[CONF_COMFORT_GUARD_DELTA],
        }
        self.debug = {k: None for k in DEBUG_KEYS}

        self._unsubs = []

    async def async_added(self) -> None:
        """Register state listeners."""
        watched = [
            self.cfg[CONF_INDOOR_TEMP_SENSOR],
            self.cfg[CONF_WEATHER_ENTITY],
            self.cfg[CONF_HEATER_SWITCH],
            self.cfg[CONF_SOLAR_CURRENT_HOUR],
            self.cfg[CONF_SOLAR_NEXT_HOUR],
            self.cfg[CONF_SOLAR_TODAY_REMAINING],
            self.cfg[CONF_SOLAR_TOMORROW],
        ]
        if self.cfg[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_CLIMATE:
            watched.append(self.cfg[CONF_BASE_CLIMATE_ENTITY])
        elif self.cfg[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_NUMBER:
            watched.append(self.cfg[CONF_BASE_NUMBER_ENTITY])
        if self.cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
            watched.append(self.cfg[CONF_OUTDOOR_TEMP_SENSOR])
        if self.cfg.get(CONF_FLOW_TEMP_SENSOR):
            watched.append(self.cfg[CONF_FLOW_TEMP_SENSOR])

        for entity_id in watched:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, [entity_id], self._debounced_recalculate
                )
            )

    async def async_will_remove(self) -> None:
        for unsub in self._unsubs:
            unsub()

    async def _debounced_recalculate(self, event) -> None:
        del event
        await self.request_callback(self.room_id)

    def _f(self, entity_id: str | None, attr: str | None = None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        raw = state.attributes.get(attr) if attr else state.state
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _calc_orientation_factor(self) -> float:
        if self.cfg.get(CONF_ORIENTATION_FACTOR) is not None:
            return float(self.cfg[CONF_ORIENTATION_FACTOR])
        mode = self.cfg.get(CONF_ORIENTATION_MODE, ORIENTATION_SOUTH)
        mapping = {
            ORIENTATION_SOUTH: 1.0,
            ORIENTATION_WEST: 0.7,
            ORIENTATION_EAST: 0.7,
            ORIENTATION_NORTH: 0.4,
        }
        return mapping.get(mode, 1.0)

    def _base_setpoint(self) -> float:
        if self.cfg[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_CLIMATE:
            result = self._f(self.cfg[CONF_BASE_CLIMATE_ENTITY], "temperature")
        elif self.cfg[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_NUMBER:
            result = self._f(self.cfg[CONF_BASE_NUMBER_ENTITY])
        elif self.cfg[CONF_BASE_SOURCE_TYPE] == BASE_SOURCE_VIRTUAL:
            result = self.cfg.get(CONF_BASE_VIRTUAL_TEMPERATURE)
        else:
            result = None
        return result if result is not None else self.base_setpoint

    def _trim_window(self, buffer: deque[tuple[datetime, float]], now: datetime) -> None:
        cutoff = now - timedelta(minutes=60)
        while buffer and buffer[0][0] < cutoff:
            buffer.popleft()

    def _slope_cph(self, buffer: deque[tuple[datetime, float]]) -> float:
        if len(buffer) < 2:
            return 0.0
        oldest_ts, oldest = buffer[0]
        latest_ts, latest = buffer[-1]
        dt_h = (latest_ts - oldest_ts).total_seconds() / 3600
        if dt_h <= 0:
            return 0.0
        return (latest - oldest) / dt_h

    def _outdoor_drop_gain(self) -> float:
        if len(self.outdoor_samples) < 2:
            return 1.0
        oldest = self.outdoor_samples[0][1]
        latest = self.outdoor_samples[-1][1]
        outdoor_drop = latest - oldest
        return max(1.0, min(1.5, 1.0 + max(0.0, -outdoor_drop) / 4.0))

    def _clamp(self, val: float, low: float, high: float) -> float:
        return max(low, min(high, val))

    async def async_recalculate_and_control(self) -> None:
        now = utcnow()
        indoor = self._f(self.cfg[CONF_INDOOR_TEMP_SENSOR])
        if indoor is None:
            return

        weather = self.hass.states.get(self.cfg[CONF_WEATHER_ENTITY])
        wind_speed = 0.0
        wind_gust = 0.0
        weather_outdoor = None
        if weather:
            wind_speed = float(weather.attributes.get("wind_speed", 0.0) or 0.0)
            wind_gust = float(weather.attributes.get("wind_gust_speed", wind_speed) or wind_speed)
            weather_outdoor = weather.attributes.get("temperature")

        outdoor = self._f(self.cfg.get(CONF_OUTDOOR_TEMP_SENSOR))
        if outdoor is None and weather_outdoor is not None:
            try:
                outdoor = float(weather_outdoor)
            except (TypeError, ValueError):
                outdoor = None

        flow_temp = self._f(self.cfg.get(CONF_FLOW_TEMP_SENSOR))
        base = self._base_setpoint()

        self.base_setpoint = base
        self.indoor_samples.append((now, indoor))
        self._trim_window(self.indoor_samples, now)
        self.trend_cph = self._slope_cph(self.indoor_samples)

        if outdoor is not None:
            self.outdoor_samples.append((now, outdoor))
            self._trim_window(self.outdoor_samples, now)
        self.outdoor_drop_gain = self._outdoor_drop_gain()

        cur = self._f(self.cfg[CONF_SOLAR_CURRENT_HOUR]) or 0.0
        nxt = self._f(self.cfg[CONF_SOLAR_NEXT_HOUR]) or 0.0
        rem = self._f(self.cfg[CONF_SOLAR_TODAY_REMAINING]) or 0.0
        tom = self._f(self.cfg[CONF_SOLAR_TOMORROW]) or 0.0

        solar_impulse = cur * 1.0 + nxt * 1.2 + rem * 0.25 + tom * 0.1
        solar_score = self._clamp(solar_impulse / max(0.1, self.cfg[CONF_SOLAR_NORM_KWH]), 0.0, 1.0)

        w_eff = wind_speed + (wind_gust - wind_speed) * 0.25
        wind_span = max(0.1, self.cfg[CONF_WIND_NORM_KMH] - self.cfg[CONF_WIND_BASE_KMH])
        wind_score = self._clamp((w_eff - self.cfg[CONF_WIND_BASE_KMH]) / wind_span, 0.0, 1.0)

        outdoor_score = 0.0
        if outdoor is not None:
            denom = max(0.1, self.cfg[CONF_OUTDOOR_BASE_C] - self.cfg[CONF_OUTDOOR_NORM_C])
            outdoor_score = self._clamp((self.cfg[CONF_OUTDOOR_BASE_C] - outdoor) / denom, 0.0, 1.0)

        solar_gain = self._clamp(1 + self.trend_cph / 1.5, 0.8, 1.4)
        wind_gain = self._clamp(1 + (-self.trend_cph) / 1.2, 0.8, 1.5)
        outdoor_gain = self.outdoor_drop_gain
        orientation_factor = self._calc_orientation_factor()

        offsets = Offsets()
        if self.cfg[CONF_ENABLE_SOLAR]:
            offsets.solar = (
                -solar_score
                * self.cfg[CONF_MAX_COOLING_DEGC]
                * solar_gain
                * orientation_factor
            )
        if self.cfg[CONF_ENABLE_WIND]:
            offsets.wind = (
                wind_score
                * self.cfg[CONF_MAX_WIND_BOOST_DEGC]
                * wind_gain
                * (self.cfg[CONF_WIND_EFFECT_PERCENT] / 100.0)
            )
        if self.cfg[CONF_ENABLE_OUTDOOR]:
            offsets.outdoor = outdoor_score * self.cfg[CONF_MAX_OUTDOOR_BOOST_DEGC] * outdoor_gain

        total_offset = offsets.total
        if indoor < (base - self.cfg[CONF_COMFORT_GUARD_DELTA]):
            total_offset = max(total_offset, -0.1)
        if (
            self.cfg[CONF_ENABLE_FLOW_GUARD]
            and flow_temp is not None
            and flow_temp < self.cfg[CONF_FLOW_LOW_THRESHOLD]
        ):
            total_offset = max(total_offset, -0.1)

        raw = base + total_offset
        final_sp = self._clamp(raw, base - 0.2, base + 1.0)

        self.computed_final_setpoint = final_sp
        self.current_offsets = {
            "solar": offsets.solar,
            "wind": offsets.wind,
            "outdoor": offsets.outdoor,
            "total": total_offset,
        }

        request_heat = self.is_heating
        hyst = self.cfg[CONF_HYSTERESIS_DEGC]
        if indoor <= (final_sp - hyst):
            request_heat = True
        elif indoor >= (final_sp + hyst):
            request_heat = False

        await self._apply_switch_request(request_heat)

        self.debug = {
            "base_setpoint": round(base, 3),
            "indoor_temp": round(indoor, 3),
            "outdoor_temp": round(outdoor, 3) if outdoor is not None else None,
            "wind_speed": round(wind_speed, 3),
            "wind_gust_speed": round(wind_gust, 3),
            "solar_impulse": round(solar_impulse, 3),
            "solar_score": round(solar_score, 3),
            "wind_score": round(wind_score, 3),
            "outdoor_score": round(outdoor_score, 3),
            "solar_gain": round(solar_gain, 3),
            "wind_gain": round(wind_gain, 3),
            "outdoor_gain": round(outdoor_gain, 3),
            "orientation_factor": round(orientation_factor, 3),
            "offset_solar": round(offsets.solar, 3),
            "offset_wind": round(offsets.wind, 3),
            "offset_outdoor": round(offsets.outdoor, 3),
            "offset_total": round(total_offset, 3),
            "raw_setpoint": round(raw, 3),
            "final_setpoint": round(final_sp, 3),
            "trend_cph": round(self.trend_cph, 3),
            "outdoor_drop_gain": round(self.outdoor_drop_gain, 3),
            "heating_request": request_heat,
        }

    async def _apply_switch_request(self, request_heat: bool) -> None:
        now = utcnow()
        if self.last_switch_change_ts is None:
            allowed = True
        else:
            elapsed = now - self.last_switch_change_ts
            min_on = timedelta(minutes=self.cfg[CONF_MIN_ON_MINUTES])
            min_off = timedelta(minutes=self.cfg[CONF_MIN_OFF_MINUTES])
            if request_heat:
                allowed = (not self.is_heating) and elapsed >= min_off
            else:
                allowed = self.is_heating and elapsed >= min_on

        if request_heat == self.is_heating:
            return
        if not allowed:
            return

        service = "turn_on" if request_heat else "turn_off"
        await self.hass.services.async_call(
            "switch",
            service,
            {"entity_id": self.cfg[CONF_HEATER_SWITCH]},
            blocking=True,
        )
        self.is_heating = request_heat
        self.last_switch_change_ts = now

    def async_set_mode(self, mode: str) -> None:
        self.mode = mode
        for key, value in self._comfort_tuning.items():
            self.cfg[key] = value
        if mode == MODE_ECO:
            self.cfg[CONF_MAX_COOLING_DEGC] = self._comfort_tuning[CONF_MAX_COOLING_DEGC] * 0.7
            self.cfg[CONF_MAX_WIND_BOOST_DEGC] = self._comfort_tuning[CONF_MAX_WIND_BOOST_DEGC] * 0.7
            self.cfg[CONF_MAX_OUTDOOR_BOOST_DEGC] = self._comfort_tuning[CONF_MAX_OUTDOOR_BOOST_DEGC] * 0.7
            self.cfg[CONF_COMFORT_GUARD_DELTA] = max(0.1, self._comfort_tuning[CONF_COMFORT_GUARD_DELTA] - 0.05)

    def reset_learning(self) -> None:
        self.indoor_samples.clear()
        self.outdoor_samples.clear()
        self.trend_cph = 0.0
        self.outdoor_drop_gain = 1.0

    @property
    def extra_attrs(self) -> dict[str, Any]:
        return {
            ATTR_BASE_SETPOINT: round(self.base_setpoint, 2),
            ATTR_FINAL_SETPOINT: round(self.computed_final_setpoint, 2),
            ATTR_EFFECTIVE_TARGET: round(self.computed_final_setpoint, 2),
            ATTR_OFFSETS: self.current_offsets,
            ATTR_TREND_CPH: round(self.trend_cph, 3),
            ATTR_OUTDOOR_DROP_GAIN: round(self.outdoor_drop_gain, 3),
            ATTR_LAST_SWITCH_CHANGE_TS: self.last_switch_change_ts.isoformat()
            if self.last_switch_change_ts
            else None,
        }

    @property
    def debug_json(self) -> str:
        return json.dumps(self.debug, separators=(",", ":"), sort_keys=True)

"""Per-screen telemetry from the device's own check-ins (O2/O4: no device dies quietly)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PaperboardConfigEntry
from .const import SIGNAL_CHECKIN, SIGNAL_FRAME
from .entity import ScreenEntity
from .fmt import to_float
from .runtime import HubRuntime, ScreenRuntime

# Rough LiPo state of charge from voltage; curve from the owner's trmnl-service (MIT).
_CURVE = [(4.20, 100), (4.10, 90), (4.00, 80), (3.90, 60), (3.80, 40), (3.70, 20), (3.60, 10),
          (3.50, 5), (3.30, 0)]


def battery_percent(volts: float) -> int:
    if volts >= _CURVE[0][0]:
        return 100
    for (v_hi, p_hi), (v_lo, p_lo) in pairwise(_CURVE):
        if volts >= v_lo:
            return round(p_lo + (p_hi - p_lo) * (volts - v_lo) / (v_hi - v_lo))
    return 0


def _volts(s: ScreenRuntime) -> float | None:
    return to_float(s.telemetry.get("Battery-Voltage"))


def _percent(s: ScreenRuntime) -> int | None:
    v = _volts(s)
    return battery_percent(v) if v is not None else None


def _checkin(s: ScreenRuntime) -> dt.datetime | None:
    return dt_util.utc_from_timestamp(s.last_checkin) if s.last_checkin else None


@dataclass(frozen=True, kw_only=True)
class ScreenSensorDescription(SensorEntityDescription):
    value: Callable[[ScreenRuntime], object]
    signal: str = SIGNAL_CHECKIN


SENSORS = (
    ScreenSensorDescription(key="battery", device_class=SensorDeviceClass.BATTERY,
                            native_unit_of_measurement=PERCENTAGE,
                            state_class=SensorStateClass.MEASUREMENT, value=_percent),
    ScreenSensorDescription(key="battery_voltage", device_class=SensorDeviceClass.VOLTAGE,
                            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                            state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2,
                            entity_category=EntityCategory.DIAGNOSTIC, value=_volts),
    ScreenSensorDescription(key="rssi", device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                            state_class=SensorStateClass.MEASUREMENT,
                            entity_category=EntityCategory.DIAGNOSTIC,
                            value=lambda s: to_float(s.telemetry.get("RSSI"))),
    ScreenSensorDescription(key="firmware", entity_category=EntityCategory.DIAGNOSTIC,
                            value=lambda s: s.telemetry.get("FW-Version")),
    ScreenSensorDescription(key="last_checkin", device_class=SensorDeviceClass.TIMESTAMP,
                            entity_category=EntityCategory.DIAGNOSTIC, value=_checkin),
    ScreenSensorDescription(key="render_error", entity_category=EntityCategory.DIAGNOSTIC,
                            signal=SIGNAL_FRAME,
                            value=lambda s: (s.last_error or "none")[:250]),
)


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    hub = entry.runtime_data
    for screen in hub.screens.values():
        async_add_entities([ScreenSensor(hub, screen, d) for d in SENSORS],
                           config_subentry_id=screen.subentry_id)


class ScreenSensor(ScreenEntity, SensorEntity):
    entity_description: ScreenSensorDescription

    def __init__(self, hub: HubRuntime, screen: ScreenRuntime,
                 description: ScreenSensorDescription) -> None:
        super().__init__(hub, screen, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, self.entity_description.signal.format(self.screen.subentry_id),
            self._refresh))

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self):  # type: ignore[override]
        return self.entity_description.value(self.screen)

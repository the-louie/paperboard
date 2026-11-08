"""In-memory state of the hub and its screens (config_entry.runtime_data)."""

from __future__ import annotations

import datetime as dt
import time
from collections import deque
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from .devices import DeviceStore
from .pipeline import Frame, encode_bmp_1bit

PAIRING_SECONDS = 300
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

LOG_ENTRIES = 50


@dataclass
class ScreenRuntime:
    """One screen: its secrets and the frame currently served."""

    subentry_id: str
    name: str
    image_token: str
    frame: Frame | None = None
    frame_time: dt.datetime | None = None  # when the current frame was rendered (UTC)
    refresh_rate: int = 900
    stale: bool = False  # True while the last render failed and an older frame is served
    last_error: str | None = None
    telemetry: dict[str, str] = field(default_factory=dict)  # last /api/display headers
    last_checkin: float | None = None  # time.time() of the last authenticated poll
    logs: deque[dict] = field(default_factory=lambda: deque(maxlen=LOG_ENTRIES))

    _bmp: tuple[str, bytes] | None = None

    def bmp(self) -> bytes | None:
        """The current frame as a 1-bit BMP (setup image), cached per frame."""
        if self.frame is None:
            return None
        if self._bmp is None or self._bmp[0] != self.frame.sha:
            self._bmp = (self.frame.sha, encode_bmp_1bit(self.frame.png))
        return self._bmp[1]

    def set_frame(self, frame: Frame) -> bool:
        """Store a new good frame; True when the image actually changed."""
        changed = self.frame is None or frame.sha != self.frame.sha
        self.frame, self.stale, self.last_error = frame, False, None
        self.frame_time = dt.datetime.now(dt.UTC)
        return changed

    def render_failed(self, error: str) -> None:
        """Keep serving the previous frame, flagged stale."""
        self.stale, self.last_error = self.frame is not None, error


@dataclass
class HubRuntime:
    devices: DeviceStore
    screens: dict[str, ScreenRuntime] = field(default_factory=dict)
    renderers: dict[str, Any] = field(default_factory=dict)  # subentry id -> ScreenRenderer
    base_url: str = ""
    pairing_screen: str | None = None
    last_rejected: dict[str, str] | None = None
    pairing_until: float = 0.0

    def open_pairing(self, screen_id: str, seconds: int = PAIRING_SECONDS) -> None:
        """One window per hub; pressing again (or on another screen) restarts it."""
        self.pairing_screen, self.pairing_until = screen_id, time.monotonic() + seconds

    def pairing_target(self) -> str | None:
        if self.pairing_screen and time.monotonic() < self.pairing_until:
            return self.pairing_screen
        self.pairing_screen = None
        return None

    def close_pairing(self) -> None:
        self.pairing_screen, self.pairing_until = None, 0.0

"""In-memory state of the hub and its screens (config_entry.runtime_data)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .pipeline import Frame


@dataclass
class ScreenRuntime:
    """One screen: its secrets and the frame currently served."""

    subentry_id: str
    name: str
    image_token: str
    frame: Frame | None = None
    stale: bool = False  # True while the last render failed and an older frame is served
    last_error: str | None = None

    def set_frame(self, frame: Frame) -> bool:
        """Store a new good frame; True when the image actually changed."""
        changed = self.frame is None or frame.sha != self.frame.sha
        self.frame, self.stale, self.last_error = frame, False, None
        return changed

    def render_failed(self, error: str) -> None:
        """Keep serving the previous frame, flagged stale."""
        self.stale, self.last_error = self.frame is not None, error


@dataclass
class HubRuntime:
    screens: dict[str, ScreenRuntime] = field(default_factory=dict)

"""Keep the hub's layouts current and report broken files as Repairs issues."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .layout_file import LoadResult, changed, load_all

CHECK_EVERY = dt.timedelta(seconds=30)
SIGNAL_LAYOUTS = "paperboard_layouts_changed"


def _issue_id(path: str) -> str:
    return "layout_" + Path(path).stem


class LayoutWatcher:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.user_dir = Path(hass.config.path(DOMAIN))
        self.result = LoadResult()

    async def async_load(self) -> None:
        self.result = await self.hass.async_add_executor_job(load_all, self.user_dir,
                                                             self.result)
        self._sync_issues()

    @callback
    def async_start(self) -> callback:
        return async_track_time_interval(self.hass, self._check, CHECK_EVERY)

    async def _check(self, _now: dt.datetime) -> None:
        if await self.hass.async_add_executor_job(changed, self.user_dir, self.result):
            await self.async_load()
            async_dispatcher_send(self.hass, SIGNAL_LAYOUTS)

    def _sync_issues(self) -> None:
        wanted = {_issue_id(p): (p, msgs) for p, msgs in self.result.errors.items()}
        registry = ir.async_get(self.hass)
        for issue in list(registry.issues.values()):
            if issue.domain == DOMAIN and issue.issue_id.startswith("layout_") \
                    and issue.issue_id not in wanted:
                ir.async_delete_issue(self.hass, DOMAIN, issue.issue_id)
        for issue_id, (path, msgs) in wanted.items():
            ir.async_create_issue(
                self.hass, DOMAIN, issue_id, is_fixable=False, severity=ir.IssueSeverity.ERROR,
                translation_key="layout_invalid",
                translation_placeholders={"file": path, "errors": "\n".join(msgs[:10])})

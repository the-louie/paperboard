"""Repairs for roles bound to entities that no longer exist. The screen is never blanked:
the affected widgets render '—' or collapse while the issue tells the owner what is gone."""

from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import DOMAIN

FIRST_CHECK = 120  # s after setup: entities of slower integrations are still loading
CHECK_EVERY = dt.timedelta(minutes=5)


def bound_entities(roles: dict[str, Any]) -> list[tuple[str, str]]:
    """(role label, entity id) for every bound entity, list roles indexed."""
    out = []
    for role, value in roles.items():
        if isinstance(value, list):
            out += [(f"{role}[{i}]", eid) for i, eid in enumerate(value)]
        elif value:
            out.append((role, value))
    return out


def _issue_id(entity_id: str) -> str:
    return "role_missing_" + entity_id.replace(".", "_")


class RoleWatcher:
    def __init__(self, hass: HomeAssistant, roles: dict[str, Any]) -> None:
        self.hass, self.roles = hass, roles

    @callback
    def async_start(self) -> callback:
        unsub_later = async_call_later(self.hass, FIRST_CHECK, self._check)
        unsub_every = async_track_time_interval(self.hass, self._check, CHECK_EVERY)

        def _stop() -> None:
            unsub_later()
            unsub_every()
        return _stop

    @callback
    def _check(self, _now: dt.datetime | None = None) -> None:
        registry = er.async_get(self.hass)
        missing = {eid: role for role, eid in bound_entities(self.roles)
                   if self.hass.states.get(eid) is None and registry.async_get(eid) is None}
        wanted = {_issue_id(eid) for eid in missing}
        for issue in list(ir.async_get(self.hass).issues.values()):
            if issue.domain == DOMAIN and issue.issue_id.startswith("role_missing_") \
                    and issue.issue_id not in wanted:
                ir.async_delete_issue(self.hass, DOMAIN, issue.issue_id)
        for eid, role in missing.items():
            ir.async_create_issue(self.hass, DOMAIN, _issue_id(eid), is_fixable=False,
                                  severity=ir.IssueSeverity.WARNING,
                                  translation_key="role_missing",
                                  translation_placeholders={"role": role, "entity": eid})

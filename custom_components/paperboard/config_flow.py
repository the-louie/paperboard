"""Config flow: one paperboard hub per Home Assistant instance."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BASE_URL,
    CONF_REFRESH_RATE,
    DEFAULT_REFRESH_RATE,
    DOMAIN,
    MAX_REFRESH_RATE,
    MIN_REFRESH_RATE,
)
from .schema import vol


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Optional(CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "")): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)),
        vol.Required(CONF_REFRESH_RATE,
                     default=defaults.get(CONF_REFRESH_RATE, DEFAULT_REFRESH_RATE)):
            NumberSelector(NumberSelectorConfig(min=MIN_REFRESH_RATE, max=MAX_REFRESH_RATE,
                                                step=60, unit_of_measurement="s",
                                                mode=NumberSelectorMode.BOX)),
    })


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    return {CONF_BASE_URL: (user_input.get(CONF_BASE_URL) or "").rstrip("/"),
            CONF_REFRESH_RATE: int(user_input[CONF_REFRESH_RATE])}


class PaperboardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the hub. Screens are added later as config subentries (T-16)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Paperboard", data={},
                                           options=_clean(user_input))
        try:
            suggested = get_url(self.hass, allow_external=False, allow_cloud=False)
        except NoURLAvailableError:
            suggested = ""
        return self.async_show_form(step_id="user",
                                    data_schema=_schema({CONF_BASE_URL: suggested}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PaperboardOptionsFlow:
        return PaperboardOptionsFlow()


class PaperboardOptionsFlow(OptionsFlowWithReload):
    """Edit hub defaults; the entry reloads automatically when they change."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        return self.async_show_form(step_id="init",
                                    data_schema=_schema(dict(self.config_entry.options)))

"""Config flow: one paperboard hub per Home Assistant instance."""

from __future__ import annotations

import secrets
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BASE_URL,
    CONF_IMAGE_TOKEN,
    CONF_LAYOUT,
    CONF_NAME,
    CONF_PROFILE,
    CONF_REFRESH_RATE,
    DEFAULT_LAYOUT,
    DEFAULT_PROFILE,
    DEFAULT_REFRESH_RATE,
    DOMAIN,
    MAX_REFRESH_RATE,
    MIN_REFRESH_RATE,
    PROFILES,
    SUBENTRY_SCREEN,
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

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_SCREEN: ScreenSubentryFlow}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PaperboardOptionsFlow:
        return PaperboardOptionsFlow()


class PaperboardOptionsFlow(OptionsFlow):
    """Edit hub defaults. The entry's update listener reloads it (see __init__.py)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        return self.async_show_form(step_id="init",
                                    data_schema=_schema(dict(self.config_entry.options)))


def _screen_schema(defaults: dict[str, Any], hub_refresh: int) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): TextSelector(),
        vol.Required(CONF_PROFILE, default=defaults.get(CONF_PROFILE, DEFAULT_PROFILE)):
            SelectSelector(SelectSelectorConfig(options=list(PROFILES),
                                                mode=SelectSelectorMode.DROPDOWN,
                                                translation_key="profile")),
        vol.Required(CONF_LAYOUT, default=defaults.get(CONF_LAYOUT, DEFAULT_LAYOUT)):
            TextSelector(),
        vol.Required(CONF_REFRESH_RATE, default=defaults.get(CONF_REFRESH_RATE, hub_refresh)):
            NumberSelector(NumberSelectorConfig(min=MIN_REFRESH_RATE, max=MAX_REFRESH_RATE,
                                                step=60, unit_of_measurement="s",
                                                mode=NumberSelectorMode.BOX)),
    })


class ScreenSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure one e-ink screen. Pairing data (MAC, keys) is added later (T-19)."""

    def _hub_refresh(self) -> int:
        return int(self._get_entry().options.get(CONF_REFRESH_RATE, DEFAULT_REFRESH_RATE))

    @staticmethod
    def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
        return {CONF_NAME: user_input[CONF_NAME].strip(), CONF_PROFILE: user_input[CONF_PROFILE],
                CONF_LAYOUT: user_input[CONF_LAYOUT].strip() or DEFAULT_LAYOUT,
                CONF_REFRESH_RATE: int(user_input[CONF_REFRESH_RATE])}

    async def async_step_user(self, user_input: dict[str, Any] | None = None
                              ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = self._clean(user_input)
            if not data[CONF_NAME]:
                errors[CONF_NAME] = "name_required"
            else:
                data[CONF_IMAGE_TOKEN] = secrets.token_urlsafe(32)
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        return self.async_show_form(step_id="user", errors=errors,
                                    data_schema=_screen_schema(user_input or {},
                                                               self._hub_refresh()))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None
                                     ) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            data = self._clean(user_input)
            if data[CONF_NAME]:
                # Keep pairing data (mac, keys) that the form does not show.
                return self.async_update_and_abort(self._get_entry(), subentry,
                                                   title=data[CONF_NAME],
                                                   data={**subentry.data, **data})
        return self.async_show_form(step_id="reconfigure",
                                    data_schema=_screen_schema(dict(subentry.data),
                                                               self._hub_refresh()))

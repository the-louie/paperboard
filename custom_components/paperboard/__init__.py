"""Paperboard: designed e-ink dashboards from Home Assistant data, served to TRMNL devices."""

from __future__ import annotations

import secrets

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_BASE_URL,
    CONF_IMAGE_TOKEN,
    CONF_LAYOUT,
    CONF_NAME,
    CONF_PROFILE,
    CONF_REFRESH_RATE,
    CONF_ROLES,
    DEFAULT_PROFILE,
    DEFAULT_REFRESH_RATE,
    DOMAIN,
    PROFILES,
    SUBENTRY_SCREEN,
)
from .devices import DeviceStore
from .fonts import load_fonts
from .layout_watch import LayoutWatcher
from .layouts import get_layout
from .pipeline import PanelProfile
from .renderer import ScreenRenderer
from .runtime import HubRuntime, ScreenRuntime
from .views import DisplayView, ImageView, LogView, SetupView

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.IMAGE, Platform.SENSOR]

type PaperboardConfigEntry = ConfigEntry[HubRuntime]

_VIEWS_REGISTERED = f"{DOMAIN}_views_registered"


async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry) -> bool:
    """Set up the hub: runtime state, views, and one device per screen subentry."""
    if not hass.data.get(_VIEWS_REGISTERED):
        # Views cannot be unregistered; they look the hub up per request instead.
        hass.http.register_view(ImageView(hass))
        hass.http.register_view(SetupView(hass))
        hass.http.register_view(DisplayView(hass))
        hass.http.register_view(LogView(hass))
        hass.data[_VIEWS_REGISTERED] = True

    fonts = await hass.async_add_executor_job(load_fonts)
    watcher = LayoutWatcher(hass)
    await watcher.async_load()
    entry.async_on_unload(watcher.async_start())
    store = DeviceStore(hass, entry.entry_id)
    await store.async_load()
    hub = HubRuntime(devices=store, base_url=entry.options.get(CONF_BASE_URL, ""),
                     layouts=watcher, roles=dict(entry.options.get(CONF_ROLES, {})))
    registry = dr.async_get(hass)
    wanted: set[str] = set()
    for subentry in list(entry.subentries.values()):
        if subentry.subentry_type != SUBENTRY_SCREEN:
            continue
        if not subentry.data.get(CONF_IMAGE_TOKEN):
            # Before the listener exists, so this does not trigger a reload.
            hass.config_entries.async_update_subentry(
                entry, subentry,
                data={**subentry.data, CONF_IMAGE_TOKEN: secrets.token_urlsafe(32)})
            subentry = entry.subentries[subentry.subentry_id]
        screen = hub.screens[subentry.subentry_id] = ScreenRuntime(
            subentry_id=subentry.subentry_id,
            name=subentry.data.get(CONF_NAME, subentry.title),
            image_token=subentry.data[CONF_IMAGE_TOKEN],
            refresh_rate=int(subentry.data.get(
                CONF_REFRESH_RATE, entry.options.get(CONF_REFRESH_RATE, DEFAULT_REFRESH_RATE))),
        )
        device = registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            config_subentry_id=subentry.subentry_id,
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.data.get(CONF_NAME, subentry.title),
            manufacturer="Paperboard",
            model=subentry.data.get(CONF_PROFILE),
        )
        wanted.add(device.id)
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if device.id not in wanted:
            registry.async_remove_device(device.id)
    for screen_id in [s for s in store.devices if s not in hub.screens]:
        store.forget(screen_id)  # the screen was deleted: its device key dies with it

    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    for subentry_id, screen in hub.screens.items():
        data = entry.subentries[subentry_id].data
        width, height, depth, limit = PROFILES.get(data.get(CONF_PROFILE, DEFAULT_PROFILE),
                                                   PROFILES[DEFAULT_PROFILE])
        renderer = ScreenRenderer(hass, screen, get_layout(data.get(CONF_LAYOUT, "")),
                                  PanelProfile(width, height, depth, limit), fonts)
        hub.renderers[subentry_id] = renderer
        renderer.async_start()
        entry.async_on_unload(renderer.async_stop)
    # Options and subentry changes both fire update listeners; reload picks them all up.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PaperboardConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

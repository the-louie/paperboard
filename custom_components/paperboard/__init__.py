"""Paperboard: designed e-ink dashboards from Home Assistant data, served to TRMNL devices."""

from __future__ import annotations

import secrets

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import (
    i18n,
    pipeline,
    widget_registry,  # noqa: F401 - registers the layout widget types
)
from .compose import as_layout, scheduled_layout
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
    PROFILE_ALIASES,
    PROFILE_AUTO,
    SUBENTRY_SCREEN,
)
from .data import CalendarCache, ForecastCache, PriceProvider, SolarProvider
from .devices import DeviceStore
from .fonts import load_fonts
from .layout_watch import SIGNAL_LAYOUTS, LayoutWatcher
from .layouts import Layout, get_layout
from .pipeline import PanelProfile
from .profiles import names as profile_names
from .profiles import resolve as resolve_profile
from .raster_worker import WORKER
from .renderer import DEFAULT_CYCLE, ScreenRenderer
from .role_watch import RoleWatcher
from .runtime import HubRuntime, ScreenRuntime
from .style import Theme
from .views import DisplayView, ImageView, LogView, SetupView

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.IMAGE, Platform.SENSOR]

type PaperboardConfigEntry = ConfigEntry[HubRuntime]

_VIEWS_REGISTERED = f"{DOMAIN}_views_registered"


WARMUP_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>'

async def async_setup_entry(hass: HomeAssistant, entry: PaperboardConfigEntry) -> bool:
    """Set up the hub: runtime state, views, and one device per screen subentry."""
    if not hass.data.get(_VIEWS_REGISTERED):
        # Views cannot be unregistered; they look the hub up per request instead.
        hass.http.register_view(ImageView(hass))
        hass.http.register_view(SetupView(hass))
        hass.http.register_view(DisplayView(hass))
        hass.http.register_view(LogView(hass))
        hass.data[_VIEWS_REGISTERED] = True

    # Warm the model-registry cache off the loop: resolve() is called from the loop later.
    await hass.async_add_executor_job(profile_names)
    await hass.async_add_executor_job(i18n.load_catalogs)  # drawn texts; file reads off the loop
    fonts = await hass.async_add_executor_job(load_fonts)
    if pipeline.USE_WORKER:  # start the render process now, not on the first frame (B-088)
        # Fire and forget: async_add_executor_job returns a Future, not a coroutine.
        hass.async_add_executor_job(WORKER.render, WARMUP_SVG, str(fonts.font_dir))

        async def _stop_worker(_event: Event) -> None:
            # B-092: HA does not unload config entries on stop; end the child here too.
            await hass.async_add_executor_job(WORKER.shutdown)

        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop_worker))
    watcher = LayoutWatcher(hass)
    await watcher.async_load()
    entry.async_on_unload(watcher.async_start())
    # A changed layout file: reload the hub so every renderer picks the new spec up.
    @callback
    def _layouts_changed() -> None:
        hass.config_entries.async_schedule_reload(entry.entry_id)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_LAYOUTS, _layouts_changed))
    store = DeviceStore(hass, entry.entry_id)
    await store.async_load()
    hub = HubRuntime(devices=store, base_url=entry.options.get(CONF_BASE_URL, ""),
                     layouts=watcher, roles=dict(entry.options.get(CONF_ROLES, {})))
    entry.async_on_unload(RoleWatcher(hass, hub.roles).async_start())
    hub.forecasts = ForecastCache(hass, hub.roles.get("weather"))
    entry.async_on_unload(hub.forecasts.async_start())
    hub.prices = PriceProvider(hass, hub.roles.get("price"))
    entry.async_on_unload(hub.prices.async_start())
    hub.solar = SolarProvider(hass, hub.roles.get("solar_forecast_today"))
    entry.async_on_unload(hub.solar.async_start())
    hub.calendars = CalendarCache(hass, hub.roles.get("calendars"))
    entry.async_on_unload(hub.calendars.async_start())
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
        if (paired := store.devices.get(subentry.subentry_id)) is not None:
            screen.last_checkin, screen.last_rate = paired.last_checkin, paired.last_rate
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
        choice = data.get(CONF_PROFILE, DEFAULT_PROFILE)
        choice = PROFILE_ALIASES.get(choice, choice)
        auto = choice == PROFILE_AUTO
        prof = resolve_profile(screen.telemetry.get("Model"), None, None) if auto \
            else resolve_profile(choice)
        renderer = ScreenRenderer(hass, screen,
                                  layout_for(watcher, data.get(CONF_LAYOUT, ""), prof.bit_depth),
                                  PanelProfile(prof.width, prof.height, prof.bit_depth,
                                               prof.byte_limit), fonts, hub)
        renderer.auto_profile = auto
        renderer.layout_name = data.get(CONF_LAYOUT, "")
        spec = watcher.result.layouts.get(renderer.layout_name)
        names = getattr(spec, "cycle", None) or DEFAULT_CYCLE
        renderer.set_cycle({n: layout_for(watcher, n, prof.bit_depth) for n in names
                            if n in watcher.result.layouts},
                           getattr(spec, "hold_minutes", None))
        hub.renderers[subentry_id] = renderer
        renderer.async_start()
        entry.async_on_unload(renderer.async_stop)
    # Options and subentry changes both fire update listeners; reload picks them all up.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


def layout_for(watcher: LayoutWatcher, name: str, depth: int) -> Layout:
    """A YAML layout (bundled or the user's) by name, else a built-in code layout."""
    spec = watcher.result.layouts.get(name)
    if spec is not None and hasattr(spec, "entries"):  # a schedule of other layouts
        return scheduled_layout(spec, lambda n: layout_for(watcher, n, depth))
    if spec is not None:
        return as_layout(spec, lambda: Theme(bit_depth=depth))
    return get_layout(name)


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PaperboardConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data.devices.async_flush()
    # A reload starts a fresh worker on its first render. Off the loop: shutdown waits.
    await hass.async_add_executor_job(WORKER.shutdown)
    return unloaded

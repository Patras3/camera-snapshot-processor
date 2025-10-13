"""The Camera Snapshot Processor integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import setup_api
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CAMERA]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Camera Snapshot Processor component."""
    # Register API endpoints
    setup_api(hass)

    # Register the custom panel static files
    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=f"/{DOMAIN}_panel",
                path=str(frontend_path),
                cache_headers=False,
            )
        ]
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Camera Snapshot Processor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entry"] = entry

    # Register single unified panel (only if not already registered)
    panel_url = f"/{DOMAIN}_panel/panel.html"

    # Check if panel is already registered
    if DOMAIN not in hass.data.get("frontend_panels", {}):
        try:
            frontend.async_register_built_in_panel(
                hass,
                component_name="iframe",
                sidebar_title="Snapshot Processor",
                sidebar_icon="mdi:camera-enhance",
                frontend_url_path=DOMAIN,
                config={"url": panel_url},
                require_admin=True,
            )
            _LOGGER.info("Registered Snapshot Processor panel")
        except ValueError as err:
            _LOGGER.warning(
                "Panel already registered (this is normal on reload): %s", err
            )
    else:
        _LOGGER.debug("Panel already exists, skipping registration")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Config entry updated, reloading integration to apply changes")
    await hass.config_entries.async_reload(entry.entry_id)
    _LOGGER.info("Integration reload complete")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop("entry", None)

        # Unregister panel if this is the last entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if len(entries) <= 1:  # This entry is being unloaded
            try:
                frontend.async_remove_panel(hass, DOMAIN)
                _LOGGER.info("Unregistered Snapshot Processor panel")
            except KeyError:
                _LOGGER.debug("Panel was not registered")

    return unload_ok

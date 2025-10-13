"""Config flow for Camera Snapshot Processor integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CameraSnapshotProcessorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Camera Snapshot Processor."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step - create single integration entry."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Create single integration entry with empty cameras dict
            return self.async_create_entry(
                title="Camera Snapshot Processor",
                data={"cameras": {}},
            )

        # Show simple confirmation form
        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "step_description": (
                    "Set up Camera Snapshot Processor.\n\n"
                    "After setup, use the Snapshot Processor panel "
                    "in the sidebar to add and configure cameras with live preview."
                )
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow - redirect to custom panel."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Redirect to custom panel for configuration."""
        return self.async_abort(
            reason="use_panel",
            description_placeholders={"panel_url": f"/{DOMAIN}"},
        )

"""Config flow for the Voice Assistant Bridge integration.

Single-step UI: ask for the voice-assistant base URL (e.g.
http://localhost:3000 if HA is in host network mode on the same Pi as
voice-assistant) and a Bearer API key from HTTP_API_KEYS.
"""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN


class VoiceAssistantBridgeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Walk the user through registering a voice-assistant endpoint."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect base URL + API key, then probe `/health` before saving."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            api_key = user_input[CONF_API_KEY]

            await self.async_set_unique_id(base_url)
            self._abort_if_unique_id_configured()

            # Verify reachability against /health (no auth required) so the
            # user gets immediate feedback instead of failing at the first
            # voice command.
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    f"{base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status != 200:
                        errors["base"] = "cannot_connect"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Voice Assistant Bridge ({base_url})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_KEY: api_key,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

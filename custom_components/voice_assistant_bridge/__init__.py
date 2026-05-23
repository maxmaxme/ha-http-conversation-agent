"""The Voice Assistant Bridge integration.

Routes HA Assist conversation requests to the standalone voice-assistant
service (https://github.com/maxmaxme/voice-assistant) via its `POST /assist`
HTTP endpoint, instead of HA's built-in intent handling. STT and TTS
slots in the HA pipeline are not affected — they keep using whatever the
user has configured (Whisper / Piper / etc.).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Voice Assistant Bridge from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Voice Assistant Bridge config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

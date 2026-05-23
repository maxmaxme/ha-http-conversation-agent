"""Conversation entity that forwards user text to the voice-assistant service."""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

import aiohttp
from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_TIMEOUT_SEC, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register the conversation entity for this config entry."""
    async_add_entities([VoiceAssistantBridgeAgent(entry)])


class VoiceAssistantBridgeAgent(ConversationEntity):
    """A HA conversation agent that delegates to voice-assistant's HTTP API.

    The voice-assistant repo keeps the user's session server-side via
    OpenAI Responses API + previous_response_id, so we don't need to ship
    history with each call. HA's conversation_id is logged but not
    forwarded — a single conversation thread per voice-assistant instance
    is the v1 contract.
    """

    _attr_has_entity_name = True
    _attr_name = "Voice Assistant Bridge"
    _attr_supported_features = conversation.ConversationEntityFeature(0)

    def __init__(self, entry: ConfigEntry) -> None:
        """Store the config entry; URL/key are read fresh on each call."""
        self._entry = entry
        self._attr_unique_id = entry.entry_id

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Voice-assistant handles language detection itself (OpenAI LLM is multilingual)."""
        return conversation.MATCH_ALL

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Forward `user_input.text` to voice-assistant `POST /assist`."""
        base_url = self._entry.data[CONF_BASE_URL].rstrip("/")
        api_key = self._entry.data[CONF_API_KEY]
        url = f"{base_url}/assist"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {"text": user_input.text}

        _LOGGER.debug(
            "Forwarding to voice-assistant url=%s text=%r conv_id=%s",
            url,
            user_input.text,
            user_input.conversation_id,
        )

        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                url,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SEC),
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except asyncio.TimeoutError:
            return _error_result(
                user_input,
                f"voice-assistant timed out (>{DEFAULT_TIMEOUT_SEC}s)",
            )
        except aiohttp.ClientResponseError as err:
            return _error_result(
                user_input,
                f"voice-assistant returned {err.status}: {err.message}",
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("voice-assistant request failed")
            return _error_result(user_input, f"voice-assistant unreachable: {err}")

        reply_text = (data or {}).get("response", "")
        if not reply_text:
            _LOGGER.warning("voice-assistant returned empty reply: %r", data)
            return _error_result(user_input, "voice-assistant returned empty reply")

        response_intent = intent.IntentResponse(language=user_input.language)
        response_intent.async_set_speech(reply_text)
        return ConversationResult(
            response=response_intent,
            conversation_id=user_input.conversation_id,
            continue_conversation=bool((data or {}).get("continue_conversation")),
        )


def _error_result(user_input: ConversationInput, message: str) -> ConversationResult:
    """Build a ConversationResult carrying an error response."""
    response_intent = intent.IntentResponse(language=user_input.language)
    response_intent.async_set_error(
        intent.IntentResponseErrorCode.UNKNOWN,
        message,
    )
    return ConversationResult(
        response=response_intent,
        conversation_id=user_input.conversation_id,
    )

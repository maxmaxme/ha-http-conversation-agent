# HTTP Conversation Agent

Home Assistant conversation agent that forwards every Assist query to a
configurable HTTP backend and returns the response to HA's TTS stage.
The component itself is backend-agnostic — point it at anything that
implements the contract below: self-hosted LLM proxies, n8n webhooks,
FastAPI services, or the reference implementation
[`maxmaxme/voice-assistant`](https://github.com/maxmaxme/voice-assistant).

Designed to slot into the HA Voice PE pipeline:

```
Voice PE ──▶ HA STT ──▶ HTTP Conversation Agent ──POST {endpoint}──▶ your backend ──▶ HA TTS ──▶ Voice PE
```

## Contract

The backend must speak this minimal HTTP contract:

- **Request:** `POST {base_url}{endpoint_path}`
  - `Content-Type: application/json`
  - `Authorization: Bearer <api_key>` (only sent when an API key is configured)
  - Body: `{"text": "<user utterance>"}`
- **Response:** JSON object with
  - `response: string` — text to speak back (required, non-empty)
  - `continue_conversation: bool` — optional; when `true`, HA's Assist
    pipeline reopens the mic without a fresh wake-word
- **Health probe (optional):** `GET {base_url}{health_path}` must return
  HTTP 200. Used only by the config flow at setup time; leave the path
  blank in the UI to skip it.

That's the whole interface. Any backend that wraps its handler in those
shapes works.

## Installation (HACS)

One-click via [My Home Assistant](https://my.home-assistant.io/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maxmaxme&repository=ha-http-conversation-agent&category=integration)

Or manually:

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/maxmaxme/ha-http-conversation-agent`, category
   **Integration**.
2. Find **HTTP Conversation Agent** in HACS → Download.
3. Restart Home Assistant.
4. Then add the integration in HA:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=http_conversation_agent)

   Or: Settings → Devices & Services → **Add Integration** → "HTTP
   Conversation Agent".
5. Fill in:
   - **Base URL** — e.g. `http://localhost:3000`.
   - **API key** — optional Bearer token. Leave empty for unauthenticated
     backends.
   - **Conversation endpoint path** — default `/assist`. Use whatever
     route your backend exposes.
   - **Health-check path** — default `/health`. Leave blank to skip the
     setup-time probe.

## Using as the conversation agent

Settings → Voice assistants → pick your pipeline → **Conversation agent**
→ "HTTP Conversation Agent".

## Migrating from `voice_assistant_bridge` (≤ 0.2.x)

The integration was renamed in 0.3 from `voice_assistant_bridge` /
"Voice Assistant Bridge" to `http_conversation_agent` / "HTTP
Conversation Agent" to reflect that any HTTP backend works, not just
`voice-assistant`. Home Assistant treats this as a new integration —
remove the old entry in Settings → Devices & Services, then add the new
one. Your existing `voice-assistant` URL + API key still work as-is
(defaults match the previous behaviour: endpoint `/assist`, health
`/health`).

## License

[MIT](LICENSE) © 2026 maxmaxme. Permissive on purpose — this is a Home Assistant
custom integration, so it matches the HA ecosystem's norms (HA core is
Apache-2.0) and stays freely reusable.

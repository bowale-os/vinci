"""
ElevenLabs TTS client.

Converts appeal letter text to MP3 audio using the ElevenLabs v1 API.
Returns base64-encoded MP3 so the frontend can play it directly without
a separate file hosting step — important for hackathon demo stability.

Voice: Rachel (21m00Tcm4TlvDq8ikWAM) — calm, neutral American English.
  stability=0.55        → consistent, professional delivery
  similarity_boost=0.75 → stays close to the reference voice
  style=0.0             → no expressive styling — clinical tone
  use_speaker_boost=True → cleaner audio on laptop speakers
"""
import base64

import httpx

from config import settings

_BASE = "https://api.elevenlabs.io/v1"
_HEADERS = {
    "xi-api-key": settings.elevenlabs_api_key,
    "Content-Type": "application/json",
}

# Character limit safety check — free tier is 10k chars/month
_MAX_CHARS = 4500  # single appeal letter cap; truncate with note if exceeded


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CHARS:
        return text
    truncated = text[:_MAX_CHARS]
    # Cut at last sentence boundary
    last_period = truncated.rfind(". ")
    if last_period > _MAX_CHARS - 300:
        truncated = truncated[: last_period + 1]
    return truncated + "\n\n[Audio truncated at character limit. Full letter available as text.]"


async def synthesize_speech(text: str) -> str:
    """
    Convert text to speech via ElevenLabs.
    Returns a data URI string: "data:audio/mpeg;base64,<encoded_mp3>"
    that the frontend <audio> element can play directly.
    """
    if not settings.elevenlabs_api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Add it to backend/.env to enable audio."
        )

    clean_text = _truncate(text.strip())
    voice_id   = settings.elevenlabs_voice_id

    payload = {
        "text": clean_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{_BASE}/text-to-speech/{voice_id}",
            headers=_HEADERS,
            json=payload,
        )

    if resp.status_code == 401:
        raise RuntimeError("ElevenLabs API key is invalid or expired.")
    if resp.status_code == 429:
        raise RuntimeError("ElevenLabs rate limit reached. Try again in a moment.")
    resp.raise_for_status()

    mp3_bytes  = resp.content
    b64        = base64.b64encode(mp3_bytes).decode("utf-8")
    return f"data:audio/mpeg;base64,{b64}"


async def list_voices() -> list[dict]:
    """Return available ElevenLabs voices for voice selection UI."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/voices", headers=_HEADERS)
        resp.raise_for_status()
    voices = resp.json().get("voices", [])
    return [
        {
            "voice_id": v["voice_id"],
            "name": v["name"],
            "category": v.get("category", ""),
            "preview_url": v.get("preview_url", ""),
        }
        for v in voices
    ]

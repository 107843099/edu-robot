import asyncio
import base64
import os
import random
import time
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from yova_shared import EventEmitter, get_clean_logger
from yova_shared.api import ApiConnector

from .webhook_stream import collect_text_from_ndjson_body, parse_n8n_stream_line

SUPPORTED_FORMATS = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "aac": "audio/aac",
    "m4a": "audio/mp4",
    "wma": "audio/x-ms-wma",
}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _get_file_format(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip(".")


def _is_format_supported(format_ext: str) -> bool:
    return format_ext in SUPPORTED_FORMATS


class N8nConnector(ApiConnector):
    """Send transcripts to an n8n Webhook and stream NDJSON token output as events."""

    def __init__(self, logger=None):
        super().__init__()
        self.logger = get_clean_logger("n8n_connector", logger)
        self.event_emitter = EventEmitter(logger=logger)
        self.webhook_url: Optional[str] = None
        self.auth_header_name: Optional[str] = None
        self.auth_header_value: Optional[str] = None
        self.timeout_seconds: float = 120.0
        self.stream: bool = True
        self.user_agent: str = DEFAULT_USER_AGENT
        self.extra_payload: Dict[str, Any] = {}
        self.chat_input_key: str = "chatInput"
        self.session_id_key: str = "sessionId"
        self.session_switch_threshold_seconds: float = 30.0
        self.include_hmmm_chunk: bool = True
        self.thinking_delay_seconds: float = 2.0
        self.is_connected: bool = False
        self._client: Optional[httpx.AsyncClient] = None
        self._effective_session_id: Optional[str] = None
        self._last_session_decision_time: Optional[float] = None

    async def configure(self, config: Any) -> None:
        self.webhook_url = (config.get("webhook_url") or os.getenv("N8N_WEBHOOK_URL") or "").strip()
        self.auth_header_name = (config.get("auth_header_name") or os.getenv("N8N_AUTH_HEADER_NAME") or "").strip() or None
        raw_val = config.get("auth_header_value")
        if raw_val is None:
            raw_val = os.getenv("N8N_AUTH_HEADER_VALUE")
        self.auth_header_value = (raw_val or "").strip() or None
        self.timeout_seconds = float(config.get("timeout_seconds", self.timeout_seconds))
        self.stream = bool(config.get("stream", self.stream))
        self.user_agent = str(config.get("user_agent", self.user_agent))
        extra = config.get("extra_payload")
        self.extra_payload = dict(extra) if isinstance(extra, dict) else {}
        self.chat_input_key = str(config.get("chat_input_key", self.chat_input_key))
        self.session_id_key = str(config.get("session_id_key", self.session_id_key))
        self.session_switch_threshold_seconds = float(
            config.get(
                "session_switch_threshold_seconds",
                self.session_switch_threshold_seconds,
            )
        )
        self.include_hmmm_chunk = bool(config.get("include_hmmm_chunk", self.include_hmmm_chunk))
        self.thinking_delay_seconds = float(config.get("thinking_delay_seconds", self.thinking_delay_seconds))

    def get_thinking_sound_base64(self, thinking_index: Optional[int] = None) -> str:
        """
        Load one of `yova_shared/assets/thinking_{1..4}.wav` and return it as a `data:audio/wav;base64,...` URL.
        """
        if thinking_index is None:
            thinking_index = random.randint(1, 4)
        if not 1 <= thinking_index <= 4:
            raise ValueError(f"Invalid thinking_index={thinking_index}. Expected 1..4.")

        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "yova_shared",
            "assets",
            f"thinking_{thinking_index}.wav",
        )
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found!")

        format_ext = _get_file_format(file_path)
        if not _is_format_supported(format_ext):
            supported_formats = ", ".join(SUPPORTED_FORMATS.keys())
            raise ValueError(
                f"Unsupported audio format: {format_ext}. Supported formats: {supported_formats}"
            )

        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
        base64_string = base64.b64encode(audio_data).decode("utf-8")
        mime_type = SUPPORTED_FORMATS[format_ext]
        return f"data:{mime_type};base64,{base64_string}"

    async def _emit_thinking_sounds_until_first_chunk(
        self, message_id: str, first_server_chunk_received: asyncio.Event
    ) -> None:
        """
        Periodically emit low-priority `message_chunk` containing thinking audio while we wait
        for the first server response chunk.
        """
        # Avoid busy loop if misconfigured.
        delay_seconds = max(0.01, float(self.thinking_delay_seconds))

        while not first_server_chunk_received.is_set():
            try:
                await asyncio.wait_for(first_server_chunk_received.wait(), timeout=delay_seconds)
                # Event is set -> stop without playing another thinking sound.
                break
            except asyncio.TimeoutError:
                # No server chunk yet -> play thinking sound.
                pass

            if first_server_chunk_received.is_set():
                break

            thinking_index = random.randint(1, 4)
            chunk_data = {
                "id": message_id,
                "text": self.get_thinking_sound_base64(thinking_index),
                # Low priority so the real server text chunk (priority 100) preempts filler.
                "priority_score": 0,
            }
            await self.event_emitter.emit_event("message_chunk", chunk_data)

    async def connect(self) -> None:
        if not self.webhook_url:
            raise ConnectionError("n8n webhook_url is not configured")
        parsed = urlparse(self.webhook_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ConnectionError(f"Invalid n8n webhook URL: {self.webhook_url!r}")
        timeout = httpx.Timeout(self.timeout_seconds)
        self._client = httpx.AsyncClient(timeout=timeout)
        self.is_connected = True
        self.logger.info("N8nConnector: ready for webhook requests")

    def _resolve_session_id(self, detected_user_id: Optional[str]) -> str:
        candidate = (detected_user_id or "").strip() or "anonymous"
        now = time.monotonic()

        if self._effective_session_id is None:
            self._effective_session_id = candidate
            self._last_session_decision_time = now
            return self._effective_session_id

        assert self._last_session_decision_time is not None
        elapsed = now - self._last_session_decision_time
        if elapsed >= max(0.0, float(self.session_switch_threshold_seconds)):
            self._effective_session_id = candidate

        self._last_session_decision_time = now
        return self._effective_session_id

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "identity",
            "User-Agent": self.user_agent,
            "X-Accel-Buffering": "no",
        }
        if self.auth_header_name and self.auth_header_value is not None:
            headers[self.auth_header_name] = self.auth_header_value
        return headers

    def get_hmmm_sound_base64(self) -> str:
        file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "yova_shared",
            "assets",
            f"hmmm_nova_{random.randint(1, 9)}.wav",
        )
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found!")
        format_ext = _get_file_format(file_path)
        if not _is_format_supported(format_ext):
            supported_formats = ", ".join(SUPPORTED_FORMATS.keys())
            raise ValueError(
                f"Unsupported audio format: {format_ext}. Supported formats: {supported_formats}"
            )
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()
        base64_string = base64.b64encode(audio_data).decode("utf-8")
        mime_type = SUPPORTED_FORMATS[format_ext]
        return f"data:{mime_type};base64,{base64_string}"

    async def send_message(self, text: str, session_id: Optional[str] = None) -> Any:
        if not self.is_connected or not self._client:
            raise ConnectionError("Not connected. Call connect() first.")
        if not text or not text.strip():
            return ""

        message_id = str(uuid.uuid4())
        sid = self._resolve_session_id(session_id)

        first_server_chunk_received = asyncio.Event()
        thinking_task: Optional[asyncio.Task] = None

        if self.include_hmmm_chunk:
            chunk_data = {
                "id": message_id,
                "text": self.get_hmmm_sound_base64(),
                "priority_score": 0,
            }
            await self.event_emitter.emit_event("message_chunk", chunk_data)
            thinking_task = asyncio.create_task(
                self._emit_thinking_sounds_until_first_chunk(message_id, first_server_chunk_received)
            )

        await self.event_emitter.emit_event("processing_started", {"id": message_id})

        if thinking_task is None:
            thinking_task = asyncio.create_task(
                self._emit_thinking_sounds_until_first_chunk(message_id, first_server_chunk_received)
            )

        payload = {
            **self.extra_payload,
            self.chat_input_key: text,
            self.session_id_key: sid,
        }

        try:
            if self.stream:
                full = await self._send_streaming(message_id, payload, first_server_chunk_received)
            else:
                full = await self._send_buffered(message_id, payload, first_server_chunk_received)
            completion_data = {"id": message_id, "text": full}
            await self.event_emitter.emit_event("message_completed", completion_data)
            return full
        except Exception as e:
            self.logger.error(f"N8nConnector: request failed: {e}")
            raise ConnectionError(f"Failed to send message to n8n: {e}") from e
        finally:
            # Ensure we never keep emitting filler chunks after the request ends.
            first_server_chunk_received.set()
            if thinking_task is not None:
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass

    async def _send_streaming(
        self,
        message_id: str,
        payload: Dict[str, Any],
        first_server_chunk_received: asyncio.Event,
    ) -> str:
        assert self._client is not None
        full_response = ""
        first_token = True
        async with self._client.stream(
            "POST",
            self.webhook_url,
            json=payload,
            headers=self._build_headers(),
        ) as response:
            response.raise_for_status()
            enc = (response.headers.get("content-encoding") or "").strip().lower()
            if enc and enc != "identity":
                self.logger.warning(
                    "N8nConnector: Content-Encoding=%r (identity was requested)", enc
                )
            async for line in response.aiter_lines():
                piece = parse_n8n_stream_line(line)
                if piece is None:
                    continue
                if first_token:
                    first_server_chunk_received.set()
                    await self.event_emitter.emit_event("processing_completed", {"id": message_id})
                    first_token = False
                full_response += piece
                await self.event_emitter.emit_event(
                    "message_chunk",
                    {"id": message_id, "text": piece, "priority_score": 100},
                )
        if first_token:
            # No server chunk arrived; stop thinking filler.
            first_server_chunk_received.set()
            await self.event_emitter.emit_event("processing_completed", {"id": message_id})
        return full_response

    async def _send_buffered(
        self,
        message_id: str,
        payload: Dict[str, Any],
        first_server_chunk_received: asyncio.Event,
    ) -> str:
        assert self._client is not None
        resp = await self._client.post(
            self.webhook_url,
            json=payload,
            headers=self._build_headers(),
        )
        resp.raise_for_status()
        body = resp.text
        ndjson_text = collect_text_from_ndjson_body(body)
        if ndjson_text:
            first_server_chunk_received.set()
            await self.event_emitter.emit_event("processing_completed", {"id": message_id})
            await self.event_emitter.emit_event(
                "message_chunk",
                {"id": message_id, "text": ndjson_text, "priority_score": 100},
            )
            return ndjson_text
        await self.event_emitter.emit_event("processing_completed", {"id": message_id})
        text = body.strip()
        if text:
            await self.event_emitter.emit_event(
                "message_chunk",
                {"id": message_id, "text": text, "priority_score": 100},
            )
        return text

    def add_event_listener(self, event_type: str, listener):
        self.event_emitter.add_event_listener(event_type, listener)

    def remove_event_listener(self, event_type: str, listener):
        self.event_emitter.remove_event_listener(event_type, listener)

    def clear_event_listeners(self, event_type: str = None):
        self.event_emitter.clear_event_listeners(event_type)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self.is_connected = False

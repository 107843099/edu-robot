import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch

import pytest

from yova_api_n8n.n8n_connector import N8nConnector


class TestN8nConnector:
    @pytest.fixture
    def connector(self):
        return N8nConnector()

    @pytest.mark.asyncio
    async def test_configure_and_connect(self, connector):
        await connector.configure({"webhook_url": "https://example.com/hook"})
        await connector.connect()
        assert connector.is_connected
        assert connector._client is not None
        await connector.close()

    @pytest.mark.asyncio
    async def test_connect_missing_url(self, connector):
        await connector.configure({"webhook_url": ""})
        with pytest.raises(ConnectionError, match="webhook_url"):
            await connector.connect()

    @pytest.mark.asyncio
    async def test_connect_invalid_scheme(self, connector):
        await connector.configure({"webhook_url": "ftp://bad/wrong"})
        with pytest.raises(ConnectionError, match="Invalid"):
            await connector.connect()

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, connector):
        await connector.configure({"webhook_url": "https://example.com/hook"})
        with pytest.raises(ConnectionError, match="Not connected"):
            await connector.send_message("hi")

    @pytest.mark.asyncio
    async def test_send_empty_message(self, connector):
        await connector.configure({"webhook_url": "https://example.com/hook"})
        await connector.connect()
        connector.include_hmmm_chunk = False
        assert await connector.send_message("") == ""
        assert await connector.send_message("   ") == ""
        await connector.close()

    @pytest.mark.asyncio
    async def test_send_message_streaming(self, connector):
        await connector.configure(
            {
                "webhook_url": "https://example.com/hook",
                "stream": True,
            }
        )
        connector.include_hmmm_chunk = False
        await connector.connect()

        line1 = json.dumps(
            {"type": "item", "content": "Hel", "metadata": {"nodeName": "AI"}}
        )
        line2 = json.dumps(
            {"type": "item", "content": "lo", "metadata": {"nodeName": "AI"}}
        )

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}

        async def aiter_lines():
            yield line1
            yield line2

        mock_resp.aiter_lines = aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        stream_cm.__aexit__ = AsyncMock(return_value=None)

        connector._client.stream = MagicMock(return_value=stream_cm)
        connector.event_emitter.emit_event = AsyncMock()

        result = await connector.send_message("Test message")

        assert result == "Hello"
        calls = connector.event_emitter.emit_event.call_args_list
        types = [c[0][0] for c in calls]
        assert "processing_started" in types
        assert "processing_completed" in types
        assert types.count("message_chunk") == 2
        assert types[-1] == "message_completed"

        await connector.close()

    @pytest.mark.asyncio
    async def test_thinking_sound_loop_stops_on_first_stream_chunk(self, connector):
        await connector.configure(
            {
                "webhook_url": "https://example.com/hook",
                "stream": True,
            }
        )
        connector.include_hmmm_chunk = False
        connector.thinking_delay_seconds = 0.05

        # Make thinking chunk deterministic (we only assert the emitted values).
        connector.get_thinking_sound_base64 = MagicMock(
            side_effect=lambda idx=None: f"data:audio/wav;base64,thinking{idx if idx is not None else 0}"
        )

        line1 = json.dumps(
            {"type": "item", "content": "Hel", "metadata": {"nodeName": "AI"}}
        )
        line2 = json.dumps(
            {"type": "item", "content": "lo", "metadata": {"nodeName": "AI"}}
        )

        server_first_chunk_event = asyncio.Event()

        async def aiter_lines():
            await server_first_chunk_event.wait()
            yield line1
            yield line2

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_resp.aiter_lines = aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        stream_cm.__aexit__ = AsyncMock(return_value=None)

        await connector.connect()

        connector._client.stream = MagicMock(return_value=stream_cm)
        connector.event_emitter.emit_event = AsyncMock()

        task = asyncio.create_task(connector.send_message("Test message"))

        # Wait until the first thinking sound chunk is emitted.
        thinking_seen = False
        for _ in range(200):
            calls = connector.event_emitter.emit_event.call_args_list
            for call in calls:
                event_type = call[0][0]
                payload = call[0][1]
                if (
                    event_type == "message_chunk"
                    and isinstance(payload, dict)
                    and str(payload.get("text", "")).startswith("data:audio/wav;base64,thinking")
                ):
                    thinking_seen = True
                    break
            if thinking_seen:
                break
            await asyncio.sleep(0.01)

        assert thinking_seen, "Expected at least one thinking sound chunk before the first server chunk"

        # Allow the first streamed server chunk to arrive.
        server_first_chunk_event.set()

        result = await task
        assert result == "Hello"

        calls = connector.event_emitter.emit_event.call_args_list

        first_server_chunk_index = None
        for i, call in enumerate(calls):
            event_type = call[0][0]
            payload = call[0][1]
            if event_type == "message_chunk" and isinstance(payload, dict) and payload.get("text") == "Hel":
                first_server_chunk_index = i
                break

        assert first_server_chunk_index is not None, "Did not find the first server chunk in emitted events"

        thinking_after = [
            call
            for i, call in enumerate(calls)
            if i > first_server_chunk_index
            and call[0][0] == "message_chunk"
            and isinstance(call[0][1], dict)
            and str(call[0][1].get("text", "")).startswith("data:audio/wav;base64,thinking")
        ]

        assert thinking_after == [], "Thinking loop should stop after the first server chunk"

        await connector.close()

    @pytest.mark.asyncio
    async def test_send_message_buffered_ndjson(self, connector):
        await connector.configure(
            {
                "webhook_url": "https://example.com/hook",
                "stream": False,
            }
        )
        connector.include_hmmm_chunk = False
        await connector.connect()

        body = "\n".join(
            [
                json.dumps({"type": "begin"}),
                json.dumps({"type": "item", "content": "OK", "metadata": {}}),
            ]
        )
        mock_post_resp = MagicMock()
        mock_post_resp.raise_for_status = MagicMock()
        mock_post_resp.text = body

        connector._client.post = AsyncMock(return_value=mock_post_resp)
        connector.event_emitter.emit_event = AsyncMock()

        result = await connector.send_message("x")
        assert result == "OK"
        await connector.close()

    @pytest.mark.asyncio
    async def test_send_message_api_error(self, connector):
        await connector.configure({"webhook_url": "https://example.com/hook"})
        connector.include_hmmm_chunk = False
        await connector.connect()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("boom")

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        stream_cm.__aexit__ = AsyncMock(return_value=None)
        connector._client.stream = MagicMock(return_value=stream_cm)

        with pytest.raises(ConnectionError, match="Failed to send message to n8n"):
            await connector.send_message("x")

        await connector.close()

    def test_event_listener_management(self, connector):
        mock_listener = MagicMock()
        connector.event_emitter.add_event_listener = MagicMock()
        connector.event_emitter.remove_event_listener = MagicMock()
        connector.event_emitter.clear_event_listeners = MagicMock()

        connector.add_event_listener("test_event", mock_listener)
        connector.event_emitter.add_event_listener.assert_called_once_with(
            "test_event", mock_listener
        )

        connector.remove_event_listener("test_event", mock_listener)
        connector.event_emitter.remove_event_listener.assert_called_once_with(
            "test_event", mock_listener
        )

        connector.clear_event_listeners("test_event")
        connector.event_emitter.clear_event_listeners.assert_called_once_with(
            "test_event"
        )

    def test_session_id_sticks_within_threshold(self, connector):
        connector.session_switch_threshold_seconds = 30.0
        with patch("yova_api_n8n.n8n_connector.time.monotonic", side_effect=[100.0, 120.0]):
            first = connector._resolve_session_id("john")
            second = connector._resolve_session_id("kate")

        assert first == "john"
        assert second == "john"

    def test_session_id_switches_after_threshold_and_uses_anonymous(self, connector):
        connector.session_switch_threshold_seconds = 30.0
        with patch("yova_api_n8n.n8n_connector.time.monotonic", side_effect=[100.0, 131.0, 165.0]):
            first = connector._resolve_session_id("john")
            second = connector._resolve_session_id("kate")
            third = connector._resolve_session_id(None)

        assert first == "john"
        assert second == "kate"
        assert third == "anonymous"

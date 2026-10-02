import json

import pytest

from yova_api_n8n.webhook_stream import collect_text_from_ndjson_body, parse_n8n_stream_line


@pytest.mark.parametrize(
    "line,expected",
    [
        ("", None),
        ("not json", None),
        (json.dumps({"type": "begin"}), None),
        (json.dumps({"type": "end"}), None),
        (
            json.dumps(
                {
                    "type": "item",
                    "content": "hello",
                    "metadata": {"nodeName": "Respond to Webhook"},
                }
            ),
            None,
        ),
        (
            json.dumps({"type": "item", "content": "x", "metadata": {"nodeName": "AI Agent"}}),
            "x",
        ),
    ],
)
def test_parse_n8n_stream_line(line, expected):
    assert parse_n8n_stream_line(line) == expected


def test_collect_text_from_ndjson_body():
    lines = [
        json.dumps({"type": "begin"}),
        json.dumps({"type": "item", "content": "a", "metadata": {}}),
        json.dumps(
            {
                "type": "item",
                "content": "skip",
                "metadata": {"nodeName": "Respond to Webhook"},
            }
        ),
        json.dumps({"type": "item", "content": "b", "metadata": {}}),
    ]
    body = "\n".join(lines)
    assert collect_text_from_ndjson_body(body) == "ab"

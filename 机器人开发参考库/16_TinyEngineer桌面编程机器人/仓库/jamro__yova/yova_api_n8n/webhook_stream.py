"""Parse n8n webhook streaming NDJSON lines (Respond to Webhook + AI Agent)."""

import json
from typing import Optional


def parse_n8n_stream_line(line: str) -> Optional[str]:
    """
    Return assistant ``content`` from one n8n NDJSON line, or None if the line
    should be ignored (non-item, empty content, Respond to Webhook echo, etc.).
    """
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    if obj.get("type") != "item":
        return None
    md = obj.get("metadata") or {}
    if md.get("nodeName") == "Respond to Webhook":
        return None
    content = obj.get("content")
    if content is None or content == "":
        return None
    return str(content)


def collect_text_from_ndjson_body(text: str) -> str:
    """Join all parseable ``content`` fragments from a full response body."""
    parts = []
    for raw in text.splitlines():
        piece = parse_n8n_stream_line(raw)
        if piece is not None:
            parts.append(piece)
    return "".join(parts)

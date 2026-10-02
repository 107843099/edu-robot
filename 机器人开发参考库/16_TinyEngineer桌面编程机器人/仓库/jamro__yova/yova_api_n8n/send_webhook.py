#!/usr/bin/env python3
"""
Send a JSON POST to an n8n Webhook trigger and print the HTTP response.

Configuration (first match wins for URL): ``--url``, then environment variable
``N8N_WEBHOOK_URL``, then ``n8n.webhook_url`` in ``yova.config.json`` (same file
as the main YOVA app; see [config.md](../docs/config.md)).

Auth: environment variables ``N8N_AUTH_HEADER_NAME`` / ``N8N_AUTH_HEADER_VALUE``
override ``n8n.auth_header_name`` / ``n8n.auth_header_value`` from
``yova.config.json`` when the env vars are **set** (even if empty). Otherwise
values come from the config file.

Streaming, timeout, User-Agent, ``extra_payload``, and custom body field names
(``chat_input_key``, ``session_id_key``) are read from the ``n8n`` object when
present; ``--no-stream`` still forces non-streaming.

Required n8n configuration
------------------------------
- **HTTP method:** The Webhook node must accept **POST** only (or include POST if
  multiple methods are enabled). This script always sends **POST** with a JSON body.

- **Body:** `Content-Type: application/json`. The default payload includes
  ``chatInput`` (user message) and ``sessionId`` (UUID per run). Match these keys
  in your workflow or change ``--message`` / field names via code.

- **Webhook → AI Agent / memory:** n8n puts the request JSON under ``$json.body``,
  while Chat Trigger and Simple Memory expect ``sessionId`` and ``chatInput`` on
  the **root** of the item. Either add an **Edit Fields (Set)** node after the
  Webhook that copies ``body.sessionId`` and ``body.chatInput`` to top-level
  fields, or configure **Simple Memory → Session ID → Define below** with an
  expression such as ``{{ $json.sessionId || $json.body.sessionId }}`` and align
  the agent prompt with ``$json.body`` if needed.

- **Respond:** If the workflow ends with **Respond to Webhook**, set the Webhook
  **Respond** option to **Using 'Respond to Webhook' Node** (not *When Last Node
  Finishes*), or n8n will error about an unused Respond node.

- **Streaming:** Webhook **Respond → Streaming response**, streaming on **Respond
  to Webhook** and **AI Agent**. n8n sends newline-delimited JSON; this script
  prints only the **content** field from **item** events (typically the AI Agent
  tokens), and skips **begin** / **end** and the duplicate **Respond to Webhook**
  payload. If everything still appears at once,
  the bottleneck is usually **reverse proxies** (Cloudflare, nginx) buffering the
  full body until n8n finishes—try ``python3 -u`` for unbuffered Python I/O, and
  on your host consider disabling response buffering (e.g. nginx
  ``proxy_buffering off``, or Cloudflare/cache rules that still buffer streamed
  origins).

- **Production URL:** Call the workflow’s production webhook URL while the
  workflow is **Active**.

- **Header auth (n8n “Header Auth” credential):** In n8n, **Credentials → Header
  Auth** has two fields: **Name** = HTTP header name, **Value** = full header
  value. The Webhook node (**Authentication → Header Auth**) must use that
  credential. This script must send **exactly** that name and value (same string
  as in **Value**, including any ``Bearer `` prefix if you stored it there).
  A **403** body ``Authorization data is wrong!`` means the name or value did
  not match; ``WWW-Authenticate: Basic`` can still appear and does **not** mean
  the Webhook is using Basic auth. **Do not** confuse with **Bearer Auth** on
  the Webhook—that mode expects ``Authorization: Bearer <token>`` and is a
  separate authentication type.

Some reverse proxies (e.g. Cloudflare) block Python’s default User-Agent; this
script sets a browser-like User-Agent so the request can reach the instance.

**Timing (stderr):** in streaming mode, logs (1) when the POST is sent, (2) when
HTTP **response headers** are received, (3) first **raw body** chunk, (4) first
**non-empty** AI ``content``.

**Reading the numbers:** If (2) is small but (3) is large, the TCP connection is
open but **nothing is written to the body** until then — usually **n8n waiting
for the model’s first streamed chunk** (TTFT), not Cloudflare/nginx buffering.
If (3) and (4) match, the first read already contained text; **tokens that feel
“instant” after** are often the model (and n8n) emitting the rest in a tight
burst — not a second buffering stage.

**``Accept-Encoding: identity``** avoids gzip on the wire; gzip + some stacks can
delay or batch decoded output for streaming responses.
"""

import argparse
import codecs
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from yova_api_n8n.webhook_stream import parse_n8n_stream_line
from yova_shared import get_config


def _load_n8n_config() -> Dict[str, Any]:
    """Return the ``n8n`` object from ``yova.config.json``, or {} if missing or unreadable."""
    try:
        cfg = get_config()
        if not isinstance(cfg, dict):
            return {}
        n8n = cfg.get("n8n")
        return dict(n8n) if isinstance(n8n, dict) else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _emit_n8n_stream_line(line: str, timing: Optional[Dict[str, Any]] = None) -> None:
    content = parse_n8n_stream_line(line)
    if content is None:
        return
    if timing is not None and timing.get("first_token_mono") is None:
        timing["first_token_mono"] = time.perf_counter()
        delta_ms = (timing["first_token_mono"] - timing["t_send_mono"]) * 1000
        print(f"[send_webhook] first token +{delta_ms:.0f}ms after send", file=sys.stderr)
    sys.stdout.write(content)
    sys.stdout.flush()


def _print_buffered_body(text: str, timing: Optional[Dict[str, Any]] = None) -> None:
    for raw in text.splitlines():
        _emit_n8n_stream_line(raw, timing=timing)
    print(flush=True)


def _stream_response_body(
    resp: urllib.response.addinfourl,
    encoding: str,
    timing: Optional[Dict[str, Any]] = None,
) -> None:
    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    line_buf = ""
    while True:
        chunk = resp.read(2048)
        if not chunk:
            text = decoder.decode(b"", final=True)
            if text:
                line_buf += text
            if line_buf.strip():
                _emit_n8n_stream_line(line_buf, timing=timing)
            print(flush=True)
            break
        if timing is not None and timing.get("first_body_mono") is None:
            timing["first_body_mono"] = time.perf_counter()
            dt_send = (timing["first_body_mono"] - timing["t_send_mono"]) * 1000
            dt_hdr = (timing["first_body_mono"] - timing["t_headers_mono"]) * 1000
            print(
                f"[send_webhook] first body bytes +{dt_send:.0f}ms after send "
                f"(+{dt_hdr:.0f}ms after headers)",
                file=sys.stderr,
            )
        text = decoder.decode(chunk)
        if not text:
            continue
        line_buf += text
        while True:
            nl = line_buf.find("\n")
            if nl == -1:
                break
            _emit_n8n_stream_line(line_buf[:nl], timing=timing)
            line_buf = line_buf[nl + 1 :]


def main() -> int:
    parser = argparse.ArgumentParser(description="POST JSON to an n8n webhook.")
    parser.add_argument(
        "--url",
        default=None,
        help="Webhook URL (overrides N8N_WEBHOOK_URL and yova.config.json n8n.webhook_url)",
    )
    parser.add_argument(
        "--message",
        "-m",
        default="hello",
        help="Value for chatInput (or n8n.chat_input_key) in the JSON body",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Read the full response then print once (no incremental chunks)",
    )
    args = parser.parse_args()
    n8n_cfg = _load_n8n_config()

    url = (args.url or "").strip() if args.url else ""
    if not url:
        url = os.environ.get("N8N_WEBHOOK_URL", "").strip()
    if not url:
        url = (n8n_cfg.get("webhook_url") or "").strip()
    if not url:
        print(
            "Error: webhook URL required (--url, N8N_WEBHOOK_URL, or n8n.webhook_url in yova.config.json)",
            file=sys.stderr,
        )
        return 2

    if "N8N_AUTH_HEADER_NAME" in os.environ:
        auth_name = os.environ["N8N_AUTH_HEADER_NAME"].strip() or None
    else:
        auth_name = (n8n_cfg.get("auth_header_name") or "").strip() or None

    if "N8N_AUTH_HEADER_VALUE" in os.environ:
        raw_av = os.environ["N8N_AUTH_HEADER_VALUE"]
        auth_value = raw_av.strip() if raw_av else None
    else:
        raw_cv = n8n_cfg.get("auth_header_value")
        if raw_cv is None:
            auth_value = None
        else:
            auth_value = str(raw_cv).strip() or None

    stream = not args.no_stream and bool(n8n_cfg.get("stream", True))
    timeout = float(n8n_cfg.get("timeout_seconds", 120))
    user_agent = str(n8n_cfg.get("user_agent") or USER_AGENT)
    chat_key = str(n8n_cfg.get("chat_input_key", "chatInput"))
    session_key = str(n8n_cfg.get("session_id_key", "sessionId"))
    extra = n8n_cfg.get("extra_payload")
    extra = dict(extra) if isinstance(extra, dict) else {}

    if stream and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except (OSError, ValueError):
            pass
    payload = {
        **extra,
        chat_key: args.message,
        session_key: str(uuid.uuid4()),
    }
    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
        "User-Agent": user_agent,
        "X-Accel-Buffering": "no",
    }
    if auth_name and auth_value is not None:
        headers[auth_name] = auth_value

    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    t_send_mono = time.perf_counter()
    print(
        f"[send_webhook] request sent {datetime.now(timezone.utc).isoformat()}",
        file=sys.stderr,
    )
    stream_timing: Optional[Dict[str, Any]] = None
    if stream:
        stream_timing = {
            "t_send_mono": t_send_mono,
            "t_headers_mono": None,
            "first_body_mono": None,
            "first_token_mono": None,
        }
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if stream_timing is not None:
                stream_timing["t_headers_mono"] = time.perf_counter()
                dt_hdr = (stream_timing["t_headers_mono"] - t_send_mono) * 1000
                print(
                    f"[send_webhook] response headers +{dt_hdr:.0f}ms after send",
                    file=sys.stderr,
                )
            charset = resp.headers.get_content_charset() or "utf-8"
            if stream_timing is not None:
                enc = resp.headers.get("Content-Encoding", "").strip()
                if enc and enc.lower() != "identity":
                    print(
                        f"[send_webhook] note: Content-Encoding={enc!r} "
                        "(identity was requested; if streaming looks batched, check proxy)",
                        file=sys.stderr,
                    )
            if stream:
                _stream_response_body(resp, charset, timing=stream_timing)
            else:
                raw = resp.read()
                _print_buffered_body(raw.decode(charset, errors="replace"), timing=None)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace").strip()
        msg = f"{e.code} {e.reason}"
        if err_body:
            msg = f"{msg}\n{err_body}"
        print(msg, file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(e.reason, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

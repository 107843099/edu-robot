"""MindPaw AI Gateway.

The ESP8266 talks to this service through the OpenAI-compatible
``/v1/chat/completions`` endpoint. Secrets stay at the gateway instead of
being embedded in the robot firmware.
"""

import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


APP_VERSION = "0.1.0"
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "12"))
MAX_CONTENT_CHARS = int(os.getenv("MAX_CONTENT_CHARS", "6000"))
UPSTREAM_TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "18"))
GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN", "")
PROVIDER = os.getenv("AI_PROVIDER", "ark").lower()
UPSTREAM_URL = os.getenv(
    "UPSTREAM_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
)
UPSTREAM_API_KEY = os.getenv("ARK_API_KEY", os.getenv("UPSTREAM_API_KEY", ""))
UPSTREAM_MODEL = os.getenv("ARK_ENDPOINT_ID", os.getenv("UPSTREAM_MODEL", ""))

app = FastAPI(title="MindPaw AI Gateway", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(min_length=1, max_length=MAX_MESSAGES)
    model: str = Field(default="mindpaw", max_length=128)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=256, ge=1, le=1024)
    response_format: Optional[Dict[str, Any]] = None

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for message in messages:
            if message.get("role") not in {"system", "user", "assistant"}:
                raise ValueError("unsupported message role")
            content = message.get("content", "")
            if not isinstance(content, str) or len(content) > MAX_CONTENT_CHARS:
                raise ValueError("message content is too large")
        return messages


def authorize(authorization: Optional[str] = Header(default=None)) -> None:
    """Require a gateway token when one is configured."""
    if not GATEWAY_TOKEN:
        return
    expected = f"Bearer {GATEWAY_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid gateway token")


def _effective_model(requested: str) -> str:
    # Endpoint IDs are deployment configuration, not client-controlled secrets.
    if PROVIDER == "ark" and UPSTREAM_MODEL:
        return UPSTREAM_MODEL
    return requested


def _extract_json_content(content: Any) -> Dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("upstream content is not text")
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("upstream content is not an object")

    # Keep the device contract bounded even if a provider ignores the prompt.
    reply = str(parsed.get("reply_text", "嗯？"))[:200]
    def bounded_int(name: str, default: int, low: int, high: int) -> int:
        try:
            value = int(parsed.get(name, default))
        except (TypeError, ValueError):
            value = default
        return max(low, min(high, value))

    return {
        "reply_text": reply,
        "action": bounded_int("action", -1, -1, 18),
        "expression": bounded_int("expression", -1, -1, 9),
        "melody": bounded_int("melody", -1, -1, 9),
        "repeat": bounded_int("repeat", 0, 0, 4),
        "emotion": bounded_int("emotion", 0, 0, 5),
    }


def _mock_response(request: ChatRequest) -> Dict[str, Any]:
    latest = next(
        (m.get("content", "") for m in reversed(request.messages) if m.get("role") == "user"),
        "你好",
    )
    reply = "你好！我是 MindPaw" if "你好" in latest else "汪！我收到啦"
    content = json.dumps(
        {"reply_text": reply, "action": 12, "expression": 0, "melody": 3, "repeat": 1, "emotion": 1},
        ensure_ascii=False,
    )
    return _openai_response(content, request.model, "mock")


def _openai_response(content: str, model: str, response_id: str) -> Dict[str, Any]:
    return {
        "id": f"mindpaw-{response_id}-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
    }


@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    return {"status": "ok", "version": APP_VERSION, "provider": PROVIDER}


@app.post("/v1/chat/completions", dependencies=[Depends(authorize)])
async def chat_completions(request: ChatRequest) -> Dict[str, Any]:
    if PROVIDER == "mock":
        return _mock_response(request)
    if not UPSTREAM_API_KEY:
        raise HTTPException(status_code=503, detail="upstream API key is not configured")

    payload = request.model_dump(exclude_none=True)
    payload["model"] = _effective_model(request.model)
    headers = {"Authorization": f"Bearer {UPSTREAM_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
            response = await client.post(UPSTREAM_URL, json=payload, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=504, detail="upstream request failed") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"upstream returned {response.status_code}")

    try:
        upstream = response.json()
        content = upstream["choices"][0]["message"]["content"]
        normalized = _extract_json_content(content)
    except (ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="upstream response failed MindPaw schema validation") from exc
    return _openai_response(json.dumps(normalized, ensure_ascii=False), payload["model"], "upstream")

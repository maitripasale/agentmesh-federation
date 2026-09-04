import os
import re
import uuid

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://metrics-agent:8002")

app = FastAPI(title="Metrics A2A Agent", version="0.1.0")


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict = {}


AGENT_CARD = {
    "name": "Metrics Agent",
    "description": "Inspects service latency, errors, CPU, and memory.",
    "version": "0.1.0",
    "url": f"{PUBLIC_URL}/a2a",
    "protocolVersion": "0.3.0",
    "capabilities": {"streaming": False},
    "skills": [
        {
            "id": "metrics-query",
            "name": "Service metrics",
            "description": "Inspect latency, error rate, CPU and memory.",
            "tags": ["prometheus", "metrics", "sre"],
            "examples": ["Show metrics for checkout-api"],
        }
    ],
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json", "text/plain"],
}


@app.on_event("startup")
async def register() -> None:
    payload = {
        "id": "metrics",
        "name": AGENT_CARD["name"],
        "description": AGENT_CARD["description"],
        "capabilities": ["metrics-query", "service-health"],
        "tags": ["prometheus", "metrics", "sre"],
        "agent_card_url": f"{PUBLIC_URL}/.well-known/agent-card.json",
        "health_url": f"{PUBLIC_URL}/health",
        "version": "0.1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            await client.post(f"{REGISTRY_URL}/agents", json=payload)
    except Exception:
        pass


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return AGENT_CARD


@app.post("/a2a")
def a2a_message(request: JsonRpcRequest) -> dict:
    message = request.params.get("message", request.params)
    text = ""
    if isinstance(message, dict):
        for part in message.get("parts", []):
            if isinstance(part, dict):
                text += part.get("text", "")

    service = "checkout-api" if "checkout-api" in text else "unknown-service"
    metrics = {
        "service": service,
        "p95_latency_ms": 842 if service == "checkout-api" else 120,
        "error_rate_pct": 18.4 if service == "checkout-api" else 0.3,
        "cpu_pct": 43,
        "memory_pct": 61,
    }

    return {
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "kind": "message",
            "messageId": str(uuid.uuid4()),
            "role": "agent",
            "parts": [{"kind": "data", "data": metrics}],
        },
    }

import os
import re
import uuid

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from agents.kubernetes.diagnostics import diagnose_service, recent_events

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://kubernetes-agent:8001")

app = FastAPI(title="Kubernetes Diagnostics A2A Agent", version="0.1.0")


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict = {}


AGENT_CARD = {
    "name": "Kubernetes Diagnostics Agent",
    "description": "Diagnoses workload failures and deployment issues.",
    "version": "0.1.0",
    "url": f"{PUBLIC_URL}/a2a",
    "protocolVersion": "0.3.0",
    "capabilities": {"streaming": False},
    "skills": [
        {
            "id": "kubernetes-diagnostics",
            "name": "Kubernetes diagnostics",
            "description": "Inspect workload health and recent cluster events.",
            "tags": ["kubernetes", "cloud", "incidents"],
            "examples": ["Why is checkout-api failing after deployment?"],
        }
    ],
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json", "text/plain"],
}


def extract_service(text: str) -> str:
    quoted = re.findall(r"[`'\"]([a-zA-Z0-9_-]+)[`'\"]", text)
    if quoted:
        return quoted[0]
    for known in ("checkout-api", "worker"):
        if known in text:
            return known
    return "checkout-api"


@app.on_event("startup")
async def register() -> None:
    payload = {
        "id": "kubernetes-diagnostics",
        "name": AGENT_CARD["name"],
        "description": AGENT_CARD["description"],
        "capabilities": ["kubernetes-diagnostics", "deployment-debugging"],
        "tags": ["kubernetes", "cloud", "incidents"],
        "agent_card_url": f"{PUBLIC_URL}/.well-known/agent-card.json",
        "health_url": f"{PUBLIC_URL}/health",
        "version": "0.1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            await client.post(f"{REGISTRY_URL}/agents", json=payload)
    except Exception:
        # Registry may still be starting. The coordinator can retry registration
        # by restarting this service.
        pass


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return AGENT_CARD


@app.post("/a2a")
def a2a_message(request: JsonRpcRequest) -> dict:
    if request.method not in {"message/send", "tasks/send"}:
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32601, "message": "Method not found"},
        }

    message = request.params.get("message", request.params)
    text = ""
    if isinstance(message, dict):
        for part in message.get("parts", []):
            if isinstance(part, dict):
                text += part.get("text", "")

    service = extract_service(text)
    result = {
        "diagnosis": diagnose_service(service),
        "events": recent_events(service),
    }

    return {
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "kind": "message",
            "messageId": str(uuid.uuid4()),
            "role": "agent",
            "parts": [{"kind": "data", "data": result}],
        },
    }

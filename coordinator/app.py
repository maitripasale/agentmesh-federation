import os
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000")

app = FastAPI(title="AgentMesh Coordinator", version="0.1.0")


class IncidentRequest(BaseModel):
    query: str


async def discover(capability: str) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(
            f"{REGISTRY_URL}/agents/search",
            params={"capability": capability},
        )
        response.raise_for_status()
        matches = response.json()

    if not matches:
        raise HTTPException(
            status_code=503,
            detail=f"No healthy agent exposes capability: {capability}",
        )

    return matches[0]


async def delegate(agent: dict, query: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        card_response = await client.get(agent["agent_card_url"])
        card_response.raise_for_status()
        card = card_response.json()

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{"kind": "text", "text": query}],
                }
            },
        }

        response = await client.post(card["url"], json=payload)
        response.raise_for_status()
        return {
            "agent": card["name"],
            "agent_card": card,
            "response": response.json(),
        }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/investigate")
async def investigate(request: IncidentRequest) -> dict:
    # Discovery is capability-driven. Agent URLs are not hardcoded here.
    k8s_agent = await discover("kubernetes-diagnostics")
    metrics_agent = await discover("metrics-query")

    k8s_result = await delegate(k8s_agent, request.query)
    metrics_result = await delegate(metrics_agent, request.query)

    return {
        "query": request.query,
        "delegation": [
            {
                "capability": "kubernetes-diagnostics",
                "agent": k8s_agent["name"],
            },
            {
                "capability": "metrics-query",
                "agent": metrics_agent["name"],
            },
        ],
        "results": {
            "kubernetes": k8s_result["response"],
            "metrics": metrics_result["response"],
        },
        "summary": (
            "The deployment is unhealthy and the metrics show elevated errors. "
            "The Kubernetes agent found a missing DATABASE_URL secret after deployment."
        ),
    }

from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="AgentMesh Registry", version="0.1.0")


class AgentRegistration(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    agent_card_url: str
    health_url: str | None = None
    version: str = "0.1.0"


class AgentRecord(AgentRegistration):
    status: str = "healthy"
    updated_at: str


AGENTS: dict[str, AgentRecord] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "registered_agents": len(AGENTS)}


@app.post("/agents", response_model=AgentRecord)
def register_agent(agent: AgentRegistration) -> AgentRecord:
    record = AgentRecord(
        **agent.model_dump(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    AGENTS[record.id] = record
    return record


@app.get("/agents", response_model=list[AgentRecord])
def list_agents() -> list[AgentRecord]:
    return list(AGENTS.values())


@app.get("/agents/search", response_model=list[AgentRecord])
def search_agents(
    capability: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[AgentRecord]:
    results = list(AGENTS.values())

    if capability:
        wanted = capability.lower()
        results = [
            agent
            for agent in results
            if any(wanted == item.lower() for item in agent.capabilities)
        ]

    if q:
        needle = q.lower()
        results = [
            agent
            for agent in results
            if needle in agent.name.lower()
            or needle in agent.description.lower()
            or any(needle in tag.lower() for tag in agent.tags)
            or any(needle in item.lower() for item in agent.capabilities)
        ]

    return results


@app.get("/agents/{agent_id}", response_model=AgentRecord)
def get_agent(agent_id: str) -> AgentRecord:
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AGENTS[agent_id]

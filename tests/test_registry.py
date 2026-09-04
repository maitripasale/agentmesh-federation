from fastapi.testclient import TestClient

from registry.app import app

client = TestClient(app)


def test_register_and_search_agent():
    payload = {
        "id": "test-agent",
        "name": "Test Agent",
        "description": "test",
        "capabilities": ["logs-search"],
        "tags": ["logs"],
        "agent_card_url": "http://example.test/.well-known/agent-card.json",
    }

    response = client.post("/agents", json=payload)
    assert response.status_code == 200

    response = client.get("/agents/search", params={"capability": "logs-search"})
    assert response.status_code == 200
    assert any(agent["id"] == "test-agent" for agent in response.json())

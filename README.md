# AgentMesh

AgentMesh is a federated agent discovery and delegation platform. Agents register capabilities in a searchable registry, publish A2A-style Agent Cards, receive delegated work over JSON-RPC, and expose domain tools through MCP.

## Why this project

Most multi-agent demos hardcode a set of agents inside one application. AgentMesh treats agents as independently deployed services.

The interesting engineering boundary is:

1. **Discovery**: find an agent by capability.
2. **Identity/metadata**: read its Agent Card.
3. **Agent-to-agent delegation**: send a task over an A2A-style JSON-RPC endpoint.
4. **Agent-to-tool access**: expose diagnostics through MCP.
5. **Failure isolation**: keep agent implementations loosely coupled from the coordinator.

## Architecture

```text
                       +--------------------+
                       |  Agent Registry    |
                       |  FastAPI           |
                       +---------+----------+
                                 |
                         capability search
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
        +--------------------+       +--------------------+
        | Kubernetes Agent   |       | Metrics Agent      |
        | Agent Card + A2A   |       | Agent Card + A2A   |
        +---------+----------+       +--------------------+
                  |
                  | same diagnostic functions
                  v
        +--------------------+
        | Kubernetes MCP     |
        | FastMCP tools      |
        +--------------------+

                       +--------------------+
User ---------------->| Coordinator        |
incident question      | discovery + A2A    |
                       +--------------------+
```

## Demo flow

Request:

```text
Why is checkout-api failing after the latest deployment?
```

The coordinator:

1. searches the registry for `kubernetes-diagnostics`;
2. searches for `metrics-query`;
3. fetches each discovered Agent Card;
4. delegates the same incident context to both agents;
5. combines their responses.

The Kubernetes agent identifies a simulated missing `DATABASE_URL` secret. The metrics agent reports elevated latency and error rate.

## Run

### Docker

```bash
docker compose up --build
```

Wait a few seconds for the agents to register, then:

```bash
curl -X POST http://localhost:8003/investigate \
  -H "Content-Type: application/json" \
  -d '{"query":"Why is checkout-api failing after the latest deployment?"}'
```

Inspect the registry:

```bash
curl http://localhost:8000/agents
```

Inspect Agent Cards:

```bash
curl http://localhost:8001/.well-known/agent-card.json
curl http://localhost:8002/.well-known/agent-card.json
```

## MCP server

The Kubernetes diagnostics are also exposed as MCP tools using the official Python MCP SDK and `FastMCP`.

Install dependencies, then run:

```bash
python -m mcp_servers.kubernetes.server
```

Available tools:

- `diagnose_kubernetes_service`
- `get_recent_kubernetes_events`

You can also run the server through MCP Inspector when the MCP CLI is installed.

## Tests

```bash
pytest -q
```

## What is intentionally simplified

The current A2A transport uses the same core ideas as A2A: Agent Cards, capability discovery, and JSON-RPC task/message delegation. A production version should replace the small transport layer with the official `a2a-sdk`, validate cards with the A2A Inspector/TCK, add authentication, durable task state, retries, health-aware routing, and protocol-version negotiation.

The registry is in-memory for quick local execution. A production version would use PostgreSQL and signed registrations.

## Next milestones

- Replace the minimal A2A transport with the official `a2a-sdk`
- Add PostgreSQL-backed registry persistence
- Add health-aware routing and agent failover
- Add a logs agent with an MCP-backed search tool
- Add Prometheus metrics and a Grafana dashboard
- Add signed capability documents and authentication
- Add integration tests for timeouts, duplicate messages, and failed agents

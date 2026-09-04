# Architecture Notes

## Design principle

The coordinator should depend on **capabilities**, not agent identities or URLs.

Bad:

```python
K8S_AGENT_URL = "http://k8s-agent:8001"
```

Better:

```text
need: kubernetes-diagnostics
        |
        v
registry search
        |
        v
agent card
        |
        v
delegate task
```

This makes it possible to add multiple implementations of a capability later.

## Protocol boundaries

### A2A-style boundary

Used between the coordinator and independently deployed agents.

```text
Coordinator -> Agent Card -> Agent JSON-RPC endpoint
```

### MCP boundary

Used to expose domain tools such as Kubernetes diagnostics.

```text
Agent or MCP Client -> MCP Server -> Domain Tool
```

A2A is for collaboration between agentic applications. MCP is for exposing tools and resources to an agent or model-facing application.

## Failure model for next iteration

The next version should record:

- agent heartbeat;
- recent success rate;
- p95 response latency;
- timeout count;
- consecutive failures.

Selection can then prefer healthy agents and fail over to another agent advertising the same capability.

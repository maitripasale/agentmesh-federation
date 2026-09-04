from mcp.server.fastmcp import FastMCP

from agents.kubernetes.diagnostics import diagnose_service, recent_events

mcp = FastMCP("AgentMesh Kubernetes Tools")


@mcp.tool()
def diagnose_kubernetes_service(service: str) -> dict:
    """Inspect the health of a Kubernetes workload in the demo cluster."""
    return diagnose_service(service)


@mcp.tool()
def get_recent_kubernetes_events(service: str) -> list[dict]:
    """Return recent Kubernetes events for a service in the demo cluster."""
    return recent_events(service)


if __name__ == "__main__":
    mcp.run()

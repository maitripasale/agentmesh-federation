from dataclasses import dataclass


@dataclass
class Pod:
    name: str
    status: str
    restarts: int
    reason: str = ""


SAMPLE_PODS = {
    "checkout-api": Pod(
        name="checkout-api-7c9d8",
        status="CrashLoopBackOff",
        restarts=9,
        reason="Missing DATABASE_URL secret after deployment",
    ),
    "worker": Pod(
        name="worker-5fdd4",
        status="Running",
        restarts=0,
    ),
}


def diagnose_service(service: str) -> dict:
    pod = SAMPLE_PODS.get(service)
    if not pod:
        return {
            "service": service,
            "status": "unknown",
            "summary": "No matching workload found in the demo cluster.",
        }

    return {
        "service": service,
        "pod": pod.name,
        "status": pod.status,
        "restarts": pod.restarts,
        "reason": pod.reason,
        "summary": (
            f"{service} is {pod.status}. {pod.reason}"
            if pod.reason
            else f"{service} is healthy."
        ),
    }


def recent_events(service: str) -> list[dict]:
    if service == "checkout-api":
        return [
            {
                "type": "Warning",
                "reason": "BackOff",
                "message": "Back-off restarting failed container",
            },
            {
                "type": "Warning",
                "reason": "Failed",
                "message": "Secret DATABASE_URL not found",
            },
        ]

    return [
        {
            "type": "Normal",
            "reason": "Healthy",
            "message": f"No recent warnings for {service}",
        }
    ]

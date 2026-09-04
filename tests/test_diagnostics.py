from agents.kubernetes.diagnostics import diagnose_service, recent_events


def test_checkout_diagnosis():
    result = diagnose_service("checkout-api")
    assert result["status"] == "CrashLoopBackOff"
    assert "DATABASE_URL" in result["reason"]


def test_recent_events():
    events = recent_events("checkout-api")
    assert any(item["reason"] == "Failed" for item in events)

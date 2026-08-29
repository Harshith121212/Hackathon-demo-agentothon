import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_get_fleet_and_risks_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test /api/fleet
        res_fleet = await client.get("/api/fleet")
        assert res_fleet.status_code == 200
        fleet_data = res_fleet.json()
        assert "vessels" in fleet_data
        assert fleet_data["count"] >= 50

        # Test /api/risks
        res_risks = await client.get("/api/risks")
        assert res_risks.status_code == 200
        risks_data = res_risks.json()
        assert "assessments" in risks_data
        assert "stats" in risks_data


@pytest.mark.asyncio
async def test_scenario_trigger_and_action_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger Typhoon Malakas Scenario
        res_scen = await client.post("/api/scenarios/trigger/typhoon_malakas")
        assert res_scen.status_code == 200
        scen_data = res_scen.json()
        assert scen_data["stats"]["critical_count"] >= 1

        # 2. Query Investigation for Ocean Star
        res_inv = await client.get("/api/investigate/VSL-OS-104")
        assert res_inv.status_code == 200
        inv_data = res_inv.json()
        assert "brief" in inv_data
        assert "actions" in inv_data
        assert len(inv_data["actions"]) >= 1

        action = inv_data["actions"][0]
        action_id = action["action_id"]
        assert action["status"] == "PENDING_APPROVAL"

        # 3. Test Human Operator Approval
        res_appr = await client.post(f"/api/actions/{action_id}/approve", json={"operator_name": "Senior Fleet Controller"})
        assert res_appr.status_code == 200
        appr_data = res_appr.json()
        assert appr_data["action"]["status"] == "APPROVED"
        assert appr_data["action"]["approved_by"] == "Senior Fleet Controller"

        # 4. Check Audit Log
        res_audit = await client.get("/api/actions/audit-log")
        assert res_audit.status_code == 200
        audit_data = res_audit.json()
        assert any(item["action_id"] == action_id for item in audit_data["audit_log"])

        # 5. Reset to baseline
        res_reset = await client.post("/api/scenarios/trigger/reset")
        assert res_reset.status_code == 200

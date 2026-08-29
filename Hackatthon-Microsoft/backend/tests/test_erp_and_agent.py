import pytest
from datetime import datetime, timezone, timedelta
from backend.app.core.models import RiskAssessment, RiskTier, WeatherExposure, IncidentType, ActionStatus
from backend.app.erp.database import MaritimeERPDatabase
from backend.app.adapters.simulated_data import generate_initial_dataset
from backend.app.agent.tools import AgentToolSuite
from backend.app.agent.investigation_agent import AIInvestigationAgent


@pytest.mark.asyncio
async def test_agent_investigation_and_action_generation():
    now = datetime.now(timezone.utc)
    erp_db = MaritimeERPDatabase()
    vessels_list, voyages_dict, incidents = generate_initial_dataset()
    vessels_dict = {v.vessel_id: v for v in vessels_list}
    
    # Mock exposure
    exposure = WeatherExposure(
        exposure_id="EXP-TEST-01",
        vessel_id="VSL-OS-104",
        voyage_id="OS-104",
        incident_type=IncidentType.SEVERE_WEATHER,
        start_time=now + timedelta(hours=6),
        end_time=now + timedelta(hours=14),
        duration_hours=8.0,
        peak_lat=6.5,
        peak_lon=94.5,
        max_wind_knots=62.0,
        max_wave_m=9.2,
        min_distance_nm=12.0,
        peak_severity_score=92.0,
        confidence_pct=78.0,
        description="Typhoon Malakas with 9.2m waves and 62kts winds.",
    )
    exposures_dict = {"VSL-OS-104": exposure}

    assessment = RiskAssessment(
        assessment_id="RSK-TEST-01",
        vessel_id="VSL-OS-104",
        voyage_id="OS-104",
        vessel_name="Ocean Star",
        risk_tier=RiskTier.CRITICAL,
        risk_score=88.0,
        primary_factors=["Typhoon Malakas intercept", "Customer SLA breach risk"],
        exposure=exposure,
        incident=None,
        requires_ai_investigation=True,
        assessed_at=now,
        projected_delay_hours=36.0,
    )

    tool_suite = AgentToolSuite(
        erp_db=erp_db,
        vessels_dict=vessels_dict,
        voyages_dict=voyages_dict,
        exposures_dict=exposures_dict,
        incidents_dict={inc.incident_id: inc for inc in incidents},
    )

    agent = AIInvestigationAgent(tool_suite)
    brief, draft_actions = await agent.investigate_voyage(assessment)

    # Validate Management Risk Brief
    assert brief.vessel_id == "VSL-OS-104"
    assert brief.risk_level == RiskTier.CRITICAL
    assert "Acme Logistics" in brief.why_explanation or any("Acme" in imp.details for imp in brief.operational_impacts)
    assert len(brief.operational_impacts) >= 3  # Customer SLA, Crew rotation, Drydock/Berth
    assert brief.total_estimated_financial_exposure_usd > 50000
    assert brief.confidence_score_pct >= 75.0
    assert len(brief.reasoning_trace) >= 6

    # Validate Draft Actions
    assert len(draft_actions) >= 1
    cust_draft = next(a for a in draft_actions if "Charterer" in a.recipient_type or "Customer" in a.recipient_type)
    assert cust_draft.status == ActionStatus.PENDING_APPROVAL
    assert "Acme Logistics" in cust_draft.draft_content or "Ocean Star" in cust_draft.draft_content
    assert cust_draft.recipient_email == "operations.desk@acmelogistics.com"

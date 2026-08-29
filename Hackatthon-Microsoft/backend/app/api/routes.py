from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Body
from pydantic import BaseModel

from backend.app.events.dispatcher import FleetEventDispatcher
from backend.app.core.models import ActionStatus

router = APIRouter()
dispatcher = FleetEventDispatcher()


class ActionEditPayload(BaseModel):
    edited_content: str
    operator_name: Optional[str] = "Chief Fleet Controller"


class ActionRejectPayload(BaseModel):
    reason: Optional[str] = "Dismissed by operator"
    operator_name: Optional[str] = "Chief Fleet Controller"


class ActionApprovePayload(BaseModel):
    operator_name: Optional[str] = "Chief Fleet Controller"
    notes: Optional[str] = None


@router.get("/fleet")
async def get_fleet() -> Dict[str, Any]:
    """Returns all fleet vessels with current telemetry, voyage mapping, and risk tier."""
    vessels_out = []
    for v in dispatcher.vessels.values():
        assessment = dispatcher.assessments.get(v.vessel_id)
        voy_id = v.vessel_id.replace("VSL-", "")
        voy = dispatcher.voyages.get(voy_id) or dispatcher.voyages.get(f"VY-{v.vessel_id[-3:]}")
        vessels_out.append({
            "vessel_id": v.vessel_id,
            "imo": v.imo,
            "name": v.name,
            "type": v.type.value,
            "flag": v.flag,
            "lat": v.lat,
            "lon": v.lon,
            "speed_knots": v.speed_knots,
            "heading_deg": v.heading_deg,
            "destination": v.destination,
            "eta": v.eta.isoformat(),
            "draft_m": v.draft_m,
            "length_m": v.length_m,
            "voyage_id": voy.voyage_id if voy else None,
            "departure_port": voy.departure_port if voy else None,
            "risk_tier": assessment.risk_tier.value if assessment else "NORMAL",
            "risk_score": assessment.risk_score if assessment else 5.0,
            "requires_ai": assessment.requires_ai_investigation if assessment else False,
        })
    return {"vessels": vessels_out, "count": len(vessels_out)}


@router.get("/voyage/{voyage_id}")
async def get_voyage(voyage_id: str) -> Dict[str, Any]:
    """Returns voyage details, waypoints, and projected trajectory."""
    voy = dispatcher.voyages.get(voyage_id)
    if not voy:
        raise HTTPException(status_code=404, detail="Voyage not found")

    vessel = dispatcher.vessels.get(voy.vessel_id)
    trajectory = []
    if vessel:
        pts = dispatcher.trajectory_engine.project_voyage_trajectory(vessel, voy)
        trajectory = [pt.model_dump(mode="json") for pt in pts]

    exposure = dispatcher.exposures.get(voy.vessel_id)

    return {
        "voyage": voy.model_dump(mode="json"),
        "trajectory": trajectory,
        "exposure": exposure.model_dump(mode="json") if exposure else None,
    }


@router.get("/risks")
async def get_risks() -> Dict[str, Any]:
    """Returns fleet risk assessments, active storms, and active incidents."""
    assessments_list = [a.model_dump(mode="json") for a in dispatcher.assessments.values()]
    tier_weights = {"CRITICAL": 4, "HIGH": 3, "WATCH": 2, "NORMAL": 1}
    assessments_list.sort(key=lambda a: (tier_weights.get(a["risk_tier"], 0), a["risk_score"]), reverse=True)

    stats = {
        "total": len(assessments_list),
        "critical": sum(1 for a in assessments_list if a["risk_tier"] == "CRITICAL"),
        "high": sum(1 for a in assessments_list if a["risk_tier"] == "HIGH"),
        "watch": sum(1 for a in assessments_list if a["risk_tier"] == "WATCH"),
        "normal": sum(1 for a in assessments_list if a["risk_tier"] == "NORMAL"),
    }

    return {
        "assessments": assessments_list,
        "stats": stats,
        "storms": dispatcher.weather_provider.fetch_active_storms_summary(),
        "incidents": [inc.model_dump(mode="json") for inc in dispatcher.incident_provider.get_all_active_incidents()],
    }


@router.get("/investigate/{vessel_id}")
async def get_investigation(vessel_id: str) -> Dict[str, Any]:
    """Returns the Management Risk Brief and Draft Actions for a vessel."""
    brief = dispatcher.briefs.get(vessel_id)
    if not brief:
        # Check if assessment exists
        assessment = dispatcher.assessments.get(vessel_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Vessel not found in fleet assessments")

        # Run investigation on demand
        brief, draft_acts = await dispatcher.agent.investigate_voyage(assessment)
        dispatcher.briefs[vessel_id] = brief
        for act in draft_acts:
            dispatcher.actions[act.action_id] = act

    # Collect draft actions for this brief
    actions_list = [
        act.model_dump(mode="json")
        for act in dispatcher.actions.values()
        if act.vessel_id == vessel_id or act.brief_id == brief.brief_id
    ]

    return {
        "brief": brief.model_dump(mode="json"),
        "actions": actions_list,
    }


@router.post("/investigate/{vessel_id}/run")
async def run_investigation_on_demand(vessel_id: str) -> Dict[str, Any]:
    """Forces a fresh AI investigation run on a specific vessel."""
    assessment = dispatcher.assessments.get(vessel_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Vessel assessment not found")

    brief, draft_acts = await dispatcher.agent.investigate_voyage(assessment)
    dispatcher.briefs[vessel_id] = brief
    for act in draft_acts:
        dispatcher.actions[act.action_id] = act

    return {
        "brief": brief.model_dump(mode="json"),
        "actions": [act.model_dump(mode="json") for act in draft_acts],
    }


@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, payload: ActionApprovePayload = Body(default=ActionApprovePayload())) -> Dict[str, Any]:
    """Operator approves a draft action (e.g. sending customer SLA memo)."""
    act = await dispatcher.approve_action(action_id, operator_name=payload.operator_name, notes=payload.notes)
    if not act:
        raise HTTPException(status_code=404, detail="Action ID not found")
    return {"status": "SUCCESS", "action": act.model_dump(mode="json")}


@router.post("/actions/{action_id}/edit")
async def edit_and_approve_action(action_id: str, payload: ActionEditPayload) -> Dict[str, Any]:
    """Operator edits draft content and approves."""
    act = await dispatcher.edit_and_approve_action(action_id, edited_content=payload.edited_content, operator_name=payload.operator_name)
    if not act:
        raise HTTPException(status_code=404, detail="Action ID not found")
    return {"status": "SUCCESS", "action": act.model_dump(mode="json")}


@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, payload: ActionRejectPayload = Body(default=ActionRejectPayload())) -> Dict[str, Any]:
    """Operator rejects the draft action."""
    act = await dispatcher.reject_action(action_id, operator_name=payload.operator_name, reason=payload.reason)
    if not act:
        raise HTTPException(status_code=404, detail="Action ID not found")
    return {"status": "SUCCESS", "action": act.model_dump(mode="json")}


@router.get("/actions/audit-log")
async def get_audit_log() -> Dict[str, Any]:
    """Returns history of human-in-the-loop action approvals and rejections."""
    return {"audit_log": dispatcher.action_audit_log, "count": len(dispatcher.action_audit_log)}


@router.post("/scenarios/trigger/{scenario_id}")
async def trigger_scenario(scenario_id: str) -> Dict[str, Any]:
    """Triggers interactive demo scenarios."""
    if scenario_id == "typhoon_malakas":
        return await dispatcher.trigger_scenario_typhoon_malakas()
    elif scenario_id == "red_sea_security":
        return await dispatcher.trigger_scenario_red_sea_security()
    elif scenario_id == "reset":
        return await dispatcher.trigger_scenario_reset()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_id}")


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Returns observability metrics: throughput, filter ratios, latencies."""
    return dispatcher.metrics

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket

from backend.app.core.models import (
    Vessel,
    Voyage,
    MaritimeIncident,
    WeatherExposure,
    RiskAssessment,
    ManagementRiskBrief,
    DraftAction,
    ActionStatus,
    RiskTier,
)
from backend.app.adapters.simulated_data import generate_initial_dataset
from backend.app.adapters.weather_provider import WeatherProvider
from backend.app.adapters.incident_provider import IncidentProvider
from backend.app.engine.trajectory import TrajectoryEngine
from backend.app.engine.intersection import IntersectionEngine
from backend.app.engine.risk_engine import RiskEngine
from backend.app.erp.database import MaritimeERPDatabase
from backend.app.agent.tools import AgentToolSuite
from backend.app.agent.investigation_agent import AIInvestigationAgent


class FleetEventDispatcher:
    """Central event orchestrator, simulation controller, and WebSocket broadcaster."""

    def __init__(self):
        # 1. Initialize dataset
        vessels_list, voyages_dict, initial_incidents = generate_initial_dataset()
        self.vessels: Dict[str, Vessel] = {v.vessel_id: v for v in vessels_list}
        self.voyages: Dict[str, Voyage] = voyages_dict

        # 2. Providers & ERP Database
        self.weather_provider = WeatherProvider()
        self.incident_provider = IncidentProvider(initial_incidents)
        self.erp_db = MaritimeERPDatabase()

        # 3. Engines
        self.trajectory_engine = TrajectoryEngine(step_hours=2.0)
        self.intersection_engine = IntersectionEngine(self.weather_provider, self.incident_provider)
        self.risk_engine = RiskEngine(
            self.trajectory_engine,
            self.intersection_engine,
            self.weather_provider,
            self.incident_provider,
        )

        # 4. Storage for exposures, assessments, briefs, and actions
        self.exposures: Dict[str, WeatherExposure] = {}
        self.assessments: Dict[str, RiskAssessment] = {}
        self.briefs: Dict[str, ManagementRiskBrief] = {}
        self.actions: Dict[str, DraftAction] = {}
        self.action_audit_log: List[Dict[str, Any]] = []

        # 5. Agent
        self.tool_suite = AgentToolSuite(
            erp_db=self.erp_db,
            vessels_dict=self.vessels,
            voyages_dict=self.voyages,
            exposures_dict=self.exposures,
            incidents_dict=self.incident_provider.incidents,
        )
        self.agent = AIInvestigationAgent(self.tool_suite)

        # 6. Active WebSocket connections
        self.active_connections: Set[WebSocket] = set()

        # 7. Metrics state
        self.metrics = {
            "total_evaluations_run": 0,
            "vessels_screened_total": 0,
            "candidates_evaluated_total": 0,
            "ai_investigations_triggered": 0,
            "actions_approved_count": 0,
            "actions_rejected_count": 0,
            "avg_filter_latency_ms": 0.45,
            "avg_risk_latency_ms": 2.10,
            "avg_agent_latency_ms": 420.0,
            "active_scenario": "BASELINE",
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event_type: str, data: Any):
        """Broadcasts a JSON message to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        
        # Serialize with Pydantic / JSON default handler
        raw = json.dumps(message, default=str)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(raw)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.active_connections.discard(ws)

    async def run_full_fleet_evaluation(self) -> Dict[str, Any]:
        """Runs the deterministic 2-tier risk engine over the fleet."""
        t0 = time.perf_counter()
        
        vessels_list = list(self.vessels.values())
        assessments, stats = await self.risk_engine.evaluate_fleet(vessels_list, self.voyages)
        
        t_eval = (time.perf_counter() - t0) * 1000.0

        # Update stored assessments & exposures
        self.assessments.clear()
        self.exposures.clear()
        
        for a in assessments:
            self.assessments[a.vessel_id] = a
            if a.exposure:
                self.exposures[a.vessel_id] = a.exposure

        # Automatically trigger AI investigation on CRITICAL/HIGH vessels if not already investigated
        for a in assessments:
            if a.requires_ai_investigation and a.vessel_id not in self.briefs:
                t_agent_0 = time.perf_counter()
                brief, draft_acts = await self.agent.investigate_voyage(a)
                t_agent = (time.perf_counter() - t_agent_0) * 1000.0
                
                self.briefs[a.vessel_id] = brief
                for act in draft_acts:
                    self.actions[act.action_id] = act
                
                self.metrics["ai_investigations_triggered"] += 1
                self.metrics["avg_agent_latency_ms"] = round(t_agent, 2)

        # Update metrics
        self.metrics["total_evaluations_run"] += 1
        self.metrics["vessels_screened_total"] += len(vessels_list)
        self.metrics["candidates_evaluated_total"] += stats["candidates_screened"]
        self.metrics["avg_risk_latency_ms"] = round(t_eval, 2)

        payload = {
            "assessments": [a.model_dump(mode="json") for a in assessments],
            "stats": stats,
            "storms": self.weather_provider.fetch_active_storms_summary(),
            "incidents": [inc.model_dump(mode="json") for inc in self.incident_provider.get_all_active_incidents()],
            "metrics": self.metrics,
        }

        await self.broadcast("FLEET_RISK_UPDATED", payload)
        return payload

    async def trigger_scenario_typhoon_malakas(self) -> Dict[str, Any]:
        """Flagship Hackathon Scenario: Injects Typhoon Malakas and evaluates immediate cascade."""
        self.weather_provider.inject_severe_typhoon_malakas()
        self.metrics["active_scenario"] = "TYPHOON_MALAKAS"
        
        # Clear previous briefs for fresh investigation
        if "VSL-OS-104" in self.briefs:
            del self.briefs["VSL-OS-104"]

        res = await self.run_full_fleet_evaluation()
        await self.broadcast("SCENARIO_TRIGGERED", {"scenario": "TYPHOON_MALAKAS", "message": "Severe Typhoon Malakas formed in Andaman Sea / Bay of Bengal."})
        return res

    async def trigger_scenario_red_sea_security(self) -> Dict[str, Any]:
        """Scenario: Injects escalated Red Sea incident affecting Star Voyager."""
        now = datetime.now(timezone.utc)
        self.incident_provider.inject_incident(
            MaritimeIncident(
                incident_id="INC-SEC-REDSEA-CRIT",
                type=IncidentType.SECURITY_CONFLICT,
                title="CRITICAL: Southern Red Sea Transit Closure Advisory",
                description="Active surface projectile activity. All commercial vessels advised to divert via Cape of Good Hope.",
                lat=14.0,
                lon=42.5,
                radius_nm=180.0,
                severity_score=95.0,
                active=True,
                reported_at=now,
                affected_corridors=["Bab-el-Mandeb", "Red Sea"],
            )
        )
        self.metrics["active_scenario"] = "RED_SEA_CONFLICT"
        res = await self.run_full_fleet_evaluation()
        await self.broadcast("SCENARIO_TRIGGERED", {"scenario": "RED_SEA_CONFLICT", "message": "Red Sea transit security level elevated to CRITICAL."})
        return res

    async def trigger_scenario_reset(self) -> Dict[str, Any]:
        """Resets all storms, incidents, briefs, and actions to baseline state."""
        self.weather_provider.reset_weather()
        vessels_list, voyages_dict, initial_incidents = generate_initial_dataset()
        self.incident_provider.reset_incidents(initial_incidents)
        self.briefs.clear()
        self.actions.clear()
        self.metrics["active_scenario"] = "BASELINE"
        
        res = await self.run_full_fleet_evaluation()
        await self.broadcast("SCENARIO_RESET", {"message": "Fleet reset to baseline nominal parameters."})
        return res

    async def approve_action(self, action_id: str, operator_name: str = "Chief Fleet Controller", notes: Optional[str] = None) -> Optional[DraftAction]:
        """Human-in-the-loop action approval."""
        act = self.actions.get(action_id)
        if not act:
            return None

        now = datetime.now(timezone.utc)
        act.status = ActionStatus.APPROVED
        act.approved_by = operator_name
        act.approved_at = now
        act.operator_notes = notes

        self.metrics["actions_approved_count"] += 1

        self.action_audit_log.append({
            "action_id": act.action_id,
            "vessel_id": act.vessel_id,
            "voyage_id": act.voyage_id,
            "status": "APPROVED",
            "approved_by": operator_name,
            "timestamp": now.isoformat(),
            "recipient": act.recipient_email,
            "subject": act.subject,
        })

        await self.broadcast("ACTION_STATE_CHANGED", act.model_dump(mode="json"))
        return act

    async def edit_and_approve_action(self, action_id: str, edited_content: str, operator_name: str = "Chief Fleet Controller") -> Optional[DraftAction]:
        """Operator edits content and approves the action."""
        act = self.actions.get(action_id)
        if not act:
            return None

        now = datetime.now(timezone.utc)
        act.status = ActionStatus.EDITED
        act.edited_content = edited_content
        act.approved_by = operator_name
        act.approved_at = now

        self.metrics["actions_approved_count"] += 1

        self.action_audit_log.append({
            "action_id": act.action_id,
            "vessel_id": act.vessel_id,
            "voyage_id": act.voyage_id,
            "status": "EDITED_AND_APPROVED",
            "approved_by": operator_name,
            "timestamp": now.isoformat(),
            "recipient": act.recipient_email,
            "subject": act.subject,
            "edited_content": edited_content,
        })

        await self.broadcast("ACTION_STATE_CHANGED", act.model_dump(mode="json"))
        return act

    async def reject_action(self, action_id: str, operator_name: str = "Chief Fleet Controller", reason: str = "Dismissed by operator") -> Optional[DraftAction]:
        """Operator rejects the draft action."""
        act = self.actions.get(action_id)
        if not act:
            return None

        now = datetime.now(timezone.utc)
        act.status = ActionStatus.REJECTED
        act.approved_by = operator_name
        act.approved_at = now
        act.operator_notes = reason

        self.metrics["actions_rejected_count"] += 1

        self.action_audit_log.append({
            "action_id": act.action_id,
            "vessel_id": act.vessel_id,
            "status": "REJECTED",
            "approved_by": operator_name,
            "timestamp": now.isoformat(),
            "reason": reason,
        })

        await self.broadcast("ACTION_STATE_CHANGED", act.model_dump(mode="json"))
        return act

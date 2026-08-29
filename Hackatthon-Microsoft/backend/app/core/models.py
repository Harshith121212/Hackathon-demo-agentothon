from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VesselType(str, Enum):
    CONTAINER = "Container"
    TANKER = "Tanker"
    BULK_CARRIER = "Bulk Carrier"
    LNG_CARRIER = "LNG Carrier"
    GENERAL_CARGO = "General Cargo"


class RiskTier(str, Enum):
    NORMAL = "NORMAL"        # Green: safe operational parameters
    WATCH = "WATCH"          # Yellow: marginal conditions, monitor
    HIGH = "HIGH"            # Orange: significant exposure, evaluate business impact
    CRITICAL = "CRITICAL"    # Red: severe breach risk, customer SLA / crew / safety threat


class ActionStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"


class IncidentType(str, Enum):
    SEVERE_WEATHER = "Severe Weather"
    SECURITY_CONFLICT = "Security Conflict"
    PIRACY_ADVISORY = "Piracy Advisory"
    PORT_CONGESTION = "Port Congestion"
    CANAL_RESTRICTION = "Canal Restriction"
    FOG_LOW_VISIBILITY = "Low Visibility Fog"


class Waypoint(BaseModel):
    name: str
    lat: float
    lon: float
    order: int
    speed_limit_knots: Optional[float] = None
    passed: bool = False
    estimated_arrival: Optional[datetime] = None


class Vessel(BaseModel):
    vessel_id: str
    imo: str
    name: str
    type: VesselType
    flag: str
    lat: float
    lon: float
    speed_knots: float
    heading_deg: float
    destination: str
    eta: datetime
    draft_m: float
    length_m: float
    max_wave_tolerance_m: float = 6.5
    max_wind_tolerance_knots: float = 45.0


class Voyage(BaseModel):
    voyage_id: str
    vessel_id: str
    departure_port: str
    destination_port: str
    departure_time: datetime
    scheduled_eta: datetime
    projected_eta: datetime
    waypoints: List[Waypoint]
    current_waypoint_idx: int = 0
    status: str = "IN_TRANSIT"  # SCHEDULED, IN_TRANSIT, COMPLETED, DELAYED


class WeatherPoint(BaseModel):
    lat: float
    lon: float
    valid_time: datetime
    wind_speed_knots: float
    wind_gust_knots: float
    wave_height_m: float
    wave_period_s: float = 8.0
    visibility_nm: float = 10.0
    condition: str = "Moderate"
    storm_name: Optional[str] = None
    radius_nm: float = 50.0


class MaritimeIncident(BaseModel):
    incident_id: str
    type: IncidentType
    title: str
    description: str
    lat: float
    lon: float
    radius_nm: float
    severity_score: float = Field(ge=0.0, le=100.0)  # 0 to 100
    active: bool = True
    reported_at: datetime
    valid_until: Optional[datetime] = None
    affected_corridors: List[str] = Field(default_factory=list)


class ProjectedTrajectoryPoint(BaseModel):
    timestamp: datetime
    lat: float
    lon: float
    speed_knots: float
    heading_deg: float
    accumulated_distance_nm: float
    waypoint_name: Optional[str] = None


class WeatherExposure(BaseModel):
    exposure_id: str
    vessel_id: str
    voyage_id: str
    incident_type: IncidentType
    start_time: datetime
    end_time: datetime
    duration_hours: float
    peak_lat: float
    peak_lon: float
    max_wind_knots: float
    max_wave_m: float
    min_distance_nm: float
    peak_severity_score: float
    confidence_pct: float
    description: str


class RiskAssessment(BaseModel):
    assessment_id: str
    vessel_id: str
    voyage_id: str
    vessel_name: str
    risk_tier: RiskTier
    risk_score: float = Field(ge=0.0, le=100.0)
    primary_factors: List[str]
    exposure: Optional[WeatherExposure] = None
    incident: Optional[MaritimeIncident] = None
    requires_ai_investigation: bool = False
    assessed_at: datetime
    projected_delay_hours: float = 0.0


# --- Simulated Maritime ERP Models ---

class CustomerSLA(BaseModel):
    customer_id: str
    customer_name: str
    tier: str  # VIP Tier 1, Tier 2, Standard
    contract_id: str
    cargo_description: str
    cargo_value_usd: float
    committed_delivery_date: datetime
    penalty_per_day_late_usd: float
    cargo_temperature_sensitive: bool = False
    requires_advance_notice_hours: int = 24
    contact_email: str
    contact_person: str


class CrewSchedule(BaseModel):
    vessel_id: str
    current_master: str
    crew_count: int
    scheduled_crew_change_port: str
    scheduled_crew_change_date: datetime
    visa_expiry_cutoff: datetime
    max_continuous_duty_exceeded_if_delayed_by_hours: float = 24.0
    impact_note: str


class MaintenanceSchedule(BaseModel):
    vessel_id: str
    drydock_port: str
    scheduled_drydock_start: datetime
    mandatory_class_inspection_deadline: datetime
    demurrage_fee_per_day_usd: float = 25000.0
    impact_note: str


class PortCall(BaseModel):
    port_code: str
    port_name: str
    country: str
    reserved_berth_window_start: datetime
    reserved_berth_window_end: datetime
    pilot_booked_time: datetime
    current_congestion_level: str  # LOW, MODERATE, HIGH, CRITICAL
    average_wait_time_hours: float = 0.0
    berth_cancellation_penalty_usd: float = 15000.0


# --- AI Investigation & Management Output Models ---

class ImpactArea(str, Enum):
    CUSTOMER_SLA = "Customer SLA & Penalty"
    CREW_ROTATION = "Crew Duty & Visa Expiry"
    MAINTENANCE_DRYDOCK = "Drydock & Class Overhaul"
    PORT_BERTH = "Berth Reservation & Demurrage"
    VESSEL_SAFETY = "Hull & Cargo Sea-State Integrity"


class OperationalImpactPoint(BaseModel):
    area: ImpactArea
    severity: RiskTier
    details: str
    financial_exposure_usd: float = 0.0


class ManagementRiskBrief(BaseModel):
    brief_id: str
    vessel_id: str
    voyage_id: str
    vessel_name: str
    generated_at: datetime
    risk_level: RiskTier
    summary_headline: str
    why_explanation: str
    expected_exposure_window: str
    weather_summary: str
    operational_impacts: List[OperationalImpactPoint]
    total_estimated_financial_exposure_usd: float
    evidence_points: List[str]
    confidence_score_pct: float
    recommended_attention: List[str]  # e.g. ["Operations", "Customer Management", "Bunker/Fleet Lead"]
    reasoning_trace: List[str] = Field(default_factory=list)


class DraftAction(BaseModel):
    action_id: str
    brief_id: str
    vessel_id: str
    voyage_id: str
    recipient_type: str  # Customer, Operations Desk, Master, Port Agent
    recipient_name: str
    recipient_email: str
    subject: str
    draft_content: str
    rationale: str
    created_at: datetime
    status: ActionStatus = ActionStatus.PENDING_APPROVAL
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    edited_content: Optional[str] = None
    operator_notes: Optional[str] = None

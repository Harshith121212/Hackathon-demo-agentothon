from typing import Dict, Any, Optional
from datetime import datetime
from backend.app.core.models import (
    Vessel,
    Voyage,
    WeatherExposure,
    MaritimeIncident,
    CustomerSLA,
    CrewSchedule,
    MaintenanceSchedule,
    PortCall,
)
from backend.app.erp.database import MaritimeERPDatabase


class AgentToolSuite:
    """Tool execution interface providing the AI agent access to ERP and operational state."""

    def __init__(
        self,
        erp_db: MaritimeERPDatabase,
        vessels_dict: Dict[str, Vessel],
        voyages_dict: Dict[str, Voyage],
        exposures_dict: Dict[str, WeatherExposure],
        incidents_dict: Dict[str, MaritimeIncident],
    ):
        self.erp_db = erp_db
        self.vessels_dict = vessels_dict
        self.voyages_dict = voyages_dict
        self.exposures_dict = exposures_dict
        self.incidents_dict = incidents_dict

    def get_vessel_details(self, vessel_id: str) -> Dict[str, Any]:
        """Returns physical specifications, current coordinate, speed, heading, and limits of the vessel."""
        v = self.vessels_dict.get(vessel_id)
        if not v:
            return {"error": f"Vessel {vessel_id} not found"}
        return {
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
            "max_wave_tolerance_m": v.max_wave_tolerance_m,
            "max_wind_tolerance_knots": v.max_wind_tolerance_knots,
        }

    def get_voyage_details(self, voyage_id: str) -> Dict[str, Any]:
        """Returns departure port, destination port, schedule, and remaining waypoint count."""
        voy = self.voyages_dict.get(voyage_id)
        if not voy:
            return {"error": f"Voyage {voyage_id} not found"}
        return {
            "voyage_id": voy.voyage_id,
            "vessel_id": voy.vessel_id,
            "departure_port": voy.departure_port,
            "destination_port": voy.destination_port,
            "scheduled_eta": voy.scheduled_eta.isoformat(),
            "projected_eta": voy.projected_eta.isoformat(),
            "waypoints_count": len(voy.waypoints),
            "unpassed_waypoints": [wp.name for wp in voy.waypoints if not wp.passed],
            "status": voy.status,
        }

    def get_weather_exposure(self, vessel_id: str) -> Dict[str, Any]:
        """Returns deterministic weather exposure metrics: time window, max waves, max wind, and severity."""
        exp = self.exposures_dict.get(vessel_id)
        if not exp:
            return {"exposure_found": False, "message": "No severe weather exposure recorded for this vessel."}
        return {
            "exposure_found": True,
            "exposure_id": exp.exposure_id,
            "incident_type": exp.incident_type.value,
            "start_time": exp.start_time.strftime("%Y-%m-%d %H:%M UTC"),
            "end_time": exp.end_time.strftime("%Y-%m-%d %H:%M UTC"),
            "duration_hours": exp.duration_hours,
            "peak_lat": exp.peak_lat,
            "peak_lon": exp.peak_lon,
            "max_wind_knots": exp.max_wind_knots,
            "max_wave_m": exp.max_wave_m,
            "severity_score": exp.peak_severity_score,
            "confidence_pct": exp.confidence_pct,
            "description": exp.description,
        }

    def get_customer_sla(self, voyage_id: str) -> Dict[str, Any]:
        """Returns customer charter contract, cargo details, valuation, committed delivery date, and penalty terms."""
        sla = self.erp_db.get_customer_sla(voyage_id)
        if not sla:
            return {"sla_found": False, "message": "Standard spot cargo; no VIP SLA penalties attached."}
        return {
            "sla_found": True,
            "customer_name": sla.customer_name,
            "tier": sla.tier,
            "contract_id": sla.contract_id,
            "cargo_description": sla.cargo_description,
            "cargo_value_usd": sla.cargo_value_usd,
            "committed_delivery_date": sla.committed_delivery_date.strftime("%Y-%m-%d %H:%M UTC"),
            "penalty_per_day_late_usd": sla.penalty_per_day_late_usd,
            "cargo_temperature_sensitive": sla.cargo_temperature_sensitive,
            "requires_advance_notice_hours": sla.requires_advance_notice_hours,
            "contact_email": sla.contact_email,
            "contact_person": sla.contact_person,
        }

    def get_crew_schedule(self, vessel_id: str) -> Dict[str, Any]:
        """Returns master name, crew change window, visa expiration date, and labor compliance limits."""
        cs = self.erp_db.get_crew_schedule(vessel_id)
        if not cs:
            return {"crew_schedule_found": False, "message": "Standard crew rotation profile."}
        return {
            "crew_schedule_found": True,
            "current_master": cs.current_master,
            "crew_count": cs.crew_count,
            "scheduled_crew_change_port": cs.scheduled_crew_change_port,
            "scheduled_crew_change_date": cs.scheduled_crew_change_date.strftime("%Y-%m-%d %H:%M UTC"),
            "visa_expiry_cutoff": cs.visa_expiry_cutoff.strftime("%Y-%m-%d %H:%M UTC"),
            "max_delay_allowance_hours": cs.max_continuous_duty_exceeded_if_delayed_by_hours,
            "impact_note": cs.impact_note,
        }

    def get_maintenance_schedule(self, vessel_id: str) -> Dict[str, Any]:
        """Returns drydock shipyard booking, class renewal deadline, and forfeiture fees."""
        ms = self.erp_db.get_maintenance_schedule(vessel_id)
        if not ms:
            return {"maintenance_scheduled": False, "message": "No imminent shipyard or drydock booking."}
        return {
            "maintenance_scheduled": True,
            "drydock_port": ms.drydock_port,
            "scheduled_drydock_start": ms.scheduled_drydock_start.strftime("%Y-%m-%d %H:%M UTC"),
            "mandatory_class_deadline": ms.mandatory_class_inspection_deadline.strftime("%Y-%m-%d %H:%M UTC"),
            "demurrage_fee_per_day_usd": ms.demurrage_fee_per_day_usd,
            "impact_note": ms.impact_note,
        }

    def get_port_congestion(self, port_code: str) -> Dict[str, Any]:
        """Returns port congestion level, berth reservation window, and average wait time."""
        pc = self.erp_db.get_port_call(port_code)
        if not pc:
            return {"port_found": False, "message": f"Port {port_code} normal operational conditions."}
        return {
            "port_found": True,
            "port_code": pc.port_code,
            "port_name": pc.port_name,
            "congestion_level": pc.current_congestion_level,
            "average_wait_time_hours": pc.average_wait_time_hours,
            "berth_reservation_start": pc.reserved_berth_window_start.strftime("%Y-%m-%d %H:%M UTC"),
            "berth_reservation_end": pc.reserved_berth_window_end.strftime("%Y-%m-%d %H:%M UTC"),
            "berth_cancellation_penalty_usd": pc.berth_cancellation_penalty_usd,
        }

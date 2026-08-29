import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from backend.app.core.models import MaritimeIncident, IncidentType


class IncidentProvider:
    """Manages maritime security, geopolitical risks, and port disruption bulletins."""

    def __init__(self, initial_incidents: Optional[List[MaritimeIncident]] = None):
        self.incidents: Dict[str, MaritimeIncident] = {}
        if initial_incidents:
            for inc in initial_incidents:
                self.incidents[inc.incident_id] = inc

    def calculate_distance_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R_nm = 3440.065
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R_nm * c

    def get_all_active_incidents(self) -> List[MaritimeIncident]:
        return [inc for inc in self.incidents.values() if inc.active]

    def find_intersecting_incidents(self, lat: float, lon: float, buffer_nm: float = 20.0) -> List[MaritimeIncident]:
        intersecting = []
        for inc in self.get_all_active_incidents():
            dist = self.calculate_distance_nm(lat, lon, inc.lat, inc.lon)
            if dist <= (inc.radius_nm + buffer_nm):
                intersecting.append(inc)
        return intersecting

    def inject_incident(self, incident: MaritimeIncident):
        self.incidents[incident.incident_id] = incident

    def remove_incident(self, incident_id: str):
        if incident_id in self.incidents:
            del self.incidents[incident_id]

    def reset_incidents(self, default_incidents: List[MaritimeIncident]):
        self.incidents.clear()
        for inc in default_incidents:
            self.incidents[inc.incident_id] = inc

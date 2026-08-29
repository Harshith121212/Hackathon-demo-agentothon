import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from backend.app.core.models import (
    Vessel,
    Voyage,
    ProjectedTrajectoryPoint,
    WeatherPoint,
    WeatherExposure,
    MaritimeIncident,
    IncidentType,
)
from backend.app.adapters.weather_provider import WeatherProvider
from backend.app.adapters.incident_provider import IncidentProvider


class IntersectionEngine:
    """Spatiotemporal intersection engine matching projected trajectories with dynamic weather and incident fields."""

    def __init__(self, weather_provider: WeatherProvider, incident_provider: IncidentProvider):
        self.weather_provider = weather_provider
        self.incident_provider = incident_provider

    async def evaluate_trajectory_exposure(
        self,
        vessel: Vessel,
        voyage: Voyage,
        trajectory: List[ProjectedTrajectoryPoint],
    ) -> Tuple[Optional[WeatherExposure], Optional[MaritimeIncident]]:
        """
        Evaluates deterministic weather and incident exposure across the projected trajectory.
        Returns WeatherExposure (if severe/marginal conditions detected) and any intersecting Incident.
        """
        if not trajectory:
            return None, None

        exposed_points: List[Tuple[ProjectedTrajectoryPoint, WeatherPoint]] = []
        intersecting_incident: Optional[MaritimeIncident] = None

        # Check incidents first along current & projected path
        for pt in trajectory:
            incidents = self.incident_provider.find_intersecting_incidents(pt.lat, pt.lon)
            if incidents:
                intersecting_incident = incidents[0]
                break

        # Check spatiotemporal weather along the trajectory
        for pt in trajectory:
            wx_point = await self.weather_provider.fetch_forecast_for_point(pt.lat, pt.lon, pt.timestamp)
            
            # Exposure condition: wave height > vessel threshold * 0.7 or wind > vessel tolerance * 0.75
            is_wave_severe = wx_point.wave_height_m >= min(4.0, vessel.max_wave_tolerance_m * 0.7)
            is_wind_severe = wx_point.wind_speed_knots >= min(32.0, vessel.max_wind_tolerance_knots * 0.75)

            if is_wave_severe or is_wind_severe or wx_point.storm_name is not None:
                exposed_points.append((pt, wx_point))

        if not exposed_points and not intersecting_incident:
            return None, None

        if not exposed_points:
            # Only incident detected
            return None, intersecting_incident

        # Aggregate continuous exposure window
        start_time = exposed_points[0][0].timestamp
        end_time = exposed_points[-1][0].timestamp
        duration_hours = max(2.0, (end_time - start_time).total_seconds() / 3600.0)

        # Find peak severity point
        peak_pt, peak_wx = max(exposed_points, key=lambda pair: (pair[1].wave_height_m * 10 + pair[1].wind_speed_knots))
        
        # Calculate severity score (0 to 100)
        wave_ratio = peak_wx.wave_height_m / max(1.0, vessel.max_wave_tolerance_m)
        wind_ratio = peak_wx.wind_speed_knots / max(1.0, vessel.max_wind_tolerance_knots)
        severity_score = min(100.0, max(wave_ratio, wind_ratio) * 100.0)

        # Confidence is higher for near-term projections (e.g. 85-95% in 24-48h, 75-80% in 3-5 days)
        hours_from_now = (start_time - datetime.now(timezone.utc)).total_seconds() / 3600.0
        confidence = max(65.0, min(95.0, 92.0 - (hours_from_now / 48.0) * 8.0))

        storm_label = peak_wx.storm_name or "Severe Maritime Gale"
        desc = (
            f"{storm_label} with sustained winds up to {peak_wx.wind_speed_knots:.0f} kts "
            f"(gusts {peak_wx.wind_gust_knots:.0f} kts) and significant wave height of {peak_wx.wave_height_m:.1f}m."
        )

        exposure = WeatherExposure(
            exposure_id=f"EXP-{uuid.uuid4().hex[:8].upper()}",
            vessel_id=vessel.vessel_id,
            voyage_id=voyage.voyage_id,
            incident_type=IncidentType.SEVERE_WEATHER,
            start_time=start_time,
            end_time=end_time,
            duration_hours=round(duration_hours, 1),
            peak_lat=peak_pt.lat,
            peak_lon=peak_pt.lon,
            max_wind_knots=peak_wx.wind_speed_knots,
            max_wave_m=peak_wx.wave_height_m,
            min_distance_nm=peak_wx.radius_nm,
            peak_severity_score=round(severity_score, 1),
            confidence_pct=round(confidence, 1),
            description=desc,
        )

        return exposure, intersecting_incident

import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import httpx

from backend.app.core.models import WeatherPoint


class ActiveStorm:
    def __init__(
        self,
        storm_id: str,
        name: str,
        center_lat: float,
        center_lon: float,
        speed_drift_knots: float,
        drift_heading_deg: float,
        max_wind_knots: float,
        max_wave_m: float,
        radius_nm: float,
        formation_time: datetime,
    ):
        self.storm_id = storm_id
        self.name = name
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.speed_drift_knots = speed_drift_knots
        self.drift_heading_deg = drift_heading_deg
        self.max_wind_knots = max_wind_knots
        self.max_wave_m = max_wave_m
        self.radius_nm = radius_nm
        self.formation_time = formation_time

    def get_center_at(self, target_time: datetime) -> (float, float):
        dt_hours = (target_time - self.formation_time).total_seconds() / 3600.0
        dist_nm = self.speed_drift_knots * dt_hours
        rad_heading = math.radians(self.drift_heading_deg)
        
        # 1 deg latitude ~ 60 nautical miles
        delta_lat = (dist_nm * math.cos(rad_heading)) / 60.0
        avg_lat = self.center_lat + (delta_lat / 2.0)
        cos_lat = max(0.1, math.cos(math.radians(avg_lat)))
        delta_lon = (dist_nm * math.sin(rad_heading)) / (60.0 * cos_lat)

        return self.center_lat + delta_lat, self.center_lon + delta_lon


class WeatherProvider:
    """Provides spatial-temporal marine weather forecast grids and dynamic storm models."""

    def __init__(self):
        now = datetime.now(timezone.utc)
        self.active_storms: Dict[str, ActiveStorm] = {}
        
        # Initialize default weather systems
        self._init_default_storms(now)

    def _init_default_storms(self, base_time: datetime):
        # Default mild system in North Atlantic
        self.active_storms["STORM-NATL-01"] = ActiveStorm(
            storm_id="STORM-NATL-01",
            name="North Atlantic Gale",
            center_lat=48.0,
            center_lon=-25.0,
            speed_drift_knots=12.0,
            drift_heading_deg=65.0,
            max_wind_knots=42.0,
            max_wave_m=5.8,
            radius_nm=180.0,
            formation_time=base_time - timedelta(hours=6),
        )

    def inject_severe_typhoon_malakas(self, base_time: Optional[datetime] = None):
        """Injects the flagship Typhoon Malakas intersecting Ocean Star's voyage."""
        if base_time is None:
            base_time = datetime.now(timezone.utc)

        # Centered in Andaman Sea / Bay of Bengal Gateway directly intercepting Ocean Star's projected timeline
        self.active_storms["TYPHOON-MALAKAS"] = ActiveStorm(
            storm_id="TYPHOON-MALAKAS",
            name="Typhoon Malakas (Severe Cyclone)",
            center_lat=6.00,
            center_lon=92.50,
            speed_drift_knots=3.0,
            drift_heading_deg=315.0,
            max_wind_knots=64.0,  # Force 12 Hurricane / Violent Cyclone
            max_wave_m=9.2,       # Extreme significant wave height
            radius_nm=280.0,
            formation_time=base_time,
        )

    def remove_typhoon(self):
        if "TYPHOON-MALAKAS" in self.active_storms:
            del self.active_storms["TYPHOON-MALAKAS"]

    def reset_weather(self):
        now = datetime.now(timezone.utc)
        self.active_storms.clear()
        self._init_default_storms(now)

    def calculate_distance_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in nautical miles."""
        R_nm = 3440.065  # Earth radius in nautical miles
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

    async def fetch_forecast_for_point(self, lat: float, lon: float, target_time: datetime) -> WeatherPoint:
        """Evaluates weather point at specific lat/lon and target_time."""
        # Baseline calm/moderate sea condition
        base_wind = 12.0 + (abs(lat) % 10) * 0.8
        base_wave = 1.2 + (abs(lat) % 5) * 0.2
        base_gust = base_wind * 1.3
        storm_detected_name = None
        max_dist_to_storm = 9999.0

        # Check impact of any active storm systems at target_time
        for storm in self.active_storms.values():
            storm_lat, storm_lon = storm.get_center_at(target_time)
            dist_nm = self.calculate_distance_nm(lat, lon, storm_lat, storm_lon)
            if dist_nm < storm.radius_nm:
                intensity_ratio = max(0.0, 1.0 - (dist_nm / storm.radius_nm))
                factor = intensity_ratio ** 1.1
                wind_contrib = (storm.max_wind_knots - 15.0) * factor
                wave_contrib = (storm.max_wave_m - 1.5) * factor
                
                base_wind = max(base_wind, 15.0 + wind_contrib)
                base_wave = max(base_wave, 1.5 + wave_contrib)
                base_gust = max(base_gust, base_wind * 1.4)
                storm_detected_name = storm.name
                max_dist_to_storm = dist_nm

        condition = "Calm"
        if base_wave > 6.0 or base_wind > 45.0:
            condition = "Severe Storm"
        elif base_wave > 4.0 or base_wind > 30.0:
            condition = "Rough Seas"
        elif base_wave > 2.5 or base_wind > 20.0:
            condition = "Moderate Seas"

        return WeatherPoint(
            lat=lat,
            lon=lon,
            valid_time=target_time,
            wind_speed_knots=round(base_wind, 1),
            wind_gust_knots=round(base_gust, 1),
            wave_height_m=round(base_wave, 2),
            wave_period_s=9.5 if base_wave > 4.0 else 7.0,
            visibility_nm=3.0 if base_wind > 40.0 else 10.0,
            condition=condition,
            storm_name=storm_detected_name,
            radius_nm=max_dist_to_storm,
        )

    def fetch_active_storms_summary(self) -> List[Dict]:
        """Returns list of active storms with their live coordinates and severity."""
        now = datetime.now(timezone.utc)
        summaries = []
        for s in self.active_storms.values():
            c_lat, c_lon = s.get_center_at(now)
            summaries.append({
                "storm_id": s.storm_id,
                "name": s.name,
                "lat": round(c_lat, 3),
                "lon": round(c_lon, 3),
                "radius_nm": s.radius_nm,
                "max_wind_knots": s.max_wind_knots,
                "max_wave_m": s.max_wave_m,
            })
        return summaries

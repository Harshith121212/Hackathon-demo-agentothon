import math
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
from backend.app.core.models import Vessel, Voyage, Waypoint, ProjectedTrajectoryPoint


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the Great Circle distance in nautical miles between two points."""
    R_nm = 3440.065
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R_nm * c


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the initial compass bearing in degrees from (lat1, lon1) to (lat2, lon2)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
    return bearing_deg


def interpolate_great_circle(
    lat1: float, lon1: float, lat2: float, lon2: float, fraction: float
) -> Tuple[float, float]:
    """Interpolates along the great circle arc between point 1 and point 2 at fraction [0, 1]."""
    if fraction <= 0.0:
        return lat1, lon1
    if fraction >= 1.0:
        return lat2, lon2

    d_nm = haversine_distance_nm(lat1, lon1, lat2, lon2)
    if d_nm < 0.001:
        return lat1, lon1

    delta = d_nm / 3440.065  # angular distance in radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    lam1 = math.radians(lon1)
    lam2 = math.radians(lon2)

    a = math.sin((1.0 - fraction) * delta) / math.sin(delta)
    b = math.sin(fraction * delta) / math.sin(delta)

    x = a * math.cos(phi1) * math.cos(lam1) + b * math.cos(phi2) * math.cos(lam2)
    y = a * math.cos(phi1) * math.sin(lam1) + b * math.cos(phi2) * math.sin(lam2)
    z = a * math.sin(phi1) + b * math.sin(phi2)

    res_phi = math.atan2(z, math.sqrt(x**2 + y**2))
    res_lam = math.atan2(y, x)

    return round(math.degrees(res_phi), 4), round(math.degrees(res_lam), 4)


class TrajectoryEngine:
    """Deterministic trajectory projection engine computing time-indexed vessel positions."""

    def __init__(self, step_hours: float = 2.0):
        self.step_hours = step_hours

    def project_voyage_trajectory(
        self,
        vessel: Vessel,
        voyage: Voyage,
        start_time: Optional[datetime] = None,
        max_horizon_days: int = 14,
    ) -> List[ProjectedTrajectoryPoint]:
        """
        Projects vessel's deterministic future positions at regular time intervals.
        Starting from vessel's current position and following remaining waypoints.
        """
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        trajectory: List[ProjectedTrajectoryPoint] = []
        
        # Point 0: Current vessel position
        current_pt = ProjectedTrajectoryPoint(
            timestamp=start_time,
            lat=vessel.lat,
            lon=vessel.lon,
            speed_knots=vessel.speed_knots,
            heading_deg=vessel.heading_deg,
            accumulated_distance_nm=0.0,
            waypoint_name="Current Position",
        )
        trajectory.append(current_pt)

        # Build list of legs starting from current location to unpassed waypoints
        unpassed_waypoints = [wp for wp in voyage.waypoints if not wp.passed]
        if not unpassed_waypoints:
            return trajectory

        legs: List[Tuple[float, float, float, float, float, str]] = []
        
        # First leg: from current pos to first unpassed waypoint
        first_wp = unpassed_waypoints[0]
        leg_speed = first_wp.speed_limit_knots or vessel.speed_knots
        legs.append((vessel.lat, vessel.lon, first_wp.lat, first_wp.lon, leg_speed, first_wp.name))

        # Subsequent legs between remaining waypoints
        for i in range(len(unpassed_waypoints) - 1):
            wp_a = unpassed_waypoints[i]
            wp_b = unpassed_waypoints[i + 1]
            leg_sp = wp_b.speed_limit_knots or vessel.speed_knots
            legs.append((wp_a.lat, wp_a.lon, wp_b.lat, wp_b.lon, leg_sp, wp_b.name))

        current_time = start_time
        accumulated_distance = 0.0
        max_end_time = start_time + timedelta(days=max_horizon_days)

        for lat_a, lon_a, lat_b, lon_b, speed_kts, wp_name in legs:
            leg_dist_nm = haversine_distance_nm(lat_a, lon_a, lat_b, lon_b)
            if leg_dist_nm <= 0.1:
                continue

            leg_hours = leg_dist_nm / max(1.0, speed_kts)
            leg_bearing = initial_bearing_deg(lat_a, lon_a, lat_b, lon_b)

            # Step along the leg in discrete chunks
            elapsed_on_leg = 0.0
            while elapsed_on_leg < leg_hours:
                elapsed_on_leg += self.step_hours
                current_time += timedelta(hours=self.step_hours)

                if current_time > max_end_time:
                    return trajectory

                fraction = min(1.0, elapsed_on_leg / leg_hours)
                step_lat, step_lon = interpolate_great_circle(lat_a, lon_a, lat_b, lon_b, fraction)
                dist_stepped = fraction * leg_dist_nm

                pt = ProjectedTrajectoryPoint(
                    timestamp=current_time,
                    lat=step_lat,
                    lon=step_lon,
                    speed_knots=speed_kts,
                    heading_deg=leg_bearing,
                    accumulated_distance_nm=round(accumulated_distance + dist_stepped, 1),
                    waypoint_name=wp_name if fraction >= 0.98 else None,
                )
                trajectory.append(pt)

            accumulated_distance += leg_dist_nm

        return trajectory

import pytest
from datetime import datetime, timezone, timedelta
from backend.app.core.models import Vessel, VesselType, Voyage, Waypoint
from backend.app.engine.trajectory import (
    haversine_distance_nm,
    initial_bearing_deg,
    interpolate_great_circle,
    TrajectoryEngine,
)


def test_haversine_distance():
    # Singapore (1.28, 103.85) to Rotterdam (51.98, 4.10) direct great circle ~ 5600+ nm
    dist = haversine_distance_nm(1.28, 103.85, 51.98, 4.10)
    assert 5500 < dist < 6200

    # Same point distance should be zero
    assert haversine_distance_nm(10.0, 20.0, 10.0, 20.0) == 0.0


def test_initial_bearing():
    # North bearing from (0, 0) to (10, 0) should be 0 deg
    bearing_north = initial_bearing_deg(0.0, 0.0, 10.0, 0.0)
    assert abs(bearing_north - 0.0) < 0.1 or abs(bearing_north - 360.0) < 0.1

    # East bearing from (0, 0) to (0, 10) should be 90 deg
    bearing_east = initial_bearing_deg(0.0, 0.0, 0.0, 10.0)
    assert abs(bearing_east - 90.0) < 0.1


def test_interpolate_great_circle():
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 10.0, 0.0
    mid_lat, mid_lon = interpolate_great_circle(lat1, lon1, lat2, lon2, 0.5)
    assert abs(mid_lat - 5.0) < 0.1
    assert abs(mid_lon - 0.0) < 0.1


def test_trajectory_engine_projection():
    now = datetime.now(timezone.utc)
    vessel = Vessel(
        vessel_id="VSL-TEST-01",
        imo="IMO9999999",
        name="Test Voyager",
        type=VesselType.CONTAINER,
        flag="Panama",
        lat=1.28,
        lon=103.85,
        speed_knots=20.0,
        heading_deg=290.0,
        destination="Rotterdam",
        eta=now + timedelta(days=10),
        draft_m=12.0,
        length_m=300.0,
    )

    voyage = Voyage(
        voyage_id="VY-TEST-01",
        vessel_id="VSL-TEST-01",
        departure_port="Singapore",
        destination_port="Rotterdam",
        departure_time=now,
        scheduled_eta=now + timedelta(days=10),
        projected_eta=now + timedelta(days=10),
        waypoints=[
            Waypoint(name="WP1", lat=1.28, lon=103.85, order=1, passed=True),
            Waypoint(name="WP2", lat=2.50, lon=101.50, order=2, passed=False),
            Waypoint(name="WP3", lat=5.50, lon=95.00, order=3, passed=False),
        ],
        current_waypoint_idx=1,
        status="IN_TRANSIT",
    )

    engine = TrajectoryEngine(step_hours=2.0)
    trajectory = engine.project_voyage_trajectory(vessel, voyage, start_time=now)

    assert len(trajectory) > 0
    assert trajectory[0].lat == vessel.lat
    assert trajectory[0].lon == vessel.lon
    # Ensure trajectory timestamps are monotonically increasing
    for i in range(len(trajectory) - 1):
        assert trajectory[i + 1].timestamp > trajectory[i].timestamp
        assert trajectory[i + 1].accumulated_distance_nm >= trajectory[i].accumulated_distance_nm

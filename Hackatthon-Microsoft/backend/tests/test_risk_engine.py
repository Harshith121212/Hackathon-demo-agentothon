import pytest
from datetime import datetime, timezone, timedelta
from backend.app.core.models import Vessel, VesselType, Voyage, Waypoint, IncidentType, MaritimeIncident
from backend.app.adapters.weather_provider import WeatherProvider
from backend.app.adapters.incident_provider import IncidentProvider
from backend.app.engine.trajectory import TrajectoryEngine
from backend.app.engine.intersection import IntersectionEngine
from backend.app.engine.risk_engine import RiskEngine


@pytest.mark.asyncio
async def test_intersection_with_severe_storm():
    now = datetime.now(timezone.utc)
    weather = WeatherProvider()
    incidents = IncidentProvider()
    
    # Inject Typhoon in Andaman Sea
    weather.inject_severe_typhoon_malakas(now)

    vessel = Vessel(
        vessel_id="VSL-OS-104",
        imo="IMO9821453",
        name="Ocean Star",
        type=VesselType.CONTAINER,
        flag="Panama",
        lat=4.80,
        lon=98.50,
        speed_knots=18.5,
        heading_deg=295.0,
        destination="Rotterdam",
        eta=now + timedelta(days=16),
        draft_m=14.5,
        length_m=366.0,
        max_wave_tolerance_m=6.0,
    )

    voyage = Voyage(
        voyage_id="OS-104",
        vessel_id="VSL-OS-104",
        departure_port="Singapore",
        destination_port="Rotterdam",
        departure_time=now - timedelta(days=1),
        scheduled_eta=now + timedelta(days=16),
        projected_eta=now + timedelta(days=16),
        waypoints=[
            Waypoint(name="Andaman Gateway", lat=6.00, lon=95.00, order=1, passed=False),
            Waypoint(name="Sri Lanka South", lat=5.80, lon=80.50, order=2, passed=False),
        ],
        status="IN_TRANSIT",
    )

    traj_engine = TrajectoryEngine(step_hours=1.0)
    trajectory = traj_engine.project_voyage_trajectory(vessel, voyage, start_time=now)
    
    intersection_engine = IntersectionEngine(weather, incidents)
    exposure, incident = await intersection_engine.evaluate_trajectory_exposure(vessel, voyage, trajectory)

    assert exposure is not None
    assert exposure.max_wave_m >= 6.0
    assert exposure.duration_hours >= 1.0
    assert exposure.peak_severity_score >= 70.0
    assert exposure.incident_type == IncidentType.SEVERE_WEATHER


@pytest.mark.asyncio
async def test_risk_scoring_and_fleet_scale_filter():
    now = datetime.now(timezone.utc)
    weather = WeatherProvider()
    weather.inject_severe_typhoon_malakas(now)
    incidents = IncidentProvider()

    traj_engine = TrajectoryEngine(step_hours=2.0)
    intersection_engine = IntersectionEngine(weather, incidents)
    risk_engine = RiskEngine(traj_engine, intersection_engine, weather, incidents)

    # Create 100 mock vessels to test fast O(N) spatial filtering
    vessels = []
    voyages = {}

    # 1 Affected vessel (Ocean Star)
    os_vessel = Vessel(
        vessel_id="VSL-OS-104",
        imo="IMO9821453",
        name="Ocean Star",
        type=VesselType.CONTAINER,
        flag="Panama",
        lat=4.80,
        lon=98.50,
        speed_knots=18.5,
        heading_deg=295.0,
        destination="Rotterdam",
        eta=now + timedelta(days=16),
        draft_m=14.5,
        length_m=366.0,
    )
    os_voyage = Voyage(
        voyage_id="OS-104",
        vessel_id="VSL-OS-104",
        departure_port="Singapore",
        destination_port="Rotterdam",
        departure_time=now - timedelta(days=1),
        scheduled_eta=now + timedelta(days=16),
        projected_eta=now + timedelta(days=16),
        waypoints=[
            Waypoint(name="Andaman Gateway", lat=6.00, lon=95.00, order=1, passed=False),
            Waypoint(name="Sri Lanka South Passage", lat=5.80, lon=80.50, order=2, passed=False),
        ],
        status="IN_TRANSIT",
    )
    vessels.append(os_vessel)
    voyages["OS-104"] = os_voyage

    # 99 Unaffected vessels placed far away in Atlantic and Pacific
    for i in range(1, 100):
        v_id = f"VSL-TEST-{i:03d}"
        voy_id = f"VY-{i:03d}"
        v = Vessel(
            vessel_id=v_id,
            imo=f"IMO9{i:06d}",
            name=f"Vessel {i}",
            type=VesselType.TANKER,
            flag="Liberia",
            lat=-30.0 + (i % 20),
            lon=-20.0 + (i % 20),
            speed_knots=14.0,
            heading_deg=45.0,
            destination="Santos",
            eta=now + timedelta(days=10),
            draft_m=12.0,
            length_m=200.0,
        )
        voy = Voyage(
            voyage_id=voy_id,
            vessel_id=v_id,
            departure_port="Cape Town",
            destination_port="Santos",
            departure_time=now,
            scheduled_eta=now + timedelta(days=10),
            projected_eta=now + timedelta(days=10),
            waypoints=[Waypoint(name="WP1", lat=-30.0, lon=-20.0, order=1, passed=False)],
            status="IN_TRANSIT",
        )
        vessels.append(v)
        voyages[voy_id] = voy

    assessments, stats = await risk_engine.evaluate_fleet(vessels, voyages)

    assert stats["total_evaluated"] == 100
    # Coarse filter should have selected candidate(s) near Andaman/Bay of Bengal and ignored distant Atlantic ships
    assert stats["candidates_screened"] <= 10
    assert stats["critical_count"] >= 1

    # Verify Ocean Star is CRITICAL
    os_assessment = next(a for a in assessments if a.vessel_id == "VSL-OS-104")
    assert os_assessment.risk_tier.value == "CRITICAL"
    assert os_assessment.requires_ai_investigation is True
    assert os_assessment.projected_delay_hours > 0

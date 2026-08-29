from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
from backend.app.core.models import Vessel, VesselType, Voyage, Waypoint, MaritimeIncident, IncidentType


def generate_initial_dataset() -> Tuple[List[Vessel], Dict[str, Voyage], List[MaritimeIncident]]:
    now = datetime.now(timezone.utc)

    # 1. Primary flagship demo vessels with high-detail routes
    # Ocean Star: Singapore -> Rotterdam (Voyage OS-104)
    ocean_star_waypoints = [
        Waypoint(name="Singapore Port Departure", lat=1.28, lon=103.85, order=1, passed=True),
        Waypoint(name="Malacca Strait South", lat=2.18, lon=102.15, order=2, passed=True),
        Waypoint(name="Malacca Strait North", lat=4.50, lon=99.00, order=3, passed=True),
        Waypoint(name="Andaman Sea Gateway", lat=6.00, lon=95.00, order=4, passed=False),
        Waypoint(name="Sri Lanka South Passage", lat=5.80, lon=80.50, order=5, passed=False),
        Waypoint(name="Arabian Sea Deep Water", lat=11.50, lon=62.00, order=6, passed=False),
        Waypoint(name="Gulf of Aden Entry", lat=12.50, lon=48.00, order=7, passed=False),
        Waypoint(name="Bab-el-Mandeb Strait", lat=12.60, lon=43.30, order=8, passed=False),
        Waypoint(name="Red Sea Midpoint", lat=20.00, lon=38.50, order=9, passed=False),
        Waypoint(name="Suez Canal South Entry", lat=29.90, lon=32.55, order=10, passed=False),
        Waypoint(name="Port Said North Exit", lat=31.30, lon=32.30, order=11, passed=False),
        Waypoint(name="Crete South Corridor", lat=34.50, lon=24.00, order=12, passed=False),
        Waypoint(name="Strait of Sicily", lat=37.20, lon=11.50, order=13, passed=False),
        Waypoint(name="Gibraltar Strait", lat=36.00, lon=-5.35, order=14, passed=False),
        Waypoint(name="Bay of Biscay West", lat=44.50, lon=-8.50, order=15, passed=False),
        Waypoint(name="English Channel Approach", lat=49.80, lon=-3.50, order=16, passed=False),
        Waypoint(name="Rotterdam Maascenter Arrival", lat=51.98, lon=4.10, order=17, passed=False),
    ]

    ocean_star = Vessel(
        vessel_id="VSL-OS-104",
        imo="IMO9821453",
        name="Ocean Star",
        type=VesselType.CONTAINER,
        flag="Panama",
        lat=4.80,
        lon=98.50,  # Currently exiting Malacca Strait into Andaman Sea
        speed_knots=18.5,
        heading_deg=295.0,
        destination="Rotterdam (NLRTM)",
        eta=now + timedelta(days=16, hours=4),
        draft_m=14.5,
        length_m=366.0,
        max_wave_tolerance_m=6.0,
        max_wind_tolerance_knots=42.0,
    )

    voyage_os104 = Voyage(
        voyage_id="OS-104",
        vessel_id="VSL-OS-104",
        departure_port="Singapore",
        destination_port="Rotterdam",
        departure_time=now - timedelta(days=1, hours=8),
        scheduled_eta=now + timedelta(days=16, hours=4),
        projected_eta=now + timedelta(days=16, hours=4),
        waypoints=ocean_star_waypoints,
        current_waypoint_idx=3,
        status="IN_TRANSIT",
    )

    # Pacific Voyager: Shanghai -> Los Angeles (Voyage PV-88)
    pacific_voyager_waypoints = [
        Waypoint(name="Yangshan Deepwater Port", lat=30.60, lon=122.10, order=1, passed=True),
        Waypoint(name="East China Sea Exit", lat=31.00, lon=126.50, order=2, passed=True),
        Waypoint(name="Tokara Strait", lat=29.80, lon=130.00, order=3, passed=True),
        Waypoint(name="North Pacific Great Circle 1", lat=36.00, lon=150.00, order=4, passed=False),
        Waypoint(name="Mid Pacific Northern Arc", lat=42.00, lon=180.00, order=5, passed=False),
        Waypoint(name="Gulf of Alaska South", lat=41.50, lon=-150.00, order=6, passed=False),
        Waypoint(name="California Offshore Corridor", lat=35.50, lon=-126.00, order=7, passed=False),
        Waypoint(name="Los Angeles Harbour Pilot", lat=33.72, lon=-118.25, order=8, passed=False),
    ]

    pacific_voyager = Vessel(
        vessel_id="VSL-PV-88",
        imo="IMO9734120",
        name="Pacific Voyager",
        type=VesselType.CONTAINER,
        flag="Liberia",
        lat=32.50,
        lon=135.00,
        speed_knots=19.2,
        heading_deg=75.0,
        destination="Los Angeles (USLAX)",
        eta=now + timedelta(days=9, hours=12),
        draft_m=15.2,
        length_m=399.0,
    )

    voyage_pv88 = Voyage(
        voyage_id="PV-88",
        vessel_id="VSL-PV-88",
        departure_port="Shanghai",
        destination_port="Los Angeles",
        departure_time=now - timedelta(days=2, hours=6),
        scheduled_eta=now + timedelta(days=9, hours=12),
        projected_eta=now + timedelta(days=9, hours=12),
        waypoints=pacific_voyager_waypoints,
        current_waypoint_idx=3,
        status="IN_TRANSIT",
    )

    # Gulf Titan: Ras Tanura -> Ningbo (Voyage GT-505) - VLCC Crude
    gulf_titan_waypoints = [
        Waypoint(name="Ras Tanura Terminal", lat=26.65, lon=50.15, order=1, passed=True),
        Waypoint(name="Strait of Hormuz", lat=26.30, lon=56.50, order=2, passed=True),
        Waypoint(name="Gulf of Oman", lat=24.50, lon=58.50, order=3, passed=True),
        Waypoint(name="Arabian Sea Southeast", lat=14.00, lon=68.00, order=4, passed=False),
        Waypoint(name="Dondra Head Sri Lanka", lat=5.60, lon=80.60, order=5, passed=False),
        Waypoint(name="Malacca Strait South Entry", lat=2.50, lon=101.50, order=6, passed=False),
        Waypoint(name="Singapore East Anchorage", lat=1.30, lon=104.20, order=7, passed=False),
        Waypoint(name="South China Sea Main", lat=13.50, lon=114.00, order=8, passed=False),
        Waypoint(name="Taiwan Strait South", lat=22.50, lon=119.00, order=9, passed=False),
        Waypoint(name="Ningbo-Zhoushan Anchorage", lat=29.85, lon=122.15, order=10, passed=False),
    ]

    gulf_titan = Vessel(
        vessel_id="VSL-GT-505",
        imo="IMO9654321",
        name="Gulf Titan",
        type=VesselType.TANKER,
        flag="Marshall Islands",
        lat=21.00,
        lon=62.00,
        speed_knots=14.0,
        heading_deg=135.0,
        destination="Ningbo (CNNGB)",
        eta=now + timedelta(days=11, hours=18),
        draft_m=20.5,
        length_m=333.0,
    )

    voyage_gt505 = Voyage(
        voyage_id="GT-505",
        vessel_id="VSL-GT-505",
        departure_port="Ras Tanura",
        destination_port="Ningbo",
        departure_time=now - timedelta(days=3, hours=4),
        scheduled_eta=now + timedelta(days=11, hours=18),
        projected_eta=now + timedelta(days=11, hours=18),
        waypoints=gulf_titan_waypoints,
        current_waypoint_idx=3,
        status="IN_TRANSIT",
    )

    # Atlantic Horizon: Santos -> Antwerp (Voyage AH-12) - Agri-Bulk
    atlantic_horizon_waypoints = [
        Waypoint(name="Santos Port Outbound", lat=-23.98, lon=-46.30, order=1, passed=True),
        Waypoint(name="Cabo Frio Offshore", lat=-23.10, lon=-41.80, order=2, passed=True),
        Waypoint(name="Recife East Arc", lat=-8.50, lon=-34.00, order=3, passed=False),
        Waypoint(name="Equator Mid-Atlantic", lat=0.00, lon=-28.00, order=4, passed=False),
        Waypoint(name="Canary Islands West", lat=28.00, lon=-18.50, order=5, passed=False),
        Waypoint(name="Finisterre Traffic Lane", lat=43.00, lon=-9.50, order=6, passed=False),
        Waypoint(name="English Channel West", lat=49.50, lon=-4.00, order=7, passed=False),
        Waypoint(name="Flushing Scheldt Entry", lat=51.40, lon=3.60, order=8, passed=False),
        Waypoint(name="Antwerp Bulk Quay", lat=51.28, lon=4.32, order=9, passed=False),
    ]

    atlantic_horizon = Vessel(
        vessel_id="VSL-AH-12",
        imo="IMO9412988",
        name="Atlantic Horizon",
        type=VesselType.BULK_CARRIER,
        flag="Singapore",
        lat=-14.20,
        lon=-37.10,
        speed_knots=13.5,
        heading_deg=25.0,
        destination="Antwerp (BEANR)",
        eta=now + timedelta(days=14, hours=6),
        draft_m=12.8,
        length_m=229.0,
    )

    voyage_ah12 = Voyage(
        voyage_id="AH-12",
        vessel_id="VSL-AH-12",
        departure_port="Santos",
        destination_port="Antwerp",
        departure_time=now - timedelta(days=2, hours=10),
        scheduled_eta=now + timedelta(days=14, hours=6),
        projected_eta=now + timedelta(days=14, hours=6),
        waypoints=atlantic_horizon_waypoints,
        current_waypoint_idx=2,
        status="IN_TRANSIT",
    )

    # Red Sea Star Voyager: Jeddah -> Genoa (SV-201)
    star_voyager_waypoints = [
        Waypoint(name="Jeddah Islamic Port", lat=21.48, lon=39.15, order=1, passed=True),
        Waypoint(name="Red Sea Central Channel", lat=19.50, lon=39.80, order=2, passed=True),
        Waypoint(name="Bab-el-Mandeb Transit", lat=12.70, lon=43.25, order=3, passed=False),
        Waypoint(name="Djibouti Offshore", lat=11.60, lon=43.15, order=4, passed=False),
    ]

    star_voyager = Vessel(
        vessel_id="VSL-SV-201",
        imo="IMO9558812",
        name="Star Voyager",
        type=VesselType.CONTAINER,
        flag="Malta",
        lat=15.20,
        lon=41.80,
        speed_knots=17.0,
        heading_deg=160.0,
        destination="Djibouti (DJJIB)",
        eta=now + timedelta(days=1, hours=8),
        draft_m=13.0,
        length_m=294.0,
    )

    voyage_sv201 = Voyage(
        voyage_id="SV-201",
        vessel_id="VSL-SV-201",
        departure_port="Jeddah",
        destination_port="Djibouti",
        departure_time=now - timedelta(hours=18),
        scheduled_eta=now + timedelta(days=1, hours=8),
        projected_eta=now + timedelta(days=1, hours=8),
        waypoints=star_voyager_waypoints,
        current_waypoint_idx=2,
        status="IN_TRANSIT",
    )

    vessels_list = [ocean_star, pacific_voyager, gulf_titan, atlantic_horizon, star_voyager]
    voyages_dict = {
        "OS-104": voyage_os104,
        "PV-88": voyage_pv88,
        "GT-505": voyage_gt505,
        "AH-12": voyage_ah12,
        "SV-201": voyage_sv201,
    }

    # Generate 45 additional realistic merchant vessels across the world
    routes_templates = [
        # (name_prefix, type, flag, [start_lat, start_lon], [dest_lat, dest_lon], from_p, to_p, speed)
        ("Nordic", VesselType.TANKER, "Norway", (58.0, 4.0), (51.5, 3.5), "Stavanger", "Rotterdam", 13.0),
        ("Tokyo", VesselType.CONTAINER, "Japan", (34.0, 137.0), (1.3, 103.8), "Tokyo", "Singapore", 18.0),
        ("Caspian", VesselType.BULK_CARRIER, "Cyprus", (36.5, -4.0), (41.0, 28.9), "Gibraltar", "Istanbul", 12.5),
        ("Poseidon", VesselType.LNG_CARRIER, "Greece", (25.5, 54.0), (32.0, 120.0), "Ras Laffan", "Incheon", 17.5),
        ("Hanseatic", VesselType.GENERAL_CARGO, "Germany", (54.0, 8.0), (60.0, 24.0), "Hamburg", "Helsinki", 14.0),
        ("Aura", VesselType.CONTAINER, "Marshall Islands", (22.3, 114.1), (34.7, 135.4), "Hong Kong", "Osaka", 19.0),
        ("Southern", VesselType.BULK_CARRIER, "Liberia", (-20.0, 118.0), (35.0, 129.0), "Port Hedland", "Busan", 12.0),
        ("Starlight", VesselType.TANKER, "Bahamas", (28.0, -90.0), (51.0, 2.0), "Houston", "Dunkirk", 14.5),
        ("Baltic", VesselType.CONTAINER, "Denmark", (55.5, 12.5), (59.3, 18.0), "Copenhagen", "Stockholm", 16.0),
    ]

    for idx in range(6, 51):
        tpl = routes_templates[(idx - 6) % len(routes_templates)]
        v_type = tpl[1]
        v_name = f"{tpl[0]} {['Mariner', 'Navigator', 'Trader', 'Leader', 'Carrier', 'Express', 'Pioneer'][idx % 7]} {idx}"
        v_id = f"VSL-GEN-{idx:03d}"
        voy_id = f"VY-{idx:03d}"
        
        # Calculate intermediate pos
        lat_step = (tpl[4][0] - tpl[3][0]) * ((idx % 9) / 10.0)
        lon_step = (tpl[4][1] - tpl[3][1]) * ((idx % 9) / 10.0)
        curr_lat = round(tpl[3][0] + lat_step, 4)
        curr_lon = round(tpl[3][1] + lon_step, 4)

        wp1 = Waypoint(name=f"{tpl[5]} Port", lat=tpl[3][0], lon=tpl[3][1], order=1, passed=True)
        wp2 = Waypoint(name="Midway Passage", lat=(tpl[3][0] + tpl[4][0])/2, lon=(tpl[3][1] + tpl[4][1])/2, order=2, passed=False)
        wp3 = Waypoint(name=f"{tpl[6]} Terminus", lat=tpl[4][0], lon=tpl[4][1], order=3, passed=False)

        v_obj = Vessel(
            vessel_id=v_id,
            imo=f"IMO9{idx:06d}",
            name=v_name,
            type=v_type,
            flag=tpl[2],
            lat=curr_lat,
            lon=curr_lon,
            speed_knots=tpl[7] + (idx % 3) * 0.5,
            heading_deg=(idx * 45) % 360,
            destination=tpl[6],
            eta=now + timedelta(days=(idx % 12) + 2, hours=(idx * 3) % 24),
            draft_m=11.0 + (idx % 8),
            length_m=200.0 + (idx % 150),
        )

        voy_obj = Voyage(
            voyage_id=voy_id,
            vessel_id=v_id,
            departure_port=tpl[5],
            destination_port=tpl[6],
            departure_time=now - timedelta(days=1 + (idx % 4)),
            scheduled_eta=v_obj.eta,
            projected_eta=v_obj.eta,
            waypoints=[wp1, wp2, wp3],
            current_waypoint_idx=1,
            status="IN_TRANSIT",
        )

        vessels_list.append(v_obj)
        voyages_dict[voy_id] = voy_obj

    # Initial maritime incidents (Security & Congestion)
    incidents = [
        MaritimeIncident(
            incident_id="INC-SEC-01",
            type=IncidentType.SECURITY_CONFLICT,
            title="Southern Red Sea / Bab-el-Mandeb High Risk Security Zone",
            description="Escalated UAV and projectile risk targeting merchant vessels without military escort. UKMTO advisory in effect.",
            lat=13.10,
            lon=43.10,
            radius_nm=140.0,
            severity_score=85.0,
            active=True,
            reported_at=now - timedelta(days=2),
            affected_corridors=["Bab-el-Mandeb", "Southern Red Sea"],
        ),
        MaritimeIncident(
            incident_id="INC-PIR-02",
            type=IncidentType.PIRACY_ADVISORY,
            title="Singapore Strait Eastbound TSS Boarding Warning",
            description="Multiple armed skiff approaches reported near Phillip Channel.",
            lat=1.20,
            lon=103.90,
            radius_nm=35.0,
            severity_score=45.0,
            active=True,
            reported_at=now - timedelta(hours=14),
            affected_corridors=["Singapore Strait TSS"],
        ),
        MaritimeIncident(
            incident_id="INC-PRT-03",
            type=IncidentType.PORT_CONGESTION,
            title="Port of Rotterdam Deep Sea Terminal Crane Maintenance Congestion",
            description="Expected berth delays of 36-48 hours for ultra-large container vessels at Maasvlakte II.",
            lat=51.96,
            lon=4.08,
            radius_nm=25.0,
            severity_score=60.0,
            active=True,
            reported_at=now - timedelta(days=1),
            affected_corridors=["Rotterdam Maasvlakte"],
        ),
    ]

    return vessels_list, voyages_dict, incidents

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from backend.app.core.models import (
    CustomerSLA,
    CrewSchedule,
    MaintenanceSchedule,
    PortCall,
)


class MaritimeERPDatabase:
    """Simulated Internal Maritime Enterprise Resource Planning (ERP) database."""

    def __init__(self):
        now = datetime.now(timezone.utc)
        self.customers: Dict[str, CustomerSLA] = {}
        self.crew_schedules: Dict[str, CrewSchedule] = {}
        self.maintenance_schedules: Dict[str, MaintenanceSchedule] = {}
        self.port_calls: Dict[str, PortCall] = {}

        self._seed_data(now)

    def _seed_data(self, now: datetime):
        # 1. Customer SLAs (keyed by voyage_id)
        self.customers["OS-104"] = CustomerSLA(
            customer_id="CUST-ACME-01",
            customer_name="Acme Logistics Global",
            tier="VIP Tier 1 Strategic Partner",
            contract_id="SLA-2026-ACME-99",
            cargo_description="High-Precision Semiconductor Lithography Units & Cryogenic Medical Sensors (140 TEU)",
            cargo_value_usd=42500000.0,
            committed_delivery_date=now + timedelta(days=16, hours=12),
            penalty_per_day_late_usd=85000.0,
            cargo_temperature_sensitive=True,
            requires_advance_notice_hours=24,
            contact_email="operations.desk@acmelogistics.com",
            contact_person="Victoria Lindqvist (VP Global Freight)",
        )

        self.customers["PV-88"] = CustomerSLA(
            customer_id="CUST-APEX-02",
            customer_name="Apex Retail Freight",
            tier="Tier 1 Partner",
            contract_id="SLA-2026-APEX-14",
            cargo_description="Consumer Electronics & High-End Apparel (450 TEU)",
            cargo_value_usd=28000000.0,
            committed_delivery_date=now + timedelta(days=10, hours=0),
            penalty_per_day_late_usd=40000.0,
            cargo_temperature_sensitive=False,
            requires_advance_notice_hours=48,
            contact_email="supplychain@apexretail.com",
            contact_person="Marcus Vance (Logistics Director)",
        )

        self.customers["GT-505"] = CustomerSLA(
            customer_id="CUST-SINO-03",
            customer_name="SinoChem Energy Logistics",
            tier="Tier 1 Energy Charterer",
            contract_id="SLA-2026-CHEM-88",
            cargo_description="2.1M Barrels Light Arabian Crude Oil",
            cargo_value_usd=168000000.0,
            committed_delivery_date=now + timedelta(days=12, hours=0),
            penalty_per_day_late_usd=65000.0,
            cargo_temperature_sensitive=False,
            requires_advance_notice_hours=24,
            contact_email="crude.desk@sinochem-logistics.com",
            contact_person="Zhang Wei (Fleet Commercial Manager)",
        )

        self.customers["AH-12"] = CustomerSLA(
            customer_id="CUST-CARG-04",
            customer_name="Cargill Agri Global",
            tier="Tier 2 Agribusiness",
            contract_id="SLA-2026-CARG-31",
            cargo_description="65,000 MT Brazilian Export Soybeans",
            cargo_value_usd=31500000.0,
            committed_delivery_date=now + timedelta(days=15, hours=0),
            penalty_per_day_late_usd=20000.0,
            cargo_temperature_sensitive=False,
            requires_advance_notice_hours=48,
            contact_email="chartering@cargill-maritime.com",
            contact_person="Eduardo Santos (Senior Broker)",
        )

        # 2. Crew Schedules (keyed by vessel_id)
        self.crew_schedules["VSL-OS-104"] = CrewSchedule(
            vessel_id="VSL-OS-104",
            current_master="Capt. Henrik Lind (Master Mariner)",
            crew_count=22,
            scheduled_crew_change_port="Rotterdam",
            scheduled_crew_change_date=now + timedelta(days=16, hours=8),
            visa_expiry_cutoff=now + timedelta(days=17, hours=12),
            max_continuous_duty_exceeded_if_delayed_by_hours=24.0,
            impact_note="Critical: 4 senior deck officers reach mandatory MLC maximum 11-month continuous service limit; EU transit visas expire in 40h post scheduled ETA.",
        )

        self.crew_schedules["VSL-PV-88"] = CrewSchedule(
            vessel_id="VSL-PV-88",
            current_master="Capt. Chen Wei",
            crew_count=24,
            scheduled_crew_change_port="Los Angeles",
            scheduled_crew_change_date=now + timedelta(days=10, hours=12),
            visa_expiry_cutoff=now + timedelta(days=18, hours=0),
            max_continuous_duty_exceeded_if_delayed_by_hours=96.0,
            impact_note="Normal buffer. US B1/B2 visas valid for 8+ days beyond scheduled arrival.",
        )

        # 3. Maintenance Schedules (keyed by vessel_id)
        self.maintenance_schedules["VSL-OS-104"] = MaintenanceSchedule(
            vessel_id="VSL-OS-104",
            drydock_port="Damen Shiprepair Rotterdam (Yard 4)",
            scheduled_drydock_start=now + timedelta(days=17, hours=18),
            mandatory_class_inspection_deadline=now + timedelta(days=22, hours=0),
            demurrage_fee_per_day_usd=28000.0,
            impact_note="Yard drydock slot reserved. If arrival delayed > 24 hours, drydock slot is forfeited to following vessel, triggering $28,000/day standby penalty.",
        )

        # 4. Port Calls (keyed by port_code)
        self.port_calls["NLRTM"] = PortCall(
            port_code="NLRTM",
            port_name="Port of Rotterdam - Maasvlakte II",
            country="Netherlands",
            reserved_berth_window_start=now + timedelta(days=16, hours=2),
            reserved_berth_window_end=now + timedelta(days=17, hours=6),
            pilot_booked_time=now + timedelta(days=16, hours=3),
            current_congestion_level="HIGH",
            average_wait_time_hours=18.0,
            berth_cancellation_penalty_usd=17500.0,
        )

        self.port_calls["USLAX"] = PortCall(
            port_code="USLAX",
            port_name="Port of Los Angeles - Pier 400",
            country="USA",
            reserved_berth_window_start=now + timedelta(days=9, hours=10),
            reserved_berth_window_end=now + timedelta(days=10, hours=18),
            pilot_booked_time=now + timedelta(days=9, hours=11),
            current_congestion_level="LOW",
            average_wait_time_hours=4.0,
            berth_cancellation_penalty_usd=12000.0,
        )

    def get_customer_sla(self, voyage_id: str) -> Optional[CustomerSLA]:
        return self.customers.get(voyage_id)

    def get_crew_schedule(self, vessel_id: str) -> Optional[CrewSchedule]:
        return self.crew_schedules.get(vessel_id)

    def get_maintenance_schedule(self, vessel_id: str) -> Optional[MaintenanceSchedule]:
        return self.maintenance_schedules.get(vessel_id)

    def get_port_call(self, port_code: str) -> Optional[PortCall]:
        return self.port_calls.get(port_code)

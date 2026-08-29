from typing import Protocol, List, Optional
from datetime import datetime
from backend.app.core.models import Vessel, Voyage, WeatherPoint, MaritimeIncident


class AISProviderProtocol(Protocol):
    """Abstraction for AIS / Vessel tracking providers (e.g. Spire, MarineTraffic, or Simulator)."""
    async def fetch_vessels(self) -> List[Vessel]:
        ...

    async def fetch_vessel_by_id(self, vessel_id: str) -> Optional[Vessel]:
        ...

    async def fetch_voyage_for_vessel(self, vessel_id: str) -> Optional[Voyage]:
        ...


class WeatherProviderProtocol(Protocol):
    """Abstraction for Marine Weather Providers (e.g. Open-Meteo Marine, NOAA GFS, Copernicus, or Simulator)."""
    async def fetch_forecast_for_point(self, lat: float, lon: float, target_time: datetime) -> WeatherPoint:
        ...

    async def fetch_active_storms(self) -> List[WeatherPoint]:
        ...


class IncidentProviderProtocol(Protocol):
    """Abstraction for Maritime Security & Port Disruption feeds (e.g. UKMTO, IMB Piracy, Port Authorities)."""
    async def fetch_active_incidents(self) -> List[MaritimeIncident]:
        ...

/**
 * Map Module: Leaflet interactive global fleet tracking, route projection, and weather overlays
 */

let mapInstance = null;
let vesselLayerGroup = null;
let stormLayerGroup = null;
let incidentLayerGroup = null;
let routeLayerGroup = null;
let selectedVesselId = null;

function getRiskColor(tier) {
  switch (tier) {
    case 'CRITICAL': return '#ef4444';
    case 'HIGH': return '#f97316';
    case 'WATCH': return '#eab308';
    case 'NORMAL':
    default: return '#10b981';
  }
}

function createShipSvg(headingDeg, riskColor, isCritical, isHigh) {
  const pulseClass = isCritical ? 'vessel-marker-critical' : (isHigh ? 'vessel-marker-high' : '');
  return `
    <div class="vessel-marker-icon ${pulseClass}" style="transform: rotate(${headingDeg}deg);">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="${riskColor}" stroke="#ffffff" stroke-width="1.2">
        <polygon points="12,2 20,20 12,16 4,20" />
      </svg>
    </div>
  `;
}

function initFleetMap() {
  if (mapInstance) return;

  mapInstance = L.map('map', {
    center: [18.0, 75.0],
    zoom: 3,
    minZoom: 2,
    maxZoom: 12,
    zoomControl: true,
  });

  // Base Dark Tile Layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(mapInstance);

  vesselLayerGroup = L.layerGroup().addTo(mapInstance);
  stormLayerGroup = L.layerGroup().addTo(mapInstance);
  incidentLayerGroup = L.layerGroup().addTo(mapInstance);
  routeLayerGroup = L.layerGroup().addTo(mapInstance);
}

function renderVessels(vessels, assessmentsDict, onSelectCallback) {
  if (!vesselLayerGroup) return;
  vesselLayerGroup.clearLayers();

  vessels.forEach(vessel => {
    const assessment = assessmentsDict[vessel.vessel_id] || {};
    const riskTier = assessment.risk_tier || vessel.risk_tier || 'NORMAL';
    const riskColor = getRiskColor(riskTier);
    const isCritical = riskTier === 'CRITICAL';
    const isHigh = riskTier === 'HIGH';

    const customIcon = L.divIcon({
      className: 'custom-vessel-div',
      html: createShipSvg(vessel.heading_deg || 0, riskColor, isCritical, isHigh),
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    const marker = L.marker([vessel.lat, vessel.lon], { icon: customIcon });

    marker.on('click', () => {
      selectedVesselId = vessel.vessel_id;
      if (onSelectCallback) onSelectCallback(vessel, assessment);
    });

    // Tooltip
    marker.bindTooltip(
      `<strong>${vessel.name}</strong><br><span style="color:${riskColor}">${riskTier}</span> • ${vessel.speed_knots} kts`,
      { direction: 'top', offset: [0, -10], opacity: 0.9 }
    );

    vesselLayerGroup.addLayer(marker);
  });
}

function renderStorms(storms) {
  if (!stormLayerGroup) return;
  stormLayerGroup.clearLayers();

  storms.forEach(storm => {
    const radiusMeters = (storm.radius_nm || 100) * 1852.0;

    const circle = L.circle([storm.lat, storm.lon], {
      radius: radiusMeters,
      color: '#ef4444',
      weight: 1.5,
      dashArray: '6, 6',
      fillColor: '#ef4444',
      fillOpacity: 0.18,
      className: 'storm-circle',
    });

    circle.bindTooltip(
      `<strong>🌀 ${storm.name}</strong><br>Max Wind: ${storm.max_wind_knots} kts<br>Wave Height: ${storm.max_wave_m}m`,
      { direction: 'center', permanent: false }
    );

    stormLayerGroup.addLayer(circle);

    // Inner violent storm core
    const coreCircle = L.circle([storm.lat, storm.lon], {
      radius: radiusMeters * 0.35,
      color: '#dc2626',
      weight: 2,
      fillColor: '#991b1b',
      fillOpacity: 0.35,
    });
    stormLayerGroup.addLayer(coreCircle);
  });
}

function renderIncidents(incidents) {
  if (!incidentLayerGroup) return;
  incidentLayerGroup.clearLayers();

  incidents.forEach(inc => {
    const radiusMeters = (inc.radius_nm || 50) * 1852.0;
    const isSecurity = inc.type.includes('Security') || inc.type.includes('Conflict');

    const circle = L.circle([inc.lat, inc.lon], {
      radius: radiusMeters,
      color: isSecurity ? '#f59e0b' : '#38bdf8',
      weight: 1.5,
      fillColor: isSecurity ? '#f59e0b' : '#38bdf8',
      fillOpacity: 0.15,
    });

    circle.bindTooltip(
      `<strong>⚠️ ${inc.title}</strong><br>${inc.description}`,
      { direction: 'top', opacity: 0.95 }
    );

    incidentLayerGroup.addLayer(circle);
  });
}

function drawVesselRoute(voyage, trajectory, exposure) {
  if (!routeLayerGroup) return;
  routeLayerGroup.clearLayers();

  if (!voyage || !voyage.waypoints || voyage.waypoints.length === 0) return;

  const latLngs = voyage.waypoints.map(wp => [wp.lat, wp.lon]);

  // Draw full planned voyage line
  const routeLine = L.polyline(latLngs, {
    color: '#00f2fe',
    weight: 2.5,
    opacity: 0.7,
    dashArray: '4, 8',
  });
  routeLayerGroup.addLayer(routeLine);

  // Draw trajectory points if provided
  if (trajectory && trajectory.length > 0) {
    const trajLatLngs = trajectory.map(pt => [pt.lat, pt.lon]);
    const trajLine = L.polyline(trajLatLngs, {
      color: '#38bdf8',
      weight: 3.5,
      opacity: 0.9,
    });
    routeLayerGroup.addLayer(trajLine);
  }

  // Draw waypoint node markers
  voyage.waypoints.forEach(wp => {
    const wpMarker = L.circleMarker([wp.lat, wp.lon], {
      radius: wp.passed ? 3 : 4.5,
      color: wp.passed ? '#64748b' : '#00f2fe',
      fillColor: wp.passed ? '#334155' : '#0f172a',
      fillOpacity: 1.0,
      weight: 2,
    });
    wpMarker.bindTooltip(`Waypoint ${wp.order}: ${wp.name}`);
    routeLayerGroup.addLayer(wpMarker);
  });

  // Highlight exposure segment if present
  if (exposure && exposure.peak_lat && exposure.peak_lon) {
    const expMarker = L.circleMarker([exposure.peak_lat, exposure.peak_lon], {
      radius: 8,
      color: '#ef4444',
      fillColor: '#ef4444',
      fillOpacity: 0.8,
      weight: 3,
    });
    expMarker.bindTooltip(
      `<strong>🔴 Weather Intercept Peak</strong><br>Time: ${exposure.start_time} to ${exposure.end_time}<br>Waves: ${exposure.max_wave_m}m`,
      { permanent: true, direction: 'top' }
    );
    routeLayerGroup.addLayer(expMarker);
  }
}

function focusMapOn(lat, lon, zoom = 5) {
  if (mapInstance) {
    mapInstance.flyTo([lat, lon], zoom, { duration: 1.2 });
  }
}

window.FleetMap = {
  initFleetMap,
  renderVessels,
  renderStorms,
  renderIncidents,
  drawVesselRoute,
  focusMapOn,
};

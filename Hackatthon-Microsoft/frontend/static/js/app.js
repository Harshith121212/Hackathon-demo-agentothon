/**
 * Main Application Controller: State Management, WebSocket Sync, Event Listeners
 */

let appState = {
  vessels: [],
  assessments: {},
  storms: [],
  incidents: [],
  stats: {},
  metrics: {},
  selectedVessel: null,
  activeFilterTier: 'ALL',
  searchQuery: '',
};

// --- Initialization ---

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Map
  FleetMap.initFleetMap();

  // 2. Initialize Live Clock
  startUtcClock();

  // 3. Setup Navigation Tabs
  setupTabNavigation();

  // 4. Setup Filter and Search Listeners
  setupFiltersAndSearch();

  // 5. Setup Scenario Buttons
  setupScenarioTriggers();

  // 6. Setup Modal Events
  setupModalEvents();

  // 7. Initial REST Fetch & WebSocket Connect
  await fetchInitialData();
  initWebSocket();
});

// --- Live UTC Clock ---

function startUtcClock() {
  function updateTime() {
    const now = new Date();
    const timeStr = now.toISOString().substring(11, 19) + ' UTC';
    const dateStr = now.toISOString().substring(0, 10);
    const elTime = document.getElementById('live-utc-time');
    const elDate = document.getElementById('live-utc-date');
    if (elTime) elTime.innerText = timeStr;
    if (elDate) elDate.innerText = dateStr;
  }
  updateTime();
  setInterval(updateTime, 1000);
}

// --- Navigation Tabs ---

function setupTabNavigation() {
  const tabCommand = document.getElementById('tab-command');
  const tabActions = document.getElementById('tab-actions');
  const tabObservability = document.getElementById('tab-observability');

  const viewCommand = document.getElementById('view-command');
  const viewActions = document.getElementById('view-actions');
  const viewObservability = document.getElementById('view-observability');

  function switchTab(activeTab, activeView) {
    [tabCommand, tabActions, tabObservability].forEach(t => {
      t.className = 'px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition flex items-center relative';
    });
    activeTab.className = 'px-3 py-1 text-xs font-medium rounded-md bg-cyan-600 text-white shadow transition flex items-center relative';

    [viewCommand, viewActions, viewObservability].forEach(v => v.classList.add('hidden'));
    activeView.classList.remove('hidden');

    if (activeView === viewCommand && window.FleetMap && FleetMap.mapInstance) {
      setTimeout(() => FleetMap.mapInstance.invalidateSize(), 100);
    }
    if (activeView === viewActions) {
      ActionsModule.fetchAndRenderActions();
    }
  }

  tabCommand.addEventListener('click', () => switchTab(tabCommand, viewCommand));
  tabActions.addEventListener('click', () => switchTab(tabActions, viewActions));
  tabObservability.addEventListener('click', () => switchTab(tabObservability, viewObservability));
}

// --- WebSocket Sync ---

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/fleet-stream`;
  let ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[WebSocket] Connected to Fleet Stream');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleWebSocketMessage(msg);
    } catch (e) {
      console.error('[WebSocket] Parse error:', e);
    }
  };

  ws.onclose = () => {
    console.warn('[WebSocket] Disconnected. Reconnecting in 3s...');
    setTimeout(initWebSocket, 3000);
  };
}

function handleWebSocketMessage(msg) {
  if (msg.event === 'INITIAL_STATE' || msg.event === 'FLEET_RISK_UPDATED') {
    const data = msg.data;
    if (data.assessments) {
      appState.assessments = {};
      data.assessments.forEach(a => { appState.assessments[a.vessel_id] = a; });
    }
    if (data.stats) appState.stats = data.stats;
    if (data.storms) appState.storms = data.storms;
    if (data.incidents) appState.incidents = data.incidents;
    if (data.metrics) appState.metrics = data.metrics;

    refreshUI();
  } else if (msg.event === 'SCENARIO_TRIGGERED' || msg.event === 'SCENARIO_RESET') {
    fetchInitialData();
  } else if (msg.event === 'ACTION_STATE_CHANGED') {
    ActionsModule.updateLocalAction(msg.data);
  }
}

// --- REST Fetch ---

async function fetchInitialData() {
  try {
    const [fleetRes, risksRes, metricsRes] = await Promise.all([
      fetch('/api/fleet'),
      fetch('/api/risks'),
      fetch('/api/metrics'),
    ]);

    const fleetData = await fleetRes.json();
    const risksData = await risksRes.json();
    const metricsData = await metricsRes.json();

    appState.vessels = fleetData.vessels || [];
    appState.storms = risksData.storms || [];
    appState.incidents = risksData.incidents || [];
    appState.stats = risksData.stats || {};
    appState.metrics = metricsData || {};

    appState.assessments = {};
    if (risksData.assessments) {
      risksData.assessments.forEach(a => { appState.assessments[a.vessel_id] = a; });
    }

    refreshUI();
  } catch (e) {
    console.error('Failed to fetch initial data:', e);
  }
}

// --- Refresh UI Components ---

function refreshUI() {
  updateKpiHeader();
  renderRiskQueue();
  
  FleetMap.renderVessels(appState.vessels, appState.assessments, onVesselSelected);
  FleetMap.renderStorms(appState.storms);
  FleetMap.renderIncidents(appState.incidents);

  MetricsModule.updateObservabilityMetrics(appState.metrics, appState.stats);
}

function updateKpiHeader() {
  const stats = appState.stats;
  document.getElementById('kpi-total-vessels').innerText = stats.total || appState.vessels.length || 50;
  document.getElementById('kpi-critical-count').innerText = stats.critical || 0;
  document.getElementById('kpi-high-count').innerText = stats.high || 0;
  document.getElementById('kpi-watch-count').innerText = stats.watch || 0;
  document.getElementById('kpi-normal-count').innerText = stats.normal || 0;

  document.getElementById('pill-crit-count').innerText = stats.critical || 0;
  document.getElementById('pill-high-count').innerText = stats.high || 0;
  document.getElementById('pill-watch-count').innerText = stats.watch || 0;
}

function renderRiskQueue() {
  const container = document.getElementById('risk-cards-list');
  if (!container) return;

  const query = appState.searchQuery.toLowerCase();
  const activeTier = appState.activeFilterTier;

  // Filter vessels
  const filtered = appState.vessels.filter(v => {
    const assessment = appState.assessments[v.vessel_id] || {};
    const tier = assessment.risk_tier || v.risk_tier || 'NORMAL';

    if (activeTier !== 'ALL' && tier !== activeTier) return false;

    if (query) {
      const matchName = v.name.toLowerCase().includes(query);
      const matchVoy = (v.voyage_id || '').toLowerCase().includes(query);
      const matchDest = (v.destination || '').toLowerCase().includes(query);
      const matchDep = (v.departure_port || '').toLowerCase().includes(query);
      if (!matchName && !matchVoy && !matchDest && !matchDep) return false;
    }

    return true;
  });

  // Sort: CRITICAL, HIGH, WATCH, NORMAL
  const weights = { CRITICAL: 4, HIGH: 3, WATCH: 2, NORMAL: 1 };
  filtered.sort((a, b) => {
    const tierA = (appState.assessments[a.vessel_id] || {}).risk_tier || a.risk_tier || 'NORMAL';
    const tierB = (appState.assessments[b.vessel_id] || {}).risk_tier || b.risk_tier || 'NORMAL';
    return (weights[tierB] || 0) - (weights[tierA] || 0);
  });

  document.getElementById('queue-total-count').innerText = `${filtered.length} Vessels`;

  container.innerHTML = '';
  if (filtered.length === 0) {
    container.innerHTML = `<div class="text-slate-500 text-xs text-center py-8">No vessels matching current filter.</div>`;
    return;
  }

  filtered.forEach(vessel => {
    const assessment = appState.assessments[vessel.vessel_id] || {};
    const tier = assessment.risk_tier || vessel.risk_tier || 'NORMAL';
    const score = assessment.risk_score || vessel.risk_score || 5.0;

    let tierBadgeClass = 'bg-emerald-950/60 border-emerald-700/60 text-emerald-400';
    let tierIcon = '🟢';
    let cardBorder = 'border-slate-800';

    if (tier === 'CRITICAL') {
      tierBadgeClass = 'bg-rose-950/90 border-rose-600 text-rose-400 font-bold';
      tierIcon = '🔴';
      cardBorder = 'border-rose-700/80 shadow-lg shadow-rose-950/40';
    } else if (tier === 'HIGH') {
      tierBadgeClass = 'bg-amber-950/80 border-amber-600 text-amber-400 font-bold';
      tierIcon = '🟠';
      cardBorder = 'border-amber-700/60';
    } else if (tier === 'WATCH') {
      tierBadgeClass = 'bg-yellow-950/70 border-yellow-600 text-yellow-400';
      tierIcon = '🟡';
      cardBorder = 'border-yellow-800/40';
    }

    const card = document.createElement('div');
    card.className = `bg-slate-900/90 border ${cardBorder} rounded-xl p-3.5 space-y-2 hover:bg-slate-850 cursor-pointer transition`;

    const primaryFactor = (assessment.primary_factors && assessment.primary_factors.length > 0)
      ? assessment.primary_factors[0]
      : 'Nominal voyage progress on clear route';

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-bold text-white font-mono">${vessel.name}</span>
          <span class="text-[10px] font-mono text-slate-400">(${vessel.vessel_id})</span>
        </div>
        <span class="px-2 py-0.5 text-[10px] rounded border ${tierBadgeClass}">${tierIcon} ${tier}</span>
      </div>

      <div class="flex items-center justify-between text-[11px] font-mono text-slate-300">
        <div>${vessel.departure_port || 'Origin'} → <strong class="text-cyan-300">${vessel.destination}</strong></div>
        <div class="text-slate-400 font-semibold">${vessel.speed_knots} kts</div>
      </div>

      <div class="bg-slate-950/80 border border-slate-800 rounded p-2 text-[11px] text-slate-300 leading-snug">
        <div class="text-slate-400 font-sans line-clamp-2">${primaryFactor}</div>
      </div>

      <div class="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[11px]">
        <div class="text-slate-400 font-mono">Score: <strong class="text-white">${score}/100</strong></div>
        ${(tier === 'CRITICAL' || tier === 'HIGH') ? `
          <button onclick="event.stopPropagation(); triggerInvestigation('${vessel.vessel_id}')" class="px-2.5 py-1 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded shadow transition flex items-center">
            <i data-lucide="bot" class="w-3 h-3 mr-1"></i> View Investigation
          </button>
        ` : `
          <button onclick="event.stopPropagation(); triggerInvestigation('${vessel.vessel_id}')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition flex items-center">
            <i data-lucide="search" class="w-3 h-3 mr-1"></i> Details
          </button>
        `}
      </div>
    `;

    card.addEventListener('click', () => {
      onVesselSelected(vessel, assessment);
    });

    container.appendChild(card);
  });

  if (window.lucide) window.lucide.createIcons();
}

// --- Vessel Selection Handler ---

async function onVesselSelected(vessel, assessment) {
  appState.selectedVessel = vessel;

  // Center map on vessel
  FleetMap.focusMapOn(vessel.lat, vessel.lon, 6);

  // Fetch voyage details & trajectory to draw route
  const voyId = vessel.voyage_id || vessel.vessel_id.replace('VSL-', '');
  try {
    const res = await fetch(`/api/voyage/${voyId}`);
    if (res.ok) {
      const voyData = await res.json();
      FleetMap.drawVesselRoute(voyData.voyage, voyData.trajectory, voyData.exposure);
    }
  } catch (e) {
    console.error('Failed to load voyage route:', e);
  }

  // Show Floating Quick Card
  const quickCard = document.getElementById('vessel-quick-card');
  if (quickCard) {
    document.getElementById('quick-vessel-name').innerText = vessel.name;
    document.getElementById('quick-voyage-id').innerText = voyId;
    document.getElementById('quick-speed-heading').innerText = `${vessel.speed_knots} kts / ${vessel.heading_deg}°`;
    document.getElementById('quick-dep-port').innerText = vessel.departure_port || 'Departure';
    document.getElementById('quick-dest-port').innerText = vessel.destination;

    const tier = assessment?.risk_tier || vessel.risk_tier || 'NORMAL';
    const riskBadge = document.getElementById('quick-risk-tier');
    riskBadge.innerText = tier;
    riskBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded ${
      tier === 'CRITICAL' ? 'bg-rose-950 border border-rose-600 text-rose-400' : (tier === 'HIGH' ? 'bg-amber-950 border border-amber-600 text-amber-400' : 'bg-emerald-950 border border-emerald-600 text-emerald-400')
    }`;

    const desc = (assessment?.primary_factors && assessment.primary_factors.length > 0)
      ? assessment.primary_factors[0]
      : 'Nominal conditions along corridor.';
    document.getElementById('quick-exposure-desc').innerText = desc;

    document.getElementById('btn-quick-investigate').onclick = () => {
      triggerInvestigation(vessel.vessel_id);
    };

    quickCard.classList.remove('hidden');
    if (window.lucide) window.lucide.createIcons();
  }
}

// --- Trigger AI Investigation ---

async function triggerInvestigation(vesselId) {
  try {
    const res = await fetch(`/api/investigate/${vesselId}`);
    if (!res.ok) {
      alert('Could not fetch investigation for vessel.');
      return;
    }
    const briefData = await res.json();
    AgentView.openInvestigationModal(vesselId, briefData);

    // Also populate Action Center
    if (briefData.actions && briefData.actions.length > 0) {
      ActionsModule.renderActionCards(briefData.actions);
    }
  } catch (e) {
    console.error('Failed to trigger investigation:', e);
  }
}
window.triggerInvestigation = triggerInvestigation;

// --- Filters and Search ---

function setupFiltersAndSearch() {
  const searchInput = document.getElementById('risk-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      appState.searchQuery = e.target.value;
      renderRiskQueue();
    });
  }

  const pills = document.querySelectorAll('.filter-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => {
        p.classList.remove('active', 'bg-cyan-600', 'text-white');
        p.classList.add('bg-slate-800');
      });
      pill.classList.add('active', 'bg-cyan-600', 'text-white');
      pill.classList.remove('bg-slate-800');

      appState.activeFilterTier = pill.dataset.tier;
      renderRiskQueue();
    });
  });
}

// --- Scenario Triggers ---

function setupScenarioTriggers() {
  const btnTyphoon = document.getElementById('btn-scenario-typhoon');
  const btnRedSea = document.getElementById('btn-scenario-redsea');
  const btnReset = document.getElementById('btn-scenario-reset');

  btnTyphoon.addEventListener('click', async () => {
    btnTyphoon.disabled = true;
    try {
      await fetch('/api/scenarios/trigger/typhoon_malakas', { method: 'POST' });
      await fetchInitialData();
      // Auto select Ocean Star
      const oceanStar = appState.vessels.find(v => v.name.includes('Ocean Star'));
      if (oceanStar) {
        onVesselSelected(oceanStar, appState.assessments[oceanStar.vessel_id]);
      }
    } finally {
      btnTyphoon.disabled = false;
    }
  });

  btnRedSea.addEventListener('click', async () => {
    btnRedSea.disabled = true;
    try {
      await fetch('/api/scenarios/trigger/red_sea_security', { method: 'POST' });
      await fetchInitialData();
    } finally {
      btnRedSea.disabled = false;
    }
  });

  btnReset.addEventListener('click', async () => {
    btnReset.disabled = true;
    try {
      await fetch('/api/scenarios/trigger/reset', { method: 'POST' });
      await fetchInitialData();
      const quickCard = document.getElementById('vessel-quick-card');
      if (quickCard) quickCard.classList.add('hidden');
    } finally {
      btnReset.disabled = false;
    }
  });
}

// --- Modal Events ---

function setupModalEvents() {
  const btnClose = document.getElementById('btn-modal-close');
  const btnCloseSec = document.getElementById('btn-modal-close-secondary');
  const btnOpenActions = document.getElementById('btn-modal-open-actions');
  const btnQuickClose = document.getElementById('btn-quick-close');

  if (btnClose) btnClose.addEventListener('click', AgentView.closeInvestigationModal);
  if (btnCloseSec) btnCloseSec.addEventListener('click', AgentView.closeInvestigationModal);
  if (btnQuickClose) btnQuickClose.addEventListener('click', () => {
    document.getElementById('vessel-quick-card').classList.add('hidden');
  });

  if (btnOpenActions) {
    btnOpenActions.addEventListener('click', () => {
      AgentView.closeInvestigationModal();
      document.getElementById('tab-actions').click();
    });
  }

  const toggleTrace = document.getElementById('toggle-reasoning-trace');
  if (toggleTrace) {
    toggleTrace.addEventListener('click', () => {
      const trace = document.getElementById('modal-reasoning-trace');
      trace.classList.toggle('hidden');
    });
  }
}

/**
 * Agent View Module: Renders AI Investigation Briefs, Evidence, and Reasoning Traces
 */

function openInvestigationModal(vesselId, briefData) {
  const modal = document.getElementById('investigation-modal');
  if (!modal || !briefData || !briefData.brief) return;

  const brief = briefData.brief;

  // Set Vessel Title & Badge
  document.getElementById('modal-vessel-title').innerText = `Investigation: ${brief.vessel_name} (Voyage ${brief.voyage_id})`;
  
  const riskBadge = document.getElementById('modal-risk-badge');
  riskBadge.innerText = `${brief.risk_level === 'CRITICAL' ? '🔴' : (brief.risk_level === 'HIGH' ? '🟠' : '🟡')} ${brief.risk_level}`;
  riskBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded ${
    brief.risk_level === 'CRITICAL'
      ? 'bg-rose-950 border border-rose-600 text-rose-400'
      : (brief.risk_level === 'HIGH' ? 'bg-amber-950 border border-amber-600 text-amber-400' : 'bg-yellow-950 border border-yellow-600 text-yellow-400')
  }`;

  // Headline & Why Explanation
  document.getElementById('modal-headline').innerText = brief.summary_headline || 'Deterministic Risk Alert';
  document.getElementById('modal-why-text').innerText = brief.why_explanation || '';

  // Metrics Row
  document.getElementById('modal-exposure-window').innerText = brief.expected_exposure_window || 'Imminent';
  document.getElementById('modal-max-weather').innerText = brief.weather_summary || 'Severe Sea-State';
  document.getElementById('modal-financial-exposure').innerText = `$${(brief.total_estimated_financial_exposure_usd || 0).toLocaleString()}`;
  document.getElementById('modal-confidence-score').innerText = `${brief.confidence_score_pct || 78}%`;

  // Cross-Departmental Impacts
  const impactsContainer = document.getElementById('modal-impacts-list');
  impactsContainer.innerHTML = '';

  if (brief.operational_impacts && brief.operational_impacts.length > 0) {
    brief.operational_impacts.forEach(imp => {
      const card = document.createElement('div');
      card.className = 'bg-slate-900/80 border border-slate-800 rounded-xl p-3 space-y-1';
      
      let icon = 'alert-triangle';
      let tagColor = 'text-amber-400 bg-amber-950/60 border-amber-600/40';
      if (imp.area.includes('Customer')) {
        icon = 'package';
        tagColor = 'text-rose-400 bg-rose-950/60 border-rose-600/40';
      } else if (imp.area.includes('Crew')) {
        icon = 'users';
        tagColor = 'text-indigo-400 bg-indigo-950/60 border-indigo-600/40';
      } else if (imp.area.includes('Drydock') || imp.area.includes('Maintenance')) {
        icon = 'wrench';
        tagColor = 'text-cyan-400 bg-cyan-950/60 border-cyan-600/40';
      } else if (imp.area.includes('Port')) {
        icon = 'anchor';
        tagColor = 'text-yellow-400 bg-yellow-950/60 border-yellow-600/40';
      }

      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <i data-lucide="${icon}" class="w-4 h-4 text-cyan-400"></i>
            <span class="font-bold text-slate-200">${imp.area}</span>
          </div>
          <div class="flex items-center space-x-2">
            ${imp.financial_exposure_usd > 0 ? `<span class="font-mono font-bold text-amber-400">+$${imp.financial_exposure_usd.toLocaleString()}</span>` : ''}
            <span class="px-2 py-0.5 text-[10px] font-bold rounded border ${tagColor}">${imp.severity}</span>
          </div>
        </div>
        <div class="text-slate-300 text-xs leading-relaxed mt-1">${imp.details}</div>
      `;
      impactsContainer.appendChild(card);
    });
  }

  // Agent Reasoning Trace
  const traceContainer = document.getElementById('modal-reasoning-trace');
  traceContainer.innerHTML = '';
  if (brief.reasoning_trace && brief.reasoning_trace.length > 0) {
    brief.reasoning_trace.forEach(step => {
      const stepDiv = document.createElement('div');
      stepDiv.className = 'py-1 border-b border-slate-900 last:border-0 flex items-start space-x-2';
      
      let stepBadge = 'text-cyan-400';
      if (step.includes('Step 1')) stepBadge = 'text-rose-400';
      if (step.includes('Step 4') || step.includes('Customer')) stepBadge = 'text-amber-400';
      if (step.includes('Step 8') || step.includes('Synthesis')) stepBadge = 'text-emerald-400 font-bold';

      stepDiv.innerHTML = `
        <span class="text-slate-500 select-none">›</span>
        <span class="${stepBadge} leading-tight">${step}</span>
      `;
      traceContainer.appendChild(stepDiv);
    });
  }

  // Re-render icons inside modal
  if (window.lucide) {
    window.lucide.createIcons();
  }

  modal.classList.remove('hidden');
}

function closeInvestigationModal() {
  const modal = document.getElementById('investigation-modal');
  if (modal) modal.classList.add('hidden');
}

window.AgentView = {
  openInvestigationModal,
  closeInvestigationModal,
};

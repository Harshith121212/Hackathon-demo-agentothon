/**
 * Human-in-the-Loop Action Center Module: Approve, Edit, Reject Draft Communications
 */

let activeDraftActions = [];

async function fetchAndRenderActions() {
  const container = document.getElementById('action-cards-container');
  if (!container) return;

  // We can fetch from all active vessels or query audit log
  try {
    const res = await fetch('/api/actions/audit-log');
    const auditData = await res.json();
    renderAuditLog(auditData.audit_log || []);
  } catch (e) {
    console.error('Failed to load audit log:', e);
  }
}

function renderActionCards(actionsList) {
  const container = document.getElementById('action-cards-container');
  if (!container) return;

  activeDraftActions = actionsList;
  container.innerHTML = '';

  const pendingBadge = document.getElementById('pending-actions-badge');
  const pendingCount = actionsList.filter(a => a.status === 'PENDING_APPROVAL').length;
  
  if (pendingBadge) {
    if (pendingCount > 0) {
      pendingBadge.innerText = pendingCount;
      pendingBadge.classList.remove('hidden');
    } else {
      pendingBadge.classList.add('hidden');
    }
  }

  if (!actionsList || actionsList.length === 0) {
    container.innerHTML = `
      <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400 space-y-2">
        <i data-lucide="inbox" class="w-8 h-8 mx-auto text-slate-600"></i>
        <div class="text-sm font-semibold">No Pending Draft Actions</div>
        <p class="text-xs text-slate-500">When an AI investigation identifies critical operational exposures, draft communications will be generated here for your authorization.</p>
      </div>
    `;
    if (window.lucide) window.lucide.createIcons();
    return;
  }

  actionsList.forEach(action => {
    const card = document.createElement('div');
    card.id = `action-card-${action.action_id}`;
    card.className = 'bg-[#0f172a] border border-slate-800 rounded-xl p-5 shadow-xl space-y-4';

    const isPending = action.status === 'PENDING_APPROVAL';
    const isApproved = action.status === 'APPROVED' || action.status === 'EDITED';
    const isRejected = action.status === 'REJECTED';

    let statusBadge = `<span class="px-2.5 py-1 text-[11px] font-mono font-bold rounded bg-amber-950/80 border border-amber-500 text-amber-300">⏳ PENDING OPERATOR APPROVAL</span>`;
    if (isApproved) {
      statusBadge = `<span class="px-2.5 py-1 text-[11px] font-mono font-bold rounded bg-emerald-950/80 border border-emerald-500 text-emerald-300">✅ APPROVED & DISPATCHED</span>`;
    } else if (isRejected) {
      statusBadge = `<span class="px-2.5 py-1 text-[11px] font-mono font-bold rounded bg-rose-950/80 border border-rose-500 text-rose-300">❌ REJECTED</span>`;
    }

    card.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded-lg bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center">
            <i data-lucide="${action.recipient_type.includes('Charterer') ? 'mail' : 'radio'}" class="w-4 h-4 text-cyan-400"></i>
          </div>
          <div>
            <div class="text-sm font-bold text-white font-mono">${action.recipient_type}: ${action.recipient_name}</div>
            <div class="text-xs text-slate-400 font-mono">To: ${action.recipient_email} • Voyage ${action.voyage_id}</div>
          </div>
        </div>
        ${statusBadge}
      </div>

      <div class="space-y-1">
        <div class="text-xs font-mono text-slate-400 font-semibold">Subject:</div>
        <div class="text-xs font-bold text-white bg-slate-900/80 px-3 py-1.5 rounded border border-slate-800">${action.subject}</div>
      </div>

      <div class="space-y-1">
        <div class="flex items-center justify-between text-xs font-mono text-slate-400">
          <span class="font-semibold">AI Generated Message Content:</span>
          <span class="text-[11px] text-indigo-400">Rationale: ${action.rationale}</span>
        </div>
        <textarea id="textarea-${action.action_id}" ${!isPending ? 'readonly' : ''} class="w-full h-44 bg-slate-950/90 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 leading-relaxed focus:outline-none focus:border-cyan-500 custom-scrollbar ${!isPending ? 'opacity-80 cursor-default' : ''}">${action.edited_content || action.draft_content}</textarea>
      </div>

      ${isPending ? `
        <div class="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <div class="text-xs text-slate-500 italic">
            * Human operator review required. Messages are never sent autonomously.
          </div>
          <div class="flex space-x-3">
            <button onclick="handleRejectAction('${action.action_id}')" class="px-3.5 py-1.5 bg-rose-950/70 hover:bg-rose-900 border border-rose-600/60 text-rose-300 hover:text-white rounded-lg text-xs font-semibold transition flex items-center">
              <i data-lucide="x" class="w-3.5 h-3.5 mr-1.5"></i> Reject
            </button>
            <button onclick="handleEditAction('${action.action_id}')" class="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 rounded-lg text-xs font-semibold transition flex items-center">
              <i data-lucide="edit-3" class="w-3.5 h-3.5 mr-1.5"></i> Save Edits
            </button>
            <button onclick="handleApproveAction('${action.action_id}')" class="px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-lg text-xs shadow-lg transition flex items-center">
              <i data-lucide="send" class="w-3.5 h-3.5 mr-1.5"></i> Authorize & Dispatch
            </button>
          </div>
        </div>
      ` : `
        <div class="pt-2 border-t border-slate-800/80 text-xs font-mono text-slate-400 flex items-center justify-between">
          <span>Processed by: <strong class="text-white">${action.approved_by || 'Chief Fleet Controller'}</strong></span>
          <span>Status: <strong class="${isApproved ? 'text-emerald-400' : 'text-rose-400'}">${action.status}</strong></span>
        </div>
      `}
    `;

    container.appendChild(card);
  });

  if (window.lucide) window.lucide.createIcons();
}

function renderAuditLog(logItems) {
  const table = document.getElementById('action-audit-table');
  if (!table) return;

  if (!logItems || logItems.length === 0) {
    table.innerHTML = `<div class="text-slate-500 py-3 text-center">No actions logged yet.</div>`;
    return;
  }

  table.innerHTML = logItems.map(item => `
    <div class="py-2.5 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="px-2 py-0.5 text-[10px] font-bold rounded ${item.status.includes('APPROVED') ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}">
          ${item.status}
        </span>
        <span class="text-slate-300 font-semibold">${item.recipient || item.vessel_id}</span>
        <span class="text-slate-500 truncate max-w-md">${item.subject || item.reason || ''}</span>
      </div>
      <div class="text-right text-slate-500 text-[10px]">
        <div>${item.approved_by}</div>
        <div>${item.timestamp ? item.timestamp.split('T')[1].split('.')[0] + ' UTC' : ''}</div>
      </div>
    </div>
  `).join('');
}

async function handleApproveAction(actionId) {
  try {
    const res = await fetch(`/api/actions/${actionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_name: 'Chief Fleet Controller' }),
    });
    const data = await res.json();
    if (data.action) {
      updateLocalAction(data.action);
    }
  } catch (e) {
    console.error('Failed to approve action:', e);
  }
}

async function handleEditAction(actionId) {
  const textarea = document.getElementById(`textarea-${actionId}`);
  if (!textarea) return;

  const newContent = textarea.value;
  try {
    const res = await fetch(`/api/actions/${actionId}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edited_content: newContent, operator_name: 'Chief Fleet Controller' }),
    });
    const data = await res.json();
    if (data.action) {
      updateLocalAction(data.action);
    }
  } catch (e) {
    console.error('Failed to edit action:', e);
  }
}

async function handleRejectAction(actionId) {
  try {
    const res = await fetch(`/api/actions/${actionId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_name: 'Chief Fleet Controller', reason: 'Operator identified alternative mitigation' }),
    });
    const data = await res.json();
    if (data.action) {
      updateLocalAction(data.action);
    }
  } catch (e) {
    console.error('Failed to reject action:', e);
  }
}

function updateLocalAction(updatedAction) {
  const idx = activeDraftActions.findIndex(a => a.action_id === updatedAction.action_id);
  if (idx >= 0) {
    activeDraftActions[idx] = updatedAction;
  } else {
    activeDraftActions.push(updatedAction);
  }
  renderActionCards(activeDraftActions);
  fetchAndRenderActions();
}

window.ActionsModule = {
  renderActionCards,
  renderAuditLog,
  fetchAndRenderActions,
  updateLocalAction,
};

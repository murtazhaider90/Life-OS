function localDateISO(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function mondayISO(d = new Date()) {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - day);
  return localDateISO(x);
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function isoFromLocal(value) {
  return value ? new Date(value).toISOString() : null;
}

function toast(message) {
  const el = document.querySelector('#toast');
  el.textContent = message;
  el.hidden = false;
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  let body = null;
  try { body = await response.json(); } catch (_) {}
  if (!response.ok) {
    throw new Error(body?.detail || `HTTP ${response.status}`);
  }
  return body;
}

async function load() {
  const today = localDateISO();
  const weekStart = mondayISO();

  const [health, tasks, events, briefing, context, focusStatus] = await Promise.all([
    requestJson('/health').catch(() => null),
    requestJson('/api/tasks').catch(() => []),
    requestJson('/api/calendar').catch(() => []),
    requestJson(`/api/briefing/morning?brief_date=${today}`).catch(() => null),
    requestJson('/api/context/summary').catch(() => null),
    requestJson('/api/focus/status').catch(() => null),
  ]);

  document.querySelector('#system-status').textContent = health ? `v${health.version} · local` : 'Server issue';

  document.querySelector('#tasks').innerHTML = tasks.length
    ? tasks.slice(0, 10).map(t => `
      <div class="item">
        <strong>${escapeHtml(t.title)}</strong> · ${t.duration_minutes}m
        <br><small>${escapeHtml(t.module || 'General')} ${t.topic ? '· ' + escapeHtml(t.topic) : ''}</small>
        ${t.completed ? '<br><small>Completed</small>' : `<br><button onclick="completeTask(${t.id})">Mark complete</button>`}
      </div>`).join('')
    : '<p class="muted">No tasks yet.</p>';

  document.querySelector('#calendar').innerHTML = events.length
    ? events.slice(0, 10).map(e => `<div class="item"><strong>${escapeHtml(e.title)}</strong><br><small>${new Date(e.starts_at).toLocaleString()} → ${new Date(e.ends_at).toLocaleTimeString()}</small></div>`).join('')
    : '<p class="muted">No events yet.</p>';

  if (briefing?.next_action) {
    const a = briefing.next_action;
    document.querySelector('#next-action').innerHTML = `
      <div class="metric">${escapeHtml(a.title)}</div>
      <p>${escapeHtml(a.instruction || '')}</p>
      <p><strong>Start with ${a.suggested_initial_minutes || a.duration_minutes} minutes.</strong></p>
      <small>${escapeHtml(a.context_adjustment || a.why || '')}</small>
    `;
  } else {
    document.querySelector('#next-action').innerHTML = '<p>No pending academic action found.</p>';
  }

  if (context) {
    const sleepText = context.sleep?.duration_minutes
      ? `${(context.sleep.duration_minutes / 60).toFixed(1)}h recorded sleep`
      : 'no recent sleep record';
    document.querySelector('#context-summary').innerHTML = `
      <div class="metric">${escapeHtml(context.planning_load.replaceAll('_', ' '))}</div>
      <p>Suggested block: <strong>${context.recommended_block_minutes} min</strong> · gap: ${context.recommended_gap_minutes} min</p>
      <small>${escapeHtml(sleepText)}${context.reasons.length ? ' · ' + escapeHtml(context.reasons.join(' · ')) : ''}</small>
    `;
  }

  try {
    const plan = await requestJson(`/api/plans/weekly/active?week_start=${weekStart}`);
    document.querySelector('#week-summary').innerHTML = `
      <div class="metric">${plan.scheduled_minutes}m planned</div>
      <p>Version ${plan.version} · ${plan.blocks.length} blocks</p>
      <small>${plan.capacity_shortfall_minutes ? plan.capacity_shortfall_minutes + 'm does not fit in current capacity.' : 'All currently required minutes fit.'}</small>
    `;
  } catch (_) {
    document.querySelector('#week-summary').innerHTML = '<p class="muted">No active plan for this week yet.</p>';
  }

  renderFocus(focusStatus);
}

function renderFocus(status) {
  const statusEl = document.querySelector('#focus-status');
  const domainsEl = document.querySelector('#focus-domains');
  const apply = document.querySelector('#focus-apply');
  const release = document.querySelector('#focus-release');
  if (!status) {
    statusEl.textContent = 'Could not load focus status.';
    return;
  }
  statusEl.innerHTML = status.adguard_configured
    ? `<strong>AdGuard configured</strong> · ${status.active_interventions.length ? 'focus mode active' : 'focus mode inactive'}`
    : '<strong>AdGuard not configured</strong><br><small>Add LIFE_OS_ADGUARD_* settings to .env when you are ready.</small>';
  domainsEl.textContent = status.enabled_domains.length ? `Domains: ${status.enabled_domains.join(', ')}` : 'No focus domains configured.';
  apply.disabled = !status.adguard_configured || status.enabled_domains.length === 0;
  release.disabled = !status.adguard_configured;
}

async function completeTask(id) {
  try {
    await requestJson(`/api/tasks/${id}/complete`, {method: 'POST'});
    toast('Task completed.');
    await load();
  } catch (err) { toast(err.message); }
}
window.completeTask = completeTask;

document.querySelector('#task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const payload = {
    title: f.get('title'),
    module: f.get('module') || null,
    topic: f.get('topic') || null,
    objective: null,
    expected_output: null,
    source_material: f.get('source_material') || null,
    duration_minutes: Number(f.get('duration')),
    difficulty: Number(f.get('difficulty')),
    priority: Number(f.get('priority')),
    deadline: isoFromLocal(f.get('deadline')),
  };
  try {
    await requestJson('/api/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    event.target.reset();
    toast('Task added.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#calendar-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const payload = {
    title: f.get('title'),
    starts_at: isoFromLocal(f.get('starts_at')),
    ends_at: isoFromLocal(f.get('ends_at')),
    event_type: f.get('event_type') || 'fixed',
    source: 'manual_input',
    source_ref: null,
  };
  try {
    await requestJson('/api/calendar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    event.target.reset();
    toast('Commitment added.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#state-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const energy = f.get('energy');
  const focus = f.get('focus');
  if (!energy && !focus) return toast('Enter energy or focus.');
  const payload = {
    observed_at: new Date().toISOString(),
    energy: energy ? Number(energy) : null,
    focus: focus ? Number(focus) : null,
    difficulty: null,
    confused: null,
    study_session_id: null,
  };
  try {
    await requestJson('/api/state-inputs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    toast('Check-in saved.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#sleep-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const q = f.get('quality');
  const payload = {
    sleep_start: isoFromLocal(f.get('sleep_start')),
    sleep_end: isoFromLocal(f.get('sleep_end')),
    quality: q ? Number(q) : null,
    source: 'manual_input',
    source_ref: null,
  };
  try {
    await requestJson('/api/context/sleep', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    toast('Sleep record saved.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#training-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const intensity = f.get('intensity');
  const payload = {
    starts_at: isoFromLocal(f.get('starts_at')),
    duration_minutes: Number(f.get('duration')),
    intensity: intensity ? Number(intensity) : null,
    modality: f.get('modality') || null,
    source: 'manual_input',
    source_ref: null,
  };
  try {
    await requestJson('/api/context/training', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    event.target.reset();
    toast('Training context saved.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#meal-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  const size = f.get('size_rating');
  const payload = {
    consumed_at: isoFromLocal(f.get('consumed_at')),
    meal_type: f.get('meal_type'),
    size_rating: size ? Number(size) : null,
    notes: null,
    source: 'manual_input',
    source_ref: null,
  };
  try {
    await requestJson('/api/context/meals', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    event.target.reset();
    toast('Meal context saved.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#generate-week').addEventListener('click', async () => {
  const payload = {
    week_start: mondayISO(),
    day_start_hour: 8,
    day_end_hour: 22,
    max_block_minutes: 60,
    minimum_gap_minutes: 10,
  };
  try {
    const result = await requestJson('/api/plans/weekly', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    toast(`Weekly plan v${result.version} generated with ${result.blocks.length} blocks.`);
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#focus-domain-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const f = new FormData(event.target);
  try {
    await requestJson('/api/focus/domains', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({domain:f.get('domain'), reason:'User-selected focus domain'})
    });
    event.target.reset();
    toast('Focus domain added.');
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#focus-apply').addEventListener('click', async () => {
  if (!confirm('Apply your configured Life OS block rules in AdGuard Home for 45 minutes?')) return;
  try {
    const result = await requestJson('/api/focus/apply', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({duration_minutes:45, confirm:true})
    });
    toast(result.applied ? 'Focus mode applied.' : result.reason);
    await load();
  } catch (err) { toast(err.message); }
});

document.querySelector('#focus-release').addEventListener('click', async () => {
  if (!confirm('Release Life OS focus-domain blocks from AdGuard Home?')) return;
  try {
    await requestJson('/api/focus/release', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({confirm:true})
    });
    toast('Focus mode released.');
    await load();
  } catch (err) { toast(err.message); }
});

load();
setInterval(() => load().catch(() => {}), 60000);

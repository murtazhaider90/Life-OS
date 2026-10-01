function localDateISO(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

async function load() {
  const today = localDateISO();
  const [tasksRes, calendarRes, briefingRes] = await Promise.all([
    fetch('/api/tasks'),
    fetch('/api/calendar'),
    fetch(`/api/briefing/morning?brief_date=${today}`),
  ]);
  if (tasksRes.ok) {
    const tasks = await tasksRes.json();
    document.querySelector('#tasks').innerHTML = tasks.length ? tasks.slice(0, 8).map(t => `<p>${escapeHtml(t.title)} · ${t.duration_minutes}m</p>`).join('') : '<p>No tasks yet.</p>';
  }
  if (calendarRes.ok) {
    const events = await calendarRes.json();
    document.querySelector('#calendar').innerHTML = events.length ? events.slice(0, 8).map(e => `<p>${escapeHtml(e.title)} · ${new Date(e.starts_at).toLocaleString()}</p>`).join('') : '<p>No events yet.</p>';
  }
  if (briefingRes.ok) {
    const briefing = await briefingRes.json();
    const a = briefing.next_action;
    document.querySelector('#next-action').innerHTML = a
      ? `<strong>${escapeHtml(a.title)}</strong> · ${a.duration_minutes}m<br>${escapeHtml(a.instruction || '')}<br><small>${escapeHtml(a.why || '')}</small>`
      : 'No pending academic action was found.';
  }
}
function escapeHtml(s) { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
load();

async function load() {
  const [tasksRes, calendarRes] = await Promise.all([fetch('/api/tasks'), fetch('/api/calendar')]);
  if (!tasksRes.ok || !calendarRes.ok) return;
  const tasks = await tasksRes.json();
  const events = await calendarRes.json();
  document.querySelector('#tasks').innerHTML = tasks.length ? tasks.slice(0, 8).map(t => `<p>${escapeHtml(t.title)} · ${t.duration_minutes}m</p>`).join('') : '<p>No tasks yet.</p>';
  document.querySelector('#calendar').innerHTML = events.length ? events.slice(0, 8).map(e => `<p>${escapeHtml(e.title)} · ${new Date(e.starts_at).toLocaleString()}</p>`).join('') : '<p>No events yet.</p>';
}
function escapeHtml(s) { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
load();

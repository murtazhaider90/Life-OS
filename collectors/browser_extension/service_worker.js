const endpoint = 'http://127.0.0.1:8000/api/activity/events/bulk';
chrome.runtime.onInstalled.addListener(() => chrome.alarms.create('sample', { periodInMinutes: 1 }));
chrome.alarms.onAlarm.addListener(alarm => { if (alarm.name === 'sample') sample(); });

async function sample() {
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (!tab || !tab.url) return;
  let domain;
  try {
    const u = new URL(tab.url);
    if (!['http:', 'https:'].includes(u.protocol)) return;
    domain = u.hostname.toLowerCase();
  } catch { return; }
  const event = {
    kind: 'domain_sample',
    occurred_at: new Date().toISOString(),
    duration_seconds: 60,
    application: 'browser',
    domain,
    source: 'browser_extension',
    source_event_id: `browser:${Math.floor(Date.now()/60000)}:${domain}`
  };
  try {
    await fetch(endpoint, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({events:[event]}) });
  } catch (_) {}
}

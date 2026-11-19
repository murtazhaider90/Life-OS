(() => {
  const uploadForm = document.querySelector('#academic-upload-form');
  const askForm = document.querySelector('#academic-ask-form');
  const mode = document.querySelector('#academic-mode');
  const summary = document.querySelector('#academic-summary');
  const modulesEl = document.querySelector('#academic-modules');
  const assessmentsEl = document.querySelector('#academic-assessments');
  const output = document.querySelector('#academic-answer');

  function esc(value) {
    return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }

  function toastAcademic(message) {
    if (typeof window.toast === 'function') return window.toast(message);
    const el = document.querySelector('#toast');
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 3500);
  }

  async function api(url, options = {}) {
    const response = await fetch(url, options);
    let body = null;
    try { body = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(body?.detail || `HTTP ${response.status}`);
    return body;
  }

  function showOutput(title, text, extraHtml = '') {
    output.hidden = false;
    output.innerHTML = `<h3>${esc(title)}</h3><pre>${esc(text)}</pre>${extraHtml}`;
    output.scrollIntoView({behavior:'smooth', block:'nearest'});
  }

  async function refreshAcademic() {
    try {
      const [status, assessments] = await Promise.all([
        api('/api/academic/status'),
        api('/api/academic/assessments'),
      ]);
      mode.textContent = status.ai.configured
        ? `AI provider · ${status.ai.model || 'configured'}`
        : 'Local extractive mode';

      const modules = status.modules || [];
      summary.textContent = modules.length
        ? `${modules.length} module(s) · ${modules.reduce((a,m)=>a+m.documents,0)} documents indexed`
        : 'No course material indexed yet.';

      modulesEl.innerHTML = modules.length
        ? modules.map(m => `
          <div class="academic-item">
            <strong>${esc(m.module)}</strong>
            <small>${m.documents} docs · ${m.learning_objectives} objectives · ${m.assessments} assessments</small>
            ${m.weak_topics.length ? `<small>Weak: ${esc(m.weak_topics.join(', '))}</small>` : ''}
            ${m.retrieval_due_topics.length ? `<small>Retrieval due: ${esc(m.retrieval_due_topics.join(', '))}</small>` : ''}
          </div>
        `).join('')
        : '<span class="muted">None yet.</span>';

      assessmentsEl.innerHTML = assessments.length
        ? assessments.map(a => `
          <div class="academic-item">
            <strong>${esc(a.title)}</strong>
            <small>${esc(a.module)} · ${esc(a.assessment_type)}${a.weight_percent != null ? ' · ' + a.weight_percent + '%' : ''}</small>
            <small>${a.deadline ? 'Deadline: ' + new Date(a.deadline).toLocaleString() : 'Deadline not recorded'}</small>
            <div class="button-row">
              <button type="button" data-breakdown="${a.id}">Break down</button>
              <button type="button" class="secondary" data-breakdown-tasks="${a.id}">Create tasks</button>
            </div>
          </div>
        `).join('')
        : '<span class="muted">None yet.</span>';
    } catch (err) {
      summary.textContent = `Academic status unavailable: ${err.message}`;
    }
  }

  uploadForm.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(event.target);
    const files = form.getAll('files').filter(Boolean);
    if (!files.length) return;
    const payload = new FormData();
    payload.append('module', form.get('module'));
    if (form.get('academic_year')) payload.append('academic_year', form.get('academic_year'));
    for (const file of files) payload.append('files', file);
    const button = event.target.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Ingesting…';
    try {
      const result = await api('/api/course/documents/bulk', {method:'POST', body:payload});
      const ingested = result.files.filter(x => x.status === 'ingested').length;
      const duplicates = result.files.filter(x => x.status === 'duplicate').length;
      const failed = result.files.length - ingested - duplicates;
      toastAcademic(`Academic Brain: ${ingested} ingested, ${duplicates} duplicates, ${failed} failed.`);
      await refreshAcademic();
    } catch (err) {
      toastAcademic(err.message);
    } finally {
      button.disabled = false;
      button.textContent = 'Ingest selected files';
    }
  });

  askForm.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(event.target);
    const payload = {
      question: form.get('question'),
      module: form.get('module') || null,
      topic: null,
      limit: 8,
      allow_general_knowledge: form.get('allow_general') === 'on',
    };
    const button = event.target.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Thinking from sources…';
    try {
      const result = await api('/api/academic/ask', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload),
      });
      const sourceHtml = result.sources?.length
        ? '<div class="academic-sources"><strong>Retrieved sources</strong>' +
          result.sources.map(s => `<div><code>[${esc(s.source_id)}]</code> ${esc(s.title)}${s.page ? ', p.' + s.page : ''} · ${esc(s.document_type)}</div>`).join('') +
          '</div>'
        : '';
      const warning = result.conflict_warning
        ? `<div class="academic-warning"><strong>Conflict warning:</strong> ${esc(result.conflict_warning)}</div>`
        : '';
      showOutput('Academic answer', result.answer, warning + sourceHtml);
    } catch (err) {
      showOutput('Academic answer failed', err.message);
    } finally {
      button.disabled = false;
      button.textContent = 'Ask Academic Brain';
    }
  });

  async function runRevision(createTasks) {
    try {
      const result = await api('/api/academic/revision-plan', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({module:null, create_tasks:createTasks, horizon_days:14}),
      });
      const lines = result.recommendations.map(r =>
        `${r.module} — ${r.topic} [${r.status}]: ${r.activity} (${r.duration_minutes} min)`
      );
      if (createTasks) lines.push(`\nCreated ${result.created_task_ids.length} planner task(s).`);
      showOutput(createTasks ? 'Revision tasks created' : 'Revision plan', lines.join('\n') || 'No evidence-backed revision priorities yet.');
      if (window.load) await window.load();
    } catch (err) {
      showOutput('Revision plan failed', err.message);
    }
  }

  document.querySelector('#academic-revision').addEventListener('click', () => runRevision(false));
  document.querySelector('#academic-revision-tasks').addEventListener('click', () => runRevision(true));
  document.querySelector('#academic-refresh').addEventListener('click', refreshAcademic);

  assessmentsEl.addEventListener('click', async event => {
    const button = event.target.closest('button');
    if (!button) return;
    const assessmentId = button.dataset.breakdown || button.dataset.breakdownTasks;
    if (!assessmentId) return;
    const createTasks = Boolean(button.dataset.breakdownTasks);
    button.disabled = true;
    try {
      const result = await api(`/api/academic/assessments/${assessmentId}/breakdown`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({create_tasks:createTasks}),
      });
      const lines = result.actions.map(a => `${a.title} (${a.duration_minutes} min) → ${a.expected_output}`);
      if (createTasks) lines.push(`\nCreated ${result.created_task_ids.length} task(s).`);
      showOutput(`Breakdown — ${result.title}`, lines.join('\n'));
      if (window.load) await window.load();
    } catch (err) {
      showOutput('Assessment breakdown failed', err.message);
    } finally {
      button.disabled = false;
    }
  });

  refreshAcademic();
})();

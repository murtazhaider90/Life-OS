(() => {
  const panel = document.querySelector('#assistant-panel');
  const launcher = document.querySelector('#assistant-launcher');
  const closeBtn = document.querySelector('#assistant-close');
  const messages = document.querySelector('#assistant-messages');
  const question = document.querySelector('#assistant-question');
  const input = document.querySelector('#assistant-input');
  const send = document.querySelector('#assistant-send');
  const mic = document.querySelector('#assistant-mic');
  const speakToggle = document.querySelector('#assistant-speak');
  const mode = document.querySelector('#assistant-mode');
  const privacy = document.querySelector('#assistant-privacy');

  let recognition = null;
  let listening = false;
  let currentPrompt = null;

  function openPanel() {
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    setTimeout(() => input.focus(), 50);
  }

  function closePanel() {
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
  }

  function appendMessage(role, text) {
    const row = document.createElement('div');
    row.className = `assistant-message ${role}`;
    row.textContent = text;
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    if (role === 'assistant') speak(text);
  }

  function speak(text) {
    if (!speakToggle.checked || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-GB';
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
  }

  async function api(url, options = {}) {
    const res = await fetch(url, options);
    let body = null;
    try { body = await res.json(); } catch (_) {}
    if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
    return body;
  }

  async function refreshPrompts({autoOpen = false} = {}) {
    try {
      const status = await api('/api/assistant/status');
      currentPrompt = status.questions?.[0] || null;
      if (currentPrompt) {
        question.hidden = false;
        question.innerHTML = `<strong>${escapeHtml(currentPrompt.prompt)}</strong><br><small>${escapeHtml(currentPrompt.reason)}</small><br><small>Try: “${escapeHtml(currentPrompt.example)}”</small>`;
        const todayKey = `life-os-assistant-popped-${new Date().toISOString().slice(0,10)}`;
        if (autoOpen && !localStorage.getItem(todayKey)) {
          localStorage.setItem(todayKey, '1');
          setTimeout(() => {
            openPanel();
            appendMessage('assistant', currentPrompt.prompt);
          }, 800);
        }
      } else {
        question.hidden = true;
      }
    } catch (_) {}
  }

  async function submitMessage(text) {
    const value = (text || input.value).trim();
    if (!value) return;
    appendMessage('user', value);
    input.value = '';
    send.disabled = true;
    mic.disabled = true;
    try {
      const result = await api('/api/assistant/message', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({text: value}),
      });
      appendMessage('assistant', result.reply);
      await refreshPrompts();
      if (window.load) await window.load();
    } catch (err) {
      appendMessage('assistant', `I couldn't do that safely: ${err.message}`);
    } finally {
      send.disabled = false;
      mic.disabled = false;
    }
  }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }

  async function setupRecognition() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      mode.textContent = 'Text only in this browser';
      mic.disabled = true;
      privacy.textContent = 'Speech recognition is unavailable in this browser. Typed assistant input still works.';
      return null;
    }

    const r = new Recognition();
    r.lang = 'en-GB';
    r.continuous = false;
    r.interimResults = true;
    r.maxAlternatives = 1;

    let localReady = false;
    try {
      if ('processLocally' in r && typeof Recognition.available === 'function') {
        const availability = await Recognition.available({
          langs: ['en-GB'],
          processLocally: true,
          quality: 'dictation',
        });
        if (availability === 'available') {
          r.processLocally = true;
          localReady = true;
        }
      }
    } catch (_) {}

    if (localReady) {
      mode.textContent = 'Voice: on-device';
      privacy.textContent = 'Voice recognition is using the browser’s on-device mode. Raw assistant transcripts are not persisted by Life OS.';
    } else {
      mode.textContent = 'Voice: browser service';
      privacy.textContent = 'Your browser may send microphone audio to its speech-recognition service. Life OS does not store raw transcripts.';
    }

    r.onstart = () => {
      listening = true;
      mic.classList.add('listening');
      mic.textContent = '■';
      input.placeholder = 'Listening…';
    };

    r.onresult = (event) => {
      let transcript = '';
      let final = false;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
        if (event.results[i].isFinal) final = true;
      }
      input.value = transcript.trim();
      if (final && input.value) setTimeout(() => submitMessage(input.value), 120);
    };

    r.onerror = (event) => {
      appendMessage('assistant', `Voice input stopped: ${event.error}. You can still type.`);
    };

    r.onend = () => {
      listening = false;
      mic.classList.remove('listening');
      mic.textContent = '🎙';
      input.placeholder = 'Type or talk…';
    };

    return r;
  }

  async function startVoice() {
    if (!recognition) recognition = await setupRecognition();
    if (!recognition) return;

    const browserMayUseCloud = !('processLocally' in recognition) || recognition.processLocally !== true;
    if (browserMayUseCloud && localStorage.getItem('life-os-voice-cloud-consent') !== 'yes') {
      const ok = confirm('Your browser may send microphone audio to its speech-recognition service. Life OS itself will not store the raw transcript. Continue?');
      if (!ok) return;
      localStorage.setItem('life-os-voice-cloud-consent', 'yes');
    }

    try {
      if (listening) recognition.stop();
      else recognition.start();
    } catch (err) {
      appendMessage('assistant', `Could not start the microphone: ${err.message}`);
    }
  }

  launcher.addEventListener('click', openPanel);
  closeBtn.addEventListener('click', closePanel);
  send.addEventListener('click', () => submitMessage());
  mic.addEventListener('click', startVoice);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') submitMessage();
  });
  speakToggle.checked = localStorage.getItem('life-os-assistant-speak') === 'yes';
  speakToggle.addEventListener('change', () => {
    localStorage.setItem('life-os-assistant-speak', speakToggle.checked ? 'yes' : 'no');
    if (!speakToggle.checked && 'speechSynthesis' in window) window.speechSynthesis.cancel();
  });

  setupRecognition().then(r => { recognition = r; });
  refreshPrompts({autoOpen: true});
})();

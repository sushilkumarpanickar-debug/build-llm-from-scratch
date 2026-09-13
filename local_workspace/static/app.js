'use strict';

const $ = id => document.getElementById(id);
let state;
let health = {};
let integrationState = [];
let busy = false;
let recorder;
let audioChunks = [];

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function notice(message = '', error = false) {
  $('notice').textContent = message;
  $('notice').classList.toggle('error', error);
}

function currentScope() { return $('scope').value || 'Personal'; }

async function jsonRequest(path, data, method = 'POST') {
  const options = {method, headers: {'X-Workspace-Token': state.token}};
  if (data) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify({...data, scope: currentScope()});
  }
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw Error(result.error || result.detail || 'Request failed');
  return result;
}

async function load(conversationId) {
  const query = new URLSearchParams({scope: currentScope()});
  if (conversationId) query.set('conversation_id', conversationId);
  const response = await fetch('/api/state?' + query);
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Could not load the workspace');
  state = result;
  const scope = $('scope');
  scope.replaceChildren(...state.scopes.map(name => new Option(name, name, false, name === state.scope)));
  render();
}

function show(name, message = '', trigger = null) {
  document.querySelectorAll('.view').forEach(node => { node.hidden = node.id !== name; });
  document.querySelectorAll('.left-rail nav button').forEach(node => node.classList.remove('active'));
  const activeNav = trigger && trigger.closest('.left-rail nav') ? trigger : document.querySelector(`.left-rail nav button[data-view="${name}"]:not([data-message])`);
  if (activeNav) activeNav.classList.add('active');
  window.scrollTo({top: 0, behavior: 'smooth'});
  if (message) notice(message);
}

function render() {
  renderModels(); renderConversations(); renderMessages(); renderNotes();
  renderDocuments(); renderTasks(); renderSettings(); renderDashboard(); renderCapabilities();
  renderIntegrations();
}

function renderModels() {
  const current = state.settings.model;
  for (const id of ['model', 'settings-model']) {
    const select = $(id);
    select.replaceChildren();
    if (!state.models.length) select.append(new Option('No local chat model', ''));
    state.models.forEach(name => select.append(new Option(name, name, false, name === current)));
  }
}

function renderConversations() {
  const select = $('conversation');
  select.replaceChildren();
  state.conversations.forEach(item => select.append(new Option(item.title, item.id, false, state.conversation && item.id === state.conversation.id)));
}

function sourceChip(source) {
  const label = source.type === 'document' ? `${source.title} · ${source.location}` : `Memory ${source.id} · ${source.title}`;
  return el('span', label, 'source-chip');
}

function renderMessages() {
  const root = $('messages');
  root.replaceChildren();
  if (!state.messages.length) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('b', '◈'), el('h2', 'What shall we work on?'), el('p', 'Ask DAKSH, use the microphone, or teach it with your local documents. The active domain controls retrieval.'));
    root.append(empty);
    $('source-panel').replaceChildren(el('p', 'No sources retrieved yet.'));
    return;
  }
  let latestSources = [];
  for (const message of state.messages) {
    const card = el('article', undefined, 'message ' + message.role);
    card.append(el('strong', message.role === 'user' ? 'YOU' : 'DAKSH'), el('p', message.content));
    if (message.sources && message.sources.length) {
      const sourceRow = el('div', undefined, 'message-sources');
      message.sources.forEach(source => sourceRow.append(sourceChip(source)));
      card.append(sourceRow);
      if (message.role === 'assistant') latestSources = message.sources;
    }
    root.append(card);
  }
  root.scrollTop = root.scrollHeight;
  renderSourcePanel(latestSources);
}

function renderSourcePanel(sources) {
  const root = $('source-panel');
  root.replaceChildren();
  if (!sources.length) return root.append(el('p', 'No sources used in the latest response.'));
  sources.forEach(source => {
    const item = el('div', undefined, 'source-item');
    item.append(el('strong', source.title), el('span', source.type === 'document' ? source.location : `Memory ${source.id}`));
    root.append(item);
  });
}

function renderNotes() {
  const root = $('notes');
  const query = $('search').value.toLowerCase();
  const rows = state.notes.filter(note => (note.title + ' ' + note.content + ' ' + note.category).toLowerCase().includes(query));
  root.replaceChildren();
  if (!rows.length) root.append(el('p', query ? 'No matching memories.' : 'No memories stored in this domain.', 'muted'));
  rows.forEach(note => {
    const card = el('article', undefined, 'card');
    card.append(el('span', note.category.replaceAll('_', ' ').toUpperCase(), 'card-tag'), el('h3', note.title), el('p', note.content), el('small', `MEMORY ${note.id} · ${note.source} · ${new Date(note.created).toLocaleDateString()}`));
    root.append(card);
  });
}

function renderDocuments() {
  const root = $('documents-list');
  root.replaceChildren();
  if (!state.documents.length) root.append(el('p', 'No documents indexed in this domain.', 'muted'));
  state.documents.forEach(document => {
    const card = el('article', undefined, 'card document-card');
    const top = el('div', undefined, 'card-top');
    top.append(el('span', document.kind.toUpperCase(), 'card-tag'), el('span', document.status.toUpperCase(), 'status ' + document.status));
    const remove = el('button', 'REMOVE', 'text-button danger');
    remove.addEventListener('click', async () => {
      if (!confirm(`Remove ${document.filename} and its local index?`)) return;
      try { await jsonRequest(`/api/documents/${document.id}?scope=${encodeURIComponent(currentScope())}`, null, 'DELETE'); await load(); }
      catch (error) { notice(error.message, true); }
    });
    card.append(top, el('h3', document.filename), el('p', `${document.chunk_count} searchable chunks · added ${new Date(document.created).toLocaleString()}`), remove);
    root.append(card);
  });
}

function renderTasks() {
  const root = $('task-list');
  root.replaceChildren();
  if (!state.tasks.length) root.append(el('p', 'No missions are staged.', 'muted'));
  state.tasks.forEach(task => {
    const card = el('article', undefined, 'card');
    const select = document.createElement('select');
    ['planned', 'in_progress', 'completed'].forEach(status => select.append(new Option(status.replace('_', ' '), status, false, task.status === status)));
    select.addEventListener('change', async () => {
      try { await jsonRequest('/api/tasks/status', {id: task.id, status: select.value}); await load(); }
      catch (error) { notice(error.message, true); }
    });
    card.append(el('span', `MISSION ${task.id}`, 'card-tag'), el('h3', task.title), el('p', task.plan), select);
    root.append(card);
  });
}

function renderSettings() {
  $('stt-model').value = state.settings.stt_model || 'tiny';
  $('speech-enabled').checked = state.settings.speech_enabled === 'true';
  const embedding = $('embedding-model');
  embedding.replaceChildren();
  const name = health.embedding_model || state.settings.embedding_model || 'nomic-embed-text';
  embedding.append(new Option(name, name, true, true));
  $('note-category').replaceChildren(...state.memory_categories.map(category => new Option(category.replaceAll('_', ' '), category)));
}

function addFeed(icon, title, detail, status, warn = false) {
  const item = el('div', undefined, 'feed-item' + (warn ? ' warn' : ''));
  const copy = el('span'); copy.append(el('strong', title), el('small', detail));
  item.append(el('i', icon), copy, el('b', status)); $('intelligence-feed').append(item);
}

function addAgent(icon, title, detail, className = '') {
  const item = el('div', undefined, 'agent-card ' + className);
  const copy = el('span'); copy.append(el('strong', title), el('small', detail));
  item.append(el('i', icon), copy, el('b', className === 'offline' ? '○' : '●')); $('agent-grid').append(item);
}

function renderDashboard() {
  const readyDocs = state.documents.filter(item => item.status === 'ready');
  const openTasks = state.tasks.filter(item => item.status !== 'completed');
  const modelCount = state.models.length;
  const coreOnline = health.status === 'ready' || modelCount > 0;
  $('nav-task-count').textContent = openTasks.length;
  $('nav-chat-count').textContent = state.conversations.length;
  $('overview-core').textContent = coreOnline ? 'Active' : 'Limited';
  $('overview-memory').textContent = `${state.notes.length} stored`;
  $('overview-voice').textContent = health.transcription ? 'Ready' : 'Offline';
  $('overview-agents').textContent = `${openTasks.length} missions`;
  $('overview-models').textContent = `${modelCount} connected`;
  $('core-state').textContent = coreOnline ? 'ALL SYSTEMS OPERATIONAL' : 'LOCAL CORE LIMITED';
  $('voice-status-dot').textContent = health.transcription ? '●' : '○';
  $('voice-label').textContent = health.transcription ? 'Ready' : 'Unavailable';
  $('dock-status').textContent = health.transcription ? 'Tap to speak' : 'Voice offline';
  $('monitor-memory').textContent = state.notes.length;
  $('monitor-docs').textContent = readyDocs.length;
  $('memory-gauge').style.setProperty('--value', Math.min(100, 12 + state.notes.length * 7));
  $('docs-gauge').style.setProperty('--value', Math.min(100, 12 + readyDocs.length * 9));
  $('insight-memory').textContent = state.notes.length;
  $('insight-docs').textContent = readyDocs.length;
  $('insight-chat').textContent = state.conversations.length;

  $('intelligence-feed').replaceChildren();
  addFeed('◉', 'Local inference core', modelCount ? state.settings.model || state.models[0] : 'Start Ollama to connect', modelCount ? 'ONLINE' : 'OFFLINE', !modelCount);
  addFeed('▱', 'Knowledge index', `${readyDocs.length} files ready for retrieval`, readyDocs.length ? 'READY' : 'EMPTY', !readyDocs.length);
  addFeed('◇', 'Mission queue', `${openTasks.length} open · ${state.tasks.length} total`, openTasks.length ? 'ACTIVE' : 'CLEAR');
  addFeed('◖', 'Voice interface', health.transcription ? 'Faster-Whisper running locally' : 'Transcription dependency unavailable', health.transcription ? 'READY' : 'OFFLINE', !health.transcription);
  addFeed('✓', 'Privacy boundary', health.local_only ? 'Bound to this Mac only' : 'Review server binding', health.local_only ? 'LOCAL' : 'CHECK', !health.local_only);

  $('agent-grid').replaceChildren();
  addAgent('▱', 'Memory Agent', `${state.notes.length} records`, health.database ? '' : 'offline');
  addAgent('⌕', 'Retrieval Agent', `${readyDocs.length} indexed files`, health.embedding_model ? '' : 'offline');
  addAgent('◖', 'Voice Agent', health.transcription ? 'Ready' : 'Unavailable', health.transcription ? '' : 'offline');
  addAgent('◇', 'Mission Planner', `${openTasks.length} open`, modelCount ? 'standby' : 'offline');
  addAgent('◉', 'System Agent', health.database ? 'SQLite online' : 'Database offline', health.database ? '' : 'offline');
  addAgent('₹', 'Finance Agent', health.finance ? 'Read-only ready' : 'Unavailable', health.finance ? '' : 'offline');

  $('timeline').replaceChildren();
  const events = state.tasks.slice(0, 3).map(task => ({time: new Date(task.created).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}), title: task.title, status: task.status.replace('_', ' ')}));
  if (!events.length) events.push(
    {time: 'NOW', title: 'Local AI core ready', status: modelCount ? 'online' : 'limited'},
    {time: 'NOW', title: 'Knowledge index scanned', status: `${readyDocs.length} files`},
    {time: 'NEXT', title: 'Awaiting your directive', status: 'standby'}
  );
  events.forEach(event => {
    const row = el('div', undefined, 'timeline-row');
    row.append(el('time', event.time), el('span', event.title), el('b', event.status.toUpperCase())); $('timeline').append(row);
  });

  const services = [
    [state.settings.model || state.models[0] || 'Ollama', modelCount ? 'CHAT ONLINE' : 'CHAT OFFLINE', modelCount],
    [health.embedding_model || state.settings.embedding_model || 'Embeddings', health.embedding_model ? 'RAG ONLINE' : 'RAG OFFLINE', !!health.embedding_model],
    [`Whisper ${state.settings.stt_model || 'tiny'}`, health.transcription ? 'VOICE ONLINE' : 'VOICE OFFLINE', !!health.transcription],
    ['macOS Speech', health.speech ? 'OUTPUT READY' : 'OUTPUT OFFLINE', !!health.speech]
  ];
  $('llm-count').textContent = `${services.filter(item => item[2]).length} CONNECTED`;
  $('llm-grid').replaceChildren();
  services.forEach(([name, status, online]) => {
    const card = el('div', undefined, 'llm-card ' + (online ? 'online' : ''));
    const copy = el('span'); copy.append(el('strong', name), el('small', status));
    card.append(el('i', online ? '●' : '○'), copy); $('llm-grid').append(card);
  });
}

function renderCapabilities() {
  const root = $('capabilities'); root.replaceChildren();
  const entries = [
    ['Ollama local inference', health.models && health.models.length ? health.models.join(', ') : 'OFFLINE', !!(health.models && health.models.length)],
    ['Semantic document search', health.embedding_model || 'MODEL MISSING', !!health.embedding_model],
    ['Local voice input', health.transcription ? 'FASTER-WHISPER' : 'OFFLINE', !!health.transcription],
    ['macOS spoken replies', health.speech ? 'SAY READY' : 'OFFLINE', !!health.speech],
    ['Persistent workspace', health.database ? 'SQLITE READY' : 'OFFLINE', !!health.database],
    ['Deterministic finance skill', health.finance ? 'CSV / XLSX READY' : 'OFFLINE', !!health.finance],
    ['DAKSH Finance MCP', health.mcp_finance ? 'STDIO READY' : 'OFFLINE', !!health.mcp_finance],
    ['Network boundary', health.local_only ? '127.0.0.1 ONLY' : 'CHECK REQUIRED', !!health.local_only]
  ];
  entries.forEach(([name, status, live]) => {
    const item = el('div', undefined, 'capability ' + (live ? 'live' : 'planned'));
    item.append(el('strong', name), el('span', status)); root.append(item);
  });
}

function renderIntegrations() {
  const root = $('integrations');
  root.replaceChildren();
  integrationState.forEach(item => {
    const card = el('article', undefined, `connector ${item.decision}`);
    const top = el('div', undefined, 'connector-title');
    top.append(el('strong', item.name), el('b', item.decision.replace('_', ' ').toUpperCase()));
    card.append(top, el('p', item.description), el('small', `${item.access} · ${item.cost} · ${item.installed ? 'available on this Mac' : 'not active'}`));
    root.append(card);
  });
}

function renderFinance(result) {
  const root = $('finance-results');
  root.replaceChildren();
  root.append(el('h2', result.filename), el('p', result.method, 'muted'));
  result.sheets.forEach(sheet => {
    const section = el('section', undefined, 'finance-sheet');
    section.append(el('h3', sheet.name), el('small', `${sheet.rows.toLocaleString()} rows · ${sheet.columns} columns`));
    if (sheet.numeric_columns.length) {
      const table = document.createElement('table');
      const head = document.createElement('tr');
      ['Column', 'Role', 'Count', 'Sum', 'Average', 'Min', 'Max'].forEach(label => head.append(el('th', label)));
      table.append(head);
      sheet.numeric_columns.forEach(column => {
        const row = document.createElement('tr');
        [column.name, column.role, column.count, column.sum, column.average, column.minimum, column.maximum].forEach(value => row.append(el('td', typeof value === 'number' ? value.toLocaleString(undefined, {maximumFractionDigits: 2}) : value)));
        table.append(row);
      });
      section.append(table);
    }
    sheet.warnings.forEach(warning => section.append(el('p', warning, 'finance-warning')));
    root.append(section);
  });
}

async function scan() {
  try {
    const [healthResponse, integrationsResponse] = await Promise.all([fetch('/api/health'), fetch('/api/integrations')]);
    health = await healthResponse.json();
    integrationState = (await integrationsResponse.json()).integrations || [];
    renderSettings(); renderCapabilities(); renderDashboard(); renderIntegrations();
  } catch (error) { notice('System scan failed: ' + error.message, true); }
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = value; });
  document.body.classList.toggle('thinking', value);
  $('dock-status').textContent = value ? 'Processing locally' : (health.transcription ? 'Tap to speak' : 'Voice offline');
}

function setRecordingUi(recording) {
  for (const id of ['mic', 'side-mic', 'dock-mic', 'quick-voice']) $(id).classList.toggle('recording', recording);
  $('mic').textContent = recording ? '■ STOP' : '◉ MIC';
  $('voice-label').textContent = recording ? 'Listening' : (health.transcription ? 'Ready' : 'Unavailable');
  $('dock-status').textContent = recording ? 'Listening locally · tap to stop' : (health.transcription ? 'Tap to speak' : 'Voice offline');
}

async function beginRecording() {
  if (!navigator.mediaDevices || !window.MediaRecorder) throw Error('This browser does not support microphone recording.');
  const stream = await navigator.mediaDevices.getUserMedia({audio: true});
  audioChunks = []; recorder = new MediaRecorder(stream);
  recorder.addEventListener('dataavailable', event => { if (event.data.size) audioChunks.push(event.data); });
  recorder.addEventListener('stop', async () => {
    stream.getTracks().forEach(track => track.stop()); setRecordingUi(false);
    const blob = new Blob(audioChunks, {type: recorder.mimeType || 'audio/webm'});
    const form = new FormData(); form.append('scope', currentScope()); form.append('file', blob, 'voice.webm');
    try {
      notice('Transcribing on this Mac…');
      const response = await fetch('/api/voice/transcribe', {method: 'POST', headers: {'X-Workspace-Token': state.token}, body: form});
      const result = await response.json();
      if (!response.ok) throw Error(result.error || 'Transcription failed');
      $('prompt').value = result.text; show('chat');
      notice(result.text ? 'Voice input is ready to send.' : 'No speech was detected.'); $('prompt').focus();
    } catch (error) { notice(error.message, true); }
  });
  recorder.start(); setRecordingUi(true); notice('Listening locally. Tap the microphone again when finished.');
}

async function toggleRecording() {
  try { if (recorder && recorder.state === 'recording') recorder.stop(); else await beginRecording(); }
  catch (error) { notice(error.message, true); }
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => show(button.dataset.view, button.dataset.message, button)));
$('scope').addEventListener('change', async () => { notice(); await load(); show('dashboard'); });
$('conversation').addEventListener('change', () => load($('conversation').value).catch(error => notice(error.message, true)));
$('search').addEventListener('input', renderNotes);
$('refresh').addEventListener('click', scan);
$('global-search').addEventListener('keydown', event => {
  if (event.key !== 'Enter') return;
  const query = event.target.value.trim(); if (!query) return;
  $('search').value = query; renderNotes(); show('knowledge');
});

$('new-conversation').addEventListener('click', async () => {
  try { const created = await jsonRequest('/api/conversations', {title: 'New conversation'}); await load(created.id); show('chat'); }
  catch (error) { notice(error.message, true); }
});
$('delete-conversation').addEventListener('click', async () => {
  if (!state.conversation || !confirm(`Delete “${state.conversation.title}” and its messages?`)) return;
  try { const result = await jsonRequest(`/api/conversations/${state.conversation.id}?scope=${encodeURIComponent(currentScope())}`, null, 'DELETE'); await load(result.next_conversation_id); }
  catch (error) { notice(error.message, true); }
});

$('chat-form').addEventListener('submit', async event => {
  event.preventDefault(); if (busy) return;
  const prompt = $('prompt').value.trim(); if (!prompt) return;
  setBusy(true); notice('DAKSH is reasoning locally…');
  try {
    await jsonRequest('/api/chat', {prompt, model: $('model').value, conversation_id: state.conversation.id, speak: true});
    $('prompt').value = ''; await load(state.conversation.id); notice();
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
});

for (const id of ['mic', 'side-mic', 'dock-mic', 'quick-voice', 'overview-voice-button']) $(id).addEventListener('click', toggleRecording);

$('note-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await jsonRequest('/api/memories', {category: $('note-category').value, title: $('note-title').value, content: $('note-content').value, source: $('note-source').value});
    event.target.reset(); $('note-source').value = 'My explicit note'; await load(); notice('Memory stored in this domain.');
  } catch (error) { notice(error.message, true); }
});

$('document-form').addEventListener('submit', async event => {
  event.preventDefault(); const file = $('document-file').files[0]; if (!file) return;
  const form = new FormData(); form.append('scope', currentScope()); form.append('file', file);
  $('upload-progress').hidden = false; event.submitter.disabled = true; notice('Indexing locally…');
  try {
    const response = await fetch('/api/documents', {method: 'POST', headers: {'X-Workspace-Token': state.token}, body: form});
    const result = await response.json(); if (!response.ok) throw Error(result.error || 'Indexing failed');
    event.target.reset(); await load(); notice(result.duplicate ? 'This file was already indexed.' : `${file.name} is ready for local retrieval.`);
  } catch (error) { notice(error.message, true); }
  finally { $('upload-progress').hidden = true; event.submitter.disabled = false; }
});

$('finance-form').addEventListener('submit', async event => {
  event.preventDefault(); const file = $('finance-file').files[0]; if (!file) return;
  const form = new FormData(); form.append('scope', currentScope()); form.append('file', file);
  $('finance-progress').hidden = false; event.submitter.disabled = true; notice('Analysing figures locally…');
  try {
    const response = await fetch('/api/finance/analyze', {method: 'POST', headers: {'X-Workspace-Token': state.token}, body: form});
    const result = await response.json(); if (!response.ok) throw Error(result.error || 'Finance analysis failed');
    renderFinance(result); notice(`${file.name} was analysed without modifying the file.`);
  } catch (error) { notice(error.message, true); }
  finally { $('finance-progress').hidden = true; event.submitter.disabled = false; }
});

$('task-form').addEventListener('submit', async event => {
  event.preventDefault(); setBusy(true);
  try { await jsonRequest('/api/tasks', {prompt: $('task-prompt').value, model: $('model').value}); event.target.reset(); await load(); notice('Mission plan staged.'); }
  catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
});

$('settings-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await jsonRequest('/api/settings', {model: $('settings-model').value, embedding_model: $('embedding-model').value, stt_model: $('stt-model').value, speech_enabled: String($('speech-enabled').checked)});
    await load(state.conversation && state.conversation.id); notice('Local settings saved.');
  } catch (error) { notice(error.message, true); }
});

function updateClock() {
  const now = new Date();
  $('clock').textContent = now.toLocaleTimeString([], {hour12: false});
  $('date').textContent = now.toLocaleDateString([], {weekday: 'short', day: '2-digit', month: 'short', year: 'numeric'}).toUpperCase();
}

updateClock(); setInterval(updateClock, 1000); show('dashboard');
load().then(scan).catch(error => notice(error.message, true));

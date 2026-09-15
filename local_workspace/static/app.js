'use strict';

const $ = id => document.getElementById(id);
let state;
let health = {};
let integrationState = [];
let busy = false;
let recorder;
let audioChunks = [];
const voiceSession = {
  active: false, stream: null, context: null, analyser: null, samples: null,
  recorder: null, chunks: [], frame: null, timeout: null, processing: false, speaking: false
};

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
  if (name !== 'holo' && $('holo-frame').getAttribute('src') !== 'about:blank') $('holo-frame').src = 'about:blank';
  document.querySelectorAll('.view').forEach(node => { node.hidden = node.id !== name; });
  document.querySelectorAll('.left-rail nav button').forEach(node => node.classList.remove('active'));
  const activeNav = trigger && trigger.closest('.left-rail nav') ? trigger : document.querySelector(`.left-rail nav button[data-view="${name}"]:not([data-message])`);
  if (activeNav) activeNav.classList.add('active');
  window.scrollTo({top: 0, behavior: 'smooth'});
  if (message) notice(message);
}

function render() {
  renderBrainGraph();
  renderModels(); renderConversations(); renderMessages(); renderNotes();
  renderDocuments(); renderTasks(); renderSettings(); renderDashboard(); renderCapabilities();
  renderIntegrations(); renderCommunications();
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
  const comm = state.communications || {inbox: [], approvals: [], calendar: [], pending_approvals: 0, unread_messages: 0};
  const coreOnline = health.status === 'ready' || modelCount > 0;
  $('nav-task-count').textContent = openTasks.length;
  $('nav-chat-count').textContent = state.conversations.length;
  $('nav-message-count').textContent = comm.unread_messages + comm.pending_approvals;
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
  addFeed('⌁', 'Communications bridge', `${comm.unread_messages} unread · ${comm.pending_approvals} approvals`, comm.pending_approvals ? 'REVIEW' : 'READY', comm.pending_approvals > 0);
  addFeed('✓', 'Privacy boundary', health.local_only ? 'Bound to this Mac only' : 'Review server binding', health.local_only ? 'LOCAL' : 'CHECK', !health.local_only);

  $('agent-grid').replaceChildren();
  addAgent('▱', 'Memory Agent', `${state.notes.length} records`, health.database ? '' : 'offline');
  addAgent('⌕', 'Retrieval Agent', `${readyDocs.length} indexed files`, health.embedding_model ? '' : 'offline');
  addAgent('◖', 'Voice Agent', health.transcription ? 'Ready' : 'Unavailable', health.transcription ? '' : 'offline');
  addAgent('◇', 'Mission Planner', `${openTasks.length} open`, modelCount ? 'standby' : 'offline');
  addAgent('◉', 'System Agent', health.database ? 'SQLite online' : 'Database offline', health.database ? '' : 'offline');
  addAgent('₹', 'Finance Agent', health.finance ? 'Read-only ready' : 'Unavailable', health.finance ? '' : 'offline');
  addAgent('⌁', 'Message Agent', `${comm.unread_messages} unread`, health.communications ? '' : 'offline');

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
    ['Communications bridge', health.communications ? 'INBOX / APPROVALS READY' : 'OFFLINE', !!health.communications],
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

function communicationTime(value) {
  if (!value) return 'TIME UNKNOWN';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString([], {dateStyle: 'medium', timeStyle: 'short'});
}

function renderCommunications() {
  const comm = state.communications || {connectors: [], inbox: [], approvals: [], calendar: [], pending_approvals: 0, unread_messages: 0};
  $('approval-summary').textContent = `${comm.pending_approvals} PENDING`;
  $('inbox-summary').textContent = `${comm.unread_messages} NEW`;

  const connectors = $('communication-connectors');
  connectors.replaceChildren();
  comm.connectors.forEach(item => {
    const card = el('article', undefined, `communication-connector ${item.configured ? 'online' : ''}`);
    const copy = el('span');
    copy.append(el('strong', item.name), el('small', item.detail));
    card.append(el('i', item.configured ? '●' : '○'), copy, el('b', item.configured ? 'READY' : 'SETUP'));
    connectors.append(card);
  });

  const inbox = $('communication-inbox');
  inbox.replaceChildren();
  if (!comm.inbox.length) inbox.append(el('p', 'No connector messages have been imported.', 'muted'));
  comm.inbox.forEach(item => {
    const card = el('article', undefined, `communication-item ${item.status}`);
    const top = el('div', undefined, 'communication-meta');
    top.append(el('span', item.connector.toUpperCase(), 'card-tag'), el('time', communicationTime(item.received)));
    const actions = el('div', undefined, 'communication-actions');
    const stage = el('button', item.status === 'staged' ? 'MISSION STAGED' : 'STAGE MISSION');
    stage.disabled = item.status === 'staged';
    stage.addEventListener('click', async () => {
      try { const result = await jsonRequest(`/api/communications/messages/${item.id}/task`, {}); await load(); show('tasks'); notice(`Mission ${result.task_id} staged from ${item.connector}.`); }
      catch (error) { notice(error.message, true); }
    });
    const reviewed = el('button', 'MARK REVIEWED');
    reviewed.disabled = item.status === 'reviewed' || item.status === 'archived';
    reviewed.addEventListener('click', async () => {
      try { await jsonRequest(`/api/communications/messages/${item.id}/status`, {status: 'reviewed'}); await load(); show('communications'); }
      catch (error) { notice(error.message, true); }
    });
    actions.append(stage, reviewed);
    card.append(top, el('h3', item.subject || `${item.connector} message`), el('p', item.body), el('small', `FROM ${item.sender || 'UNKNOWN'} · ${item.status.toUpperCase()}`), actions);
    inbox.append(card);
  });

  const approvals = $('communication-approvals');
  approvals.replaceChildren();
  if (!comm.approvals.length) approvals.append(el('p', 'No external instructions are waiting for approval.', 'muted'));
  comm.approvals.forEach(item => {
    const card = el('article', undefined, `communication-item approval-${item.status}`);
    const top = el('div', undefined, 'communication-meta');
    top.append(el('span', item.connector.toUpperCase(), 'card-tag'), el('b', item.status.toUpperCase()));
    card.append(top, el('h3', item.action.replaceAll('_', ' ')));
    if (item.action === 'gmail_reply_draft' && item.proposed_body) {
      card.append(el('p', `TO: ${item.to_address}\nSUBJECT: ${item.reply_subject}`, 'reply-address'));
      const reply = document.createElement('textarea');
      reply.className = 'reply-editor'; reply.rows = 8; reply.value = item.proposed_body;
      reply.disabled = item.status !== 'pending';
      card.append(reply);
      if (item.status === 'pending') {
        const save = el('button', 'SAVE EDIT');
        save.addEventListener('click', async () => {
          try { await jsonRequest(`/api/communications/approvals/${item.id}/reply`, {body: reply.value}); await load(); show('communications'); notice('Reply proposal updated locally.'); }
          catch (error) { notice(error.message, true); }
        });
        card.append(save);
      }
      if (item.google_draft_id) card.append(el('p', `Saved in Gmail Drafts · ${item.google_draft_id}`, 'draft-saved'));
    } else {
      card.append(el('p', item.detail));
    }
    card.append(el('small', `REQUESTED BY ${item.requested_by || 'UNKNOWN'} · ${communicationTime(item.created)}`));
    if (item.status === 'pending') {
      const actions = el('div', undefined, 'communication-actions');
      const approveLabel = item.action === 'gmail_reply_draft' ? 'APPROVE TO GMAIL DRAFT' : 'APPROVE & STAGE';
      for (const [label, status] of [[approveLabel, 'approved'], ['REJECT', 'rejected']]) {
        const button = el('button', label, status === 'approved' ? 'primary' : 'danger');
        button.addEventListener('click', async () => {
          try { await jsonRequest(`/api/communications/approvals/${item.id}`, {status, note: `${label} in DAKSH UI`}); await load(); show('communications'); notice(`Instruction ${status}.`); }
          catch (error) { notice(error.message, true); }
        });
        actions.append(button);
      }
      card.append(actions);
    }
    approvals.append(card);
  });

  const calendar = $('communication-calendar');
  calendar.replaceChildren();
  if (!comm.calendar.length) calendar.append(el('p', 'No upcoming Google Calendar events have been imported.', 'muted'));
  comm.calendar.forEach(item => {
    const card = el('article', undefined, 'communication-item calendar-item');
    card.append(el('time', communicationTime(item.starts_at), 'calendar-time'), el('h3', item.title));
    if (item.location) card.append(el('p', item.location));
    card.append(el('small', `${item.status.toUpperCase()} · ${item.connector.replaceAll('_', ' ').toUpperCase()}`));
    calendar.append(card);
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
  $('mic').classList.toggle('recording', recording);
  $('mic').textContent = recording ? '■ STOP' : '◉ MIC';
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

function setVoiceState(stateName, title, caption) {
  $('voice-mode').dataset.state = stateName;
  $('voice-state').textContent = title;
  $('voice-caption').textContent = caption;
  $('voice-label').textContent = title.charAt(0) + title.slice(1).toLowerCase();
  $('dock-status').textContent = caption;
}

function addVoiceTurn(role, text) {
  const root = $('voice-log');
  if (root.children.length === 1 && root.firstElementChild.tagName === 'P') root.replaceChildren();
  const turn = el('article', undefined, `voice-turn ${role}`);
  turn.append(el('strong', role === 'user' ? 'YOU' : role === 'assistant' ? 'DAKSH' : 'SYSTEM'), el('p', text));
  root.append(turn);
  root.scrollTop = root.scrollHeight;
}

function stopVoiceCapture() {
  if (voiceSession.frame) cancelAnimationFrame(voiceSession.frame);
  if (voiceSession.timeout) clearTimeout(voiceSession.timeout);
  voiceSession.frame = null; voiceSession.timeout = null;
  if (voiceSession.recorder && voiceSession.recorder.state === 'recording') voiceSession.recorder.stop();
  $('voice-mode').style.setProperty('--voice-level', 0);
}

async function listenVoiceTurn() {
  if (!voiceSession.active || voiceSession.processing) return;
  if (voiceSession.recorder && voiceSession.recorder.state === 'recording') return;
  if (!voiceSession.stream) throw Error('Microphone stream is unavailable.');
  voiceSession.chunks = [];
  let heardSpeech = false;
  let lastSpeech = Date.now();
  const started = Date.now();
  const recording = new MediaRecorder(voiceSession.stream);
  voiceSession.recorder = recording;
  recording.addEventListener('dataavailable', event => { if (event.data.size) voiceSession.chunks.push(event.data); });
  recording.addEventListener('stop', () => processVoiceTurn(voiceSession.chunks, recording.mimeType));
  recording.start(200);
  setVoiceState('listening', 'LISTENING', 'Speak naturally. I will respond when you pause.');

  const watch = () => {
    if (!voiceSession.active || recording.state !== 'recording') return;
    voiceSession.analyser.getByteTimeDomainData(voiceSession.samples);
    let energy = 0;
    for (const sample of voiceSession.samples) energy += Math.pow((sample - 128) / 128, 2);
    const rms = Math.sqrt(energy / voiceSession.samples.length);
    const level = Math.min(1, rms * 11);
    $('voice-mode').style.setProperty('--voice-level', level.toFixed(2));
    if (rms > 0.025) { heardSpeech = true; lastSpeech = Date.now(); }
    if (heardSpeech && Date.now() - lastSpeech > 1150 && Date.now() - started > 900) return stopVoiceCapture();
    voiceSession.frame = requestAnimationFrame(watch);
  };
  voiceSession.frame = requestAnimationFrame(watch);
  voiceSession.timeout = setTimeout(stopVoiceCapture, 20000);
}

async function transcribeVoiceTurn(chunks, mimeType) {
  const blob = new Blob(chunks, {type: mimeType || 'audio/webm'});
  if (blob.size < 500) return '';
  const extension = /mp4|m4a/i.test(mimeType) ? 'mp4' : /ogg/i.test(mimeType) ? 'ogg' : 'webm';
  const form = new FormData();
  form.append('scope', currentScope()); form.append('file', blob, `voice.${extension}`);
  const response = await fetch('/api/voice/transcribe', {method: 'POST', headers: {'X-Workspace-Token': state.token}, body: form});
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Transcription failed');
  return result.text.trim();
}

function spokenText(text) {
  return text.replace(/```[\s\S]*?```/g, ' code omitted from speech ')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1').replace(/[*_#>`]/g, '').replace(/\s+/g, ' ').trim();
}

function speakVoiceAnswer(text) {
  return new Promise(async resolve => {
    const speech = spokenText(text);
    if (!speech) return resolve();
    setVoiceState('speaking', 'SPEAKING', 'You may interrupt me at any time.');
    voiceSession.speaking = true;
    if ('speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) {
      const utterance = new SpeechSynthesisUtterance(speech);
      const voices = speechSynthesis.getVoices();
      utterance.voice = voices.find(item => /daniel|alex|arthur/i.test(item.name) && /^en/i.test(item.lang)) || voices.find(item => /^en/i.test(item.lang)) || null;
      utterance.rate = 0.96; utterance.pitch = 0.82;
      utterance.onend = utterance.onerror = () => { voiceSession.speaking = false; resolve(); };
      speechSynthesis.cancel(); speechSynthesis.speak(utterance);
      return;
    }
    try { await jsonRequest('/api/voice/speak', {text: speech}); }
    finally {
      setTimeout(() => { voiceSession.speaking = false; resolve(); }, Math.min(15000, Math.max(1500, speech.length * 48)));
    }
  });
}

async function processVoiceTurn(chunks, mimeType) {
  if (!voiceSession.active) return;
  voiceSession.processing = true;
  try {
    setVoiceState('thinking', 'TRANSCRIBING', 'Whisper is processing your voice locally.');
    const prompt = await transcribeVoiceTurn(chunks, mimeType);
    if (!voiceSession.active) return;
    if (!prompt) {
      addVoiceTurn('system', 'I did not detect clear speech. Listening again.');
      voiceSession.processing = false;
      return setTimeout(() => listenVoiceTurn().catch(showVoiceError), 500);
    }
    addVoiceTurn('user', prompt);
    setVoiceState('thinking', 'REASONING', 'The local Ollama model is preparing a response.');
    const result = await jsonRequest('/api/chat', {
      prompt, model: $('model').value, conversation_id: state.conversation.id,
      speak: false, voice_mode: true
    });
    if (!voiceSession.active) return;
    addVoiceTurn('assistant', result.response);
    await load(state.conversation.id);
    await speakVoiceAnswer(result.response);
  } catch (error) {
    showVoiceError(error);
    await new Promise(resolve => setTimeout(resolve, 1400));
  } finally {
    voiceSession.processing = false;
    if (voiceSession.active && !voiceSession.speaking) listenVoiceTurn().catch(showVoiceError);
  }
}

function showVoiceError(error) {
  const message = error && error.message ? error.message : String(error);
  setVoiceState('error', 'VOICE LINK ERROR', message);
  addVoiceTurn('system', message);
}

async function openVoiceMode() {
  if (voiceSession.active) return;
  if (!health.transcription) return notice('Local voice transcription is not ready.', true);
  if (!navigator.mediaDevices || !window.MediaRecorder) return notice('This browser cannot start a voice session.', true);
  voiceSession.active = true;
  $('voice-mode').hidden = false;
  document.body.classList.add('voice-active');
  $('voice-domain').textContent = currentScope().toUpperCase();
  $('voice-model').textContent = state.settings.model || state.models[0] || 'OFFLINE';
  $('voice-memory').textContent = `${state.notes.length} RECORDS`;
  $('voice-log').replaceChildren(el('p', 'Voice link opened. Your turns will appear here.'));
  try {
    setVoiceState('idle', 'MICROPHONE ACCESS', 'Allow microphone access to begin the private voice session.');
    const microphone = navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}})
      .then(stream => { if (!voiceSession.active) stream.getTracks().forEach(track => track.stop()); return stream; });
    const permissionTimeout = new Promise((_, reject) => setTimeout(() => reject(Error('Microphone access timed out. Allow microphone permission in your browser, then start the session again.')), 12000));
    voiceSession.stream = await Promise.race([microphone, permissionTimeout]);
    const AudioEngine = window.AudioContext || window.webkitAudioContext;
    voiceSession.context = new AudioEngine();
    if (voiceSession.context.state === 'suspended') await voiceSession.context.resume();
    voiceSession.analyser = voiceSession.context.createAnalyser();
    voiceSession.analyser.fftSize = 1024;
    voiceSession.samples = new Uint8Array(voiceSession.analyser.fftSize);
    voiceSession.context.createMediaStreamSource(voiceSession.stream).connect(voiceSession.analyser);
    addVoiceTurn('system', 'Voice conversation ready. Speak after the listening signal.');
    await listenVoiceTurn();
  } catch (error) {
    showVoiceError(error);
    voiceSession.active = false;
  }
}

function endVoiceMode() {
  voiceSession.active = false; voiceSession.processing = false; voiceSession.speaking = false;
  stopVoiceCapture();
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  if (voiceSession.stream) voiceSession.stream.getTracks().forEach(track => track.stop());
  if (voiceSession.context) voiceSession.context.close().catch(() => {});
  voiceSession.stream = null; voiceSession.context = null; voiceSession.analyser = null; voiceSession.recorder = null;
  $('voice-mode').hidden = true; document.body.classList.remove('voice-active');
  $('voice-label').textContent = health.transcription ? 'Ready' : 'Unavailable';
  $('dock-status').textContent = health.transcription ? 'Continuous conversation' : 'Voice offline';
}

function interruptVoice() {
  if (!voiceSession.active) return openVoiceMode();
  if (voiceSession.processing && !voiceSession.speaking) {
    setVoiceState('thinking', 'REASONING', 'Finishing the current local response.');
    return;
  }
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  voiceSession.speaking = false; voiceSession.processing = false;
  listenVoiceTurn().catch(showVoiceError);
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => show(button.dataset.view, button.dataset.message, button)));
$('scope').addEventListener('change', async () => {
  $('holo-frame').src = 'about:blank';
  $('local-skill-result').textContent = ''; $('local-skill-input').value = '';
  for (const k of ['goal','context','probability','loss','tolerance']) $('protocol-'+k).value = '';
  $('protocol-result').textContent = '';
  $('local-skill-download').disabled = true; $('local-skill-pdf').disabled=true; localSkillReport = '';
  notice(); await load(); show('graph');
});
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

$('mic').addEventListener('click', toggleRecording);
for (const id of ['side-mic', 'dock-mic', 'quick-voice', 'overview-voice-button']) $(id).addEventListener('click', openVoiceMode);
$('voice-close').addEventListener('click', endVoiceMode);
$('voice-end').addEventListener('click', endVoiceMode);
$('voice-interrupt').addEventListener('click', interruptVoice);
document.addEventListener('keydown', event => { if (event.key === 'Escape' && voiceSession.active) endVoiceMode(); });

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

$('poll-communications').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  notice('Checking configured channels…');
  try {
    const result = await jsonRequest('/api/communications/poll', {});
    await load(); show('communications');
    const imported = result.results.reduce((sum, item) => sum + (item.imported || item.imported_or_updated || 0), 0);
    const errors = result.results.filter(item => item.error).length;
    notice(errors ? `Check finished with ${errors} connector error. ${imported} items imported or updated.` : `Channels checked. ${imported} items imported or updated.`, errors > 0);
  } catch (error) { notice(error.message, true); }
  finally { event.currentTarget.disabled = false; }
});

function updateClock() {
  const now = new Date();
  $('clock').textContent = now.toLocaleTimeString([], {hour12: false});
  $('date').textContent = now.toLocaleDateString([], {weekday: 'short', day: '2-digit', month: 'short', year: 'numeric'}).toUpperCase();
}

let brainGraph = null;
function renderBrainGraph() {
  const groups = {
    core: {name:'Workspace',c:'#f5c86b',r:14,pace:10,pause:10},
    documents: {name:'Documents',c:'#38bdf8',r:7,pace:8,pause:30},
    memory: {name:'Explicit memory',c:'#2dd4bf',r:7,pace:8,pause:30},
    tasks: {name:'Tasks',c:'#c4b5fd',r:7,pace:8,pause:30},
    conversations: {name:'Conversations',c:'#94a3b8',r:6,pace:8,pause:30},
    approvals: {name:'Approvals',c:'#fb923c',r:8,pace:8,pause:30}
  };
  const nodes = [{label:state.scope,key:'workspace',g:'core',view:'dashboard',detail:'Current private workspace. Grouping links do not imply business relationships.'}];
  const links = [];
  const records = [
    ['documents',state.documents,'documents',x=>x.filename, x=>`${x.status} · ${x.chunk_count} indexed chunks`],
    ['memory',state.notes,'knowledge',x=>x.title,x=>`${x.category}\n${x.content.slice(0,240)}`],
    ['tasks',state.tasks,'tasks',x=>x.title,x=>x.status],
    ['conversations',state.conversations,'chat',x=>x.title,x=>'Persistent local conversation'],
    ['approvals',state.communications.approvals,'communications',x=>`${x.connector}: ${x.reply_subject || x.action}`,x=>`${x.status} · Review in Messages before acting`]
  ];
  for (const [g,items,view,label,detail] of records) {
    if (!items.length) continue;
    const hub = nodes.length;
    nodes.push({label:groups[g].name,key:`group:${g}`,g,view,detail:`${items.length} records in ${state.scope}`});
    links.push({s:0,t:hub});
    for (const x of items) {
      links.push({s:hub,t:nodes.length});
      nodes.push({label:label(x),key:`${g}:${x.id}`,g,view,detail:detail(x),recordId:x.id});
    }
  }
  // Resolve only explicit [[title]] references with one unambiguous target.
  for (const note of state.notes) {
    const s = nodes.findIndex(n=>n.key===`memory:${note.id}`);
    for (const match of note.content.matchAll(/\[\[([^\]]+)\]\]/g)) {
      const name = match[1].split('|')[0].trim().toLowerCase();
      const targets = nodes.map((n,i)=>({n,i})).filter(x=>x.i!==s && x.n.recordId && x.n.label.toLowerCase()===name);
      if (targets.length===1 && !links.some(l=>l.s===s && l.t===targets[0].i)) links.push({s,t:targets[0].i,reference:true});
    }
  }
  brainGraph = {groups,nodes,links};
  $('graph-summary').textContent = `${state.scope} · ${nodes.filter(n=>n.recordId).length} real records · ${links.filter(l=>l.reference).length} explicit references. ${nodes.length===1 ? 'Add a document or memory to grow your graph.' : ''}`;
  $('brain-frame').src = '/brain-map.html?revision=' + Date.now();
}
window.addEventListener('message', event => {
  const frame = $('brain-frame');
  if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
  if (event.data?.type==='daksh-graph-ready' && brainGraph) frame.contentWindow.postMessage({type:'daksh-graph',graph:brainGraph},location.origin);
  if (event.data?.type==='daksh-graph-open' && brainGraph) {
    const node = brainGraph.nodes.find(n=>n.key===event.data.key);
    if (!node) return;
    show(node.view);
    if (node.g==='conversations' && node.recordId) load(node.recordId).catch(error=>notice(error.message,true));
    else notice(node.label);
  }
});
$('graph-refresh').addEventListener('click',()=>load(state.conversation?.id).catch(error=>notice(error.message,true)));
let localSkillReport = '';
async function loadLocalSkillCatalog() {
  const response = await fetch('/api/local-skills');
  if (!response.ok) throw Error('Could not load local workflow references.');
  const catalog = await response.json();
  $('local-skill-select').replaceChildren(...catalog.skills.map(x=>new Option(`${x.suite.includes('finance')?'Finance':'Agency'} · ${x.name}`,x.id)));
}
window.addEventListener('message',event=> {
  const frame = $('holo-frame');
  if (event.origin!==location.origin || event.source!==frame.contentWindow || event.data?.type!=='daksh-holo-ready') return;
  const files = state.notes.slice(0,40).map(x=>({name:`memory-${x.id}.md`,title:x.title,body:x.content.slice(0,420),full:x.content.slice(0,4000)}));
  const documents = state.documents.slice(0,40).map(x=>({name:x.filename,title:x.filename,body:`${x.status} · ${x.chunk_count} indexed chunks`,full:'Open Knowledge Base and ask DAKSH for document-grounded answers. This card shows indexing metadata, not extracted document content.'}));
  const tree = [];
  if(files.length)tree.push({kind:'folder',name:'MEMORY',files});
  if(documents.length)tree.push({kind:'folder',name:'DOCUMENTS',files:documents});
  if(!tree.length)tree.push({kind:'folder',name:state.scope.toUpperCase(),files:[{name:'welcome.md',title:'Add your knowledge',body:'Add explicit memory or upload documents in DAKSH to populate this deck.',full:'This is a welcome card, not a stored memory. Camera frames stay in this page. Leave the deck or press Stop deck to release the camera.'}]});
  frame.contentWindow.postMessage({type:'daksh-holo',tree},location.origin);
});
$('holo-start').addEventListener('click',()=>{$('holo-frame').src='/holo/holo.html';});
$('holo-demo').addEventListener('click',()=>{$('holo-frame').src='/holo/holo.html?sim=1';});
$('holo-stop').addEventListener('click',()=>{$('holo-frame').src='about:blank';});
$('local-skill-form').addEventListener('submit',async event=> {
  event.preventDefault();
  $('local-skill-run').disabled=true; $('local-skill-download').disabled=true; $('local-skill-pdf').disabled=true;
  $('local-skill-status').textContent='Working with your local Ollama model…';
  $('local-skill-result').textContent=''; localSkillReport='';
  const requestedScope=currentScope();
  try {
    const result=await jsonRequest('/api/local-skills/run',{skill:$('local-skill-select').value,evidence:$('local-skill-input').value});
    if(currentScope()!==requestedScope)return;
    localSkillReport=`# DAKSH local workflow report\n\nWorkspace: ${result.scope}\nModel: ${result.model}\nWorkflow: ${result.skill}\n\n${result.response}`;
    $('local-skill-result').textContent=result.response;
    $('local-skill-status').textContent='Local report ready. Review assumptions and evidence gaps before use.';
    $('local-skill-download').disabled=false; $('local-skill-pdf').disabled=false;
    await load(state.conversation?.id);
  } catch(error) { if(currentScope()===requestedScope)$('local-skill-status').textContent=error.message; }
  finally { $('local-skill-run').disabled=false; }
});
$('local-skill-download').addEventListener('click',()=> {
  if(!localSkillReport)return;
  const url=URL.createObjectURL(new Blob([localSkillReport],{type:'text/markdown'}));
  const link=document.createElement('a');link.href=url;link.download='DAKSH-local-report.md';link.click();URL.revokeObjectURL(url);
});
$('local-skill-pdf').addEventListener('click',async()=> {
  if(!localSkillReport)return;
  const button=$('local-skill-pdf');button.disabled=true;
  try {
    const response=await fetch('/api/local-skills/export',{method:'POST',headers:{'Content-Type':'application/json','X-Workspace-Token':state.token},body:JSON.stringify({scope:currentScope(),report:localSkillReport})});
    if(!response.ok)throw Error('PDF export could not finish. Check local dependencies.');
    const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download='DAKSH-local-report.pdf';link.click();URL.revokeObjectURL(url);
  }catch(error){$('local-skill-status').textContent=error.message;}finally{button.disabled=!localSkillReport;}
});
loadLocalSkillCatalog().catch(error=>notice(error.message,true));
updateClock(); setInterval(updateClock, 1000); show('graph');
load().then(scan).catch(error => notice(error.message, true));

$('protocol-form').addEventListener('submit', async event => {
  event.preventDefault(); const scope = state.scope;
  const data = {scope, goal:$('protocol-goal').value,domain:$('protocol-domain').value,context:$('protocol-context').value};
  for (const k of ['probability','loss','tolerance']) if ($('protocol-'+k).value !== '') data[k] = Number($('protocol-'+k).value);
  try {
    const response = await fetch('/api/protocol/contract',{method:'POST',headers:{'Content-Type':'application/json','X-Workspace-Token':state.token},body:JSON.stringify(data)});
    const result = await response.json(); if (!response.ok) throw Error(result.detail || 'Contract failed');
    if (state.scope === scope) $('protocol-result').textContent = result.markdown;
  } catch (error) { if (state.scope === scope) $('protocol-result').textContent = error.message; }
});

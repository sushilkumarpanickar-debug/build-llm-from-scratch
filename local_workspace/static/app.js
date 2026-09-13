'use strict';

const $ = id => document.getElementById(id);
let state;
let health = {};
let busy = false;
let recorder;
let audioChunks = [];

const headings = {
  chat: 'Good evening. Systems are standing by.',
  knowledge: 'Memory architecture, under your control.',
  documents: 'Your local knowledge, indexed and ready.',
  tasks: 'Mission planning and agent readiness.',
  settings: 'Every capability, truthfully mapped.'
};
const labels = {chat:'COMMAND CENTRE',knowledge:'MEMORY VAULT',documents:'KNOWLEDGE FILES',tasks:'MISSIONS',settings:'SYSTEMS MATRIX'};

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

async function jsonRequest(path, data, method = 'POST') {
  const options = {method, headers: {'X-Workspace-Token': state.token}};
  if (data) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify({...data, scope: $('scope').value});
  }
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw Error(result.error || result.detail || 'Request failed');
  return result;
}

async function load(conversationId) {
  const query = new URLSearchParams({scope: $('scope').value});
  if (conversationId) query.set('conversation_id', conversationId);
  const response = await fetch('/api/state?' + query);
  state = await response.json();
  if (!response.ok) throw Error(state.error || 'Could not load the workspace');
  render();
}

function show(name) {
  document.querySelectorAll('.view').forEach(node => { node.hidden = node.id !== name; });
  document.querySelectorAll('nav button').forEach(node => node.classList.toggle('active', node.dataset.view === name));
  $('heading').textContent = headings[name];
  $('breadcrumb').textContent = $('scope').value.toUpperCase() + ' / ' + labels[name];
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function render() {
  renderModels();
  renderConversations();
  renderMessages();
  renderNotes();
  renderDocuments();
  renderTasks();
  renderSettings();
  renderMap();
}

function renderModels() {
  const current = state.settings.model;
  for (const id of ['model', 'settings-model']) {
    const select = $(id);
    select.replaceChildren();
    if (!state.models.length) select.append(new Option('No local chat model', ''));
    state.models.forEach(name => select.append(new Option(name, name, false, name === current)));
  }
  $('model-status').textContent = state.models.length ? (current || state.models[0]).toUpperCase() : 'OLLAMA MODEL OFFLINE';
}

function renderConversations() {
  const select = $('conversation');
  select.replaceChildren();
  state.conversations.forEach(item => select.append(new Option(item.title, item.id, false, state.conversation && item.id === state.conversation.id)));
}

function sourceChip(source) {
  const label = source.type === 'document'
    ? `${source.title} · ${source.location}`
    : `Memory ${source.id} · ${source.title}`;
  return el('span', label, 'source-chip');
}

function renderMessages() {
  const root = $('messages');
  root.replaceChildren();
  if (!state.messages.length) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('span', '◈', 'symbol'), el('h2', 'What shall we work on?'), el('p', 'Ask DAKSH, use the microphone, or teach it with your local documents. Your domain controls which memory and files can be retrieved.'));
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
      try {
        await jsonRequest(`/api/documents/${document.id}?scope=${encodeURIComponent($('scope').value)}`, null, 'DELETE');
        await load();
      } catch (error) { notice(error.message, true); }
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
    ['planned','in_progress','completed'].forEach(status => select.append(new Option(status.replace('_', ' '), status, false, task.status === status)));
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
}

function renderMap() {
  $('map-memory').textContent = `${state.notes.length} records`;
  $('map-docs').textContent = `${state.documents.filter(item => item.status === 'ready').length} indexed`;
  $('map-tasks').textContent = `${state.tasks.length} staged`;
  $('map-domain').textContent = state.scope.toUpperCase();
  $('map-model').textContent = state.models.length ? (state.settings.model || state.models[0]) : 'offline';
  $('map-voice').textContent = health.transcription ? 'local ready' : 'offline';
  $('node-total').textContent = `${state.notes.length + state.documents.reduce((sum, item) => sum + item.chunk_count, 0)} NODES`;
  $('note-category').replaceChildren(...state.memory_categories.map(category => new Option(category.replaceAll('_', ' '), category)));
}

function renderCapabilities() {
  const root = $('capabilities');
  root.replaceChildren();
  const entries = [
    ['Ollama local inference', health.models && health.models.length ? health.models.join(', ') : 'OFFLINE', !!(health.models && health.models.length)],
    ['Semantic document search', health.embedding_model || 'MODEL MISSING', !!health.embedding_model],
    ['Local voice input', health.transcription ? 'FASTER-WHISPER' : 'OFFLINE', !!health.transcription],
    ['macOS spoken replies', health.speech ? 'SAY READY' : 'OFFLINE', !!health.speech],
    ['Persistent workspace', health.database ? 'SQLITE READY' : 'OFFLINE', !!health.database],
    ['Network boundary', health.local_only ? '127.0.0.1 ONLY' : 'CHECK REQUIRED', !!health.local_only]
  ];
  entries.forEach(([name, status, live]) => {
    const item = el('div', undefined, 'capability ' + (live ? 'live' : 'planned'));
    item.append(el('strong', name), el('span', status)); root.append(item);
  });
  $('embedding-state').textContent = health.embedding_model ? 'ONLINE' : 'OFFLINE';
  $('core-state').textContent = health.status === 'ready' ? 'LOCAL CORE ONLINE' : 'LOCAL CORE LIMITED';
}

async function scan() {
  try {
    const response = await fetch('/api/health');
    health = await response.json();
    renderCapabilities(); renderSettings(); renderMap();
  } catch (error) { notice('System scan failed: ' + error.message, true); }
}

async function setBusy(value) {
  busy = value;
  document.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = value; });
  $('inference-state').textContent = value ? 'PROCESSING' : 'STANDBY';
  document.body.classList.toggle('thinking', value);
}

async function beginRecording() {
  if (!navigator.mediaDevices || !window.MediaRecorder) throw Error('This browser does not support microphone recording.');
  const stream = await navigator.mediaDevices.getUserMedia({audio: true});
  audioChunks = [];
  recorder = new MediaRecorder(stream);
  recorder.addEventListener('dataavailable', event => { if (event.data.size) audioChunks.push(event.data); });
  recorder.addEventListener('stop', async () => {
    stream.getTracks().forEach(track => track.stop());
    $('mic').classList.remove('recording'); $('mic').textContent = '◉ MIC';
    const blob = new Blob(audioChunks, {type: recorder.mimeType || 'audio/webm'});
    const form = new FormData();
    form.append('scope', $('scope').value); form.append('file', blob, 'voice.webm');
    try {
      notice('Transcribing on this Mac…');
      const response = await fetch('/api/voice/transcribe', {method:'POST', headers:{'X-Workspace-Token':state.token}, body:form});
      const result = await response.json();
      if (!response.ok) throw Error(result.error || 'Transcription failed');
      $('prompt').value = result.text; notice(result.text ? 'Voice input is ready to send.' : 'No speech was detected.'); $('prompt').focus();
    } catch (error) { notice(error.message, true); }
  });
  recorder.start(); $('mic').classList.add('recording'); $('mic').textContent = '■ STOP'; notice('Listening locally. Press STOP when finished.');
}

document.querySelectorAll('nav button').forEach(button => button.addEventListener('click', () => show(button.dataset.view)));
document.querySelectorAll('[data-view]:not(nav button)').forEach(button => button.addEventListener('click', () => show(button.dataset.view)));
$('scope').addEventListener('change', async () => { notice(); await load(); show('chat'); });
$('conversation').addEventListener('change', () => load($('conversation').value).catch(error => notice(error.message, true)));
$('search').addEventListener('input', renderNotes);
$('refresh').addEventListener('click', scan);

$('new-conversation').addEventListener('click', async () => {
  try { const created = await jsonRequest('/api/conversations', {title:'New conversation'}); await load(created.id); }
  catch (error) { notice(error.message, true); }
});
$('delete-conversation').addEventListener('click', async () => {
  if (!state.conversation || !confirm(`Delete “${state.conversation.title}” and its messages?`)) return;
  try {
    const result = await jsonRequest(`/api/conversations/${state.conversation.id}?scope=${encodeURIComponent($('scope').value)}`, null, 'DELETE');
    await load(result.next_conversation_id);
  } catch (error) { notice(error.message, true); }
});

$('chat-form').addEventListener('submit', async event => {
  event.preventDefault(); if (busy) return;
  const prompt = $('prompt').value.trim(); if (!prompt) return;
  await setBusy(true); notice('DAKSH is reasoning locally…');
  try {
    await jsonRequest('/api/chat', {prompt, model:$('model').value, conversation_id:state.conversation.id, speak:true});
    $('prompt').value = ''; await load(state.conversation.id); notice();
  } catch (error) { notice(error.message, true); }
  finally { await setBusy(false); }
});

$('mic').addEventListener('click', async () => {
  try { if (recorder && recorder.state === 'recording') recorder.stop(); else await beginRecording(); }
  catch (error) { notice(error.message, true); }
});

$('note-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await jsonRequest('/api/memories', {category:$('note-category').value,title:$('note-title').value,content:$('note-content').value,source:$('note-source').value});
    event.target.reset(); $('note-source').value = 'My explicit note'; await load(); notice('Memory stored in this domain.');
  } catch (error) { notice(error.message, true); }
});

$('document-form').addEventListener('submit', async event => {
  event.preventDefault(); const file = $('document-file').files[0]; if (!file) return;
  const form = new FormData(); form.append('scope', $('scope').value); form.append('file', file);
  $('upload-progress').hidden = false; event.submitter.disabled = true; notice('Indexing locally…');
  try {
    const response = await fetch('/api/documents', {method:'POST',headers:{'X-Workspace-Token':state.token},body:form});
    const result = await response.json(); if (!response.ok) throw Error(result.error || 'Indexing failed');
    event.target.reset(); await load(); notice(result.duplicate ? 'This file was already indexed.' : `${file.name} is ready for local retrieval.`);
  } catch (error) { notice(error.message, true); }
  finally { $('upload-progress').hidden = true; event.submitter.disabled = false; }
});

$('task-form').addEventListener('submit', async event => {
  event.preventDefault(); await setBusy(true);
  try { await jsonRequest('/api/tasks', {prompt:$('task-prompt').value,model:$('model').value}); event.target.reset(); await load(); notice('Mission plan staged.'); }
  catch (error) { notice(error.message, true); } finally { await setBusy(false); }
});

$('settings-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await jsonRequest('/api/settings', {model:$('settings-model').value,embedding_model:$('embedding-model').value,stt_model:$('stt-model').value,speech_enabled:String($('speech-enabled').checked)});
    await load(state.conversation.id); notice('Local settings saved.');
  } catch (error) { notice(error.message, true); }
});

setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString([], {hour12:false}); }, 1000);
load().then(scan).catch(error => notice(error.message, true));

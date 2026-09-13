'use strict';

const $ = id => document.getElementById(id);
let state;
let view = 'chat';
let busy = false;

const headings = {
  chat: 'Good evening. Systems are standing by.',
  knowledge: 'Memory architecture, under your control.',
  tasks: 'Mission planning and agent readiness.',
  connections: 'Every capability, truthfully mapped.'
};

const viewLabels = {
  chat: 'COMMAND CENTRE',
  knowledge: 'MEMORY VAULT',
  tasks: 'MISSIONS & AGENTS',
  connections: 'SYSTEMS MATRIX'
};

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function notice(message = '') { $('notice').textContent = message; }

async function api(path, data) {
  const response = await fetch(path, data ? {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Workspace-Token': state.token},
    body: JSON.stringify({...data, scope: $('scope').value})
  } : {});
  const result = await response.json();
  if (!response.ok) throw Error(result.error || 'Request failed');
  return result;
}

function show(name) {
  view = name;
  document.querySelectorAll('.view').forEach(node => { node.hidden = node.id !== name; });
  document.querySelectorAll('nav button').forEach(node => node.classList.toggle('active', node.dataset.view === name));
  $('heading').textContent = headings[name];
  $('breadcrumb').textContent = $('scope').value.toUpperCase() + ' / ' + viewLabels[name];
}

function renderNotes() {
  const root = $('notes');
  const query = $('search').value.toLowerCase();
  const notes = state.notes.filter(note => (note.title + ' ' + note.content).toLowerCase().includes(query));
  root.replaceChildren();
  if (!notes.length) root.append(el('p', query ? 'No matching memories.' : 'No memories stored in this domain.', 'muted'));
  for (const note of notes) {
    const card = el('article', undefined, 'card');
    card.append(el('h3', note.title), el('p', note.content), el('small', 'MEMORY ' + note.id + ' · ' + note.source + ' · ' + new Date(note.created).toLocaleDateString()));
    root.append(card);
  }
}

function renderTasks() {
  const root = $('task-list');
  root.replaceChildren();
  if (!state.tasks.length) root.append(el('p', 'No missions are staged. Define an outcome above.', 'muted'));
  for (const task of state.tasks) {
    const card = el('article', undefined, 'card');
    const select = el('select');
    select.setAttribute('aria-label', 'Status for ' + task.title);
    for (const [value, label] of [['planned', 'PLAN READY'], ['in_progress', 'IN PROGRESS'], ['completed', 'COMPLETED BY ME']]) {
      const option = el('option', label);
      option.value = value;
      select.append(option);
    }
    select.value = task.status;
    select.onchange = async () => {
      try {
        await api('/api/tasks/status', {id: task.id, status: select.value});
        await load();
      } catch (error) {
        notice(error.message);
        select.value = task.status;
      }
    };
    card.append(el('h3', task.title), el('p', task.plan), el('small', 'LOCAL AI PLAN · REVIEW REQUIRED'), el('br'), select);
    root.append(card);
  }
}

function renderCapabilities() {
  const root = $('capabilities');
  root.replaceChildren();
  const capabilities = [
    ['Ollama · reasoning and planning', state.models.length ? 'ONLINE' : 'OFFLINE', state.models.length ? 'live' : 'planned'],
    ['Domain memory and mission records', 'ONLINE', 'live'],
    ['GitHub repositories', 'DISCOVERED · BRIDGE PENDING', 'planned'],
    ['Commander → Manager → Worker', 'IMPLEMENTATION PENDING', 'planned'],
    ['Voice and desktop control', 'NOT CONNECTED', 'planned'],
    ['Email, calendar and external tools', 'NOT CONNECTED', 'planned']
  ];
  for (const [name, status, mode] of capabilities) {
    const row = el('div', undefined, 'capability ' + mode);
    row.append(el('strong', name), el('span', status));
    root.append(row);
  }
}

function render() {
  const selected = $('model').value;
  $('model').replaceChildren(...state.models.map(model => {
    const option = el('option', model);
    option.value = model;
    return option;
  }));
  if (state.models.includes(selected)) $('model').value = selected;
  if (!state.models.length) $('model').append(el('option', 'No local model available'));
  $('model-status').textContent = state.models.length ? 'LOCAL CORE · ONLINE' : 'LOCAL CORE · OFFLINE';
  $('inference-state').textContent = busy ? 'ACTIVE' : state.models.length ? 'STANDBY' : 'OFFLINE';
  $('local-caption').textContent = state.models.length ? 'Ollama is ready. All model traffic stays on this Mac.' : 'Open Ollama with a local model, then run a system scan.';
  $('note-count').textContent = state.notes.length;
  $('task-count').textContent = state.tasks.length;
  $('model-count').textContent = state.models.length;

  const messages = $('messages');
  messages.replaceChildren();
  if (!state.messages.length) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('div', '◈', 'symbol'), el('h2', 'Awaiting your directive.'), el('p', 'Ask DAKSH to reason with your saved memory, shape an idea, or prepare a mission plan.'));
    messages.append(empty);
  }
  for (const message of [...state.messages].reverse()) {
    const item = el('article', undefined, 'message ' + message.role);
    item.append(el('strong', message.role === 'user' ? 'OPERATOR' : 'DAKSH'), el('p', message.content));
    messages.append(item);
  }
  messages.scrollTop = messages.scrollHeight;
  renderNotes();
  renderTasks();
  renderCapabilities();
  show(view);
}

async function load() {
  state = await api('/api/state?scope=' + encodeURIComponent($('scope').value));
  render();
}

document.querySelectorAll('[data-view]').forEach(button => { button.onclick = () => show(button.dataset.view); });
$('scope').onchange = () => { notice(); load().catch(error => notice(error.message)); };
$('search').oninput = renderNotes;
$('refresh').onclick = () => load().then(() => notice('SYSTEM SCAN COMPLETE · Capability state refreshed.')).catch(error => notice(error.message));

$('note-form').onsubmit = async event => {
  event.preventDefault();
  try {
    await api('/api/notes', {title: $('note-title').value, content: $('note-content').value, source: $('note-source').value});
    $('note-form').reset();
    await load();
    notice('MEMORY STORED · Saved inside ' + $('scope').value + '.');
  } catch (error) { notice(error.message); }
};

async function generate(event, type) {
  event.preventDefault();
  if (busy) return;
  if (!state.models.length) {
    show('connections');
    notice('Open Ollama with a local model, then run a system scan.');
    return;
  }
  busy = true;
  const form = event.target;
  const input = $(type === 'chat' ? 'prompt' : 'task-prompt');
  form.querySelector('button').disabled = true;
  $('scope').disabled = true;
  $('inference-state').textContent = 'ACTIVE';
  notice(type === 'chat' ? 'INFERENCE ACTIVE · DAKSH is reasoning locally…' : 'MISSION ANALYSIS ACTIVE · Generating a reviewable plan…');
  try {
    await api('/api/' + type, {prompt: input.value, model: $('model').value});
    input.value = '';
    await load();
    notice();
  } catch (error) { notice(error.message); }
  finally {
    busy = false;
    form.querySelector('button').disabled = false;
    $('scope').disabled = false;
    $('inference-state').textContent = state.models.length ? 'STANDBY' : 'OFFLINE';
  }
}

$('chat-form').onsubmit = event => generate(event, 'chat');
$('task-form').onsubmit = event => generate(event, 'tasks');
function updateClock() { $('clock').textContent = new Date().toLocaleTimeString([], {hour12: false}); }
updateClock();
setInterval(updateClock, 1000);
load().catch(error => notice(error.message));

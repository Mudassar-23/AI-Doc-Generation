/* ============== CONFIG ============== */
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : '';  // Same origin in production

/* ============== STATE ============== */
const state = {
  projectName: '',
  source: 'github',
  aiProvider: 'mock',
  repoUrl: '',
  patToken: '',
  jobId: null,
  pollTimer: null,
  queuePollTimer: null,
  tokenStats: {
    chunksTotal: null,   // total tokens across all chunks (from chunking stage)
    numChunks: null,
    tmplIn: null,        // total input tokens for template filling
    tmplOut: null,       // total output tokens for template filling
    numDocs: null,
  },
};

// Frontend-only: job IDs the user has dismissed from the queue panel
const dismissedJobIds = new Set();

const PIPELINE_STAGES = [
  { id: 'cloning',          title: 'Clone repository' },
  { id: 'analyzing',        title: 'Analyze codebase structure' },
  { id: 'chunking',         title: 'Build semantic chunks' },
  { id: 'llm_analysis',     title: 'AI chunk analysis' },
  { id: 'context_building', title: 'Build structured context' },
  { id: 'template_filling', title: 'Generate documents' },
  { id: 'packaging',        title: 'Package ZIP' },
];

/* ============== SCREEN NAV ============== */
function goTo(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelector('.wrap').classList.toggle('wide', id === 'screen-pipeline');
}

/* ============== ELAPSED TIMER ============== */
let elapsedTimer = null;
function startElapsedTimer() {
  const start = Date.now();
  clearInterval(elapsedTimer);
  const el = document.getElementById('infoElapsed');
  if (el) el.textContent = '00:00';
  elapsedTimer = setInterval(() => {
    const s = Math.floor((Date.now() - start) / 1000);
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    const e = document.getElementById('infoElapsed');
    if (e) e.textContent = `${mm}:${ss}`;
  }, 1000);
}
function stopElapsedTimer() { clearInterval(elapsedTimer); }

/* ============== URL PARSING ============== */
function parseGithubUrl(url) {
  const m = url.match(/github\.com\/([^\/\s]+)\/([^\/\s#?]+)/i);
  if (!m) throw new Error('Could not parse GitHub URL. Expected: https://github.com/owner/repo');
  return { owner: m[1], repo: m[2].replace(/\.git$/, '') };
}
function parseAzureUrl(url) {
  const m = url.match(/dev\.azure\.com\/([^\/\s]+)\/([^\/\s]+)\/_git\/([^\/\s#?]+)/i);
  if (!m) throw new Error('Could not parse Azure DevOps URL. Expected: https://dev.azure.com/org/project/_git/repo');
  return { org: decodeURIComponent(m[1]), project: decodeURIComponent(m[2]), repo: decodeURIComponent(m[3]) };
}

/* ============== STEP 1: NAME ============== */
document.getElementById('toConnect').addEventListener('click', () => {
  const name = document.getElementById('projectName').value.trim();
  if (!name) { document.getElementById('projectName').style.borderColor = 'var(--bad)'; return; }
  state.projectName = name;
  document.getElementById('connectTitle').textContent = `Connect a repository for "${name}"`;
  goTo('screen-connect');
});

/* ============== STEP 2: SOURCE ============== */
function setSource(src) {
  state.source = src;
  document.getElementById('tab-github').classList.toggle('active', src === 'github');
  document.getElementById('tab-azure').classList.toggle('active', src === 'azure');
  const urlInput = document.getElementById('repoUrl');
  urlInput.placeholder = src === 'github' ? 'https://github.com/owner/repo' : 'https://dev.azure.com/org/project/_git/repo';
}

/* ============== STEP 2: START PIPELINE ============== */
document.getElementById('startPipeline').addEventListener('click', async () => {
  const url = document.getElementById('repoUrl').value.trim();
  const errBox = document.getElementById('connectError');
  errBox.style.display = 'none';

  if (!url) { errBox.textContent = 'Enter a repository URL.'; errBox.style.display = 'block'; return; }

  // Validate URL format
  try {
    if (state.source === 'github') parseGithubUrl(url);
    else parseAzureUrl(url);
  } catch (e) {
    errBox.textContent = e.message; errBox.style.display = 'block'; return;
  }

  state.repoUrl = url;
  state.patToken = document.getElementById('patToken') ? document.getElementById('patToken').value.trim() : '';

  // Submit job to backend
  try {
    const response = await fetch(`${API_BASE}/api/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: state.projectName,
        repo_url: state.repoUrl,
        pat_token: state.patToken || null,
        source_type: state.source === 'github' ? 'github' : 'azure_devops',
        ai_provider: state.aiProvider,
      }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || `Server error (${response.status})`);
    }

    const data = await response.json();
    state.jobId = data.job_id;

    // Switch to pipeline screen
    goTo('screen-pipeline');
    setupPipelineUI();
    startElapsedTimer();
    startProgressPolling();
    startQueuePolling();
    log(`Job submitted — ID: ${data.job_id}, queue position: ${data.queue_position}`);

  } catch (e) {
    errBox.textContent = `Failed to submit job: ${e.message}`;
    errBox.style.display = 'block';
  }
});

/* ============== PIPELINE UI ============== */
function setupPipelineUI() {
  const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
  el('infoProject', state.projectName);
  el('infoSource', state.source === 'github' ? 'GitHub' : 'Azure DevOps');

  // Build stepper
  const list = document.getElementById('stepList');
  list.innerHTML = '';
  PIPELINE_STAGES.forEach((step, i) => {
    const row = document.createElement('div');
    row.className = 'step pending';
    row.id = 'step-' + step.id;
    row.innerHTML = `
      <div class="step-badge">${i + 1}</div>
      <div class="step-body">
        <div class="step-title">${step.title}</div>
        <div class="step-meta"></div>
      </div>`;
    list.appendChild(row);
  });

  document.getElementById('logBox').innerHTML = '';
  document.getElementById('retryWrap').style.display = 'none';
  el('statStatus', 'Queued');
  el('statStage', '—');
  el('statProgress', '0%');
  // Reset token stats for new run
  state.tokenStats = { chunksTotal: null, numChunks: null, tmplIn: null, tmplOut: null, numDocs: null };
  const ts = document.getElementById('tokenSection');
  if (ts) ts.style.display = 'none';
  updateTokenUI();
}

function updateStepUI(stageId, status, meta) {
  const row = document.getElementById('step-' + stageId);
  if (!row) return;
  row.className = 'step ' + status;
  const badge = row.querySelector('.step-badge');
  const metaEl = row.querySelector('.step-meta');
  if (status === 'running') badge.innerHTML = '<div class="spin"></div>';
  else if (status === 'done') badge.textContent = '✓';
  else if (status === 'error') badge.textContent = '!';
  else badge.textContent = PIPELINE_STAGES.findIndex(s => s.id === stageId) + 1;
  metaEl.textContent = meta || '';
}

/* ============== TOKEN STATS ============== */
/**
 * Parse "TOKENS:{...} rest of message" prefix written by the stage manager.
 * Returns the JSON object or null if not present.
 */
function parseTokenMeta(message) {
  if (!message || !message.startsWith('TOKENS:')) return null;
  const jsonEnd = message.indexOf(' ', 7);
  const jsonStr = jsonEnd === -1 ? message.slice(7) : message.slice(7, jsonEnd);
  try { return JSON.parse(jsonStr); } catch { return null; }
}

/** Strip the TOKENS:{...} prefix so the stepper shows a clean message. */
function stripTokenPrefix(message) {
  if (!message || !message.startsWith('TOKENS:')) return message;
  const spaceIdx = message.indexOf(' ', 7);
  return spaceIdx === -1 ? '' : message.slice(spaceIdx + 1);
}

/** Update the Token Usage section inside the Live Stats side card. */
function updateTokenUI() {
  const s = state.tokenStats;

  const fmt = (n) => n == null ? '—' : n.toLocaleString();
  const fmtK = (n) => n == null ? '—' : (n >= 1000 ? (n / 1000).toFixed(1) + 'k' : n.toLocaleString());

  const setVal = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };

  setVal('tokChunksTotal', fmtK(s.chunksTotal));
  setVal('tokNumChunks',   fmt(s.numChunks));
  setVal('tokTmplIn',      fmtK(s.tmplIn));
  setVal('tokTmplOut',     fmtK(s.tmplOut));
  setVal('tokTmplTotal',   s.tmplIn != null && s.tmplOut != null ? fmtK(s.tmplIn + s.tmplOut) : '—');

  // Reveal the section once we have any data
  const section = document.getElementById('tokenSection');
  if (section && (s.chunksTotal != null || s.tmplIn != null)) {
    section.style.display = 'block';
  }
}

/* ============== PROGRESS POLLING ============== */
function startProgressPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(pollProgress, 2000);
  pollProgress(); // Immediate first poll
}

function stopProgressPolling() {
  if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
}

async function pollProgress() {
  if (!state.jobId) return;

  try {
    const res = await fetch(`${API_BASE}/api/jobs/${state.jobId}/progress`);
    if (!res.ok) return;
    const data = await res.json();

    // Update status display
    const el = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
    el('statStatus', data.status.charAt(0).toUpperCase() + data.status.slice(1));
    el('statStage', data.current_stage || '—');
    el('statProgress', data.overall_percent + '%');

    // Update each stage — parse token meta from message if present
    for (const stage of data.stages) {
      let status = 'pending';
      if (stage.percent >= 100) status = 'done';
      else if (stage.percent > 0) status = 'running';

      const rawMsg = stage.message || '';
      const tokenMeta = parseTokenMeta(rawMsg);
      const displayMsg = tokenMeta ? stripTokenPrefix(rawMsg) : rawMsg;

      // Absorb token stats into state
      if (tokenMeta) {
        if (stage.stage === 'chunking') {
          state.tokenStats.chunksTotal = tokenMeta.chunks_total ?? state.tokenStats.chunksTotal;
          state.tokenStats.numChunks   = tokenMeta.num_chunks   ?? state.tokenStats.numChunks;
        } else if (stage.stage === 'template_filling') {
          state.tokenStats.tmplIn  = tokenMeta.tmpl_in  ?? state.tokenStats.tmplIn;
          state.tokenStats.tmplOut = tokenMeta.tmpl_out ?? state.tokenStats.tmplOut;
          state.tokenStats.numDocs = tokenMeta.num_docs  ?? state.tokenStats.numDocs;
        }
        updateTokenUI();
      }

      updateStepUI(stage.stage, status, displayMsg);
    }

    // Log current activity
    if (data.message && data.status === 'running') {
      // Only log if message changed
      const logBox = document.getElementById('logBox');
      const lastMsg = logBox.lastElementChild?.textContent || '';
      if (!lastMsg.includes(data.message)) {
        log(data.message);
      }
    }

    // Check if job completed or failed
    if (data.status === 'completed') {
      stopProgressPolling();
      stopElapsedTimer();
      log('Pipeline completed! Documentation ready.', 'ok');
      // Brief delay then show results
      setTimeout(() => showResults(), 1000);
    } else if (data.status === 'failed') {
      stopProgressPolling();
      stopElapsedTimer();

      // Find and mark the failed stage
      for (const stage of data.stages) {
        if (stage.percent > 0 && stage.percent < 100) {
          updateStepUI(stage.stage, 'error', stage.message || 'Failed');
        }
      }

      log('Pipeline failed! Check logs for details.', 'err');
      document.getElementById('retryWrap').style.display = 'block';
    }

  } catch (e) {
    // Silently ignore network errors during polling
  }
}

/* ============== QUEUE POLLING ============== */
function startQueuePolling() {
  if (state.queuePollTimer) clearInterval(state.queuePollTimer);
  state.queuePollTimer = setInterval(pollQueue, 5000);
  pollQueue();
}

function stopQueuePolling() {
  if (state.queuePollTimer) { clearInterval(state.queuePollTimer); state.queuePollTimer = null; }
}

async function pollQueue() {
  try {
    const res = await fetch(`${API_BASE}/api/queue`);
    if (!res.ok) return;
    const data = await res.json();

    const el = document.getElementById('queueCount');
    if (el) el.textContent = `${data.total_jobs} jobs`;

    const list = document.getElementById('liveQueueList');
    if (!list) return;
    list.innerHTML = '';

    // Show up to 10 most recent jobs, excluding frontend-dismissed ones
    const jobs = data.jobs.slice(0, 10).filter(j => !dismissedJobIds.has(j.id));
    for (const job of jobs) {
      const statusClass = 'qs-' + job.status;
      const statusLabel = { queued: 'Queued', running: 'Running', completed: 'Completed', failed: 'Failed' }[job.status] || job.status;
      const isRunning = job.status === 'running';
      const isCurrent = job.id === state.jobId;

      const row = document.createElement('div');
      row.className = 'queue-row';
      row.style.opacity = isCurrent ? '1' : '0.7';
      row.innerHTML = `
        <span class="queue-name">${isCurrent ? '→ ' : ''}#${job.id} ${job.project_name.substring(0, 20)}</span>
        <span class="queue-status ${statusClass}">${isRunning ? '<span class="qdot"></span>' : ''}${statusLabel}${job.queue_position ? ' #' + job.queue_position : ''}</span>
        <button class="queue-delete-btn" title="Dismiss from view" aria-label="Dismiss job #${job.id}">×</button>`;

      // Delete button — frontend only, does not touch the database
      row.querySelector('.queue-delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        dismissedJobIds.add(job.id);
        row.classList.add('queue-row-removing');
        setTimeout(() => row.remove(), 220);
      });

      list.appendChild(row);
    }
  } catch (e) {
    // Silently ignore
  }
}

/* ============== RESULTS ============== */
async function showResults() {
  stopQueuePolling();
  goTo('screen-results');

  try {
    const res = await fetch(`${API_BASE}/api/jobs/${state.jobId}`);
    const job = await res.json();

    document.getElementById('resultsSub').textContent =
      `Generated for "${job.project_name}" from ${job.source_type === 'github' ? 'GitHub' : 'Azure DevOps'} · ${job.repo_url.replace(/^https?:\/\//, '')}`;

    const pillbar = document.getElementById('pillbar');
    pillbar.innerHTML = `
      <div class="pill"><span class="dot" style="background:var(--good)"></span>ZIP ready</div>
      <div class="pill"><span class="dot" style="background:${job.zip_generated ? 'var(--good)' : 'var(--bad)'}"></span>ZIP: ${job.zip_generated ? 'Yes' : 'No'}</div>`;

    // Show file list from logs
    const allFiles = ['PRD.md', 'Architecture-Design.md', 'Database-Design.md', 'API-Specification.md',
                      'Deployment-Guide.md', 'Run-Locally.md', 'Stack-and-Techniques.md', 'Review-and-TODO.md', 'index.json'];
    const fileListEl = document.getElementById('fileList');
    fileListEl.innerHTML = '';
    allFiles.forEach(name => {
      const row = document.createElement('div');
      row.innerHTML = `
        <div class="file-row">
          <div class="file-ico">${name.endsWith('.json') ? '{ }' : '📄'}</div>
          <div>
            <div class="file-name">${name}</div>
            <div class="file-meta">Generated by AI pipeline</div>
          </div>
        </div>`;
      fileListEl.appendChild(row);
    });

  } catch (e) {
    document.getElementById('resultsSub').textContent = 'Documentation generated successfully.';
  }
}

/* ============== DOWNLOAD ============== */
document.getElementById('downloadZip').addEventListener('click', async () => {
  if (!state.jobId) return;
  window.open(`${API_BASE}/api/jobs/${state.jobId}/download`, '_blank');
});

/* ============== RETRY ============== */
document.getElementById('retryBtn').addEventListener('click', async () => {
  if (!state.jobId) return;
  try {
    const res = await fetch(`${API_BASE}/api/jobs/${state.jobId}/retry`, { method: 'POST' });
    if (res.ok) {
      log('Job re-queued for retry...', 'ok');
      document.getElementById('retryWrap').style.display = 'none';
      startElapsedTimer();
      startProgressPolling();
      startQueuePolling();
    } else {
      log('Retry failed — job may not be in failed state.', 'err');
    }
  } catch (e) {
    log(`Retry error: ${e.message}`, 'err');
  }
});

/* ============== LOGGING ============== */
function log(msg, cls) {
  const box = document.getElementById('logBox');
  const line = document.createElement('div');
  if (cls) line.className = cls;
  const t = new Date().toLocaleTimeString();
  line.innerHTML = `<span class="t">${t}</span>${escapeHtml(msg)}`;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

/* ============== RESET ============== */
function resetAll() {
  stopElapsedTimer();
  stopProgressPolling();
  stopQueuePolling();
  state.projectName = ''; state.repoUrl = ''; state.patToken = ''; state.jobId = null;
  state.tokenStats = { chunksTotal: null, numChunks: null, tmplIn: null, tmplOut: null, numDocs: null };
  dismissedJobIds.clear();
  const ts = document.getElementById('tokenSection');
  if (ts) ts.style.display = 'none';
  document.getElementById('projectName').value = '';
  document.getElementById('repoUrl').value = '';
  if (document.getElementById('patToken')) document.getElementById('patToken').value = '';
  goTo('screen-name');
}

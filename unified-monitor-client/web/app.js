/* Vogel-Kamera Web-GUI
 *
 * Wird als einzige Skriptquelle geladen (CSP: script-src 'self'). Deshalb gibt es
 * im HTML keine onclick-Attribute: Knöpfe tragen data-action="…" und werden unten
 * in ACTIONS einer Funktion zugeordnet.
 */
'use strict';

const REFRESH_MS = 5000;
// Stufen des Dauer-Reglers in Sekunden (Server erlaubt 3–600 s)
const DURATIONS = [10, 15, 20, 30, 45, 60, 90, 120, 180, 300, 600];
// Bis zu dieser Größe lädt der Download wie bisher per fetch+Blob (funktioniert auch,
// wenn Chrome das selbstsignierte Zertifikat nur als Ausnahme kennt). Größere Dateien
// würden den Browser-Speicher sprengen und laufen über einen Ticket-Link.
const BLOB_DOWNLOAD_MAX_MB = 200;

// Kamera-Regler: eine Zeile pro Einstellung von /api/camera-settings
const CAM_SETTINGS = [
  { key: 'lens_position', label: '📷 Fokus', min: 0.5, max: 10, step: 0.5,
    hint: '0.5 = 2 m … 10 = 10 cm',
    fmt: v => `${v.toFixed(1)} (≈ ${v > 0 ? Math.round(100 / v) : '∞'} cm)` },
  { key: 'ev', label: '☀️ Belichtung (EV)', min: -2, max: 2, step: 0.5,
    hint: '−2 = dunkel … +2 = hell' },
  { key: 'awb', label: '💡 Weißabgleich (AWB)',
    options: [['auto', 'Auto'], ['daylight', 'Tageslicht'], ['cloudy', 'Bewölkt'],
              ['tungsten', 'Glühbirne'], ['fluorescent', 'Leuchtstoffröhre'], ['indoor', 'Innen']] },
  { key: 'brightness', label: '☀️ Helligkeit', min: -1, max: 1, step: 0.1,
    hint: '−1 = dunkel … +1 = hell' },
  { key: 'contrast', label: '🎨 Kontrast', min: 0.5, max: 2, step: 0.1,
    hint: '0.5 = flach … 1 = normal … 2 = knackig' },
  { key: 'saturation', label: '🌈 Sättigung', min: 0, max: 2, step: 0.1,
    hint: '0 = Graustufen … 1 = normal … 2 = kräftig' },
  { key: 'sharpness', label: '✨ Schärfe', min: 0, max: 2, step: 0.1,
    hint: '0 = keine … 1 = normal … 2 = extra' },
  { key: 'gain', label: '📈 Gain (ISO)', min: 1, max: 8, step: 0.5,
    hint: '1 = normal … 8 = max, nur bei wenig Licht' },
];

let token = sessionStorage.getItem('pi_token') || '';
let _targets = [];          // lokale Kopie der Sync-Ziele
let _detectionMode = false; // wird von renderStatus() aktualisiert
let _detectionRunning = false;
let _recordingsRev = null;  // zuletzt angezeigter Stand der Aufnahmeliste
let _offlineSince = null;

const $ = id => document.getElementById(id);

// ── Hilfsfunktionen ──────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = $('toast');
  el.textContent = msg;
  el.style.borderColor = type === 'error' ? 'rgba(248,81,73,.5)'
                       : type === 'ok'    ? 'rgba(63,185,80,.5)'
                       : 'var(--border)';
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 4000);
}

/** API-Aufruf. Rückgabe: JSON-Objekt, oder null bei Netzfehler / abgelaufenem Login. */
async function apiFetch(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(path, opts);
    if (res.status === 401) { doLogout('Sitzung abgelaufen – bitte neu anmelden.'); return null; }
    return res.json().catch(() => ({}));
  } catch (_) {
    return null;
  }
}

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function setText(id, text) { const el = $(id); if (el) el.textContent = text; }
function setHtml(id, html) { const el = $(id); if (el) el.innerHTML = html; }

/** Status-Pill. Grün = aktiv, grau = Ruhezustand (kein Fehler). */
function pill(active, onText, offText) {
  return `<span class="pill ${active ? 'pill-green' : 'pill-gray'}">${active ? onText : offText}</span>`;
}
function colored(color, text) {
  return `<span style="color:${color};font-weight:600">${text}</span>`;
}
function flashStatus(el, text, ms = 2500) {
  if (!el) return;
  el.textContent = text;
  clearTimeout(el._t);
  if (ms) el._t = setTimeout(() => { el.textContent = ''; }, ms);
}
function fmtDuration(s) {
  if (s < 60) return s + ' s';
  return (s / 60).toLocaleString('de-DE') + ' min';
}
function storeGet(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }
function storeSet(key, val) { try { localStorage.setItem(key, val); } catch (_) { /* privat/gesperrt */ } }

// ── Login ────────────────────────────────────────────────────────────────
async function doLogin() {
  const pw   = $('pw').value;
  const totp = $('totp').value;
  const btn  = $('login-btn');
  if (!pw || !totp) { showLoginErr('Bitte beide Felder ausfüllen.'); return; }
  btn.disabled = true; btn.textContent = 'Anmelden…';
  $('login-error').style.display = 'none';
  try {
    const res = await fetch('/api/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pw, totp }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { showLoginErr(data.error || 'Anmeldung fehlgeschlagen.'); return; }
    token = data.token; sessionStorage.setItem('pi_token', token);
    showDashboard();
  } catch (e) { showLoginErr('Verbindungsfehler: ' + e.message);
  } finally { btn.disabled = false; btn.textContent = 'Anmelden'; }
}

function showLoginErr(msg) {
  const el = $('login-error');
  el.textContent = msg; el.style.display = 'block';
}

function showDashboard() {
  $('login-screen').style.display = 'none';
  $('dashboard').style.display = 'block';
  _recordingsRev = null;
  loadProfiles();
  poll();
}

function doLogout(reason) {
  clearTimeout(_pollTimer);
  stopPreview();
  closePlayer();
  token = '';
  sessionStorage.removeItem('pi_token');
  $('dashboard').style.display = 'none';
  $('login-screen').style.display = 'flex';
  $('pw').value = ''; $('totp').value = '';
  if (typeof reason === 'string') showLoginErr(reason);
}

// ── Abfrage-Schleife ─────────────────────────────────────────────────────
// Eine Abfrage nach der anderen (kein setInterval → keine Überlappung bei langsamer
// Verbindung) und nur, solange der Tab sichtbar ist.
let _pollTimer = null;
let _pollBusy = false;

async function poll() {
  clearTimeout(_pollTimer);
  if (!token || document.hidden || _pollBusy) return;
  _pollBusy = true;
  try { await refreshAll(); } finally { _pollBusy = false; }
  if (token && !document.hidden) _pollTimer = setTimeout(poll, REFRESH_MS);
}

async function refreshAll(forceRecordings = false) {
  const data = await apiFetch('/api/status');
  if (!token) return;
  if (!data) { setOffline(true); return; }
  setOffline(false);
  renderStatus(data);
  // Aufnahmeliste nur neu laden, wenn sie sich geändert hat
  if (forceRecordings || data.recordings_rev == null || data.recordings_rev !== _recordingsRev) {
    if (await fetchRecordings()) _recordingsRev = data.recordings_rev ?? null;
  }
}

function setOffline(offline) {
  const banner = $('conn-banner');
  if (offline) {
    if (!_offlineSince) _offlineSince = new Date();
    banner.textContent = '⚠ Keine Verbindung zur Kamera seit '
      + _offlineSince.toLocaleTimeString('de-DE') + ' – die angezeigten Werte sind veraltet.';
    banner.style.display = 'block';
    setHtml('s-health', colored('#ef4444', '✗ Keine Verbindung'));
  } else {
    _offlineSince = null;
    banner.style.display = 'none';
  }
  $('main').classList.toggle('stale', offline);
}

// ── Status ───────────────────────────────────────────────────────────────
function renderPowerbank(pb) {
  const group = $('pb-group');
  if (!Object.keys(pb).length) { group.style.display = 'none'; return; }
  group.style.display = 'block';
  const W = v => v != null ? v.toFixed(1) + ' W' : '–';
  if (pb.battery_percent != null) {
    const p = pb.battery_percent;
    setHtml('s-pb-battery', colored(p <= 10 ? '#ef4444' : p <= 25 ? '#f97316' : '#22c55e', p + ' %'));
  } else { setText('s-pb-battery', '–'); }
  const info = $('s-pb-info');
  const t = pb.updated_at
    ? new Date(pb.updated_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : null;
  if (pb.ok === false) {
    info.textContent = '⚠️ nicht erreichbar' + (t ? ' · Stand ' + t : '');
    info.title = pb.error || '';
  } else {
    info.textContent = t ? 'Stand ' + t : 'wird abgefragt …';
    info.title = '';
  }
  setText('s-pb-out', W(pb.total_output_w));
  setText('s-pb-in',  W(pb.total_input_w));
  const ports = [['usb_c1', 'C1'], ['usb_c2', 'C2'], ['usb_a', 'A']]
    .filter(([k]) => pb[k] && pb[k].mode !== 'off')
    .map(([k, n]) => `${n} ${pb[k].power_w.toFixed(1)} W`);
  setText('s-pb-ports', ports.join(' · '));
  setText('s-pb-temp', pb.temperature_c != null ? pb.temperature_c + ' °C' : '–');
}

function renderHailo(data) {
  const hw = data.hailo_hw || {};
  const hailoActive = data.detection_running && data.active_engine === 'hailo';
  setHtml('s-hailo', pill(hailoActive, '🔬 Aktiv', 'Inaktiv'));
  const hwEl = $('s-hailo-hw');
  if (hw.device_present) {
    const parts = [];
    if (hw.driver_version) parts.push('Treiber ' + hw.driver_version);
    if (hw.fw_version)     parts.push('FW ' + hw.fw_version);
    hwEl.textContent = parts.join(' · ');
    hwEl.style.display = 'block';
  } else {
    hwEl.style.display = 'none';
  }
  if (hw.npu_temp_c != null) {
    const t = hw.npu_temp_c;
    setHtml('s-npu-temp', colored(t >= 80 ? '#ef4444' : t >= 65 ? '#f97316' : '#22c55e', t.toFixed(1) + ' °C'));
  } else { setText('s-npu-temp', '–'); }
  setText('s-npu-clock', hw.nn_clock_mhz != null ? hw.nn_clock_mhz + ' MHz' : '–');
  if (hw.throttle_level != null) {
    const lvl = hw.throttle_level;
    if (lvl < 0) {
      setHtml('s-throttle', colored('#22c55e', '– Normal'));
    } else {
      const mhz = hw.nn_clock_mhz != null ? ' ' + hw.nn_clock_mhz + ' MHz' : '';
      setHtml('s-throttle', colored(lvl === 0 ? '#f97316' : '#ef4444', `L${lvl}${mhz}`));
    }
  } else if (hw.throttle_zone != null) {
    const zones = ['✅ Normal', '⚠️ Warm', '🔴 Kritisch'];
    const cols  = ['#22c55e', '#f97316', '#ef4444'];
    const z = hw.throttle_zone;
    setHtml('s-throttle', colored(cols[z] || '#ef4444', zones[z] || 'Zone ' + Number(z)));
  } else { setText('s-throttle', '–'); }
}

function renderProgress(prefix, running, progress, duration, remaining) {
  const wrap = $(prefix + '-progress-wrap');
  if (running && progress != null) {
    wrap.style.display = 'block';
    $(prefix + '-progress').value = progress;
    setText(prefix + '-progress-label', progress + ' %');
    const dur = duration || 0, rem = remaining ?? 0;
    setText(prefix + '-progress-time', `${dur - rem} s / ${dur} s (≈ ${rem} s verbleibend)`);
  } else {
    wrap.style.display = 'none';
    $(prefix + '-progress').value = 0;
  }
}

function renderStatus(data) {
  setHtml('s-health', colored('#22c55e', '✓ Healthy'));
  const errBox = $('error-box');
  if (data.last_error) { errBox.textContent = '⚠ Letzter Fehler: ' + data.last_error; errBox.style.display = 'block'; }
  else errBox.style.display = 'none';
  $('hw-error-box').style.display = data.camera_hw_error ? 'block' : 'none';

  _detectionRunning = !!data.detection_running;
  _detectionMode    = !!data.detection_mode;
  setHtml('s-detect',   pill(data.detection_running, 'Aktiv', 'Gestoppt'));
  setHtml('s-det-mode', pill(data.detection_mode, '🤖 Automatik', 'Manuell'));
  setHtml('s-rec',      pill(data.recording_running, '⏺ Läuft', 'Bereit'));
  renderHailo(data);
  renderPowerbank(data.powerbank || {});

  renderLastDetection(data);
  const todayRec = data.today_recordings ?? data.birds_recorded;
  setText('s-birds', todayRec != null ? String(todayRec) : '–');
  const now = new Date();
  setText('s-birds-date',
    now.toLocaleDateString('de-DE', { weekday: 'short' }).replace('.', '') + ' '
    + now.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }));

  if (data.detection_target != null) {
    const icons = { bird: '🐦', person: '🧍', dog: '🐕', cat: '🐈', all4: '🐦🧍🐕🐈' };
    const names = { bird: 'Vogel', person: 'Person', dog: 'Hund', cat: 'Katze', all4: 'Alle 4' };
    const icon = icons[data.detection_target] || '🎯';
    const name = names[data.detection_target] || data.detection_target;
    const thr  = data.detection_threshold != null ? (data.detection_threshold * 100).toFixed(0) + ' %' : '';
    setHtml('s-target', `${icon} ${escHtml(name)}<br><small style="color:var(--muted)">${thr} Konfidenz</small>`);
    const rb = $('det-target-' + data.detection_target);
    if (rb && !rb.checked) rb.checked = true;
  }
  if (data.active_engine) {
    const sel = $('engine-select');
    if (sel.value !== data.active_engine) sel.value = data.active_engine;
  }
  if (data.detection_threshold != null) {
    const sl = $('det-threshold');
    if (!sl.matches(':active') && parseFloat(sl.value) !== data.detection_threshold) {
      sl.value = data.detection_threshold;
      setText('det-threshold-val', data.detection_threshold.toFixed(2));
    }
  }

  // Ein Knopf für Start/Stopp, passend zum aktuellen Zustand
  const detBtn = $('det-toggle-btn');
  if (!detBtn._busy) {
    detBtn.disabled = false;
    detBtn.className = 'btn ' + (_detectionMode ? 'btn-danger' : 'btn-success');
    detBtn.textContent = _detectionMode ? '■ Detection-Modus stoppen' : '▶ Detection-Modus starten';
  }

  const blocked = _detectionMode;
  const anyRunning = data.recording_running || data.audio_running;
  $('rec-btn').disabled = anyRunning || blocked;
  $('aud-btn').disabled = anyRunning || blocked;
  $('rec-kill-btn').style.display = anyRunning ? 'inline-flex' : 'none';
  $('rec-blocked-info').style.display = blocked ? 'block' : 'none';
  $('det-mode-info').style.display = blocked ? 'block' : 'none';
  renderProgress('rec', data.recording_running, data.recording_progress,
                 data.recording_duration, data.recording_remaining);
  renderProgress('aud', data.audio_running, data.audio_progress,
                 data.audio_duration, data.audio_remaining);
  const n = data.birds_recorded;
  setText('det-birds-inline', n ? `(${n} Aufnahme${n !== 1 ? 'n' : ''})` : '');

  const badge = $('pending-badge');
  if (data.pending > 0) { badge.textContent = data.pending; badge.style.display = 'inline'; }
  else badge.style.display = 'none';

  const sys = data.system || {};
  setText('s-cpu', sys.cpu_percent != null ? sys.cpu_percent.toFixed(0) + ' %' : '–');
  if (sys.cpu_temp != null) {
    const t = sys.cpu_temp;
    setHtml('s-temp', colored(t >= 75 ? '#ef4444' : t >= 60 ? '#f97316' : '#22c55e', t.toFixed(1) + ' °C'));
  } else { setText('s-temp', '–'); }
  if (sys.load_1min != null) setText('s-load', `${sys.load_1min} / ${sys.load_5min} / ${sys.load_15min}`);
  if (sys.mem_used_mb && sys.mem_total_mb) setText('s-mem', `${sys.mem_used_mb} / ${sys.mem_total_mb} MB`);
  if (sys.disk_free_gb != null) setText('s-disk', sys.disk_free_gb + ' GB frei');
  if (sys.container_ram_mb != null) setText('s-docker-ram', sys.container_ram_mb + ' MB');
  if (sys.net_rx_kbs != null) setText('s-net-rx', sys.net_rx_kbs + ' KB/s');
  if (sys.net_tx_kbs != null) setText('s-net-tx', sys.net_tx_kbs + ' KB/s');
  if (sys.uptime_days != null) {
    const pad = v => String(v).padStart(2, '0');
    setText('s-uptime', (sys.uptime_days > 0 ? sys.uptime_days + 'T ' : '')
      + pad(sys.uptime_hours) + 'h ' + pad(sys.uptime_minutes) + 'm');
  }

  syncCameraControls(data);
  setText('last-update', 'Update: ' + new Date().toLocaleTimeString('de-DE'));
  if (data.version) setText('gui-version', 'v' + data.version);
  renderGrafanaLink(data.grafana_url, data.grafana_port);
}

const CLASS_NAMES = { bird: 'Vogel', person: 'Person', dog: 'Hund', cat: 'Katze' };
function className(c) { return CLASS_NAMES[c] || (c ? c.charAt(0).toUpperCase() + c.slice(1) : '?'); }
function percent(v) { return (v * 100).toFixed(0) + '\u202F%'; }

/** Kachel „Objekt erkannt": letzte Auslösung (übersteht Neustarts) und darunter, was die
 *  Kamera gerade sieht, wenn es unter der Schwelle bleibt. */
function renderLastDetection(data) {
  const d = data.last_detection;
  if (d) {
    const conf = d.conf != null ? percent(d.conf) : '';
    // Datum nur nennen, wenn die Auslösung nicht von heute ist
    const today = new Date().toLocaleDateString('sv-SE');   // JJJJ-MM-TT in Ortszeit
    let when = d.time || '';
    if (d.date && d.date !== today) {
      const [y, m, day] = d.date.split('-');
      when = `${day}.${m}.${y} ${when}`;
    }
    setHtml('s-last-det', `${escHtml(className(d.class))}\u00A0${escHtml(conf)}<br><small style="color:var(--muted)">${escHtml(when)}</small>`);
  } else {
    setText('s-last-det', '–');
  }
  const seenEl = $('s-seen');
  const s = data.seen_detection;
  if (s) {
    seenEl.textContent = `sieht gerade: ${className(s.class)} ${percent(s.conf)} – unter der Schwelle (${percent(s.threshold)})`;
    seenEl.title = 'Die Kamera erkennt das Ziel, aber nicht sicher genug für eine Aufnahme. Confidence senken, wenn das ein Treffer sein sollte.';
    seenEl.style.display = 'block';
  } else {
    seenEl.style.display = 'none';
  }
}

/** Knopf „Monitoring" in der Kopfzeile: feste Adresse, oder Grafana auf diesem Pi
 *  (dann der Rechnername, unter dem die GUI gerade aufgerufen wird, plus Port). */
function renderGrafanaLink(url, port) {
  const link = $('grafana-link');
  if (!url && Number.isInteger(port) && port > 0) {
    url = `http://${window.location.hostname}:${port}/d/vogel-kamera`;
  }
  let ok = false;
  try { ok = !!url && ['http:', 'https:'].includes(new URL(url).protocol); } catch (_) { /* ungültig */ }
  if (ok && link.getAttribute('href') !== url) link.href = url;
  link.style.display = ok ? 'inline-flex' : 'none';
}

// ── Detection ────────────────────────────────────────────────────────────
async function toggleDetectionMode(btn) {
  btn._busy = true; btn.disabled = true;
  try {
    if (_detectionMode) {
      const d = await apiFetch('/api/detection/mode/stop', 'POST');
      if (d?.success) {
        const n = d.birds_recorded || 0;
        toast(`⏹ Detection-Modus gestoppt (${n} Aufnahme${n !== 1 ? 'n' : ''})`, 'ok');
      } else toast('❌ Fehler beim Stoppen', 'error');
    } else {
      const rb = document.querySelector('input[name="det-target"]:checked');
      const target = rb ? rb.value : 'bird';
      const label = { bird: 'Vogelerkennung', person: 'Menscherkennung', dog: 'Hundeerkennung',
                      cat: 'Katzenerkennung', all4: 'Alle-4-Erkennung' }[target] || (target + '-Erkennung');
      const d = await apiFetch('/api/detection/mode/start', 'POST');
      if (d?.success) toast(`✅ Detection-Modus gestartet – Aufnahme bei ${label}`, 'ok');
      else toast('❌ ' + (d?.error || 'Fehler beim Starten'), 'error');
    }
  } finally {
    btn._busy = false;
    await refreshAll();
  }
}

async function switchEngine(engine) {
  const statusEl = $('engine-status');
  statusEl.textContent = '⏳ Wechsle...';
  const d = await apiFetch('/api/detection-engine', 'POST', { engine });
  if (d?.success) {
    toast(d.changed ? `🔄 Engine gewechselt auf ${engine}` : `✔ Bereits aktiv: ${engine}`, 'ok');
    statusEl.textContent = '';
  } else {
    toast('❌ ' + (d?.error || 'Engine-Wechsel fehlgeschlagen'), 'error');
    statusEl.textContent = '⚠ Fehler';
  }
  refreshAll();
}

async function applyDetectionSettings() {
  const rb = document.querySelector('input[name="det-target"]:checked');
  const target    = rb ? rb.value : 'bird';
  const threshold = parseFloat($('det-threshold').value);
  const statusEl  = $('det-settings-status');
  flashStatus(statusEl, '⏳ Speichere…', 0);
  const d = await apiFetch('/api/detection-settings', 'POST', { target_class: target, threshold });
  if (d?.success) {
    flashStatus(statusEl, '✔ Gespeichert');
  } else {
    toast('❌ ' + (d?.error || 'Einstellung konnte nicht gespeichert werden'), 'error');
    flashStatus(statusEl, '⚠ Fehler', 0);
  }
  refreshAll();
}

// ── Aufnahme ─────────────────────────────────────────────────────────────
function selectedDuration() {
  return DURATIONS[parseInt($('rec-dur').value, 10)] ?? 15;
}
function updateDurationLabel() {
  setText('rec-dur-label', fmtDuration(selectedDuration()));
}
/** Stellt den Regler auf die Stufe, die der gespeicherten Dauer am nächsten liegt. */
function setDuration(seconds) {
  let best = 0;
  DURATIONS.forEach((d, i) => { if (Math.abs(d - seconds) < Math.abs(DURATIONS[best] - seconds)) best = i; });
  $('rec-dur').value = best;
  updateDurationLabel();
}
let _recSaveTimer = null;
/** Speichert Profil + Dauer. Gebündelt, weil ein Regler per Tastatur bei jedem Schritt feuert. */
function saveRecSettings() {
  clearTimeout(_recSaveTimer);
  _recSaveTimer = setTimeout(() => {
    apiFetch('/api/rec-settings', 'POST', { profile: $('rec-profile').value, duration: selectedDuration() });
  }, 300);
}

async function startRecord(btn) {
  btn.disabled = true;
  const d = await apiFetch('/api/record', 'POST',
                           { duration: selectedDuration(), profile: $('rec-profile').value });
  if (d?.success) toast(`⏺ ${d.message || 'Aufnahme gestartet'}`, 'ok');
  else { toast('❌ ' + (d?.error || 'Aufnahme fehlgeschlagen'), 'error'); btn.disabled = false; }
  refreshAll();
}

async function startAudio(btn) {
  btn.disabled = true;
  const d = await apiFetch('/api/record/audio', 'POST', { duration: selectedDuration() });
  if (d?.success) toast('🎤 ' + (d.message || 'Audio-Aufnahme gestartet'), 'ok');
  else { toast('❌ ' + (d?.error || 'Audio-Aufnahme fehlgeschlagen'), 'error'); btn.disabled = false; }
  refreshAll();
}

async function killRecord(btn) {
  if (!confirm('Hängenden Aufnahme-/Audio-Prozess jetzt sofort beenden?')) return;
  btn.disabled = true;
  const d = await apiFetch('/api/record/kill', 'POST', {});
  if (d?.success) toast('⛔ Prozess beendet', 'ok');
  else toast('❌ ' + (d?.error || 'Kill fehlgeschlagen'), 'error');
  btn.disabled = false;
  refreshAll();
}

async function loadProfiles() {
  const profiles = await apiFetch('/api/profiles');
  if (!profiles) return;
  const sel = $('rec-profile');
  sel.replaceChildren(...Object.entries(profiles).map(([k, v]) => new Option(v.label, k)));
  const settings = await apiFetch('/api/rec-settings');
  if (settings?.profile && profiles[settings.profile]) sel.value = settings.profile;
  if (settings?.duration) setDuration(settings.duration);
}

async function startConvert(btn) {
  btn.disabled = true;
  const d = await apiFetch('/api/convert', 'POST');
  toast(d?.success ? '🔄 Konvertierung läuft – alle ausstehenden H264 werden verarbeitet'
                   : '❌ ' + (d?.error || 'Fehler'), d?.success ? 'ok' : 'error');
  setTimeout(() => { btn.disabled = false; refreshAll(true); }, 3000);
}

async function startTransfer(btn) {
  btn.disabled = true;
  const d = await apiFetch('/api/transfer', 'POST');
  toast(d?.success ? '📤 Übertragung gestartet – alle MP4s werden gesendet'
                   : '❌ ' + (d?.error || 'Fehler'), d?.success ? 'ok' : 'error');
  setTimeout(() => { btn.disabled = false; }, 4000);
}

// ── Kamera-Regler (aus CAM_SETTINGS erzeugt) ─────────────────────────────
function camLabel(def, value) {
  return def.fmt ? def.fmt(value) : value.toFixed(1);
}

function buildCameraControls() {
  const box = $('cam-settings');
  for (const def of CAM_SETTINGS) {
    const id = 'cam-' + def.key;
    const row = document.createElement('div');
    row.className = 'cam-row';
    const label = document.createElement('label');
    label.htmlFor = id; label.textContent = def.label + ':';
    const status = document.createElement('span');
    status.className = 'cam-status'; status.id = id + '-status';
    let input;
    if (def.options) {
      input = document.createElement('select');
      input.append(...def.options.map(([v, t]) => new Option(t, v)));
      row.append(label, input, status);
    } else {
      input = document.createElement('input');
      input.type = 'range';
      input.min = def.min; input.max = def.max; input.step = def.step;
      const val = document.createElement('span');
      val.className = 'cam-val'; val.id = id + '-val';
      const hint = document.createElement('span');
      hint.className = 'cam-hint'; hint.textContent = '(' + def.hint + ')';
      input.addEventListener('input', () => { val.textContent = camLabel(def, parseFloat(input.value)); });
      row.append(label, input, val, hint, status);
    }
    input.id = id;
    input.addEventListener('change', () => saveCameraSetting(def, input, status));
    box.append(row);
  }
}

async function saveCameraSetting(def, input, statusEl) {
  const value = def.options ? input.value : parseFloat(input.value);
  flashStatus(statusEl, '…', 0);
  const res = await apiFetch('/api/camera-settings', 'POST', { [def.key]: value });
  if (res?.success) flashStatus(statusEl, '✓ gespeichert');
  else flashStatus(statusEl, '✗ Fehler', 0);
}

/** Übernimmt die Kamera-Werte aus /api/status – außer der Regler wird gerade bedient. */
function syncCameraControls(data) {
  for (const def of CAM_SETTINGS) {
    const value = data[def.key];
    if (value == null) continue;
    const input = $('cam-' + def.key);
    if (!input || input.matches(':active') || document.activeElement === input) continue;
    if (def.options) {
      if (input.value !== value) input.value = value;
    } else {
      if (parseFloat(input.value) !== value) input.value = value;
      setText('cam-' + def.key + '-val', camLabel(def, value));
    }
  }
}

// ── Aufnahmeliste ────────────────────────────────────────────────────────
async function fetchRecordings() {
  const list = await apiFetch('/api/recordings');
  if (!list) return false;
  const tbody = $('recordings-body');
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Keine Aufnahmen vorhanden</td></tr>';
    return true;
  }
  let lastDate = '';
  tbody.innerHTML = list.map(r => {
    let hdr = '';
    const d = (r.date || '').split(' ')[0];
    if (d && d !== lastDate) {
      lastDate = d;
      let label = d;
      try {
        label = new Date(d + 'T00:00:00').toLocaleDateString('de-DE',
          { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
      } catch (_) { /* Datum bleibt roh */ }
      hdr = `<tr class="date-header"><td colspan="4">📅 ${escHtml(label)}</td></tr>`;
    }
    const isAudio = r.type === 'audio';
    const path = escHtml(r.rel_path || r.name);
    const attrs = `data-path="${path}" data-type="${isAudio ? 'audio' : 'video'}" data-size="${Number(r.size_mb) || 0}"`;
    const badge = isAudio ? '<span class="type-badge type-audio">🎵 Audio</span>'
                          : '<span class="type-badge type-video">🎬 Video</span>';
    return `${hdr}<tr>
      <td>${badge}${escHtml(r.name)}</td>
      <td class="size-col">${escHtml(r.size_mb)} MB</td>
      <td>${escHtml((r.created || '').slice(11))}</td>
      <td><div class="row-actions">
        <button class="btn btn-neutral btn-small" data-action="play" ${attrs}>▶ Abspielen</button>
        <button class="btn btn-neutral btn-small" data-action="download" ${attrs}>⬇ Download</button>
        <button class="btn btn-danger btn-small" data-action="delete" ${attrs}>🗑 Löschen</button>
      </div></td>
    </tr>`;
  }).join('');
  return true;
}

/** Holt einen kurzlebigen Link für genau eine Datei (siehe /api/download-ticket). */
async function fileTicket(relPath) {
  const t = await apiFetch('/api/download-ticket', 'POST', { p: relPath });
  if (!t?.url) { toast('❌ ' + (t?.error || 'Datei nicht erreichbar'), 'error'); return null; }
  return t.url;
}

function triggerDownload(href, filename) {
  const a = document.createElement('a');
  a.href = href; a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function downloadFile(btn) {
  const relPath = btn.dataset.path;
  const filename = relPath.split('/').pop() || 'recording.mp4';
  btn.disabled = true;
  try {
    if (parseFloat(btn.dataset.size) > BLOB_DOWNLOAD_MAX_MB) {
      // Große Datei: der Browser lädt selbst (Fortschritt im Download-Manager, kein RAM-Verbrauch)
      const url = await fileTicket(relPath);
      if (url) triggerDownload(url + '&dl=1', filename);
      return;
    }
    const resp = await fetch('/api/download?p=' + encodeURIComponent(relPath),
                             { headers: { 'Authorization': 'Bearer ' + token } });
    if (!resp.ok) {
      let msg = 'HTTP ' + resp.status;
      try { msg = (await resp.json()).error || msg; } catch (_) { /* keine JSON-Antwort */ }
      toast('❌ Download-Fehler: ' + msg, 'error');
      return;
    }
    const href = URL.createObjectURL(await resp.blob());
    triggerDownload(href, filename);
    setTimeout(() => URL.revokeObjectURL(href), 10000);
  } catch (e) {
    toast('❌ Download-Fehler: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function deleteFile(btn) {
  const relPath = btn.dataset.path;
  const extra = btn.dataset.type === 'audio' ? '' : '\n(inkl. H264-Quelldatei und WAV falls vorhanden)';
  if (!confirm(`"${relPath}" wirklich löschen?${extra}`)) return;
  const d = await apiFetch('/api/delete', 'POST', { p: relPath });
  if (d?.success) {
    toast('🗑 Gelöscht: ' + (d.deleted || []).join(', '), 'ok');
    refreshAll(true);
  } else {
    toast('❌ ' + (d?.error || 'Fehler beim Löschen'), 'error');
  }
}

// ── Dialoge (Hilfe, Player) ──────────────────────────────────────────────
let _dialogReturnFocus = null;

function openDialog(overlayId) {
  _dialogReturnFocus = document.activeElement;
  const overlay = $(overlayId);
  overlay.classList.add('open');
  overlay.querySelector('[role="dialog"]').focus();
}
function closeDialog(overlayId) {
  const overlay = $(overlayId);
  if (!overlay.classList.contains('open')) return;
  overlay.classList.remove('open');
  if (_dialogReturnFocus?.isConnected) _dialogReturnFocus.focus();
  _dialogReturnFocus = null;
}

async function playFile(btn) {
  const relPath = btn.dataset.path;
  const url = await fileTicket(relPath);
  if (!url) return;
  const media = document.createElement(btn.dataset.type === 'audio' ? 'audio' : 'video');
  media.controls = true; media.autoplay = true; media.playsInline = true;
  media.src = url;
  media.addEventListener('error', () => toast('❌ Wiedergabe nicht möglich – bitte herunterladen', 'error'));
  setText('player-title', relPath.split('/').pop());
  $('player-body').replaceChildren(media);
  openDialog('player-overlay');
}

function closePlayer() {
  const media = $('player-body').firstElementChild;
  if (media) { media.pause(); media.removeAttribute('src'); media.load(); }
  $('player-body').replaceChildren();
  closeDialog('player-overlay');
}

// ── Einstellungen: Sync-Ziele ────────────────────────────────────────────
function toggleSettings(btn) {
  const p = $('settings-panel');
  const show = p.style.display !== 'block';
  p.style.display = show ? 'block' : 'none';
  btn.setAttribute('aria-expanded', String(show));
  if (show) loadSettings();
}

async function loadSettings() {
  const d = await apiFetch('/api/settings');
  if (!d) return;
  _targets = d.targets || [];
  renderTargets();
}

function renderTargets() {
  const c = $('targets-container');
  if (!_targets.length) {
    c.innerHTML = '<p style="color:var(--muted);font-size:.875rem;margin-bottom:.75rem;">Noch keine Sync-Ziele konfiguriert. Klicke auf „＋ Ziel hinzufügen".</p>';
    return;
  }
  // Eingaben landen über data-field per Event-Delegation in _targets (siehe unten)
  c.innerHTML = _targets.map((t, i) => `
    <div class="target-card" id="tc-${i}" data-idx="${i}">
      <div class="target-card-header">
        <input class="name-input" type="text" data-field="name" aria-label="Name des Ziels"
               value="${escHtml(t.name || 'Ziel ' + (i + 1))}" placeholder="Name des Ziels">
        <label class="toggle-label">
          <input type="checkbox" data-field="enabled" ${t.enabled !== false ? 'checked' : ''}>
          Aktiv
        </label>
        <button class="btn btn-danger btn-small" data-action="remove-target" aria-label="Ziel entfernen">✕</button>
      </div>
      <div class="settings-grid">
        <div class="field">
          <label for="t-host-${i}">Host / IP</label>
          <input type="text" id="t-host-${i}" data-field="host" value="${escHtml(t.host || '')}" placeholder="192.168.1.100">
        </div>
        <div class="field">
          <label for="t-user-${i}">SSH Benutzer</label>
          <input type="text" id="t-user-${i}" data-field="user" value="${escHtml(t.user || '')}" placeholder="benutzer">
        </div>
        <div class="field" style="grid-column:span 2">
          <label for="t-path-${i}">Ziel-Pfad (Remote)</label>
          <input type="text" id="t-path-${i}" data-field="path" value="${escHtml(t.path || '')}" placeholder="/home/benutzer/Videos/">
        </div>
        <div class="field" style="grid-column:span 2">
          <label for="t-key-${i}">SSH Private Key <span style="color:var(--muted);font-weight:400">${t.key_set ? '(gespeichert – leer lassen = unverändert)' : '(leer lassen = Key-Auth deaktiviert)'}</span></label>
          <textarea id="t-key-${i}" data-field="ssh_key" placeholder="-----BEGIN OPENSSH PRIVATE KEY-----&#10;...&#10;-----END OPENSSH PRIVATE KEY-----"></textarea>
        </div>
      </div>
      <div class="action-row" style="margin-top:.5rem;">
        <button class="btn btn-neutral" style="font-size:.82rem;padding:.3rem .7rem;" data-action="test-target">🔌 Testen</button>
        <span class="test-result-inline" id="tr-${i}"></span>
      </div>
    </div>
  `).join('');
}

function targetIndex(el) {
  return parseInt(el.closest('[data-idx]').dataset.idx, 10);
}

function addTarget() {
  _targets.push({ name: `Ziel ${_targets.length + 1}`, host: '', user: '', path: '', enabled: true });
  renderTargets();
  $(`tc-${_targets.length - 1}`)?.scrollIntoView({ behavior: 'smooth' });
}

function removeTarget(btn) {
  _targets.splice(targetIndex(btn), 1);
  renderTargets();
}

async function saveAllTargets(btn) {
  const status = $('save-status');
  btn.disabled = true; status.textContent = 'Speichert…';
  const d = await apiFetch('/api/settings/targets', 'POST', { targets: _targets });
  btn.disabled = false;
  if (d?.success) {
    toast('💾 Sync-Ziele gespeichert', 'ok');
    _targets = d.targets;
    renderTargets();
    flashStatus(status, '✓ Gespeichert', 3000);
  } else {
    toast('❌ ' + (d?.error || 'Fehler beim Speichern'), 'error');
    status.textContent = '';
  }
}

async function testTarget(btn) {
  const i = targetIndex(btn);
  const res = $(`tr-${i}`);
  btn.disabled = true; btn.textContent = '🔌 Teste…';
  res.style.display = 'none';
  // Erst speichern, damit der Key auf dem Server ist
  await apiFetch('/api/settings/targets', 'POST', { targets: _targets });
  const d = await apiFetch('/api/settings/test', 'POST', { target_id: i });
  btn.disabled = false; btn.textContent = '🔌 Testen';
  res.style.display = 'inline-block';
  res.className = 'test-result-inline ' + (d?.success ? 'test-ok' : 'test-err');
  res.textContent = d?.message || d?.error || 'Keine Antwort';
}

// ── Live-Vorschau ────────────────────────────────────────────────────────
// Das Panel ist ausgeblendet, solange Hailo die Kamera exklusiv belegt. Der Code
// bleibt erhalten, damit die Vorschau später wieder aktiviert werden kann.
let _previewActive = false;
let _previewTimer  = null;
let _previewErrCnt = 0;

function togglePreview() {
  if (_previewActive) { stopPreview(); return; }
  _previewActive = true;
  _previewErrCnt = 0;
  setText('preview-toggle-btn', '⏹ Vorschau stoppen');
  const placeholder = $('preview-placeholder');
  placeholder.textContent = '📷 Bild wird geladen…';
  placeholder.style.display = 'flex';
  $('preview-img').style.display = 'none';
  pollFrame();
}

function stopPreview() {
  if (!_previewActive) return;
  _previewActive = false;
  clearTimeout(_previewTimer);
  const img = $('preview-img');
  if (img.src && img.src.startsWith('blob:')) URL.revokeObjectURL(img.src);
  img.removeAttribute('src');
  img.style.display = 'none';
  const placeholder = $('preview-placeholder');
  placeholder.style.display = 'flex';
  placeholder.textContent = '📷 Vorschau wird geladen…';
  setText('preview-toggle-btn', '📷 Vorschau starten');
  setText('preview-status', '');
}

async function pollFrame() {
  if (!_previewActive) return;
  const img         = $('preview-img');
  const placeholder = $('preview-placeholder');
  let delay = 250;
  if (document.hidden) {
    delay = 2000;   // Tab im Hintergrund: keine Bilder holen
  } else {
    try {
      const resp = await fetch('/api/snapshot', { headers: { 'Authorization': 'Bearer ' + token } });
      if (resp.ok) {
        const url = URL.createObjectURL(await resp.blob());
        const old = img.src;
        img.src = url;
        if (old && old.startsWith('blob:')) URL.revokeObjectURL(old);
        img.style.display = 'block';
        placeholder.style.display = 'none';
        setText('preview-status', 'Stream aktiv ●');
        _previewErrCnt = 0;
      } else if (resp.status === 503) {
        delay = 2000;   // kein Bild vorhanden → nicht viermal pro Sekunde nachfragen
        if (_detectionRunning) {
          _previewErrCnt = 0;
          setText('preview-status', '🔬 Hailo-Detection aktiv');
          placeholder.textContent = '🔬 Hailo-NPU Detection läuft – kein Live-Frame verfügbar';
          placeholder.style.display = 'flex';
          img.style.display = 'none';
        } else {
          _previewErrCnt++;
          setText('preview-status', 'Warte auf Detection…');
          if (_previewErrCnt > 5) {
            placeholder.textContent = '⚠ Kein Bild – Detection gestartet?';
            placeholder.style.display = 'flex';
            img.style.display = 'none';
          }
        }
      } else if (resp.status === 401) {
        doLogout('Sitzung abgelaufen – bitte neu anmelden.'); return;
      } else {
        setText('preview-status', '⚠ Fehler: HTTP ' + resp.status);
      }
    } catch (e) {
      _previewErrCnt++;
      delay = 2000;
      if (_previewErrCnt > 5) setText('preview-status', '⚠ ' + e.message);
    }
  }
  if (_previewActive) _previewTimer = setTimeout(pollFrame, delay);
}

// ── Ereignisse ───────────────────────────────────────────────────────────
const ACTIONS = {
  'help':           () => openDialog('help-overlay'),
  'close-help':     () => closeDialog('help-overlay'),
  'close-player':   closePlayer,
  'settings':       toggleSettings,
  'logout':         () => doLogout(),
  'add-target':     addTarget,
  'remove-target':  removeTarget,
  'test-target':    testTarget,
  'save-targets':   saveAllTargets,
  'det-toggle':     toggleDetectionMode,
  'record':         startRecord,
  'audio':          startAudio,
  'kill':           killRecord,
  'convert':        startConvert,
  'transfer':       startTransfer,
  'preview-toggle': togglePreview,
  'play':           playFile,
  'download':       downloadFile,
  'delete':         deleteFile,
};

document.addEventListener('click', e => {
  const el = e.target.closest('[data-action]');
  if (el && !el.disabled) { ACTIONS[el.dataset.action]?.(el); return; }
  // Klick auf den abgedunkelten Hintergrund schließt den Dialog
  if (e.target.id === 'help-overlay') closeDialog('help-overlay');
  if (e.target.id === 'player-overlay') closePlayer();
});

document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if ($('player-overlay').classList.contains('open')) closePlayer();
  else closeDialog('help-overlay');
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden) clearTimeout(_pollTimer);
  else poll();
});

function init() {
  buildCameraControls();
  updateDurationLabel();

  $('login-form').addEventListener('submit', e => { e.preventDefault(); doLogin(); });
  $('pw').addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); $('totp').focus(); }
  });

  $('rec-dur').addEventListener('input', updateDurationLabel);
  $('rec-dur').addEventListener('change', saveRecSettings);
  $('rec-profile').addEventListener('change', saveRecSettings);

  $('engine-select').addEventListener('change', e => switchEngine(e.target.value));
  $('det-threshold').addEventListener('input', e => {
    setText('det-threshold-val', parseFloat(e.target.value).toFixed(2));
  });
  $('det-threshold').addEventListener('change', applyDetectionSettings);
  document.querySelectorAll('input[name="det-target"]').forEach(rb => {
    rb.addEventListener('change', applyDetectionSettings);
  });

  // Eingaben in den Sync-Ziel-Karten → _targets
  $('targets-container').addEventListener('input', e => {
    const field = e.target.dataset.field;
    if (!field) return;
    _targets[targetIndex(e.target)][field] =
      e.target.type === 'checkbox' ? e.target.checked : e.target.value;
  });

  // Auf-/Zugeklappt merken; auf dem Handy startet „System & Hardware" zugeklappt
  for (const id of ['system-details', 'cam-details']) {
    const el = $(id);
    const saved = storeGet('vk_open_' + id);
    if (saved != null) el.open = saved === '1';
    else if (id === 'system-details') el.open = window.innerWidth > 600;
    el.addEventListener('toggle', () => storeSet('vk_open_' + id, el.open ? '1' : '0'));
  }

  if (token) showDashboard();
}

init();

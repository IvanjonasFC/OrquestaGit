import { Command, open as openExternal } from '@tauri-apps/plugin-shell';

// invoke solo se usa dentro de Tauri; import dinamico para no romper en navegador.
let _invoke = null;

// ---------------------------------------------------------------------------
// Deteccion de entorno
// ---------------------------------------------------------------------------
const IN_TAURI = typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;

// Estado global
let SCRIPT = 'src/core/orquesta_core.py';   // fallback relativo (dev)
let ROOT = null;
let PYBIN = null;                            // se resuelve al primer uso
let globalGithubPath = '';

// ---------------------------------------------------------------------------
// Navegacion de pestañas
// ---------------------------------------------------------------------------
const tabs = document.querySelectorAll('.nav-item');
const contents = document.querySelectorAll('.tab-content');
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    contents.forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    const el = document.getElementById(tab.dataset.tab);
    if (el) el.classList.add('active');
    
    // Close side panel when navigating away from dashboard
    if (tab.dataset.tab !== 'dashboard') {
      const sp = document.getElementById('repo-detail-panel');
      if (sp) { sp.classList.remove('open'); currentDetailRepo = null; }
    }
    
    onTabShown(tab.dataset.tab);
  });
});

// Side Panel Tabs logic
const spTabs = document.querySelectorAll('.sp-tab');
const spContents = document.querySelectorAll('.sp-tab-content');
spTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    spTabs.forEach(t => t.classList.remove('active'));
    spContents.forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    const el = document.getElementById(tab.dataset.sptab);
    if (el) el.classList.add('active');
    
    // Auto-load logic for side panel tabs
    if (tab.dataset.sptab === 'sp-seguridad' && currentDetailRepo) {
      loadRepoSecops(currentDetailRepo);
    } else if (tab.dataset.sptab === 'sp-cicd' && currentDetailRepo) {
      loadRepoCicd(currentDetailRepo);
    } else if (tab.dataset.sptab === 'sp-git' && currentDetailRepo) {
      // Clear reflog on open, user clicks load
      const rc = document.getElementById('sp-reflog-results');
      if (rc && !rc.innerHTML) rc.innerHTML = ''; 
    }
  });
});

let currentDetailRepo = null;
const btnCloseSp = document.getElementById('btn-close-sp');
if (btnCloseSp) {
  btnCloseSp.addEventListener('click', () => {
    document.getElementById('repo-detail-panel').classList.remove('open');
    currentDetailRepo = null;
    document.querySelectorAll('.repo-item.selected').forEach(e => e.classList.remove('selected'));
  });
}


// ---------------------------------------------------------------------------
// Consola / logger
// ---------------------------------------------------------------------------
const logs = document.getElementById('logs');
function log(msg, color = 'var(--fg-2)') {
  if (!logs) return;
  const line = document.createElement('span');
  line.style.color = color;
  line.textContent = msg;
  logs.appendChild(line);
  logs.appendChild(document.createElement('br'));
  logs.parentElement.scrollTop = logs.parentElement.scrollHeight;
  const drawer = document.getElementById('console-drawer');
  if (drawer && drawer.classList.contains('collapsed')) drawer.classList.add('has-unread');
}

// Cajon de consola: cabecera clicable abre/cierra; abrir limpia el no-leido.
(function wireConsoleDrawer() {
  })();

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ---------------------------------------------------------------------------
// Tema (claro / oscuro)
// ---------------------------------------------------------------------------
const THEME_KEY = 'orq_theme';
const SUN = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="currentColor"/><path style="fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round" d="M12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>';
const MOON = '<svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" fill="currentColor"/></svg>';
function applyTheme(t) {
  if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
  else document.documentElement.removeAttribute('data-theme');
  const btn = document.getElementById('btn-theme');
  if (btn) btn.innerHTML = (t === 'light') ? MOON : SUN; // muestra a qué cambiaría
}
function initTheme() { applyTheme(localStorage.getItem(THEME_KEY) || 'dark'); }
function toggleTheme() {
  const next = (localStorage.getItem(THEME_KEY) || 'dark') === 'light' ? 'dark' : 'light';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// ---------------------------------------------------------------------------
// Idioma (ES / EN)
// ---------------------------------------------------------------------------
let LANG = localStorage.getItem('orq_lang') || 'es';
const I18N = {
  es: {
    tag:'Tech Lead IA', sec_panel:'Panel', sec_crear:'Crear', sec_calidad:'Calidad',
    sec_mant:'Mantenimiento', sec_sistema:'Sistema',
    nav_dashboard:'Dashboard', nav_architect:'El Arquitecto', nav_inspector:'Revisor IA',
    nav_secops:'Auditor SecOps', nav_pruner:'El Barrendero', nav_autosync:'Radar AutoSync',
    nav_reflog:'Máquina del Tiempo', nav_config:'Ajustes IA',
    pk_none:'Sin carpeta', pk_current:'Carpeta de repos actual', pk_set:'Cambiar carpeta (ruta absoluta)',
    pk_use:'Usar y escanear', pk_rescan:'Re-escanear', search_ph:'Buscar repositorios...',
    t_dashboard:'Dashboard General', d_dashboard:'Vista global de tus repositorios locales.',
    kpi_total:'Proyectos detectados', kpi_dirty:'Cambios sin subir', kpi_env:'Estado del entorno',
    repos_detected:'Repositorios detectados', scanning:'Escaneando...',
    t_architect:'Inicializar Proyecto', d_architect:'Genera un proyecto nuevo con estructura profesional y git init a partir de una plantilla.',
    f_name:'Nombre', f_template:'Plantilla', b_build:'Construir Arquitectura',
    tpl_save_title:'Guardar un repo como plantilla propia', tpl_name:'Nombre', b_save_tpl:'Guardar como plantilla',
    t_inspector:'Revisor IA', d_inspector:'Usa Ollama o tu IA preferida para analizar tu último commit (Code Smells, bugs, seguridad).',
    b_inspect:'Auditar Commit', f_repo:'Repositorio', opt_scan:'Escanea primero...',
    t_secops:'Auditor SecOps', d_secops:'Analiza vulnerabilidades de dependencias en todos tus repositorios.', b_audit:'Auditar Todos',
    nav_cicd:'CI/CD Autopiloto', t_cicd:'CI/CD Autopiloto', d_cicd:'Detecta el stack de un repo y genera e inyecta un workflow de GitHub Actions listo para usar.', b_detect:'Detectar stack', b_preview:'Ver workflow', b_inject:'Inyectar',
    t_pruner:'El Barrendero', d_pruner:'Encuentra ramas muertas (merged) en todos tus repositorios locales.',
    b_scanall:'Escanear Todo', pruner_hint:'Pulsa "Escanear Todo" para buscar ramas muertas.',
    t_autosync:'Radar AutoSync', d_autosync:'Comprueba en silencio si hay commits pendientes de bajar/subir en cada repo.', b_sync:'Sincronizar Radar',
    t_reflog:'Máquina del Tiempo', d_reflog:'Revierte errores graves visualizando el historial oculto (reflog) de cada repo.', b_history:'Ver Historial',
    t_config:'Ajustes de IA', d_config:'Configura el motor de IA para el Revisor. Recomendamos Ollama en local (privado y gratis).',
    f_provider:'Proveedor', f_endpoint:'Endpoint', f_model:'Modelo', ph_key:'Solo para OpenAI/Anthropic...',
    b_save:'Guardar Configuración', b_test:'Probar conexión', b_refresh:'Actualizar', b_retry:'Reintentar', b_restore:'Revertir', b_confirm:'¿Seguro?',
    ollama_check:'Comprobando si Ollama está encendido…', ollama_idle:'Pulsa "Probar conexión" para comprobar tu motor de IA.',
    ollama_on:'Ollama activo', ollama_off:'Ollama no detectado. Enciéndelo con "ollama serve" o instálalo desde ollama.com',
    reflog_hint:'Abre esta pestaña para ver el historial de todos tus repos.', reflog_empty:'Sin historial de reflog.',
    term_title:'Consola',
    boot:'Sistema en línea. Esperando órdenes...',
  },
  en: {
    tag:'AI Tech Lead', sec_panel:'Panel', sec_crear:'Create', sec_calidad:'Quality',
    sec_mant:'Maintenance', sec_sistema:'System',
    nav_dashboard:'Dashboard', nav_architect:'The Architect', nav_inspector:'AI Reviewer',
    nav_secops:'SecOps Auditor', nav_pruner:'The Sweeper', nav_autosync:'AutoSync Radar',
    nav_reflog:'Time Machine', nav_config:'AI Settings',
    pk_none:'No folder', pk_current:'Current repos folder', pk_set:'Change folder (absolute path)',
    pk_use:'Use & scan', pk_rescan:'Re-scan', search_ph:'Search repositories...',
    t_dashboard:'General Dashboard', d_dashboard:'Global view of your local repositories.',
    kpi_total:'Detected projects', kpi_dirty:'Uncommitted changes', kpi_env:'Environment status',
    repos_detected:'Detected repositories', scanning:'Scanning...',
    t_architect:'Initialize Project', d_architect:'Generates a new project with a professional structure and git init from a template.',
    f_name:'Name', f_template:'Template', b_build:'Build Architecture',
    tpl_save_title:'Save a repo as your own template', tpl_name:'Name', b_save_tpl:'Save as template',
    t_inspector:'AI Reviewer', d_inspector:'Use Ollama or your favorite AI to analyze your latest commit (code smells, bugs, security).',
    b_inspect:'Audit Commit', f_repo:'Repository', opt_scan:'Scan first...',
    t_secops:'SecOps Auditor', d_secops:'Scans dependency vulnerabilities across all your repositories.', b_audit:'Audit All',
    nav_cicd:'CI/CD Autopilot', t_cicd:'CI/CD Autopilot', d_cicd:'Detects a repo stack and generates and injects a ready-to-use GitHub Actions workflow.', b_detect:'Detect stack', b_preview:'View workflow', b_inject:'Inject',
    t_pruner:'The Sweeper', d_pruner:'Finds dead (merged) branches across all your local repositories.',
    b_scanall:'Scan All', pruner_hint:'Press "Scan All" to look for dead branches.',
    t_autosync:'AutoSync Radar', d_autosync:'Silently checks whether each repo has commits to pull/push.', b_sync:'Sync Radar',
    t_reflog:'Time Machine', d_reflog:'Undo serious mistakes by viewing each repo\'s hidden history (reflog).', b_history:'View History',
    t_config:'AI Settings', d_config:'Configure the AI engine for the Reviewer. We recommend Ollama locally (private and free).',
    f_provider:'Provider', f_endpoint:'Endpoint', f_model:'Model', ph_key:'Only for OpenAI/Anthropic...',
    b_save:'Save Settings', b_test:'Test connection', b_refresh:'Refresh', b_retry:'Retry', b_restore:'Restore', b_confirm:'Sure?',
    ollama_check:'Checking whether Ollama is running…', ollama_idle:'Click "Test connection" to check your AI engine.',
    ollama_on:'Ollama running', ollama_off:'Ollama not detected. Start it with "ollama serve" or install it from ollama.com',
    reflog_hint:'Open this tab to see the history of all your repos.', reflog_empty:'No reflog history.',
    term_title:'Console',
    boot:'System online. Awaiting orders...',
  },
};
function tr(key) { return (I18N[LANG] && I18N[LANG][key]) || (I18N.es[key] || key); }
function applyLang() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const v = tr(el.dataset.i18n); if (v) el.textContent = v;
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const v = tr(el.dataset.i18nPh); if (v) el.setAttribute('placeholder', v);
  });
  const lb = document.getElementById('btn-lang');
  if (lb) lb.textContent = LANG.toUpperCase();
  document.documentElement.setAttribute('lang', LANG);
}
function toggleLang() {
  LANG = (LANG === 'es') ? 'en' : 'es';
  localStorage.setItem('orq_lang', LANG);
  applyLang();
}

// ---------------------------------------------------------------------------
// Chrome de ventana (frameless) + dropdown de carpeta
// ---------------------------------------------------------------------------
async function tauriWin() {
  const w = await import('@tauri-apps/api/window');
  return w.getCurrentWindow();
}

const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
if (btnToggleSidebar) {
  btnToggleSidebar.addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('collapsed');
    btnToggleSidebar.classList.toggle('collapsed');
  });
}

function setPickerPath(root) {
  const cur = document.getElementById('picker-current');
  const pth = document.getElementById('picker-path');
  const name = root ? root.split(/[\\/]/).filter(Boolean).pop() : null;
  if (cur) cur.textContent = name || tr('pk_none');
  if (pth) pth.textContent = root || '—';
}

// ---------------------------------------------------------------------------
// Puente con Python (robusto)
// ---------------------------------------------------------------------------
async function resolveEnv() {
  if (!IN_TAURI) return;
  // 1) Primario: comando Rust app_paths → ruta absoluta correcta (tras recompilar).
  try {
    const core = await import('@tauri-apps/api/core');
    _invoke = core.invoke;
    const p = await _invoke('app_paths');
    if (p && p.script) { SCRIPT = p.script; ROOT = p.root; return; }
  } catch (e) { /* Rust aún no recompilado: usamos el probe relativo */ }
  // 2) Fallback robusto: probar rutas candidatas relativas al cwd del proceso.
  await probeScript();
}

async function probeScript() {
  const candidates = [
    'src/core/orquesta_core.py',
    '../src/core/orquesta_core.py',
    '../../src/core/orquesta_core.py',
    './src/core/orquesta_core.py',
  ];
  try {
    const bin = await resolvePython();
    for (const c of candidates) {
      try {
        const out = await Command.create(bin,
          ['-c', 'import os,sys;print("Y" if os.path.exists(sys.argv[1]) else "N")', c]).execute();
        if ((out.stdout || '').trim() === 'Y') { SCRIPT = c; return; }
      } catch (_) { /* siguiente */ }
    }
  } catch (_) { /* sin python: runPython ya avisa */ }
}

async function resolvePython() {
  if (PYBIN) return PYBIN;
  const candidates = ['python', 'py', 'python3'];
  for (const bin of candidates) {
    try {
      const out = await Command.create(bin, ['--version']).execute();
      if (out.code === 0 || (out.stdout + out.stderr).toLowerCase().includes('python')) {
        PYBIN = bin;
        return bin;
      }
    } catch (_) { /* probar siguiente */ }
  }
  throw new Error('No se encontro Python en el sistema (python / py / python3).');
}

async function runPython(action, args = []) {
  if (!IN_TAURI) {
    log(`[DEMO] "${action}" requiere la app de escritorio (npm run tauri dev).`, 'var(--warn)');
    return null;
  }
  try {
    const bin = await resolvePython();
    const out = await Command.create(bin, [SCRIPT, action, ...args]).execute();
    if (out.code !== 0 && !out.stdout) {
      log(`[ERROR] ${action}: ${out.stderr || 'codigo ' + out.code}`, 'var(--bad)');
      return null;
    }
    let data;
    try {
      data = JSON.parse(out.stdout.trim().split('\n').pop());
    } catch (e) {
      log(`[WARN] Salida no JSON de ${action}: ${out.stdout.slice(0, 200)}`, 'var(--fg-1)');
      return null;
    }
    if (data && data.ok === false) {
      log(`[ERROR] ${action}: ${data.error || 'desconocido'}`, 'var(--bad)');
      return data; // devolvemos igual por si el llamador quiere el detalle
    }
    return data;
  } catch (err) {
    log(`[ERROR FATAL] ${action}: ${err}`, 'var(--bad)');
    return null;
  }
}

// ---------------------------------------------------------------------------
// Banner de entorno (modo demo)
// ---------------------------------------------------------------------------
function showEnvBanner() {
  const banner = document.getElementById('env-banner');
  if (!banner) return;
  if (IN_TAURI) { banner.style.display = 'none'; return; }
  banner.style.display = 'block';
  banner.innerHTML = `
    <b>Modo demo (navegador).</b> Las funciones locales (git / Python) estan
    desactivadas aqui. Lanza la app real con
    <code style="color:var(--brand)">npm run tauri dev</code> para escanear tus repos.`;
}

// ---------------------------------------------------------------------------
// Dashboard: scan real + grid por repo (estilo RepoBar)
// ---------------------------------------------------------------------------
function pill(text, color) {
  return `<span class="pill" style="--pc:${color}"><span class="pdot"></span>${esc(text)}</span>`;
}

function renderRepoGrid(repos) {
  const grid = document.getElementById('repo-grid');
  if (!grid) return;
  grid.innerHTML = '';
  if (!repos || repos.length === 0) {
    grid.innerHTML = '<div class="desc" style="margin-left:0;">No se encontraron repositorios.</div>';
    return;
  }
  repos.forEach(r => {
    const dirty = r.dirty > 0;
    const behind = r.behind > 0;
    const ahead = r.ahead > 0;
    
    let timeAgo = '';
    if (r.scanned_at) {
        const diffStr = Math.max(0, Math.floor((Date.now() / 1000) - r.scanned_at));
        if (diffStr < 60) timeAgo = `hace ${diffStr}s`;
        else timeAgo = `hace ${Math.floor(diffStr/60)}m`;
    }

    const row = document.createElement('div');
    row.className = 'repo-item glass-panel';
    row.dataset.name = (r.name || '').toLowerCase();
    const accent = behind ? 'var(--bad)' : ((dirty || ahead) ? 'var(--warn)' : 'var(--good)');
    row.style.boxShadow = 'inset 3px 0 0 ' + accent;
    
    // Phosphor icons
    const folderIcon = '<svg viewBox="0 0 256 256" fill="currentColor"><path d="M216,72H130.67L102.93,51.2a16.12,16.12,0,0,0-9.6-3.2H40A16,16,0,0,0,24,64V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V88A16,16,0,0,0,216,72Zm0,128H40V64H93.33l27.74,20.8a16.12,16.12,0,0,0,9.6,3.2H216Z"/></svg>';
    const githubIcon = '<svg viewBox="0 0 256 256" fill="currentColor"><path d="M208.31,75.68A59.78,59.78,0,0,0,202.93,28,8,8,0,0,0,196,24a59.75,59.75,0,0,0-48,24H124A59.75,59.75,0,0,0,76,24a8,8,0,0,0-6.93,4,59.78,59.78,0,0,0-5.38,47.68A58.14,58.14,0,0,0,56,104v8a56.06,56.06,0,0,0,48.44,55.47A39.8,39.8,0,0,0,96,192v8H72a24,24,0,0,1-24-24A40,40,0,0,0,8,136a8,8,0,0,0,0,16,24,24,0,0,1,24,24,40,40,0,0,0,40,40H96v16a8,8,0,0,0,16,0V192a24,24,0,0,1,48,0v40a8,8,0,0,0,16,0V192a39.8,39.8,0,0,0-8.44-24.53A56.06,56.06,0,0,0,216,112v-8A58.14,58.14,0,0,0,208.31,75.68ZM200,112a40,40,0,0,1-40,40H112a40,40,0,0,1-40-40v-8a41.74,41.74,0,0,1,6.9-22.48A8,8,0,0,0,80,73.83a43.81,43.81,0,0,1,.79-33.58,43.88,43.88,0,0,1,32.32,20.06A8,8,0,0,0,119.82,64h32.35a8,8,0,0,0,6.74-3.69,43.87,43.87,0,0,1,32.32-20.06A43.81,43.81,0,0,1,192,73.83a8.09,8.09,0,0,0,1,7.65A41.72,41.72,0,0,1,200,104Z"/></svg>';
    const shieldIcon = '<svg viewBox="0 0 256 256" fill="currentColor"><path d="M208,40H48A16,16,0,0,0,32,56v58.78c0,89.61,75.82,119.34,91,124.39a15.53,15.53,0,0,0,10,0c15.2-5.05,91-34.78,91-124.39V56A16,16,0,0,0,208,40Zm-34.34,69.66-48,48a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L120,140.69l42.34-42.35a8,8,0,0,1,11.32,11.32Z"/></svg>';
    const broomIcon = '<svg viewBox="0 0 256 256" fill="currentColor"><path d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192ZM112,104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"/></svg>';
    const syncIcon = '<svg viewBox="0 0 256 256" fill="currentColor"><path d="M240,56v48a8,8,0,0,1-8,8H184a8,8,0,0,1,0-16h28.9l-16.5-15.09A80,80,0,0,0,55.35,90.26a8,8,0,0,1-13.86-8A96,96,0,0,1,207.51,73l16.49,15.06V56a8,8,0,0,1,16,0ZM211,153.75a8,8,0,0,0-11,2.86A80,80,0,0,1,59.56,169.74L43.06,184h28.9a8,8,0,0,0,0-16H24a8,8,0,0,0-8,8v48a8,8,0,0,0,16,0V182.94l16.49,15.05A96,96,0,0,0,213.83,164.71,8,8,0,0,0,211,153.75Z"/></svg>';

    row.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;">
        <!-- Left: Info -->
        <div style="display:flex; flex-direction:column; gap:4px; min-width:150px; width:30%;">
          <b style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(r.name)}</b>
          <span style="font-size:11px; color:var(--fg-3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(r.path)}</span>
        </div>
        <!-- Middle: Git Status -->
        <div style="display:flex; flex-direction:column; gap:4px; min-width:120px;">
          <span style="font-size:11px; color:var(--fg-3);">rama: <b style="color:var(--brand)">${esc(r.branch)}</b></span>
          <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
            ${dirty ? pill(r.dirty + ' sin commit', 'var(--warn)') : pill('limpio', 'var(--good)')}
            ${behind ? pill('↓ ' + r.behind, 'var(--bad)') : ''}
            ${ahead ? pill('↑ ' + r.ahead, 'var(--warn)') : ''}
            ${!r.upstream && r.upstream !== undefined ? pill('sin upstream', 'var(--fg-3)') : ''}
          </div>
        </div>
        <!-- Right: Actions -->
        <div class="repo-actions" style="display:flex; gap:4px; align-items:center;">
          <button class="icon-btn action-folder" data-tip="Abrir carpeta">${folderIcon}</button>
          <button class="icon-btn action-github" data-tip="Abrir en GitHub">${githubIcon}</button>
          <button class="icon-btn action-audit" data-tip="Auditar seguridad">${shieldIcon}</button>
          <button class="icon-btn action-clean" data-tip="Limpiar ramas">${broomIcon}</button>
          <button class="icon-btn action-sync" data-tip="Sincronizar">${syncIcon}</button>
        </div>
      </div>`;
    
    // Wire Quick Actions
    const btnFolder = row.querySelector('.action-folder');
    const btnGithub = row.querySelector('.action-github');
    const btnAudit = row.querySelector('.action-audit');
    const btnClean = row.querySelector('.action-clean');
    const btnSync = row.querySelector('.action-sync');
    
    btnFolder.addEventListener('click', async (e) => {
        e.stopPropagation();
        // Fallback simple: run_python -> explorer path (solo para desktop)
        if (IN_TAURI) {
           const cmd = await import('@tauri-apps/plugin-shell');
           cmd.Command.create('explorer', [r.path]).execute().catch(()=>{});
        }
    });
    btnGithub.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!IN_TAURI) return;
        try {
            const bin = await resolvePython();
            const cmd = await import('@tauri-apps/plugin-shell');
            const out = await cmd.Command.create(bin, [SCRIPT.replace('orquesta_core.py', 'repo_meta.py'), 'get_remote', r.path]).execute();
            const data = JSON.parse(out.stdout.trim().split('\n').pop());
            if (data && data.remote) openExternal(data.remote);
            else log('Este repo no tiene remoto configurado.', 'var(--fg-3)');
        } catch (_) { log('No se pudo abrir GitHub.', 'var(--bad)'); }
    });
    btnAudit.addEventListener('click', (e) => {
        e.stopPropagation();
        openSidePanel(r);
        document.querySelector('.sp-tab[data-sptab="sp-seguridad"]').click();
        const btnDeep = document.getElementById('btn-sp-secops-deep');
        if (btnDeep) btnDeep.click();
    });
    btnClean.addEventListener('click', (e) => {
        e.stopPropagation();
        openSidePanel(r);
        document.querySelector('.sp-tab[data-sptab="sp-git"]').click();
    });
    btnSync.addEventListener('click', (e) => {
        e.stopPropagation();
        openSidePanel(r);
        document.querySelector('.sp-tab[data-sptab="sp-git"]').click();
        const btnSpSync = document.getElementById('btn-sp-git-sync');
        if (btnSpSync) btnSpSync.click();
    });

    row.addEventListener('click', () => {
       document.querySelectorAll('.repo-item.selected').forEach(e => e.classList.remove('selected'));
       row.classList.add('selected');
       openSidePanel(r);
    });

    grid.appendChild(row);
  });
}

// ── Panel de detalle enriquecido con repo_meta.py detail ──
async function repoMeta(action, args = []) {
  if (!IN_TAURI) return null;
  try {
    const bin = await resolvePython();
    const cmd = await import('@tauri-apps/plugin-shell');
    const out = await cmd.Command.create(bin, [SCRIPT.replace('orquesta_core.py', 'repo_meta.py'), action, ...args]).execute();
    return JSON.parse(out.stdout.trim().split('\n').pop());
  } catch (_) { return null; }
}

function spRow(k, vHtml) {
  return `<div style="display:flex; justify-content:space-between; gap:12px; padding:7px 0;
    border-bottom:1px solid var(--hairline); font-size:12.5px;">
    <span style="color:var(--fg-3);">${esc(k)}</span>
    <span style="color:var(--fg-1); font-family:var(--font-mono); text-align:right;">${vHtml}</span></div>`;
}

function renderResumenDetail(d) {
  const health = (d.behind > 0 || d.dirty > 0) ? pill('atención', 'var(--warn)') : pill('al día', 'var(--good)');
  const lc = d.last_commit;
  const commit = lc
    ? `<b style="color:var(--brand)">${esc(lc.hash)}</b> ${esc(lc.subject)}
       <div style="color:var(--fg-3); font-size:11px; margin-top:3px;">${esc(lc.author)} · ${esc(lc.rel_time)}</div>`
    : '—';
  return `
    <div class="card" style="padding:14px 16px; margin-bottom:12px;">
      ${spRow('Salud', health)}
      ${spRow('Rama', `<span style="color:var(--brand)">${esc(d.branch)}</span>`)}
      ${spRow('Sincronización', `↑${d.ahead} / ↓${d.behind}`)}
      ${spRow('Sin commitear', String(d.dirty))}
    </div>
    <div class="card" style="padding:14px 16px;">
      <div style="font-size:11px; color:var(--fg-3); text-transform:uppercase; letter-spacing:.06em; margin-bottom:8px;">Último commit</div>
      <div style="font-size:12.5px; line-height:1.5;">${commit}</div>
    </div>`;
}

function renderGitDetail(d) {
  const gh = d.remote
    ? `<a href="#" id="sp-open-github" style="color:var(--accent);">Abrir en GitHub ↗</a>`
    : '<span style="color:var(--fg-3)">sin remoto</span>';
  const wt = (d.worktrees && d.worktrees.length > 1)
    ? d.worktrees.length + ' worktrees'
    : ((d.worktrees && d.worktrees.length === 1) ? '1 (principal)' : '—');
  return `<div class="card" style="padding:14px 16px; margin-bottom:14px;">
    ${spRow('Rama', `<span style="color:var(--brand)">${esc(d.branch)}</span>`)}
    ${spRow('Upstream', d.upstream ? esc(d.upstream) : '<span style="color:var(--fg-3)">sin upstream</span>')}
    ${spRow('Adelante / atrás', `↑${d.ahead} / ↓${d.behind}`)}
    ${spRow('Sin commitear', String(d.dirty))}
    ${spRow('Stash', String(d.stash))}
    ${spRow('Tags', String(d.tags))}
    ${spRow('Worktrees', esc(wt))}
    ${spRow('Remoto', gh)}
  </div>`;
}

async function loadRepoDetail(repo) {
  const d = await repoMeta('detail', [repo.path]);
  if (!d || d.ok === false) return;
  const resumen = document.getElementById('sp-resumen-container');
  if (resumen) resumen.innerHTML = renderResumenDetail(d);
  const gitTab = document.getElementById('sp-git');
  if (gitTab) {
    let box = document.getElementById('sp-git-detail');
    if (!box) { box = document.createElement('div'); box.id = 'sp-git-detail'; gitTab.insertBefore(box, gitTab.firstChild); }
    box.innerHTML = renderGitDetail(d);
    const gl = document.getElementById('sp-open-github');
    if (gl) gl.addEventListener('click', (e) => { e.preventDefault(); if (d.remote) openExternal(d.remote); });
  }
}

function openSidePanel(repo) {
  currentDetailRepo = repo;
  const sp = document.getElementById('repo-detail-panel');
  if (sp) sp.classList.add('open');
  
  const title = document.getElementById('sp-repo-name');
  if (title) title.textContent = repo.name;
  
  // Rellenar resumen
  const resumen = document.getElementById('sp-resumen-container');
  if (resumen) {
    resumen.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:8px;">
        <div><b>Ruta:</b> <span style="font-family:var(--font-mono); font-size:11.5px; color:var(--fg-1);">${esc(repo.path)}</span></div>
        <div><b>Rama:</b> <span style="color:var(--brand)">${esc(repo.branch)}</span></div>
        <div><b>Estado Git:</b> ${repo.dirty ? repo.dirty + ' sin commit' : 'limpio'}</div>
        <div><b>Ahead/Behind:</b> ↑${repo.ahead || 0} / ↓${repo.behind || 0}</div>
      </div>
    `;
  }
  
  // Enriquecer con datos reales (último commit, upstream, stash, worktrees, remoto…)
  loadRepoDetail(repo);

  // Activar la pestaña actualmente seleccionada
  const activeTab = document.querySelector('.sp-tab.active');
  if (activeTab) activeTab.click();
}

async function loadRepoSecops(repo) {
    const c = document.getElementById('sp-secops-results');
    if (c) {
       c.innerHTML = '<div class="desc">Haz clic en Auditar o Escaneo Profundo para obtener datos de seguridad.</div>';
    }
}

async function loadRepoCicd(repo) {
    const btn = document.getElementById('btn-sp-cicd-detect');
    if (btn) btn.dataset.repoPath = repo.path;
    const c = document.getElementById('sp-cicd-results');
    if (c) c.innerHTML = '<div class="desc">Pulsa Detectar Stack.</div>';
}

// Side Panel Handlers
on('btn-sp-git-sync', async () => {
    if (!currentDetailRepo) return;
    const btn = document.getElementById('btn-sp-git-sync');
    btn.disabled = true; btn.textContent = 'Sincronizando...';
    // Se asume un comando de sync seguro (fast-forward)
    log(`> Sincronizando ${currentDetailRepo.name}...`, 'var(--warn)');
    const res = await runPython('sync_all', [currentDetailRepo.path]); // sync_all handles single path if passed
    if (res && res.ok) log(`[✔] ${currentDetailRepo.name}: Sincronizado`, 'var(--good)');
    btn.disabled = false; btn.textContent = 'Sincronizar (Fast-Forward)';
    refreshDashboardView();
});

on('btn-sp-git-clean', async () => {
    if (!currentDetailRepo) return;
    const btn = document.getElementById('btn-sp-git-clean');
    if (btn.dataset.armed !== '1') {
        btn.dataset.armed = '1'; btn.textContent = tr('b_confirm');
        setTimeout(() => { if (btn.dataset.armed === '1') { btn.dataset.armed = '0'; btn.textContent = 'Limpiar ramas muertas'; } }, 3500);
        return;
    }
    btn.dataset.armed = '0';
    btn.disabled = true; btn.textContent = 'Limpiando...';
    log(`> Limpiando ramas muertas en ${currentDetailRepo.name}...`, 'var(--warn)');
    const res = await runPython('prune_all', [currentDetailRepo.path]); // prune_all handles single path
    if (res) log(`[✔] ${currentDetailRepo.name}: Ramas muertas limpiadas.`, 'var(--good)');
    btn.disabled = false; btn.textContent = 'Limpiar ramas muertas';
});

on('btn-sp-reflog', async () => {
    if (!currentDetailRepo) return;
    const c = document.getElementById('sp-reflog-results');
    c.innerHTML = '<div class="desc">Cargando reflog...</div>';
    const data = await runPython('reflog_all', [currentDetailRepo.path, '10']);
    c.innerHTML = '';
    
    const repos = (data && data.repos) || [];
    if (!repos.length || !repos[0].entries.length) {
        c.innerHTML = '<div class="desc">Sin historial.</div>'; return;
    }
    const entries = repos[0].entries;
    entries.forEach(en => {
        const row = document.createElement('div');
        row.style = 'display:flex; align-items:center; gap:10px; padding:6px 0; border-top:1px solid var(--hairline); font-family:var(--font-mono); font-size:11.5px;';
        row.innerHTML =
          `<span style="color:var(--brand); min-width:62px;">${esc(en.hash)}</span>` +
          `<span style="color:var(--fg-3); min-width:82px;">${esc(en.time)}</span>` +
          `<span style="color:var(--fg-1); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${esc(en.action)}</span>`;
        c.appendChild(row);
    });
});

on('btn-sp-secops-audit', async () => {
    if (!currentDetailRepo) return;
    const btn = document.getElementById('btn-sp-secops-audit');
    btn.disabled = true; btn.textContent = 'Auditando...';
    const c = document.getElementById('sp-secops-results');
    c.innerHTML = '<div class="desc">Auditando npm/pip...</div>';
    const res = await runPython('secops_all', [currentDetailRepo.path]);
    
    // Re-use renderSecopsList logic but inject into sp-secops-results
    if (res && res.repos && res.repos.length > 0) {
        c.innerHTML = '';
        // Hack: temporarily point secops-results to sp-secops-results
        const oldC = document.getElementById('secops-results');
        const tmpC = document.createElement('div'); tmpC.id = 'secops-results';
        c.appendChild(tmpC);
        renderSecopsList({repos: res.repos});
        c.innerHTML = tmpC.innerHTML; // move content
    } else {
        c.innerHTML = '<div class="desc">Sin dependencias auditables.</div>';
    }
    
    btn.disabled = false; btn.textContent = 'Auditar (Rápido)';
});

on('btn-sp-secops-deep', async () => {
    if (!currentDetailRepo) return;
    const btn = document.getElementById('btn-sp-secops-deep');
    btn.disabled = true; btn.textContent = 'Escaneando...';
    const c = document.getElementById('sp-deep-results');
    c.innerHTML = '<div class="desc">Ejecutando secops_engine.py... esto puede tardar.</div>';
    
    try {
        if (!IN_TAURI) { c.innerHTML = '<div class="desc" style="color:var(--warn)">Modo demo. Usa Tauri dev.</div>'; btn.disabled = false; btn.textContent = 'Escaneo Profundo'; return; }
        const cmd = await import('@tauri-apps/plugin-shell');
        const bin = await resolvePython();
        const out = await cmd.Command.create(bin, [SCRIPT.replace('orquesta_core.py', 'secops_engine.py'), 'deep_scan', currentDetailRepo.path]).execute();
        if (out.code !== 0 && !out.stdout) {
            c.innerHTML = `<div class="desc" style="color:var(--bad)">Error: ${esc(out.stderr)}</div>`;
        } else {
            let data;
            try { data = JSON.parse(out.stdout.trim().split('\n').pop()); } catch(e) {}
            if (data && data.summary) {
                const badge = `CRIT: ${data.summary.critical}, HIGH: ${data.summary.high}, MED: ${data.summary.medium}`;
                const gate = data.gate.passed ? pill('PASA', 'var(--good)') : pill('FALLA', 'var(--bad)');
                
                let findingsHtml = data.findings.map(f => `
                    <div style="font-size:11.5px; border-top:1px solid var(--hairline); padding:6px 0;">
                        <span style="color:var(--bad); font-weight:bold;">${esc(f.severity)}</span> 
                        <span style="color:var(--fg-3)">[${esc(f.scanner)}]</span> 
                        <span style="color:var(--fg-1)">${esc(f.title)}</span>
                        <div style="color:var(--fg-2)">${esc(f.file || '')}:${esc(f.line || '')}</div>
                        ${f.remediation ? `<div style="color:var(--good)">Arreglo: ${esc(f.remediation)}</div>` : ''}
                    </div>
                `).join('');
                
                c.innerHTML = `
                    <div style="margin-bottom:12px; display:flex; gap:12px; align-items:center;">
                        <b>Gate:</b> ${gate}
                        <span style="font-size:11.5px; color:var(--fg-3)">${badge}</span>
                    </div>
                    ${findingsHtml || '<div class="desc">Sin hallazgos. ¡Seguro!</div>'}
                `;
            } else {
                c.innerHTML = `<div class="desc" style="color:var(--bad)">Respuesta no válida del motor SecOps.</div>`;
            }
        }
    } catch (e) {
        c.innerHTML = `<div class="desc" style="color:var(--bad)">Error fatal al llamar a secops_engine.py</div>`;
    }
    
    btn.disabled = false; btn.textContent = 'Escaneo Profundo';
});

on('btn-sp-cicd-detect', async () => {
    if (!currentDetailRepo) return;
    const btn = document.getElementById('btn-sp-cicd-detect');
    btn.disabled = true; btn.textContent = 'Detectando...';
    
    const det = await runPython('cicd_detect', [currentDetailRepo.path]);
    
    // Re-use logic but inject to sp-cicd-results
    const c = document.getElementById('sp-cicd-results');
    if (c) {
        c.innerHTML = '';
        // Same hack as secops
        const tmpC = document.createElement('div'); tmpC.id = 'cicd-results';
        document.body.appendChild(tmpC);
        renderCicdDetect(det, currentDetailRepo.path);
        c.innerHTML = tmpC.innerHTML;
        document.body.removeChild(tmpC);
    }
    
    btn.disabled = false; btn.textContent = 'Detectar Stack';
});

// Fix global actions on Dashboard
const btnSyncAll = document.getElementById('btn-sync-all');
if (btnSyncAll) {
    // Reemplaza los listeners viejos si se pudiera, o simplemente los viejos fallarán suavemente si faltan contenedores
    btnSyncAll.addEventListener('click', async () => {
        btnSyncAll.disabled = true; btnSyncAll.textContent = 'Sincronizando...';
        log('> Sincronizando radar (fetch en todos los repos)...', 'var(--warn)');
        await runPython('bg_refresh_sync', globalGithubPath ? [globalGithubPath] : []);
        const data = await runPython('sync_all', globalGithubPath ? [globalGithubPath] : []);
        if (data) log(`[✔] Sincronización completada.`, 'var(--good)');
        await refreshDashboardView();
        btnSyncAll.disabled = false; btnSyncAll.textContent = 'Sincronizar Todos';
    });
}

const btnSecopsAll = document.getElementById('btn-secops-all');
if (btnSecopsAll) {
    btnSecopsAll.addEventListener('click', async () => {
        btnSecopsAll.disabled = true; btnSecopsAll.textContent = 'Auditando...';
        log('> Auditando dependencias (npm/pip audit)...', 'var(--warn)');
        await runPython('bg_refresh_secops', globalGithubPath ? [globalGithubPath] : []);
        log(`[✔] Auditoría completada. Los badges se actualizarán.`, 'var(--good)');
        await refreshDashboardView();
        btnSecopsAll.disabled = false; btnSecopsAll.textContent = 'Auditar Todos';
    });
}

const btnPruneAll = document.getElementById('btn-prune-all');
if (btnPruneAll) {
    btnPruneAll.addEventListener('click', async () => {
        if (btnPruneAll.dataset.armed !== '1') {
            btnPruneAll.dataset.armed = '1'; btnPruneAll.textContent = '¿Seguro?';
            setTimeout(() => { if (btnPruneAll.dataset.armed === '1') { btnPruneAll.dataset.armed = '0'; btnPruneAll.textContent = 'Barrer Todos'; } }, 3500);
            return;
        }
        btnPruneAll.dataset.armed = '0';
        btnPruneAll.disabled = true; btnPruneAll.textContent = 'Barriendo...';
        log('> Buscando ramas muertas...', 'var(--warn)');
        await runPython('bg_refresh_pruner', globalGithubPath ? [globalGithubPath] : []);
        log(`[✔] Barrido de ramas muertas completado.`, 'var(--good)');
        await refreshDashboardView();
        btnPruneAll.disabled = false; btnPruneAll.textContent = 'Barrer Todos';
    });
}


async function fetchKPIs() {
  showEnvBanner();
  if (!IN_TAURI) {
    const demo = [
      { name: 'orquesta-git', path: '', branch: 'main', dirty: 3, ahead: 1, behind: 0, upstream: true },
      { name: 'api-server', path: '', branch: 'develop', dirty: 0, ahead: 0, behind: 2, upstream: true },
      { name: 'landing-web', path: '', branch: 'main', dirty: 0, ahead: 0, behind: 0, upstream: true },
    ];
    setKPI('kpi-total', demo.length);
    setKPI('kpi-uncommited', demo.filter(r => r.dirty > 0).length, true);
    renderRepoGrid(demo);
    return;
  }

  log('> Escaneando repositorios locales...', 'var(--warn)');
  let data = await runPython('scan');
  if (!data) return;
  if (data.ok === false) { log(`[ERROR] ${data.error}`, 'var(--bad)'); return; }
  
  if (data.total === 0 && data.path) {
    log('> Detectando repositorios por primera vez. Esto puede tardar unos segundos...', 'var(--fg-2)');
    await runPython('bg_refresh_repos', [data.path]);
    data = await runPython('scan');
  }

  globalGithubPath = data.path || '';
  setPickerPath(data.path);
  setKPI('kpi-total', data.total);
  setKPI('kpi-uncommited', data.uncommitted, data.uncommitted > 0);
  renderRepoGrid(data.repos);

  fillRepoSelect('ai-repo-select', data.repos);
  fillRepoSelect('cicd-repo-select', data.repos);
  fillRepoSelect('tpl-save-repo', data.repos);
  log(`[✔] ${data.total} repos en ${data.path}.`, 'var(--good)');
}

function fillRepoSelect(id, repos) {
  const sel = document.getElementById(id);
  if (!sel || !repos) return;
  sel.innerHTML = '';
  repos.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.path;
    opt.textContent = r.name;
    sel.appendChild(opt);
  });
}

function setKPI(id, val, warn = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = val;
  el.classList.toggle('warn', !!warn);
  el.classList.toggle('good', !warn);
}

function renderPruneList(data) {
  const container = document.getElementById('pruner-results');
  if (!container) return;
  container.innerHTML = '';
  const withDead = (data.repos || []).filter(r => r.branches && r.branches.length > 0);
  if (withDead.length === 0) {
    container.innerHTML = '<div class="desc" style="margin-left:0;">Todo limpio. No hay ramas muertas.</div>';
    return;
  }
  withDead.forEach(repo => {
    const div = document.createElement('div');
    div.className = 'repo-item glass-panel';
    div.style.boxShadow = 'inset 3px 0 0 var(--warn)';
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;">
        <b>${esc(repo.name)}</b>
        <span style="color:var(--warn)">${repo.branches.length} ramas muertas</span>
      </div>
      <div style="font-size:11px; color:var(--fg-3); margin-top:6px;">${esc(repo.branches.join(', '))}</div>`;
    const btn = document.createElement('button');
    btn.className = 'cta warn';
    btn.style = 'height:30px; padding:0 12px; font-size:11px; margin-top:8px; align-self:flex-start;';
    btn.textContent = 'Limpiar ramas';
    btn.addEventListener('click', async () => {
      btn.disabled = true; btn.textContent = 'Limpiando...';
      const res = await runPython('prune_exec', [repo.path, ...repo.branches]);
      if (res && res.ok) {
        log(`[✔] ${repo.name}: borradas ${res.deleted.length} ramas.`, 'var(--good)');
        div.remove();
      } else {
        btn.disabled = false; btn.textContent = 'Reintentar';
      }
    });
    div.appendChild(btn);
    container.appendChild(div);
  });
}

function renderSyncList(data) {
  const container = document.getElementById('sync-results');
  if (!container) return;
  container.innerHTML = '';
  if (!data.repos || data.repos.length === 0) {
    container.innerHTML = '<div class="desc" style="margin-left:0;">Sin repositorios.</div>';
    return;
  }
  data.repos.forEach(repo => {
    const behind = repo.behind > 0;
    const ahead = repo.ahead > 0;
    const color = behind ? 'var(--bad)' : (ahead ? 'var(--warn)' : 'var(--good)');
    const div = document.createElement('div');
    div.className = 'repo-item glass-panel';
    div.style.boxShadow = 'inset 3px 0 0 ' + color;
    div.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;">
        <div style="display:flex; flex-direction:column; gap:2px;">
          <b>${esc(repo.name)}</b>
          <span style="font-size:11px; color:var(--fg-3);">rama: ${esc(repo.branch || '?')}</span>
        </div>
        <span style="color:${color}">${esc(repo.message || '')}</span>
      </div>`;
    container.appendChild(div);
  });
}

function renderSecopsList(data) {
  const SEV = { critical: ['var(--bad)','crítica'], high: ['var(--bad)','alta'], moderate: ['var(--warn)','media'], low: ['var(--fg-3)','baja'], info: ['var(--fg-3)','info'] };
  let container = document.getElementById('secops-results');
  if (!container) {
    container = document.createElement('div');
    container.id = 'secops-results';
    container.style = 'margin-top:24px; display:flex; flex-direction:column; gap:12px;';
    document.getElementById('secops').appendChild(container);
  }
  container.innerHTML = '';
  const audit = (data.repos || []).filter(r => r.type && r.type !== 'none');
  if (audit.length === 0) {
    container.innerHTML = '<div class="desc" style="margin-left:0;">No se encontraron dependencias auditables (npm, pip, cargo). Pulsa "Auditar Todos".</div>';
    return;
  }
  audit.forEach(repo => {
    const vuln = repo.vulns > 0;
    const findings = repo.findings || [];
    const div = document.createElement('div');
    div.className = 'repo-item glass-panel';
    div.style.boxShadow = 'inset 3px 0 0 ' + (vuln ? 'var(--bad)' : 'var(--good)');

    const head = document.createElement('div');
    head.style = 'display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;' + (vuln ? ' cursor:pointer;' : '');
    head.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px; min-width:0;">
        ${vuln ? '<span class="sec-caret" style="color:var(--fg-3); font-size:11px;">▸</span>' : ''}
        <b>${esc(repo.name)} <span style="font-size:10px; color:var(--fg-3)">(${esc(repo.type)})</span></b>
      </div>
      <span style="color:${vuln ? 'var(--bad)' : 'var(--good)'}; white-space:nowrap;">${vuln ? repo.vulns + ' vulnerabilidades' : 'Seguro'}</span>`;
    div.appendChild(head);

    if (repo.msg) {
      const m = document.createElement('div');
      m.style = 'font-size:11px; color:var(--fg-3); margin-top:6px;';
      m.textContent = repo.msg;
      div.appendChild(m);
    }

    if (vuln) {
      const detail = document.createElement('div');
      detail.style = 'display:none; margin-top:12px; border-top:1px solid var(--hairline); padding-top:12px;';

      // Cómo actuar
      if (repo.fix_cmd) {
        const rem = document.createElement('div');
        rem.style = 'display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px;';
        rem.innerHTML = `<span style="font-size:11.5px; color:var(--fg-2);">Cómo arreglar:</span>
          <code style="font-family:var(--font-mono); font-size:11.5px; background:rgba(0,0,0,.25); border:1px solid var(--hairline); border-radius:6px; padding:2px 8px; color:var(--fg-1);">${esc(repo.fix_cmd)}</code>`;
        if (repo.type === 'npm') {
          const fixBtn = document.createElement('button');
          fixBtn.className = 'cta warn';
          fixBtn.style = 'height:28px; padding:0 12px; font-size:11px;';
          fixBtn.textContent = 'Arreglar';
          fixBtn.dataset.armed = '0';
          fixBtn.addEventListener('click', async () => {
            if (fixBtn.dataset.armed !== '1') {
              fixBtn.dataset.armed = '1'; fixBtn.textContent = tr('b_confirm');
              setTimeout(() => { if (fixBtn.dataset.armed === '1') { fixBtn.dataset.armed = '0'; fixBtn.textContent = 'Arreglar'; } }, 3500);
              return;
            }
            fixBtn.dataset.armed = '0'; fixBtn.disabled = true; fixBtn.textContent = '…';
            log(`> ${repo.name}: ejecutando npm audit fix...`, 'var(--warn)');
            const res = await runPython('secops_fix', [repo.path]);
            if (res && res.ok) {
              log(`[✔] ${repo.name}: npm audit fix aplicado. Reauditando...`, 'var(--good)');
              await runPython('bg_refresh_secops', [globalGithubPath]);
              await refreshSecopsView();
            } else if (res) {
              log(`[ERROR] ${repo.name}: ${res.error || 'no se pudo arreglar'}`, 'var(--bad)');
              fixBtn.disabled = false; fixBtn.textContent = 'Arreglar';
            }
          });
          rem.appendChild(fixBtn);
        }
        if (repo.fix_major) {
          const note = document.createElement('span');
          note.style = 'font-size:10.5px; color:var(--warn);';
          note.textContent = 'Algunas requieren cambio mayor (revisa antes de forzar).';
          rem.appendChild(note);
        }
        detail.appendChild(rem);
      }

      // Findings
      findings.forEach(f => {
        const sev = SEV[f.severity] || ['var(--fg-3)', f.severity || ''];
        const row = document.createElement('div');
        row.style = 'display:flex; align-items:baseline; gap:8px; padding:5px 0; font-size:11.5px; border-top:1px solid rgba(255,255,255,.04);';
        row.innerHTML = `
          <span style="color:${sev[0]}; font-weight:600; min-width:56px; text-transform:capitalize;">${esc(sev[1])}</span>
          <span style="font-family:var(--font-mono); color:var(--fg-1); min-width:0;">${esc(f.package)}${f.range ? ' <span style=\'color:var(--fg-3)\'>' + esc(f.range) + '</span>' : ''}</span>
          <span style="color:var(--fg-2); flex:1;">${esc(f.title)}${f.fix ? ' — <span style=\'color:var(--good)\'>' + esc(f.fix) + '</span>' : ''}</span>`;
        detail.appendChild(row);
      });

      div.appendChild(detail);
      head.addEventListener('click', () => {
        const open = detail.style.display !== 'none';
        detail.style.display = open ? 'none' : 'block';
        const car = head.querySelector('.sec-caret');
        if (car) car.textContent = open ? '▸' : '▾';
      });
    }

    container.appendChild(div);
  });
}

const CICD_STACK_LABELS = { tauri: 'Tauri (Node + Rust)', node: 'Node.js', python: 'Python', rust: 'Rust', go: 'Go' };

function renderCicdDetect(det, repoPath) {
  const c = document.getElementById('cicd-results');
  if (!c) return;
  c.innerHTML = '';
  if (!det || det.ok === false) {
    c.innerHTML = `<div class="desc" style="margin-left:0;">${esc((det && det.error) || 'No se pudo detectar el stack.')}</div>`;
    return;
  }
  const detected = det.detected || [];
  if (detected.length === 0) {
    c.innerHTML = '<div class="desc" style="margin-left:0;">Sin stack soportado (node / python / rust / go) en este repo.</div>';
    return;
  }

  const panel = document.createElement('div');
  panel.className = 'repo-item glass-panel';
  const ciBadge = det.has_ci
    ? '<span style="color:var(--warn)">Ya tiene ci.yml</span>'
    : '<span style="color:var(--good)">Sin CI todavia</span>';
  panel.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px;">
      <b>${esc(CICD_STACK_LABELS[det.primary] || det.primary || 'Detectado')}</b>
      ${ciBadge}
    </div>
    <div style="font-size:11px; color:var(--fg-3); margin-top:6px;">${esc(det.summary || detected.map(x => CICD_STACK_LABELS[x] || x).join(', '))}</div>`;

  const controls = document.createElement('div');
  controls.style = 'display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px;';
  const sel = document.createElement('select');
  detected.forEach(id => {
    const o = document.createElement('option');
    o.value = id;
    o.textContent = CICD_STACK_LABELS[id] || id;
    if (id === det.primary) o.selected = true;
    sel.appendChild(o);
  });
  const btnPreview = document.createElement('button');
  btnPreview.className = 'cta';
  btnPreview.textContent = tr('b_preview');
  btnPreview.style = 'height:34px; padding:0 14px; font-size:12px;';
  const btnInject = document.createElement('button');
  btnInject.className = 'cta warn';
  btnInject.textContent = tr('b_inject');
  btnInject.style = 'height:34px; padding:0 14px; font-size:12px;';
  controls.appendChild(sel);
  controls.appendChild(btnPreview);
  controls.appendChild(btnInject);
  panel.appendChild(controls);

  const pre = document.createElement('pre');
  pre.style = 'margin-top:14px; background:rgba(0,0,0,.28); border:1px solid var(--border, #2a2a2a); border-radius:8px; padding:14px; overflow:auto; max-height:360px; font-family:var(--font-mono); font-size:12px; white-space:pre; display:none;';
  panel.appendChild(pre);

  btnPreview.addEventListener('click', async () => {
    btnPreview.disabled = true;
    const gen = await runPython('cicd_generate', [repoPath, sel.value]);
    btnPreview.disabled = false;
    if (gen && gen.ok) { pre.style.display = 'block'; pre.textContent = gen.yaml; }
    else log(`[ERROR] ${(gen && gen.error) || 'No se pudo generar el workflow.'}`, 'var(--bad)');
  });

  btnInject.addEventListener('click', async () => {
    btnInject.disabled = true;
    const prev = btnInject.textContent;
    btnInject.textContent = tr('scanning');
    let res = await runPython('cicd_inject', [repoPath, sel.value]);
    if (res && res.ok === false && /force/i.test(res.error || '')) {
      log('> Ya existe un workflow. Sobrescribiendo...', 'var(--warn)');
      res = await runPython('cicd_inject', [repoPath, sel.value, 'force']);
    }
    btnInject.disabled = false;
    btnInject.textContent = prev;
    if (res && res.ok) log(`[✔] ${res.message} → ${res.path}`, 'var(--good)');
    else if (res) log(`[ERROR] ${res.error}`, 'var(--bad)');
  });

  c.appendChild(panel);
}

function renderReflog(path, data) {
  let container = document.getElementById('reflog-results');
  if (!container) {
    container = document.createElement('div');
    container.id = 'reflog-results';
    container.style = 'margin-top:24px; display:flex; flex-direction:column; gap:8px;';
    document.getElementById('reflog').appendChild(container);
  }
  container.innerHTML = '';
  if (!data.entries || data.entries.length === 0) {
    container.innerHTML = '<div class="desc" style="margin-left:0;">Sin historial de reflog.</div>';
    return;
  }
  data.entries.forEach(e => {
    const row = document.createElement('div');
    row.className = 'repo-item glass-panel';
    const head = document.createElement('div');
    head.style = 'display:flex; justify-content:space-between; width:100%; align-items:center; gap:12px;';
    head.innerHTML = `
      <div><b style="color:var(--brand)">${esc(e.hash)}</b>
        <span style="color:var(--fg-3)">(${esc(e.time)})</span></div>`;
    const btn = document.createElement('button');
    btn.className = 'cta warn';
    btn.style = 'height:30px; padding:0 12px; font-size:11px;';
    btn.textContent = 'Revertir aqui';
    btn.addEventListener('click', async () => {
      btn.disabled = true; btn.textContent = 'Revirtiendo...';
      const res = await runPython('restore', [path, e.hash]);
      if (res && res.ok) log(`[✔] ${res.message}`, 'var(--good)');
      btn.disabled = false; btn.textContent = 'Revertir aqui';
    });
    head.appendChild(btn);
    const sub = document.createElement('div');
    sub.style = 'font-size:11px; margin-top:4px;';
    sub.textContent = e.action;
    row.appendChild(head);
    row.appendChild(sub);
    container.appendChild(row);
  });
}

function on(id, handler) {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', handler);
}

on('btn-prune-all', async () => {
  const btn = document.getElementById('btn-prune-all');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log('> Buscando ramas muertas (git branch --merged)...', 'var(--warn)');
  await runPython('bg_refresh_pruner', globalGithubPath ? [globalGithubPath] : []);
  const data = await runPython('prune_all', globalGithubPath ? [globalGithubPath] : []);
  if (data) renderPruneList(data);
  if (btn) { btn.disabled = false; btn.textContent = tr('b_scanall'); }
});

on('btn-sync-all', async () => {
  const btn = document.getElementById('btn-sync-all');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log('> Sincronizando radar (fetch en todos los repos)...', 'var(--warn)');
  await runPython('bg_refresh_sync', globalGithubPath ? [globalGithubPath] : []);
  const data = await runPython('sync_all', globalGithubPath ? [globalGithubPath] : []);
  if (data) renderSyncList(data);
  if (btn) { btn.disabled = false; btn.textContent = tr('b_sync'); }
});

on('btn-secops-all', async () => {
  const btn = document.getElementById('btn-secops-all');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log('> Auditando dependencias (npm/pip audit, puede tardar)...', 'var(--warn)');
  await runPython('bg_refresh_secops', globalGithubPath ? [globalGithubPath] : []);
  const data = await runPython('secops_all', globalGithubPath ? [globalGithubPath] : []);
  if (data) renderSecopsList(data);
  if (btn) { btn.disabled = false; btn.textContent = tr('b_audit'); }
});

on('btn-cicd-detect', async () => {
  const sel = document.getElementById('cicd-repo-select');
  const path = sel ? sel.value : '';
  if (!path || path === 'undefined') { log('[ERROR] Selecciona un repositorio.', 'var(--bad)'); return; }
  const btn = document.getElementById('btn-cicd-detect');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log('> Detectando stack para CI/CD...', 'var(--warn)');
  const det = await runPython('cicd_detect', [path]);
  renderCicdDetect(det, path);
  if (btn) { btn.disabled = false; btn.textContent = tr('b_detect'); }
});

async function loadTemplates() {
  if (!IN_TAURI) return;
  const sel = document.getElementById('project-template');
  if (!sel) return;
  const res = await runPython('templates');
  if (res && res.ok && Array.isArray(res.templates)) {
    const prev = sel.value;
    sel.innerHTML = '';
    res.templates.forEach(t => {
      const o = document.createElement('option');
      o.value = t.id; o.textContent = t.label;
      sel.appendChild(o);
    });
    if (prev) sel.value = prev;
    const hint = document.getElementById('tpl-dir-hint');
    if (hint && res.dir) hint.textContent = 'Tus plantillas propias viven en: ' + res.dir;
  }
}

on('btn-tpl-save', async () => {
  const repoSel = document.getElementById('tpl-save-repo');
  const nameInp = document.getElementById('tpl-save-name');
  const repo = repoSel ? repoSel.value : '';
  const name = nameInp ? nameInp.value.trim() : '';
  if (!repo || repo === 'undefined') { log('[ERROR] Selecciona un repositorio.', 'var(--bad)'); return; }
  if (!name) { log('[ERROR] Ponle un nombre a la plantilla.', 'var(--bad)'); return; }
  const btn = document.getElementById('btn-tpl-save');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log(`> Guardando "${name}" como plantilla...`, 'var(--warn)');
  const res = await runPython('template_save', [repo, name]);
  if (res && res.ok) {
    log(`[✔] ${res.message}`, 'var(--good)');
    if (nameInp) nameInp.value = '';
    await loadTemplates();   // aparece ya en el desplegable de plantillas
  } else if (res) {
    log(`[ERROR] ${res.error || 'No se pudo guardar.'}`, 'var(--bad)');
  }
  if (btn) { btn.disabled = false; btn.textContent = tr('b_save_tpl'); }
});

on('btn-init', async () => {
  const name = (document.getElementById('project-name') || {}).value || '';
  if (!name.trim()) { log('[ERROR] Escribe un nombre de proyecto.', 'var(--bad)'); return; }
  const tplSel = document.getElementById('project-template');
  const template = tplSel ? tplSel.value : 'python';
  const btn = document.getElementById('btn-init');
  if (btn) { btn.disabled = true; btn.textContent = tr('scanning'); }
  log(`> Construyendo arquitectura para "${name}" (${template})...`, 'var(--warn)');
  const res = await runPython('init', [name.trim(), template]);
  if (res && res.ok) {
    log(`[✔] ${res.message}`, 'var(--good)');
    const inp = document.getElementById('project-name'); if (inp) inp.value = '';
    if (globalGithubPath) { await runPython('bg_refresh_repos', [globalGithubPath]); }
  } else if (res) {
    log(`[ERROR] ${res.error || 'No se pudo crear el proyecto.'}`, 'var(--bad)');
  }
  if (btn) { btn.disabled = false; btn.textContent = tr('b_build'); }
});

on('btn-inspect', async () => {
  const sel = document.getElementById('ai-repo-select');
  const path = sel ? sel.value : '';
  if (!path) { log('[ERROR] Selecciona un repositorio primero.', 'var(--bad)'); return; }
  const provider = localStorage.getItem('ai_provider') || 'ollama';
  const endpoint = localStorage.getItem('ai_endpoint') || 'http://localhost:11434/api/generate';
  const model = localStorage.getItem('ai_model') || 'llama3';
  const key = localStorage.getItem('ai_key') || 'NONE';

  const box = document.getElementById('ai-review-results');
  if (box) {
    box.style.display = 'block';
    box.textContent = 'Llamando al Tech Lead IA (analizando el último commit)...';
  }
  const data = await runPython('ai_review', [path, provider, endpoint, model, key]);
  if (!box) return;
  if (data && data.review) {
    box.textContent = '';
    const head = document.createElement('div');
    head.style = 'color:var(--brand); margin-bottom:12px;';
    head.textContent = '=== REPORTE DEL TECH LEAD ===';
    const body = document.createElement('div');
    body.textContent = data.review;
    box.appendChild(head);
    box.appendChild(body);
  } else {
    box.textContent = 'Fallo al obtener revisión. ¿Está Ollama corriendo / API key correcta?';
  }
});

const aiProviderSelect = document.getElementById('ai-provider');
const aiEndpoint = document.getElementById('ai-endpoint');
const aiModel = document.getElementById('ai-model');
const aiKey = document.getElementById('ai-key');

if (aiProviderSelect) {
  if (localStorage.getItem('ai_provider')) aiProviderSelect.value = localStorage.getItem('ai_provider');
  if (localStorage.getItem('ai_endpoint')) aiEndpoint.value = localStorage.getItem('ai_endpoint');
  if (localStorage.getItem('ai_model')) aiModel.value = localStorage.getItem('ai_model');
  if (localStorage.getItem('ai_key')) aiKey.value = localStorage.getItem('ai_key');

  aiProviderSelect.addEventListener('change', (e) => {
    if (e.target.value === 'ollama') {
      aiEndpoint.value = 'http://localhost:11434/api/generate';
      aiModel.value = 'llama3';
    } else {
      aiEndpoint.value = e.target.value === 'openai'
        ? 'https://api.openai.com/v1/chat/completions'
        : 'https://api.anthropic.com/v1/messages';
      aiModel.value = e.target.value === 'openai' ? 'gpt-4o' : 'claude-3-5-sonnet-20240620';
    }
  });
}

// ---------------------------------------------------------------------------
// Estado del motor de IA (Ollama) + Maquina del Tiempo (reflog de todos)
// ---------------------------------------------------------------------------
function aiConfigNow() {
  const provider = (aiProviderSelect && aiProviderSelect.value) || localStorage.getItem('ai_provider') || 'ollama';
  const endpoint = (aiEndpoint && aiEndpoint.value) || localStorage.getItem('ai_endpoint') || 'http://localhost:11434/api/generate';
  return { provider, endpoint };
}

function setBanner(elId, textId, state, text) {
  const el = document.getElementById(elId);
  const tx = document.getElementById(textId);
  if (el) el.className = 'ai-banner ai-banner--' + state;
  if (tx) tx.textContent = text;
}

async function checkOllama() {
  const { provider, endpoint } = aiConfigNow();
  const btn = document.getElementById('btn-inspect');
  if (provider !== 'ollama') {
    const hasKey = !!((aiKey && aiKey.value) || localStorage.getItem('ai_key'));
    setBanner('ollama-status', 'ollama-status-text', hasKey ? 'ok' : 'bad',
      hasKey ? `${provider}: API key configurada.` : `${provider}: falta la API key (ve a Ajustes IA).`);
    if (btn) btn.disabled = !hasKey;
    return;
  }
  setBanner('ollama-status', 'ollama-status-text', 'wait', tr('ollama_check'));
  if (btn) btn.disabled = true;
  const res = await runPython('ai_status', ['ollama', endpoint]);
  const ok = !!(res && res.available);
  if (ok) {
    const models = (res.models || []).slice(0, 4).join(', ');
    setBanner('ollama-status', 'ollama-status-text', 'ok', tr('ollama_on') + (models ? ' — ' + models : ''));
  } else {
    setBanner('ollama-status', 'ollama-status-text', 'bad', tr('ollama_off'));
  }
  if (btn) btn.disabled = !ok;
}

async function testAiConfig() {
  const { provider, endpoint } = aiConfigNow();
  if (provider !== 'ollama') {
    const hasKey = !!(aiKey && aiKey.value);
    setBanner('ai-config-status', 'ai-config-status-text', hasKey ? 'ok' : 'bad',
      hasKey ? `${provider}: API key lista.` : `${provider}: introduce tu API key arriba.`);
    return;
  }
  setBanner('ai-config-status', 'ai-config-status-text', 'wait', tr('ollama_check'));
  const res = await runPython('ai_status', ['ollama', endpoint]);
  if (res && res.available) {
    const models = (res.models || []).join(', ') || '(sin modelos: haz "ollama pull llama3")';
    setBanner('ai-config-status', 'ai-config-status-text', 'ok', tr('ollama_on') + ' — ' + models);
  } else {
    setBanner('ai-config-status', 'ai-config-status-text', 'bad', tr('ollama_off'));
  }
}

function renderReflogAll(data) {
  const c = document.getElementById('reflog-all-results');
  if (!c) return;
  c.innerHTML = '';
  const repos = (data && data.repos) || [];
  if (!repos.length) {
    c.innerHTML = `<div class="desc" style="margin-left:0;">${esc(tr('reflog_empty'))}</div>`;
    return;
  }
  repos.forEach(repo => {
    const box = document.createElement('div');
    box.className = 'repo-item glass-panel';
    const head = document.createElement('div');
    head.style = 'display:flex; justify-content:space-between; align-items:center; width:100%; gap:12px; margin-bottom:6px;';
    const entries = repo.entries || [];
    head.innerHTML = `<b>${esc(repo.name)}</b><span style="font-size:11px;color:var(--fg-3)">${entries.length} ${entries.length === 1 ? 'entrada' : 'entradas'}</span>`;
    box.appendChild(head);
    if (!entries.length) {
      const e = document.createElement('div');
      e.className = 'desc'; e.style = 'margin-left:0; font-size:11px;';
      e.textContent = tr('reflog_empty');
      box.appendChild(e);
    } else {
      entries.forEach(en => {
        const row = document.createElement('div');
        row.style = 'display:flex; align-items:center; gap:10px; padding:6px 0; border-top:1px solid var(--hairline); font-family:var(--font-mono); font-size:11.5px;';
        row.innerHTML =
          `<span style="color:var(--brand); min-width:62px;">${esc(en.hash)}</span>` +
          `<span style="color:var(--fg-3); min-width:82px;">${esc(en.time)}</span>` +
          `<span style="color:var(--fg-1); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${esc(en.action)}</span>`;
        const btn = document.createElement('button');
        btn.className = 'cta ghost';
        btn.style = 'height:26px; padding:0 10px; font-size:10.5px;';
        btn.textContent = tr('b_restore');
        btn.dataset.armed = '0';
        btn.addEventListener('click', async () => {
          // Doble confirmacion (reset --hard es destructivo): 1er click arma, 2o ejecuta.
          if (btn.dataset.armed !== '1') {
            btn.dataset.armed = '1';
            btn.textContent = tr('b_confirm');
            btn.classList.remove('ghost'); btn.classList.add('warn');
            setTimeout(() => {
              if (btn.dataset.armed === '1') {
                btn.dataset.armed = '0'; btn.textContent = tr('b_restore');
                btn.classList.add('ghost'); btn.classList.remove('warn');
              }
            }, 3500);
            return;
          }
          btn.dataset.armed = '0'; btn.disabled = true; btn.textContent = '…';
          const res = await runPython('restore', [repo.path, en.hash]);
          if (res && res.ok) log(`[✔] ${repo.name}: ${res.message}`, 'var(--good)');
          else if (res) log(`[ERROR] ${repo.name}: ${res.error || ''}`, 'var(--bad)');
          btn.disabled = false; btn.textContent = tr('b_restore');
          btn.classList.add('ghost'); btn.classList.remove('warn');
        });
        row.appendChild(btn);
        box.appendChild(row);
      });
    }
    c.appendChild(box);
  });
}

async function loadReflogAll() {
  if (!IN_TAURI || !globalGithubPath) return;
  const c = document.getElementById('reflog-all-results');
  if (c) c.innerHTML = `<div class="desc" style="margin-left:0;">${esc(tr('scanning'))}</div>`;
  const data = await runPython('reflog_all', [globalGithubPath, '6']);
  if (data) renderReflogAll(data);
}

on('btn-test-ai', testAiConfig);
on('btn-ollama-retry', checkOllama);
on('btn-reflog-all', loadReflogAll);

on('btn-save-ai', () => {
  if (!aiProviderSelect) return;
  localStorage.setItem('ai_provider', aiProviderSelect.value);
  localStorage.setItem('ai_endpoint', aiEndpoint.value);
  localStorage.setItem('ai_model', aiModel.value);
  localStorage.setItem('ai_key', aiKey.value);
  log('[✔] Configuracion de IA guardada en local.', 'var(--good)');
});

on('btn-theme', toggleTheme);
on('btn-lang', toggleLang);

function wireLink(id, url) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('click', (e) => {
    e.preventDefault();
    if (IN_TAURI) { openExternal(url).catch(() => {}); }
    else { try { window.open(url, '_blank'); } catch (_) {} }
  });
}
wireLink('link-portfolio', 'https://ivanjonasfc.dev');
wireLink('link-github', 'https://github.com/IvanjonasFC');

on('win-min', async () => { try { (await tauriWin()).minimize(); } catch (_) {} });
on('win-max', async () => { try { const w = await tauriWin(); await w.toggleMaximize(); } catch (_) {} });
on('win-close', async () => { try { (await tauriWin()).close(); } catch (_) {} });
document.querySelectorAll('.rz').forEach(el => {
  el.addEventListener('mousedown', async () => {
    try { const w = await tauriWin(); await w.startResizeDragging(el.dataset.rz); } catch (_) {}
  });
});

on('btn-picker', (e) => {
  const m = document.getElementById('picker-menu');
  if (m) m.classList.toggle('open');
});
document.addEventListener('click', (e) => {
  const pk = document.querySelector('.picker');
  const m = document.getElementById('picker-menu');
  if (pk && m && !pk.contains(e.target)) m.classList.remove('open');
});
on('btn-picker-save', async () => {
  const inp = document.getElementById('picker-input');
  const path = inp ? inp.value.trim() : '';
  if (!path) { log('[ERROR] Escribe una ruta.', 'var(--bad)'); return; }
  const res = await runPython('set_root', [path]);
  if (res && res.ok) {
    log(`[✔] Carpeta fijada: ${res.root} (${res.repos_detectados} repos).`, 'var(--good)');
    document.getElementById('picker-menu').classList.remove('open');
    await fetchKPIs();
  }
});
on('btn-rescan', async () => {
  const m = document.getElementById('picker-menu'); if (m) m.classList.remove('open');
  await fetchKPIs();
});

const searchInput = document.getElementById('search-input');
if (searchInput) {
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll('#repo-grid .repo-item').forEach(el => {
      el.style.display = (el.dataset.name || '').includes(q) ? '' : 'none';
    });
  });
}
window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    if (searchInput) searchInput.focus();
  }
});

// ---------------------------------------------------------------------------
// Worker de Fondo (Auto-Refresh)
// ---------------------------------------------------------------------------
function isTabActive(tab) {
  const el = document.querySelector(`.nav-item[data-tab="${tab}"]`);
  return !!(el && el.classList.contains('active'));
}

// Helpers de refresco de vista: LEEN de la cache (SQLite) y pintan.
async function refreshDashboardView() {
  const data = await runPython('scan');
  if (data && data.ok) {
    globalGithubPath = data.path || globalGithubPath;
    setKPI('kpi-total', data.total);
    setKPI('kpi-uncommited', data.uncommitted, data.uncommitted > 0);
    renderRepoGrid(data.repos);
  }
}
async function refreshAutosyncView() {
  const data = await runPython('sync_all', globalGithubPath ? [globalGithubPath] : []);
  if (data && data.ok) renderSyncList(data);
}
async function refreshPrunerView() {
  const data = await runPython('prune_all', globalGithubPath ? [globalGithubPath] : []);
  if (data) renderPruneList(data);
}
async function refreshSecopsView() {
  const data = await runPython('secops_all', globalGithubPath ? [globalGithubPath] : []);
  if (data) renderSecopsList(data);
}

// Al abrir una pestaña: pinta la cache al instante y, para las baratas,
// dispara un refresco en segundo plano. SecOps NO se auto-audita al abrir
// (npm/pip audit es lento): se lee la cache y el usuario pulsa "Auditar Todos".
async function onTabShown(tab) {
  if (!IN_TAURI) return;
  if (tab === 'inspector') { checkOllama(); return; }
  if (tab === 'ai-config') { return; }        // el usuario pulsa "Probar conexion"
  if (!globalGithubPath) return;
  try {
    if (tab === 'dashboard') { await refreshDashboardView(); }
    else if (tab === 'autosync') { await refreshAutosyncView(); }
    else if (tab === 'pruner') {
      await refreshPrunerView();               // cache primero (instantaneo)
      runPython('bg_refresh_pruner', [globalGithubPath]).then(() => {
        if (isTabActive('pruner')) refreshPrunerView();
      });
    }
    else if (tab === 'secops') { await refreshSecopsView(); }
    else if (tab === 'reflog') { await loadReflogAll(); }
  } catch (_) { /* silencioso: el worker reintenta */ }
}

let isRefreshing = false;
let workerTick = 0;
async function backgroundWorker() {
  if (!IN_TAURI || !globalGithubPath || isRefreshing) return;
  isRefreshing = true;
  try {
    workerTick++;

    // Cada ciclo (30s): estado de repos + radar de sync (barato).
    await runPython('bg_refresh_repos', [globalGithubPath]);
    if (isTabActive('dashboard')) await refreshDashboardView();

    await runPython('bg_refresh_sync', [globalGithubPath]);
    if (isTabActive('autosync')) await refreshAutosyncView();

    // Cada ~90s: ramas muertas (git branch --merged, coste medio).
    if (workerTick % 3 === 0) {
      await runPython('bg_refresh_pruner', [globalGithubPath]);
      if (isTabActive('pruner')) await refreshPrunerView();
    }

    // Cada ~10min: auditoria de dependencias (npm/pip audit, LENTO).
    if (workerTick % 20 === 0) {
      await runPython('bg_refresh_secops', [globalGithubPath]);
      if (isTabActive('secops')) await refreshSecopsView();
    }
  } catch (e) {
  }
  isRefreshing = false;
}

// ---------------------------------------------------------------------------
// Inicializacion
// ---------------------------------------------------------------------------
async function boot() {
  log(tr('boot'));
  initTheme();
  applyLang();
  await resolveEnv();
  
  if (IN_TAURI) {
    // Los controles de ventana (min/max/cerrar) ya se cablean arriba con
    // on('win-min' | 'win-max' | 'win-close'); no re-enganchar aqui con IDs
    // inexistentes (btn-win-*), que lanzaba un TypeError y cortaba el arranque.
    await fetchKPIs();
    await loadTemplates();

    setTimeout(backgroundWorker, 1000);
    setInterval(backgroundWorker, 30000);
  } else {
    await fetchKPIs();
  }
}
window.addEventListener('DOMContentLoaded', boot);

// ---------------------------------------------------------------------------
// Efecto de fondo (halo que sigue el cursor)
// ---------------------------------------------------------------------------



  // --- Floating Console Logic ---
  const term = document.getElementById('console-drawer');
  const termHead = document.getElementById('console-toggle');
  if (term && termHead) {
    let isDragging = false;
    let didDrag = false;
    let startX, startY, initialX = 0, initialY = 0;

    termHead.addEventListener('pointerdown', (e) => {
      if (term.classList.contains('collapsed')) return;
      isDragging = true;
      didDrag = false;
      startX = e.clientX;
      startY = e.clientY;
      term.style.transition = 'none';
      termHead.setPointerCapture(e.pointerId);
    });

    termHead.addEventListener('pointermove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) didDrag = true;
      if (didDrag) {
        e.preventDefault();
        term.style.transform = 	ranslate3d( + (initialX + dx) + px,  + (initialY + dy) + px, 0);
      }
    });

    termHead.addEventListener('pointerup', (e) => {
      if (isDragging) {
        isDragging = false;
        termHead.releasePointerCapture(e.pointerId);
        term.style.transition = '';
        if (didDrag) {
          initialX += e.clientX - startX;
          initialY += e.clientY - startY;
        }
      }
    });

    termHead.addEventListener('click', (e) => {
      if (didDrag) {
        e.preventDefault();
        e.stopPropagation();
        return;
      }
      term.classList.toggle('collapsed');
      if (!term.classList.contains('collapsed')) {
        term.classList.remove('has-unread');
      }
    });
  }



// Background Blob Pointer Tracking
(function() {
  const blob = document.getElementById('blob');
  if (blob) {
    let _bx = innerWidth * 0.6, _by = innerHeight * 0.4, _bq = false;
    function paintBlob() {
      _bq = false;
      blob.style.transform = "translate3d(" + _bx + "px, " + _by + "px, 0) translate(-50%, -50%)";
    }
    window.addEventListener('pointermove', (e) => {
      _bx = e.clientX; _by = e.clientY;
      if (!_bq) { _bq = true; requestAnimationFrame(paintBlob); }
    }, { passive: true });
    paintBlob();
  }
})();


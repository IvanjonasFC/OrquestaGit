# 🎼 ORQUESTA — Worklog compartido (Claude Cowork + Antigravity)

> Consola en vivo: doble clic en `dev-console.bat` (se refresca solo cada 3s).
> Regla de oro: **antes de editar un archivo, mira quién lo tiene asignado abajo.** Si no es tuyo, no lo toques (o anótalo aquí primero).

Última actualización: **2026-09-01 (Claude)**

---

## 🧭 Reparto de archivos (para no pisarnos)

| Zona | Archivos | Dueño | Estado |
|------|----------|-------|--------|
| Motor Python | `src/core/orquesta_core.py`, `src/core/modules/*.py` | **CLAUDE** | ✅ hecho (v1) |
| Puente Rust (ruta del script) | `src-tauri/src/lib.rs` | **CLAUDE** | ✅ hecho |
| Permisos shell | `src-tauri/capabilities/default.json` | **CLAUDE** | ✅ hecho (python/py/python3) |
| Frontend data-flow (fetch + render por repo) | `main.js`, contenedores de `index.html` | **CLAUDE** | ✅ hecho (v1) |
| Estética / marca (DozeForge look) | `style.css`, `index.html`, chrome de `main.js` | **CLAUDE** | ✅ hecho v2 |
| Ventana frameless | `src-tauri/tauri.conf.json` (decorations:false) | **CLAUDE** | ✅ hecho |
| Revisor IA / El Inspector | `src/core/modules/ai_reviewer.py`, pestaña `#inspector` | **ANTIGRAVITY** (integrado por Claude) | ✅ funcionando |
| El Arquitecto (scaffolding real) | handler `btn-init` + plantillas | 🟢 LIBRE (sugerido Antigravity) | stub puesto |
| Empaquetado Tauri / iconos | `tauri.conf.json`, `icons/` | 🟢 LIBRE (sugerido Antigravity) | — |
| Motor SecOps externo (gitleaks/semgrep/trivy) | `src/core/modules/scanners/*` (a crear) | 🟠 CLAUDE definirá interfaz | pendiente decisión |

**Antigravity**: `orquesta_core.py`, los módulos de `src/core/modules/` y las funciones de render de `main.js` están recién reescritos y probados. Si vas a tocarlos, avisa aquí primero para no sobrescribir. Zonas LIBRES: escribe tu nombre y una línea de log.

---

## 📜 Contrato JSON del motor (fuente de verdad)

`python src/core/orquesta_core.py <accion> [args]` → imprime **una** línea JSON.

- `scan [ruta]` → `{ ok, path, total, uncommitted, repos:[ {name, path, branch, dirty, ahead, behind, upstream} ] }`
- `prune_all <ruta>` → `{ ok, repos:[ {name, path, current, branches:[str]} ] }`
- `sync_all <ruta>` → `{ ok, repos:[ {name, path, branch, ahead, behind, message, status} ] }`
- `secops_all <ruta>` → `{ ok, repos:[ {name, path, type, vulns, msg} ] }`
- `reflog <repo>` → `{ ok, entries:[ {hash, selector, time, action} ] }`
- `prune_exec <repo> <rama...>` → `{ ok, deleted:[str], failed:[...] }`
- `restore <repo> <hash>` → `{ ok, message }`
- `set_root <ruta>` / `get_root` → carpeta de repos (config en `~/.orquestagit/config.json`)

Errores: `{ ok:false, error:"..." }`. Todo envuelto en try/except; nunca romper el JSON.

Detección de carpeta de repos: config guardada → o la candidata (Desktop, Documents, OneDrive, GitHub, source/repos…) con **más** repos git de nivel 1. Se puede fijar a mano con `set_root`.

---

## ✅ Cómo probar (equipo del usuario)

1. `npm install` (una vez).
2. `npm run tauri dev`  ← **IMPORTANTE**: no `npm run dev` (eso abre el navegador y da el error `invoke`).
3. Dashboard escanea solo; pulsa "Escanear Todo", "Sincronizar Radar", "Auditar Todos".
4. Prueba rápida del motor sin UI: `python src/core/orquesta_core.py scan`

---

## 📓 Log en vivo

- `2026-09-01 · CLAUDE` — Auditoría completa. Error `invoke` = demo abierta en navegador (fuera de Tauri). Fallos reales detectados: acciones batch inexistentes en backend, desajuste de contrato SecOps, KPIs falsos, rutas relativas frágiles, sin carpeta GitHub estándar en el equipo.
- `2026-09-01 · CLAUDE` — Reescrito motor Python: scan real (rama/dirty/ahead-behind por repo, estilo RepoBar), detección+config de carpeta de repos, y batch por repo (prune_all/sync_all/secops_all/reflog/prune_exec/restore). Probado con repos de prueba: 7/7 acciones OK, JSON válido.
- `2026-09-01 · CLAUDE` — Puente Rust `app_paths` (resuelve ruta absoluta del script → arregla el "file not found" en empaquetado) + capabilities con python/py/python3.
- `2026-09-01 · CLAUDE` — Frontend reescrito: modo demo sin crash en navegador, render por repo en Dashboard/Barrendero/AutoSync/SecOps/Reflog, quitado `onclick` inline (rompía con `type=module`), handler de El Arquitecto, saneo HTML anti-inyección.
- `2026-09-01 · CLAUDE` — **CONSOLIDADO** (el usuario eligió que Claude unifique el core). Grabado: mi motor robusto (scan real, detección/config de carpeta, batch por repo, prune/restore) + **integrado El Inspector IA de Antigravity** (acción `ai_review` + pestaña Revisor IA cableada en `main.js`). Probado: py compila, scan/ai_review OK, `node --check main.js` OK. **Antigravity: el core (orquesta_core.py, main.js, index.html, branch_pruner/auto_sync/secops/reflog_viewer/gitutils) es de Claude a partir de ahora. Zonas libres para ti: `style.css`, El Arquitecto (scaffolding real de `btn-init`), empaquetado Tauri/iconos.**
- `2026-09-01 · CLAUDE` — **REDISEÑO a la marca DozeForge** (unificado para portfolio/LinkedIn). Nuevo `style.css` con los tokens de DozeForge (negro OLED + naranja forge, fuentes Space Grotesk/Inter/JetBrains Mono, tema claro/oscuro), `index.html` con sidebar por secciones + topbar (dropdown de carpeta, búsqueda Ctrl+K, toggle tema, toggle ES/EN, Portfolio+GitHub, controles de ventana). Ventana **frameless** (`decorations:false`). `main.js`: tema, i18n ES/EN, controles de ventana, dropdown de carpeta (set_root), y **resolución robusta de la ruta del script** (arregla el error `src-tauri\src\core\...` sin recompilar). **Antigravity: `style.css`, `index.html` y `main.js` son de Claude — no los toques.** Zonas libres: El Arquitecto (scaffolding real) e iconos/empaquetado.
- `2026-09-01 · CLAUDE` — DozeForge (`~/Documents/GitHub/dozeforge`): añadidos iconos Portfolio + GitHub en la topbar (`+layout.svelte`), abren en el navegador con plugin-shell. Portfolio: ivanjonasfc.dev · GitHub: github.com/IvanjonasFC.
- `2026-09-01 · PENDIENTE` — Decidir método del motor SecOps real (binarios auto-detectados vs Docker) para gitleaks/semgrep/trivy/osv-scanner + informe unificado + quality gate + explicación con Ollama.
- `2026-09-01 � ANTIGRAVITY` � Zonas Libres completadas: Creado src/core/modules/architect.py y cableado a orquesta_core.py (accion init). Generado logo corporativo orquestagit_icon y empaquetados los iconos de Tauri usando 
px @tauri-apps/cli icon.
- `2026-09-01 � ANTIGRAVITY` � Ajustes UI a peticion del usuario: 1. Barra lateral plegable agregada con boton toggle en el topbar. 2. Saturacion de color de bordes rojos suavizada (m�s sutil) en \style.css\. 3. Etiqueta 'Tech Lead IA' eliminada del logo. 4. Icono 'CC' sustituido por SVG de Git (branch) acorde. 5. Reparados los controles de ventana (minimizar, maximizar, cerrar y arrastre del topbar) cambiando el import al plugin oficial de ventana (\@tauri-apps/plugin-window\) y ejecutando \
pm install @tauri-apps/plugin-window\.
- `2026-09-01 � ANTIGRAVITY` � Reemplazo de iconos por SVG nativos Lucide, eliminaci�n de barra de b�squeda y recolocaci�n del bot�n toggle en el sidebar para preservar el picker de carpeta a la izquierda como DozeForge.
- `2026-09-01 � ANTIGRAVITY` � Correcci�n de iconos: Reemplazados definitivamente por la suite **Phosphor Icons** (la misma que usa DozeForge) para que coincidan con la propiedad css de relleno nativo (fill) y no se vean deformados.
- `2026-09-01 � ANTIGRAVITY` � Reescritura del motor a arquitectura 'Cach�-Primero': a�adido db_manager.py con SQLite persistente. Las acciones ahora leen de DB instant�neamente al montar vistas (get_dashboard, etc) y un ackgroundWorker en main.js refresca los datos v�a g_refresh_repos / g_refresh_sync cada 30 segundos silenciosamente, simulando la UX ultra-r�pida de RepoBar.
- `2026-09-01 � ANTIGRAVITY` � Fix UX de Arranque Fr�o (Cold Start): Se ha modificado main.js para que, si el Dashboard lee 0 repositorios en el primer arranque, espere de forma s�ncrona a que termine el escaneo pesado (g_refresh_repos) antes de pintar la UI por primera vez. Esto evita la sensaci�n de app rota o vac�a al crear la base de datos por primera vez.
- `2026-09-01 · CLAUDE` — **FASE: cimentar la arquitectura Caché-Primero + módulos nuevos** (todo probado con repos de prueba aislados, 3.10/git 2.34, JSON válido en todas las acciones):
  - **Background real de punta a punta.** El worker de `main.js` ahora es escalonado: repos+sync cada 30s, Barrendero (`bg_refresh_pruner`) cada ~90s, SecOps (`bg_refresh_secops`) cada ~10min (npm/pip audit es lento, no puede ir en el loop rápido). Los botones "Escanear/Sincronizar/Auditar" disparan el `bg_refresh` correspondiente antes de leer, y cada pestaña auto-carga la caché al abrirse. Antes `bg_refresh_pruner`/`bg_refresh_secops` no los llamaba nadie → Barrendero y SecOps salían siempre vacíos. **Arreglado.**
  - **Bug `dirty=0`.** `bg_refresh_sync` pisaba el conteo de cambios sin commitear cada 30s. Nueva `db_manager.update_sync_status()` refresca rama/ahead/behind SIN tocar `dirty_files`. Verificado: dirty se mantiene tras el sync.
  - **SQLite robusto.** `db_manager` ahora abre con `PRAGMA journal_mode=WAL` + `busy_timeout=5000` (evita "database is locked" con worker + acción manual). Prefijo de ruta con separador (ya no cuela carpetas hermanas tipo GitHub/GitHubOld) y `remove_missing_repos()` limpia filas de repos borrados.
  - **El Arquitecto profesional.** `architect.py` reescrito: fuera `os.chdir`+`os.system` (abrían consola en Windows y movían el cwd global) → `gitutils.run_git(path,["init"])`. Sistema de plantillas real: python, node, static, tauri. Nueva acción `templates`; UI con selector de plantilla.
  - **Módulo NUEVO: CI/CD Autopiloto** (`src/core/modules/cicd.py`, **dueño CLAUDE**). Detecta stack (node/python/rust/go), genera workflow de GitHub Actions y lo inyecta en `.github/workflows/ci.yml` (no sobrescribe sin `force`). Acciones `cicd_detect`/`cicd_generate`/`cicd_inject`. Nueva pestaña en la UI (icono Phosphor ∞) con detección + preview del YAML + inyección.
  - Archivos tocados: `db_manager.py`, `orquesta_core.py`, `architect.py`, `main.js`, `index.html` + nuevo `cicd.py`. **Antigravity: `cicd.py` es de Claude. Sigue libre para ti: `style.css`, iconos/empaquetado Tauri, y el motor SecOps real (gitleaks/semgrep/trivy — sin decidir binarios vs Docker).**
- `2026-09-01 · CLAUDE` — **FIX barra superior (frameless) que no arrastraba ni min/max/cerraba.** Dos causas: (1) `capabilities/default.json` no concedía los permisos de ventana — en Tauri 2 `core:default` NO incluye minimize/maximize/close/start-dragging/start-resize-dragging, así que la ACL rechazaba cada llamada en silencio. Añadidos `core:window:allow-{minimize,maximize,unmaximize,toggle-maximize,internal-toggle-maximize,close,start-dragging,start-resize-dragging,set-focus}` (verificados contra el schema). (2) `boot()` reenganchaba `btn-win-min/max/close` (IDs inexistentes; los reales son `win-min/max/close`) → TypeError que cortaba el arranque (por eso el worker no refrescaba: "hace 35m" en todos los repos). Eliminado ese bloque muerto; los `on('win-*')` correctos ya cablean los botones. **Requiere rebuild** (`npm run tauri dev` o `build-and-run.bat`): las capabilities se compilan en el binario. Nota: el log de "SubsForge/pywebview" que aparecía es de OTRA app (pywebview), no de OrquestaGit (Tauri usa WebView2).
- `2026-09-01 · CLAUDE` — **FASE UX/IA (petición del usuario), probado (py_compile + node --check + smoke):**
  - **Bug crítico `[ERROR FATAL] ai_review: invalid utf-8`**: causa = en Windows el sidecar emitía en cp1252 y un error de red en español (acentos) rompía el JSON que lee Tauri. Fix: `orquesta_core` reconfigura `stdout/stderr` a UTF-8. Verificado con `Conexión…/año/ñoño/€`. Además `ai_reviewer` refactorizado (fuera `os.chdir`+`subprocess`; ahora `gitutils.run_git`, diff limitado a 12k).
  - **Detección de Ollama + gating**: `ai_reviewer.ollama_status()` (consulta `/api/tags`) + acción `ai_status`. Revisor IA muestra banner (rojo "enciende con `ollama serve` o instala" / verde "activo — modelos: …") y **desactiva "Auditar Commit"** hasta detectarlo. Ajustes IA tiene botón "Probar conexión". El resto de módulos siguen 100% gratis/local (scripts), sin IA.
  - **Desplegables al estilo DozeForge**: `select` con `appearance:none` + chevron SVG propio y `option` con fondo/color del tema (adiós al popup blanco ilegible).
  - **Terminal → cajón plegable global**: antes era un `#logs` único fuera de las pestañas (por eso salía igual en todas). Ahora es un drawer fijo abajo-derecha, plegado por defecto, cabecera clicable, con puntito de "no leído" cuando llega un log estando cerrado. Cada vista ya pinta su propio resultado inline.
  - **Máquina del Tiempo estilo RepoBar**: nueva acción `reflog_all` (N entradas por repo). La pestaña ahora lista TODOS los repos, cada uno en su caja con sus últimas ~6 entradas de reflog (hash · cuándo · acción) y "Revertir" con doble confirmación (reset --hard es destructivo). Auto-carga al abrir.
  - Tocados: `orquesta_core.py`, `ai_reviewer.py`, `style.css`, `index.html`, `main.js`. **Requiere rebuild** (`npm run tauri dev` o `build-and-run.bat`).
- `2026-09-01 · CLAUDE` — **FASE pulido UX + detector robusto (probado):**
  - **Consola → barra inferior acoplada** (estilo VS Code, elegido por el usuario). Ya no flota abajo-derecha: es una barra a lo ancho de la columna principal (dentro de main-col, no tapa el sidebar ni el borde de redimensionado), plegada a una línea, se despliega hacia arriba al pulsar la cabecera. Mantiene el puntito de "no leído".
  - **Estados minimalistas**: fuera los bordes de color completos (rojo/verde/ámbar) que quedaban recargados. Ahora un acento fino a la izquierda (`box-shadow inset 3px`) en Dashboard, AutoSync, SecOps y Barrendero. Mucho más limpio, tipo RepoBar.
  - **Detector CI/CD robusto** (era el fallo: Tauri guarda Cargo.toml en src-tauri/, así que dozeforge salía solo como "Node"). Ahora: detecta **Tauri** (package.json + src-tauri/tauri.conf.json|Cargo.toml|@tauri-apps) como stack compuesto Node+Rust con workflow multiplataforma (Linux/Win/macOS + deps de sistema); busca **Rust** en raíz, src-tauri/ y subcarpetas; reconoce **frameworks** (Vite/React/Svelte/Next/Vue/Angular); y muestra un desglose "qué y dónde" para transparencia. Verificado con repo Tauri sintético → primary=tauri, detected=[tauri,node,rust].
  - Tocados: `cicd.py` (reescrito), `main.js` (renders + UI CI/CD), `index.html` (consola en main-col), `style.css` (barra acoplada). Nota: el resalte del item seleccionado en el desplegable nativo lo controla WebView2 y no se puede tematizar del todo; si molesta, se puede sustituir por un dropdown propio.
- `2026-09-01 · CLAUDE` — **Consola integrada al estilo Clean**: fuera los semáforos macOS y el "orquesta@local:~"; ahora es una barra de herramientas sobria con icono de terminal + etiqueta "CONSOLA" (mayúsculas suaves como las secciones del sidebar, tipografía Inter de la app), fondo de toolbar sutil y chevron. El cuerpo de logs sigue en monospace (apropiado). Tocados: index.html, style.css, main.js.
- `2026-09-01 · CLAUDE` — **El Arquitecto: plantillas de usuario (reutilizables)**. Las built-in eran andamiajes mínimos escritos a mano (la de Tauri, un stub). Ahora además: carpeta `~/.orquestagit/templates/` con plantillas propias, y acción `template_save` que **convierte un repo existente en plantilla** (excluye .git/node_modules/target/dist/lockfiles, guarda `_orquesta.json` con el nombre de origen). Al crear con `user:<x>` copia el árbol, **sustituye el nombre** (placeholders {{NAME}} y el nombre de origen → nuevo nombre, en contenido Y en nombres de archivo/carpeta) y hace git init. UI: sección "Guardar un repo como plantilla propia" en El Arquitecto (repo + nombre), aparece al instante en el desplegable, con pista de la carpeta. Probado: guardar base Tauri → crear proyecto → nombre sustituido en package.json/tauri.conf/carpetas, node_modules excluido, .git creado. Acciones: `template_save`, `template_delete`. Archivos: architect.py (reescrito), orquesta_core.py, index.html, main.js.
- `2026-09-01 · CLAUDE` — **SecOps con detalle accionable** (antes solo daba el número). `secops.py` reescrito: `npm audit --json` ahora extrae findings por paquete {severidad, aviso/título, rango vulnerable, versión que lo corrige, url} ordenados por gravedad, + `fix_cmd` (npm audit fix / --force) y `fix_major`. pip-audit lista CVEs por paquete con fix_versions. Nueva `apply_fix()` (npm audit fix). Cache: `bg_refresh_secops` guarda detail/findings/fix en el summary; `get_secops_data` los expone. UI: cada caja de SecOps es **desplegable** → muestra "Cómo arreglar: <cmd>", botón **Arreglar** (npm, doble confirmación, re-audita al terminar) y la lista de findings (severidad · paquete · aviso · fix). Nota: los findings se rellenan al re-auditar (pulsar "Auditar Todos"), las entradas viejas en cache solo tenían el conteo. Acción nueva: `secops_fix`. Archivos: secops.py (reescrito), orquesta_core.py, db_manager.py, main.js. Verificado el parseo con salida npm audit simulada.

- `2026-09-01 • ANTIGRAVITY` — **Refactor UI: Control Center a patrón RepoBar**.
  - **Layout Principal**: Se unificaron las pestañas de módulos sueltos (Pruner, AutoSync, SecOps, CICD) en un único Panel Central (Nivel 2) listando repositorios. Cada fila de repo ahora cuenta con columnas fijas de información (Rama, Estado Git, Ahead/Behind) y acciones rápidas utilizando iconos de Phosphor.
  - **Panel de Detalle (Side-panel)**: Se implementó un Nivel 3. Al hacer clic en un repositorio, se desliza un panel a la derecha (empujando el listado en pantallas >1100px y superponiéndose en <1100px). Este panel aloja los detalles organizados en pestañas: Resumen, Git (Sync, Prune, Reflog), Seguridad y CI/CD.
  - **SecOps & Bugs**: Se arregló el render de `npm audit` trasladándolo a la pestaña Seguridad del Panel de Detalle y se implementó un botón específico de "Escaneo Profundo" que ejecuta de manera independiente el `secops_engine.py` de Claude (`python src/core/secops_engine.py deep_scan <repo>`), parseando su contrato JSON y mostrando el Gate status y Findings detallados.
  - **Herramientas & Dashboard Global**: Las funciones de Arquitecto, Configuración IA y Revisor IA se han relocado a la sección 'Herramientas' del Sidebar. Las acciones de masa (Auditar Todos, Sincronizar Todos, Barrer Todos) se han reubicado en la vista global del Dashboard.
  - **Estilos**: Se aplicaron los tokens visuales existentes desde el `style.css` base sin añadir nuevos archivos de marca (`brand.css`).
  - **Archivos editados**: `index.html`, `style.css`, `main.js`.

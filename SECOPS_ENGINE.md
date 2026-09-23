# 🛡️ Motor SecOps real — OrquestaGit

Backend nuevo y **autónomo** (no toca `orquesta_core.py` ni el frontend). Orquesta
herramientas DevSecOps reconocidas y las normaliza a un informe único.

## Qué cubre (lo que `npm audit` no ve)
| Escáner | Detecta | Severidad |
|---------|---------|-----------|
| **Gitleaks** | Secretos/credenciales filtradas (incl. historial git) | CRITICAL |
| **Trivy** | CVEs en deps (todos los ecosistemas), secretos, IaC/Docker | según CVE |
| **osv-scanner** | CVEs en lockfiles (npm, pip, Go, Maven…) | según OSV |
| **Semgrep** | SAST: bugs/vulns en TU código (SQLi, XSS, cmd inject) | ERROR→HIGH |

Detección automática: corre solo lo instalado y degrada con guía de instalación.
Réplica ~80-90% de GitHub Advanced Security (49 $/dev/mes) gratis.

## Archivos
- `src/core/secops_engine.py` — CLI independiente.
- `src/core/scanners/` — `base.py`, `logutil.py`, `engine.py`, `gitleaks.py`, `trivy.py`, `osv.py`, `semgrep.py`.
- Log rotativo: `~/.orquestagit/logs/secops.log` (nunca a stdout).

## CLI (imprime UNA línea JSON)
```
python src/core/secops_engine.py doctor                      # qué hay instalado + cómo instalar
python src/core/secops_engine.py deep_scan <repo> [g,t,...]  # escaneo profundo de un repo
python src/core/secops_engine.py deep_scan_all <raíz>        # todos los repos de la carpeta
python src/core/secops_engine.py explain "<título>" "<detalle>" [endpoint] [model]  # Ollama
```

## Contrato del informe (`deep_scan`)
```json
{ "ok": true, "repo": "...", "path": "...", "scanned_at": "...", "duration_s": 1.2,
  "tools": { "gitleaks": "8.18", "trivy": null, ... },
  "summary": { "critical": 2, "high": 0, "medium": 0, "low": 0, "total": 2 },
  "gate": { "threshold": "high", "passed": false },
  "findings": [ { "scanner","severity","title","detail","file","line","rule","remediation" } ],
  "missing_tools": [ { "name":"trivy", "install":"..." } ],
  "errors": [] }
```
`findings` viene ordenado de más grave a menos. `gate.passed=false` si hay algo ≥ `threshold`.

## Integración (para Antigravity — SIN tocar el core)
El frontend lo invoca **igual que a `orquesta_core.py`**, como un segundo script:
```js
const out = await Command.create(PYBIN, [SCRIPT_SECOPS, 'deep_scan_all', ROOT]).execute();
// SCRIPT_SECOPS = <root>/src/core/secops_engine.py  (usa app_paths igual que el core)
```
Render sugerido en el Auditor SecOps:
- Cabecera por repo: nombre + badges `summary` (2 CRIT / 1 HIGH…) + chip del `gate` (verde PASA / rojo FALLA).
- Al desplegar: lista de `findings` (severidad · scanner · título · `file:line` · remediation).
- Si `missing_tools` no está vacío: tarjeta "Instala para cubrir más" con los comandos.
- Botón "Explicar" por finding → acción `explain` (Ollama) para el texto en lenguaje simple.

*(Alternativa: añadir en `orquesta_core.py` una acción `secops_deep` que haga passthrough al engine. Pero no es necesario: llamarlo directo evita todo acoplamiento.)*

## Instalar los escáneres (Windows)
```
scoop install gitleaks trivy        # o binarios de sus GitHub Releases
pip install semgrep                 # SAST (soporte Win limitado → WSL/Docker)
# osv-scanner: binario de github.com/google/osv-scanner/releases
```
Empieza por **Gitleaks**: máximo valor (secretos), cero configuración.

## Quality gate
Por defecto falla con severidad ≥ HIGH. Cambia `gate_threshold` en `engine.deep_scan()`
o pásalo desde un futuro ajuste de UI. Úsalo como aduana antes de `push`.

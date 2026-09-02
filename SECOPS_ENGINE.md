# SecOps engine — OrquestaGit

A standalone security backend (it does not touch `orquesta_core.py` or the
frontend). It orchestrates well-known DevSecOps tools and normalizes their output
into a single report.

## What it covers (beyond `npm audit`)

| Scanner | Detects | Severity |
|---------|---------|----------|
| **Gitleaks** | Leaked secrets / credentials (including git history) | CRITICAL |
| **Trivy** | CVEs in dependencies (all ecosystems), secrets, IaC / Docker | per CVE |
| **osv-scanner** | CVEs in lockfiles (npm, pip, Go, Maven…) | per OSV |
| **Semgrep** | SAST: bugs / vulnerabilities in your own code (SQLi, XSS, command injection) | ERROR to HIGH |

Auto-detection: it runs only the tools installed and degrades gracefully with
installation hints. It replicates roughly 80–90% of GitHub Advanced Security for
free.

## Files

- `src/core/secops_engine.py` — standalone CLI.
- `src/core/scanners/` — `base.py`, `logutil.py`, `engine.py`, `gitleaks.py`, `trivy.py`, `osv.py`, `semgrep.py`.
- Rotating log: `~/.orquestagit/logs/secops.log` (never to stdout).

## CLI (prints ONE JSON line)

```
python src/core/secops_engine.py doctor                      # what is installed + how to install
python src/core/secops_engine.py deep_scan <repo> [g,t,...]  # deep scan of one repo
python src/core/secops_engine.py deep_scan_all <root>        # every repo under a folder
python src/core/secops_engine.py explain "<title>" "<detail>" [endpoint] [model]  # Ollama
```

## Report contract (`deep_scan`)

```json
{ "ok": true, "repo": "...", "path": "...", "scanned_at": "...", "duration_s": 1.2,
  "tools": { "gitleaks": "8.18", "trivy": null },
  "summary": { "critical": 2, "high": 0, "medium": 0, "low": 0, "total": 2 },
  "gate": { "threshold": "high", "passed": false },
  "findings": [ { "scanner", "severity", "title", "detail", "file", "line", "rule", "remediation" } ],
  "missing_tools": [ { "name": "trivy", "install": "..." } ],
  "errors": [] }
```

`findings` is ordered from most to least severe. `gate.passed` is `false` if
anything is at or above `threshold`.

## Frontend integration (without touching the core)

The frontend invokes it **exactly like `orquesta_core.py`**, as a second script:

```js
const out = await Command.create(PYBIN, [SCRIPT_SECOPS, 'deep_scan_all', ROOT]).execute();
// SCRIPT_SECOPS = <root>/src/core/secops_engine.py
```

Suggested rendering in the SecOps auditor:

- Per-repo header: name + `summary` badges (2 CRIT / 1 HIGH…) + a `gate` chip (green PASS / red FAIL).
- On expand: the list of `findings` (severity · scanner · title · `file:line` · remediation).
- If `missing_tools` is non-empty: an "Install to cover more" card with the commands.
- An "Explain" button per finding calls the `explain` action (Ollama) for plain-language text.

## Installing the scanners (Windows)

```
scoop install gitleaks trivy        # or binaries from their GitHub Releases
pip install semgrep                 # SAST (limited Windows support -> WSL / Docker)
# osv-scanner: binary from github.com/google/osv-scanner/releases
```

Start with **Gitleaks**: highest value (secrets), zero configuration.

## Quality gate

By default it fails at severity >= HIGH. Change `gate_threshold` in
`engine.deep_scan()` or pass it from a future UI setting. Use it as a customs
checkpoint before `push`.

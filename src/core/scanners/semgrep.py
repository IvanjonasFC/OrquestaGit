"""Semgrep: SAST sobre TU codigo (SQLi, XSS, inyeccion de comandos, malas
practicas). Necesita red la primera vez para bajar el ruleset (--config auto).
Soporte en Windows limitado (recomendado WSL/Docker)."""
import json
from base import which, tool_version, run, Finding

NAME = "semgrep"
INSTALL = {
    "win": "pip install semgrep  (soporte Windows limitado -> WSL/Docker)",
    "unix": "pip install semgrep  ·  o brew install semgrep",
}
_SEV = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}


def detect():
    cmd = which("semgrep", "semgrep.exe")
    return (cmd, tool_version(cmd, ["--version"])) if cmd else (None, None)


def scan(repo, timeout=600):
    cmd, ver = detect()
    if not cmd:
        return None, [], "not-installed"
    try:
        r = run([cmd, "--config", "auto", "--json", "--quiet",
                 "--timeout", "0", "--metrics", "off", str(repo)],
                cwd=repo, timeout=timeout)
        try:
            data = json.loads(r.stdout or "{}")
        except Exception:
            return ver, [], "parse-error"
        findings = []
        for res in data.get("results", []):
            ex = res.get("extra", {}) or {}
            sev = _SEV.get(str(ex.get("severity", "WARNING")).upper(), "medium")
            meta = ex.get("metadata", {}) or {}
            findings.append(Finding(
                NAME, sev,
                (ex.get("message") or res.get("check_id", "")),
                detail=ex.get("message", ""),
                file=res.get("path", ""),
                line=(res.get("start", {}) or {}).get("line", 0),
                rule=res.get("check_id", ""),
                remediation=(ex.get("fix") or meta.get("fix")
                             or "Revisa y corrige el patron marcado."),
            ).norm())
        return ver, findings, None
    except Exception as e:
        return ver, [], str(e)[:160]

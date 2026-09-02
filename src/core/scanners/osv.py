"""osv-scanner (Google): CVEs conocidas en lockfiles (npm, pip, Go, Maven...).
Muy facil de correr, cero configuracion. Alternativa ligera a Trivy para deps."""
import json
from base import which, tool_version, run, Finding

NAME = "osv-scanner"
INSTALL = {
    "win": "binario de github.com/google/osv-scanner/releases",
    "unix": "brew install osv-scanner  ·  o github.com/google/osv-scanner/releases",
}
_OK = {"critical", "high", "medium", "low"}


def detect():
    cmd = which("osv-scanner", "osv-scanner.exe")
    return (cmd, tool_version(cmd, ["--version"])) if cmd else (None, None)


def _severity(vuln):
    # OSV mete el CVSS en 'severity' o en database_specific; si no, MEDIUM.
    for s in (vuln.get("severity") or []):
        txt = str(s.get("score", "")).lower()
        for lvl in ("critical", "high", "medium", "low"):
            if lvl in txt:
                return lvl
    dbs = (vuln.get("database_specific") or {})
    sv = str(dbs.get("severity", "")).lower()
    return sv if sv in _OK else "medium"


def scan(repo, timeout=300):
    cmd, ver = detect()
    if not cmd:
        return None, [], "not-installed"
    try:
        # exit code 1 = vulnerabilidades encontradas (esperado), no es error.
        r = run([cmd, "--format", "json", "-r", str(repo)], timeout=timeout)
        try:
            data = json.loads(r.stdout or "{}")
        except Exception:
            return ver, [], "parse-error"
        findings = []
        for res in (data.get("results") or []):
            src = (res.get("source", {}) or {}).get("path", "")
            for pkg in (res.get("packages") or []):
                name = (pkg.get("package", {}) or {}).get("name", "")
                for v in (pkg.get("vulnerabilities") or []):
                    findings.append(Finding(
                        NAME, _severity(v),
                        f"{v.get('id', '')} · {name}",
                        detail=(v.get("summary") or ""),
                        file=src, rule=v.get("id", ""),
                        remediation="Actualiza la dependencia a una version parcheada.",
                    ).norm())
        return ver, findings, None
    except Exception as e:
        return ver, [], str(e)[:160]

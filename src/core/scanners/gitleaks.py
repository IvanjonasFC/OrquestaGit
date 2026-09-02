"""Gitleaks: secretos y credenciales filtradas (incl. historial git).
Un secreto filtrado se trata como CRITICAL. Siempre con --redact para NO
almacenar el valor del secreto en el informe."""
import os
import json
import tempfile
from base import which, tool_version, run, Finding

NAME = "gitleaks"
INSTALL = {
    "win": "scoop install gitleaks  ·  o binario de github.com/gitleaks/gitleaks/releases",
    "unix": "brew install gitleaks  ·  o github.com/gitleaks/gitleaks/releases",
}


def detect():
    cmd = which("gitleaks", "gitleaks.exe")
    return (cmd, tool_version(cmd, ["version"])) if cmd else (None, None)


def scan(repo, timeout=300):
    cmd, ver = detect()
    if not cmd:
        return None, [], "not-installed"
    findings = []
    try:
        with tempfile.TemporaryDirectory() as td:
            report = os.path.join(td, "gitleaks.json")
            # detect = escanea el repo (incluye historial). Codigos: 0 sin
            # fugas, 1 fugas encontradas (esperado), >1 error real.
            run([cmd, "detect", "--source", str(repo),
                 "--report-format", "json", "--report-path", report,
                 "--redact", "--no-banner", "--exit-code", "0"],
                timeout=timeout)
            data = []
            try:
                with open(report, encoding="utf-8") as f:
                    data = json.load(f) or []
            except FileNotFoundError:
                data = []
            except Exception:
                return ver, [], "parse-error"
        for it in data:
            rule = it.get("RuleID", "?")
            findings.append(Finding(
                NAME, "critical", f"Secreto: {rule}",
                detail=it.get("Description") or "Posible credencial en el codigo.",
                file=it.get("File", ""), line=it.get("StartLine", 0), rule=rule,
                remediation="Rota la credencial YA y borrala del historial "
                            "(git filter-repo / BFG). Usa variables de entorno.",
            ).norm())
        return ver, findings, None
    except Exception as e:
        return ver, [], str(e)[:160]

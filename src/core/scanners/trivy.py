"""Trivy: la navaja suiza. CVEs en dependencias (todos los ecosistemas),
secretos, y misconfiguraciones IaC (Dockerfile, k8s, Terraform)."""
import json
from base import which, tool_version, run, Finding

NAME = "trivy"
INSTALL = {
    "win": "choco install trivy  ·  o binario de github.com/aquasecurity/trivy/releases",
    "unix": "brew install trivy  ·  o github.com/aquasecurity/trivy/releases",
}
_OK = {"critical", "high", "medium", "low"}


def detect():
    cmd = which("trivy", "trivy.exe")
    return (cmd, tool_version(cmd, ["--version"])) if cmd else (None, None)


def _sev(v, default="medium"):
    s = str(v or default).lower()
    return s if s in _OK else default


def scan(repo, timeout=600):
    cmd, ver = detect()
    if not cmd:
        return None, [], "not-installed"
    try:
        r = run([cmd, "fs", "--scanners", "vuln,secret,misconfig",
                 "--format", "json", "--quiet", str(repo)], timeout=timeout)
        try:
            data = json.loads(r.stdout or "{}")
        except Exception:
            return ver, [], "parse-error"
        findings = []
        for res in (data.get("Results") or []):
            tgt = res.get("Target", "")
            for v in (res.get("Vulnerabilities") or []):
                fixed = v.get("FixedVersion")
                findings.append(Finding(
                    NAME, _sev(v.get("Severity")),
                    f"{v.get('VulnerabilityID', 'CVE')} · {v.get('PkgName', '')}",
                    detail=(v.get("Title") or v.get("Description") or ""),
                    file=tgt, rule=v.get("VulnerabilityID", ""),
                    remediation=(f"Actualiza {v.get('PkgName', '')} a {fixed}"
                                 if fixed else "Sin version parcheada aun."),
                ).norm())
            for s in (res.get("Secrets") or []):
                findings.append(Finding(
                    NAME, "critical", f"Secreto: {s.get('RuleID', '')}",
                    detail=s.get("Title", ""), file=tgt,
                    line=s.get("StartLine", 0), rule=s.get("RuleID", ""),
                    remediation="Rota la credencial y eliminala del codigo.",
                ).norm())
            for m in (res.get("Misconfigurations") or []):
                findings.append(Finding(
                    NAME, _sev(m.get("Severity")),
                    f"IaC: {m.get('ID', '')}",
                    detail=(m.get("Title") or ""), file=tgt,
                    rule=m.get("ID", ""),
                    remediation=(m.get("Resolution") or "Revisa la configuracion."),
                ).norm())
        return ver, findings, None
    except Exception as e:
        return ver, [], str(e)[:160]

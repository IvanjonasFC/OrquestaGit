"""Orquestador del motor SecOps.

Corre los escaneres DISPONIBLES sobre un repo, normaliza todo a un informe
unico (severidades CRITICAL/HIGH/MEDIUM/LOW), aplica un quality gate
configurable y lista las herramientas que faltan con su guia de instalacion.
Blindado: un fallo en un escaner nunca tumba el resto; salida siempre valida.
"""
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import gitleaks
import trivy
import osv
import semgrep
from base import SEV_ORDER
from logutil import get_logger

# Orden de valor: secretos primero (mas critico y barato), luego deps, SAST.
SCANNERS = {
    "gitleaks": gitleaks,
    "trivy": trivy,
    "osv-scanner": osv,
    "semgrep": semgrep,
}


def doctor():
    """Que hay instalado y como instalar lo que falta."""
    out = {}
    for name, mod in SCANNERS.items():
        cmd, ver = mod.detect()
        out[name] = {
            "installed": bool(cmd),
            "version": ver,
            "install": mod.INSTALL.get("win" if os.name == "nt" else "unix"),
        }
    return out


def deep_scan(repo, only=None, gate_threshold="high", timeout=600):
    log = get_logger()
    p = Path(repo)
    if not p.exists() or not p.is_dir():
        return {"ok": False, "error": "Ruta de repositorio no valida."}

    names = only or list(SCANNERS.keys())
    findings, tools, missing, errors = [], {}, [], []
    t0 = time.time()
    log.info("deep_scan START repo=%s scanners=%s", p, names)

    for name in names:
        mod = SCANNERS.get(name)
        if not mod:
            continue
        try:
            ver, fs, err = mod.scan(str(p), timeout=timeout)
            tools[name] = ver
            if err == "not-installed":
                missing.append({"name": name,
                                "install": mod.INSTALL.get(
                                    "win" if os.name == "nt" else "unix")})
                log.info("  %s: no instalado", name)
            elif err:
                errors.append({"scanner": name, "error": err})
                log.warning("  %s: error=%s", name, err)
            else:
                findings.extend(fs)
                log.info("  %s: %d hallazgos (v=%s)", name, len(fs), ver)
        except Exception as e:  # blindaje total
            errors.append({"scanner": name, "error": str(e)[:160]})
            log.exception("  %s CRASH", name)

    findings.sort(key=lambda f: (-SEV_ORDER.get(f.severity, 0), f.scanner, f.file))

    summary = {k: 0 for k in ("critical", "high", "medium", "low", "info")}
    for f in findings:
        summary[f.severity] = summary.get(f.severity, 0) + 1
    summary["total"] = len(findings)

    thr = SEV_ORDER.get(gate_threshold, 3)
    gate_passed = all(SEV_ORDER.get(f.severity, 0) < thr for f in findings)

    res = {
        "ok": True,
        "repo": p.name,
        "path": str(p),
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(time.time() - t0, 1),
        "tools": tools,
        "summary": summary,
        "gate": {"threshold": gate_threshold, "passed": gate_passed},
        "findings": [f.__dict__ for f in findings],
        "missing_tools": missing,
        "errors": errors,
    }
    log.info("deep_scan DONE repo=%s summary=%s gate=%s %.1fs",
             p.name, summary, gate_passed, res["duration_s"])
    return res


def explain(title, detail, endpoint="http://localhost:11434/api/generate",
            model="llama3"):
    """Traduce un hallazgo a lenguaje simple con Ollama local (bajo demanda)."""
    import json
    import urllib.request
    prompt = ("Eres un mentor de seguridad. En 2-3 frases y en espanol sencillo, "
              "explica que significa este hallazgo y como se arregla. No saludes.\n"
              f"Hallazgo: {title}\nDetalle: {detail}")
    try:
        data = json.dumps({"model": model, "prompt": prompt,
                           "stream": False}).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = json.loads(r.read().decode()).get("response", "").strip()
        return {"ok": True, "text": txt}
    except Exception as e:
        return {"ok": False, "error": f"Ollama no disponible: {e}"}

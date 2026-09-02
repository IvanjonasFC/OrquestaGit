"""Auditor SecOps: audita dependencias por repo y devuelve el DETALLE
(qué paquete, severidad, aviso, versión que lo corrige) + cómo remediar.

  - npm  → `npm audit --json` (real, con findings por paquete)
  - pip  → `pip-audit -f json` (CVEs por paquete, si está instalado)
  - cargo → placeholder (cargo audit pendiente)

Roadmap motor real: gitleaks/semgrep/trivy/osv-scanner como escáneres
enchufables en modules/scanners/.
"""
import os
import json
import subprocess
from pathlib import Path

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
NPM = "npm.cmd" if os.name == "nt" else "npm"

_SEV_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3, "info": 4, "": 9}


def _run(cmd, cwd, timeout=180):
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
        creationflags=_NO_WINDOW,
    )


def audit_dependencies(repo_path):
    try:
        repo = Path(repo_path)
        if not repo.exists():
            return {"ok": False, "type": "error", "vulns": 0, "msg": "Ruta no encontrada.", "findings": []}

        if (repo / "package.json").exists():
            if (repo / "package-lock.json").exists() or (repo / "node_modules").exists():
                return _audit_npm(repo)
            return {"ok": True, "type": "npm", "vulns": 0, "findings": [],
                    "msg": "package.json sin lockfile: ejecuta `npm install` para poder auditar."}
        if (repo / "requirements.txt").exists() or (repo / "pyproject.toml").exists():
            return _audit_pip(repo)
        if (repo / "Cargo.toml").exists() or (repo / "src-tauri" / "Cargo.toml").exists():
            return {"ok": True, "type": "cargo", "vulns": 0, "findings": [],
                    "msg": "Rust detectado: `cargo audit` pendiente de integrar."}
        return {"ok": True, "type": "none", "vulns": 0, "msg": "", "findings": []}
    except Exception as e:
        return {"ok": False, "type": "error", "vulns": 0, "msg": str(e), "findings": []}


def _audit_npm(repo):
    try:
        r = _run([NPM, "audit", "--json"], repo)
        data = json.loads(r.stdout or "{}")
        meta = data.get("metadata", {}).get("vulnerabilities", {})
        crit = meta.get("critical", 0); high = meta.get("high", 0)
        mod = meta.get("moderate", 0); low = meta.get("low", 0)
        total = crit + high + mod + low

        findings = []
        fix_major = False
        vulns = data.get("vulnerabilities", {})
        # --- npm v6: esquema antiguo con 'advisories' ---
        if (not vulns) and isinstance(data.get("advisories"), dict):
            for adv in data["advisories"].values():
                sev = adv.get("severity", "")
                fixed = adv.get("patched_versions", "")
                findings.append({
                    "package": adv.get("module_name", ""),
                    "severity": sev,
                    "title": adv.get("title", "(sin detalle)"),
                    "range": adv.get("vulnerable_versions", ""),
                    "fix": (f"actualizar a {fixed}" if fixed and fixed != "<0.0.0" else "npm audit fix"),
                    "url": adv.get("url", ""),
                })
            findings.sort(key=lambda f: _SEV_ORDER.get(f.get("severity"), 9))
        # --- npm v7+: esquema 'vulnerabilities' ---
        if isinstance(vulns, dict) and vulns:
            for pkg, v in vulns.items():
                sev = v.get("severity", "")
                rng = v.get("range", "")
                title = ""
                url = ""
                for via in (v.get("via") or []):
                    if isinstance(via, dict):
                        title = via.get("title") or title
                        url = via.get("url") or url
                        sev = via.get("severity") or sev
                fa = v.get("fixAvailable")
                if isinstance(fa, dict):
                    fix = f"actualizar a {fa.get('name')}@{fa.get('version')}"
                    if fa.get("isSemVerMajor"):
                        fix_major = True
                        fix += " (cambio mayor)"
                elif fa is True:
                    fix = "npm audit fix"
                else:
                    fix = "sin fix automatico"
                findings.append({"package": pkg, "severity": sev, "title": title or "(sin detalle)",
                                 "range": rng, "fix": fix, "url": url})
            findings.sort(key=lambda f: _SEV_ORDER.get(f.get("severity"), 9))

        msg = (f"{crit} criticas, {high} altas, {mod} medias, {low} bajas"
               if total else "Sin vulnerabilidades conocidas.")
        fix_cmd = ("npm audit fix --force" if fix_major else "npm audit fix") if total else None
        return {"ok": True, "type": "npm", "vulns": total, "msg": msg,
                "detail": {"critical": crit, "high": high, "moderate": mod, "low": low},
                "findings": findings[:40], "fix_cmd": fix_cmd, "fix_major": fix_major}
    except FileNotFoundError:
        return {"ok": True, "type": "npm", "vulns": 0, "msg": "npm no esta en el PATH.", "findings": []}
    except json.JSONDecodeError:
        return {"ok": True, "type": "npm", "vulns": 0, "msg": "npm audit no devolvio JSON valido.", "findings": []}
    except subprocess.TimeoutExpired:
        return {"ok": True, "type": "npm", "vulns": 0, "msg": "npm audit tardo demasiado (timeout).", "findings": []}
    except Exception as e:
        return {"ok": True, "type": "npm", "vulns": 0, "msg": f"npm audit fallo: {e}", "findings": []}


def _audit_pip(repo):
    try:
        r = _run(["pip-audit", "-f", "json"], repo)
        data = json.loads(r.stdout or "[]")
        deps = data.get("dependencies", data) if isinstance(data, dict) else data
        findings = []
        vulns = 0
        for d in deps:
            for v in (d.get("vulns", []) or []):
                vulns += 1
                fixes = ", ".join(v.get("fix_versions", []) or [])
                findings.append({"package": d.get("name", ""), "severity": "",
                                 "title": v.get("id", ""), "range": d.get("version", ""),
                                 "fix": (f"actualizar a {fixes}" if fixes else "sin fix publicado"),
                                 "url": ""})
        msg = f"{vulns} CVEs en dependencias." if vulns else "Sin CVEs conocidas."
        fix_cmd = "pip install --upgrade <paquete>" if vulns else None
        return {"ok": True, "type": "pip", "vulns": vulns, "msg": msg,
                "findings": findings[:40], "fix_cmd": fix_cmd}
    except FileNotFoundError:
        return {"ok": True, "type": "pip", "vulns": 0, "findings": [],
                "msg": "pip-audit no instalado (`pip install pip-audit`)."}
    except json.JSONDecodeError:
        return {"ok": True, "type": "pip", "vulns": 0, "msg": "pip-audit no devolvio JSON.", "findings": []}
    except subprocess.TimeoutExpired:
        return {"ok": True, "type": "pip", "vulns": 0, "msg": "pip-audit timeout.", "findings": []}
    except Exception as e:
        return {"ok": True, "type": "pip", "vulns": 0, "msg": f"pip-audit: {e}", "findings": []}


def apply_fix(repo_path, force=False):
    """Ejecuta `npm audit fix` (opcionalmente --force) en el repo."""
    repo = Path(repo_path)
    if not (repo / "package.json").exists():
        return {"ok": False, "error": "Solo npm soporta arreglo automatico por ahora."}
    cmd = [NPM, "audit", "fix"] + (["--force"] if force else [])
    try:
        r = _run(cmd, repo, timeout=300)
        out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
        return {"ok": r.returncode == 0, "message": "npm audit fix ejecutado.",
                "forced": force, "output": out[-1500:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "npm audit fix tardo demasiado (timeout)."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

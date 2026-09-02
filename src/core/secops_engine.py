#!/usr/bin/env python3
"""OrquestaGit - Motor SecOps real (CLI independiente).

Escanea repos con Gitleaks (secretos), Trivy/osv-scanner (CVEs) y Semgrep
(SAST), normaliza a un informe unico y aplica un quality gate. No toca el
motor principal: se invoca aparte, exactamente igual que orquesta_core.py.

Uso (imprime UNA linea JSON):
    python src/core/secops_engine.py doctor
    python src/core/secops_engine.py deep_scan <repo> [gitleaks,trivy,...]
    python src/core/secops_engine.py deep_scan_all <carpeta_raiz>
    python src/core/secops_engine.py explain "<titulo>" "<detalle>" [endpoint] [model]
"""
import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scanners"))

try:
    import engine
except Exception as _e:  # nunca romper el JSON
    engine = None
    _IMPORT_ERR = str(_e)


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


def main():
    if engine is None:
        emit({"ok": False, "error": f"No se pudo cargar el motor: {_IMPORT_ERR}"})
        return
    if len(sys.argv) < 2:
        emit({"ok": False, "error": "Accion requerida: doctor|deep_scan|deep_scan_all|explain"})
        return
    kind, args = sys.argv[1], sys.argv[2:]
    try:
        if kind == "doctor":
            emit({"ok": True, "scanners": engine.doctor()})
        elif kind == "deep_scan":
            if not args:
                emit({"ok": False, "error": "Falta la ruta del repositorio."})
                return
            only = args[1].split(",") if len(args) > 1 and args[1].strip() else None
            emit(engine.deep_scan(args[0], only=only))
        elif kind == "deep_scan_all":
            if not args:
                emit({"ok": False, "error": "Falta la carpeta raiz."})
                return
            root = Path(args[0])
            if not root.exists():
                emit({"ok": False, "error": "La carpeta raiz no existe.", "repos": []})
                return
            repos = []
            for it in sorted(root.iterdir(), key=lambda x: x.name.lower()):
                try:
                    if it.is_dir() and (it / ".git").exists():
                        repos.append(engine.deep_scan(str(it)))
                except Exception as e:
                    repos.append({"ok": False, "repo": it.name, "error": str(e)[:120]})
            emit({"ok": True, "repos": repos})
        elif kind == "explain":
            title = args[0] if args else ""
            detail = args[1] if len(args) > 1 else ""
            endpoint = args[2] if len(args) > 2 else "http://localhost:11434/api/generate"
            model = args[3] if len(args) > 3 else "llama3"
            emit(engine.explain(title, detail, endpoint, model))
        else:
            emit({"ok": False, "error": f"Accion desconocida: {kind}"})
    except Exception as e:
        emit({"ok": False, "error": str(e)[:200]})


if __name__ == "__main__":
    main()

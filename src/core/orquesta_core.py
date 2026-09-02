#!/usr/bin/env python3
"""
OrquestaGit - Motor central (sidecar Python).

Todo comando imprime UNA linea JSON en stdout. Nunca lanza excepciones al
exterior: cualquier fallo se devuelve como {"ok": false, "error": "..."}.

Uso:
    python orquesta_core.py <accion> [args...]

Acciones: scan, prune_all, sync_all, secops_all, reflog, prune_exec,
          restore, set_root, get_root, init, inspect
"""
import sys
import os
import json
from pathlib import Path

# Salida SIEMPRE en UTF-8. En Windows, sin esto, un error del sistema con
# acentos (p.ej. 'conexion rechazada') se emite en cp1252 y Tauri, que lee
# UTF-8, revienta con 'invalid utf-8 sequence' y corta el JSON.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Permitir importar los modulos hermanos
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules"))

branch_pruner = reflog_viewer = secops = auto_sync = gitutils = ai_reviewer = architect = cicd = None
try:
    import branch_pruner
    import auto_sync
    import secops
    import reflog_viewer
    import gitutils
    import ai_reviewer
    import architect
    import cicd
    import db_manager
except ImportError:
    pass

CONFIG_DIR = Path.home() / ".orquestagit"
CONFIG_FILE = CONFIG_DIR / "config.json"


# --------------------------------------------------------------------------
# Salida
# --------------------------------------------------------------------------
def emit(obj):
    """Imprime SIEMPRE una unica linea JSON."""
    if isinstance(obj, str):
        obj = {"ok": True, "message": obj}
    try:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False))
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception as e:  # ultimisimo salvavidas
        sys.stdout.write('{"ok": false, "error": "emit failure: %s"}\n' % str(e))


# --------------------------------------------------------------------------
# Config persistente (carpeta de repos elegida por el usuario)
# --------------------------------------------------------------------------
def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------
# Deteccion de la carpeta de repositorios
# --------------------------------------------------------------------------
def candidate_roots():
    home = Path.home()
    cands = [
        home / "Documents" / "GitHub",
        home / "OneDrive" / "Documents" / "GitHub",
        home / "GitHub",
        home / "source" / "repos",
        home / "Projects",
        home / "projects",
        home / "dev",
        home / "repos",
        home / "Code",
        home / "Desktop",
        home / "Escritorio",
        home / "OneDrive" / "Escritorio",
        home / "Documents",
        home / "OneDrive" / "Documents",
        Path("C:/GitHub"),
        Path("C:/dev"),
        Path("C:/Projects"),
    ]
    seen, out = set(), []
    for c in cands:
        try:
            key = str(c).lower()
            if key in seen:
                continue
            seen.add(key)
            if c.exists() and c.is_dir():
                out.append(c)
        except Exception:
            continue
    return out


def count_git_repos(root):
    n = 0
    try:
        for item in root.iterdir():
            if item.is_dir() and (item / ".git").exists():
                n += 1
    except Exception:
        pass
    return n


def detect_root():
    """Devuelve la mejor carpeta de repos: config guardada, o la candidata
    con mas repositorios git de nivel 1."""
    cfg = load_config()
    saved = cfg.get("root")
    if saved and Path(saved).exists():
        return Path(saved)
    best, best_n = None, 0
    for c in candidate_roots():
        n = count_git_repos(c)
        if n > best_n:
            best, best_n = c, n
    return best


def each_repo(root):
    root = Path(root)
    try:
        items = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except Exception:
        return
    for item in items:
        try:
            if item.is_dir() and (item / ".git").exists():
                yield item
        except Exception:
            continue


# --------------------------------------------------------------------------
# Acciones de Lectura (Vista - Rapidas)
# --------------------------------------------------------------------------
def action_scan(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "No se encontro ninguna carpeta.", "path": None, "total": 0, "uncommitted": 0, "repos": []}
    return db_manager.get_dashboard_data(str(root))

def action_prune_all(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta no valida.", "repos": []}
    return db_manager.get_cleanup_data(str(root))

def action_secops_all(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta no valida.", "repos": []}
    return db_manager.get_secops_data(str(root))

def action_sync_all(args):
    # AutoSync read uses the same dashboard data since ahead/behind is there
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta no valida.", "repos": []}
    return db_manager.get_dashboard_data(str(root))

# --------------------------------------------------------------------------
# Acciones de Escritura (Actualizacion en Background)
# --------------------------------------------------------------------------
def action_bg_refresh_repos(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta invalida."}
    seen = []
    for repo in each_repo(root):
        st = gitutils.repo_status(repo)
        db_manager.upsert_repo_sync(
            str(repo), repo.name,
            st.get("branch", ""),
            st.get("dirty", 0),
            st.get("ahead", 0),
            st.get("behind", 0)
        )
        seen.append(str(repo))
    # Limpia filas de repos que ya no estan en disco (renombrados/borrados).
    removed = db_manager.remove_missing_repos(str(root), seen)
    return {"ok": True, "scanned": len(seen), "removed": removed}

def action_bg_refresh_sync(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta invalida."}
    for repo in each_repo(root):
        res = auto_sync.check_sync(str(repo))
        # update_sync_status NO toca dirty_files: no pisamos el conteo de
        # cambios sin commitear que calculo bg_refresh_repos.
        db_manager.update_sync_status(
            str(repo),
            res.get("branch", "") or "",
            res.get("ahead", 0),
            res.get("behind", 0)
        )
    return {"ok": True}

def action_bg_refresh_pruner(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta invalida."}
    for repo in each_repo(root):
        res = branch_pruner.list_dead_branches(str(repo))
        db_manager.upsert_cleanup(str(repo), res.get("branches", []))
    return {"ok": True}

def action_bg_refresh_secops(args):
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta invalida."}
    for repo in each_repo(root):
        res = secops.audit_dependencies(str(repo))
        summary = {
            "vulns": res.get("vulns", 0),
            "type": res.get("type", "unknown"),
            "detail": res.get("detail"),
            "findings": res.get("findings", []),
            "fix_cmd": res.get("fix_cmd"),
            "fix_major": res.get("fix_major", False),
        }
        db_manager.upsert_audit(str(repo), res.get("type", "multi"), summary, res.get("msg", ""))
    return {"ok": True}



def action_reflog(args):
    if not args:
        return {"ok": False, "error": "Falta la ruta del repositorio."}
    return reflog_viewer.get_reflog(args[0])


def action_prune_exec(args):
    if len(args) < 2:
        return {"ok": False, "error": "Uso: prune_exec <repo> <rama> [rama...]"}
    return branch_pruner.prune_branches(args[0], args[1:])


def action_restore(args):
    if len(args) < 2:
        return {"ok": False, "error": "Uso: restore <repo> <hash>"}
    return reflog_viewer.restore_ref(args[0], args[1])


def action_set_root(args):
    if not args:
        return {"ok": False, "error": "Falta la ruta."}
    p = Path(args[0])
    if not p.exists() or not p.is_dir():
        return {"ok": False, "error": "La ruta no existe o no es carpeta."}
    cfg = load_config()
    cfg["root"] = str(p)
    save_config(cfg)
    return {"ok": True, "root": str(p), "repos_detectados": count_git_repos(p)}


def action_get_root(args):
    root = detect_root()
    return {"ok": True, "root": str(root) if root else None}


def action_ai_review(args):
    """El Inspector (integrado de Antigravity): revisa el ultimo commit con IA."""
    if ai_reviewer is None:
        return {"ok": False, "error": "Modulo ai_reviewer no disponible."}
    if len(args) < 5:
        return {"ok": False, "error": "Uso: ai_review <repo> <provider> <endpoint> <model> <api_key>"}
    repo, provider, endpoint, model, api_key = args[0], args[1], args[2], args[3], args[4]
    if api_key == "NONE":
        api_key = ""
    res = ai_reviewer.review_code(repo, provider, endpoint, model, api_key)
    if res.get("status") == "ok":
        return {"ok": True, "review": res.get("review", "")}
    return {"ok": False, "error": res.get("message", "Fallo en la revision de IA.")}


def action_init(args):
    if architect is None:
        return {"ok": False, "error": "Modulo architect no disponible."}
    if not args:
        return {"ok": False, "error": "Falta el nombre del proyecto."}

    root = detect_root()
    if not root:
        return {"ok": False, "error": "No se ha detectado ruta raiz global."}

    template = args[1] if len(args) > 1 else "python"
    return architect.init_project(str(root), args[0], template)


def action_templates(args):
    if architect is None:
        return {"ok": False, "error": "Modulo architect no disponible."}
    return architect.list_templates()

def action_cicd_detect(args):
    if cicd is None:
        return {"ok": False, "error": "Modulo cicd no disponible."}
    if not args:
        return {"ok": False, "error": "Uso: cicd_detect <repo>"}
    return cicd.detect_stack(args[0])


def action_cicd_generate(args):
    if cicd is None:
        return {"ok": False, "error": "Modulo cicd no disponible."}
    if not args:
        return {"ok": False, "error": "Uso: cicd_generate <repo> [stack]"}
    stack = args[1] if len(args) > 1 else None
    return cicd.generate_workflow(args[0], stack)


def action_cicd_inject(args):
    if cicd is None:
        return {"ok": False, "error": "Modulo cicd no disponible."}
    if not args:
        return {"ok": False, "error": "Uso: cicd_inject <repo> [stack] [force]"}
    stack = args[1] if len(args) > 1 and args[1] not in ("force", "-") else None
    force = "force" in args[1:]
    return cicd.inject_workflow(args[0], stack, force)


def action_secops_fix(args):
    if secops is None:
        return {"ok": False, "error": "Modulo secops no disponible."}
    if not args:
        return {"ok": False, "error": "Uso: secops_fix <repo> [force]"}
    force = "force" in args[1:]
    return secops.apply_fix(args[0], force)


def action_template_save(args):
    if architect is None:
        return {"ok": False, "error": "Modulo architect no disponible."}
    if len(args) < 2:
        return {"ok": False, "error": "Uso: template_save <repo> <nombre> [label]"}
    label = args[2] if len(args) > 2 else None
    return architect.save_template(args[0], args[1], label)


def action_template_delete(args):
    if architect is None:
        return {"ok": False, "error": "Modulo architect no disponible."}
    if not args:
        return {"ok": False, "error": "Uso: template_delete <nombre>"}
    return architect.delete_template(args[0])


def action_ai_status(args):
    if ai_reviewer is None:
        return {"ok": False, "error": "Modulo ai_reviewer no disponible."}
    provider = args[0] if args else "ollama"
    endpoint = args[1] if len(args) > 1 else "http://localhost:11434/api/generate"
    if provider == "ollama":
        return ai_reviewer.ollama_status(endpoint)
    # openai/anthropic: no se hace ping (gastaria credito). Disponible = hay API key.
    return {"ok": True, "available": None, "provider": provider,
            "note": "Proveedor de pago: requiere API key configurada."}


def action_reflog_all(args):
    if reflog_viewer is None:
        return {"ok": False, "error": "Modulo reflog_viewer no disponible.", "repos": []}
    root = Path(args[0]) if args else detect_root()
    if not root or not Path(root).exists():
        return {"ok": False, "error": "Ruta invalida.", "repos": []}
    try:
        n = int(args[1])
    except Exception:
        n = 6
    repos = []
    for repo in each_repo(root):
        rl = reflog_viewer.get_reflog(str(repo), n)
        repos.append({"name": repo.name, "path": str(repo),
                      "entries": rl.get("entries", []) or []})
    return {"ok": True, "repos": repos}


ACTIONS = {
    "scan": action_scan,
    "prune_all": action_prune_all,
    "sync_all": action_sync_all,
    "secops_all": action_secops_all,
    "bg_refresh_repos": action_bg_refresh_repos,
    "bg_refresh_sync": action_bg_refresh_sync,
    "bg_refresh_pruner": action_bg_refresh_pruner,
    "bg_refresh_secops": action_bg_refresh_secops,
    "reflog": action_reflog,
    "prune_exec": action_prune_exec,
    "restore": action_restore,
    "set_root": action_set_root,
    "get_root": action_get_root,
    "ai_review": action_ai_review,
    "init": action_init,
    "templates": action_templates,
    "template_save": action_template_save,
    "template_delete": action_template_delete,
    "cicd_detect": action_cicd_detect,
    "cicd_generate": action_cicd_generate,
    "cicd_inject": action_cicd_inject,
    "ai_status": action_ai_status,
    "reflog_all": action_reflog_all,
    "secops_fix": action_secops_fix,
}


def dispatch():
    if gitutils is None:
        emit({"ok": False, "error": "Modulos internos no encontrados (revisa src/core/modules)."})
        return
    if len(sys.argv) < 2:
        emit({"ok": False, "error": "No se especifico ninguna accion."})
        return
    kind = sys.argv[1]
    args = sys.argv[2:]
    fn = ACTIONS.get(kind)
    if not fn:
        emit({"ok": False, "error": f"Accion desconocida: {kind}"})
        return
    try:
        emit(fn(args))
    except Exception as e:
        emit({"ok": False, "error": f"{kind} fallo: {e}"})


if __name__ == "__main__":
    dispatch()

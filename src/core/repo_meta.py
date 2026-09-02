#!/usr/bin/env python3
"""OrquestaGit - Metadatos ligeros de un repo, BAJO DEMANDA (sin cache).

Pensado para acciones puntuales del frontend (ej. el boton "Abrir en GitHub"):
se llama como un tercer script, igual que orquesta_core.py / secops_engine.py.

Uso (imprime UNA linea JSON):
    python src/core/repo_meta.py get_remote <repo>
        -> {"ok": true, "remote": "https://github.com/user/repo"}
    python src/core/repo_meta.py detail <repo>
        -> {ok, name, path, branch, remote, upstream, ahead, behind, dirty,
            last_commit:{hash,subject,author,rel_time}, worktrees:[], stash, tags}
"""
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules"))

try:
    import gitutils
except Exception as _e:
    gitutils = None
    _IMPORT_ERR = str(_e)


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


def get_detail(repo):
    """Bundle rico por repo para llenar las pestañas del panel de detalle."""
    from pathlib import Path
    p = Path(repo)
    d = {
        "ok": True, "name": p.name, "path": str(p),
        "branch": gitutils.current_branch(repo), "remote": gitutils.remote_url(repo),
        "upstream": "", "ahead": 0, "behind": 0, "dirty": 0,
        "last_commit": None, "worktrees": [], "stash": 0, "tags": 0,
    }
    if not gitutils.is_repo(repo):
        return {"ok": False, "error": "No es un repositorio git."}
    g = gitutils.run_git
    try:
        r = g(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
        if r.returncode == 0:
            d["upstream"] = r.stdout.strip()
        r = g(repo, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.split()
            if len(parts) == 2:
                d["ahead"], d["behind"] = int(parts[0]), int(parts[1])
        r = g(repo, ["status", "--porcelain"])
        if r.returncode == 0:
            d["dirty"] = len([ln for ln in r.stdout.splitlines() if ln.strip()])
        r = g(repo, ["log", "-1", "--format=%h|%s|%an|%cr"])
        if r.returncode == 0 and r.stdout.strip():
            c = r.stdout.strip().split("|", 3)
            if len(c) == 4:
                d["last_commit"] = {"hash": c[0], "subject": c[1], "author": c[2], "rel_time": c[3]}
        r = g(repo, ["worktree", "list", "--porcelain"])
        if r.returncode == 0:
            d["worktrees"] = [ln.split(" ", 1)[1] for ln in r.stdout.splitlines()
                              if ln.startswith("worktree ")]
        r = g(repo, ["stash", "list"])
        if r.returncode == 0:
            d["stash"] = len([ln for ln in r.stdout.splitlines() if ln.strip()])
        r = g(repo, ["tag"])
        if r.returncode == 0:
            d["tags"] = len([ln for ln in r.stdout.splitlines() if ln.strip()])
    except Exception as e:
        d["error"] = str(e)[:120]
    return d


def main():
    if gitutils is None:
        emit({"ok": False, "error": f"gitutils no disponible: {_IMPORT_ERR}"})
        return
    if len(sys.argv) < 3:
        emit({"ok": False, "error": "Uso: repo_meta.py get_remote <repo>"})
        return
    action, repo = sys.argv[1], sys.argv[2]
    try:
        if action == "get_remote":
            emit({"ok": True, "remote": gitutils.remote_url(repo)})
        elif action == "detail":
            emit(get_detail(repo))
        else:
            emit({"ok": False, "error": f"Accion desconocida: {action}"})
    except Exception as e:
        emit({"ok": False, "error": str(e)[:200]})


if __name__ == "__main__":
    main()

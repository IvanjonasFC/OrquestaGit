"""Maquina del Tiempo: visualiza el reflog y permite revertir a un hash."""
import gitutils


def get_reflog(repo_path, max_entries=20):
    try:
        if not gitutils.is_repo(repo_path):
            return {"ok": False, "error": "No es un repositorio git.", "entries": []}

        fmt = "%h|%gd|%cr|%gs"
        r = gitutils.run_git(
            repo_path,
            ["reflog", "show", "--format=" + fmt, "-n", str(max_entries)],
        )
        if r.returncode != 0:
            return {"ok": True, "entries": []}

        entries = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                entries.append({
                    "hash": parts[0], "selector": parts[1],
                    "time": parts[2], "action": parts[3],
                })
        return {"ok": True, "entries": entries}
    except Exception as e:
        return {"ok": False, "error": str(e), "entries": []}


def restore_ref(repo_path, target_hash):
    try:
        if not gitutils.is_repo(repo_path):
            return {"ok": False, "error": "No es un repositorio git."}
        # Seguridad basica: el hash solo debe ser alfanumerico corto.
        h = "".join(c for c in target_hash if c.isalnum())
        if not h:
            return {"ok": False, "error": "Hash no valido."}
        r = gitutils.run_git(repo_path, ["reset", "--hard", h])
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr.strip()[:160]}
        return {"ok": True, "message": f"Restaurado a {h}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

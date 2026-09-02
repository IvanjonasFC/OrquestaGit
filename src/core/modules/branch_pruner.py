"""El Barrendero: detecta y borra ramas muertas (merged) por repo."""
import gitutils

PROTECTED = {"main", "master", "develop", "dev", "release", "staging"}


def list_dead_branches(repo_path):
    """Ramas locales ya fusionadas en la rama actual (candidatas a borrar)."""
    try:
        if not gitutils.is_repo(repo_path):
            return {"ok": False, "error": "No es un repositorio git.", "branches": []}

        current = gitutils.current_branch(repo_path)
        r = gitutils.run_git(repo_path, ["branch", "--merged"])
        if r.returncode != 0:
            return {"ok": True, "current": current, "branches": []}

        dead = []
        for line in r.stdout.splitlines():
            branch = line.replace("*", "").strip()
            if not branch:
                continue
            if branch == current or branch in PROTECTED:
                continue
            dead.append(branch)
        return {"ok": True, "current": current, "branches": dead}
    except Exception as e:
        return {"ok": False, "error": str(e), "branches": []}


def prune_branches(repo_path, branches):
    """Borra las ramas indicadas (git branch -d, seguro: solo si estan merged)."""
    try:
        if not gitutils.is_repo(repo_path):
            return {"ok": False, "error": "No es un repositorio git."}
        deleted, failed = [], []
        for b in branches:
            if b in PROTECTED:
                failed.append({"branch": b, "reason": "protegida"})
                continue
            r = gitutils.run_git(repo_path, ["branch", "-d", b])
            if r.returncode == 0:
                deleted.append(b)
            else:
                failed.append({"branch": b, "reason": r.stderr.strip()[:120]})
        return {"ok": True, "deleted": deleted, "failed": failed}
    except Exception as e:
        return {"ok": False, "error": str(e)}

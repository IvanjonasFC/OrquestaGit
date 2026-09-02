"""Utilidades git compartidas. Todo con cwd= (nunca os.chdir global)."""
import os
import subprocess
from pathlib import Path

# En Windows los ejecutables suelen llevar sufijo; git normalmente no lo necesita.
GIT = "git"

# Evita que se abra una ventana de consola en Windows por cada subproceso.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def run_git(repo, args, timeout=25):
    """Ejecuta git dentro de `repo`. Devuelve el CompletedProcess.
    Nunca lanza (salvo timeout, que se captura arriba)."""
    return subprocess.run(
        [GIT, *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=_NO_WINDOW,
    )


def is_repo(path):
    p = Path(path)
    return p.is_dir() and (p / ".git").exists()


def current_branch(repo):
    try:
        r = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return "?"


def remote_url(repo):
    """URL 'https' navegable del remoto origin (para abrir en el navegador).
    Normaliza SSH (git@host:user/repo.git) a https y quita el .git. '' si no hay."""
    try:
        r = run_git(repo, ["remote", "get-url", "origin"], timeout=10)
        if r.returncode != 0:
            return ""
        url = (r.stdout or "").strip()
        if not url:
            return ""
        if url.startswith("git@"):
            host_path = url.split("@", 1)[1]
            host, _, path = host_path.partition(":")
            url = "https://" + host + "/" + path
        elif url.startswith("ssh://"):
            url = "https://" + url[len("ssh://"):].split("@")[-1].replace(":", "/", 1)
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return ""


def repo_status(repo):
    """Estado tipo RepoBar: rama, nº de cambios sin commitear, ahead/behind, remoto."""
    repo = Path(repo)
    info = {
        "name": repo.name, "path": str(repo), "branch": "?",
        "dirty": 0, "ahead": 0, "behind": 0, "upstream": False,
        "remote": "", "error": None,
    }
    try:
        info["branch"] = current_branch(repo)
        info["remote"] = remote_url(repo)

        r = run_git(repo, ["status", "--porcelain"])
        if r.returncode == 0:
            info["dirty"] = len([ln for ln in r.stdout.splitlines() if ln.strip()])

        r = run_git(repo, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.split()
            if len(parts) == 2:
                info["ahead"] = int(parts[0])
                info["behind"] = int(parts[1])
                info["upstream"] = True
    except subprocess.TimeoutExpired:
        info["error"] = "timeout"
    except Exception as e:
        info["error"] = str(e)
    return info

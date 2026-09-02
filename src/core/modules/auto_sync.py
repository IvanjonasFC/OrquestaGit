"""Radar AutoSync: comprueba por repo si hay commits pendientes de bajar/subir."""
import gitutils


def check_sync(repo_path, do_fetch=True):
    try:
        if not gitutils.is_repo(repo_path):
            return {"ok": False, "status": "error", "message": "No es un repositorio git.",
                    "ahead": 0, "behind": 0, "branch": None}

        branch = gitutils.current_branch(repo_path)

        # 1) Fetch silencioso (puede fallar sin red / sin remoto)
        fetched = True
        if do_fetch:
            try:
                r = gitutils.run_git(repo_path, ["fetch", "--quiet"], timeout=40)
                fetched = (r.returncode == 0)
            except Exception:
                fetched = False

        # 2) ahead/behind respecto al upstream
        ahead = behind = 0
        upstream = False
        r = gitutils.run_git(repo_path, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
                upstream = True

        if not upstream:
            message = "Sin upstream configurado"
            status = "no-upstream"
        elif behind > 0 and ahead > 0:
            message = f"{behind} por bajar / {ahead} por subir (divergido)"
            status = "diverged"
        elif behind > 0:
            message = f"{behind} commits pendientes de bajar"
            status = "behind"
        elif ahead > 0:
            message = f"{ahead} commits sin subir"
            status = "ahead"
        else:
            message = "Sincronizado" if fetched else "Sincronizado (sin fetch)"
            status = "synced"

        return {
            "ok": True, "status": status, "message": message,
            "ahead": ahead, "behind": behind, "branch": branch, "fetched": fetched,
        }
    except Exception as e:
        return {"ok": False, "status": "error", "message": str(e),
                "ahead": 0, "behind": 0, "branch": None}

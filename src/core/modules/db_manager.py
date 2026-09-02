"""Caché-Primero: capa de persistencia SQLite de OrquestaGit.

Un único archivo ~/.orquestagit/orquesta.db guarda el estado de repos,
auditorías y limpieza. Las vistas leen de aquí (instantáneo); el worker de
fondo escribe aquí tras hacer el git pesado.

Robustez:
  - WAL + busy_timeout: soporta el worker (cada 30s) y acciones manuales a la
    vez sin "database is locked".
  - update_sync_status: refresca rama/ahead/behind SIN pisar dirty_files.
  - remove_missing_repos: elimina filas de repos que ya no están en disco.
  - prefijo de ruta con separador: evita colar carpetas hermanas (GitHub vs
    GitHubOld).
"""
import os
import sqlite3
import json
import time
from pathlib import Path

DB_DIR = Path.home() / ".orquestagit"
DB_PATH = DB_DIR / "orquesta.db"


def _get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    # WAL permite lectores concurrentes con un escritor; busy_timeout evita el
    # error inmediato "database is locked" cuando el worker y una acción manual
    # coinciden: espera hasta 5s a que se libere el bloqueo.
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return conn


def _norm_root(root_path):
    """Normaliza la raíz y devuelve el patrón LIKE de sus hijos directos/anidados.
    Añade el separador para que 'C:/GitHub' NO empareje 'C:/GitHubOld'."""
    root = str(root_path).rstrip("/\\")
    # SQLite LIKE usa '/' y '\\' según cómo se guardó la ruta; guardamos con
    # os.sep, así que replicamos ambos por seguridad multiplataforma.
    return root, root + os.sep + "%", root + "/%"


def init_db():
    conn = _get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            name TEXT,
            last_branch TEXT,
            dirty_files INTEGER,
            ahead INTEGER,
            behind INTEGER,
            last_scan_at REAL
        );
        CREATE TABLE IF NOT EXISTS audit_results (
            repo_id INTEGER PRIMARY KEY,
            tool TEXT,
            severity_summary_json TEXT,
            raw_output TEXT,
            scanned_at REAL,
            FOREIGN KEY(repo_id) REFERENCES repos(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS cleanup_results (
            repo_id INTEGER PRIMARY KEY,
            junk_files_json TEXT,
            scanned_at REAL,
            FOREIGN KEY(repo_id) REFERENCES repos(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# Escritura (background worker)
# --------------------------------------------------------------------------
def upsert_repo_sync(path, name, branch, dirty_files, ahead, behind):
    """Inserta/actualiza la fila COMPLETA de un repo (lo usa bg_refresh_repos)."""
    conn = _get_conn()
    c = conn.cursor()
    now = time.time()
    c.execute("""
        INSERT INTO repos (path, name, last_branch, dirty_files, ahead, behind, last_scan_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            name=excluded.name,
            last_branch=excluded.last_branch,
            dirty_files=excluded.dirty_files,
            ahead=excluded.ahead,
            behind=excluded.behind,
            last_scan_at=excluded.last_scan_at
    """, (str(path), name, branch, dirty_files, ahead, behind, now))
    conn.commit()
    conn.close()


def update_sync_status(path, branch, ahead, behind):
    """Actualiza SOLO rama/ahead/behind (lo usa bg_refresh_sync).
    NO toca dirty_files: así el fetch del radar no borra el conteo de cambios
    sin commitear que calculó bg_refresh_repos en el mismo ciclo."""
    conn = _get_conn()
    c = conn.cursor()
    now = time.time()
    c.execute("""
        UPDATE repos
           SET last_branch = ?, ahead = ?, behind = ?, last_scan_at = ?
         WHERE path = ?
    """, (branch, ahead, behind, now, str(path)))
    # Si el repo aún no existe (sync corrió antes que repos), lo creamos mínimo.
    if c.rowcount == 0:
        name = Path(path).name
        c.execute("""
            INSERT OR IGNORE INTO repos (path, name, last_branch, dirty_files, ahead, behind, last_scan_at)
            VALUES (?, ?, ?, 0, ?, ?, ?)
        """, (str(path), name, branch, ahead, behind, now))
    conn.commit()
    conn.close()


def remove_missing_repos(root_path, existing_paths):
    """Borra filas de repos bajo root_path que ya no están en disco (stale rows).
    existing_paths: iterable de rutas absolutas que SÍ existen ahora mismo."""
    root, like_sep, like_slash = _norm_root(root_path)
    keep = {str(p) for p in existing_paths}
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, path FROM repos WHERE path LIKE ? OR path LIKE ?",
        (like_sep, like_slash),
    )
    to_delete = [row["id"] for row in c.fetchall() if row["path"] not in keep]
    for rid in to_delete:
        c.execute("DELETE FROM audit_results WHERE repo_id = ?", (rid,))
        c.execute("DELETE FROM cleanup_results WHERE repo_id = ?", (rid,))
        c.execute("DELETE FROM repos WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return len(to_delete)


def upsert_audit(path, tool, summary, raw_output):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM repos WHERE path = ?", (str(path),))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    repo_id = row["id"]
    now = time.time()
    c.execute("""
        INSERT INTO audit_results (repo_id, tool, severity_summary_json, raw_output, scanned_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(repo_id) DO UPDATE SET
            tool=excluded.tool,
            severity_summary_json=excluded.severity_summary_json,
            raw_output=excluded.raw_output,
            scanned_at=excluded.scanned_at
    """, (repo_id, tool, json.dumps(summary), raw_output, now))
    conn.commit()
    conn.close()


def upsert_cleanup(path, junk_files):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM repos WHERE path = ?", (str(path),))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    repo_id = row["id"]
    now = time.time()
    c.execute("""
        INSERT INTO cleanup_results (repo_id, junk_files_json, scanned_at)
        VALUES (?, ?, ?)
        ON CONFLICT(repo_id) DO UPDATE SET
            junk_files_json=excluded.junk_files_json,
            scanned_at=excluded.scanned_at
    """, (repo_id, json.dumps(junk_files), now))
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# Lectura (vistas — rápidas)
# --------------------------------------------------------------------------
def get_dashboard_data(root_path):
    root, like_sep, like_slash = _norm_root(root_path)
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM repos WHERE path LIKE ? OR path LIKE ? ORDER BY name ASC",
        (like_sep, like_slash),
    )
    repos = []
    uncommitted = 0
    for r in c.fetchall():
        d = dict(r)
        if d.get("dirty_files", 0) and d["dirty_files"] > 0:
            uncommitted += 1
        d["scanned_at"] = d["last_scan_at"]
        d["branch"] = d["last_branch"]
        d["dirty"] = d["dirty_files"]
        d["upstream"] = bool(d.get("ahead") or d.get("behind"))
        repos.append(d)
    conn.close()
    return {"ok": True, "path": root, "total": len(repos), "uncommitted": uncommitted, "repos": repos}


def get_secops_data(root_path):
    root, like_sep, like_slash = _norm_root(root_path)
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT r.name, r.path, a.tool, a.severity_summary_json, a.raw_output, a.scanned_at
        FROM repos r
        LEFT JOIN audit_results a ON r.id = a.repo_id
        WHERE r.path LIKE ? OR r.path LIKE ?
        ORDER BY r.name ASC
    """, (like_sep, like_slash))
    repos = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("severity_summary_json"):
            summary = json.loads(d["severity_summary_json"])
            if isinstance(summary, dict):
                d["vulns"] = summary.get("vulns", 0)
                d["type"] = summary.get("type", d.get("tool") or "unknown")
                d["detail"] = summary.get("detail")
                d["findings"] = summary.get("findings") or []
                d["fix_cmd"] = summary.get("fix_cmd")
                d["fix_major"] = summary.get("fix_major", False)
            else:
                d["vulns"] = summary
                d["type"] = "unknown"
                d["findings"] = []
        else:
            d["vulns"] = None
            d["type"] = None
            d["findings"] = []
        d["msg"] = d.get("raw_output") or ""
        repos.append(d)
    conn.close()
    return {"ok": True, "repos": repos}


def get_cleanup_data(root_path):
    root, like_sep, like_slash = _norm_root(root_path)
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT r.name, r.path, r.last_branch, c.junk_files_json, c.scanned_at
        FROM repos r
        LEFT JOIN cleanup_results c ON r.id = c.repo_id
        WHERE r.path LIKE ? OR r.path LIKE ?
        ORDER BY r.name ASC
    """, (like_sep, like_slash))
    repos = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("junk_files_json"):
            d["branches"] = json.loads(d["junk_files_json"])
        else:
            d["branches"] = None
        d["current"] = d["last_branch"]
        repos.append(d)
    conn.close()
    return {"ok": True, "repos": repos}


init_db()

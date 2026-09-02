"""El Arquitecto: scaffolding de proyectos nuevos.

Dos fuentes de plantillas:
  1) BUILT-IN: andamiajes mínimos escritos aquí (python, node, static, tauri-stub).
  2) DE USUARIO: carpetas en ~/.orquestagit/templates/. Cada subcarpeta es una
     plantilla. Se pueden crear a mano o con save_template() a partir de un repo
     existente (p.ej. tu base de Tauri), para que todas tus apps nazcan iguales.

Al crear desde una plantilla de usuario se copia el árbol (sin .git/node_modules/
target/…), se sustituye el nombre (placeholders {{NAME}} y el nombre de origen si
se guardó desde un repo) y se hace git init. NO usa os.chdir ni os.system.
"""
import json
import shutil
from pathlib import Path

import gitutils

USER_TEMPLATES_DIR = Path.home() / ".orquestagit" / "templates"

# Carpetas/archivos que NUNCA entran en una plantilla (generados/pesados).
_EXCLUDE = {
    ".git", "node_modules", "target", "dist", "build", ".next", ".nuxt",
    ".svelte-kit", ".venv", "venv", "__pycache__", ".pytest_cache", ".cache",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
    ".DS_Store", "Thumbs.db",
}
_MAX_SUBST_BYTES = 512 * 1024  # no sustituir en archivos enormes/binarios

_GITIGNORE_PY = """# Python
__pycache__/
*.py[cod]
.Python
env/
venv/
.venv/
build/
dist/
*.egg-info/

# OS / IDE
.DS_Store
Thumbs.db
.vscode/
.idea/
"""

_GITIGNORE_NODE = """# Node
node_modules/
dist/
build/
.cache/
npm-debug.log*
.env
.env.local

# OS / IDE
.DS_Store
Thumbs.db
.vscode/
.idea/
"""


# --------------------------------------------------------------------------
# Plantillas BUILT-IN
# --------------------------------------------------------------------------
def _tpl_python(name):
    pkg = name.replace("-", "_")
    return {
        "README.md": f"# {name}\n\nProyecto Python generado por El Arquitecto de OrquestaGit.\n",
        ".gitignore": _GITIGNORE_PY,
        "requirements.txt": "# Anade aqui tus dependencias\n",
        "src/__init__.py": "",
        f"src/{pkg}/__init__.py": "",
        "src/main.py": 'def main():\n    print("Hola desde ' + name + '")\n\n\nif __name__ == "__main__":\n    main()\n',
        "tests/__init__.py": "",
        "tests/test_main.py": "def test_placeholder():\n    assert True\n",
    }


def _tpl_node(name):
    pkg = (
        "{\n"
        f'  "name": "{name}",\n'
        '  "version": "0.1.0",\n'
        '  "type": "module",\n'
        '  "scripts": {\n'
        '    "start": "node src/index.js",\n'
        '    "test": "echo \\"(sin tests aun)\\" && exit 0"\n'
        "  }\n"
        "}\n"
    )
    return {
        "README.md": f"# {name}\n\nProyecto Node generado por El Arquitecto de OrquestaGit.\n",
        ".gitignore": _GITIGNORE_NODE,
        "package.json": pkg,
        "src/index.js": 'console.log("Hola desde ' + name + '");\n',
        "tests/.gitkeep": "",
    }


def _tpl_static(name):
    html = (
        "<!doctype html>\n<html lang=\"es\">\n<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        f"  <title>{name}</title>\n"
        "  <link rel=\"stylesheet\" href=\"style.css\" />\n"
        "</head>\n<body>\n"
        f"  <h1>{name}</h1>\n"
        "  <script src=\"app.js\"></script>\n"
        "</body>\n</html>\n"
    )
    return {
        "README.md": f"# {name}\n\nWeb estatica generada por El Arquitecto de OrquestaGit.\n",
        ".gitignore": _GITIGNORE_NODE,
        "index.html": html,
        "style.css": ":root { color-scheme: light dark; }\nbody { font-family: system-ui, sans-serif; margin: 2rem; }\n",
        "app.js": 'console.log("' + name + ' listo");\n',
    }


def _tpl_tauri(name):
    base = _tpl_static(name)
    base["README.md"] = (
        f"# {name}\n\nApp de escritorio (Tauri) — andamiaje minimo de OrquestaGit.\n\n"
        "## Siguiente paso\n\nEjecuta `npm create tauri-app@latest` dentro de la carpeta para "
        "anadir el backend Rust, o (mejor) guarda tu propia app Tauri como plantilla desde El "
        "Arquitecto para que todas nazcan iguales.\n"
    )
    return base


_BUILTINS = {
    "python": {"label": "Python (src/tests)", "build": _tpl_python},
    "node": {"label": "Node (ESM)", "build": _tpl_node},
    "static": {"label": "Web estatica (HTML/CSS/JS)", "build": _tpl_static},
    "tauri": {"label": "Tauri (andamiaje minimo)", "build": _tpl_tauri},
}


# --------------------------------------------------------------------------
# Plantillas DE USUARIO
# --------------------------------------------------------------------------
def _user_template_meta(folder):
    """Lee _orquesta.json de una plantilla de usuario (label, origin_name)."""
    meta = {"label": folder.name, "origin_name": None}
    mf = folder / "_orquesta.json"
    if mf.exists():
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            meta["label"] = data.get("label", folder.name)
            meta["origin_name"] = data.get("origin_name")
        except Exception:
            pass
    return meta


def list_templates():
    out = [{"id": k, "label": v["label"], "source": "builtin"} for k, v in _BUILTINS.items()]
    try:
        if USER_TEMPLATES_DIR.exists():
            for folder in sorted(USER_TEMPLATES_DIR.iterdir(), key=lambda p: p.name.lower()):
                if folder.is_dir():
                    meta = _user_template_meta(folder)
                    out.append({"id": "user:" + folder.name, "label": meta["label"] + " (propia)", "source": "user"})
    except Exception:
        pass
    return {"ok": True, "templates": out, "dir": str(USER_TEMPLATES_DIR)}


def _safe_name(raw):
    safe = "".join(ch for ch in (raw or "").strip() if ch.isalnum() or ch in ("-", "_", ".")).strip()
    if not safe or safe in (".", ".."):
        return None
    return safe


def _copy_tree(src, dst):
    """Copia src→dst saltando carpetas/archivos generados (_EXCLUDE)."""
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in _EXCLUDE:
            continue
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            try:
                shutil.copy2(item, target)
            except Exception:
                pass


def _substitute_tree(root, mapping):
    """Sustituye tokens en el CONTENIDO de archivos de texto y en nombres de
    archivos/carpetas. mapping: {token: valor}."""
    root = Path(root)
    # 1) contenido
    for p in root.rglob("*"):
        if p.is_file():
            try:
                if p.stat().st_size > _MAX_SUBST_BYTES:
                    continue
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # binario o ilegible: se deja tal cual
            new = text
            for tok, val in mapping.items():
                if tok:
                    new = new.replace(tok, val)
            if new != text:
                try:
                    p.write_text(new, encoding="utf-8")
                except Exception:
                    pass
    # 2) nombres (de mas profundo a mas superficial para no invalidar rutas)
    for p in sorted(root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        new_name = p.name
        for tok, val in mapping.items():
            if tok and tok in new_name:
                new_name = new_name.replace(tok, val)
        if new_name != p.name:
            try:
                p.rename(p.with_name(new_name))
            except Exception:
                pass


def save_template(source_repo, template_name, label=None, overwrite=False):
    """Guarda un repo existente como plantilla reutilizable de usuario."""
    src = Path(source_repo)
    if not src.exists() or not src.is_dir():
        return {"ok": False, "error": "El repo de origen no existe."}
    tname = _safe_name(template_name)
    if not tname:
        return {"ok": False, "error": "Nombre de plantilla no valido."}
    dst = USER_TEMPLATES_DIR / tname
    if dst.exists() and not overwrite:
        return {"ok": False, "error": f"Ya existe una plantilla '{tname}'. Elige otro nombre."}
    try:
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        _copy_tree(src, dst)
        # manifiesto: guardamos el nombre de origen para sustituirlo al crear.
        meta = {"label": label or tname, "origin_name": src.name}
        (dst / "_orquesta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        n_files = sum(1 for _ in dst.rglob("*") if _.is_file())
        return {"ok": True, "message": f"Plantilla '{tname}' guardada ({n_files} archivos).",
                "id": "user:" + tname, "path": str(dst)}
    except Exception as e:
        return {"ok": False, "error": f"No se pudo guardar la plantilla: {e}"}


def delete_template(template_name):
    tname = _safe_name(template_name.replace("user:", ""))
    if not tname:
        return {"ok": False, "error": "Nombre no valido."}
    dst = USER_TEMPLATES_DIR / tname
    if not dst.exists():
        return {"ok": False, "error": "La plantilla no existe."}
    try:
        shutil.rmtree(dst)
        return {"ok": True, "message": f"Plantilla '{tname}' eliminada."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --------------------------------------------------------------------------
# Crear proyecto
# --------------------------------------------------------------------------
def init_project(global_path, project_name, template="python"):
    if not global_path or not project_name:
        return {"ok": False, "error": "Ruta global o nombre de proyecto vacios."}

    safe = _safe_name(project_name)
    if not safe:
        return {"ok": False, "error": "Nombre de proyecto no valido."}

    base_path = Path(global_path)
    if not base_path.exists():
        return {"ok": False, "error": "La ruta raiz (ej. GitHub) no existe."}

    project_path = base_path / safe
    if project_path.exists():
        return {"ok": False, "error": f"El directorio {safe} ya existe."}

    template = (template or "python").strip()

    try:
        if template.startswith("user:"):
            created = _build_from_user_template(template[5:], project_path, safe)
            if isinstance(created, dict):  # error
                return created
            label = "plantilla propia"
        elif template in _BUILTINS:
            files = _BUILTINS[template]["build"](safe)
            project_path.mkdir(parents=True)
            created = []
            for rel, content in files.items():
                target = project_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                created.append(rel)
            label = _BUILTINS[template]["label"]
        else:
            return {"ok": False, "error": f"Plantilla desconocida: {template}"}

        git_ok = False
        try:
            r = gitutils.run_git(project_path, ["init"])
            git_ok = (r.returncode == 0)
        except Exception:
            git_ok = False

        msg = f"Proyecto '{safe}' creado ({label}), {len(created)} archivos"
        msg += " + git init." if git_ok else " (git init no disponible)."
        return {"ok": True, "message": msg, "path": str(project_path),
                "template": template, "files": created, "git": git_ok}
    except Exception as e:
        return {"ok": False, "error": f"Fallo al inicializar el proyecto: {e}"}


def _build_from_user_template(tname, project_path, new_name):
    tname = _safe_name(tname)
    src = USER_TEMPLATES_DIR / (tname or "")
    if not tname or not src.exists():
        return {"ok": False, "error": "La plantilla de usuario no existe."}
    meta = _user_template_meta(src)
    _copy_tree(src, project_path)
    # quitar el manifiesto de la copia final
    mf = project_path / "_orquesta.json"
    if mf.exists():
        try:
            mf.unlink()
        except Exception:
            pass
    mapping = {"{{NAME}}": new_name, "{{name}}": new_name, "__NAME__": new_name}
    origin = meta.get("origin_name")
    if origin and len(origin) > 2:
        mapping[origin] = new_name
    _substitute_tree(project_path, mapping)
    return [str(p.relative_to(project_path)) for p in project_path.rglob("*") if p.is_file()]

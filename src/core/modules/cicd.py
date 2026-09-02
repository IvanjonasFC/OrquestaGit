"""CI/CD Autopiloto: detecta el stack de un repo y genera/inyecta workflows de
GitHub Actions. 100% offline y determinista.

Detección robusta:
  - Node: package.json en la raíz; además inspecciona dependencias para
    reconocer frameworks (Vite, React, Svelte, Next, Vue, Angular).
  - Rust: Cargo.toml en la raíz, en src-tauri/ o en subcarpetas de 1er nivel
    (un proyecto Tauri guarda el Cargo.toml en src-tauri/, no en la raíz).
  - Tauri: package.json + (src-tauri/tauri.conf.json | @tauri-apps/* | src-tauri/Cargo.toml)
    → stack compuesto (Node + Rust) con su propio workflow multiplataforma.
  - Python (requirements/pyproject/setup) y Go (go.mod).
Devuelve TODO lo detectado (transparencia) + un 'primary' recomendado.
"""
import json
from pathlib import Path

WORKFLOW_REL = ".github/workflows/ci.yml"
_PRIORITY = ["tauri", "node", "python", "rust", "go"]
_SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", ".venv", "venv", "src-tauri"}


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace") or "{}")
    except Exception:
        return {}


def _find_cargo(repo):
    """Localiza Cargo.toml: raíz, src-tauri/ y subcarpetas de primer nivel."""
    root = Path(repo)
    locs = []
    if (root / "Cargo.toml").exists():
        locs.append("Cargo.toml")
    if (root / "src-tauri" / "Cargo.toml").exists():
        locs.append("src-tauri/Cargo.toml")
    try:
        for d in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if d.is_dir() and d.name not in _SKIP_DIRS and not d.name.startswith("."):
                if (d / "Cargo.toml").exists():
                    locs.append(d.name + "/Cargo.toml")
    except Exception:
        pass
    return locs


def detect_stack(repo_path):
    repo = Path(repo_path)
    if not repo.exists():
        return {"ok": False, "error": "Ruta no encontrada.", "stacks": []}
    if not (repo / ".git").exists():
        return {"ok": False, "error": "No es un repositorio git.", "stacks": []}

    stacks = []
    is_tauri = False

    # --- Node + frameworks ---
    pkg = repo / "package.json"
    if pkg.exists():
        data = _read_json(pkg)
        deps = {}
        deps.update(data.get("dependencies") or {})
        deps.update(data.get("devDependencies") or {})
        frameworks = []
        for name, hit in [
            ("Tauri", any(k.startswith("@tauri-apps/") for k in deps)),
            ("Next", "next" in deps),
            ("Vite", "vite" in deps),
            ("Svelte", "svelte" in deps or "@sveltejs/kit" in deps),
            ("React", "react" in deps),
            ("Vue", "vue" in deps),
            ("Angular", "@angular/core" in deps),
        ]:
            if hit:
                frameworks.append(name)
        stacks.append({
            "id": "node", "label": "Node.js", "files": ["package.json"],
            "scripts": sorted((data.get("scripts") or {}).keys()),
            "has_lock": (repo / "package-lock.json").exists(),
            "frameworks": frameworks,
        })
        if ("Tauri" in frameworks
                or (repo / "src-tauri" / "tauri.conf.json").exists()
                or (repo / "src-tauri" / "Cargo.toml").exists()):
            is_tauri = True

    # --- Rust (raíz, src-tauri/, subcarpetas) ---
    cargo_locs = _find_cargo(repo)
    if cargo_locs:
        stacks.append({"id": "rust", "label": "Rust", "files": cargo_locs})

    # --- Python ---
    py_markers = [f for f in ("requirements.txt", "pyproject.toml", "setup.py") if (repo / f).exists()]
    if py_markers:
        has_tests = (repo / "tests").is_dir() or any(repo.glob("test_*.py")) or any(repo.glob("**/test_*.py"))
        stacks.append({"id": "python", "label": "Python", "files": py_markers, "has_tests": bool(has_tests)})

    # --- Go ---
    if (repo / "go.mod").exists():
        stacks.append({"id": "go", "label": "Go", "files": ["go.mod"]})

    # --- Tauri: stack compuesto (primario), al frente ---
    if is_tauri:
        stacks.insert(0, {
            "id": "tauri", "label": "Tauri (Node + Rust)",
            "files": ["src-tauri/tauri.conf.json"],
            "note": "App de escritorio: compila frontend (Node) y backend (Rust) en Linux/Windows/macOS.",
        })

    primary = next((pid for pid in _PRIORITY if any(s["id"] == pid for s in stacks)), None)
    detected = [s["id"] for s in stacks]

    # Resumen legible (qué y dónde) para que el usuario confíe en la detección.
    parts = []
    for s in stacks:
        lab = s["label"]
        if s["id"] == "node" and s.get("frameworks"):
            lab += " · " + ", ".join(s["frameworks"])
        elif s["id"] == "rust":
            lab += " · " + ", ".join(s["files"])
        elif s["id"] == "python" and s.get("files"):
            lab += " · " + ", ".join(s["files"])
        parts.append(lab)

    return {
        "ok": True, "stacks": stacks, "primary": primary, "detected": detected,
        "summary": "  |  ".join(parts),
        "has_ci": (repo / WORKFLOW_REL).exists(),
        "workflow_path": str(repo / WORKFLOW_REL),
    }


# --------------------------------------------------------------------------
# Generadores de YAML
# --------------------------------------------------------------------------
def _yaml_node():
    return """name: CI
on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]
    steps:
      - uses: actions/checkout@v4
      - name: Usar Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - name: Instalar dependencias
        run: npm ci
      - name: Build
        run: npm run build --if-present
      - name: Tests
        run: npm test --if-present
"""


def _yaml_python():
    return """name: CI
on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Configurar Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest
      - name: Tests
        run: pytest -q
"""


def _yaml_rust():
    return """name: CI
on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Build
        run: cargo build --verbose
      - name: Tests
        run: cargo test --verbose
"""


def _yaml_go():
    return """name: CI
on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: 'stable'
      - name: Build
        run: go build ./...
      - name: Tests
        run: go test ./...
"""


def _yaml_tauri():
    return """name: CI (Tauri)
on:
  push:
    branches: [ main, master ]
  pull_request:

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        platform: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      - name: Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - name: Rust
        uses: dtolnay/rust-toolchain@stable
      - name: Dependencias de sistema (Linux)
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
      - name: Instalar dependencias JS
        run: npm ci
      - name: Compilar app Tauri
        run: npm run tauri build
"""


_GENERATORS = {
    "node": _yaml_node,
    "python": _yaml_python,
    "rust": _yaml_rust,
    "go": _yaml_go,
    "tauri": _yaml_tauri,
}


def generate_workflow(repo_path, stack=None):
    det = detect_stack(repo_path)
    if not det.get("ok"):
        return det
    chosen = stack or det.get("primary")
    if not chosen:
        return {"ok": False, "error": "No se detectó ningún stack soportado (tauri/node/python/rust/go)."}
    if chosen not in _GENERATORS:
        return {"ok": False, "error": f"Stack no soportado: {chosen}"}
    return {"ok": True, "stack": chosen, "filename": WORKFLOW_REL,
            "yaml": _GENERATORS[chosen](), "has_ci": det.get("has_ci", False)}


def inject_workflow(repo_path, stack=None, force=False):
    gen = generate_workflow(repo_path, stack)
    if not gen.get("ok"):
        return gen
    target = Path(repo_path) / WORKFLOW_REL
    existed = target.exists()
    if existed and not force:
        return {"ok": False, "error": "Ya existe .github/workflows/ci.yml. Usa 'force' para sobrescribir.",
                "path": str(target), "existed": True}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(gen["yaml"], encoding="utf-8")
        return {"ok": True, "path": str(target), "stack": gen["stack"],
                "overwritten": existed, "message": ("Workflow sobrescrito" if existed else "Workflow creado")}
    except Exception as e:
        return {"ok": False, "error": f"No se pudo escribir el workflow: {e}", "path": str(target)}

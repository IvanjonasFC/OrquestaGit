"""Utilidades comunes de los escaneres: deteccion de binarios, ejecucion
segura y el modelo de hallazgo (Finding) normalizado."""
import os
import shutil
import subprocess
from dataclasses import dataclass

# Orden de severidad para ordenar y para el quality gate.
SEV_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
VALID_SEV = set(SEV_ORDER.keys())

# En Windows, evita abrir una ventana de consola por cada subproceso.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def which(*names):
    """Devuelve el primer ejecutable encontrado en el PATH, o None."""
    for n in names:
        p = shutil.which(n)
        if p:
            return n
    return None


def tool_version(cmd, args=("--version",), timeout=15):
    """Primera linea de `cmd --version`, o None si falla."""
    try:
        r = subprocess.run(
            [cmd, *args], capture_output=True, text=True, timeout=timeout,
            creationflags=_NO_WINDOW, encoding="utf-8", errors="replace")
        out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        return out[0].strip()[:60] if out else "instalado"
    except Exception:
        return None


def run(cmd_list, cwd=None, timeout=300):
    """Ejecuta un comando (lista de args, SIN shell -> sin inyeccion).
    Nunca lanza salvo TimeoutExpired, que el llamador captura."""
    return subprocess.run(
        cmd_list, cwd=(str(cwd) if cwd else None),
        capture_output=True, text=True, timeout=timeout,
        creationflags=_NO_WINDOW, encoding="utf-8", errors="replace")


@dataclass
class Finding:
    scanner: str
    severity: str          # critical | high | medium | low | info
    title: str
    detail: str = ""
    file: str = ""
    line: int = 0
    rule: str = ""
    remediation: str = ""

    def norm(self):
        s = (self.severity or "medium").lower()
        self.severity = s if s in VALID_SEV else "medium"
        self.title = (self.title or "")[:160]
        self.detail = (self.detail or "")[:400]
        try:
            self.line = int(self.line or 0)
        except Exception:
            self.line = 0
        return self

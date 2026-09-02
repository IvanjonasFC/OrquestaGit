"""Logging del motor SecOps.

CLAVE: los logs van SOLO a un fichero rotativo, NUNCA a stdout. El frontend
hace JSON.parse de stdout, asi que cualquier print de log romperia la salida.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER = None


def get_logger():
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    lg = logging.getLogger("orquesta.secops")
    lg.setLevel(logging.INFO)
    lg.propagate = False  # jamas escalar a la raiz (evita stdout)
    try:
        d = Path.home() / ".orquestagit" / "logs"
        d.mkdir(parents=True, exist_ok=True)
        h = RotatingFileHandler(d / "secops.log", maxBytes=512_000,
                                backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s"))
        lg.addHandler(h)
    except Exception:
        lg.addHandler(logging.NullHandler())  # si no hay disco, no rompas
    _LOGGER = lg
    return lg

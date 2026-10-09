"""Sauvegarde quotidienne de la base du bureau : `pg_dump` en PostgreSQL, copie du fichier en SQLite, compressée, datée,
sous SAUVEGARDES_DIR (volume), quatorze jours gardés. Lancée par un fil d'arrière-plan en production, ou à la main."""
from __future__ import annotations

import gzip
import logging
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from core import db

logger = logging.getLogger("zelij-core")
GARDEES = 14


def dossier() -> Path:
    p = Path(os.environ.get("SAUVEGARDES_DIR", "./data/sauvegardes"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def sauvegarder(*, executer_cmd=None) -> dict:
    """Une sauvegarde maintenant. Retourne le fichier produit et sa taille, ou l'erreur."""
    u = db.url()
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    cible = dossier() / f"bureau-{horodatage}.sql.gz"
    try:
        if u.startswith("postgres"):
            executer_cmd = executer_cmd or (lambda args: subprocess.run(args, capture_output=True, timeout=600, check=False))
            r = executer_cmd(["pg_dump", "--no-owner", "--no-privileges", u])
            if getattr(r, "returncode", 1) != 0:
                return {"ok": False, "detail": "pg_dump en échec : " + (getattr(r, "stderr", b"") or b"").decode("utf-8", errors="replace")[:200]}
            with gzip.open(cible, "wb") as f:
                f.write(getattr(r, "stdout", b""))
        else:
            source = Path(u.replace("sqlite:///", "", 1))
            if not source.exists():
                return {"ok": False, "detail": "base SQLite introuvable"}
            cible = dossier() / f"bureau-{horodatage}.sqlite.gz"
            with open(source, "rb") as src, gzip.open(cible, "wb") as dst:
                shutil.copyfileobj(src, dst)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "detail": f"sauvegarde impossible : {str(exc)[:160]}"}
    menage()
    return {"ok": True, "fichier": cible.name, "octets": cible.stat().st_size, "detail": f"{cible.name} ({cible.stat().st_size} octets)"}


def menage() -> int:
    fichiers = sorted(dossier().glob("bureau-*.gz"), key=lambda p: p.name, reverse=True)
    supprimes = 0
    for p in fichiers[GARDEES:]:
        try:
            p.unlink()
            supprimes += 1
        except OSError:
            pass
    return supprimes


def liste() -> list[dict]:
    return [{"fichier": p.name, "octets": p.stat().st_size, "date": p.name.split("-", 1)[1][:8]} for p in sorted(dossier().glob("bureau-*.gz"), key=lambda p: p.name, reverse=True)]


def _boucle(intervalle: int) -> None:
    while True:
        time.sleep(intervalle)
        try:
            res = sauvegarder()
            logger.info("Sauvegarde quotidienne : %s", res.get("detail"))
        except Exception:  # noqa: BLE001 — la boucle ne doit jamais mourir
            logger.exception("Sauvegarde quotidienne en échec")


def demarrer_fil(intervalle: int = 86400) -> threading.Thread | None:
    """Un fil discret qui sauvegarde chaque jour. Seulement en production (CORE_ENV=production) et une seule fois."""
    if os.environ.get("CORE_ENV") != "production" or getattr(demarrer_fil, "_lance", False):
        return None
    t = threading.Thread(target=_boucle, args=(intervalle,), name="sauvegarde-quotidienne", daemon=True)
    t.start()
    demarrer_fil._lance = True  # type: ignore[attr-defined]
    return t

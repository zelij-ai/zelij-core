"""L'encart « Une étoile pour Zelij Core » du bureau : un lien vers le dépôt public et, si le serveur peut joindre GitHub, le nombre
d'étoiles. La lecture est anonyme (API publique de GitHub, aucun jeton), une fois par jour au plus, en arrière-plan : une page ne
l'attend jamais, et un échec n'affiche rien. `ETOILES_GITHUB=0` retire l'encart et toute lecture (machine isolée, mode local)."""
from __future__ import annotations

import logging
import os
import threading
import time

import httpx

DEPOT = "zelij-ai/zelij-core"
URL = f"https://github.com/{DEPOT}"
TTL = 24 * 3600          # une lecture réussie vaut un jour
REESSAI = 10 * 60        # après un échec, on n'insiste pas avant dix minutes
_cache: dict = {"t": 0.0, "n": None, "en_cours": False}
_verrou = threading.Lock()
_log = logging.getLogger("zelij.etoiles")


def actif() -> bool:
    return os.environ.get("ETOILES_GITHUB", "1").strip() != "0"


def court(n: int | None) -> str:
    """36 412 → « 36 k », 1 240 → « 1,2 k », 980 → « 980 », None → «  »."""
    if n is None:
        return ""
    if n >= 10_000:
        return f"{round(n / 1000)} k"
    if n >= 1000:
        return f"{n / 1000:.1f}".replace(".", ",").replace(",0", "") + " k"
    return str(n)


def lire(client: httpx.Client | None = None) -> int | None:
    """Lecture synchrone (3 s au plus), jamais d'exception. Utilisée par le fil d'arrière-plan et par les tests."""
    try:
        c = client or httpx.Client(timeout=3)
        r = c.get(f"https://api.github.com/repos/{DEPOT}", headers={"Accept": "application/vnd.github+json", "User-Agent": "zelij-core"})
        n = int(r.json().get("stargazers_count")) if r.status_code == 200 else None
    except Exception as exc:          # réseau coupé, réponse inattendue : l'encart se passe du nombre
        _log.info("étoiles GitHub indisponibles : %s", exc)
        n = None
    with _verrou:
        _cache.update(t=time.time(), n=n, en_cours=False)
    return n


def compte(client: httpx.Client | None = None) -> int | None:
    """Le nombre en cache s'il est frais ; sinon lance la lecture en arrière-plan et rend None tout de suite."""
    with _verrou:
        age = time.time() - _cache["t"]
        if _cache["n"] is not None and age < TTL:
            return _cache["n"]
        if _cache["en_cours"] or (_cache["n"] is None and _cache["t"] and age < REESSAI):
            return _cache["n"] if age < TTL else None
        _cache["en_cours"] = True
    threading.Thread(target=lire, args=(client,), daemon=True, name="etoiles-github").start()
    return None


def encart() -> dict | None:
    """Ce que le gabarit affiche : None = pas d'encart."""
    if not actif():
        return None
    n = compte()
    return {"depot": DEPOT, "nom": DEPOT.split("/")[1], "url": URL, "etoiles": n, "libelle": court(n)}

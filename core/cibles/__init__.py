"""Cibles de déploiement de l'édition gratuite : un serveur Linux joignable en SSH, et OVH (le même serveur, plus le domaine
et le DNS par l'API OVH). Les cibles payantes (GCP…) arrivent par module signé et s'enregistrent ici de la même façon."""
from __future__ import annotations

import os

CIBLES: dict[str, dict] = {
    "ssh": {"nom": "Serveur Linux (SSH)", "module": "core.cibles.ssh"},
    "ovh": {"nom": "OVH (VPS + domaine + DNS)", "module": "core.cibles.ovh"},
}


def enregistrer_cible(identifiant: str, nom: str, module: str) -> None:
    CIBLES[identifiant] = {"nom": nom, "module": module}


def decouvrir_modules(dossier: str | None = None, cle_publique_hex: str | None = None) -> list[dict]:
    """Les modules déposés dans ZELIJ_MODULES_DIR : chaque `pack.json` de type « cible » dont la signature de l'éditeur est valide
    ET dont chaque fichier a l'empreinte signée enregistre sa cible et rend son code importable. Un module non signé, ou dont un
    fichier a été modifié, ajouté ou retiré, est ignoré et nommé dans le compte rendu : aucun code non signé n'est importé."""
    import sys
    from pathlib import Path

    from core import modules

    racine = dossier or os.environ.get("ZELIJ_MODULES_DIR", "").strip()
    constats: list[dict] = []
    if not racine or not Path(racine).is_dir():
        return constats
    for manifeste in sorted(Path(racine).glob("*/pack.json")):
        try:
            m = modules.charger_manifeste(manifeste)
        except (ValueError, KeyError) as exc:
            constats.append({"dossier": manifeste.parent.name, "ok": False, "detail": f"manifeste illisible : {str(exc)[:120]}"})
            continue
        if m.type != "cible" or not m.cible:
            continue
        if not modules.compatible(m) or not modules.verifier(m, cle_publique_hex):
            constats.append({"dossier": manifeste.parent.name, "ok": False, "detail": "signature invalide ou interface incompatible : module ignoré"})
            continue
        ecarts = modules.verifier_fichiers(m, manifeste.parent)
        if ecarts:
            constats.append({"dossier": manifeste.parent.name, "ok": False, "detail": "code différent du code signé, module ignoré : " + "; ".join(ecarts)[:200]})
            continue
        chemin = str(manifeste.parent)
        if chemin not in sys.path:
            sys.path.append(chemin)
        enregistrer_cible(m.cible["id"], m.cible.get("nom", m.nom), m.cible["module"])
        constats.append({"dossier": manifeste.parent.name, "ok": True, "detail": f"cible {m.cible['id']} enregistrée ({m.nom} {m.version})"})
    return constats


def cible_active() -> str:
    """La cible choisie à l'installation (variable CIBLE) ; `ssh` par défaut ; une cible de module n'existe qu'une fois découverte."""
    decouvrir_modules()
    c = os.environ.get("CIBLE", "ssh").strip().lower()
    return c if c in CIBLES else "ssh"


def charger(identifiant: str | None = None):
    import importlib

    ident = identifiant or cible_active()
    if ident not in CIBLES:
        decouvrir_modules()
    return importlib.import_module(CIBLES[ident]["module"])

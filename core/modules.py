"""Modules : la seule façon d'étendre le noyau. Une interface stable (`INTERFACE_MODULES`), un manifeste `pack.json`, une
signature Ed25519 de l'éditeur vérifiée avant toute activation. Un module non signé ou signé pour une autre interface ne
s'installe pas. Les cibles de déploiement (serveur SSH, OVH, GCP…) et les agents supplémentaires passent tous par ici."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from core import INTERFACE_MODULES, db

TYPES = ("cible", "agent", "pack")


class Cible(Protocol):
    """Contrat d'une cible de déploiement. Chaque méthode rend un compte rendu lisible ; aucune n'engage de paiement."""

    nom: str

    def installer(self, config: dict) -> dict: ...

    def deployer(self, version: str) -> dict: ...

    def sonder(self) -> dict: ...


@dataclass
class Manifeste:
    nom: str
    version: str
    type: str
    interface: str
    fournisseur: str
    description: str = ""
    signature: str = ""
    cible: dict | None = None     # pour un module de type « cible » : {id, nom, module} ; signé avec le reste, donc non substituable
    fichiers: dict | None = None  # chemin relatif → SHA-256 de chaque fichier du module : le code est couvert par la signature

    def charge_signee(self) -> bytes:
        d = asdict(self)
        d.pop("signature", None)
        for k in ("cible", "fichiers"):
            if d.get(k) is None:
                d.pop(k, None)
        return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def charger_manifeste(chemin: Path) -> Manifeste:
    d = json.loads(Path(chemin).read_text(encoding="utf-8"))
    for k in ("nom", "version", "type", "interface", "fournisseur"):
        if not d.get(k):
            raise ValueError(f"manifeste {chemin} : champ `{k}` manquant")
    if d["type"] not in TYPES:
        raise ValueError(f"manifeste {chemin} : type inconnu {d['type']}")
    cible = d.get("cible") if isinstance(d.get("cible"), dict) else None
    if d["type"] == "cible" and not (cible and cible.get("id") and cible.get("module")):
        raise ValueError(f"manifeste {chemin} : un module de type cible déclare `cible` {{id, nom, module}}")
    fichiers = d.get("fichiers") if isinstance(d.get("fichiers"), dict) else None
    if fichiers is not None and not all(isinstance(k, str) and isinstance(v, str) and len(v) == 64 for k, v in fichiers.items()):
        raise ValueError(f"manifeste {chemin} : `fichiers` attend {{chemin: sha256}}")
    return Manifeste(nom=d["nom"], version=d["version"], type=d["type"], interface=d["interface"], fournisseur=d["fournisseur"],
                     description=d.get("description", ""), signature=d.get("signature", ""), cible=cible, fichiers=fichiers)


IGNORES_FICHIERS = {"pack.json", "__pycache__", ".DS_Store"}


def empreintes_dossier(dossier: Path) -> dict[str, str]:
    """SHA-256 de chaque fichier du module (chemins relatifs, séparateur /), hors manifeste et caches. C'est ce que l'éditeur signe."""
    dossier = Path(dossier)
    out: dict[str, str] = {}
    for p in sorted(dossier.rglob("*")):
        if not p.is_file() or any(part in IGNORES_FICHIERS for part in p.relative_to(dossier).parts):
            continue
        out[p.relative_to(dossier).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def verifier_fichiers(m: Manifeste, dossier: Path) -> list[str]:
    """Le code sur le disque est-il exactement celui que l'éditeur a signé ? Liste des écarts (vide = conforme).
    Un manifeste sans `fichiers` est un écart : rien n'exécute du code que la signature ne couvre pas."""
    if m.fichiers is None:
        return ["manifeste sans empreintes de fichiers : le code n'est pas couvert par la signature"]
    reels = empreintes_dossier(dossier)
    ecarts = [f"{f} : modifié" for f, h in m.fichiers.items() if f in reels and reels[f] != h]
    ecarts += [f"{f} : absent" for f in m.fichiers if f not in reels]
    ecarts += [f"{f} : fichier en trop, non signé" for f in reels if f not in m.fichiers]
    return ecarts


def compatible(m: Manifeste, interface: str = INTERFACE_MODULES) -> bool:
    """Même version majeure d'interface : un module 1.x s'installe sur un noyau 1.y."""
    return m.interface.split(".")[0] == interface.split(".")[0]


def cle_publique_editeur() -> str:
    """Clé publique Ed25519 (hexadécimal) de l'éditeur des modules, posée dans l'environnement (ZELIJ_CLE_PUBLIQUE)."""
    return os.environ.get("ZELIJ_CLE_PUBLIQUE", "").strip()


def signer(m: Manifeste, cle_privee_hex: str) -> str:
    cle = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(cle_privee_hex))
    return cle.sign(m.charge_signee()).hex()


def verifier(m: Manifeste, cle_publique_hex: str | None = None) -> bool:
    pub = (cle_publique_hex if cle_publique_hex is not None else cle_publique_editeur()).strip()
    if not pub or not m.signature:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub)).verify(bytes.fromhex(m.signature), m.charge_signee())
        return True
    except (InvalidSignature, ValueError):
        return False


def generer_cles() -> tuple[str, str]:
    """(privée, publique) en hexadécimal. Outillage de l'éditeur et des tests ; la privée ne vit jamais dans une installation."""
    priv = Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives import serialization

    return (priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()).hex(),
            priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex())


def dossier_module(m: Manifeste) -> Path | None:
    """Le dossier du module dans ZELIJ_MODULES_DIR, s'il y est déposé : <dir>/<module> pour une cible, <dir>/<nom> sinon."""
    racine = os.environ.get("ZELIJ_MODULES_DIR", "").strip()
    if not racine:
        return None
    candidats = [m.cible.get("module", "")] if m.cible else []
    candidats += [m.nom, m.nom.replace("-", "_")]
    for nom in candidats:
        if nom and (Path(racine) / nom / "pack.json").is_file():
            return Path(racine) / nom
    return None


def installer(c: db.Connexion, org_id: str, m: Manifeste, *, par: str, cle_publique_hex: str | None = None) -> dict:
    """Vérifie (interface, signature, empreintes du code déposé), puis enregistre le module comme installé. Les refus sont explicites et journalisés."""
    from core.gouvernance import journaliser

    if not compatible(m):
        journaliser(c, org_id, par, "module.refuse", m.nom, f"interface {m.interface} incompatible avec {INTERFACE_MODULES}")
        return {"installe": False, "motif": f"interface {m.interface} incompatible avec le noyau {INTERFACE_MODULES}"}
    if not verifier(m, cle_publique_hex):
        journaliser(c, org_id, par, "module.refuse", m.nom, "signature absente ou invalide")
        return {"installe": False, "motif": "signature absente ou invalide : seul un module signé par l'éditeur s'installe"}
    if m.type == "cible" and m.fichiers is None:
        journaliser(c, org_id, par, "module.refuse", m.nom, "manifeste sans empreintes de fichiers")
        return {"installe": False, "motif": "manifeste sans empreintes de fichiers : le code du module doit être couvert par la signature"}
    dossier = dossier_module(m)
    if dossier is not None:
        ecarts = verifier_fichiers(m, dossier)
        if ecarts:
            journaliser(c, org_id, par, "module.refuse", m.nom, "code déposé différent du code signé : " + "; ".join(ecarts)[:200])
            return {"installe": False, "motif": "le code déposé ne correspond pas à ce que l'éditeur a signé : " + "; ".join(ecarts)[:300]}
    pub = (cle_publique_hex if cle_publique_hex is not None else cle_publique_editeur()).strip()
    c.executer("UPDATE modules SET actif = 0 WHERE org_id = ? AND nom = ?", (org_id, m.nom))
    c.executer("INSERT INTO modules (id, org_id, nom, version, type, interface, empreinte_cle, installe_le, actif) VALUES (?,?,?,?,?,?,?,?,1)",
               (db.nouvel_id(), org_id, m.nom, m.version, m.type, m.interface, hashlib.sha256(pub.encode()).hexdigest()[:16], db.maintenant()))
    journaliser(c, org_id, par, "module.installe", m.nom, f"{m.type} {m.version}")
    return {"installe": True, "nom": m.nom, "version": m.version}


def installes(c: db.Connexion, org_id: str) -> list[dict]:
    return c.lignes("SELECT nom, version, type, interface, installe_le FROM modules WHERE org_id = ? AND actif = 1 ORDER BY nom", (org_id,))

"""Fiches d'agents : un dossier par agent sous `agents/`, un fichier `agent.md` avec un en-tête (clé: valeur) et, en corps,
les consignes de l'agent en français. Pas de bibliothèque YAML : l'en-tête est volontairement simple."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_AGENTS = RACINE / "agents"
CLASSES_MODELE = {"raisonnement": "claude-opus-5-5", "equilibre": "claude-sonnet-5-5", "rapide": "claude-haiku-5-5"}


@dataclass
class Fiche:
    id: str
    nom: str
    fonction: str
    classe_modele: str = "raisonnement"
    outils: list[str] = field(default_factory=list)
    budget_tours: int = 6
    consignes: str = ""
    chemin: str = ""
    couloir: str = ""            # couloir de l'aquarium (direction, croissance, finances, batir) ; déduit de l'identifiant sinon

    @property
    def modele(self) -> str:
        """Le modèle vient de la classe, sauf si le fondateur le fixe par variable d'environnement (MODELE_<ID>)."""
        force = os.environ.get("MODELE_" + re.sub(r"[^A-Z0-9]+", "_", self.id.upper()).strip("_"), "")
        return force or CLASSES_MODELE.get(self.classe_modele, CLASSES_MODELE["raisonnement"])

    @property
    def signature(self) -> str:
        return f"{self.nom} ({self.id}), {self.fonction}"


def _valeur(brut: str):
    brut = brut.strip()
    if brut.startswith("[") and brut.endswith("]"):
        return [x.strip().strip("'\"") for x in brut[1:-1].split(",") if x.strip()]
    if brut.isdigit():
        return int(brut)
    return brut.strip("'\"")


def lire_fiche(chemin: Path) -> Fiche:
    texte = chemin.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texte, flags=re.S)
    if not m:
        raise ValueError(f"{chemin} : en-tête `---` absent")
    entete: dict = {}
    for ligne in m.group(1).splitlines():
        if ":" in ligne and not ligne.startswith("#"):
            k, v = ligne.split(":", 1)
            entete[k.strip()] = _valeur(v)
    for obligatoire in ("id", "nom", "fonction"):
        if not entete.get(obligatoire):
            raise ValueError(f"{chemin} : champ `{obligatoire}` manquant")
    return Fiche(id=str(entete["id"]), nom=str(entete["nom"]), fonction=str(entete["fonction"]),
                 classe_modele=str(entete.get("classe_modele", "raisonnement")), outils=list(entete.get("outils", []) or []),
                 budget_tours=int(entete.get("budget_tours", 6)), consignes=m.group(2).strip(), chemin=str(chemin), couloir=str(entete.get("couloir", "")))


def charger(dossier: Path | None = None) -> dict[str, Fiche]:
    dossier = dossier or DOSSIER_AGENTS
    fiches: dict[str, Fiche] = {}
    for chemin in sorted(dossier.glob("*/agent.md")):
        f = lire_fiche(chemin)
        if f.id in fiches:
            raise ValueError(f"identifiant d'agent en double : {f.id}")
        fiches[f.id] = f
    return fiches

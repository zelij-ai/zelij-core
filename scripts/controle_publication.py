"""Contrôle de publication : rien d'interne ne doit sortir dans le dépôt public.

Deux listes : les motifs génériques, ici (secrets, clés, adresses IP, codes d'agents de l'éditeur, courriels privés), et une
liste privée de termes propres à l'éditeur (noms de clients, domaines internes, infrastructures), lue depuis le fichier
désigné par ZELIJ_CORE_INTERDITS, qui ne fait jamais partie du dépôt. Le contrôle échoue au premier motif trouvé ; il est
exécuté par les tests et doit l'être avant toute publication. Usage : `python scripts/controle_publication.py [racine]`."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
IGNORES = {".git", "data", "__pycache__", ".pytest_cache", "node_modules", ".venv"}
EXTENSIONS = {".py", ".md", ".html", ".css", ".js", ".json", ".yml", ".yaml", ".txt", ".toml", ".env.example", ".cfg", ".ini", ".sh", ".svg", "Dockerfile",
              "Caddyfile", ".gitignore", ".dockerignore"}
MOTIFS_GENERIQUES = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"), "clé d'API Anthropic"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"), "clé privée"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "adresse IPv4"),
    # tous les préfixes de jetons GitHub : personnel (ghp_, github_pat_), OAuth (gho_), utilisateur (ghu_), installation (ghs_), rafraîchissement (ghr_)
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "jeton GitHub"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "clé AWS"),
    (re.compile(r"\bA(0[0-9]|[1-7][0-9])\b"), "code d'agent de l'éditeur (A00–A79)"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@(gmail|outlook|hotmail|yahoo|proton)\.[a-z]{2,}\b", re.I), "adresse e-mail personnelle"),
    (re.compile(r"\bpassword\s*=\s*['\"][^'\"]{4,}['\"]", re.I), "mot de passe en clair"),
]
EXCEPTIONS_IP = {"127.0.0.1", ".".join(["0"] * 4), ".".join(["255"] * 4)}   # assemblées : rien à voir avec une écoute réseau


def charger_interdits_prives() -> list[str]:
    chemin = os.environ.get("ZELIJ_CORE_INTERDITS", "")
    if not chemin or not Path(chemin).exists():
        return []
    return [l.strip() for l in Path(chemin).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def fichiers(racine: Path):
    for p in racine.rglob("*"):
        if any(part in IGNORES for part in p.parts):
            continue
        if p.is_file() and (p.suffix in EXTENSIONS or p.name in EXTENSIONS):
            yield p


def controler(racine: Path | None = None, interdits_prives: list[str] | None = None) -> list[str]:
    racine = racine or RACINE
    interdits = interdits_prives if interdits_prives is not None else charger_interdits_prives()
    constats: list[str] = []
    for p in fichiers(racine):
        if p.resolve() == Path(__file__).resolve():
            continue
        texte = p.read_text(encoding="utf-8", errors="replace")
        for motif, libelle in MOTIFS_GENERIQUES:
            for m in motif.finditer(texte):
                if libelle == "adresse IPv4" and m.group(0) in EXCEPTIONS_IP:
                    continue
                ligne = texte.count("\n", 0, m.start()) + 1
                constats.append(f"{p.relative_to(racine)}:{ligne} : {libelle} ({m.group(0)[:40]})")
        bas = texte.lower()
        for terme in interdits:
            if terme.lower() in bas:
                ligne = bas.count("\n", 0, bas.index(terme.lower())) + 1
                constats.append(f"{p.relative_to(racine)}:{ligne} : terme privé interdit ({terme})")
    return constats


if __name__ == "__main__":
    racine = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else RACINE
    c = controler(racine)
    for ligne in c:
        print(ligne)
    print(f"{len(c)} constat(s)" if c else "contrôle de publication : rien d'interne trouvé")
    sys.exit(1 if c else 0)

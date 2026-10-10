"""Provenance d'une décision : ce que l'agent a lu au dehors pendant qu'il la préparait, et ce que le bureau lui a refusé.

Un paquet de décision est écrit par un agent. Si une page ou un fichier lu en route contenait une consigne cachée, le paquet
peut porter la tâche d'un tiers sous un objectif anodin. Le fondateur doit donc voir, sur la décision elle-même, d'où elle
vient : les adresses lues, les fichiers du dépôt lus, les actions refusées. Rien ici ne juge le contenu : ce sont des faits
relevés par l'exécuteur, que l'agent ne peut ni écrire ni effacer."""
from __future__ import annotations

from urllib.parse import urlsplit

ELEMENTS_MAX = 8
NIVEAUX = {"interne": "Préparée sans lecture de contenu externe", "externe": "Préparée après lecture de contenu externe",
           "alerte": "À relire avec attention avant d'approuver"}


def _adresse(url: str) -> str:
    """Hôte et chemin, sans paramètres : ce qui suit le « ? » peut porter une donnée, il n'a pas à s'afficher ni à se garder."""
    p = urlsplit(str(url or "").strip())
    return ((p.hostname or "") + (p.path or "")).rstrip("/")[:90] or str(url)[:90]


def depuis_appels(appels: list[dict] | None) -> dict:
    """Relevé tiré des appels d'outils d'une exécution : pages lues, fichiers du dépôt lus, refus du bureau."""
    pages: list[str] = []
    depot: list[str] = []
    refus: list[str] = []
    for a in appels or []:
        outil, entree, resultat = str(a.get("outil") or ""), a.get("entree") if isinstance(a.get("entree"), dict) else {}, str(a.get("resultat") or "")
        if resultat.startswith("refus"):
            refus.append(f"{outil[:40]} : {resultat[8:120].strip() or 'refusé'}")
            continue
        if outil == "lire_page":
            adresse = _adresse(entree.get("url"))
            if adresse and adresse not in pages:
                pages.append(adresse)
        elif outil == "depot_lire":
            chemin = str(entree.get("chemin") or "").strip("/")[:90] or "(racine du dépôt)"
            if chemin not in depot:
                depot.append(chemin)
    return {"pages": pages[:ELEMENTS_MAX], "depot": depot[:ELEMENTS_MAX], "refus": refus[:ELEMENTS_MAX],
            "autres": max(0, len(pages) - ELEMENTS_MAX) + max(0, len(depot) - ELEMENTS_MAX)}


def evaluer(provenance: dict | None, *, demandeur: str, agent_cible: str, tache: str) -> dict:
    """Le niveau affiché sur la décision et ses raisons. `demandeur` est la signature « Prénom Nom (identifiant), fonction ».
    - interne : rien d'externe n'a été lu ;
    - externe : une page ou un fichier a été lu : la tâche est à relire ;
    - alerte : en plus, la tâche est confiée à un autre agent que celui qui a préparé la décision, ou le bureau a refusé
      une action pendant la préparation. C'est la forme que prend une décision dictée par un contenu piégé."""
    p = provenance if isinstance(provenance, dict) else {}
    pages, depot, refus = list(p.get("pages") or []), list(p.get("depot") or []), list(p.get("refus") or [])
    externe = bool(pages or depot)
    raisons: list[str] = []
    debut, fin = demandeur.find("("), demandeur.find(")")
    auteur = demandeur[debut + 1:fin].strip() if 0 <= debut < fin else ""
    if refus:
        raisons.append(f"le bureau a refusé {len(refus)} action(s) pendant la préparation")
    if externe and agent_cible and tache and auteur and agent_cible != auteur:
        raisons.append(f"la tâche est confiée à un autre agent ({agent_cible}) que celui qui a préparé la décision ({auteur})")
    niveau = "alerte" if raisons else ("externe" if externe else "interne")
    return {"niveau": niveau, "libelle": NIVEAUX[niveau], "raisons": raisons, "pages": pages, "depot": depot, "refus": refus, "autres": int(p.get("autres") or 0),
            "connue": isinstance(provenance, dict) and bool(provenance)}

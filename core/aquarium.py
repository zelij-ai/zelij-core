"""L'aquarium : regardez vos agents travailler. Ce qu'il montre est réel, rien d'autre : les exécutions des dernières
24 heures, les outils appelés, les décisions ouvertes et prises, les demandes du fondateur, le coût du jour. La scène
se rejoue sur une ligne de temps. Les postes libres nagent en pointillé dans leur couloir. La page publique (jeton)
montre la même scène, titres et comptes seulement, sans aucun détail interne."""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone

from core import db, passerelle
from core.catalogue import POSTES_LIBRES

COULOIRS = [
    {"id": "direction", "nom": "DIRECTION", "couleur": "#d19a1b"},
    {"id": "croissance", "nom": "MARKETING & PRODUITS", "couleur": "#37b385"},
    {"id": "finances", "nom": "FINANCES & CLIENTS", "couleur": "#8ea6f0"},
    {"id": "batir", "nom": "SOFTWARE FACTORY", "couleur": "#b48cf0"},
    {"id": "libres", "nom": "POSTES LIBRES", "couleur": "#8a8378"},
]
_COULOIR_PAR_AGENT = {"chef-de-cabinet": "direction", "croissance": "croissance", "finances-clients": "finances", "batisseur": "batir"}
FONDATEUR = {"id": "fondateur", "nom": "Fondateur", "fonction": "décide", "couloir": "direction", "couleur": "#f1d48a"}


def couloir_de(fiche) -> str:
    return getattr(fiche, "couloir", "") or _COULOIR_PAR_AGENT.get(fiche.id, "direction")


def _agent_depuis_signature(signature: str, fiches: dict) -> str | None:
    """« Prénom Nom (identifiant), fonction » → identifiant."""
    if not signature:
        return None
    debut, fin = signature.find("("), signature.find(")")
    if 0 < debut < fin:
        ident = signature[debut + 1:fin].strip()
        if ident in fiches:
            return ident
    for f in fiches.values():
        if f.nom and f.nom in signature:
            return f.id
    return None


def evenements(c: db.Connexion, org_id: str, fiches: dict, *, depuis: str, public: bool = False) -> list[dict]:
    """La ligne de temps : exécutions, outils, décisions ouvertes et prises, demandes et publications. Triée, bornée."""
    out: list[dict] = []
    for e in c.lignes("SELECT id, agent, tache, statut, outils, cout_usd, cree_le, fini_le FROM executions WHERE org_id = ? AND cree_le >= ? ORDER BY cree_le", (org_id, depuis)):
        out.append({"t": e["cree_le"], "type": "execution", "acteur": e["agent"], "cible": None,
                    "texte": f"{e['tache']} · {e['statut']}" if not public else f"travaille · {e['statut']}"})
        if not public:
            try:
                outils = json.loads(e["outils"] or "[]")
            except ValueError:
                outils = []
            for o in outils[:6]:
                out.append({"t": e["fini_le"] or e["cree_le"], "type": "outil", "acteur": e["agent"], "cible": None, "texte": f"outil {o.get('outil')}"})
    for d in c.lignes("SELECT demandeur, objectif, etat, consigne, decidee_par, cree_le, decidee_le FROM decisions WHERE org_id = ? AND (cree_le >= ? OR decidee_le >= ?) ORDER BY cree_le",
                      (org_id, depuis, depuis)):
        acteur = _agent_depuis_signature(d["demandeur"], fiches) or "chef-de-cabinet"
        objet = "une décision" if public else d["objectif"]      # l'objet d'une décision est interne : jamais sur la page publique
        if d["cree_le"] >= depuis:
            out.append({"t": d["cree_le"], "type": "decision", "acteur": acteur, "cible": "fondateur", "texte": f"propose : {objet}"})
        if d["decidee_le"] and d["decidee_le"] >= depuis:
            libelle = {"approuvee": "approuve", "refusee": "refuse", "a_modifier": "demande des changements"}.get(d["etat"], d["etat"])
            texte = f"{libelle} : {objet}" + (f" — {d['consigne']}" if d["consigne"] and not public else "")
            out.append({"t": d["decidee_le"], "type": "decision_ceo", "acteur": "fondateur", "cible": acteur, "texte": texte})
    for j in c.lignes("SELECT acteur, action, cible, detail, cree_le FROM journal WHERE org_id = ? AND cree_le >= ? ORDER BY cree_le", (org_id, depuis)):
        if j["action"] == "demande":
            out.append({"t": j["cree_le"], "type": "echange", "acteur": "fondateur", "cible": j["cible"] if j["cible"] in fiches else "chef-de-cabinet",
                        "texte": "demande : " + ((j["detail"] or "")[:90] if not public else "une demande au bureau")})
        elif j["action"].startswith("publication.") and j["action"] not in ("publication.brouillon",):
            out.append({"t": j["cree_le"], "type": "echange", "acteur": "croissance", "cible": "fondateur",
                        "texte": j["action"].split(".", 1)[1] + (" · " + (j["detail"] or "")[:80] if not public else "")})
        elif j["action"] == "execution.apres_approbation":
            out.append({"t": j["cree_le"], "type": "execution", "acteur": _agent_depuis_signature(j["acteur"], fiches) or "chef-de-cabinet", "cible": None,
                        "texte": "exécute le plan approuvé" if public else f"exécute le plan approuvé · {(j['detail'] or '')[:60]}"})
    out.sort(key=lambda x: x["t"])
    return out[-300:]


def etat(c: db.Connexion, org_id: str, fiches: dict, *, heures: int = 24, public: bool = False) -> dict:
    maintenant = datetime.now(timezone.utc)
    depuis = (maintenant - timedelta(hours=heures)).isoformat(timespec="seconds")
    execs = c.lignes("SELECT agent, statut, cout_usd, cree_le FROM executions WHERE org_id = ? AND cree_le >= ?", (org_id, depuis))
    attente = c.une("SELECT COUNT(*) AS n FROM decisions WHERE org_id = ? AND etat = 'en_attente'", (org_id,)) or {"n": 0}
    taux = passerelle.taux_usd_eur()
    agents = []
    for f in fiches.values():
        miens = [e for e in execs if e["agent"] == f.id]
        dernier = max((e["cree_le"] for e in miens), default=None)
        couloir = couloir_de(f)
        agents.append({"id": f.id, "nom": f.nom, "prenom": f.nom.split(" ")[0], "fonction": f.fonction, "couloir": couloir,
                       "couleur": next((k["couleur"] for k in COULOIRS if k["id"] == couloir), "#d19a1b"),
                       "actif": bool(dernier) and dernier >= (maintenant - timedelta(hours=2)).isoformat(timespec="seconds"),
                       "en_cours": any(e["statut"] == "en_cours" for e in miens), "dernier": dernier, "activite": len(miens),
                       "cout_eur": round(sum(float(e["cout_usd"] or 0) for e in miens) * taux, 4)})
    return {"heures": heures, "maintenant": maintenant.isoformat(timespec="seconds"), "depuis": depuis, "couloirs": COULOIRS, "fondateur": FONDATEUR, "agents": agents,
            "postes_libres": [{"id": p["id"], "nom": p["nom"], "resume": p["resume"], "couloir": "libres"} for p in POSTES_LIBRES],
            "evenements": evenements(c, org_id, fiches, depuis=depuis, public=public),
            "cout_jour_eur": round(sum(float(e["cout_usd"] or 0) for e in execs) * taux, 4), "executions": len(execs),
            "decisions_en_attente": int(attente["n"]), "public": public}


def jeton_public(c: db.Connexion, org_id: str) -> str | None:
    r = c.une("SELECT jeton_public FROM organisations WHERE id = ?", (org_id,))
    return (r or {}).get("jeton_public") or None


def ouvrir_vitrine(c: db.Connexion, org_id: str, *, par: str) -> str:
    """Crée ou renouvelle le jeton de la page publique. Le renouveler coupe l'ancien lien."""
    from core.gouvernance import journaliser

    jeton = secrets.token_urlsafe(18)
    c.executer("UPDATE organisations SET jeton_public = ? WHERE id = ?", (jeton, org_id))
    journaliser(c, org_id, par, "vitrine.ouverte", "", "page publique « regardez nos agents travailler »")
    return jeton


def fermer_vitrine(c: db.Connexion, org_id: str, *, par: str) -> None:
    from core.gouvernance import journaliser

    c.executer("UPDATE organisations SET jeton_public = NULL WHERE id = ?", (org_id,))
    journaliser(c, org_id, par, "vitrine.fermee", "", "")


def organisation_par_jeton(c: db.Connexion, jeton: str) -> dict | None:
    if not jeton or len(jeton) < 12:
        return None
    return c.une("SELECT id, nom FROM organisations WHERE jeton_public = ?", (jeton,))

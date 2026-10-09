"""Gouvernance : le paquet de décision et la porte du fondateur.

Un agent ne décide jamais seul de ce qui engage l'entreprise : argent, exposition publique, suppression, irréversible. Il
ouvre un paquet (objectif, proposition, pourquoi maintenant, options, recommandation, risques, réversibilité, plan, retour
arrière, impact), le fondateur approuve, refuse ou demande des changements avec une consigne obligatoire. Tout est journalisé."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from core import db

ETATS = {"en_attente": "En attente", "approuvee": "Approuvée", "refusee": "Refusée", "a_modifier": "À modifier"}
ACTIONS = {"approuver": "approuvee", "refuser": "refusee", "a_modifier": "a_modifier"}
REVERSIBILITES = ("reversible", "partielle", "irreversible")


@dataclass
class Paquet:
    demandeur: str
    objectif: str
    proposition: str = ""
    pourquoi_maintenant: str = ""
    options: list[str] = field(default_factory=list)
    recommandation: str = ""
    risques: list[str] = field(default_factory=list)
    reversibilite: str = "reversible"
    plan: list[str] = field(default_factory=list)
    retour_arriere: list[str] = field(default_factory=list)
    impact_eur: float = 0.0
    portee: str = ""
    execution_id: str | None = None
    agent_cible: str = ""       # l'agent qui exécutera le plan si le fondateur approuve (vide : rien ne s'exécute)
    tache: str = ""             # la consigne d'exécution transmise à cet agent

    def valider(self) -> list[str]:
        """Un paquet incomplet ne s'ouvre pas : le fondateur doit pouvoir décider sans poser de question."""
        manques = []
        if not self.objectif.strip():
            manques.append("objectif")
        if not self.proposition.strip():
            manques.append("proposition")
        if len(self.options) < 2:
            manques.append("au moins deux options")
        if not self.recommandation.strip():
            manques.append("recommandation")
        if self.reversibilite not in REVERSIBILITES:
            manques.append("réversibilité (reversible, partielle, irreversible)")
        if self.reversibilite != "reversible" and not self.retour_arriere:
            manques.append("retour arrière (obligatoire dès que ce n'est pas réversible)")
        return manques


def engage(paquet: Paquet, *, exposition_publique: bool = False, suppression: bool = False) -> list[str]:
    """Pourquoi la décision revient au fondateur. Liste vide = l'agent peut agir et journaliser."""
    motifs = []
    if paquet.impact_eur and paquet.impact_eur > 0:
        motifs.append(f"engage de l'argent ({paquet.impact_eur:.2f} €)")
    if paquet.reversibilite != "reversible":
        motifs.append(f"n'est pas réversible ({paquet.reversibilite})")
    if exposition_publique:
        motifs.append("expose quelque chose au public")
    if suppression:
        motifs.append("supprime des données")
    return motifs


def depuis_sortie_agent(demandeur: str, sortie: dict, *, execution_id: str | None = None, portee: str = "") -> Paquet:
    """Construit un paquet à partir du JSON rendu par un agent ; les champs absents restent vides et `valider()` les signale."""
    def liste(v) -> list[str]:
        return [str(x) for x in v] if isinstance(v, list) else ([str(v)] if v else [])

    try:
        impact = float(sortie.get("impact_eur") or 0)
    except (TypeError, ValueError):
        impact = 0.0
    return Paquet(
        demandeur=demandeur, objectif=str(sortie.get("objectif") or ""), proposition=str(sortie.get("proposition") or ""),
        pourquoi_maintenant=str(sortie.get("pourquoi_maintenant") or ""), options=liste(sortie.get("options")),
        recommandation=str(sortie.get("recommandation") or ""), risques=liste(sortie.get("risques")),
        reversibilite=str(sortie.get("reversibilite") or "reversible"), plan=liste(sortie.get("plan")),
        retour_arriere=liste(sortie.get("retour_arriere")), impact_eur=impact, portee=portee, execution_id=execution_id,
        agent_cible=str(sortie.get("agent_cible") or "")[:60], tache=str(sortie.get("tache") or "")[:4000],
    )


def journaliser(c: db.Connexion, org_id: str, acteur: str, action: str, cible: str = "", detail: str = "") -> None:
    c.executer("INSERT INTO journal (id, org_id, acteur, action, cible, detail, cree_le) VALUES (?,?,?,?,?,?,?)",
               (db.nouvel_id(), org_id, acteur, action, cible, detail[:600], db.maintenant()))


def ouvrir(c: db.Connexion, org_id: str, paquet: Paquet) -> str:
    manques = paquet.valider()
    if manques:
        raise ValueError("paquet incomplet : " + ", ".join(manques))
    did = db.nouvel_id()
    d = asdict(paquet)
    c.executer("INSERT INTO decisions (id, org_id, demandeur, objectif, proposition, pourquoi_maintenant, options, recommandation, risques, "
               "reversibilite, plan, retour_arriere, impact_eur, etat, portee, execution_id, agent_cible, tache, cree_le) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (did, org_id, d["demandeur"], d["objectif"], d["proposition"], d["pourquoi_maintenant"], json.dumps(d["options"], ensure_ascii=False),
                d["recommandation"], json.dumps(d["risques"], ensure_ascii=False), d["reversibilite"], json.dumps(d["plan"], ensure_ascii=False),
                json.dumps(d["retour_arriere"], ensure_ascii=False), d["impact_eur"], "en_attente", d["portee"], d["execution_id"],
                d["agent_cible"], d["tache"], db.maintenant()))
    journaliser(c, org_id, paquet.demandeur, "decision.ouverte", did, paquet.objectif)
    return did


def _hydrater(row: dict) -> dict:
    for k in ("options", "risques", "plan", "retour_arriere"):
        try:
            row[k] = json.loads(row.get(k) or "[]")
        except ValueError:
            row[k] = []
    row["etat_libelle"] = ETATS.get(row["etat"], row["etat"])
    return row


def en_attente(c: db.Connexion, org_id: str) -> list[dict]:
    return [_hydrater(r) for r in c.lignes("SELECT * FROM decisions WHERE org_id = ? AND etat = 'en_attente' ORDER BY cree_le", (org_id,))]


def recentes(c: db.Connexion, org_id: str, limite: int = 20) -> list[dict]:
    return [_hydrater(r) for r in c.lignes("SELECT * FROM decisions WHERE org_id = ? AND etat <> 'en_attente' ORDER BY decidee_le DESC LIMIT ?", (org_id, limite))]


def lire(c: db.Connexion, org_id: str, decision_id: str) -> dict | None:
    r = c.une("SELECT * FROM decisions WHERE id = ? AND org_id = ?", (decision_id, org_id))
    return _hydrater(r) if r else None


def decider(c: db.Connexion, org_id: str, decision_id: str, action: str, *, par: str, consigne: str = "") -> dict:
    """Exécute la décision du fondateur. « a_modifier » exige une consigne : elle est transmise à l'agent demandeur."""
    if action not in ACTIONS:
        raise ValueError("action inconnue")
    consigne = (consigne or "").strip()
    if action == "a_modifier" and not consigne:
        raise ValueError("Dis ce que tu veux changer : la consigne est transmise à l'agent demandeur.")
    d = lire(c, org_id, decision_id)
    if d is None:
        raise LookupError("décision introuvable")
    if d["etat"] != "en_attente":
        raise ValueError("décision déjà prise")
    c.executer("UPDATE decisions SET etat = ?, consigne = ?, decidee_par = ?, decidee_le = ? WHERE id = ? AND org_id = ?",
               (ACTIONS[action], consigne[:2000], par, db.maintenant(), decision_id, org_id))
    journaliser(c, org_id, par, f"decision.{ACTIONS[action]}", decision_id, consigne or d["objectif"])
    return lire(c, org_id, decision_id)

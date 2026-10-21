"""L'avocat du diable : avant que le fondateur ne tranche, un second avis qui plaide CONTRE la recommandation de l'agent.

Un agent qui ouvre une décision a déjà choisi : sa recommandation est l'option qu'il préfère, et le paquet est écrit pour
elle. L'avocat du diable lit le même paquet, sans outil, sans mémoire, et cherche ce qui ferait échouer la recommandation :
trois objections au plus, la question à poser avant d'approuver, ce qui ferait changer d'avis. Il ne décide rien, il ne
remplace rien : il s'affiche sous la recommandation, dans le bureau, dans la poche (e-mail, Telegram) et en swipant.

Coût : un appel court au modèle « rapide » (réglable par AVOCAT_MODELE), compté dans le plafond mensuel comme une exécution.
AVOCAT_DU_DIABLE=0 le retire. En mode démonstration, un réquisitoire écrit d'avance tient sa place : rien ne sort."""
from __future__ import annotations

import json
import logging
import os
import re

from core import db, passerelle

logger = logging.getLogger("zelij.core.avocat")

VERDICTS = ("approuver", "attendre", "refuser")
SYSTEM = (
    "Tu es l'avocat du diable du bureau d'une petite entreprise. Un agent vient d'ouvrir une décision pour le fondateur et "
    "recommande une option. Ton rôle : plaider CONTRE cette recommandation, honnêtement, pour que le fondateur décide en connaissance "
    "de cause. Tu n'as aucun outil, aucun accès au dehors : tu ne vois que le paquet. Tu n'inventes aucun fait ; quand tu supposes, "
    "tu écris « si… ». Tu n'écris aucune adresse web. Tu vouvoies le fondateur. Français, phrases courtes et concrètes.\n"
    "Réponds UNIQUEMENT par un objet JSON : {\"objections\": [au plus trois phrases, les plus fortes d'abord], "
    "\"question\": \"la question à poser à l'agent avant d'approuver\", \"bascule\": \"ce qui vous ferait changer d'avis sur la "
    "recommandation\", \"verdict\": \"approuver\" | \"attendre\" | \"refuser\"}. « approuver » quand, même en cherchant, la "
    "recommandation tient."
)
AVIS_DEMO = {
    "objections": ["La recommandation suppose que le besoin est confirmé ; rien dans le paquet ne le prouve.",
                   "L'option « attendre » n'a pas de coût décrit : si elle n'en a aucun, pourquoi décider aujourd'hui ?",
                   "Le retour arrière est écrit, mais personne ne dit combien de temps il prendrait."],
    "question": "Qu'est-ce qui se passe, concrètement, si cette décision attend une semaine ?",
    "bascule": "Une date ou un client qui rend l'attente coûteuse.",
    "verdict": "attendre",
}


def actif() -> bool:
    return os.environ.get("AVOCAT_DU_DIABLE", "1").strip() != "0"


def modele() -> str:
    from core.agents import CLASSES_MODELE

    return os.environ.get("AVOCAT_MODELE", "").strip() or os.environ.get("MODELE_RAPIDE", "").strip() or CLASSES_MODELE["rapide"]


def _texte(reponse) -> str:
    morceaux = []
    for b in getattr(reponse, "content", None) or []:
        if getattr(b, "type", "") == "text":
            morceaux.append(str(getattr(b, "text", "") or ""))
    return "\n".join(morceaux).strip()


def _normaliser(brut) -> dict | None:
    """Le JSON du modèle, borné et vérifié : trois objections au plus, verdict dans la liste, rien d'autre ne passe."""
    if not isinstance(brut, dict):
        return None
    objections = [str(o).strip()[:240] for o in (brut.get("objections") or []) if str(o).strip()][:3]
    if not objections:
        return None
    verdict = str(brut.get("verdict") or "attendre").strip().lower()
    if verdict not in VERDICTS:
        verdict = "attendre"
    return {"objections": objections, "question": str(brut.get("question") or "").strip()[:240],
            "bascule": str(brut.get("bascule") or "").strip()[:240], "verdict": verdict}


def depuis_texte(texte: str) -> dict | None:
    """Trouve l'objet JSON dans la réponse (même entouré de prose ou de ```), sinon None : pas d'avocat vaut mieux qu'un avocat inventé."""
    texte = (texte or "").strip()
    for candidat in (texte, re.sub(r"^```(?:json)?|```$", "", texte, flags=re.M).strip()):
        try:
            return _normaliser(json.loads(candidat))
        except ValueError:
            pass
    m = re.search(r"\{.*\}", texte, flags=re.S)
    if m:
        try:
            return _normaliser(json.loads(m.group(0)))
        except ValueError:
            return None
    return None


def requisitoire(paquet: dict) -> str:
    """Le paquet, tel que l'avocat le lit : les champs utiles, bornés, sans la tâche d'exécution ni la provenance."""
    lignes = [f"Objectif : {paquet.get('objectif', '')}", f"Proposition : {str(paquet.get('proposition', ''))[:1500]}"]
    if paquet.get("pourquoi_maintenant"):
        lignes.append(f"Pourquoi maintenant : {str(paquet['pourquoi_maintenant'])[:500]}")
    lignes.append("Options : " + " · ".join(str(o) for o in (paquet.get("options") or [])[:6]))
    lignes.append(f"Recommandation de l'agent : {paquet.get('recommandation', '')}")
    if paquet.get("risques"):
        lignes.append("Risques déclarés par l'agent : " + " ; ".join(str(r) for r in paquet["risques"][:6]))
    lignes.append(f"Réversibilité : {paquet.get('reversibilite', 'reversible')} · impact : {float(paquet.get('impact_eur') or 0):.2f} €")
    if paquet.get("plan"):
        lignes.append("Plan : " + " → ".join(str(p) for p in paquet["plan"][:8]))
    if paquet.get("retour_arriere"):
        lignes.append("Retour arrière : " + " → ".join(str(p) for p in paquet["retour_arriere"][:6]))
    return "\n".join(lignes)


def plaider(paquet: dict, *, appel=None) -> tuple[dict | None, float]:
    """Un appel court au modèle ; rend (avis, coût en USD). Avis None si le modèle ne rend rien d'exploitable."""
    m = modele()
    reponse = (appel or passerelle.appeler)(modele=m, system=SYSTEM, messages=[{"role": "user", "content": requisitoire(paquet)}], tools=None, max_tokens=700)
    cout = passerelle.cout_usd(m, getattr(reponse, "usage", None))
    avis = depuis_texte(_texte(reponse))
    if avis is not None:
        avis["modele"] = m
    return avis, cout


def enregistrer(c: db.Connexion, org_id: str, decision_id: str, avis: dict, cout_usd: float = 0.0) -> None:
    c.executer("UPDATE decisions SET avocat = ?, avocat_cout_usd = ? WHERE id = ? AND org_id = ?",
               (json.dumps(avis, ensure_ascii=False)[:4000], float(cout_usd or 0), decision_id, org_id))


def lire(brut) -> dict | None:
    """L'avis rangé en base, revalidé à la lecture (une base modifiée à la main ne fait pas afficher n'importe quoi)."""
    if not brut:
        return None
    try:
        objet = json.loads(brut)
    except (ValueError, TypeError):
        return None
    avis = _normaliser(objet)
    if avis is not None:
        avis["modele"] = str(objet.get("modele") or "")[:60]
    return avis


def plaider_decision(c: db.Connexion, org_id: str, decision_id: str, paquet: dict, *, appel=None) -> dict | None:
    """À l'ouverture d'une décision : plaide, range l'avis sur la décision, journalise. N'échoue jamais : sans avocat, la
    décision attend quand même le fondateur. Respecte le plafond mensuel comme une exécution d'agent."""
    from core import demo, gouvernance

    if not actif():
        return None
    try:
        if demo.actif():
            avis, cout = dict(AVIS_DEMO, modele="démonstration"), 0.0
        else:
            atteint, depense, plafond = passerelle.plafond_atteint(c, org_id, db.mois_courant())
            if atteint:
                gouvernance.journaliser(c, org_id, "avocat-du-diable", "decision.avocat.plafond", decision_id, f"plafond mensuel atteint : {depense:.2f} € sur {plafond:.2f} €")
                return None
            avis, cout = plaider(paquet, appel=appel)
        if avis is None:
            gouvernance.journaliser(c, org_id, "avocat-du-diable", "decision.avocat.muet", decision_id, "réponse inexploitable, pas d'avis")
            return None
        enregistrer(c, org_id, decision_id, avis, cout)
        gouvernance.journaliser(c, org_id, "avocat-du-diable", "decision.avocat", decision_id, f"{avis['verdict']} · {avis['objections'][0]}")
        return avis
    except Exception as exc:  # noqa: BLE001 — l'avocat ne bloque jamais une décision
        logger.warning("Avocat du diable : pas d'avis pour la décision %s (%s)", decision_id, type(exc).__name__)
        try:
            gouvernance.journaliser(c, org_id, "avocat-du-diable", "decision.avocat.echec", decision_id, f"{type(exc).__name__}: {str(exc)[:160]}")
        except Exception:  # noqa: BLE001
            pass
        return None

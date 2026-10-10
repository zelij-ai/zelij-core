"""Mode démonstration : voir le bureau vivre en une minute, sans clé de modèle, sans e-mail, sans rien configurer.

`CORE_DEMO=1` ouvre un bureau déjà rempli (une entreprise fictive, une journée de travail des agents, des décisions en
attente, des finances, des contacts) et remplace le modèle par un scénario écrit ici : rien ne part vers un modèle ni vers
le réseau, rien ne coûte. Tout y est faux et le bandeau le dit sur chaque page.

Trois garde-fous pour qu'il ne s'active jamais par erreur sur une vraie installation :
- il refuse de démarrer sur PostgreSQL : il ne tourne que sur sa propre base SQLite, temporaire ;
- il refuse de démarrer si la base contient déjà une organisation qui n'est pas celle de la démonstration ;
- il refuse de démarrer en production (`CORE_ENV=production`)."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from core import db

ORGANISATION = "Atelier Nord · démo"
FONDATEUR = "fondatrice@atelier-nord.example"
BANDEAU = "Entreprise fictive et agents simulés. Rien n'est envoyé à un modèle, rien ne coûte."
SUGGESTIONS = ("Rédige une page Tarifs pour notre site", "Fais le point du mois", "Trouve-moi des prospects dans ma région", "Déploie le site sur Google Cloud")
GUIDE_INSTALLATION = "https://github.com/zelij-ai/zelij-core/blob/main/docs/INSTALLATION.md"
# Ce qu'une demande dépasse dans l'édition gratuite, et le module de l'éditeur qui y répond (identifiants de core/catalogue.py).
# C'est le même paquet « construire soi-même ou installer le module » que dans une vraie installation : il mène au catalogue.
_MODULES = (
    (r"\b(prospect|d[ée]march|client[s]? potentiel|leads?)", "prospection", "Trouver des prospects et préparer les premiers messages"),
    (r"\b(seo|r[ée]f[ée]rencement|google search|moteur de recherche|positions?)", "seo-geo", "Améliorer le référencement du site"),
    (r"\b(veille|prix des concurrents|tarifs? des concurrents|surveille les prix)", "veille-prix", "Suivre les prix des concurrents"),
    (r"\b(surveill|monitor|certificat|panne|disponibilit[ée])", "surveillance", "Surveiller le site et le serveur en continu"),
    (r"\b(cloud|google|aws|azure|d[ée]ploie)", "infra-cloud", "Déployer le site sur un grand cloud"),
    (r"\b(h[ée]berge|sans rien installer|mises? à jour automatique)", "zelij-cloud", "Faire héberger le bureau par l'éditeur"),
)


def actif() -> bool:
    return os.environ.get("CORE_DEMO", "").strip() == "1"


def verifier_demarrage() -> None:
    """Lève RuntimeError si la démonstration est demandée là où elle n'a rien à faire."""
    if not actif():
        return
    if os.environ.get("CORE_ENV") == "production":
        raise RuntimeError("CORE_DEMO=1 refusé en production : la démonstration ne tourne jamais sur une installation réelle")
    if db.url().startswith("postgres"):
        raise RuntimeError("CORE_DEMO=1 refusé sur PostgreSQL : la démonstration ne tourne que sur sa base SQLite temporaire")
    with db.connexion() as c:
        autres = c.lignes("SELECT nom FROM organisations WHERE nom <> ?", (ORGANISATION,))
    if autres:
        raise RuntimeError("CORE_DEMO=1 refusé : cette base contient déjà une organisation réelle")


# ---------------------------------------------------------------- le scénario : ce que « répond » un agent simulé

def _reponse(objet: dict) -> SimpleNamespace:
    texte = json.dumps(objet, ensure_ascii=False)
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=1200, output_tokens=max(120, len(texte) // 4), cache_read_input_tokens=0))


def _agent(system: str) -> str:
    m = re.search(r"Tu es [^()\n]*\(([a-z0-9-]+)\)", system or "")
    return m.group(1) if m else "chef-de-cabinet"


def _demande(instruction: str) -> str:
    m = re.search(r"«(.*?)»", instruction or "", flags=re.S)
    return (m.group(1) if m else instruction or "").strip()


_PAGE_TARIFS = {
    "title": "Tarifs de l'Atelier Nord", "meta_description": "Trois formules claires pour vos travaux de menuiserie, sans frais cachés.", "h1": "Nos tarifs",
    "intro": "Trois formules, un devis écrit avant tout travail, et aucun supplément sans votre accord.",
    "sections": [{"h2": "Formule Essentielle", "texte": "Pose et ajustement d'un ouvrage standard, sur une journée."},
                 {"h2": "Formule Sur mesure", "texte": "Conception, fabrication en atelier et pose, avec un plan validé par vous."},
                 {"h2": "Formule Rénovation", "texte": "Reprise d'un ouvrage ancien, diagnostic compris."}],
    "faq": [{"q": "Le devis est-il gratuit ?", "a": "Oui, et il vous engage seulement une fois signé."}], "sources": [],
}


def appel(*, modele: str = "", system: str = "", messages: list | None = None, tools: list | None = None, **_) -> SimpleNamespace:
    """Tient la place du modèle. Aucun appel réseau, aucun outil : une réponse écrite d'avance selon l'agent et la demande."""
    agent = _agent(system)
    instruction = str((messages or [{}])[0].get("content") or "")
    if "Décision approuvée par le fondateur" in instruction:
        return _reponse({"fait": ["Plan exécuté dans la démonstration (rien n'a été fait pour de vrai)."],
                         "reste_a_faire": ["Avec votre clé Claude, cet agent travaillerait réellement, avec ses outils et dans son budget."], "faits_sources": [],
                         "reponse": f"Compte rendu simulé de {agent} : dans une vraie installation, vous liriez ici ce qui a été fait, ce qui reste, et les sources."})
    demande = _demande(instruction).lower()
    for motif, pack_id, objectif in _MODULES:
        if re.search(motif, demande):
            return _reponse(_paquet_module(pack_id, objectif))
    if re.search(r"\b(page|article|r[ée]dige|tarif)", demande):
        return _reponse({"decision_requise": False, "reponse": "La page est prête. Elle ne part vers le site qu'après votre approbation.", "page": _PAGE_TARIFS,
                         "pourquoi_maintenant": "La page est rédigée ; rien n'est en ligne sans vous."})
    if re.search(r"\b(point|finance|mois|compta|chiffre)", demande):
        return _reponse({"decision_requise": False, "reponse": "Point du mois (démonstration) : les ventes confirmées, les charges déclarées et le coût des agents sont sur la page "
                                                              "Finances, avec la source de chaque total. Dans une vraie installation, l'agent lit ces registres avec son outil "
                                                              "et vous signale ce qui traîne."})
    return _reponse({"decision_requise": False, "reponse": "Je suis un agent simulé : dans cette démonstration, je réponds d'après un scénario. Essayez par exemple : « "
                                                          + " », « ".join(SUGGESTIONS) + " ». Avec votre clé Claude, je travaillerais vraiment."})


def _paquet_module(pack_id: str, objectif: str) -> dict:
    """Le paquet « construire soi-même ou installer le module » : la demande dépasse l'édition gratuite, le fondateur choisit."""
    from core import catalogue

    p = catalogue.par_id(pack_id) or {"nom": pack_id, "resume": ""}
    return {
        "decision_requise": True, "reponse": f"{objectif} dépasse ce bureau : deux voies possibles.", "objectif": objectif,
        "proposition": f"Installer le module {p['nom']} de l'éditeur plutôt que de le construire à la main. {p['resume']}",
        "pourquoi_maintenant": "Vous l'avez demandé à l'instant.",
        "options": [f"Installer le module {p['nom']}", "Construire soi-même avec le Bâtisseur (plusieurs jours, dans ses limites : un seul dépôt, pas de backend)", "Ne rien faire"],
        "recommandation": f"Installer le module {p['nom']}", "risques": ["Dépendance à l'éditeur pour les mises à jour du module"], "reversibilite": "reversible",
        "plan": ["Acheter le module chez l'éditeur", "Installer le colis signé dans le bureau", "Le configurer"], "retour_arriere": ["Désinstaller le module"], "impact_eur": 0,
        "agent_cible": "chef-de-cabinet", "tache": f"catalogue:{pack_id}", "page": None}


# ---------------------------------------------------------------- la base de la démonstration

def _il_y_a(**k) -> str:
    return (datetime.now(timezone.utc) - timedelta(**k)).isoformat(timespec="seconds")


def preparer() -> str:
    """Crée l'entreprise fictive et sa journée si la base est vide. Idempotent. Rend l'identifiant du fondateur de la démonstration."""
    from core import compta, crm, gouvernance, publication

    with db.connexion() as c:
        existant = c.une("SELECT id FROM utilisateurs WHERE email = ?", (FONDATEUR,))
        if existant:
            return existant["id"]
        org, uid, now = db.nouvel_id(), db.nouvel_id(), db.maintenant()
        c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (org, ORGANISATION, _il_y_a(days=40)))
        c.executer("INSERT INTO utilisateurs (id, org_id, email, role, cree_le, derniere_connexion) VALUES (?,?,?,?,?,?)", (uid, org, FONDATEUR, "fondateur", _il_y_a(days=40), now))

        # Une journée de travail : exécutions, outils, coûts (ce que rejoue l'aquarium)
        journee = [("chef-de-cabinet", "demande-fondateur", 9.5, 0.21, ["date_du_jour"]), ("croissance", "demande-fondateur", 8.7, 0.34, ["lire_page", "lire_page"]),
                   ("finances-clients", "demande-fondateur", 7.2, 0.12, ["point_finances", "contacts_a_traiter"]), ("batisseur", "demande-fondateur", 5.9, 0.41, ["depot_lire", "depot_proposer"]),
                   ("croissance", "demande-fondateur", 4.1, 0.29, ["lire_page"]), ("chef-de-cabinet", "demande-fondateur", 2.6, 0.18, []),
                   ("batisseur", "decision-demo", 1.4, 0.37, ["etat_cible", "sonder_domaine"]), ("finances-clients", "demande-fondateur", 0.6, 0.09, ["point_finances"])]
        for agent, tache, heures, cout, outils in journee:
            c.executer("INSERT INTO executions (id, org_id, agent, tache, statut, entree, sortie, outils, modele, tokens_entree, tokens_sortie, cout_usd, tours, cree_le, fini_le) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (db.nouvel_id(), org, agent, tache, "terminee", "(démonstration)", json.dumps({"reponse": "Travail simulé pour la démonstration."}, ensure_ascii=False),
                        json.dumps([{"outil": o, "entree": {}, "resultat": "(simulé)"} for o in outils]), "simulation", 4200, 900, cout, 1 + len(outils),
                        _il_y_a(hours=heures), _il_y_a(hours=heures - 0.05)))
        for heures, agent, texte in ((9.5, "chef-de-cabinet", "Prépare la semaine"), (8.7, "croissance", "Relève les tarifs de deux concurrents"),
                                     (5.9, "batisseur", "Corrige la page Contact"), (0.6, "finances-clients", "Fais le point du mois")):
            c.executer("INSERT INTO journal (id, org_id, acteur, action, cible, detail, cree_le) VALUES (?,?,?,?,?,?,?)",
                       (db.nouvel_id(), org, FONDATEUR, "demande", agent, texte, _il_y_a(hours=heures)))

        # Décisions : deux déjà prises, trois en attente (une par niveau de provenance)
        chef, elise, sacha = ("Camille Aubert (chef-de-cabinet), chef de cabinet", "Élise Tanguy (croissance), responsable marketing et produits",
                              "Sacha Ferrand (batisseur), software factory")
        commun = dict(options=["Faire", "Attendre"], recommandation="Faire", reversibilite="reversible")
        for objectif, etat, heures in (("Corriger la page Contact", "approuver", 5.5), ("Acheter un second nom de domaine", "refuser", 3.2)):
            did = gouvernance.ouvrir(c, org, gouvernance.Paquet(demandeur=sacha if "page" in objectif else chef, objectif=objectif, proposition="Proposition de la démonstration.",
                                                                 provenance={"pages": [], "depot": [], "refus": [], "autres": 0}, **commun))
            gouvernance.decider(c, org, did, etat, par=FONDATEUR)
            c.executer("UPDATE decisions SET cree_le = ?, decidee_le = ? WHERE id = ?", (_il_y_a(hours=heures + 0.4), _il_y_a(hours=heures), did))
        gouvernance.ouvrir(c, org, gouvernance.Paquet(
            demandeur=chef, objectif="Préparer le point mensuel pour l'expert-comptable", proposition="Rassembler le journal du mois et son export.",
            pourquoi_maintenant="Le mois se termine dans dix jours.", risques=["Aucun engagement financier"], plan=["Préparer le journal", "Vous le présenter"],
            agent_cible="finances-clients", tache="Prépare le point du mois et l'export pour l'expert-comptable.", provenance={"pages": [], "depot": [], "refus": [], "autres": 0}, **commun))
        gouvernance.ouvrir(c, org, gouvernance.Paquet(
            demandeur=elise, objectif="Ajuster notre grille après le relevé des tarifs concurrents", proposition="Proposer une formule intermédiaire, entre Essentielle et Sur mesure.",
            pourquoi_maintenant="Deux concurrents ont publié une offre intermédiaire ce mois-ci.", risques=["Positionnement à expliquer aux clients actuels"],
            plan=["Rédiger la proposition", "Vous la soumettre"], agent_cible="croissance", tache="Rédige la proposition de grille pour validation.",
            provenance={"pages": ["concurrent-un.example/tarifs", "concurrent-deux.example/offres"], "depot": [], "refus": [], "autres": 0}, **commun))
        pid = publication.enregistrer_brouillon(c, org, _PAGE_TARIFS, par=elise)
        did = gouvernance.ouvrir(c, org, gouvernance.Paquet(
            demandeur=elise, objectif="Publier « Tarifs de l'Atelier Nord » sur le site", proposition=_PAGE_TARIFS["meta_description"],
            pourquoi_maintenant="La page est prête ; elle n'est en ligne qu'après votre fusion ou votre publication.", options=["Proposer la page au site", "Garder en brouillon"],
            recommandation="Proposer la page au site", risques=["Exposition publique : relire les faits avant de fusionner"], reversibilite="reversible",
            plan=["Proposition sur le site", "Relecture et fusion par vous"], retour_arriere=["Fermer la demande"], portee="publication", agent_cible="croissance",
            tache=f"publier:{pid}", provenance={"pages": [], "depot": [], "refus": [], "autres": 0}))
        c.executer("UPDATE publications SET decision_id = ? WHERE id = ?", (did, pid))

        # Finances et contacts : de quoi lire un journal du mois et un suivi conforme
        mois = db.mois_courant()
        for i, (libelle, montant, client) in enumerate((("Escalier sur mesure, acompte", 2400.0, "Famille Morel"), ("Pose de bibliothèque", 1350.0, "Cabinet Ravel"),
                                                        ("Rénovation de volets", 890.0, "M. Tessier"))):
            compta.ajouter_vente(c, org, source="manuel", reference=f"DEMO-{i + 1:03d}", date_=f"{mois}-{4 + 6 * i:02d}", libelle=libelle, montant_eur=montant, client=client, par=FONDATEUR)
        for libelle, montant, categorie, periodicite in (("Hébergement du site", 9.0, "hebergement", "mensuelle"), ("Assurance décennale", 148.0, "prestataire", "mensuelle"),
                                                         ("Nom de domaine", 12.0, "domaine", "annuelle")):
            compta.ajouter_charge(c, org, compta.valider_charge(date_=f"{mois}-02", libelle=libelle, montant_eur=str(montant), categorie=categorie, periodicite=periodicite), par=FONDATEUR)
        for email, nom, entreprise, role, base in (("contact@cabinet-ravel.example", "Hélène Ravel", "Cabinet Ravel", "client", "contrat"),
                                                   ("paul.tessier@tessier.example", "Paul Tessier", "", "client", "contrat"),
                                                   ("achats@mairie-exemple.example", "Service achats", "Mairie d'Exemple", "prospect", "interet_legitime")):
            cid = crm.creer_contact(c, org, email=email, nom=nom, entreprise=entreprise, role=role, base_legale=base, source="démonstration", par=FONDATEUR)
            crm.ajouter_echange(c, org, cid, sens="note", canal="téléphone", resume="Échange de démonstration.", par=FONDATEUR)
        return uid


def demarrer(application) -> None:
    """Appelé au chargement du bureau quand CORE_DEMO=1 : vérifie, prépare la base, branche le scénario à la place du modèle."""
    from core.executeur import Executeur

    verifier_demarrage()
    preparer()
    application.state.executeur = Executeur(appel)

"""Lot 2 : les quatre agents sont chargés, le fondateur peut s'adresser à chacun, un paquet approuvé qui désigne un agent
et une tâche s'exécute aussitôt dans les limites du plan, un agent inconnu n'est jamais désigné."""
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import agents
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import OUTILS, Executeur

ENVOIS: list = []


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)


def _reponse(texte):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=300, output_tokens=80, cache_read_input_tokens=0))


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    client.post("/connexion", data={"email": email})
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    client.get(f"/connexion/{lien}")
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))   # jeton anti-CSRF de la session
    return client


def test_les_quatre_agents_et_leurs_bornes():
    fiches = agents.charger()
    assert set(fiches) == {"chef-de-cabinet", "croissance", "finances-clients", "batisseur"}
    for f in fiches.values():
        assert f.nom and f.fonction and f.budget_tours <= 10 and set(f.outils) <= set(OUTILS)
        assert "signes" in f.consignes      # chaque agent signe « Prénom Nom (identifiant), fonction »
    b = fiches["batisseur"].consignes
    assert "300 lignes" in b and "ne fusionnes jamais" in b and "Modifier ce bureau lui-même" in b and "le fondateur paie" in b
    assert "paiement est confirmé par la plateforme de paiement" in fiches["finances-clients"].consignes
    assert "Tu ne publies rien" in fiches["croissance"].consignes
    noms = {f.nom for f in fiches.values()}
    assert len(noms) == 4


def test_demande_a_un_agent_puis_execution_apres_approbation():
    PAQUET = ('{"decision_requise": true, "reponse": "À décider.", "objectif": "Page Tarifs", "proposition": "Trois offres", '
              '"options": ["Publier", "Attendre"], "recommandation": "Publier", "reversibilite": "reversible", "plan": ["rédiger", "mettre en ligne"], '
              '"agent_cible": "croissance", "tache": "Rédiger la page Tarifs avec trois offres en fourchettes"}')
    EXEC = '{"fait": ["brouillon rédigé"], "reste_a_faire": ["mise en ligne par le Bâtisseur"], "faits_sources": [], "reponse": "Brouillon prêt."}'
    vus = []

    def faux_appel(*, modele, system, messages, tools):
        vus.append((system.split("\n", 1)[0], messages[0]["content"]))
        return _reponse(EXEC if "Décision approuvée" in messages[0]["content"] else PAQUET)

    bureau.app.state.executeur = Executeur(faux_appel)
    c = _connecter("f@lot2-core.fr")
    assert "Élise Tanguy · responsable marketing et produits" in c.get("/bureau").text      # sélecteur d'agent
    c.post("/demande", data={"texte": "Il nous faut une page Tarifs", "agent": "croissance"})
    assert vus[0][0].startswith("Tu es Élise Tanguy (croissance)") and "croissance : responsable marketing et produits" in vus[0][1]
    page = c.get("/bureau").text
    assert "Si vous approuvez :" in page and "croissance exécute" in page
    did = re.search(r'/decisions/([0-9a-f]{32})/approuver', page).group(1)
    assert c.post(f"/decisions/{did}/approuver").headers["location"].endswith("m=approuvee")
    assert vus[1][0].startswith("Tu es Élise Tanguy (croissance)") and "Rédiger la page Tarifs" in vus[1][1] and "Plan : rédiger → mettre en ligne" in vus[1][1]
    page = c.get("/bureau").text
    assert "Brouillon prêt." in page and "execution.apres_approbation" in page and "decision-" in page


def test_agent_cible_inconnu_retombe_sur_le_demandeur():
    PAQUET = ('{"decision_requise": true, "reponse": "x", "objectif": "Acheter un domaine", "proposition": "nom.fr", "options": ["Oui", "Non"], '
              '"recommandation": "Oui", "reversibilite": "reversible", "impact_eur": 12, "agent_cible": "stagiaire", "tache": "préparer le panier"}')
    bureau.app.state.executeur = Executeur(lambda **k: _reponse(PAQUET))
    c = _connecter("g@lot2-core.fr")
    c.post("/demande", data={"texte": "Un domaine ?", "agent": "batisseur"})
    page = c.get("/bureau").text
    assert "batisseur exécute « préparer le panier »" in page and "stagiaire" not in page
    # un agent demandé qui n'existe pas : le Chef de cabinet répond
    c.post("/demande", data={"texte": "Bonjour", "agent": "inconnu"})
    assert "chef-de-cabinet" in c.get("/bureau").text

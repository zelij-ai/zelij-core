"""Paquet « construire soi-même ou installer le module » (CEO 09/10) : le Chef de cabinet connaît le catalogue, propose les deux
options quand une demande dépasse le bureau, et l'approbation de l'option module conduit au catalogue, lien d'achat prêt."""
import json
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import catalogue, db
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur

ENVOIS: list = []
RACINE = bureau.RACINE.parents[1]


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)


def _reponse(texte):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=400, output_tokens=120, cache_read_input_tokens=0))


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    client.post("/connexion", data={"email": email})
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    client.get(f"/connexion/{lien}")
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))
    return client


PAQUET_MODULE = json.dumps({
    "decision_requise": True, "reponse": "Déployer sur Google Cloud dépasse ce bureau : deux voies.",
    "objectif": "Déployer le site sur Google Cloud", "proposition": "Installer le module Infra cloud de l'éditeur plutôt que de construire la cible à la main.",
    "pourquoi_maintenant": "Le site doit être en ligne avant le salon.",
    "options": ["Installer le module Infra cloud", "Construire soi-même avec le Bâtisseur (environ quatre jours, un seul dépôt, pas de backend)", "Ne rien faire"],
    "recommandation": "Installer le module Infra cloud", "risques": ["Dépendance à l'éditeur pour les mises à jour du module"], "reversibilite": "reversible",
    "plan": ["Acheter le module", "Installer le colis signé", "Configurer le projet Google Cloud"], "retour_arriere": ["Désinstaller le module"], "impact_eur": 0,
    "agent_cible": "chef-de-cabinet", "tache": "catalogue:infra-cloud", "page": None,
}, ensure_ascii=False)


def test_le_chef_de_cabinet_recoit_le_catalogue_et_la_regle():
    texte = catalogue.pour_agent()
    assert "infra-cloud (cible)" in texte and "prospection (agent)" in texte and "zelij-cloud (pack)" in texte and "€" not in texte
    assert "construire soi-même ou installer le module" in bureau.INSTRUCTION_DEMANDE and "catalogue:<identifiant>" in bureau.INSTRUCTION_DEMANDE
    fiche = (RACINE / "agents" / "chef-de-cabinet" / "agent.md").read_text(encoding="utf-8")
    assert "construire soi-même ou installer le module" in fiche and "catalogue:<identifiant du module>" in fiche and "tu n'inventes jamais un prix" in fiche
    assert catalogue.est_pack("infra-cloud") and not catalogue.est_pack("../x")


def test_paquet_module_puis_approbation_vers_le_catalogue():
    vus: list = []

    def appel(**k):
        vus.append(k["messages"][0]["content"])
        return _reponse(PAQUET_MODULE)

    bureau.app.state.executeur = Executeur(appel)
    try:
        c = _connecter("f@catalogue-test.fr")
        r = c.post("/demande", data={"texte": "Déploie le site sur Google Cloud"})
        assert r.status_code == 303 and r.headers["location"].endswith("m=demande")
        assert "Modules disponibles chez l'éditeur" in vus[0] and "infra-cloud (cible)" in vus[0]      # le catalogue est dans la consigne
        html = c.get("/bureau").text
        assert "Déployer le site sur Google Cloud" in html and "Installer le module Infra cloud" in html and "Construire soi-même" in html
        did = re.search(r'/decisions/([0-9a-f-]+)/approuver', html).group(1)
        r = c.post(f"/decisions/{did}/approuver")
        assert r.status_code == 303 and r.headers["location"] == "/catalogue?pack=infra-cloud&m=catalogue_module"
        page = c.get("/catalogue?pack=infra-cloud&m=catalogue_module").text
        assert "pack--cible" in page and "Acheter le module chez l'éditeur" in page and "zelij.ai/core/catalogue/?pack=infra-cloud&amp;instance=" in page
        assert "son lien est prêt ci-dessous" in page
        with db.connexion() as conn:
            uid = cx.lire_session(c.cookies[cx.COOKIE])
            org = conn.une("SELECT org_id FROM utilisateurs WHERE id = ?", (uid,))["org_id"]
            journal = conn.lignes("SELECT action, detail FROM journal WHERE org_id = ? AND action = 'catalogue.module'", (org,))
            assert journal and "infra-cloud" in journal[0]["detail"]
            assert conn.une("SELECT etat FROM decisions WHERE id = ?", (did,))["etat"] == "approuvee"
        # un identifiant de module inconnu ne casse rien : catalogue sans mise en avant
        assert "pack--cible" not in c.get("/catalogue?pack=inconnu").text
    finally:
        bureau.app.state.executeur = Executeur()


def test_option_construire_designe_le_batisseur():
    paquet = json.loads(PAQUET_MODULE)
    paquet.update({"recommandation": paquet["options"][1], "proposition": "Construire la cible avec le Bâtisseur, en quatre demandes de fusion.",
                   "agent_cible": "batisseur", "tache": "Préparer la cible de déploiement en quatre demandes de fusion, 300 lignes chacune au plus."})
    bureau.app.state.executeur = Executeur(lambda **k: _reponse(json.dumps(paquet, ensure_ascii=False)))
    try:
        c = _connecter("g@catalogue-test.fr")
        c.post("/demande", data={"texte": "Déploie le site sur Google Cloud, je préfère construire"})
        html = c.get("/bureau").text
        assert "batisseur exécute" in html and "quatre demandes de fusion" in html
    finally:
        bureau.app.state.executeur = Executeur()

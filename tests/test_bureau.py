"""Le bureau de bout en bout : connexion par lien, demande au Chef de cabinet (modèle simulé), paquet ouvert, décision avec
consigne obligatoire, isolation entre organisations, plafond."""
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur

ENVOIS: list[tuple[str, str, str]] = []


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)


def _reponse(texte):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=500, output_tokens=100, cache_read_input_tokens=0))


PAQUET = ('{"decision_requise": true, "reponse": "Je vous propose de trancher.", "objectif": "Ouvrir une page Tarifs", '
          '"proposition": "Trois offres, prix affichés", "pourquoi_maintenant": "deux prospects ont demandé", '
          '"options": ["Publier", "Attendre", "Ne rien faire"], "recommandation": "Publier", "risques": ["prix figés"], '
          '"reversibilite": "reversible", "plan": ["rédiger", "mettre en ligne"], "retour_arriere": ["retirer la page"], "impact_eur": 0}')
SIMPLE = '{"decision_requise": false, "reponse": "Rien à décider : la page existe déjà, je l\'ai vérifié."}'


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    assert client.post("/connexion", data={"email": email}).headers["location"].endswith("m=lien")
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    r = client.get(f"/connexion/{lien}")
    assert r.status_code == 303 and r.headers["location"] == "/bureau" and cx.COOKIE in client.cookies
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))   # jeton anti-CSRF de la session
    return client


def test_sante_et_acces():
    c = TestClient(bureau.app, follow_redirects=False)
    assert c.get("/healthz").json()["ok"] is True
    assert c.get("/bureau").status_code == 303 and c.get("/").headers["location"] == "/connexion"
    assert c.get("/connexion/faux").headers["location"].endswith("m=lien_invalide")


def test_demande_paquet_et_decision_avec_consigne(monkeypatch):
    reponses = iter([_reponse(PAQUET), _reponse(SIMPLE)])
    bureau.app.state.executeur = Executeur(lambda **k: next(reponses))
    c = _connecter("fondateur@exemple-core.fr")
    page = c.get("/bureau").text
    assert "Rien n'attend votre décision" in page and "Camille Aubert" in page
    assert c.post("/demande", data={"texte": " "}).headers["location"].endswith("m=vide")
    assert c.post("/demande", data={"texte": "Faut-il ouvrir une page Tarifs ?"}).headers["location"].endswith("m=demande")
    page = c.get("/bureau").text
    assert "Ouvrir une page Tarifs" in page and "Trois offres" in page and 'name="consigne"' in page and "required" in page
    did = re.search(r'/decisions/([0-9a-f]{32})/a_modifier', page).group(1)
    assert c.post(f"/decisions/{did}/a_modifier", data={"consigne": ""}).headers["location"].endswith("m=consigne")
    assert c.post(f"/decisions/{did}/a_modifier", data={"consigne": "sans prix affichés"}).headers["location"].endswith("m=a_modifier")
    assert c.post(f"/decisions/{did}/approuver").headers["location"].endswith("m=deja")
    page = c.get("/bureau").text
    assert "sans prix affichés" in page and "À modifier" in page and "0.00" in page   # consigne visible, coût du mois affiché
    # une demande qui n'engage rien : réponse directe, aucun paquet
    c.post("/demande", data={"texte": "La page existe-t-elle ?"})
    page = c.get("/bureau").text
    assert "Rien à décider" in page and "Rien n'attend votre décision" in page
    assert "decision.a_modifier" in page and "demande" in page   # journal


def test_isolation_entre_organisations_et_origine():
    bureau.app.state.executeur = Executeur(lambda **k: _reponse(PAQUET))
    a = _connecter("a@alpha-core.fr")
    b = _connecter("b@beta-core.fr")
    a.post("/demande", data={"texte": "Décision Alpha"})
    did = re.search(r'/decisions/([0-9a-f]{32})/approuver', a.get("/bureau").text).group(1)
    assert "Ouvrir une page Tarifs" not in b.get("/bureau").text
    assert b.post(f"/decisions/{did}/approuver").status_code == 404
    a.headers["origin"] = "https://ailleurs.example"
    assert a.post(f"/decisions/{did}/approuver").status_code == 403


def test_plafond_bloque_la_demande(monkeypatch):
    monkeypatch.setenv("PLAFOND_MENSUEL_EUR", "0")
    appels = []
    bureau.app.state.executeur = Executeur(lambda **k: appels.append(1))
    c = _connecter("p@plafond-core.fr")
    assert c.post("/demande", data={"texte": "Bonjour"}).headers["location"].endswith("m=plafond") and appels == []
    assert "disabled" in c.get("/bureau").text

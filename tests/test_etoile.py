"""Encart « Une étoile pour Zelij Core » (0.9.1) : lecture anonyme et non bloquante du nombre d'étoiles, repli silencieux,
retrait complet par ETOILES_GITHUB=0, présence dans le gabarit de base avec sa croix de fermeture."""
import time

import httpx
from fastapi.testclient import TestClient

from core import etoiles
from core.bureau import app as bureau


def _client(reponse):
    def handler(request):
        assert request.url.host == "api.github.com" and "Authorization" not in request.headers     # anonyme, rien d'autre
        return reponse
    return httpx.Client(transport=httpx.MockTransport(handler))


def _vider():
    etoiles._cache.update(t=0.0, n=None, en_cours=False)


def test_lecture_et_repli_silencieux():
    _vider()
    assert etoiles.lire(_client(httpx.Response(200, json={"stargazers_count": 36412}))) == 36412
    assert etoiles.compte() == 36412                                            # en cache, pas de nouvelle lecture
    _vider()
    assert etoiles.lire(_client(httpx.Response(403, json={"message": "rate limit"}))) is None
    assert etoiles.lire(_client(httpx.Response(200, text="pas du json"))) is None


def test_compte_ne_bloque_jamais_et_n_insiste_pas_apres_un_echec():
    _vider()
    lent = _client(httpx.Response(200, json={"stargazers_count": 7}))
    assert etoiles.compte(lent) is None                                        # première demande : lecture lancée en arrière-plan
    for _ in range(50):
        if etoiles._cache["n"] == 7:
            break
        time.sleep(0.05)
    assert etoiles.compte() == 7
    _vider()
    etoiles._cache.update(t=time.time(), n=None)                                # échec tout frais
    assert etoiles.compte(lent) is None and etoiles._cache["en_cours"] is False   # pas de relance avant dix minutes


def test_libelle_court():
    assert etoiles.court(None) == "" and etoiles.court(980) == "980"
    assert etoiles.court(1240) == "1,2 k" and etoiles.court(1000) == "1 k" and etoiles.court(36412) == "36 k"


def test_encart_present_dans_le_bureau_et_retire_par_reglage(monkeypatch):
    _vider()
    etoiles._cache.update(t=time.time(), n=36412)
    c = TestClient(bureau.app, follow_redirects=False)
    html = c.get("/connexion").text
    assert 'id="etoile"' in html and "zelij-ai/zelij-core" in html and "36 k" in html and "data-etoile-fermer" in html
    assert 'rel="noopener"' in html and "api.github.com" not in html             # le navigateur ne lit rien lui-même
    monkeypatch.setenv("ETOILES_GITHUB", "0")
    assert 'id="etoile"' not in c.get("/connexion").text

"""Décider en swipant (0.9.3) : page réservée au fondateur, une carte par décision en attente, confirmation obligatoire,
case « j'ai lu » au-delà du seuil ou si irréversible ; la décision part par la route du bureau."""
from pathlib import Path

from fastapi.testclient import TestClient

import pytest

from core.bureau import app as bureau
from core.bureau import connexion as cx
from tests.test_bureau import ENVOIS, _connecter


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)

ROOT = Path(__file__).resolve().parents[1]


def _fausses(*cartes):
    base = {"id": "d-1", "objectif": "Acheter un domaine", "demandeur": "Camille Aubert (chef-de-cabinet)", "proposition": "Le domaine exemple.fr pour 12 mois",
            "pourquoi_maintenant": "Le salon est en novembre", "options": ["A", "B"], "recommandation": "A", "risques": ["aucun"], "reversibilite": "reversible",
            "impact_eur": 14.9, "plan": ["acheter"], "retour_arriere": ["laisser expirer"], "cree_le": "2026-10-20T09:00:00"}
    return [dict(base, **c) for c in cartes]


def test_reserve_au_fondateur_et_carte_par_decision(monkeypatch):
    anonyme = TestClient(bureau.app, follow_redirects=False)
    assert anonyme.get("/decider").status_code == 303 and anonyme.get("/decider").headers["location"] == "/connexion"
    c = _connecter("fondateur-swipe@exemple.test")
    monkeypatch.setattr(bureau.gouvernance, "en_attente", lambda conn, org: _fausses({"id": "d-1"}, {"id": "d-2", "reversibilite": "irreversible", "objectif": "Supprimer le site"}, {"id": "d-3", "impact_eur": 450}))
    html = c.get("/decider").text
    assert 'id="decider"' in html and 'data-csrf="' in html and html.count('class="sw-carte"') == 3
    assert 'data-id="d-1" data-objectif="Acheter un domaine" data-lecture="0"' in html
    assert 'data-id="d-2"' in html and 'data-lecture="1"' in html.split('data-id="d-2"')[1][:120]        # irréversible : case « j'ai lu »
    assert 'data-lecture="1"' in html.split('data-id="d-3"')[1][:120]                                     # 450 € ≥ seuil 200
    assert 'dialog id="sw-feuille"' in html and 'name="_csrf"' in html and "data-sw-lu" in html and 'name="consigne"' in html
    assert "/static/decider.js" in html and "3 à trancher" in html


def test_page_vide_et_bouton_du_bureau(monkeypatch):
    c = _connecter("fondateur-swipe2@exemple.test")
    monkeypatch.setattr(bureau.gouvernance, "en_attente", lambda conn, org: [])
    html = c.get("/decider").text
    assert "Rien à trancher" in html and 'class="sw-carte"' not in html
    bureau_html = (ROOT / "core/bureau/templates/bureau.html").read_text(encoding="utf-8")
    assert 'href="/decider">Décider en swipant' in bureau_html and "{% if en_attente %}" in bureau_html.split("Décider en swipant")[0][-200:]


def test_le_geste_passe_par_la_route_du_bureau_et_confirme_toujours():
    js = (ROOT / "core/bureau/static/decider.js").read_text(encoding="utf-8")
    assert "'/decisions/' + id + '/' + action" in js and "feuille.showModal()" in js and "formulaire.setAttribute('action'" in js
    assert "fetch(" not in js                                                                            # un POST de formulaire, jamais un appel caché
    for geste in ("ArrowRight", "ArrowLeft", "ArrowUp", "pointerdown", "pointerup"):
        assert geste in js
    css = (ROOT / "core/bureau/static/app.css").read_text(encoding="utf-8")
    assert ".sw-pile" in css and ".sw-feuille" in css and "prefers-reduced-motion" in css
    from core import VERSION

    assert tuple(int(x) for x in VERSION.split(".")) >= (0, 9, 3)
    assert "## 0.9.3" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") and "En swipant" in (ROOT / "docs/MODE-D-EMPLOI.md").read_text(encoding="utf-8")

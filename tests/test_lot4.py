"""Lot 4 : publication (PR GitHub ou brouillon WordPress, jamais une mise en ligne directe), aquarium et page publique,
catalogue et installation d'un module signé, chaîne page → brouillon → décision → publication sur approbation."""
import json
import re
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from core import aquarium, db, modules, publication
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur
from core.schema import migrer

ENVOIS: list = []
PAGE = {"title": "Combien coûte un site vitrine ?", "meta_description": "Ce qu'il faut budgéter, poste par poste, avec les sources.", "h1": "Combien coûte un site vitrine ?",
        "intro": "La question revient à chaque premier rendez-vous.", "sections": [{"h2": "Le nom de domaine", "texte": "Entre 8 et 15 € par an.\nRenouvelé chaque année."}],
        "faq": [{"q": "Et l'hébergement ?", "a": "Quelques euros par mois."}], "sources": [{"title": "Tarifs publics", "url": "https://exemple.fr/tarifs"}]}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    for k in ("SITE_DEPOT", "GITHUB_TOKEN", "WP_URL", "WP_USER", "WP_APP_PASSWORD", "ZELIJ_CLE_PUBLIQUE"):
        monkeypatch.delenv(k, raising=False)


def _org(c, nom="Lot4 SAS"):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, nom, db.maintenant()))
    return oid


# ---------------------------------------------------------------- publication

def test_rendu_echappe_et_gabarit():
    corps = publication.rendre_corps({**PAGE, "sections": [{"h2": "<b>x</b>", "texte": "<script>alert(1)</script>"}]})
    assert "<script>" not in corps and "&lt;script&gt;" in corps and "Faits vérifiés le" in corps
    html = publication.rendre_page(None, PAGE, url="https://exemple.fr/blog/combien-coute-un-site-vitrine/")
    assert html.startswith("<!doctype html>") and "<title>Combien coûte un site vitrine ?</title>" in html and 'rel="canonical"' in html
    gabarit = "<html><head><title>{{titre}} · Mon site</title></head><body><h1>{{h1}}</h1>{{corps}}<p>{{date}}</p></body></html>"
    rendu = publication.rendre_page(gabarit, PAGE, url="/x/")
    assert rendu.startswith("<html>") and "· Mon site" in rendu and "Le nom de domaine" in rendu
    assert publication.slug_sur("Combien coûte un site vitrine ?") == "combien-coute-un-site-vitrine"


def test_configuration_depuis_l_environnement(monkeypatch):
    assert publication.configuration() is None
    monkeypatch.setenv("WP_URL", "https://blog.exemple.fr/")
    monkeypatch.setenv("WP_USER", "agent")
    monkeypatch.setenv("WP_APP_PASSWORD", "abcd")
    assert publication.configuration()["canal"] == "wordpress" and publication.configuration()["url"] == "https://blog.exemple.fr"
    monkeypatch.setenv("SITE_DEPOT", "fondateur/site")
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    monkeypatch.setenv("SITE_PREFIXE", "/blog/")
    conf = publication.configuration()
    assert conf["canal"] == "pr" and conf["prefixe"] == "/blog"        # le dépôt prime quand les deux existent


def test_publier_par_pr_ouvre_une_demande_sans_fusionner(monkeypatch):
    migrer()
    monkeypatch.setenv("SITE_DEPOT", "fondateur/site")
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    monkeypatch.setenv("SITE_PREFIXE", "/blog/")
    monkeypatch.setenv("SITE_DOMAINE", "https://exemple.fr")
    appels = []

    def handler(req: httpx.Request) -> httpx.Response:
        appels.append((req.method, req.url.path, json.loads(req.content) if req.content else None))
        if req.url.path == "/repos/fondateur/site":
            return httpx.Response(200, json={"default_branch": "main"})
        if req.url.path.endswith("/git/ref/heads/main"):
            return httpx.Response(200, json={"object": {"sha": "abc123"}})
        if "/contents/_gabarit/page.html" in req.url.path:
            return httpx.Response(404, json={})
        if req.url.path.endswith("/git/refs"):
            return httpx.Response(201, json={})
        if "/contents/blog/" in req.url.path and req.method == "PUT":
            return httpx.Response(201, json={})
        if req.url.path.endswith("/pulls"):
            return httpx.Response(201, json={"number": 7, "html_url": "https://github.com/fondateur/site/pull/7"})
        return httpx.Response(500, json={})

    with db.connexion() as c:
        oid = _org(c)
        pid = publication.enregistrer_brouillon(c, oid, PAGE, par="Élise Tanguy (croissance), responsable de la croissance")
        res = publication.publier(c, oid, pid, par="fondateur", client=httpx.Client(transport=httpx.MockTransport(handler)))
        assert res["ok"] and res["url"].endswith("/pull/7")
        pub = publication.lire(c, oid, pid)
        assert pub["etat"] == "proposee" and pub["canal"] == "pr" and pub["reference"].endswith("/pull/7") and pub["publie_le"]
        methodes = [(m, p) for m, p, _ in appels]
        assert ("POST", "/repos/fondateur/site/git/refs") in methodes and ("POST", "/repos/fondateur/site/pulls") in methodes
        assert not any(p.endswith("/merge") for _, p in methodes)                # jamais de fusion
        put = next(a for a in appels if a[0] == "PUT")
        assert put[1] == "/repos/fondateur/site/contents/blog/combien-coute-un-site-vitrine/index.html" and put[2]["branch"].startswith("agents/combien-coute")
        # sans canal : échec propre, journalisé
        monkeypatch.delenv("SITE_DEPOT")
        monkeypatch.delenv("GITHUB_TOKEN")
        pid2 = publication.enregistrer_brouillon(c, oid, PAGE, par="x")
        res = publication.publier(c, oid, pid2, par="fondateur")
        assert not res["ok"] and "aucun canal" in res["detail"] and publication.lire(c, oid, pid2)["etat"] == "echec"


def test_publier_wordpress_cree_un_brouillon(monkeypatch):
    migrer()
    monkeypatch.setenv("WP_URL", "https://blog.exemple.fr")
    monkeypatch.setenv("WP_USER", "agent")
    monkeypatch.setenv("WP_APP_PASSWORD", "abcd efgh")
    vus = []

    def handler(req: httpx.Request) -> httpx.Response:
        vus.append((req.url.path, json.loads(req.content), req.headers.get("authorization", "")[:6]))
        return httpx.Response(201, json={"id": 55, "link": "https://blog.exemple.fr/?p=55"})

    with db.connexion() as c:
        oid = _org(c, "WP SAS")
        pid = publication.enregistrer_brouillon(c, oid, PAGE, par="x")
        res = publication.publier(c, oid, pid, par="fondateur", client=httpx.Client(transport=httpx.MockTransport(handler)))
        assert res["ok"] and vus[0][0] == "/wp-json/wp/v2/posts" and vus[0][1]["status"] == "draft" and vus[0][2] == "Basic "
        assert publication.lire(c, oid, pid)["canal"] == "wordpress"


# ---------------------------------------------------------------- aquarium et vitrine

def test_etat_de_l_aquarium_et_jeton_public():
    migrer()
    from core import agents

    with db.connexion() as c:
        oid = _org(c, "Aqua SAS")
        c.executer("INSERT INTO executions (id, org_id, agent, tache, statut, outils, cout_usd, tours, cree_le) VALUES (?,?,?,?,?,?,?,?,?)",
                   (db.nouvel_id(), oid, "croissance", "demande-fondateur", "terminee", json.dumps([{"outil": "lire_page", "entree": {"url": "https://secret.example/x"}}]), 0.5, 2, db.maintenant()))
        c.executer("INSERT INTO journal (id, org_id, acteur, action, cible, detail, cree_le) VALUES (?,?,?,?,?,?,?)",
                   (db.nouvel_id(), oid, "f@aqua.fr", "demande", "croissance", "Rédige une page sur les tarifs secrets", db.maintenant()))
        e = aquarium.etat(c, oid, agents.charger())
        crois = next(a for a in e["agents"] if a["id"] == "croissance")
        assert crois["actif"] and crois["activite"] == 1 and crois["couloir"] == "croissance" and e["executions"] == 1
        assert [p["id"] for p in e["postes_libres"]] == ["prospection", "seo-geo", "veille-prix", "surveillance"]
        assert [k["id"] for k in e["couloirs"]] == ["direction", "croissance", "finances", "batir", "libres"] and e["fondateur"]["id"] == "fondateur"
        types = [x["type"] for x in e["evenements"]]
        assert "execution" in types and "outil" in types and "echange" in types
        echange = next(x for x in e["evenements"] if x["type"] == "echange")
        assert echange["acteur"] == "fondateur" and echange["cible"] == "croissance" and "tarifs secrets" in echange["texte"]
        pub = aquarium.etat(c, oid, agents.charger(), public=True)
        assert "outil" not in [x["type"] for x in pub["evenements"]] and "secret.example" not in json.dumps(pub) and "tarifs secrets" not in json.dumps(pub)
        assert aquarium.jeton_public(c, oid) is None
        j = aquarium.ouvrir_vitrine(c, oid, par="f")
        assert aquarium.organisation_par_jeton(c, j)["nom"] == "Aqua SAS" and aquarium.organisation_par_jeton(c, "court") is None
        aquarium.fermer_vitrine(c, oid, par="f")
        assert aquarium.organisation_par_jeton(c, j) is None


# ---------------------------------------------------------------- bureau de bout en bout

def _reponse(texte):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=300, output_tokens=80, cache_read_input_tokens=0))


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    client.post("/connexion", data={"email": email})
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    client.post(f"/connexion/{lien}")
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))   # jeton anti-CSRF de la session
    return client


def test_page_redigee_devient_decision_puis_publication(monkeypatch):
    sortie = json.dumps({"decision_requise": False, "reponse": "Voici la page.", "page": PAGE}, ensure_ascii=False)
    bureau.app.state.executeur = Executeur(lambda **k: _reponse(sortie))
    publies = []
    monkeypatch.setattr(publication, "publier", lambda c, org_id, pid, *, par, client=None: publies.append((pid, par)) or {"ok": True, "url": "https://x/pull/1", "detail": "demande n° 1"})
    c = _connecter("f@pub-core.fr")
    c.post("/demande", data={"texte": "Rédige une page sur le coût d'un site vitrine", "agent": "croissance"})
    page = c.get("/bureau").text
    assert "Publier « Combien coûte un site vitrine ? » sur le site" in page and "croissance exécute « publier:" in page
    pubs = c.get("/publications").text
    assert "Combien coûte un site vitrine ?" in pubs and "Brouillon" in pubs and "Aucun canal configuré" in pubs
    did = re.search(r'/decisions/([0-9a-f]{32})/approuver', page).group(1)
    assert c.post(f"/decisions/{did}/approuver").headers["location"].endswith("m=approuvee")
    assert len(publies) == 1 and publies[0][1] == "f@pub-core.fr"
    assert "publication.apres_approbation" in c.get("/bureau").text


def test_aquarium_vitrine_catalogue_et_module_signe(monkeypatch):
    priv, pub = modules.generer_cles()
    monkeypatch.setenv("ZELIJ_CLE_PUBLIQUE", pub)
    c = _connecter("f@aqua-core.fr")
    page = c.get("/aquarium").text
    assert 'id="aquarium"' in page and 'id="aq-horloge"' in page and "Créer la page publique" in page and "Prospection" in page
    # 12/10 : les quatre agents de l'édition arrivent avec un portrait fictif (agents/<id>/portrait.webp) ; un identifiant inconnu : 404.
    rp = c.get("/agents/croissance/portrait")
    assert rp.status_code == 200 and rp.headers["content-type"] == "image/webp" and rp.content[:4] == b"RIFF"
    assert c.get("/agents/inconnu/portrait").status_code == 404 and c.get("/agents/../x/portrait").status_code in (404, 400)
    assert c.get("/api/aquarium").json()["postes_libres"][0]["id"] == "prospection"
    assert c.post("/vitrine/ouvrir").headers["location"].endswith("m=vitrine")
    page = c.get("/aquarium").text
    jeton = re.search(r"/vitrine/([A-Za-z0-9_-]{16,})", page).group(1)
    anonyme = TestClient(bureau.app, follow_redirects=False)
    vitrine = anonyme.get(f"/vitrine/{jeton}")
    assert vitrine.status_code == 200 and "by zelij.ai" in vitrine.text and "Se déconnecter" not in vitrine.text and "aqua-core.fr" in vitrine.text
    assert anonyme.get(f"/api/vitrine/{jeton}").json()["public"] is True and anonyme.get("/vitrine/inconnu-inconnu-inconnu").status_code == 404
    assert anonyme.get("/api/aquarium").status_code == 401
    c.post("/vitrine/fermer")
    assert anonyme.get(f"/vitrine/{jeton}").status_code == 404
    cat = c.get("/catalogue").text
    assert "Infra cloud" in cat and "zelij.ai/core/catalogue/?pack=infra-cloud&amp;instance=" in cat and "Aucun module installé" in cat
    m = modules.Manifeste(nom="pack-prospection", version="1.0.0", type="pack", interface="1.0", fournisseur="zelij.ai")
    brut = json.dumps({"nom": m.nom, "version": m.version, "type": m.type, "interface": m.interface, "fournisseur": m.fournisseur, "description": "", "signature": "00"}).encode()
    assert c.post("/modules/installer", files={"manifeste": ("pack.json", brut, "application/json")}).headers["location"].endswith("m=module_refus")
    m.signature = modules.signer(m, priv)
    brut = json.dumps({"nom": m.nom, "version": m.version, "type": m.type, "interface": m.interface, "fournisseur": m.fournisseur, "description": "", "signature": m.signature}).encode()
    assert c.post("/modules/installer", files={"manifeste": ("pack.json", brut, "application/json")}).headers["location"].endswith("m=module")
    assert "pack-prospection" in c.get("/catalogue").text and "pack-prospection" in c.get("/bureau").text
    assert c.post("/modules/installer", files={"manifeste": ("pack.json", b"{pas du json", "application/json")}).headers["location"].endswith("m=manifeste")

"""Mode démonstration (0.8.0) : un bureau déjà rempli, des agents simulés, aucune clé. Et trois garde-fous pour qu'il ne
s'active jamais sur une vraie installation : pas en production, pas sur PostgreSQL, pas sur une base qui porte une organisation réelle."""
import html
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import db, demo, passerelle
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur

RACINE = Path(__file__).resolve().parents[1]
TABLES = ("jetons_connexion", "utilisateurs", "executions", "decisions", "journal", "modules", "ventes", "charges", "contacts", "echanges", "droits",
          "publications", "organisations")


def _vider():
    with db.connexion() as c:
        for t in TABLES:
            c.executer(f"DELETE FROM {t}")


@pytest.fixture
def demonstration(monkeypatch):
    """Base vide, CORE_DEMO=1, le scénario à la place du modèle ; tout est remis en état après le test."""
    _vider()
    monkeypatch.setenv("CORE_DEMO", "1")
    monkeypatch.delenv("CORE_ENV", raising=False)
    monkeypatch.setattr(cx, "UNE_SEULE_ORGANISATION", True)
    appels_reels: list = []
    monkeypatch.setattr(passerelle, "appeler", lambda **k: appels_reels.append(k))          # tout appel au vrai modèle serait une faute
    envois: list = []
    monkeypatch.setattr(cx, "envoyer_mail", lambda *a: envois.append(a) or True)
    demo.demarrer(bureau.app)
    yield {"appels_reels": appels_reels, "envois": envois}
    bureau.app.state.executeur = Executeur()
    _vider()


def _entrer():
    c = TestClient(bureau.app, follow_redirects=False)
    r = c.post("/demo/entrer")
    assert r.status_code == 303 and r.headers["location"] == "/bureau" and cx.COOKIE in c.cookies
    c.headers["origin"] = "http://testserver"
    c.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(c.cookies[cx.COOKIE]))
    return c


# ---------------------------------------------------------------- le parcours du visiteur

def test_un_bureau_deja_rempli_sans_cle_ni_email(demonstration):
    anonyme = TestClient(bureau.app, follow_redirects=False)
    page = anonyme.get("/connexion").text
    assert "Entrer dans la démonstration" in page and 'action="/demo/entrer"' in page and 'name="email"' not in page and "Démonstration." in page
    assert anonyme.post("/connexion", data={"email": "quelqu-un@ailleurs.example"}).headers["location"] == "/connexion" and not demonstration["envois"]
    c = _entrer()
    bureau_html = c.get("/bureau").text
    assert "Atelier Nord · démo" in bureau_html and "bandeau-demo" in bureau_html and "agents simulés" in bureau_html
    assert bureau_html.count('class="decision"') == 3 and "À essayer dans la démonstration" in bureau_html
    for niveau in ("provenance--interne", "provenance--externe"):
        assert niveau in bureau_html
    finances = c.get("/finances").text
    assert "Escalier sur mesure" in finances and "Assurance décennale" in finances and "bandeau-demo" in finances
    assert "Cabinet Ravel" in c.get("/contacts").text and "Tarifs de l'Atelier Nord" in html.unescape(c.get("/publications").text)
    etat = c.get("/api/aquarium").json()
    assert etat["executions"] == 8 and len(etat["evenements"]) > 15 and {a["id"] for a in etat["agents"] if a["activite"]} == {"chef-de-cabinet", "croissance", "finances-clients", "batisseur"}


def test_les_agents_simules_repondent_et_les_decisions_se_prennent(demonstration):
    c = _entrer()
    assert c.post("/demande", data={"texte": "Bonjour, que sais-tu faire ?"}).headers["location"].endswith("m=demande")
    assert "Je suis un agent simulé" in c.get("/bureau").text
    c.post("/demande", data={"texte": "Déploie le site sur Google Cloud"})
    page = c.get("/bureau").text
    assert "Déployer le site sur un grand cloud" in page and "Installer le module Infra cloud" in page and "Construire soi-même" in page
    did = re.findall(r'/decisions/([0-9a-f-]+)/approuver', page)[-1]
    assert c.post(f"/decisions/{did}/approuver").headers["location"] == "/catalogue?pack=infra-cloud&m=catalogue_module"
    c.post("/demande", data={"texte": "Rédige une page Tarifs pour notre site", "agent": "croissance"})
    assert html.unescape(c.get("/bureau").text).count("Publier « Tarifs de l'Atelier Nord » sur le site") >= 2
    # approuver une décision confiée à un agent : compte rendu simulé, sans rien d'engagé
    with db.connexion() as conn:
        point = conn.une("SELECT id FROM decisions WHERE objectif LIKE 'Préparer le point mensuel%'")["id"]
    assert c.post(f"/decisions/{point}/approuver").headers["location"].endswith("m=approuvee")
    assert "Compte rendu simulé" in c.get("/bureau").text
    assert demonstration["appels_reels"] == [] and demonstration["envois"] == []            # ni modèle, ni e-mail
    with db.connexion() as conn:
        assert {e["modele"] for e in conn.lignes("SELECT modele FROM executions WHERE tache <> 'demande-fondateur' OR modele <> 'simulation'")} <= {"claude-opus-5-5", "simulation"}


def test_le_scenario_ne_fait_aucun_appel_d_outil():
    for demande in ("Rédige une page", "Déploie sur AWS", "Fais le point du mois", "Autre chose", ""):
        r = demo.appel(modele="x", system="Tu es Camille Aubert (chef-de-cabinet), chef de cabinet.", messages=[{"role": "user", "content": f"Demande du fondateur :\n«{demande}»"}], tools=[])
        assert r.stop_reason == "end_turn" and all(b.type == "text" for b in r.content)
    assert demo._agent("Tu es Sacha Ferrand (batisseur), software factory.\n\nconsignes") == "batisseur"


def test_page_publique_porte_le_bandeau(demonstration):
    c = _entrer()
    c.post("/vitrine/ouvrir")
    jeton = re.search(r'/vitrine/([A-Za-z0-9_-]{16,})', c.get("/aquarium").text).group(1)
    assert "bandeau-demo" in TestClient(bureau.app).get(f"/vitrine/{jeton}").text


# ---------------------------------------------------------------- jamais sur une vraie installation

def test_hors_demonstration_rien_n_existe(monkeypatch):
    monkeypatch.delenv("CORE_DEMO", raising=False)
    c = TestClient(bureau.app, follow_redirects=False)
    assert c.post("/demo/entrer").status_code == 404 and cx.COOKIE not in c.cookies
    page = c.get("/connexion").text
    assert "bandeau-demo" not in page and "Entrer dans la démonstration" not in page and 'name="email"' in page
    assert not demo.actif()
    monkeypatch.setenv("CORE_DEMO", "oui")                   # seule la valeur exacte « 1 » l'active
    assert not demo.actif()


def test_refus_en_production(monkeypatch):
    _vider()
    monkeypatch.setenv("CORE_DEMO", "1")
    monkeypatch.setenv("CORE_ENV", "production")
    with pytest.raises(RuntimeError, match="production"):
        demo.demarrer(bureau.app)
    with db.connexion() as c:
        assert not c.lignes("SELECT id FROM organisations")


def test_refus_sur_postgresql(monkeypatch):
    monkeypatch.setenv("CORE_DEMO", "1")
    monkeypatch.delenv("CORE_ENV", raising=False)
    monkeypatch.setattr(db, "url", lambda: "postgresql://core:x@core-db:5432/core")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        demo.verifier_demarrage()


def test_refus_sur_une_base_qui_porte_une_organisation_reelle(monkeypatch):
    _vider()
    with db.connexion() as c:
        c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (db.nouvel_id(), "Vraie Entreprise SAS", db.maintenant()))
    monkeypatch.setenv("CORE_DEMO", "1")
    monkeypatch.delenv("CORE_ENV", raising=False)
    try:
        with pytest.raises(RuntimeError, match="organisation réelle"):
            demo.demarrer(bureau.app)
        with db.connexion() as c:
            assert [o["nom"] for o in c.lignes("SELECT nom FROM organisations")] == ["Vraie Entreprise SAS"]      # rien n'a été ajouté
    finally:
        _vider()


def test_fichier_compose_de_demonstration():
    compose = (RACINE / "docker-compose.demo.yml").read_text(encoding="utf-8")
    assert 'CORE_DEMO: "1"' in compose and "sqlite:////tmp/demo.sqlite" in compose and '"127.0.0.1:8000:8000"' in compose
    assert "env_file" not in compose and "ANTHROPIC" not in compose and "volumes:" not in compose and "CORE_ENV: demo" in compose      # ni secret, ni donnée durable
    assert "CORE_DEMO" not in (RACINE / "docker-compose.yml").read_text(encoding="utf-8") and "CORE_DEMO" not in (RACINE / ".env.example").read_text(encoding="utf-8")
    for guide in ("README.md", "README.en.md", "docs/INSTALLATION.md", "docs/INSTALLATION.en.md"):
        assert "docker-compose.demo.yml" in (RACINE / guide).read_text(encoding="utf-8"), guide


# ---------------------------------------------------------------- la suite proposée au visiteur

@pytest.mark.parametrize("demande,module,nom", [
    ("Trouve-moi des prospects dans ma région", "prospection", "Prospection"), ("Améliore notre référencement", "seo-geo", "SEO et GEO"),
    ("Mets en place une veille des tarifs", "veille-prix", "Veille des prix"), ("Surveille le certificat du site", "surveillance", "Surveillance"),
    ("Peux-tu héberger le bureau pour nous ?", "zelij-cloud", "Zelij Cloud")])
def test_une_demande_qui_depasse_l_edition_gratuite_propose_le_module(demonstration, demande, module, nom):
    c = _entrer()
    c.post("/demande", data={"texte": demande})
    page = c.get("/bureau").text
    assert f"Installer le module {nom}" in page and "Construire soi-même" in page and "Ne rien faire" in page      # trois options réelles, pas une vente forcée
    did = re.findall(r'/decisions/([0-9a-f-]+)/approuver', page)[-1]
    assert c.post(f"/decisions/{did}/approuver").headers["location"] == f"/catalogue?pack={module}&m=catalogue_module"
    catalogue = c.get(f"/catalogue?pack={module}").text
    assert "pack--cible" in catalogue and "zelij.ai/core/catalogue/?pack=" + module in catalogue and "€" not in catalogue          # aucun prix dans le bureau


def test_apres_la_demonstration_deux_voies(demonstration):
    c = _entrer()
    assert 'href="/catalogue#apres">Et après ?</a>' in c.get("/bureau").text
    catalogue = c.get("/catalogue").text
    assert 'id="apres"' in catalogue and "Installer Zelij Core chez vous" in catalogue and "Gratuit, pour toujours" in catalogue
    assert "docs/INSTALLATION.md" in catalogue and 'href="#pack-zelij-cloud"' in catalogue and 'id="pack-zelij-cloud"' in catalogue
    aquarium = c.get("/aquarium").text
    assert "la journée est simulée" in aquarium and 'data-mention="journée simulée' in aquarium
    assert "Et après ?" not in TestClient(bureau.app).get("/connexion").text                # pas de lien vers une page fermée avant d'être entré


def test_hors_demonstration_ni_bloc_ni_mention(monkeypatch):
    monkeypatch.delenv("CORE_DEMO", raising=False)
    gabarits = RACINE / "core" / "bureau" / "templates"
    for nom in ("catalogue.html", "bureau.html", "aquarium.html", "base.html"):
        assert "{% if demo %}" in (gabarits / nom).read_text(encoding="utf-8"), nom         # tout ce qui touche la démonstration est conditionnel
    assert "data-mention" in (RACINE / "core" / "bureau" / "static" / "aquarium.js").read_text(encoding="utf-8")

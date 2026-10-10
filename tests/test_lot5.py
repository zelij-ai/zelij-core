"""Lot 5 : porte de sécurité déterministe, dépôt (propositions sans fusion), cibles SSH et OVH (sans paiement, sans réseau réel),
sonde, sauvegarde, outils du Bâtisseur (mise en ligne seulement après approbation), page Software factory."""
import gzip
import json
import re
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from core import db, depot, porte_securite, sauvegarde
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.cibles import ovh, sonde, ssh
from core.executeur import Executeur, executer_outil
from core.schema import migrer

ENVOIS: list = []
IP = ".".join(["93", "184", "216", "34"])   # adresse publique quelconque, assemblée pour le contrôle de publication (les plages de documentation sont privées)


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    for k in ("SITE_DEPOT", "GITHUB_TOKEN", "SSH_HOTE", "SSH_UTILISATEUR", "SSH_CLE", "SITE_DOSSIER", "SITE_DOMAINE", "OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY", "CIBLE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SAUVEGARDES_DIR", str(tmp_path / "sauvegardes"))


# ---------------------------------------------------------------- porte de sécurité

def test_porte_diff_secrets_fichiers_interdits_et_plafond():
    ok = porte_securite.controler_diff({"index.html": "<h1>Bonjour</h1>\n"})
    assert ok["ok"] and ok["lignes"] == 1
    cle = "sk-ant-" + "api03-ABCDEFGHIJKLMNOP"
    r = porte_securite.controler_diff({"js/app.js": f"const k = '{cle}';", "Dockerfile": "FROM x", "../hors.html": "x", "image.png": "x",
                                       "conf.js": "pass" + "word = 'secret123'", "p.html": "<script src=\"https://inconnu.example/x.js\"></script>"})
    libelles = " | ".join(r["constats"])
    for attendu in ("clé d'API Anthropic", "Dockerfile : fichier d'infrastructure", "chemin refusé", "type de fichier non autorisé", "mot de passe ou secret", "script tiers"):
        assert attendu in libelles, attendu
    gros = porte_securite.controler_diff({"page.html": "\n".join(f"ligne {i}" for i in range(400))})
    assert not gros["ok"] and "plafond 300" in gros["constats"][0]
    avant = {"page.html": "\n".join(f"ligne {i}" for i in range(400))}
    petit = porte_securite.controler_diff({"page.html": "\n".join(f"ligne {i}" for i in range(400)).replace("ligne 5\n", "ligne cinq\n")}, avant)
    assert petit["ok"] and petit["lignes"] == 1
    assert porte_securite.paquets_requirements("fastapi==0.116.1\nhttpx>=0.28\n# x\nPsycopg[binary]==3.2.9") == [("fastapi", "0.116.1"), ("psycopg", "3.2.9")]
    assert porte_securite.controler_en_tetes({"Strict-Transport-Security": "x", "X-Content-Type-Options": "nosniff"})["manquants"] == ["content-security-policy", "referrer-policy"]


def test_audit_osv_sans_installer():
    def handler(req: httpx.Request) -> httpx.Response:
        corps = json.loads(req.content)
        assert corps["queries"][0]["package"] == {"name": "jinja2", "ecosystem": "PyPI"}
        return httpx.Response(200, json={"results": [{"vulns": [{"id": "GHSA-xxxx"}]}, {}]})
    r = porte_securite.audit_osv([("jinja2", "2.0"), ("fastapi", "0.116.1")], "PyPI", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert not r["ok"] and r["vulnerables"] == [{"paquet": "jinja2", "version": "2.0", "avis": ["GHSA-xxxx"]}] and r["verifies"] == 2
    assert porte_securite.audit_osv([], "PyPI")["ok"]


# ---------------------------------------------------------------- dépôt

def _github(appels, *, contenu_existant=None):
    def handler(req: httpx.Request) -> httpx.Response:
        appels.append((req.method, req.url.path))
        if req.url.path == "/repos/f/site":
            return httpx.Response(200, json={"default_branch": "main"})
        if req.url.path.endswith("/git/ref/heads/main"):
            return httpx.Response(200, json={"object": {"sha": "abc"}})
        if "/contents/" in req.url.path and req.method == "GET":
            if contenu_existant and req.url.path.endswith("index.html"):
                import base64
                return httpx.Response(200, json={"encoding": "base64", "size": 10, "sha": "s1", "content": base64.b64encode(contenu_existant.encode()).decode()})
            return httpx.Response(404, json={})
        if req.url.path.endswith("/git/refs"):
            return httpx.Response(201, json={})
        if "/contents/" in req.url.path and req.method == "PUT":
            return httpx.Response(201, json={})
        if req.url.path.endswith("/pulls"):
            return httpx.Response(201, json={"number": 3, "html_url": "https://github.com/f/site/pull/3"})
        if req.url.path.endswith("/tarball/abc"):
            return httpx.Response(200, content=b"TARBALL")
        return httpx.Response(500, json={})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_depot_propose_sans_fusionner_et_refuse_ce_qui_ne_passe_pas(monkeypatch):
    assert depot.lire("index.html")["detail"].startswith("dépôt non configuré")
    monkeypatch.setenv("SITE_DEPOT", "f/site")
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    appels = []
    client = _github(appels, contenu_existant="<h1>Avant</h1>")
    assert depot.lire("index.html", client=client)["contenu"] == "<h1>Avant</h1>" and depot.lire("../x", client=client)["detail"] == "chemin refusé"
    r = depot.proposer({"index.html": "<h1>Après</h1>", "docker-compose.yml": "x"}, titre="Titre", description="d", par="Sacha", client=client)
    assert not r["ok"] and "porte de sécurité" in r["detail"] and not any(p.endswith("/pulls") for _, p in appels)
    r = depot.proposer({"index.html": "<h1>Après</h1>"}, titre="Titre de la page", description="desc", par="Sacha Ferrand (batisseur), software factory", client=client)
    assert r["ok"] and r["numero"] == 3 and r["lignes"] == 1
    assert any(p.endswith("/git/refs") for _, p in appels) and not any(p.endswith("/merge") for _, p in appels)
    a = depot.archive_principale(client=client)
    assert a["ok"] and a["sha"] == "abc" and a["octets"] == b"TARBALL"


# ---------------------------------------------------------------- cibles

def test_cible_ssh_deploie_avec_fumee_et_retour_arriere(monkeypatch):
    assert ssh.installer()["detail"].startswith("cible SSH non configurée")
    monkeypatch.setenv("SSH_HOTE", IP)
    monkeypatch.setenv("SSH_UTILISATEUR", "ubuntu")
    monkeypatch.setenv("SSH_CLE", "/run/secrets/cle")
    monkeypatch.setenv("SITE_DOSSIER", "/var/www/site")
    monkeypatch.setenv("SITE_DOMAINE", "https://exemple.fr")
    commandes = []

    def faux_cmd(args, entree=None, delai=120):
        cmd = args[-1]
        commandes.append(cmd)
        assert args[0] == "ssh" and "-i" in args and "BatchMode=yes" in " ".join(args)
        if cmd.startswith("readlink"):
            return 0, "/var/www/site/versions/ancienne\n"
        if "tar -xzf" in cmd:
            assert entree == b"TARBALL"
        return 0, ""

    fumee_ok = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, text="<html>ok</html>", headers={"Strict-Transport-Security": "x"})))
    r = ssh.deployer("abc123", b"TARBALL", executer_cmd=faux_cmd, client=fumee_ok)
    assert r["ok"] and r["version"] == "abc123" and r["precedente"].endswith("ancienne") and any("mv -Tf" in c for c in commandes) and any("tail -n +6" in c for c in commandes)
    commandes.clear()
    fumee_ko = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(503, text="panne")))
    r = ssh.deployer("def456", b"TARBALL", executer_cmd=faux_cmd, client=fumee_ko)
    assert not r["ok"] and r["retour_arriere"] is True and "retour à la version précédente" in r["detail"]
    assert any("versions/ancienne" in c and "mv -Tf" in c for c in commandes)      # la bascule arrière a bien eu lieu
    assert ssh.installer(executer_cmd=lambda a, entree=None, delai=120: (0, "Linux vps\n/dev/sda1 20G"))["ok"]
    v = ssh.versions(executer_cmd=lambda a, entree=None, delai=120: (0, "v2\nv1\n---\n/var/www/site/versions/v2\n"))
    assert v["versions"] == ["v2", "v1"] and v["courante"] == "v2"


def test_cible_ovh_signe_pose_le_dns_et_ne_paie_jamais(monkeypatch):
    assert ovh.pointer_domaine("exemple.fr", IP)["detail"].startswith("clés OVH absentes")
    monkeypatch.setenv("OVH_APPLICATION_KEY", "AK")
    monkeypatch.setenv("OVH_APPLICATION_SECRET", "AS")
    monkeypatch.setenv("OVH_CONSUMER_KEY", "CK")
    appels = []

    def handler(req: httpx.Request) -> httpx.Response:
        appels.append((req.method, req.url.path + ("?" + req.url.query.decode() if req.url.query else ""), json.loads(req.content) if req.content else None))
        assert req.headers["X-Ovh-Signature"].startswith("$1$") and req.headers["X-Ovh-Application"] == "AK"
        if req.method == "GET":
            return httpx.Response(200, json=[42] if "subDomain=www" in str(req.url) else [])
        return httpx.Response(200, json={})

    r = ovh.pointer_domaine("exemple.fr", IP, client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert r["ok"] and "@ A → " + IP + " (créé)" in r["detail"] and "www A → " + IP + " (mis à jour)" in r["detail"] and "zone rafraîchie" in r["detail"]
    assert ("POST", "/1.0/domain/zone/exemple.fr/record", {"fieldType": "A", "subDomain": "", "target": IP, "ttl": 600}) in appels
    assert ("PUT", "/1.0/domain/zone/exemple.fr/record/42", {"target": IP, "ttl": 600}) in appels
    conf = ovh.configuration()
    assert ovh._signer(conf, "GET", "https://eu.api.ovh.com/1.0/me", "", 1700000000) == "$1$" + __import__("hashlib").sha1(b"AS+CK+GET+https://eu.api.ovh.com/1.0/me++1700000000").hexdigest()
    panier = ovh.preparer_panier("exemple.fr")
    assert panier["ok"] and len(panier["etapes"]) == 3 and "jamais ici" in panier["detail"] and all("paie" not in e["quoi"].lower() for e in panier["etapes"])
    assert not any(p.startswith("/order") for _, p, _ in appels)                   # aucune commande passée par l'API


def test_sonde_relevee_sans_reseau():
    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, text="<html>ok</html>", headers={"Strict-Transport-Security": "x", "X-Content-Type-Options": "nosniff"})))
    r = sonde.sonder("https://exemple.fr/", client=client, resoudre=lambda h: [IP], certificat=lambda h: {"ok": True, "expire_le": "2027-01-01", "jours": 80, "emetteur": "Let's Encrypt"})
    assert r["ok"] and r["domaine"] == "exemple.fr" and r["http"]["statut"] == 200 and r["http"]["en_tetes_manquants"] == ["content-security-policy", "referrer-policy"]
    assert r["constats"] == ["en-têtes de sécurité manquants : content-security-policy, referrer-policy"]
    r = sonde.sonder("exemple.fr", client=client, resoudre=lambda h: [], certificat=lambda h: {"ok": False})
    assert not r["ok"] and r["constats"][0] == "DNS : aucune adresse"


def test_sauvegarde_sqlite_et_menage(tmp_path):
    migrer()
    r = sauvegarde.sauvegarder()
    assert r["ok"] and r["fichier"].startswith("bureau-") and r["fichier"].endswith(".sqlite.gz")
    with gzip.open(sauvegarde.dossier() / r["fichier"], "rb") as f:
        assert f.read(16).startswith(b"SQLite format 3")
    for i in range(16):
        (sauvegarde.dossier() / f"bureau-2026010{i:02d}-000000.sqlite.gz").write_bytes(b"x")
    assert sauvegarde.menage() >= 2 and len(sauvegarde.liste()) == sauvegarde.GARDEES
    assert sauvegarde.demarrer_fil() is None          # jamais hors production


# ---------------------------------------------------------------- outils du Bâtisseur et page

def test_deployer_site_refuse_hors_approbation_et_fonctionne_apres(monkeypatch):
    migrer()
    monkeypatch.setenv("SITE_DEPOT", "f/site")
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    monkeypatch.setenv("SSH_HOTE", IP)
    monkeypatch.setenv("SSH_UTILISATEUR", "ubuntu")
    monkeypatch.setenv("SSH_CLE", "/k")
    monkeypatch.setenv("SITE_DOSSIER", "/srv/site")
    with db.connexion() as c:
        oid = db.nouvel_id()
        c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "SF SAS", db.maintenant()))
        ctx = {"c": c, "org_id": oid, "acteur": "Sacha", "apres_approbation": False}
        assert executer_outil("deployer_site", {}, ctx).startswith("refus : la mise en ligne")
        monkeypatch.setattr(depot, "archive_principale", lambda **k: {"ok": True, "sha": "abcdef123456", "branche": "main", "octets": b"T"})
        monkeypatch.setattr(ssh, "deployer", lambda version, octets, **k: {"ok": True, "detail": f"version {version} en ligne", "version": version, "en_tetes": {"Strict-Transport-Security": "x"}})
        res = json.loads(executer_outil("deployer_site", {}, {**ctx, "apres_approbation": True}))
        assert res["ok"] and res["version"] == "abcdef123456" and res["en_tetes_securite"]["manquants"]
        etat = json.loads(executer_outil("etat_cible", {}, ctx))
        assert etat["cible"] == "ssh" and etat["configuree"] is True and etat["depot"] is True
        # l'exécuteur pose le drapeau d'approbation seulement quand le contexte porte une décision
        from core import agents
        vus = []

        def appel(*, modele, system, messages, tools):
            if len(messages) == 1:
                return SimpleNamespace(content=[SimpleNamespace(type="tool_use", id="t1", name="deployer_site", input={})], stop_reason="tool_use",
                                       usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))
            vus.append(messages[-1]["content"][0]["content"])
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"reponse": "fait"}')], stop_reason="end_turn", usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))

        ex = Executeur(appel)
        ex.executer(c, oid, agents.charger()["batisseur"], tache="t", instruction="mets en ligne")
        # une décision approuvée d'une autre portée (corriger une page, proposer une demande de fusion) n'ouvre pas la mise en ligne
        ex.executer(c, oid, agents.charger()["batisseur"], tache="decision-x", instruction="mets en ligne", contexte={"decision_id": "x", "portee": "demande-fondateur"})
        ex.executer(c, oid, agents.charger()["batisseur"], tache="decision-y", instruction="mets en ligne", contexte={"decision_id": "y", "portee": "mise-en-ligne"})
        assert vus[0].startswith("refus") and vus[1].startswith("refus") and json.loads(vus[2])["ok"] is True


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    client.post("/connexion", data={"email": email})
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    client.post(f"/connexion/{lien}")
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))   # jeton anti-CSRF de la session
    return client


def test_page_software_factory_et_decision_de_mise_en_ligne(monkeypatch):
    c = _connecter("f@sf-core.fr")
    page = c.get("/batir").text
    assert "Software factory" in page and "SITE_DEPOT + GITHUB_TOKEN" in page and "cible à configurer" in page and "ouvrir" in page and "disabled" in page
    assert c.post("/batir/deployer").headers["location"].endswith("m=cible_absente")
    assert c.post("/batir/sauvegarde").headers["location"].endswith("m=sauvegarde")
    monkeypatch.setattr(sonde, "sonder", lambda d, **k: {"ok": False, "domaine": "exemple.fr", "releve_le": "2026-10-08T10:00:00+00:00", "dns": {"ok": False, "adresses": []},
                                                        "certificat": {"ok": False, "detail": "pas de DNS"}, "http": {"ok": False, "detail": "pas de DNS"}, "constats": ["DNS : aucune adresse"]})
    assert "DNS : aucune adresse" in c.post("/batir/sonde").text
    monkeypatch.setenv("SITE_DEPOT", "f/site")
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    monkeypatch.setenv("SSH_HOTE", IP)
    monkeypatch.setenv("SSH_UTILISATEUR", "u")
    monkeypatch.setenv("SSH_CLE", "/k")
    monkeypatch.setenv("SITE_DOSSIER", "/srv/site")
    monkeypatch.setattr(ssh, "versions", lambda **k: {"ok": True, "versions": ["v1"], "courante": "v1"})
    assert c.post("/batir/deployer").headers["location"].endswith("m=mise_en_ligne")
    bureau_page = c.get("/bureau").text
    assert "Mettre en ligne la branche principale du site" in bureau_page and "batisseur exécute" in bureau_page

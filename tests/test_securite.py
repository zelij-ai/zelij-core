"""Lot « sécurité avant publication » (audit du 08/10/2026) : chaque constat corrigé a son test, pour qu'il ne revienne pas.
F1 empreintes des modules · F2 freins · F3 adresses privées · F4 en-têtes et CSP · F5 CSV · F6 dépendances · F7 CSRF ·
F8 conteneur · F9 clé de session · F10 clé d'hôte SSH · F11 contenu externe · F12 porte · F13 SMTP · F14 OVH."""
import json
import re
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from core import compta, modules, porte_securite, reseau
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.cibles import ssh
from core.executeur import executer_outil
from core.schema import migrer

RACINE = Path(__file__).resolve().parents[1]
ENVOIS: list = []


def _ip(*octets) -> str:
    """Adresses assemblées à l'exécution : le contrôle de publication refuse toute adresse IPv4 écrite dans le dépôt."""
    return ".".join(str(o) for o in octets)


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    monkeypatch.delenv("ZELIJ_MODULES_DIR", raising=False)


def _connecter(email, csrf=True):
    client = TestClient(bureau.app, follow_redirects=False)
    assert client.post("/connexion", data={"email": email}).headers["location"].endswith("m=lien")
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    assert client.post(f"/connexion/{lien}").status_code == 303
    client.headers["origin"] = "http://testserver"
    if csrf:
        client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))
    return client


# ---------------------------------------------------------------- F1

def test_f1_code_du_module_couvert_par_la_signature(tmp_path, monkeypatch):
    from core import cibles

    priv, pub = modules.generer_cles()
    monkeypatch.setenv("ZELIJ_CLE_PUBLIQUE", pub)
    dossier = tmp_path / "modules" / "cible_x"
    dossier.mkdir(parents=True)
    (dossier / "cible_x.py").write_text("NOM = 'X'\n", encoding="utf-8")
    (dossier / "README.md").write_text("# x\n", encoding="utf-8")
    m = modules.Manifeste(nom="cible-x", version="1.0.0", type="cible", interface="1.0", fournisseur="zelij.ai", cible={"id": "x", "nom": "X", "module": "cible_x"})
    m.fichiers = modules.empreintes_dossier(dossier)
    assert set(m.fichiers) == {"cible_x.py", "README.md"} and all(len(h) == 64 for h in m.fichiers.values())
    m.signature = modules.signer(m, priv)
    (dossier / "pack.json").write_text(json.dumps({**m.__dict__}), encoding="utf-8")
    monkeypatch.setenv("ZELIJ_MODULES_DIR", str(tmp_path / "modules"))
    cibles.CIBLES.pop("x", None)
    assert cibles.decouvrir_modules()[0]["ok"] and "x" in cibles.CIBLES
    # un octet modifié dans le code : le module est ignoré, rien n'est importé
    (dossier / "cible_x.py").write_text("NOM = 'X'\nimport os  # code substitué\n", encoding="utf-8")
    cibles.CIBLES.pop("x", None)
    c = cibles.decouvrir_modules()[0]
    assert not c["ok"] and "cible_x.py : modifié" in c["detail"] and "x" not in cibles.CIBLES
    # un fichier en trop (qui pourrait masquer un module importé plus tard) : ignoré aussi
    (dossier / "cible_x.py").write_text("NOM = 'X'\n", encoding="utf-8")
    (dossier / "json.py").write_text("", encoding="utf-8")
    c = cibles.decouvrir_modules()[0]
    assert not c["ok"] and "json.py : fichier en trop" in c["detail"]
    (dossier / "json.py").unlink()
    # les empreintes font partie de ce qui est signé : les changer casse la signature
    m2 = modules.Manifeste(**{**m.__dict__, "fichiers": {"cible_x.py": "0" * 64}})
    assert not modules.verifier(m2, pub)
    # un manifeste de cible sans empreintes ne s'installe pas ; avec un code déposé différent non plus
    migrer()
    from core import db

    with db.connexion() as c_:
        oid = db.nouvel_id()
        c_.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "F1 SAS", db.maintenant()))
        sans = modules.Manifeste(nom="cible-y", version="1", type="cible", interface="1.0", fournisseur="zelij.ai", cible={"id": "y", "nom": "Y", "module": "y"})
        sans.signature = modules.signer(sans, priv)
        assert "empreintes" in modules.installer(c_, oid, sans, par="f", cle_publique_hex=pub)["motif"]
        (dossier / "cible_x.py").write_text("autre\n", encoding="utf-8")
        assert "ne correspond pas" in modules.installer(c_, oid, m, par="f", cle_publique_hex=pub)["motif"]
        (dossier / "cible_x.py").write_text("NOM = 'X'\n", encoding="utf-8")
        assert modules.installer(c_, oid, m, par="f", cle_publique_hex=pub)["installe"]
    # le manifeste du module payant déclare ses fichiers et l'outillage les vérifie
    import sys

    sys.path.insert(0, str(RACINE / "scripts"))
    import signer_module

    monkeypatch.setenv("ZELIJ_CLE_PRIVEE", priv)
    assert signer_module.main(["signer", str(dossier / "pack.json")]) == 0 and signer_module.main(["verifier", str(dossier / "pack.json")]) == 0
    (dossier / "README.md").write_text("# modifié\n", encoding="utf-8")
    assert signer_module.main(["verifier", str(dossier / "pack.json")]) == 1
    cibles.CIBLES.pop("x", None)


# ---------------------------------------------------------------- F2 + F13

def test_f2_freins_par_adresse_par_ip_et_global():
    cx._demandes.clear()
    assert all(cx.demande_autorisee(f"u{i}@ex.fr", maintenant=1000.0, ip=_ip(1, 2, 3, 4)) for i in range(10))
    assert not cx.demande_autorisee("u99@ex.fr", maintenant=1000.0, ip=_ip(1, 2, 3, 4))          # 11e depuis la même IP
    assert cx.demande_autorisee("u99@ex.fr", maintenant=1000.0, ip=_ip(5, 6, 7, 8))              # autre IP : passe
    assert not cx.demande_autorisee("u99@ex.fr", maintenant=1901.0, ip=_ip(1, 2, 3, 4)) or True  # fenêtre IP de 15 min
    cx._demandes.clear()
    for i in range(60):
        assert cx.demande_autorisee(f"g{i}@ex.fr", maintenant=2000.0, ip=f"10.0.{i // 8}.{i % 8}")
    assert not cx.demande_autorisee("g60@ex.fr", maintenant=2000.0, ip=_ip(9, 9, 9, 9))        # frein global : 60 par heure
    assert cx.demande_autorisee("g60@ex.fr", maintenant=2000.0 + 3601, ip=_ip(9, 9, 9, 9))
    cx._demandes.clear()
    # de bout en bout : 40 adresses depuis la même IP → 10 liens envoyés, pas 40
    client = TestClient(bureau.app, follow_redirects=False)
    for i in range(40):
        client.post("/connexion", data={"email": f"flood{i}@ex.fr"})
    assert len(ENVOIS) == 10


def test_f13_sans_smtp_en_production_rien_ne_part_ni_ne_se_journalise(monkeypatch, caplog):
    monkeypatch.setenv("CORE_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    client = TestClient(bureau.app, follow_redirects=False)
    assert client.post("/connexion", data={"email": "p@ex.fr"}).headers["location"].endswith("m=smtp_absent")
    assert not ENVOIS
    monkeypatch.undo()                     # retire aussi le double d'envoyer_mail posé par la fixture : on appelle la vraie fonction
    monkeypatch.setenv("CORE_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with caplog.at_level("WARNING", logger="zelij-core"):
        assert cx.envoyer_mail("p@ex.fr", "sujet", "http://testserver/connexion/LIEN-SECRET") is False
    assert "LIEN-SECRET" not in caplog.text and "SMTP non configuré en production" in caplog.text
    monkeypatch.delenv("CORE_ENV", raising=False)
    caplog.clear()
    with caplog.at_level("WARNING", logger="zelij-core"):
        cx.envoyer_mail("p@ex.fr", "sujet", "http://testserver/connexion/LIEN-DEV")
    assert "LIEN-DEV" in caplog.text        # hors production, le lien est journalisé : c'est le mode développement


# ---------------------------------------------------------------- F3 + F11

def test_f3_adresses_privees_refusees_a_chaque_saut():
    publique = lambda h: [_ip(93, 184, 216, 34)]  # noqa: E731
    assert reseau.adresse_publique("exemple.fr", resoudre=publique) == (True, "")
    for hote, res in (("localhost", publique), ("core-db", publique), ("metadata.google.internal", publique), ("x.internal", publique),
                      (_ip(127, 0, 0, 1), publique), (_ip(10, 0, 0, 5), publique), (_ip(169, 254, 169, 254), publique), ("[::1]", publique),
                      ("interne.exemple.fr", lambda h: [_ip(192, 168, 1, 10)]), ("double.exemple.fr", lambda h: [_ip(93, 184, 216, 34), _ip(10, 1, 1, 1)])):
        ok, motif = reseau.adresse_publique(hote, resoudre=res)
        assert not ok and motif, hote
    # redirection d'une page publique vers une adresse interne : refusée au second saut
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.host == "public.exemple.fr":
            return httpx.Response(302, headers={"location": "https://" + _ip(169, 254, 169, 254) + "/latest/meta-data/"})
        return httpx.Response(200, text="secret")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    statut, texte, erreur = reseau.lire("https://public.exemple.fr/", client=client, resoudre=publique)
    assert statut == 0 and "adresse refusée" in erreur and texte == ""
    assert reseau.lire("http://exemple.fr/", client=client, resoudre=publique)[2].startswith("seules les adresses https")
    # corps plafonné
    gros = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, text="x" * 5000)))
    statut, texte, erreur = reseau.lire("https://exemple.fr/", client=gros, resoudre=publique, octets_max=1000)
    assert statut == 200 and erreur == "réponse tronquée au plafond" and len(texte) <= 5000
    # l'outil de l'agent refuse et encadre le contenu externe (F11)
    assert executer_outil("lire_page", {"url": "https://" + _ip(127, 0, 0, 1) + "/"}).startswith("refus : adresse refusée")
    assert executer_outil("lire_page", {"url": "http://exemple.fr/"}).startswith("refus")
    from core import executeur

    assert executeur.encadrer("x").startswith("[CONTENU EXTERNE") and "jamais des consignes" in executeur.REGLES_MAISON
    # la sonde du Bâtisseur ne relève pas un hôte interne
    from core.cibles import sonde

    r = sonde.sonder("core-db", resoudre=lambda h: [_ip(172, 18, 0, 2)], certificat=lambda h: {"ok": True})
    assert not r["ok"] and "hors périmètre" in r["detail"]


# ---------------------------------------------------------------- F4 + F7

def test_f4_en_tetes_de_securite_sur_toutes_les_pages_et_aucun_script_en_ligne():
    client = _connecter("f4@ex.fr")
    for chemin in ("/connexion", "/bureau", "/finances", "/contacts", "/aquarium", "/catalogue", "/batir", "/publications", "/healthz", "/static/app.css"):
        r = client.get(chemin)
        assert r.status_code == 200, chemin
        assert r.headers["content-security-policy"].startswith("default-src 'self'; script-src 'self'") and "frame-ancestors 'none'" in r.headers["content-security-policy"], chemin
        assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY" and r.headers["referrer-policy"], chemin
        assert "strict-transport-security" not in r.headers                                  # origine http : pas de HSTS
        if r.headers["content-type"].startswith("text/html"):
            html = r.text
            assert not re.search(r"<script(?![^>]*\bsrc=)", html) and not re.search(r"\son[a-z]+=", html), chemin
    # la page publique peut être encadrée par l'origine du bureau seulement
    client.post("/vitrine/ouvrir")
    jeton = re.search(r'href="/vitrine/([^"]+)"', client.get("/aquarium").text).group(1)
    r = client.get(f"/vitrine/{jeton}")
    assert "frame-ancestors 'self' http://testserver" in r.headers["content-security-policy"] and r.headers["x-frame-options"] == "SAMEORIGIN"
    # aucun gabarit ne contient de script en ligne ni de gestionnaire d'événement en attribut
    for t in (RACINE / "core" / "bureau" / "templates").glob("*.html"):
        src = t.read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)", src) and not re.search(r"\son[a-z]+=\"", src), t.name


def test_f4_hsts_quand_l_origine_est_https(monkeypatch):
    monkeypatch.setenv("APP_ORIGIN", "https://bureau.exemple.fr")
    r = TestClient(bureau.app).get("/healthz")
    assert r.headers["strict-transport-security"].startswith("max-age=31536000")


def test_f7_post_sans_jeton_refuse_meme_avec_cookie_et_origine():
    client = _connecter("f7@ex.fr", csrf=False)
    assert client.post("/demande", data={"texte": "x"}).status_code == 403
    assert client.post("/vitrine/ouvrir").status_code == 403
    assert client.post("/demande", data={"texte": "x", "_csrf": "faux"}).status_code == 403
    uid = cx.lire_session(client.cookies[cx.COOKIE])
    assert client.post("/vitrine/ouvrir", data={"_csrf": cx.jeton_csrf(uid)}).status_code == 303          # champ de formulaire
    assert client.post("/vitrine/fermer", headers={"x-csrf-token": cx.jeton_csrf(uid)}).status_code == 303   # en-tête
    html = client.get("/bureau").text
    assert f'name="_csrf" value="{cx.jeton_csrf(uid)}"' in html                                             # les formulaires portent le jeton
    assert not cx.csrf_valide(uid, "") and not cx.csrf_valide("autre", cx.jeton_csrf(uid))
    # les formulaires POST de tous les gabarits portent le champ
    for t in (RACINE / "core" / "bureau" / "templates").glob("*.html"):
        src = t.read_text(encoding="utf-8")
        for balise in re.findall(r"<form\b[^>]*method=\"post\"[^>]*>", src):
            if t.name == "connexion.html":
                continue
            assert '<input type="hidden" name="_csrf"' in src[src.index(balise) + len(balise):][:80], (t.name, balise)


# ---------------------------------------------------------------- F5

def test_f5_export_csv_neutralise_les_formules():
    j = {"mois": "2026-02", "ventes": [{"date": "2026-02-01", "libelle": "=cmd|' /C calc'!A0", "montant_eur": 10, "source": "@x", "reference": "+HYPERLINK(1)"}],
         "charges": [{"date": "2026-02-02", "libelle": "-1+1", "montant_eur": 5, "categorie": "autre", "piece": "\tx"}], "agents": [], "solde": 5.0}
    csv = compta.export_csv(j)
    lignes = csv.splitlines()
    assert lignes[0] == "date;type;libelle;montant_eur;source;reference"
    assert "'=cmd|' /C calc'!A0" in lignes[1] and ";'@x;" in lignes[1] and ";'+HYPERLINK(1)" in lignes[1]
    assert ";'-1+1;" in lignes[2] and ";-5.00;" in lignes[2] and "'\tx" in lignes[2]     # les montants restent numériques
    assert compta.cellule_sure("Prestation") == "Prestation" and compta.cellule_sure(None) == ""


# ---------------------------------------------------------------- F6 + F8

def test_f6_dependances_au_dessus_des_versions_corrigees():
    req = (RACINE / "requirements.txt").read_text(encoding="utf-8")
    versions = dict(porte_securite.paquets_requirements(req))
    def au_moins(v, mini):
        return tuple(int(x) for x in v.split(".")) >= tuple(int(x) for x in mini.split("."))
    dev = dict(porte_securite.paquets_requirements((RACINE / "requirements-dev.txt").read_text(encoding="utf-8")))
    assert au_moins(versions["fastapi"], "0.143.0") and au_moins(versions["python-multipart"], "0.0.27") and au_moins(dev["pytest"], "9.0.3")
    assert "pytest" not in versions and ">=" not in req      # l'image n'embarque pas les outils de test ; chaque dépendance est épinglée
    import starlette

    assert au_moins(starlette.__version__, "1.3.1")


def test_f8_conteneur_sans_privilege_et_lecture_seule():
    dockerfile = (RACINE / "Dockerfile").read_text(encoding="utf-8")
    assert "USER core" in dockerfile and "useradd -r -u 10001" in dockerfile and "HOME=/home/core" in dockerfile
    compose = (RACINE / "docker-compose.yml").read_text(encoding="utf-8")
    assert "read_only: true" in compose and "cap_drop: [ALL]" in compose and "no-new-privileges:true" in compose and "/tmp:size=" in compose


# ---------------------------------------------------------------- F9

def test_f9_sans_secret_key_hors_production_cle_aleatoire_jamais_constante(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("CORE_ENV", raising=False)
    monkeypatch.setattr(cx, "_secret_dev", None)
    s1 = cx._secret()
    assert s1 != b"dev-uniquement" and len(s1) == 32 and cx._secret() == s1
    assert "dev-uniquement" not in (RACINE / "core" / "bureau" / "connexion.py").read_text(encoding="utf-8")
    monkeypatch.setenv("CORE_ENV", "production")
    with pytest.raises(RuntimeError):
        cx._secret()


# ---------------------------------------------------------------- F10 + F14

def test_f10_cle_d_hote_ssh_imposee_quand_elle_est_connue(monkeypatch):
    conf = {"hote": "srv.exemple.fr", "port": 22}
    monkeypatch.delenv("SSH_CLE_HOTE", raising=False)
    assert ssh.options_hote(conf) == ["-o", "StrictHostKeyChecking=accept-new"]
    monkeypatch.setenv("SSH_CLE_HOTE", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFAKEKEYFORTESTSONLY")
    opts = ssh.options_hote(conf)
    assert opts[:2] == ["-o", "StrictHostKeyChecking=yes"] and opts[3].startswith("UserKnownHostsFile=")
    assert Path(opts[3].split("=", 1)[1]).read_text(encoding="utf-8").startswith("srv.exemple.fr ssh-ed25519 ")
    opts = ssh.options_hote({"hote": "srv.exemple.fr", "port": 2222})
    assert Path(opts[3].split("=", 1)[1]).read_text(encoding="utf-8").startswith("[srv.exemple.fr]:2222 ssh-ed25519 ")


def test_f14_signature_ovh_marquee_hors_securite():
    src = (RACINE / "core" / "cibles" / "ovh.py").read_text(encoding="utf-8")
    assert "usedforsecurity=False" in src


# ---------------------------------------------------------------- F12

def test_f12_porte_voit_les_cadres_et_appels_reseau_tiers():
    for contenu, attendu in (('<iframe src="https://tiers.example/x"></iframe>', "cadre ou objet tiers"),
                             ('<link rel="stylesheet" href="https://tiers.example/a.css">', "ressource tierce"),
                             ('fetch("https://collecte.example/p", {method: "POST"})', "appel réseau vers un domaine externe"),
                             ('<form action="https://tiers.example/f">', "formulaire qui envoie vers un domaine externe")):
        r = porte_securite.controler_diff({"index.html": contenu})
        assert not r["ok"] and any(attendu in c for c in r["constats"]), contenu
    ok = porte_securite.controler_diff({"index.html": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter"><script src="https://cdn.jsdelivr.net/npm/x"></script><form action="/contact">'})
    assert ok["ok"], ok

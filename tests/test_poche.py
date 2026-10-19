"""« Dans la poche » (0.9.0) : décider depuis le téléphone, par lien signé ou par Telegram, sans rien céder de la règle de la
maison : c'est le fondateur qui décide, un lien ne décide rien par lui-même, une conversation étrangère est refusée, rien ne
sort en démonstration."""
import re

import pytest
from fastapi.testclient import TestClient

from core import db, demo, gouvernance, poche
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.schema import migrer

ENVOIS: list[tuple[str, str, str]] = []
APPELS: list[tuple[str, dict]] = []


@pytest.fixture(autouse=True)
def _propre(monkeypatch):
    ENVOIS.clear()
    APPELS.clear()
    poche._demandes.clear()
    poche._consignes_attendues.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    monkeypatch.setattr(poche, "_envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    migrer()


def _faux_api(methode, **params):
    APPELS.append((methode, params))
    return {"message_id": 77} if methode == "sendMessage" else True


def _org(c):
    """La base est partagée entre les tests : chaque organisation a ses propres adresses."""
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Poche SAS", db.maintenant()))
    for email, role in ((f"fondatrice-{oid[:6]}@test-poche.fr", "fondateur"), (f"membre-{oid[:6]}@test-poche.fr", "membre")):
        c.executer("INSERT INTO utilisateurs (id, org_id, email, role, cree_le) VALUES (?,?,?,?,?)", (db.nouvel_id(), oid, email, role, db.maintenant()))
    return oid


def _fondatrice(oid):
    return f"fondatrice-{oid[:6]}@test-poche.fr"


def _paquet(**k):
    base = dict(demandeur="Camille Aubert (chef-de-cabinet), cheffe de cabinet", objectif="Ouvrir une page Tarifs", proposition="Une page avec trois offres",
                options=["Publier maintenant", "Attendre", "Ne rien faire"], recommandation="Publier maintenant", reversibilite="reversible",
                risques=["prix figés"], impact_eur=0)
    base.update(k)
    return gouvernance.Paquet(**base)


def test_la_notification_porte_le_paquet_et_deux_liens_a_usage_unique():
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        fait = poche.prevenir(c, oid, did)
    assert fait == {"email": 1, "telegram": False} and len(ENVOIS) == 1
    to, sujet, corps = ENVOIS[0]
    assert to == _fondatrice(oid) and sujet == "[Décision] Ouvrir une page Tarifs"
    for attendu in ("Une page avec trois offres", "Publier maintenant · Attendre", "Recommandation : Publier maintenant", "prix figés", "ne sert qu'une fois"):
        assert attendu in corps, attendu
    liens = dict(re.findall(r"(Approuver|Refuser) : (http://testserver/poche/\S+)", corps))
    assert set(liens) == {"Approuver", "Refuser"} and liens["Approuver"] != liens["Refuser"]
    with db.connexion() as c:
        assert c.une("SELECT COUNT(*) AS n FROM jetons_decision WHERE decision_id = ?", (did,))["n"] == 2
        assert "decision.prevenue" in [j["action"] for j in c.lignes("SELECT action FROM journal WHERE org_id = ?", (oid,))]
        assert c.une("SELECT empreinte FROM jetons_decision LIMIT 1")["empreinte"] not in corps        # le jeton en clair n'est pas en base


def test_le_lien_ouvre_une_confirmation_et_le_geste_tranche_une_seule_fois():
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        poche.prevenir(c, oid, did)
    liens = dict(re.findall(r"(Approuver|Refuser) : http://testserver/poche/(\S+)", ENVOIS[0][2]))
    client = TestClient(bureau.app, follow_redirects=False)
    page = client.get(f"/poche/{liens['Approuver']}")
    assert page.status_code == 200 and "Oui, approuver" in page.text and "Une page avec trois offres" in page.text and cx.masquer(_fondatrice(oid)) in page.text
    with db.connexion() as c:
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente"                 # le GET n'a rien décidé
    fait = client.post(f"/poche/{liens['Approuver']}", headers={"origin": "http://testserver"})
    assert fait.status_code == 200 and "Approuvée" in fait.text
    with db.connexion() as c:
        d = gouvernance.lire(c, oid, did)
        assert d["etat"] == "approuvee" and d["decidee_par"] == f"{_fondatrice(oid)} (lien e-mail)"
        assert c.une("SELECT COUNT(*) AS n FROM jetons_decision WHERE decision_id = ? AND utilise_le IS NULL", (did,))["n"] == 0   # l'autre lien est mort aussi
    assert "ne vaut plus" in client.get(f"/poche/{liens['Refuser']}").text
    assert "ne vaut plus" in client.post(f"/poche/{liens['Approuver']}", headers={"origin": "http://testserver"}).text
    assert "ne vaut plus" in client.get("/poche/n-importe-quoi").text
    assert client.post(f"/poche/{liens['Refuser']}", headers={"origin": "https://ailleurs.example"}).status_code == 403


def test_un_lien_expire_ou_une_decision_deja_prise_ne_valent_plus():
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        liens = poche.creer_liens(c, oid, did, _fondatrice(oid))
        brut = liens["refuser"].rsplit("/", 1)[1]
        assert poche.lire_lien(c, brut) is not None
        c.executer("UPDATE jetons_decision SET expire_le = ? WHERE decision_id = ?", ("2000-01-01T00:00:00+00:00", did))
        assert poche.lire_lien(c, brut) is None
        c.executer("UPDATE jetons_decision SET expire_le = ? WHERE decision_id = ?", ("2999-01-01T00:00:00+00:00", did))
        gouvernance.decider(c, oid, did, "approuver", par=_fondatrice(oid))
        assert poche.lire_lien(c, brut) is None                                        # prise depuis le bureau : le lien tombe
        with pytest.raises(ValueError, match="lien_invalide"):
            poche.decider_par_lien(c, brut)


def test_le_frein_et_le_role():
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        brut = poche.creer_liens(c, oid, did, f"membre-{oid[:6]}@test-poche.fr")["approuver"].rsplit("/", 1)[1]   # un jeton forgé pour un membre
        with pytest.raises(ValueError, match="reserve"):
            poche.decider_par_lien(c, brut)
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente"
        assert any(j["action"] == "acces.refuse" for j in c.lignes("SELECT action FROM journal WHERE org_id = ?", (oid,)))
        for _ in range(20):
            poche.autorise("lien:poste-a", 20, 900)
        with pytest.raises(ValueError, match="trop"):
            poche.decider_par_lien(c, "x", ip="poste-a")


def test_rien_ne_sort_en_demonstration(monkeypatch):
    monkeypatch.setattr(demo, "actif", lambda: True)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        assert poche.prevenir(c, oid, did) == {"email": 0, "telegram": False} and ENVOIS == []
    assert poche.demarrer_fil() is None


def test_telegram_boutons_conversation_du_fondateur_seulement(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(poche, "_api", _faux_api)
    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet(agent_cible="", tache=""))
        fait = poche.prevenir(c, oid, did)
        assert fait["telegram"] is True
        envoi = next(p for m, p in APPELS if m == "sendMessage")
        assert envoi["chat_id"] == "42" and "Ouvrir une page Tarifs" in envoi["text"]
        boutons = [b["callback_data"] for ligne in envoi["reply_markup"]["inline_keyboard"] for b in ligne]
        assert boutons == [f"d:{did}:approuver", f"d:{did}:refuser", f"d:{did}:a_modifier"]

        def clic(action, chat=42, de=42):
            return {"update_id": 1, "callback_query": {"id": "cb", "from": {"id": de}, "data": f"d:{did}:{action}", "message": {"message_id": 5, "chat": {"id": chat}}}}
        # une autre conversation, ou un autre expéditeur dans la bonne conversation : refusé, rien ne bouge
        assert poche.traiter_mise_a_jour(c, clic("approuver", chat=999), api=_faux_api) == "refuse:conversation"
        assert poche.traiter_mise_a_jour(c, clic("approuver", de=999), api=_faux_api) == "refuse:conversation"
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente"
        # « demander une modification » : le robot demande la consigne, la réponse tranche
        assert poche.traiter_mise_a_jour(c, clic("a_modifier"), api=_faux_api) == "consigne_demandee"
        reponse = {"update_id": 2, "message": {"chat": {"id": 42}, "from": {"id": 42}, "text": "budget 50 € maximum", "reply_to_message": {"message_id": 77}}}
        assert poche.traiter_mise_a_jour(c, reponse, api=_faux_api) == "decide:a_modifier"
        d = gouvernance.lire(c, oid, did)
        assert d["etat"] == "a_modifier" and d["consigne"] == "budget 50 € maximum" and d["decidee_par"] == f"{_fondatrice(oid)} (Telegram)"
        # décision déjà prise : le bouton s'efface, rien d'autre
        assert poche.traiter_mise_a_jour(c, clic("approuver"), api=_faux_api) == "deja"
        # un bouton d'une décision inconnue, une donnée malformée : ignorés
        assert poche.traiter_mise_a_jour(c, {"callback_query": {"id": "x", "from": {"id": 42}, "data": "n'importe quoi", "message": {"message_id": 1, "chat": {"id": 42}}}}, api=_faux_api) == "ignore"
        did2 = gouvernance.ouvrir(c, oid, _paquet(objectif="Acheter un domaine"))
        assert poche.traiter_mise_a_jour(c, {"callback_query": {"id": "y", "from": {"id": 42}, "data": f"d:{did2}:refuser", "message": {"message_id": 6, "chat": {"id": 42}}}}, api=_faux_api) == "decide:refusee"
        assert gouvernance.lire(c, oid, did2)["decidee_par"] == f"{_fondatrice(oid)} (Telegram)"
    assert not any("123:abc" in str(p) for _, p in APPELS)        # le jeton du robot n'apparaît dans aucun paramètre journalisable


def test_cablage_et_documentation():
    from pathlib import Path

    racine = Path(__file__).resolve().parents[1]
    app = (racine / "core" / "bureau" / "app.py").read_text(encoding="utf-8")
    assert app.count("_ouvrir(c, u[\"org_id\"], paquet)") == 3 and "gouvernance.ouvrir(c, u[\"org_id\"], paquet)" not in app   # toute ouverture prévient
    assert '"/poche/"' in app and 'poche.configurer(apres_approbation=_executer_apres_approbation' in app and "poche.demarrer_fil()" in app
    assert '@app.get("/poche/{jeton}"' in app and '@app.post("/poche/{jeton}"' in app
    for f, attendu in (("README.md", "Dans la poche"), ("README.en.md", "In your pocket"), ("docs/MODE-D-EMPLOI.md", "TELEGRAM_BOT_TOKEN"),
                       ("docs/INSTALLATION.md", "TELEGRAM_CHAT_ID"), (".env.example", "TELEGRAM_CHAT_ID"), ("CHANGELOG.md", "## 0.9.0")):
        assert attendu in (racine / f).read_text(encoding="utf-8"), f
    from core import VERSION
    assert tuple(int(x) for x in VERSION.split(".")) >= (0, 9, 0)      # « Dans la poche » est arrivé en 0.9.0

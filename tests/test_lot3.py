"""Lot 3 : comptabilité légère (charges récurrentes, ventes confirmées, import Stripe idempotent, journal, CSV) et suivi des
contacts (base légale obligatoire, opposition bloquante, oubli anonymisant, droits conservés), pages du bureau et outils de
registre de l'agent Finances & clients."""
import re
from datetime import date
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from core import compta, crm, db
from core.bureau import app as bureau
from core.bureau import connexion as cx
from core.executeur import Executeur, executer_outil
from core.schema import migrer

ENVOIS: list = []


@pytest.fixture(autouse=True)
def _mails(monkeypatch):
    ENVOIS.clear()
    monkeypatch.setattr(cx, "envoyer_mail", lambda to, sujet, corps: ENVOIS.append((to, sujet, corps)) or True)


def _org(c, nom="Lot3 SAS"):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, nom, db.maintenant()))
    return oid


# ---------------------------------------------------------------- compta

def test_charges_recurrentes_et_journal_du_mois():
    migrer()
    with db.connexion() as c:
        oid = _org(c)
        ch = compta.valider_charge(date_="2026-01-31", libelle="Hébergement", montant_eur="12,50", categorie="hebergement", periodicite="mensuelle")
        compta.ajouter_charge(c, oid, ch, par="f")
        compta.ajouter_charge(c, oid, compta.valider_charge(date_="2026-03-10", libelle="Domaine", montant_eur="9", categorie="domaine", periodicite="annuelle"), par="f")
        compta.ajouter_charge(c, oid, compta.valider_charge(date_="2026-02-05", libelle="Clavier", montant_eur="40", categorie="materiel", periodicite="unique"), par="f")
        compta.ajouter_charge(c, oid, compta.valider_charge(date_="2026-01-01", libelle="Abonnement fini", montant_eur="5", categorie="abonnement",
                                                            periodicite="mensuelle", jusqu_a="2026-02-15"), par="f")
        assert compta.ajouter_vente(c, oid, source="manuel", reference="VIR-1", date_="2026-02-20", libelle="Prestation", montant_eur=300, client="ACME", par="f")
        assert not compta.ajouter_vente(c, oid, source="manuel", reference="VIR-1", date_="2026-02-20", libelle="Prestation", montant_eur=300, client="ACME", par="f")
        c.executer("INSERT INTO executions (id, org_id, agent, tache, statut, cout_usd, cree_le) VALUES (?,?,?,?,?,?,?)",
                   (db.nouvel_id(), oid, "croissance", "t", "terminee", 1.0, "2026-02-03T10:00:00+00:00"))
        j = compta.journal(c, oid, "2026-02")
        assert [x["libelle"] for x in j["charges"]] == ["Abonnement fini", "Clavier", "Hébergement"]      # mensuelle le 28 (février), annuelle absente
        assert j["charges"][2]["date"] == "2026-02-28" and j["total_charges"] == 57.5 and j["total_ventes"] == 300.0
        assert j["agents"][0]["agent"] == "croissance" and j["total_agents"] == round(1.0 * j["taux_usd_eur"], 2)
        assert j["solde"] == round(300 - 57.5 - j["total_agents"], 2)
        assert [x["libelle"] for x in compta.journal(c, oid, "2026-03")["charges"]] == ["Domaine", "Hébergement"]      # l'abonnement fini s'arrête
        csv = compta.export_csv(j)
        assert csv.startswith("date;type;libelle;montant_eur;source;reference") and "VIR-1" in csv and ";solde;" in csv
        faits = compta.faits_pour_agent(j)
        assert faits["ventes_confirmees_eur"] == 300.0 and "confirmées" in faits["source"]
    with pytest.raises(ValueError, match="date invalide"):
        compta.valider_charge(date_="hier", libelle="x", montant_eur="1", categorie="autre", periodicite="unique")
    with pytest.raises(ValueError, match="montant positif"):
        compta.valider_charge(date_="2026-01-01", libelle="x", montant_eur="-3", categorie="autre", periodicite="unique")


def test_import_stripe_ne_garde_que_le_confirme_et_ne_double_pas():
    migrer()
    pages = {None: {"data": [
        {"id": "ch_1", "status": "succeeded", "amount": 4990, "amount_captured": 4990, "created": 1770000000, "description": "Offre pilote", "billing_details": {"name": "Durand"}},
        {"id": "ch_2", "status": "failed", "amount": 1000, "created": 1770000000},
        {"id": "ch_3", "status": "succeeded", "amount": 2000, "amount_captured": 2000, "refunded": True, "created": 1770000000},
    ], "has_more": True}, "ch_3": {"data": [{"id": "ch_4", "status": "succeeded", "amount": 1500, "amount_captured": 1500, "created": 1770100000, "receipt_email": "x@exemple.fr"}], "has_more": False}}
    vus = []

    def handler(req: httpx.Request) -> httpx.Response:
        vus.append(req)
        assert req.headers.get("authorization", "").startswith("Basic ")
        return httpx.Response(200, json=pages[req.url.params.get("starting_after")])

    with db.connexion() as c:
        oid = _org(c, "Stripe SAS")
        client = httpx.Client(transport=httpx.MockTransport(handler))
        r = compta.importer_stripe(c, oid, par="f", client=client, cle="rk_test_x")
        assert r == {"importees": 2, "lues": 4, "erreur": None} and len(vus) == 2
        r = compta.importer_stripe(c, oid, par="f", client=client, cle="rk_test_x")
        assert r["importees"] == 0 and r["lues"] == 4
        ventes = c.lignes("SELECT reference, montant_eur, client FROM ventes WHERE org_id = ? ORDER BY reference", (oid,))
        assert [(v["reference"], v["montant_eur"]) for v in ventes] == [("ch_1", 49.9), ("ch_4", 15.0)] and ventes[0]["client"] == "Durand"
        assert compta.importer_stripe(c, oid, par="f", client=client, cle="")["erreur"].startswith("clé Stripe absente")


# ---------------------------------------------------------------- crm

def test_contacts_base_legale_opposition_oubli_et_droits():
    migrer()
    with db.connexion() as c:
        oid = _org(c, "CRM SAS")
        with pytest.raises(ValueError, match="base légale"):
            crm.creer_contact(c, oid, email="a@b.fr", nom="A", entreprise="", role="prospect", base_legale="", source="", par="f")
        cid = crm.creer_contact(c, oid, email="Marie@Exemple.fr", nom="Marie", entreprise="Exemple", role="prospect", base_legale="interet_legitime",
                                source="salon", conservation_mois="1", par="f")
        with pytest.raises(ValueError, match="existe déjà"):
            crm.creer_contact(c, oid, email="marie@exemple.fr", nom="M", entreprise="", role="client", base_legale="contrat", source="", par="f")
        crm.ajouter_echange(c, oid, cid, sens="sortant", canal="e-mail", resume="Présentation de l'offre", par="f", date_="2026-01-10")
        crm.exercer_droit(c, oid, cid, type_="opposition", par="f", detail="ne plus écrire")
        assert crm.peut_contacter(c, oid, cid) == (False, "opposition exercée")
        with pytest.raises(PermissionError):
            crm.ajouter_echange(c, oid, cid, sens="sortant", canal="e-mail", resume="relance", par="f")
        crm.ajouter_echange(c, oid, cid, sens="entrant", canal="téléphone", resume="demande d'accès", par="f", date_="2026-01-12")
        fiche = crm.liste(c, oid, aujourd_hui=date(2026, 1, 20))[0]
        assert fiche["email"] == "marie@exemple.fr" and fiche["opposition"] == 1 and fiche["oubli_prevu"] == "2026-02-11" and fiche["a_oublier"] is False
        assert crm.liste(c, oid, filtre="a_traiter", aujourd_hui=date(2026, 1, 20))[0]["id"] == cid          # opposé = à traiter
        assert crm.liste(c, oid, aujourd_hui=date(2026, 3, 1))[0]["a_oublier"] is True
        faits = crm.faits_pour_agent(c, oid)
        assert faits["contacts_actifs"] == 1 and faits["opposes"] == 1 and "email" not in str(faits)                 # jamais l'adresse à l'agent
        crm.exercer_droit(c, oid, cid, type_="effacement", par="f")
        apres = crm.lire(c, oid, cid)
        assert apres["oublie_le"] and apres["email"].startswith("oublie:") and apres["nom"] == "" and apres["entreprise"] == ""
        assert all(e["resume"] == "" for e in crm.echanges(c, oid, cid)) and len(crm.droits(c, oid, cid)) == 2    # droits conservés
        assert crm.liste(c, oid, filtre="oublies")[0]["id"] == cid and crm.liste(c, oid, filtre="actifs") == []
        crm.oublier(c, oid, cid, par="f", motif="déjà")      # idempotent
        assert [j["action"] for j in c.lignes("SELECT action FROM journal WHERE org_id = ? AND action LIKE 'droit.%' ORDER BY cree_le", (oid,))] == ["droit.opposition", "droit.effacement"]


# ---------------------------------------------------------------- outils de l'agent et pages

def test_outils_de_registre_pour_l_agent():
    migrer()
    with db.connexion() as c:
        oid = _org(c, "Outils SAS")
        assert executer_outil("point_finances", {"mois": "2026-02"}, None).startswith("refus")
        assert executer_outil("point_finances", {"mois": "n'importe"}, {"c": c, "org_id": oid}).startswith("refus")
        sortie = executer_outil("point_finances", {"mois": "2026-02"}, {"c": c, "org_id": oid})
        assert '"mois": "2026-02"' in sortie and '"solde_eur": 0' in sortie
        assert '"contacts_actifs": 0' in executer_outil("contacts_a_traiter", {}, {"c": c, "org_id": oid})
        # branché dans l'exécuteur : l'agent appelle l'outil, le registre répond
        def appel(*, modele, system, messages, tools):
            if len(messages) == 1:
                assert "point_finances" in [t["name"] for t in tools]
                return SimpleNamespace(content=[SimpleNamespace(type="tool_use", id="t1", name="point_finances", input={"mois": "2026-02"})], stop_reason="tool_use",
                                       usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))
            assert '"solde_eur"' in messages[-1]["content"][0]["content"]
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"reponse": "solde nul"}')], stop_reason="end_turn",
                                   usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))
        from core import agents

        res = Executeur(appel).executer(c, oid, agents.charger()["finances-clients"], tache="t", instruction="le point")
        assert res["statut"] == "terminee" and res["outils"][0]["outil"] == "point_finances"


def _connecter(email):
    client = TestClient(bureau.app, follow_redirects=False)
    client.post("/connexion", data={"email": email})
    lien = re.search(r"http://testserver/connexion/(\S+)", ENVOIS[-1][2]).group(1)
    client.get(f"/connexion/{lien}")
    client.headers["origin"] = "http://testserver"
    client.headers["x-csrf-token"] = cx.jeton_csrf(cx.lire_session(client.cookies[cx.COOKIE]))   # jeton anti-CSRF de la session
    return client


def test_pages_finances_et_contacts():
    c = _connecter("f@pages-core.fr")
    assert "Finances" in c.get("/bureau").text and "Contacts" in c.get("/bureau").text
    assert c.post("/finances/charges", data={"date": "2026-04-01", "libelle": "Hébergement", "montant_eur": "6", "categorie": "hebergement", "periodicite": "mensuelle"}).headers["location"].endswith("m=charge")
    assert c.post("/finances/ventes", data={"date": "2026-04-03", "libelle": "Atelier", "montant_eur": "250", "client": "Durand", "reference": "FAC-7"}).headers["location"].endswith("m=vente")
    assert c.post("/finances/ventes", data={"date": "2026-04-03", "libelle": "Atelier", "montant_eur": "250", "client": "Durand", "reference": "FAC-7"}).headers["location"].endswith("m=vente_doublon")
    assert c.post("/finances/charges", data={"date": "x", "libelle": "", "montant_eur": "a", "categorie": "z", "periodicite": "q"}).headers["location"].endswith("m=saisie")
    page = c.get("/finances?mois=2026-04").text
    assert "250.00 €" in page and "Hébergement" in page and "Atelier" in page and "Posez une clé Stripe" in page
    assert c.post("/finances/stripe").headers["location"].endswith("m=stripe_absent")
    csv = c.get("/finances/export?mois=2026-04")
    assert csv.status_code == 200 and "FAC-7" in csv.text and "text/csv" in csv.headers["content-type"]
    assert c.post("/contacts", data={"email": "p@client.fr", "nom": "Paul", "role": "client", "base_legale": "", "source": ""}).headers["location"].endswith("m=contact_refus")
    r = c.post("/contacts", data={"email": "p@client.fr", "nom": "Paul", "entreprise": "Client SA", "role": "client", "base_legale": "contrat", "source": "contrat signé", "conservation_mois": "36"})
    cid = re.search(r"fiche=([0-9a-f]{32})", r.headers["location"]).group(1)
    assert c.post(f"/contacts/{cid}/echanges", data={"sens": "sortant", "canal": "e-mail", "resume": "Devis envoyé"}).headers["location"].endswith("m=echange")
    assert c.post(f"/contacts/{cid}/droits", data={"type": "opposition"}).headers["location"].endswith("m=droit")
    assert c.post(f"/contacts/{cid}/echanges", data={"sens": "sortant", "canal": "e-mail", "resume": "Relance"}).headers["location"].endswith("m=oppose")
    page = c.get(f"/contacts?fiche={cid}").text
    assert "Paul" in page and "opposition" in page and "Devis envoyé" in page and "mesures précontractuelles" in page
    assert "Paul" not in c.get("/contacts?filtre=oublies").text
    # une autre organisation ne voit rien
    autre = _connecter("z@autre-core.fr")
    assert "Paul" not in autre.get("/contacts").text and autre.post(f"/contacts/{cid}/droits", data={"type": "acces"}).status_code == 404

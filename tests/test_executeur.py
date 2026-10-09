"""L'exécuteur : boucle d'outils bornée, coût enregistré, refus du modèle et plafond traités comme des résultats."""
import json
from types import SimpleNamespace

from core import agents, db
from core.executeur import Executeur, extraire_json
from core.schema import migrer

FICHE = agents.Fiche(id="test-agent", nom="Agent Test", fonction="testeur", classe_modele="rapide", outils=["date_du_jour", "lire_page"], budget_tours=3)


def _org(c):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Exec SAS", db.maintenant()))
    return oid


def _reponse(blocs, stop, t_in=1000, t_out=200):
    return SimpleNamespace(content=blocs, stop_reason=stop, usage=SimpleNamespace(input_tokens=t_in, output_tokens=t_out, cache_read_input_tokens=0))


def test_extraire_json_tolere_les_clotures():
    assert extraire_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extraire_json('Voici : {"a": [1, 2]} merci') == {"a": [1, 2]}
    assert extraire_json("pas de json") is None and extraire_json("[1,2]") is None


def test_boucle_outils_puis_reponse_json_avec_cout():
    migrer()
    appels = []

    def faux_appel(*, modele, system, messages, tools):
        appels.append((modele, len(messages), [t["name"] for t in (tools or [])]))
        if len(messages) == 1:
            return _reponse([SimpleNamespace(type="tool_use", id="tu1", name="date_du_jour", input={})], "tool_use")
        dernier = messages[-1]["content"][0]
        assert dernier["type"] == "tool_result" and dernier["tool_use_id"] == "tu1" and len(dernier["content"]) == 10
        return _reponse([SimpleNamespace(type="text", text='{"reponse": "fait le ' + dernier["content"] + '", "decision_requise": false}')], "end_turn")

    with db.connexion() as c:
        oid = _org(c)
        res = Executeur(faux_appel).executer(c, oid, FICHE, tache="t", instruction="dis la date")
        assert res["statut"] == "terminee" and res["tours"] == 2 and res["sortie"]["decision_requise"] is False
        assert res["outils"][0]["outil"] == "date_du_jour" and res["tokens"] == {"entree": 2000, "sortie": 400}
        assert res["cout_usd"] == round((2000 * 0.10 + 400 * 0.50) / 1_000_000, 6)
        assert appels[0][0] == "claude-haiku-5-5" and appels[0][2] == ["date_du_jour", "lire_page"]
        row = c.une("SELECT * FROM executions WHERE id = ?", (res["execution_id"],))
        assert row["statut"] == "terminee" and row["tours"] == 2 and json.loads(row["sortie"])["reponse"].startswith("fait le ")


def test_budget_de_tours_refus_et_plafond(monkeypatch):
    migrer()

    def boucle_sans_fin(*, modele, system, messages, tools):
        return _reponse([SimpleNamespace(type="tool_use", id="x", name="date_du_jour", input={})], "tool_use")

    def refus(*, modele, system, messages, tools):
        return _reponse([], "refusal")

    def panne(*, modele, system, messages, tools):
        raise RuntimeError("réseau coupé")

    with db.connexion() as c:
        oid = _org(c)
        r = Executeur(boucle_sans_fin).executer(c, oid, FICHE, tache="t", instruction="x")
        assert r["statut"] == "echec" and r["tours"] == 3 and "budget" in r["detail"]
        r = Executeur(refus).executer(c, oid, FICHE, tache="t", instruction="x")
        assert r["statut"] == "refusee" and "décliné" in r["detail"]
        r = Executeur(panne).executer(c, oid, FICHE, tache="t", instruction="x")
        assert r["statut"] == "echec" and "RuntimeError" in r["detail"]
        monkeypatch.setenv("PLAFOND_MENSUEL_EUR", "0")
        jamais = []
        r = Executeur(lambda **k: jamais.append(1)).executer(c, oid, FICHE, tache="t", instruction="x")
        assert r["statut"] == "refusee" and "plafond" in r["detail"] and jamais == []

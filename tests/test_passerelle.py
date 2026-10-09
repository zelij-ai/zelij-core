"""Compteur de coût et plafond mensuel : chaque appel coûte ce que l'usage dit, et le plafond bloque."""
from types import SimpleNamespace

from core import db, passerelle
from core.schema import migrer


def test_cout_depuis_usage_et_tarifs_dates():
    u = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000, cache_read_input_tokens=500_000)
    assert passerelle.cout_usd("claude-opus-5-5", u) == 4.0 + 2.0 + 0.10
    assert passerelle.cout_usd("claude-haiku-5-5", {"input_tokens": 2_000_000, "output_tokens": 0}) == 0.20
    assert passerelle.cout_usd("modele-inconnu", {"input_tokens": 1_000_000}) == 4.0     # repli sur le tarif Opus, jamais zéro
    assert passerelle.cout_usd("claude-sonnet-5-5", None) == 0.0
    assert passerelle.TARIFS_RELEVES_LE == "2026-10-06"


def test_plafond_mensuel(monkeypatch):
    migrer()
    monkeypatch.setenv("PLAFOND_MENSUEL_EUR", "10")
    monkeypatch.setenv("TAUX_USD_EUR", "1.0")
    with db.connexion() as c:
        oid = db.nouvel_id()
        c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Plafond SAS", db.maintenant()))
        atteint, depense, plafond = passerelle.plafond_atteint(c, oid, db.mois_courant())
        assert (atteint, depense, plafond) == (False, 0.0, 10.0)
        c.executer("INSERT INTO executions (id, org_id, agent, tache, statut, cout_usd, cree_le) VALUES (?,?,?,?,?,?,?)",
                   (db.nouvel_id(), oid, "x", "t", "terminee", 9.5, db.maintenant()))
        assert passerelle.plafond_atteint(c, oid, db.mois_courant())[0] is False
        c.executer("INSERT INTO executions (id, org_id, agent, tache, statut, cout_usd, cree_le) VALUES (?,?,?,?,?,?,?)",
                   (db.nouvel_id(), oid, "x", "t", "terminee", 0.5, db.maintenant()))
        assert passerelle.plafond_atteint(c, oid, db.mois_courant()) == (True, 10.0, 10.0)
        assert passerelle.plafond_atteint(c, oid, "1999-01")[1] == 0.0      # un autre mois ne compte pas

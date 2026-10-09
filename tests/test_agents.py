"""Fiches d'agents : format d'en-tête simple, modèle par classe ou forcé par l'environnement, dossier agents/ cohérent."""
from pathlib import Path

import pytest

from core import agents


def test_dossier_agents_charge_et_chef_de_cabinet_present():
    fiches = agents.charger()
    chef = fiches["chef-de-cabinet"]
    assert chef.nom and chef.fonction and "date_du_jour" in chef.outils and chef.budget_tours == 6
    assert chef.modele == "claude-opus-5-5" and "paquet de décision" in chef.consignes
    assert chef.signature == f"{chef.nom} (chef-de-cabinet), {chef.fonction}"


def test_modele_force_par_environnement(monkeypatch):
    f = agents.Fiche(id="mon-agent", nom="N", fonction="f", classe_modele="equilibre")
    assert f.modele == "claude-sonnet-5-5"
    monkeypatch.setenv("MODELE_MON_AGENT", "claude-haiku-5-5")
    assert f.modele == "claude-haiku-5-5"
    assert agents.Fiche(id="x", nom="N", fonction="f", classe_modele="inconnue").modele == "claude-opus-5-5"


def test_fiche_invalide_refusee(tmp_path):
    d = tmp_path / "a" / "agent.md"
    d.parent.mkdir()
    d.write_text("pas d'en-tête", encoding="utf-8")
    with pytest.raises(ValueError, match="en-tête"):
        agents.lire_fiche(d)
    d.write_text("---\nid: a\nnom: A\n---\ncorps", encoding="utf-8")
    with pytest.raises(ValueError, match="fonction"):
        agents.lire_fiche(d)
    d.write_text("---\nid: a\nnom: A\nfonction: f\noutils: [lire_page, date_du_jour]\nbudget_tours: 3\n---\ncorps", encoding="utf-8")
    f = agents.lire_fiche(d)
    assert f.outils == ["lire_page", "date_du_jour"] and f.budget_tours == 3 and f.consignes == "corps"
    (tmp_path / "b").mkdir()
    Path(tmp_path / "b" / "agent.md").write_text("---\nid: a\nnom: B\nfonction: f\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="double"):
        agents.charger(tmp_path)

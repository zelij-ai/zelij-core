"""La porte du fondateur : paquet complet ou rien, consigne obligatoire pour « à modifier », journal sur chaque geste."""
import pytest

from core import db, gouvernance
from core.schema import migrer


def _org(c):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Test SAS", db.maintenant()))
    return oid


def _paquet(**k):
    base = dict(demandeur="Camille Aubert (chef-de-cabinet), cheffe de cabinet", objectif="Ouvrir une page Tarifs", proposition="Une page avec trois offres",
                options=["Publier maintenant", "Attendre le pilote", "Ne rien faire"], recommandation="Publier maintenant", reversibilite="reversible")
    base.update(k)
    return gouvernance.Paquet(**base)


def test_un_paquet_incomplet_ne_s_ouvre_pas():
    migrer()
    assert gouvernance.Paquet(demandeur="x", objectif="").valider() == ["objectif", "proposition", "au moins deux options", "recommandation"]
    assert _paquet(reversibilite="irreversible").valider() == ["retour arrière (obligatoire dès que ce n'est pas réversible)"]
    assert _paquet(reversibilite="bizarre", retour_arriere=["x"]).valider() == ["réversibilité (reversible, partielle, irreversible)"]
    with db.connexion() as c:
        oid = _org(c)
        with pytest.raises(ValueError):
            gouvernance.ouvrir(c, oid, _paquet(options=["une seule"]))


def test_engage_dit_pourquoi_la_decision_revient_au_fondateur():
    assert gouvernance.engage(_paquet()) == []
    motifs = gouvernance.engage(_paquet(impact_eur=120, reversibilite="irreversible", retour_arriere=["revert"]), exposition_publique=True, suppression=True)
    assert len(motifs) == 4 and motifs[0].startswith("engage de l'argent (120.00 €)")


def test_decider_approuve_refuse_et_exige_une_consigne():
    migrer()
    with db.connexion() as c:
        oid = _org(c)
        d1 = gouvernance.ouvrir(c, oid, _paquet())
        d2 = gouvernance.ouvrir(c, oid, _paquet(objectif="Acheter un domaine", impact_eur=12))
        d3 = gouvernance.ouvrir(c, oid, _paquet(objectif="Lettre mensuelle"))
        assert [d["objectif"] for d in gouvernance.en_attente(c, oid)] == ["Ouvrir une page Tarifs", "Acheter un domaine", "Lettre mensuelle"]
        with pytest.raises(ValueError, match="Dis ce que tu veux changer"):
            gouvernance.decider(c, oid, d3, "a_modifier", par="fondateur@test-sas.fr", consigne="  ")
        assert gouvernance.decider(c, oid, d1, "approuver", par="fondateur@test-sas.fr")["etat"] == "approuvee"
        assert gouvernance.decider(c, oid, d2, "refuser", par="fondateur@test-sas.fr")["etat"] == "refusee"
        r = gouvernance.decider(c, oid, d3, "a_modifier", par="fondateur@test-sas.fr", consigne="budget 50 € maximum")
        assert r["etat"] == "a_modifier" and r["consigne"] == "budget 50 € maximum"
        with pytest.raises(ValueError, match="déjà"):
            gouvernance.decider(c, oid, d1, "refuser", par="fondateur@test-sas.fr")
        with pytest.raises(LookupError):
            gouvernance.decider(c, oid, "inconnue", "approuver", par="x")
        with pytest.raises(ValueError, match="action"):
            gouvernance.decider(c, oid, d1, "bruler", par="x")
        actions = [j["action"] for j in c.lignes("SELECT action FROM journal WHERE org_id = ? ORDER BY cree_le", (oid,))]
        assert actions.count("decision.ouverte") == 3 and "decision.approuvee" in actions and "decision.refusee" in actions and "decision.a_modifier" in actions
        assert gouvernance.en_attente(c, oid) == [] and len(gouvernance.recentes(c, oid)) == 3


def test_depuis_sortie_agent_tolere_les_champs_manquants():
    p = gouvernance.depuis_sortie_agent("agent", {"objectif": "x", "options": "une", "impact_eur": "abc"})
    assert p.options == ["une"] and p.impact_eur == 0.0 and "proposition" in p.valider()

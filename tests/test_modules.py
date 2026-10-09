"""Modules : interface stable, manifeste signé Ed25519 vérifié avant installation, refus explicites et journalisés."""
import json

from core import INTERFACE_MODULES, db, modules
from core.schema import migrer


def _manifeste(**k):
    base = dict(nom="cible-gcp", version="1.0.0", type="cible", interface=INTERFACE_MODULES, fournisseur="zelij.ai", description="Déploiement GCP",
                fichiers={"cible_gcp.py": "0" * 64})
    base.update(k)
    return modules.Manifeste(**base)


def test_signature_et_verification():
    priv, pub = modules.generer_cles()
    m = _manifeste()
    m.signature = modules.signer(m, priv)
    assert modules.verifier(m, pub) is True
    m2 = _manifeste(version="1.0.1", signature=m.signature)            # un champ change : la signature ne tient plus
    assert modules.verifier(m2, pub) is False
    assert modules.verifier(_manifeste(), pub) is False                  # pas de signature
    assert modules.verifier(m, "") is False and modules.verifier(m, "zz") is False
    _, autre_pub = modules.generer_cles()
    assert modules.verifier(m, autre_pub) is False                       # signé par quelqu'un d'autre


def test_compatibilite_d_interface_et_manifeste_fichier(tmp_path):
    assert modules.compatible(_manifeste(interface="1.7")) and not modules.compatible(_manifeste(interface="2.0"))
    chemin = tmp_path / "pack.json"
    chemin.write_text(json.dumps({"nom": "x", "version": "0.1", "type": "agent", "interface": "1.0", "fournisseur": "zelij.ai"}), encoding="utf-8")
    assert modules.charger_manifeste(chemin).type == "agent"
    chemin.write_text(json.dumps({"nom": "x", "version": "0.1", "type": "virus", "interface": "1.0", "fournisseur": "zelij.ai"}), encoding="utf-8")
    try:
        modules.charger_manifeste(chemin)
        raise AssertionError("type inconnu accepté")
    except ValueError:
        pass


def test_installation_refuse_sans_signature_et_journalise():
    migrer()
    priv, pub = modules.generer_cles()
    with db.connexion() as c:
        oid = db.nouvel_id()
        c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Mod SAS", db.maintenant()))
        r = modules.installer(c, oid, _manifeste(), par="fondateur", cle_publique_hex=pub)
        assert r["installe"] is False and "signature" in r["motif"]
        m = _manifeste()
        m.signature = modules.signer(m, priv)
        assert modules.installer(c, oid, m, par="fondateur", cle_publique_hex=pub)["installe"] is True
        m2 = _manifeste(version="1.1.0")
        m2.signature = modules.signer(m2, priv)
        modules.installer(c, oid, m2, par="fondateur", cle_publique_hex=pub)
        actifs = modules.installes(c, oid)
        assert [(a["nom"], a["version"]) for a in actifs] == [("cible-gcp", "1.1.0")]      # la version précédente est désactivée
        m3 = _manifeste(interface="2.0")
        m3.signature = modules.signer(m3, priv)
        assert "incompatible" in modules.installer(c, oid, m3, par="fondateur", cle_publique_hex=pub)["motif"]
        actions = [j["action"] for j in c.lignes("SELECT action FROM journal WHERE org_id = ? ORDER BY cree_le", (oid,))]
        assert actions == ["module.refuse", "module.installe", "module.installe", "module.refuse"]

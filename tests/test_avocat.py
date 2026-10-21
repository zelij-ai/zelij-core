"""L'avocat du diable (0.9.4) : plaide contre la recommandation, borné et vérifié ; rangé sur la décision ; compté dans le
plafond ; jamais bloquant ; retirable ; écrit d'avance en démonstration ; visible dans le bureau, en swipant et dans la poche."""
import json
from pathlib import Path
from types import SimpleNamespace

from core import avocat, db, gouvernance, passerelle, poche
from core.schema import migrer

ROOT = Path(__file__).resolve().parents[1]


def _reponse(texte: str, tokens_out: int = 150):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texte)], stop_reason="end_turn",
                           usage=SimpleNamespace(input_tokens=900, output_tokens=tokens_out, cache_read_input_tokens=0))


def _org(c):
    oid = db.nouvel_id()
    c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (oid, "Avocat SAS", db.maintenant()))
    return oid


def _paquet(**k):
    base = dict(demandeur="Camille Aubert (chef-de-cabinet), chef de cabinet", objectif="Acheter un second nom de domaine", proposition="exemple.fr pour 12 mois",
                options=["Acheter", "Attendre", "Ne rien faire"], recommandation="Acheter", reversibilite="reversible", impact_eur=14.9, risques=["aucun"])
    base.update(k)
    return gouvernance.Paquet(**base)


AVIS = {"objections": ["Le besoin n'est pas démontré.", "Le domaine actuel suffit.", "Le prix de renouvellement n'est pas écrit.", "Une quatrième, de trop"],
        "question": "Quel client a demandé ce nom ?", "bascule": "Un prospect qui le tape déjà.", "verdict": "attendre"}


def test_l_avis_est_borne_verifie_et_retrouve_meme_dans_de_la_prose():
    avis = avocat.depuis_texte("Voici mon avis :\n```json\n" + json.dumps(AVIS, ensure_ascii=False) + "\n```")
    assert avis["objections"] == AVIS["objections"][:3] and avis["verdict"] == "attendre" and avis["question"].startswith("Quel client")
    assert avocat.depuis_texte("je ne sais pas") is None and avocat.depuis_texte('{"objections": []}') is None
    assert avocat.depuis_texte('{"objections": ["x"], "verdict": "brûler"}')["verdict"] == "attendre"      # verdict inconnu → attendre
    assert avocat.lire("pas du json") is None and avocat.lire("") is None
    texte = avocat.requisitoire({"objectif": "A", "proposition": "B", "options": ["x", "y"], "recommandation": "x", "impact_eur": 3, "tache": "secret"})
    assert "Recommandation de l'agent : x" in texte and "secret" not in texte                                # la tâche d'exécution n'est pas plaidée
    assert "plaider CONTRE" in avocat.SYSTEM and "aucune adresse web" in avocat.SYSTEM and "n'inventes aucun fait" in avocat.SYSTEM


def test_plaide_range_l_avis_le_compte_et_ne_bloque_jamais(monkeypatch):
    migrer()
    monkeypatch.delenv("AVOCAT_DU_DIABLE", raising=False)
    monkeypatch.delenv("CORE_DEMO", raising=False)
    appels = []

    def appel(**k):
        appels.append(k)
        return _reponse(json.dumps(AVIS, ensure_ascii=False))

    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        from dataclasses import asdict

        avis = avocat.plaider_decision(c, oid, did, asdict(_paquet()), appel=appel)
        assert avis["verdict"] == "attendre" and avis["modele"] == avocat.modele()
        assert appels[0]["tools"] is None and appels[0]["max_tokens"] == 700 and "Acheter un second nom de domaine" in appels[0]["messages"][0]["content"]
        d = gouvernance.lire(c, oid, did)
        assert d["avocat"]["objections"][0] == "Le besoin n'est pas démontré." and len(d["avocat"]["objections"]) == 3
        assert gouvernance.en_attente(c, oid)[0]["avocat"]["verdict"] == "attendre"
        assert passerelle.cout_du_mois_eur(c, oid, db.mois_courant()) > 0                                    # compté dans le plafond
        assert any(r["action"] == "decision.avocat" for r in c.lignes("SELECT action FROM journal WHERE cible = ?", (did,)))

        # un modèle muet ou en panne : pas d'avis, pas d'erreur, la décision attend quand même
        did2 = gouvernance.ouvrir(c, oid, _paquet(objectif="Autre"))
        assert avocat.plaider_decision(c, oid, did2, asdict(_paquet()), appel=lambda **k: _reponse("…")) is None
        assert gouvernance.lire(c, oid, did2)["avocat"] is None

        def panne(**k):
            raise RuntimeError("réseau")

        assert avocat.plaider_decision(c, oid, did2, asdict(_paquet()), appel=panne) is None
        assert any(r["action"] == "decision.avocat.echec" for r in c.lignes("SELECT action FROM journal WHERE cible = ?", (did2,)))

        # retirable, et respectueux du plafond
        monkeypatch.setenv("AVOCAT_DU_DIABLE", "0")
        assert avocat.plaider_decision(c, oid, did2, asdict(_paquet()), appel=appel) is None and len(appels) == 1
        monkeypatch.setenv("AVOCAT_DU_DIABLE", "1")
        monkeypatch.setenv("PLAFOND_MENSUEL_EUR", "0")
        assert avocat.plaider_decision(c, oid, did2, asdict(_paquet()), appel=appel) is None and len(appels) == 1
        assert any(r["action"] == "decision.avocat.plafond" for r in c.lignes("SELECT action FROM journal WHERE cible = ?", (did2,)))


def test_en_demonstration_un_avis_ecrit_d_avance_et_rien_ne_sort(monkeypatch):
    migrer()
    monkeypatch.setenv("CORE_DEMO", "1")
    monkeypatch.delenv("AVOCAT_DU_DIABLE", raising=False)

    def jamais(**k):
        raise AssertionError("aucun appel en démonstration")

    with db.connexion() as c:
        oid = _org(c)
        did = gouvernance.ouvrir(c, oid, _paquet())
        from dataclasses import asdict

        avis = avocat.plaider_decision(c, oid, did, asdict(_paquet()), appel=jamais)
        assert avis["modele"] == "démonstration" and avis["objections"] == avocat.AVIS_DEMO["objections"]
        assert gouvernance.lire(c, oid, did)["avocat_cout_usd"] == 0
    src = (ROOT / "core/demo.py").read_text(encoding="utf-8")
    assert "_avocat.enregistrer(c, org, d[\"id\"], dict(_avocat.AVIS_DEMO" in src


def test_visible_dans_le_bureau_en_swipant_et_dans_la_poche():
    d = {"objectif": "Acheter", "demandeur": "Camille", "proposition": "exemple.fr", "options": ["Acheter", "Attendre"], "recommandation": "Acheter",
         "reversibilite": "reversible", "impact_eur": 14.9, "avocat": dict(AVIS, objections=AVIS["objections"][:3])}
    texte = poche.texte_decision(d)
    assert "L'avocat du diable plaide contre la recommandation (verdict : attendre)" in texte and "- Le besoin n'est pas démontré." in texte
    assert "À demander avant d'approuver : Quel client a demandé ce nom ?" in texte
    for gabarit, marque in (("bureau.html", 'class="avocat avocat--{{ d.avocat.verdict }}"'), ("decider.html", "avocat-chip--{{ d.avocat.verdict }}"),
                            ("poche.html", "L'avocat du diable ({{ d.avocat.verdict }})")):
        assert marque in (ROOT / "core/bureau/templates" / gabarit).read_text(encoding="utf-8"), gabarit
    assert ".avocat--refuser" in (ROOT / "core/bureau/static/app.css").read_text(encoding="utf-8")
    app = (ROOT / "core/bureau/app.py").read_text(encoding="utf-8")
    assert "_avocat.plaider_decision(c, org_id, did, _asdict(paquet))" in app and app.index("_avocat.plaider_decision") < app.index("poche.prevenir(c, org_id, did)")
    assert "AVOCAT_DU_DIABLE" in (ROOT / ".env.example").read_text(encoding="utf-8")
    from core import VERSION

    assert tuple(int(x) for x in VERSION.split(".")) >= (0, 9, 4)
    assert "## 0.9.4" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") and "## L'avocat du diable" in (ROOT / "docs/MODE-D-EMPLOI.md").read_text(encoding="utf-8")

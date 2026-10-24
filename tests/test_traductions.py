"""Le README dans 23 langues (CEO 24/10/2026) : un fichier par langue, la même barre de langues partout, les mêmes repères
(image de l'aquarium, démo, clé publique, licence, « by zelij.ai »), les guides anglais pour les langues autres que le français."""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
import barre_langues as bl  # noqa: E402

REPERES = ("docs/img/aquarium.gif", "docker-compose.demo.yml", "http://localhost:8000", "8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a",
           "ZELIJ_CLE_PUBLIQUE", "tests/test_securite.py", "securite@zelij.ai", "scripts/controle_publication.py", "AGPL", "portraits/README.md",
           "by zelij.ai — https://zelij.ai/", "Camille Aubert", "Sacha Ferrand")


def test_vingt_trois_langues_et_la_meme_barre_partout():
    assert len(bl.LANGUES) == 23 and len({c for c, _ in bl.LANGUES}) == 23
    assert bl.appliquer(RACINE, verifier=True) == []           # python scripts/barre_langues.py remet la barre d'aplomb
    for code, libelle in bl.LANGUES:
        texte = (RACINE / bl.fichier(code)).read_text(encoding="utf-8")
        lignes = texte.split("\n")
        assert lignes[0] == "# Zelij Core" and f"**{libelle}**" in lignes[2] and lignes[2].count(" · ") == 22, code
        for autre, autre_libelle in bl.LANGUES:
            if autre != code:
                assert f"[{autre_libelle}]({bl.fichier(autre)})" in lignes[2], (code, autre)
        for repere in REPERES:
            assert repere in texte, (code, repere)
        assert len(texte) > 3500, code   # le chinois tient en moins de caractères
        guides = ("docs/INSTALLATION.md", "docs/MODE-D-EMPLOI.md") if code == "fr" else ("docs/INSTALLATION.en.md", "docs/MODE-D-EMPLOI.en.md")
        for g in guides:
            assert g in texte, (code, g)
        assert "<!-- langues -->" not in texte, code


def test_la_barre_est_deterministe():
    assert bl.barre("fr").startswith("[English](README.en.md) · ") and "**Français**" in bl.barre("fr")
    assert bl.barre("en").startswith("**English** · [简体中文](README.zh-CN.md)") and bl.barre("en").endswith("[Română](README.ro.md)")

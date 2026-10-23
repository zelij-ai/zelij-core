"""Frugal par construction (0.9.5) : l'échelle et les deux règles sont dans les règles de la maison de tous les agents."""
from pathlib import Path

from core import VERSION, executeur

ROOT = Path(__file__).resolve().parents[1]


def test_les_regles_de_frugalite_sont_dans_la_maison():
    r = executeur.REGLES_MAISON
    assert "7. Frugalité" in r and "8. Toute logique à risque" in r
    for marche in executeur.FRUGALITE:
        assert marche in r, marche
    assert "Jamais au détriment de la validation, des erreurs, de la sécurité ou de l'accessibilité" in r
    assert "ce que tu n'as pas vérifié" in r and "« raccourci : »" in r
    assert "Paresseux sur la solution, jamais sur la lecture" in r
    assert "## Frugal par construction" in (ROOT / "docs/MODE-D-EMPLOI.md").read_text(encoding="utf-8")
    assert "## 0.9.5" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") and tuple(int(x) for x in VERSION.split(".")) >= (0, 9, 5)

"""La barre de langues des README : une ligne identique dans les 23 fichiers, la langue courante en gras, les autres en lien.
`python scripts/barre_langues.py` réécrit la ligne 3 de chaque README ; `--verifier` dit seulement lesquelles sont à corriger."""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# (code de fichier, libellé affiché) dans l'ordre d'affichage ; README.md est le français
LANGUES: tuple[tuple[str, str], ...] = (
    ("en", "English"), ("zh-CN", "简体中文"), ("zh-TW", "繁體中文"), ("ja", "日本語"), ("ko", "한국어"), ("tr", "Türkçe"),
    ("ru", "Русский"), ("vi", "Tiếng Việt"), ("th", "ไทย"), ("de", "Deutsch"), ("es", "Español"), ("fr", "Français"),
    ("uk", "Українська"), ("pl", "Polski"), ("pt-BR", "Português (Brasil)"), ("ar", "العربية"), ("fa", "فارسی"),
    ("id", "Bahasa Indonesia"), ("it", "Italiano"), ("el", "Ελληνικά"), ("ml", "മലയാളം"), ("ur", "Roman Urdu"), ("ro", "Română"),
)


def fichier(code: str) -> str:
    return "README.md" if code == "fr" else f"README.{code}.md"


def barre(courante: str) -> str:
    return " · ".join(f"**{libelle}**" if code == courante else f"[{libelle}]({fichier(code)})" for code, libelle in LANGUES)


def appliquer(racine: Path = RACINE, *, verifier: bool = False) -> list[str]:
    """Rend les fichiers dont la ligne 3 a été (ou devrait être) réécrite ; la ligne 1 doit être le titre, la ligne 2 vide."""
    changes = []
    for code, _ in LANGUES:
        p = racine / fichier(code)
        lignes = p.read_text(encoding="utf-8").split("\n")
        assert lignes[0].startswith("# ") and lignes[1] == "", p
        attendu = barre(code)
        if lignes[2] != attendu:
            changes.append(p.name)
            if not verifier:
                lignes[2] = attendu
                p.write_text("\n".join(lignes), encoding="utf-8")
    return changes


if __name__ == "__main__":
    verif = "--verifier" in sys.argv
    racine = Path(sys.argv[sys.argv.index("--racine") + 1]).resolve() if "--racine" in sys.argv else RACINE
    changes = appliquer(racine, verifier=verif)
    print(("à corriger" if verif else "réécrits") + " : " + (", ".join(changes) if changes else "aucun"))
    sys.exit(1 if (verif and changes) else 0)

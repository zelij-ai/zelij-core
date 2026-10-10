"""Base SQLite temporaire, aucun e-mail, aucun appel réel au modèle."""
import os
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="zelij-core-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP, 'test.sqlite').as_posix()}"
os.environ["APP_ORIGIN"] = "http://testserver"
os.environ.pop("SMTP_HOST", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("FONDATEUR_EMAIL", None)
os.environ["PLAFOND_MENSUEL_EUR"] = "50"


import pytest


@pytest.fixture(autouse=True)
def _freins_remis_a_zero(monkeypatch):
    """Les freins (par adresse, par IP, global) sont en mémoire : chaque test repart de zéro. Les tests partagent une base
    et y créent chacun leur organisation : la règle « une installation, une organisation » est levée ici, et vérifiée à part
    (tests/test_audit_074.py la rétablit)."""
    from core.bureau import connexion as cx

    cx._demandes.clear()
    monkeypatch.setattr(cx, "UNE_SEULE_ORGANISATION", False)

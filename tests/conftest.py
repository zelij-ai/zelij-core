"""Base SQLite temporaire, aucun e-mail, aucun appel réel au modèle."""
import os
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="zelij-core-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP, 'test.sqlite').as_posix()}"
os.environ["APP_ORIGIN"] = "http://testserver"
os.environ.pop("SMTP_HOST", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["PLAFOND_MENSUEL_EUR"] = "50"


import pytest


@pytest.fixture(autouse=True)
def _freins_remis_a_zero():
    """Les freins (par adresse, par IP, global) sont en mémoire : chaque test repart de zéro."""
    from core.bureau import connexion as cx

    cx._demandes.clear()

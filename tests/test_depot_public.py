"""Dépôt public prêt à accueillir (lot 2) et à distribuer (lot 3) : fichiers d'accueil, gabarits, CI, version, image."""
import re
from pathlib import Path

from core import VERSION

RACINE = Path(__file__).resolve().parents[1]


def _lire(chemin: str) -> str:
    return (RACINE / chemin).read_text(encoding="utf-8")


def test_fichiers_d_accueil_des_contributeurs():
    securite = _lire("SECURITY.md")
    assert "securite@zelij.ai" in securite and "tests/test_securite.py" in securite and "pip-audit" in securite
    contrib = _lire("CONTRIBUTING.md")
    assert "gratuit pour vous, à vie" in contrib and "Un test par changement" in contrib and "AGPL-3.0" in contrib
    assert "le fondateur décide" in contrib
    assert "securite@zelij.ai" in _lire("CODE_OF_CONDUCT.md")
    for gabarit in (".github/ISSUE_TEMPLATE/bogue.yml", ".github/ISSUE_TEMPLATE/proposition.yml", ".github/ISSUE_TEMPLATE/config.yml", ".github/PULL_REQUEST_TEMPLATE.md"):
        assert (RACINE / gabarit).is_file(), gabarit
    assert "blank_issues_enabled: false" in _lire(".github/ISSUE_TEMPLATE/config.yml")
    assert "controle_publication" in _lire(".github/PULL_REQUEST_TEMPLATE.md")


def test_ci_execute_toutes_les_verifications():
    ci = _lire(".github/workflows/ci.yml")
    for etape in ("python -m pytest -q", "pyflakes core scripts tests", "pip-audit -r requirements.txt", "bandit -q -r core scripts -ll",
                  "python scripts/controle_publication.py", "docker build", "/healthz"):
        assert etape in ci, etape
    assert "permissions:\n  contents: read" in ci
    assert "pull_request:" in ci and "branches: [main]" in ci


def test_version_publie_image_et_archive_en_accord_avec_le_code():
    rel = _lire(".github/workflows/release.yml")
    assert 'tags: ["v*.*.*"]' in rel and "uses: ./.github/workflows/ci.yml" in rel
    assert "ghcr.io/${{ github.repository }}:${{ github.ref_name }}" in rel and "core.VERSION" in rel
    assert "softprops/action-gh-release" in rel and "CHANGELOG.md" in rel
    # ci.yml est appelable par release.yml
    assert "workflow_call:" in _lire(".github/workflows/ci.yml")
    image = _lire("docker-compose.image.yml")
    assert "ghcr.io/zelij-ai/zelij-core:${CORE_IMAGE_TAG:-latest}" in image and "build: !reset null" in image
    changelog = _lire("CHANGELOG.md")
    assert changelog.startswith("# Journal des versions") and f"## {VERSION} " in changelog, f"CHANGELOG sans entrée pour {VERSION}"
    assert re.match(r"\d+\.\d+\.\d+$", VERSION)
    readme = _lire("README.md")
    assert "docker-compose.image.yml" in readme and "CHANGELOG.md" in readme and "CONTRIBUTING.md" in readme
    assert "docker-compose.image.yml" in _lire("docs/INSTALLATION.md") and "docker-compose.image.yml" in _lire("docs/INSTALLATION.en.md")

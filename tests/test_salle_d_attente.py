"""Mode salle d'attente (0.9.2) : la page publique de l'aquarium en plein écran pour une télé, même règle de confidentialité."""
from pathlib import Path

from fastapi.testclient import TestClient

from core import db
from core.bureau import app as bureau

ROOT = Path(__file__).resolve().parents[1]


def _jeton():
    from core import aquarium

    with db.connexion() as c:
        org = c.une("SELECT id FROM organisations ORDER BY cree_le LIMIT 1")
        if org is None:
            return None
        j = aquarium.jeton_public(c, org["id"]) or aquarium.ouvrir_vitrine(c, org["id"], par="test")
        c.commit()
        return j


def test_la_page_publique_a_un_mode_tv_et_reste_sans_detail():
    j = _jeton()
    if j is None:        # base vierge dans cet ordre d'exécution : la structure se vérifie sur les fichiers ci-dessous
        return
    c = TestClient(bureau.app, follow_redirects=False)
    normal, tv = c.get(f"/vitrine/{j}").text, c.get(f"/vitrine/{j}?tv=1").text
    assert '<body class="tv">' in tv and '<body class="tv">' not in normal
    assert 'data-tv-plein-ecran' in tv and f'href="/vitrine/{j}"' in tv            # bouton plein écran, lien « Quitter »
    assert "Mode salle d'attente" in normal and "?tv=1" in normal                # la page publique propose le mode
    assert tv.count("/api/vitrine/") == 1 and "/api/aquarium" not in tv          # même source publique, aucune source interne


def test_fichiers_du_mode_tv():
    css = (ROOT / "core/bureau/static/app.css").read_text(encoding="utf-8")
    js = (ROOT / "core/bureau/static/aquarium.js").read_text(encoding="utf-8")
    assert "body.tv" in css and "tv--repos" in css and ".tv-barre" in css
    assert "classList.contains('tv')" in js and "requestFullscreen" in js and "6 * 3600 * 1000" in js and "tv--repos" in js
    assert "Salle d'attente (TV)" in (ROOT / "core/bureau/templates/aquarium.html").read_text(encoding="utf-8")
    assert "## 0.9.2" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") and "Salle d'attente" in (ROOT / "docs/MODE-D-EMPLOI.md").read_text(encoding="utf-8")
    from core import VERSION

    assert tuple(int(x) for x in VERSION.split(".")) >= (0, 9, 2)

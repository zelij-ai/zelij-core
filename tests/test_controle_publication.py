"""Rien d'interne ne sort : le contrôle de publication passe sur le dépôt lui-même et attrape ce qu'il doit attraper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import controle_publication as cp  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]


def test_le_depot_passe_le_controle():
    constats = cp.controler(RACINE, interdits_prives=[])
    assert constats == [], "\n".join(constats)


def test_le_controle_attrape_les_motifs(tmp_path):
    # Les échantillons sont assemblés à l'exécution : le contrôle, qui lit aussi ce fichier, ne doit pas les y trouver en clair.
    cle = "sk-ant-" + "api03-ABCDEFGHIJKLMNOP"
    ip = ".".join(["203", "0", "113", "9"])
    code = "A" + "27"
    courriel = "someone@" + "gmail.com"
    (tmp_path / "a.py").write_text(f"cle = '{cle}'\nhote = '{ip}'\nagent = '{code}'\n", encoding="utf-8")
    (tmp_path / "b.md").write_text(f"Contact : {courriel} — client Dupont\npassword = 'secret123'\n", encoding="utf-8")
    (tmp_path / "c.txt").write_text("boucle locale 127.0.0.1 ok\n", encoding="utf-8")
    constats = cp.controler(tmp_path, interdits_prives=["Dupont"])
    libelles = " | ".join(constats)
    for attendu in ("clé d'API Anthropic", "adresse IPv4", "code d'agent", "adresse e-mail personnelle", "mot de passe en clair", "terme privé interdit (Dupont)"):
        assert attendu in libelles, attendu
    assert "127.0.0.1" not in libelles


def test_liste_privee_lue_depuis_l_environnement(tmp_path, monkeypatch):
    f = tmp_path / "interdits.txt"
    f.write_text("# commentaire\nNomSecret\n\n", encoding="utf-8")
    monkeypatch.setenv("ZELIJ_CORE_INTERDITS", str(f))
    assert cp.charger_interdits_prives() == ["NomSecret"]
    monkeypatch.setenv("ZELIJ_CORE_INTERDITS", str(tmp_path / "absent.txt"))
    assert cp.charger_interdits_prives() == []

"""Mode d'emploi complet et portraits (CEO 09/10) : guides présents et cohérents avec la configuration, mise en https par
docker-compose.tls.yml, photos du fondateur et des agents servies depuis portraits/ avec silhouette de repli."""
import re
from pathlib import Path

from fastapi.testclient import TestClient

from core.bureau import app as bureau

RACINE = Path(__file__).resolve().parents[1]


def test_guides_presents_et_coherents_avec_la_configuration():
    env = (RACINE / ".env.example").read_text(encoding="utf-8")
    for nom in ("docs/INSTALLATION.md", "docs/INSTALLATION.en.md", "docs/MODE-D-EMPLOI.md", "docs/MODE-D-EMPLOI.en.md", "portraits/README.md"):
        texte = (RACINE / nom).read_text(encoding="utf-8")
        assert len(texte) > (800 if nom.endswith("README.md") else 1500), nom
        ips = set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", texte)) - {"127.0.0.1", ".".join(["0"] * 4)}
        assert not ips, (nom, ips)                                                    # aucune adresse IP dans la documentation publique
    install = (RACINE / "docs" / "INSTALLATION.md").read_text(encoding="utf-8")
    for variable in ("ANTHROPIC_API_KEY", "PLAFOND_MENSUEL_EUR", "CORE_DB_PASSWORD", "SECRET_KEY", "APP_ORIGIN", "SMTP_HOST", "CORE_DOMAINE", "ZELIJ_CLE_PUBLIQUE", "SSH_CLE_HOTE", "SITE_DEPOT"):
        assert variable in install and variable in env, variable
    assert "docker-compose.tls.yml" in install and "portraits/" in install and "Dépannage" in install
    readme = (RACINE / "README.md").read_text(encoding="utf-8")
    assert "docs/INSTALLATION.md" in readme and "docs/MODE-D-EMPLOI.md" in readme and "portraits/README.md" in readme
    readme_en = (RACINE / "README.en.md").read_text(encoding="utf-8")
    assert "docs/INSTALLATION.en.md" in readme_en and "docs/MODE-D-EMPLOI.en.md" in readme_en


def test_mise_en_https_par_caddy():
    tls = (RACINE / "docker-compose.tls.yml").read_text(encoding="utf-8")
    assert "image: caddy:2-alpine" in tls and "CORE_DOMAINE" in tls and '"443:443"' in tls and "ports: !reset []" in tls
    assert "./infra/Caddyfile:/etc/caddy/Caddyfile:ro" in tls
    caddy = (RACINE / "infra" / "Caddyfile").read_text(encoding="utf-8")
    assert "{$CORE_DOMAINE}" in caddy and "reverse_proxy core-app:8000" in caddy and "X-Forwarded-Proto" in caddy
    compose = (RACINE / "docker-compose.yml").read_text(encoding="utf-8")
    assert "./portraits:/srv/app/portraits:ro" in compose
    assert "COPY --chown=core:core portraits ./portraits" in (RACINE / "Dockerfile").read_text(encoding="utf-8")


def test_portraits_fondateur_et_agents(tmp_path, monkeypatch):
    client = TestClient(bureau.app)
    # silhouette fournie dans le dépôt, servie sans connexion (la vitrine publique l'affiche)
    r = client.get("/portraits/fondateur")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml") and b"<svg" in r.content
    assert client.get("/portraits/inconnu").status_code == 404 and client.get("/portraits/..%2Ffondateur").status_code == 404
    # 12/10 : chaque agent de l'édition arrive avec le portrait d'un personnage fictif (agents/<id>/portrait.webp)
    r = client.get("/agents/chef-de-cabinet/portrait")
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp" and r.content[:4] == b"RIFF"
    # une photo déposée dans portraits/ prend le pas sur la silhouette du fondateur ET sur le portrait livré d'un agent
    monkeypatch.setattr(bureau, "PORTRAITS", tmp_path)
    (tmp_path / "fondateur.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    (tmp_path / "fondateur.png").write_bytes(b"\x89PNG\r\n\x1a\nfaux")
    (tmp_path / "chef-de-cabinet.webp").write_bytes(b"RIFFfaux")
    r = client.get("/portraits/fondateur")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.headers["cache-control"] == "public, max-age=300"
    r = client.get("/agents/chef-de-cabinet/portrait")
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp" and r.content == b"RIFFfaux"
    assert client.get("/agents/croissance/portrait").status_code == 200 and client.get("/agents/inconnu/portrait").status_code == 404
    # l'en-tête du bureau et l'aquarium vont chercher le portrait du fondateur
    assert 'src="/portraits/fondateur' in (RACINE / "core" / "bureau" / "templates" / "base.html").read_text(encoding="utf-8")
    assert "'/portraits/fondateur'" in (RACINE / "core" / "bureau" / "static" / "aquarium.js").read_text(encoding="utf-8")
    assert (RACINE / "portraits" / "fondateur.svg").is_file() and (RACINE / "portraits" / "agent.svg").is_file()

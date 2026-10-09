"""Le dépôt du site, vu par le Bâtisseur : lire, lister, proposer. Un seul dépôt (SITE_DEPOT), un jeton restreint à ce dépôt
(GITHUB_TOKEN), jamais la branche principale : chaque proposition est une branche `batisseur/…` et une demande de fusion,
passée par la porte de sécurité. Le Bâtisseur ne fusionne pas, et ne touche jamais à ce bureau."""
from __future__ import annotations

import base64
import os
import re

import httpx

from core import porte_securite

_API = "https://api.github.com"
_TIMEOUT = httpx.Timeout(40.0)


def configuration() -> dict | None:
    depot, jeton = os.environ.get("SITE_DEPOT", "").strip(), os.environ.get("GITHUB_TOKEN", "").strip()
    if depot and jeton and "/" in depot:
        return {"depot": depot, "jeton": jeton}
    return None


def _h(conf: dict) -> dict:
    return {"Authorization": f"Bearer {conf['jeton']}", "Accept": "application/vnd.github+json", "User-Agent": "zelij-core-batisseur"}


def _branche_principale(client: httpx.Client, conf: dict) -> tuple[str, str] | None:
    r = client.get(f"{_API}/repos/{conf['depot']}", headers=_h(conf))
    if r.status_code != 200:
        return None
    principale = r.json().get("default_branch") or "main"
    r = client.get(f"{_API}/repos/{conf['depot']}/git/ref/heads/{principale}", headers=_h(conf))
    if r.status_code != 200:
        return None
    return principale, r.json()["object"]["sha"]


def lire(chemin: str, *, client: httpx.Client | None = None) -> dict:
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "dépôt non configuré (SITE_DEPOT, GITHUB_TOKEN)"}
    sur = porte_securite._chemin_sur(chemin)
    if sur is None:
        return {"ok": False, "detail": "chemin refusé"}
    propre = client is None
    client = client or httpx.Client(timeout=_TIMEOUT)
    try:
        r = client.get(f"{_API}/repos/{conf['depot']}/contents/{sur}", headers=_h(conf))
        if r.status_code == 404:
            return {"ok": False, "detail": "fichier absent"}
        if r.status_code != 200:
            return {"ok": False, "detail": f"GitHub a répondu {r.status_code}"}
        d = r.json()
        if isinstance(d, list):
            return {"ok": True, "dossier": True, "entrees": [{"nom": x.get("name"), "type": x.get("type"), "taille": x.get("size")} for x in d][:200]}
        if d.get("encoding") == "base64" and d.get("size", 0) <= 200_000:
            return {"ok": True, "chemin": sur, "contenu": base64.b64decode(d["content"]).decode("utf-8", errors="replace"), "sha": d.get("sha")}
        return {"ok": False, "detail": "fichier trop volumineux ou binaire"}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return {"ok": False, "detail": f"GitHub injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()


def proposer(fichiers: dict[str, str], *, titre: str, description: str, par: str, client: httpx.Client | None = None) -> dict:
    """Passe la porte de sécurité (diff, secrets, fichiers interdits, dépendances si touchées), puis ouvre la demande de fusion."""
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "dépôt non configuré (SITE_DEPOT, GITHUB_TOKEN)"}
    if not fichiers or not isinstance(fichiers, dict):
        return {"ok": False, "detail": "aucun fichier proposé"}
    if len(fichiers) > 12:
        return {"ok": False, "detail": "au plus douze fichiers par proposition"}
    propre = client is None
    client = client or httpx.Client(timeout=_TIMEOUT)
    try:
        existants: dict[str, str] = {}
        shas: dict[str, str] = {}
        for chemin in fichiers:
            sur = porte_securite._chemin_sur(chemin)
            if sur is None:
                continue
            actuel = lire(sur, client=client)
            if actuel.get("ok") and not actuel.get("dossier"):
                existants[sur] = actuel["contenu"]
                shas[sur] = actuel.get("sha", "")
        porte = porte_securite.controler_diff(fichiers, existants)
        if not porte["ok"]:
            return {"ok": False, "detail": "porte de sécurité : " + " ; ".join(porte["constats"][:6]), "porte": porte}
        audits = []
        for chemin, contenu in fichiers.items():
            nom = chemin.rsplit("/", 1)[-1]
            if nom == "requirements.txt":
                audits.append(porte_securite.audit_osv(porte_securite.paquets_requirements(contenu), "PyPI", client=client))
            elif nom == "package-lock.json":
                audits.append(porte_securite.audit_osv(porte_securite.paquets_package_lock(contenu), "npm", client=client))
        for a in audits:
            if a["vulnerables"]:
                return {"ok": False, "detail": "porte de sécurité : dépendances vulnérables " + ", ".join(f"{v['paquet']} {v['version']} ({', '.join(v['avis'])})" for v in a["vulnerables"][:4])}
            if a["erreur"]:
                return {"ok": False, "detail": f"porte de sécurité : audit des dépendances impossible ({a['erreur']}) ; proposition retenue"}
        base = _branche_principale(client, conf)
        if base is None:
            return {"ok": False, "detail": "dépôt ou branche principale inaccessible : jeton restreint à ce dépôt ?"}
        principale, sha = base
        slug = re.sub(r"[^a-z0-9]+", "-", (titre or "proposition").lower()).strip("-")[:40] or "proposition"
        import secrets

        branche = f"batisseur/{slug}-{secrets.token_hex(3)}"
        r = client.post(f"{_API}/repos/{conf['depot']}/git/refs", headers=_h(conf), json={"ref": f"refs/heads/{branche}", "sha": sha})
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"création de branche refusée ({r.status_code})"}
        for chemin, contenu in fichiers.items():
            sur = porte_securite._chemin_sur(chemin)
            charge = {"message": f"{titre[:72]} — {sur}", "branch": branche, "content": base64.b64encode(contenu.encode("utf-8")).decode()}
            if shas.get(sur):
                charge["sha"] = shas[sur]
            r = client.put(f"{_API}/repos/{conf['depot']}/contents/{sur}", headers=_h(conf), json=charge)
            if r.status_code not in (200, 201):
                return {"ok": False, "detail": f"écriture de {sur} refusée ({r.status_code})"}
        corps = (f"{description}\n\n---\nProposé par {par} dans les limites du Bâtisseur : {porte['lignes']} ligne(s) changée(s), "
                 f"{len(fichiers)} fichier(s), porte de sécurité passée. Rien n'est en ligne tant que cette demande n'est pas fusionnée par le fondateur.")
        r = client.post(f"{_API}/repos/{conf['depot']}/pulls", headers=_h(conf), json={"title": titre[:90], "head": branche, "base": principale, "body": corps})
        if r.status_code not in (200, 201):
            return {"ok": False, "detail": f"demande de fusion refusée ({r.status_code})"}
        return {"ok": True, "url": r.json().get("html_url", ""), "numero": r.json().get("number"), "lignes": porte["lignes"],
                "detail": f"demande de fusion n° {r.json().get('number')} ouverte sur {conf['depot']} ({porte['lignes']} ligne(s))"}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return {"ok": False, "detail": f"GitHub injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()


def archive_principale(*, client: httpx.Client | None = None) -> dict:
    """L'archive tar.gz de la branche principale, pour la mise en ligne : sha + octets."""
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "dépôt non configuré"}
    propre = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(120.0), follow_redirects=True)
    try:
        base = _branche_principale(client, conf)
        if base is None:
            return {"ok": False, "detail": "dépôt inaccessible"}
        principale, sha = base
        r = client.get(f"{_API}/repos/{conf['depot']}/tarball/{sha}", headers=_h(conf))
        if r.status_code != 200:
            return {"ok": False, "detail": f"archive indisponible ({r.status_code})"}
        return {"ok": True, "sha": sha, "branche": principale, "octets": r.content}
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"GitHub injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()

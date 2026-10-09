"""Porte de sécurité déterministe (gratuite, sans tokens) : ce qui doit être vrai avant qu'une proposition de code parte ou
qu'une mise en ligne se fasse. Pas une opinion : des règles. Secrets et motifs interdits dans le diff, fichiers interdits
(nouveau service, infrastructure), taille du diff, dépendances connues vulnérables (base OSV, requête réseau, sans rien
installer), en-têtes de sécurité et certificat à l'arrivée. Un rouge bloque ; le Bâtisseur corrige ou explique."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

import httpx

LIGNES_MAX = 300
OCTETS_MAX = 400_000
INTERDITS_CHEMINS = ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".env", ".github/workflows/", "systemd/", ".service", "Caddyfile", "nginx.conf")
EXTENSIONS_TEXTE = {".html", ".htm", ".css", ".js", ".mjs", ".json", ".md", ".txt", ".xml", ".svg", ".py", ".toml", ".yml", ".yaml", ".csv", ".webmanifest"}
MOTIFS_SECRETS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"), "clé d'API Anthropic"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"), "clé privée"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "jeton GitHub"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "clé AWS"),
    (re.compile(r"\b(sk|rk)_(live|test)_[A-Za-z0-9]{10,}\b"), "clé Stripe"),
    (re.compile(r"(password|mot_de_passe|passwd|secret)\s*[:=]\s*['\"][^'\"]{6,}['\"]", re.I), "mot de passe ou secret en clair"),
    (re.compile(r"<script[^>]+src=[\"']https?://(?!(?:cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com)/)", re.I), "script tiers chargé depuis un domaine inconnu"),
    (re.compile(r"<(?:iframe|embed|object)[^>]+(?:src|data)=[\"']https?://", re.I), "cadre ou objet tiers embarqué (iframe, embed, object)"),
    (re.compile(r"<link[^>]+href=[\"']https?://(?!(?:fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com)/)", re.I), "ressource tierce liée depuis un domaine inconnu"),
    (re.compile(r"\b(?:fetch|XMLHttpRequest|navigator\.sendBeacon|new WebSocket)\s*\(?\s*[\"']https?://", re.I), "appel réseau vers un domaine externe dans le code"),
    (re.compile(r"<form[^>]+action=[\"']https?://", re.I), "formulaire qui envoie vers un domaine externe"),
]
EN_TETES_ATTENDUS = ("strict-transport-security", "x-content-type-options", "content-security-policy", "referrer-policy")
OSV = "https://api.osv.dev/v1/querybatch"


def _chemin_sur(chemin: str) -> str | None:
    p = PurePosixPath((chemin or "").replace("\\", "/"))
    if not str(p) or p.is_absolute() or ".." in p.parts or str(p).startswith("."):
        return None
    return str(p)


def controler_diff(fichiers: dict[str, str], existants: dict[str, str] | None = None) -> dict:
    """Vérifie un lot de fichiers proposés (chemin → contenu). Retourne {ok, constats, lignes}."""
    existants = existants or {}
    constats: list[str] = []
    lignes = 0
    octets = 0
    for chemin, contenu in fichiers.items():
        sur = _chemin_sur(chemin)
        if sur is None:
            constats.append(f"{chemin} : chemin refusé (absolu, remontant ou caché)")
            continue
        nom = PurePosixPath(sur).name
        if any(sur.startswith(i) or sur.endswith(i) or nom == i for i in INTERDITS_CHEMINS):
            constats.append(f"{sur} : fichier d'infrastructure ou de service, hors périmètre du Bâtisseur")
        if PurePosixPath(sur).suffix.lower() not in EXTENSIONS_TEXTE:
            constats.append(f"{sur} : type de fichier non autorisé (texte seulement)")
        if not isinstance(contenu, str):
            constats.append(f"{sur} : contenu illisible")
            continue
        octets += len(contenu.encode("utf-8", errors="replace"))
        for motif, libelle in MOTIFS_SECRETS:
            if motif.search(contenu):
                constats.append(f"{sur} : {libelle}")
        avant = (existants.get(sur) or "").splitlines()
        apres = contenu.splitlines()
        lignes += _lignes_changees(avant, apres)
    if lignes > LIGNES_MAX:
        constats.append(f"diff de {lignes} lignes : plafond {LIGNES_MAX} (découper en plusieurs propositions)")
    if octets > OCTETS_MAX:
        constats.append(f"{octets} octets proposés : plafond {OCTETS_MAX}")
    return {"ok": not constats, "constats": constats, "lignes": lignes}


def _lignes_changees(avant: list[str], apres: list[str]) -> int:
    import difflib

    n = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, avant, apres, autojunk=False).get_opcodes():
        if op != "equal":
            n += max(i2 - i1, j2 - j1)
    return n


def paquets_requirements(texte: str) -> list[tuple[str, str]]:
    out = []
    for ligne in (texte or "").splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]*\])?==([A-Za-z0-9_.+-]+)$", ligne)
        if m:
            out.append((m.group(1).lower(), m.group(2)))
    return out


def paquets_package_lock(texte: str) -> list[tuple[str, str]]:
    import json

    try:
        d = json.loads(texte or "{}")
    except ValueError:
        return []
    out = []
    for chemin, info in (d.get("packages") or {}).items():
        if chemin.startswith("node_modules/") and isinstance(info, dict) and info.get("version"):
            out.append((chemin.rsplit("node_modules/", 1)[-1], str(info["version"])))
    return out[:400]


def audit_osv(paquets: list[tuple[str, str]], ecosysteme: str, *, client: httpx.Client | None = None) -> dict:
    """Interroge la base OSV pour chaque (paquet, version). Pas d'installation, pas d'exécution : une requête, une réponse."""
    if not paquets:
        return {"ok": True, "vulnerables": [], "verifies": 0, "erreur": None}
    propre = client is None
    client = client or httpx.Client(timeout=30)
    try:
        r = client.post(OSV, json={"queries": [{"package": {"name": n, "ecosystem": ecosysteme}, "version": v} for n, v in paquets]})
        if r.status_code != 200:
            return {"ok": False, "vulnerables": [], "verifies": 0, "erreur": f"OSV a répondu {r.status_code}"}
        resultats = r.json().get("results") or []
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "vulnerables": [], "verifies": 0, "erreur": f"OSV injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()
    vulnerables = []
    for (nom, version), res in zip(paquets, resultats):
        ids = [v.get("id") for v in (res.get("vulns") or []) if v.get("id")]
        if ids:
            vulnerables.append({"paquet": nom, "version": version, "avis": ids[:5]})
    return {"ok": not vulnerables, "vulnerables": vulnerables, "verifies": len(paquets), "erreur": None}


def controler_en_tetes(en_tetes: dict) -> dict:
    """Après une mise en ligne : les en-têtes de sécurité attendus sont-ils là ? Manquants = avertissement, pas retour arrière."""
    bas = {k.lower(): v for k, v in (en_tetes or {}).items()}
    manquants = [h for h in EN_TETES_ATTENDUS if h not in bas]
    return {"ok": not manquants, "manquants": manquants}

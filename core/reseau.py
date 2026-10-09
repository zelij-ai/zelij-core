"""Réseau sortant des agents : une adresse lue par un agent doit être publique. Les adresses privées, de boucle locale, de
lien local et les noms internes (métadonnées cloud, services du réseau Docker) sont refusés avant toute connexion, à chaque
saut de redirection, et la réponse est plafonnée. Une page lue par un agent peut contenir des consignes hostiles : ce filtre
empêche qu'elles servent à sonder l'intérieur du serveur."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

NOMS_INTERDITS = ("localhost", "metadata.google.internal", "metadata", "kubernetes.default")
SUFFIXES_INTERDITS = (".localhost", ".internal", ".local", ".lan", ".home", ".corp", ".intranet")
OCTETS_MAX = 2_000_000
SAUTS_MAX = 5


def _resoudre(hote: str) -> list[str]:
    return sorted({x[4][0] for x in socket.getaddrinfo(hote, None, proto=socket.IPPROTO_TCP)})


def adresse_publique(hote: str, *, resoudre=_resoudre) -> tuple[bool, str]:
    """(ok, motif). Un nom sans point (service d'un réseau interne) ou dont une adresse résolue n'est pas publique est refusé."""
    h = (hote or "").strip().lower().rstrip(".")
    if not h:
        return False, "hôte absent"
    if h in NOMS_INTERDITS or h.endswith(SUFFIXES_INTERDITS):
        return False, f"nom interne refusé ({h})"
    try:
        ips = [ipaddress.ip_address(h.strip("[]"))]
    except ValueError:
        if "." not in h:
            return False, f"nom sans domaine refusé ({h})"
        try:
            ips = [ipaddress.ip_address(x) for x in resoudre(h)]
        except (OSError, ValueError) as exc:
            return False, f"résolution impossible ({str(exc)[:80]})"
        if not ips:
            return False, "aucune adresse"
    for ip in ips:
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified or not ip.is_global:
            return False, f"adresse non publique refusée ({ip})"
    return True, ""


def lire(url: str, *, client: httpx.Client | None = None, resoudre=_resoudre, octets_max: int = OCTETS_MAX, en_tetes: dict | None = None) -> tuple[int, str, str]:
    """GET en https seulement, redirections suivies une par une avec le filtre à chaque saut, corps plafonné. (statut, texte, erreur)."""
    propre = client is None
    client = client or httpx.Client(timeout=20)
    try:
        for _ in range(SAUTS_MAX + 1):
            parts = urlsplit(url)
            if parts.scheme != "https":
                return 0, "", "seules les adresses https sont lues"
            ok, motif = adresse_publique(parts.hostname or "", resoudre=resoudre)
            if not ok:
                return 0, "", f"adresse refusée : {motif}"
            try:
                with client.stream("GET", url, headers=en_tetes or {}, follow_redirects=False) as r:
                    if r.is_redirect and r.headers.get("location"):
                        url = str(r.next_request.url) if r.next_request is not None else r.headers["location"]
                        continue
                    morceaux, total = [], 0
                    for bloc in r.iter_bytes():
                        total += len(bloc)
                        if total > octets_max:
                            return r.status_code, b"".join(morceaux).decode(r.encoding or "utf-8", errors="replace"), "réponse tronquée au plafond"
                        morceaux.append(bloc)
                    return r.status_code, b"".join(morceaux).decode(r.encoding or "utf-8", errors="replace"), ""
            except httpx.HTTPError as exc:
                return 0, "", f"erreur de lecture : {str(exc)[:200]}"
        return 0, "", "trop de redirections"
    finally:
        if propre:
            client.close()

"""Sonde du domaine : DNS, certificat, réponse HTTP, en-têtes de sécurité. Des faits datés, pas d'avis. Utilisée par le
Bâtisseur à la demande, après chaque mise en ligne, et par le point hebdomadaire."""
from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

import httpx

from core import porte_securite


def _resoudre(hote: str) -> list[str]:
    try:
        return sorted({x[4][0] for x in socket.getaddrinfo(hote, None, proto=socket.IPPROTO_TCP)})
    except OSError:
        return []


def _certificat(hote: str, delai: float = 8.0) -> dict:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hote, 443), timeout=delai) as s, ctx.wrap_socket(s, server_hostname=hote) as t:
            cert = t.getpeercert()
        fin = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        jours = (fin - datetime.now(timezone.utc)).days
        emetteur = dict(x[0] for x in cert.get("issuer", ())).get("organizationName", "")
        return {"ok": jours > 7, "expire_le": fin.date().isoformat(), "jours": jours, "emetteur": emetteur}
    except (OSError, ssl.SSLError, KeyError, ValueError) as exc:
        return {"ok": False, "detail": str(exc)[:120]}


def sonder(domaine: str, *, client: httpx.Client | None = None, resoudre=_resoudre, certificat=_certificat) -> dict:
    """Retourne un relevé daté. `resoudre` et `certificat` sont injectables pour les tests."""
    hote = (domaine or "").replace("https://", "").replace("http://", "").split("/")[0].strip()
    if not hote:
        return {"ok": False, "detail": "domaine absent"}
    releve: dict = {"domaine": hote, "releve_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    from core import reseau

    ips = resoudre(hote)
    ok_public, motif = reseau.adresse_publique(hote, resoudre=lambda h: ips) if ips else (True, "")
    if not ok_public:
        # un hôte interne (réseau Docker, boucle locale, métadonnées cloud) n'est jamais relevé : ni DNS, ni certificat, ni HTTP
        return {**releve, "ok": False, "detail": f"hors périmètre : {motif}", "constats": [f"domaine refusé : {motif}"]}
    releve["dns"] = {"ok": bool(ips), "adresses": ips}
    releve["certificat"] = certificat(hote) if ips else {"ok": False, "detail": "pas de DNS"}
    propre = client is None
    client = client or httpx.Client(timeout=15, follow_redirects=True)
    try:
        if ips:
            import time

            debut = time.perf_counter()
            r = client.get(f"https://{hote}/", headers={"User-Agent": "ZelijCore/sonde"})
            duree_ms = int((time.perf_counter() - debut) * 1000)
            en_tetes = porte_securite.controler_en_tetes(dict(r.headers))
            releve["http"] = {"ok": r.status_code == 200, "statut": r.status_code, "duree_ms": duree_ms, "en_tetes_manquants": en_tetes["manquants"]}
        else:
            releve["http"] = {"ok": False, "detail": "pas de DNS"}
    except httpx.HTTPError as exc:
        releve["http"] = {"ok": False, "detail": f"injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()
    releve["ok"] = bool(releve["dns"]["ok"] and releve["certificat"].get("ok") and releve["http"].get("ok"))
    constats = []
    if not releve["dns"]["ok"]:
        constats.append("DNS : aucune adresse")
    if not releve["certificat"].get("ok"):
        constats.append("certificat : " + (f"expire dans {releve['certificat']['jours']} jour(s)" if "jours" in releve["certificat"] else releve["certificat"].get("detail", "invalide")))
    if not releve["http"].get("ok"):
        constats.append("HTTP : " + str(releve["http"].get("statut") or releve["http"].get("detail")))
    if releve["http"].get("en_tetes_manquants"):
        constats.append("en-têtes de sécurité manquants : " + ", ".join(releve["http"]["en_tetes_manquants"]))
    releve["constats"] = constats
    return releve

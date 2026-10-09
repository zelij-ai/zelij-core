"""Cible OVH : le serveur est un VPS OVH (mis en ligne par la cible SSH) et le domaine est chez OVH, dont l'API pose les
enregistrements DNS. Le Bâtisseur ne commande rien et ne paie rien : il prépare le panier (un lien et une liste), le
fondateur paie dans son espace client puis colle les clés d'API dans le .env.

Variables : OVH_ENDPOINT (ovh-eu), OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY (droits GET/PUT/POST sur
/domain/zone/*), plus celles de la cible SSH. Signature OVH : SHA-1 de secret+consumer+méthode+url+corps+horodatage."""
from __future__ import annotations

import hashlib
import json
import os
import time

import httpx

from core.cibles import ssh as cible_ssh

NOM = "OVH (VPS + domaine + DNS)"
ENDPOINTS = {"ovh-eu": "https://eu.api.ovh.com/1.0", "ovh-ca": "https://ca.api.ovh.com/1.0", "ovh-us": "https://api.us.ovhcloud.com/1.0"}
PANIER_VPS = "https://www.ovhcloud.com/fr/vps/"
PANIER_DOMAINE = "https://www.ovhcloud.com/fr/domains/"


def configuration() -> dict | None:
    ak, as_, ck = (os.environ.get(k, "").strip() for k in ("OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY"))
    if not (ak and as_ and ck):
        return None
    return {"base": ENDPOINTS.get(os.environ.get("OVH_ENDPOINT", "ovh-eu").strip(), ENDPOINTS["ovh-eu"]), "ak": ak, "as": as_, "ck": ck}


def _signer(conf: dict, methode: str, url: str, corps: str, horodatage: int) -> str:
    brut = "+".join([conf["as"], conf["ck"], methode.upper(), url, corps, str(horodatage)])
    # SHA-1 imposé par le protocole de signature de l'API OVH ; il n'est pas utilisé ici comme garantie d'intégrité.
    return "$1$" + hashlib.sha1(brut.encode(), usedforsecurity=False).hexdigest()


def appel(methode: str, chemin: str, corps: dict | None = None, *, client: httpx.Client | None = None, horodatage: int | None = None) -> tuple[int, object]:
    conf = configuration()
    if conf is None:
        return 0, {"erreur": "clés OVH absentes"}
    url = conf["base"] + chemin
    texte = json.dumps(corps, separators=(",", ":"), ensure_ascii=False) if corps is not None else ""
    ts = horodatage or int(time.time())
    h = {"X-Ovh-Application": conf["ak"], "X-Ovh-Consumer": conf["ck"], "X-Ovh-Timestamp": str(ts), "X-Ovh-Signature": _signer(conf, methode, url, texte, ts),
         "Content-Type": "application/json", "User-Agent": "zelij-core-batisseur"}
    propre = client is None
    client = client or httpx.Client(timeout=30)
    try:
        r = client.request(methode.upper(), url, headers=h, content=texte.encode() if texte else None)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, r.text
    except httpx.HTTPError as exc:
        return 0, {"erreur": f"OVH injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()


def pointer_domaine(zone: str, ip: str, *, sous_domaines: tuple[str, ...] = ("", "www"), client: httpx.Client | None = None) -> dict:
    """Pose (ou remplace) les enregistrements A de la zone vers l'IP du serveur, puis rafraîchit la zone. Idempotent."""
    if configuration() is None:
        return {"ok": False, "detail": "clés OVH absentes (OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY)"}
    if not zone or not ip:
        return {"ok": False, "detail": "zone et IP requises"}
    faits = []
    for sd in sous_domaines:
        code, ids = appel("GET", f"/domain/zone/{zone}/record?fieldType=A&subDomain={sd}", client=client)
        if code != 200 or not isinstance(ids, list):
            return {"ok": False, "detail": f"lecture de la zone {zone} impossible ({code}) : droits de l'API ?", "faits": faits}
        if ids:
            code, rep = appel("PUT", f"/domain/zone/{zone}/record/{ids[0]}", {"target": ip, "ttl": 600}, client=client)
            faits.append(f"{sd or '@'} A → {ip} (mis à jour)" if code in (200, 204) else f"{sd or '@'} : mise à jour refusée ({code})")
        else:
            code, rep = appel("POST", f"/domain/zone/{zone}/record", {"fieldType": "A", "subDomain": sd, "target": ip, "ttl": 600}, client=client)
            faits.append(f"{sd or '@'} A → {ip} (créé)" if code in (200, 201) else f"{sd or '@'} : création refusée ({code})")
    code, _ = appel("POST", f"/domain/zone/{zone}/refresh", client=client)
    return {"ok": all("refusée" not in f for f in faits) and code in (200, 204), "detail": " ; ".join(faits) + (" ; zone rafraîchie" if code in (200, 204) else f" ; rafraîchissement refusé ({code})"), "faits": faits}


def preparer_panier(domaine: str | None = None) -> dict:
    """Ce que le fondateur doit commander lui-même, avec les liens : le Bâtisseur n'achète rien."""
    etapes = [
        {"quoi": "Un VPS OVH d'entrée de gamme (Linux, Debian ou Ubuntu récent)", "lien": PANIER_VPS,
         "ensuite": "noter l'adresse IP et déposer votre clé publique SSH ; renseigner SSH_HOTE, SSH_UTILISATEUR, SSH_CLE, SITE_DOSSIER dans le .env"},
        {"quoi": f"Le nom de domaine {domaine or 'de votre choix'} chez OVH", "lien": PANIER_DOMAINE + (f"?search={domaine}" if domaine else ""),
         "ensuite": "créer les clés d'API (https://eu.api.ovh.com/createToken/) avec les droits GET, POST, PUT sur /domain/zone/* ; les coller dans le .env"},
        {"quoi": "Un certificat TLS", "lien": "", "ensuite": "rien à acheter : le serveur l'obtient lui-même (Caddy ou certbot) une fois le DNS en place"},
    ]
    return {"ok": True, "etapes": etapes, "detail": "panier préparé ; le paiement se fait dans l'espace client OVH, jamais ici"}


def installer(config: dict | None = None, **k) -> dict:
    """Installation OVH = installation SSH du VPS + DNS si le domaine et l'IP sont connus."""
    res = cible_ssh.installer(config, **{x: y for x, y in k.items() if x == "executer_cmd"})
    domaine = os.environ.get("SITE_DOMAINE", "").replace("https://", "").replace("http://", "").strip("/")
    ip = os.environ.get("SSH_HOTE", "").strip()
    if res.get("ok") and domaine and ip and configuration() is not None and ip.replace(".", "").isdigit():
        dns = pointer_domaine(domaine, ip, client=k.get("client"))
        res["dns"] = dns
        res["detail"] += " ; DNS : " + dns["detail"]
    return res


def deployer(version: str, octets: bytes, **k) -> dict:
    return cible_ssh.deployer(version, octets, **k)


def versions(**k) -> dict:
    return cible_ssh.versions(**k)

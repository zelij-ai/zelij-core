"""Cible « serveur Linux en SSH » : le site statique du fondateur est mis en ligne par versions sous un dossier, avec une
bascule atomique (lien symbolique), un test de fumée et un retour arrière automatique. Les commandes passent par le client
OpenSSH du conteneur avec la clé du fondateur ; `executer_cmd` est injectable pour les tests.

Variables : SSH_HOTE, SSH_UTILISATEUR, SSH_CLE (chemin de la clé privée, montée en lecture seule), SSH_PORT (22),
SITE_DOSSIER (dossier des versions sur le serveur, ex. /var/www/site), SITE_DOMAINE (https://…) pour la fumée,
SSH_CLE_HOTE (facultatif : la clé publique du serveur telle que `ssh-keyscan` l'affiche ; posée, toute autre clé est refusée ;
absente, la clé est acceptée à la première connexion et mémorisée)."""
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

import httpx

NOM = "Serveur Linux (SSH)"
VERSIONS_GARDEES = 5


def configuration() -> dict | None:
    hote, user, cle, dossier = (os.environ.get(k, "").strip() for k in ("SSH_HOTE", "SSH_UTILISATEUR", "SSH_CLE", "SITE_DOSSIER"))
    if not (hote and user and cle and dossier):
        return None
    return {"hote": hote, "utilisateur": user, "cle": cle, "port": int(os.environ.get("SSH_PORT", "22") or 22), "dossier": dossier.rstrip("/"),
            "domaine": os.environ.get("SITE_DOMAINE", "").strip().rstrip("/")}


def _executer_cmd(args: list[str], *, entree: bytes | None = None, delai: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(args, input=entree, capture_output=True, timeout=delai, check=False)
        return r.returncode, (r.stdout or b"").decode("utf-8", errors="replace") + (r.stderr or b"").decode("utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 255, str(exc)[:200]


def options_hote(conf: dict) -> list[str]:
    """Avec SSH_CLE_HOTE, la clé du serveur est imposée (fichier known_hosts dédié, vérification stricte) ; sans, confiance au premier contact."""
    cle_hote = os.environ.get("SSH_CLE_HOTE", "").strip()
    if not cle_hote:
        return ["-o", "StrictHostKeyChecking=accept-new"]
    hote = conf["hote"] if int(conf.get("port", 22)) == 22 else f"[{conf['hote']}]:{conf['port']}"
    ligne = cle_hote if cle_hote.split()[0] == hote else f"{hote} {cle_hote}"
    # Un seul fichier par clé d'hôte, réécrit à l'identique : pas un fichier temporaire de plus à chaque commande.
    chemin = Path(tempfile.gettempdir()) / f"known_hosts-{hashlib.sha256(ligne.encode()).hexdigest()[:16]}.txt"
    chemin.write_text(ligne.strip() + "\n", encoding="utf-8")
    return ["-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={chemin}"]


def _ssh(conf: dict, commande: str, *, executer_cmd=_executer_cmd, entree: bytes | None = None) -> tuple[int, str]:
    base = ["ssh", "-i", conf["cle"], "-p", str(conf["port"]), "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", *options_hote(conf),
            f"{conf['utilisateur']}@{conf['hote']}", commande]
    return executer_cmd(base, entree=entree)


def installer(config: dict | None = None, *, executer_cmd=_executer_cmd) -> dict:
    """Vérifie l'accès, crée l'arborescence des versions. Ne touche à rien d'autre sur la machine."""
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "cible SSH non configurée (SSH_HOTE, SSH_UTILISATEUR, SSH_CLE, SITE_DOSSIER)"}
    code, sortie = _ssh(conf, f"mkdir -p {shlex.quote(conf['dossier'])}/versions && uname -a && df -h {shlex.quote(conf['dossier'])} | tail -1", executer_cmd=executer_cmd)
    if code != 0:
        return {"ok": False, "detail": f"connexion ou préparation impossible : {sortie.strip()[:200]}"}
    return {"ok": True, "detail": "accès vérifié, dossier des versions prêt", "serveur": sortie.strip()[:300]}


def deployer(version: str, octets: bytes, *, executer_cmd=_executer_cmd, client: httpx.Client | None = None) -> dict:
    """Envoie l'archive, la déplie dans versions/<version>, bascule le lien `courant`, teste, revient en arrière si besoin."""
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "cible SSH non configurée"}
    version = "".join(ch for ch in version if ch.isalnum() or ch in "-_.")[:40] or "version"
    d = shlex.quote(conf["dossier"])
    cible = f"{conf['dossier']}/versions/{version}"
    # 1. envoi et dépliage (l'archive GitHub a un dossier racine : on l'aplatit)
    code, sortie = _ssh(conf, f"mkdir -p {shlex.quote(cible)} && tar -xzf - -C {shlex.quote(cible)} --strip-components=1 && test -f {shlex.quote(cible)}/index.html",
                        executer_cmd=executer_cmd, entree=octets)
    if code != 0:
        _ssh(conf, f"rm -rf {shlex.quote(cible)}", executer_cmd=executer_cmd)
        return {"ok": False, "detail": f"envoi ou dépliage en échec (index.html attendu à la racine) : {sortie.strip()[:160]}"}
    # 2. mémoriser la version courante puis basculer atomiquement
    code, precedente = _ssh(conf, f"readlink {d}/courant || true", executer_cmd=executer_cmd)
    precedente = precedente.strip()
    code, sortie = _ssh(conf, f"ln -sfn {shlex.quote(cible)} {d}/courant.tmp && mv -Tf {d}/courant.tmp {d}/courant", executer_cmd=executer_cmd)
    if code != 0:
        return {"ok": False, "detail": f"bascule impossible : {sortie.strip()[:160]}"}
    # 3. fumée
    fumee = tester_fumee(conf["domaine"], client=client) if conf["domaine"] else {"ok": True, "detail": "pas de domaine déclaré : fumée sautée"}
    if not fumee["ok"]:
        if precedente:
            _ssh(conf, f"ln -sfn {shlex.quote(precedente)} {d}/courant.tmp && mv -Tf {d}/courant.tmp {d}/courant", executer_cmd=executer_cmd)
        return {"ok": False, "detail": f"test de fumée en échec ({fumee['detail']}) : retour à la version précédente", "retour_arriere": bool(precedente)}
    # 4. ménage : garder les dernières versions
    _ssh(conf, f"cd {d}/versions && ls -1t | tail -n +{VERSIONS_GARDEES + 1} | xargs -r rm -rf", executer_cmd=executer_cmd)
    return {"ok": True, "detail": f"version {version} en ligne" + (f" ({fumee['detail']})" if fumee.get("detail") else ""), "version": version, "precedente": precedente or None,
            "en_tetes": fumee.get("en_tetes", {})}


def tester_fumee(domaine: str, *, client: httpx.Client | None = None) -> dict:
    """La page d'accueil répond 200 avec du HTML. Les en-têtes sont rapportés pour la porte de sécurité."""
    if not domaine:
        return {"ok": False, "detail": "domaine absent"}
    propre = client is None
    client = client or httpx.Client(timeout=20, follow_redirects=True)
    try:
        r = client.get(domaine + "/", headers={"User-Agent": "ZelijCore/fumee"})
        ok = r.status_code == 200 and "<html" in r.text[:4000].lower()
        return {"ok": ok, "detail": f"HTTP {r.status_code}" + ("" if ok else ", page inattendue"), "en_tetes": dict(r.headers)}
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"injoignable : {str(exc)[:120]}"}
    finally:
        if propre:
            client.close()


def versions(*, executer_cmd=_executer_cmd) -> dict:
    conf = configuration()
    if conf is None:
        return {"ok": False, "detail": "cible SSH non configurée", "versions": [], "courante": None}
    code, sortie = _ssh(conf, f"ls -1t {shlex.quote(conf['dossier'])}/versions 2>/dev/null; echo ---; readlink {shlex.quote(conf['dossier'])}/courant || true", executer_cmd=executer_cmd)
    if code != 0:
        return {"ok": False, "detail": sortie.strip()[:160], "versions": [], "courante": None}
    liste, _, courante = sortie.partition("---")
    return {"ok": True, "versions": [v for v in liste.split() if v], "courante": (courante.strip().rsplit("/", 1)[-1] or None)}


def archive_vers_fichier(octets: bytes) -> Path:
    """Utilitaire pour un envoi par scp si le flux par ssh n'est pas souhaité."""
    f = tempfile.NamedTemporaryFile(prefix="site-", suffix=".tar.gz", delete=False)
    f.write(octets)
    f.close()
    return Path(f.name)

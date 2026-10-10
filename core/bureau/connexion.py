"""Connexion sans mot de passe : lien e-mail à usage unique (20 minutes), session en cookie signé HMAC, HttpOnly, 30 jours.
Une installation, une organisation : la première adresse la crée (ou seulement FONDATEUR_EMAIL si elle est posée) ; ensuite, une
adresse inconnue ne reçoit plus rien, seule une invitation (jeton portant org_id) rattache quelqu'un. Aucun mot de passe nulle part."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import smtplib
import ssl
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from core import db

logger = logging.getLogger("zelij-core")
COOKIE = "core_session"
DUREE_SESSION = 30 * 86400
DUREE_JETON = timedelta(minutes=20)
_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
_demandes: dict[str, list[float]] = {}
# Freins sur les liens de connexion (et les invitations) : par adresse, par adresse IP, et global. Sans eux, le formulaire
# est un relais de courriels : n'importe qui ferait envoyer des milliers de messages depuis le SMTP du fondateur.
FREINS = {"email": (5, 900), "ip": (10, 900), "global": (60, 3600)}
_CLES_MAX = 5000
_secret_dev: bytes | None = None
# Les clés du .env (modèle, paiement, dépôt, serveur) appartiennent à l'installation, pas à une organisation : une seconde
# organisation les utiliserait toutes. Le noyau n'en admet donc qu'une. Seuls les tests lèvent cette règle.
UNE_SEULE_ORGANISATION = True


def _secret() -> bytes:
    global _secret_dev
    s = os.environ.get("SECRET_KEY", "")
    if s:
        return s.encode()
    if os.environ.get("CORE_ENV") == "production":
        raise RuntimeError("SECRET_KEY absente en production")
    if _secret_dev is None:
        # Hors production : une clé aléatoire par processus, jamais une constante connue de tous (les sessions tombent au redémarrage).
        _secret_dev = secrets.token_bytes(32)
        logger.warning("SECRET_KEY absente : clé de session temporaire générée (développement seulement)")
    return _secret_dev


def production() -> bool:
    return os.environ.get("CORE_ENV") == "production"


def email_valide(email: str) -> str | None:
    e = (email or "").strip().lower()
    return e if _EMAIL_RE.match(e) and len(e) <= 200 else None


def masquer(email: str) -> str:
    """Une adresse telle qu'elle peut figurer dans les journaux du serveur : première lettre et domaine."""
    nom, _, domaine = (email or "").partition("@")
    return f"{nom[:1]}***@{domaine}" if domaine else "***"


def fondateur_declare() -> str:
    """FONDATEUR_EMAIL (facultatif) : posée, seule cette adresse peut créer l'organisation de l'installation."""
    return os.environ.get("FONDATEUR_EMAIL", "").strip().lower()


def inscription_possible(c: db.Connexion, email: str) -> bool:
    """Cette adresse peut-elle recevoir un lien ? Oui si elle a déjà un compte. Sinon, seulement tant qu'aucune organisation
    n'existe, et seulement pour FONDATEUR_EMAIL si elle est posée. Une installation = une organisation."""
    if c.une("SELECT id FROM utilisateurs WHERE email = ?", (email,)):
        return True
    if not UNE_SEULE_ORGANISATION:
        return True
    if c.une("SELECT id FROM organisations LIMIT 1"):
        return False
    attendu = fondateur_declare()
    return not attendu or attendu == email


def demande_autorisee(email: str, maintenant: float | None = None, ip: str = "") -> bool:
    """Un lien par demande, dans les freins (adresse, IP, global). Une demande refusée n'est ni comptée ni mémorisée :
    un flot d'adresses inventées ne fait pas grossir la mémoire du serveur."""
    t = maintenant or time.time()
    cles = [("email:" + email, FREINS["email"]), ("global", FREINS["global"])] + ([("ip:" + ip, FREINS["ip"])] if ip else [])
    recentes = {k: [x for x in _demandes.get(k, []) if t - x < fenetre] for k, (_, fenetre) in cles}
    if any(len(recentes[k]) >= plafond for k, (plafond, _) in cles):
        logger.warning("lien de connexion refusé (frein) pour %s depuis %s", masquer(email), ip or "?")
        return False
    for k, _ in cles:
        _demandes[k] = recentes[k] + [t]
    if len(_demandes) > _CLES_MAX:
        for k in [k for k, v in _demandes.items() if not v or t - max(v) > 3600]:
            del _demandes[k]
    return True


def jeton_csrf(user_id: str, n: int = 0) -> str:
    """Jeton anti-CSRF dérivé de la session (utilisateur et numéro de session) : un formulaire forgé depuis un autre site ne
    peut pas le connaître, et il change à chaque déconnexion."""
    return hmac.new(_secret(), f"csrf.{user_id}.{int(n)}".encode(), hashlib.sha256).hexdigest()[:40]


def csrf_valide(user_id: str, jeton: str | None, n: int = 0) -> bool:
    return bool(jeton) and hmac.compare_digest(jeton_csrf(user_id, n), str(jeton))


def _empreinte(brut: str) -> str:
    return hashlib.sha256((brut or "").encode()).hexdigest()


def creer_jeton(c: db.Connexion, email: str, *, org_id: str | None = None) -> str:
    brut = secrets.token_urlsafe(32)
    c.executer("INSERT INTO jetons_connexion (id, email, empreinte, expire_le, org_id, cree_le) VALUES (?,?,?,?,?,?)",
               (db.nouvel_id(), email, _empreinte(brut), (datetime.now(timezone.utc) + DUREE_JETON).isoformat(timespec="seconds"), org_id, db.maintenant()))
    return brut


def consommer_jeton(c: db.Connexion, brut: str) -> dict | None:
    row = c.une("SELECT * FROM jetons_connexion WHERE empreinte = ?", (_empreinte(brut),))
    now = db.maintenant()
    if row is None or row["utilise_le"] is not None or row["expire_le"] < now:
        return None
    # Usage unique tenu par la base : deux requêtes simultanées sur le même lien, une seule passe.
    if c.executer("UPDATE jetons_connexion SET utilise_le = ? WHERE id = ? AND utilise_le IS NULL", (now, row["id"])) != 1:
        return None
    user = c.une("SELECT * FROM utilisateurs WHERE email = ?", (row["email"],))
    if user is None:
        if row["org_id"]:
            if not c.une("SELECT id FROM organisations WHERE id = ?", (row["org_id"],)):
                return None
            org_id, role = row["org_id"], "membre"
        else:
            # Contrôle refait au clic : entre la demande du lien et son usage, une autre adresse a pu créer l'organisation.
            if not inscription_possible(c, row["email"]):
                logger.warning("création d'organisation refusée pour %s : l'installation a déjà la sienne", masquer(row["email"]))
                return None
            org_id, role = db.nouvel_id(), "fondateur"
            c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (org_id, row["email"].split("@", 1)[1], now))
        uid = db.nouvel_id()
        c.executer("INSERT INTO utilisateurs (id, org_id, email, role, cree_le, derniere_connexion) VALUES (?,?,?,?,?,?)",
                   (uid, org_id, row["email"], role, now, now))
        user = c.une("SELECT * FROM utilisateurs WHERE id = ?", (uid,))
    else:
        c.executer("UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?", (now, user["id"]))
    return user


def signer_session(user_id: str, maintenant: int | None = None, n: int = 0) -> str:
    """`n` est le numéro de session de l'utilisateur (colonne session_n) : la déconnexion l'augmente, et tout cookie signé
    avec un numéro plus ancien cesse de valoir, même copié ailleurs."""
    exp = (maintenant or int(time.time())) + DUREE_SESSION
    corps = f"{user_id}.{exp}.{int(n)}"
    return f"{corps}.{hmac.new(_secret(), corps.encode(), hashlib.sha256).hexdigest()}"


def _lire(valeur: str | None, maintenant: int | None = None) -> tuple[str, int] | None:
    parts = (valeur or "").split(".")
    try:
        if len(parts) == 4:
            user_id, exp, n, mac = parts
            corps, n_i = f"{user_id}.{exp}.{n}", int(n)
        elif len(parts) == 3:                      # cookie émis avant la 0.7.4 : numéro de session 0
            user_id, exp, mac = parts
            corps, n_i = f"{user_id}.{exp}", 0
        else:
            return None
        exp_i = int(exp)
    except ValueError:
        return None
    attendu = hmac.new(_secret(), corps.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, attendu) or exp_i < (maintenant or int(time.time())):
        return None
    return user_id, n_i


def lire_session(valeur: str | None, maintenant: int | None = None) -> str | None:
    """L'utilisateur que le cookie désigne, si la signature et l'échéance tiennent. Le numéro de session se compare en base
    (voir `numero_session`) : c'est le bureau qui le fait, à chaque requête."""
    lu = _lire(valeur, maintenant)
    return lu[0] if lu else None


def numero_session(valeur: str | None, maintenant: int | None = None) -> int:
    lu = _lire(valeur, maintenant)
    return lu[1] if lu else 0


def revoquer_sessions(c: db.Connexion, user_id: str) -> None:
    """Déconnexion : tous les cookies de cet utilisateur, sur tous ses appareils, cessent de valoir."""
    c.executer("UPDATE utilisateurs SET session_n = session_n + 1 WHERE id = ?", (user_id,))


def envoyer_mail(to: str, sujet: str, corps: str) -> bool:
    """SMTP du fondateur (variables SMTP_*). Sans SMTP, le message est journalisé : développement et tests. Le certificat du
    serveur de messagerie est vérifié : STARTTLS sur le port 587, TLS direct sur le port 465."""
    hote = os.environ.get("SMTP_HOST", "")
    if not hote:
        if production():
            logger.error("SMTP non configuré en production : e-mail non envoyé à %s (le contenu n'est pas journalisé)", masquer(to))
            return False
        logger.warning("SMTP non configuré : e-mail non envoyé à %s — %s\n%s", to, sujet, corps)
        return False
    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM_EMAIL", "bureau@localhost")
    msg["To"], msg["Subject"] = to, sujet
    msg.set_content(corps)
    port = int(os.environ.get("SMTP_PORT", "587") or 587)
    contexte = ssl.create_default_context()
    try:
        if port == 465:
            smtp = smtplib.SMTP_SSL(hote, port, timeout=20, context=contexte)
        else:
            smtp = smtplib.SMTP(hote, port, timeout=20)
        with smtp:
            if port != 465:
                smtp.starttls(context=contexte)
            if os.environ.get("SMTP_USERNAME"):
                smtp.login(os.environ["SMTP_USERNAME"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Envoi SMTP en échec vers %s", masquer(to))
        return False


def email_connexion(lien: str) -> tuple[str, str]:
    return ("Votre lien de connexion — Zelij Core",
            "Bonjour,\n\nPour entrer dans votre bureau, ouvrez ce lien (valable 20 minutes, une seule fois) :\n\n"
            f"{lien}\n\nSi vous n'avez rien demandé, ignorez cet e-mail : aucun compte n'est créé sans ce clic.\n\n— Zelij Core")

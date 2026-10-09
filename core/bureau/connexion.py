"""Connexion sans mot de passe : lien e-mail à usage unique (20 minutes), session en cookie signé HMAC, HttpOnly, 30 jours.
La première adresse crée l'organisation ; une invitation (jeton portant org_id) rattache l'invité. Aucun mot de passe nulle part."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import smtplib
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
_secret_dev: bytes | None = None


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


def _frein(cle: str, plafond: int, fenetre: int, t: float) -> bool:
    recentes = [x for x in _demandes.get(cle, []) if t - x < fenetre]
    _demandes[cle] = recentes
    return len(recentes) < plafond


def demande_autorisee(email: str, maintenant: float | None = None, ip: str = "") -> bool:
    """Un lien par demande, dans les freins (adresse, IP, global) ; une demande refusée n'est pas comptée deux fois."""
    t = maintenant or time.time()
    cles = [("email:" + email, FREINS["email"]), ("global", FREINS["global"])] + ([("ip:" + ip, FREINS["ip"])] if ip else [])
    if not all(_frein(k, n, f, t) for k, (n, f) in cles):
        logger.warning("lien de connexion refusé (frein) pour %s depuis %s", email, ip or "?")
        return False
    for k, _ in cles:
        _demandes[k].append(t)
    return True


def jeton_csrf(user_id: str) -> str:
    """Jeton anti-CSRF dérivé de la session : un formulaire forgé depuis un autre site ne peut pas le connaître."""
    return hmac.new(_secret(), f"csrf.{user_id}".encode(), hashlib.sha256).hexdigest()[:40]


def csrf_valide(user_id: str, jeton: str | None) -> bool:
    return bool(jeton) and hmac.compare_digest(jeton_csrf(user_id), str(jeton))


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
    c.executer("UPDATE jetons_connexion SET utilise_le = ? WHERE id = ?", (now, row["id"]))
    user = c.une("SELECT * FROM utilisateurs WHERE email = ?", (row["email"],))
    if user is None:
        if row["org_id"]:
            org_id, role = row["org_id"], "membre"
        else:
            org_id, role = db.nouvel_id(), "fondateur"
            c.executer("INSERT INTO organisations (id, nom, cree_le) VALUES (?,?,?)", (org_id, row["email"].split("@", 1)[1], now))
        uid = db.nouvel_id()
        c.executer("INSERT INTO utilisateurs (id, org_id, email, role, cree_le, derniere_connexion) VALUES (?,?,?,?,?,?)",
                   (uid, org_id, row["email"], role, now, now))
        user = c.une("SELECT * FROM utilisateurs WHERE id = ?", (uid,))
    else:
        c.executer("UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?", (now, user["id"]))
    return user


def signer_session(user_id: str, maintenant: int | None = None) -> str:
    exp = (maintenant or int(time.time())) + DUREE_SESSION
    corps = f"{user_id}.{exp}"
    return f"{corps}.{hmac.new(_secret(), corps.encode(), hashlib.sha256).hexdigest()}"


def lire_session(valeur: str | None, maintenant: int | None = None) -> str | None:
    try:
        user_id, exp, mac = (valeur or "").split(".")
        exp_i = int(exp)
    except ValueError:
        return None
    attendu = hmac.new(_secret(), f"{user_id}.{exp}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, attendu) or exp_i < (maintenant or int(time.time())):
        return None
    return user_id


def envoyer_mail(to: str, sujet: str, corps: str) -> bool:
    """SMTP du fondateur (variables SMTP_*). Sans SMTP, le message est journalisé : développement et tests."""
    hote = os.environ.get("SMTP_HOST", "")
    if not hote:
        if production():
            logger.error("SMTP non configuré en production : e-mail non envoyé à %s (le contenu n'est pas journalisé)", to)
            return False
        logger.warning("SMTP non configuré : e-mail non envoyé à %s — %s\n%s", to, sujet, corps)
        return False
    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM_EMAIL", "bureau@localhost")
    msg["To"], msg["Subject"] = to, sujet
    msg.set_content(corps)
    try:
        with smtplib.SMTP(hote, int(os.environ.get("SMTP_PORT", "587")), timeout=20) as smtp:
            smtp.starttls()
            if os.environ.get("SMTP_USERNAME"):
                smtp.login(os.environ["SMTP_USERNAME"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Envoi SMTP en échec vers %s", to)
        return False


def email_connexion(lien: str) -> tuple[str, str]:
    return ("Votre lien de connexion — Zelij Core",
            "Bonjour,\n\nPour entrer dans votre bureau, ouvrez ce lien (valable 20 minutes, une seule fois) :\n\n"
            f"{lien}\n\nSi vous n'avez rien demandé, ignorez cet e-mail : aucun compte n'est créé sans ce clic.\n\n— Zelij Core")

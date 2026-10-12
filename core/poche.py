"""Dans la poche : décider depuis le téléphone (0.9.0).

Quand un agent ouvre une décision, le fondateur la reçoit là où il est : par e-mail (deux liens signés, à usage unique,
« Approuver » et « Refuser », plus le lien du bureau pour demander une modification) et, s'il a branché un robot Telegram,
par un message à trois boutons. La règle de la maison ne change pas : c'est toujours lui qui décide, la décision passe par
`gouvernance.decider`, elle est journalisée avec le canal utilisé, et tout ce qui ne vient pas de lui est refusé.

Ce que ce module refuse de faire : décider sur un simple clic de lien (le lien ouvre une page de confirmation, le geste est
un POST, comme la connexion : un logiciel de messagerie qui suit les liens ne décide rien) ; accepter un bouton Telegram
venu d'une autre conversation que celle du fondateur ; envoyer quoi que ce soit en mode démonstration."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

from core import db, gouvernance

logger = logging.getLogger("zelij-core")

VALIDITE = timedelta(days=7)            # un lien de décision vaut une semaine ; la décision, elle, attend dans le bureau
ACTIONS_LIEN = ("approuver", "refuser")  # « à modifier » exige une consigne : il passe par le bureau ou par Telegram
TELEGRAM = "https://api.telegram.org"
_apres_approbation = None               # posé par le bureau : exécute ce qu'une décision approuvée désigne (agent, publication…)
_envoyer_mail = None                    # posé par le bureau : connexion.envoyer_mail (remplacé dans les tests)
_demandes: dict[str, list[float]] = {}
_consignes_attendues: dict[int, str] = {}   # Telegram : message « quelle consigne ? » → décision, le temps d'une réponse


def configurer(*, apres_approbation=None, envoyer_mail=None) -> None:
    global _apres_approbation, _envoyer_mail
    if apres_approbation is not None:
        _apres_approbation = apres_approbation
    if envoyer_mail is not None:
        _envoyer_mail = envoyer_mail


def telegram_configure() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_CHAT_ID"))


def email_configure() -> bool:
    return bool(os.environ.get("SMTP_HOST")) and os.environ.get("DECISIONS_PAR_EMAIL", "1") == "1"


def _origine() -> str:
    return os.environ.get("APP_ORIGIN", "http://localhost:8000").rstrip("/")


def _empreinte(brut: str) -> str:
    return hashlib.sha256(brut.encode()).hexdigest()


def fondateurs(c: db.Connexion, org_id: str) -> list[dict]:
    return c.lignes("SELECT id, email, org_id, role FROM utilisateurs WHERE org_id = ? AND role = 'fondateur' ORDER BY cree_le", (org_id,))


# ---------------------------------------------------------------- liens signés (e-mail)

def creer_liens(c: db.Connexion, org_id: str, decision_id: str, email: str) -> dict[str, str]:
    """Un jeton par action, haché en base, en clair dans l'e-mail seulement. Renvoie {action: url}."""
    liens = {}
    expire = (datetime.now(timezone.utc) + VALIDITE).isoformat(timespec="seconds")
    for action in ACTIONS_LIEN:
        brut = secrets.token_urlsafe(32)
        c.executer("INSERT INTO jetons_decision (id, org_id, decision_id, action, email, empreinte, expire_le, cree_le) VALUES (?,?,?,?,?,?,?,?)",
                   (db.nouvel_id(), org_id, decision_id, action, email, _empreinte(brut), expire, db.maintenant()))
        liens[action] = f"{_origine()}/poche/{brut}"
    return liens


def lire_lien(c: db.Connexion, brut: str) -> dict | None:
    """Le jeton et sa décision, s'il est encore valable (non utilisé, non expiré, décision encore en attente)."""
    j = c.une("SELECT * FROM jetons_decision WHERE empreinte = ?", (_empreinte(brut or ""),))
    if j is None or j["utilise_le"] is not None or j["expire_le"] < db.maintenant():
        return None
    d = gouvernance.lire(c, j["org_id"], j["decision_id"])
    if d is None or d["etat"] != "en_attente":
        return None
    return {"jeton": j, "decision": d}


def decider_par_lien(c: db.Connexion, brut: str, *, ip: str = "") -> dict:
    """Le POST de la page de confirmation : consomme le jeton, tranche, lance ce qui suit. Lève ValueError si rien ne va."""
    if not autorise(f"lien:{ip or '?'}", 20, 900):
        raise ValueError("trop")
    v = lire_lien(c, brut)
    if v is None:
        raise ValueError("lien_invalide")
    j = v["jeton"]
    maintenant = db.maintenant()
    if c.executer("UPDATE jetons_decision SET utilise_le = ? WHERE id = ? AND utilise_le IS NULL", (maintenant, j["id"])) != 1:
        raise ValueError("lien_invalide")
    # les autres liens de la même décision ne valent plus rien : une décision, un geste
    c.executer("UPDATE jetons_decision SET utilise_le = ? WHERE decision_id = ? AND utilise_le IS NULL", (maintenant, j["decision_id"]))
    return _trancher(c, j["org_id"], j["decision_id"], j["action"], email=j["email"], canal="lien e-mail")


def _trancher(c: db.Connexion, org_id: str, decision_id: str, action: str, *, email: str, canal: str, consigne: str = "") -> dict:
    u = c.une("SELECT u.*, o.nom AS organisation FROM utilisateurs u JOIN organisations o ON o.id = u.org_id WHERE u.email = ? AND u.org_id = ?",
              (email, org_id))
    if u is None or u.get("role") != "fondateur":
        gouvernance.journaliser(c, org_id, email, "acces.refuse", decision_id, f"décision depuis {canal} : pas le fondateur")
        raise ValueError("reserve")
    d = gouvernance.decider(c, org_id, decision_id, action, par=f"{email} ({canal})", consigne=consigne)
    if d["etat"] == "approuvee" and d.get("agent_cible") and d.get("tache") and _apres_approbation is not None:
        _apres_approbation(c, u, d)
    return d


# ---------------------------------------------------------------- notification à l'ouverture

def texte_decision(d: dict, liens: dict[str, str] | None = None) -> str:
    """Le paquet, en clair, tel qu'il arrive sur un téléphone. Pas de HTML : lisible partout."""
    lignes = [f"Décision à prendre — {d['objectif']}", "", f"Demandée par : {d['demandeur']}", "", d["proposition"][:1200]]
    if d.get("pourquoi_maintenant"):
        lignes += ["", f"Pourquoi maintenant : {d['pourquoi_maintenant'][:400]}"]
    if d.get("options"):
        lignes += ["", "Options : " + " · ".join(d["options"][:4])]
    if d.get("recommandation"):
        lignes.append(f"Recommandation : {d['recommandation']}")
    if d.get("risques"):
        lignes += ["", "Risques : " + " ; ".join(d["risques"][:4])]
    lignes.append(f"Réversibilité : {d.get('reversibilite', 'reversible')}" + (f" · impact {d['impact_eur']:.0f} €" if d.get("impact_eur") else ""))
    if liens:
        lignes += ["", f"Approuver : {liens['approuver']}", f"Refuser : {liens['refuser']}",
                   f"Demander une modification (avec votre consigne) : {_origine()}/bureau",
                   "", "Chaque lien ouvre une page de confirmation et ne sert qu'une fois ; il vaut sept jours. Ce n'est pas vous qui avez demandé ? Ignorez ce message : rien ne se passe sans votre geste."]
    return "\n".join(lignes)


def prevenir(c: db.Connexion, org_id: str, decision_id: str) -> dict:
    """À l'ouverture d'une décision : e-mail au fondateur avec les liens, message Telegram avec les boutons. Renvoie ce qui est
    parti. Jamais en mode démonstration (rien ne sort), jamais sans fondateur."""
    from core import demo

    fait = {"email": 0, "telegram": False}
    if demo.actif():
        return fait
    d = gouvernance.lire(c, org_id, decision_id)
    if d is None or d["etat"] != "en_attente":
        return fait
    if email_configure() and _envoyer_mail is not None:
        for f in fondateurs(c, org_id):
            liens = creer_liens(c, org_id, decision_id, f["email"])
            if _envoyer_mail(f["email"], f"[Décision] {d['objectif'][:80]}", texte_decision(d, liens)):
                fait["email"] += 1
    if telegram_configure():
        fait["telegram"] = envoyer_telegram(d)
    if fait["email"] or fait["telegram"]:
        gouvernance.journaliser(c, org_id, "bureau", "decision.prevenue", decision_id,
                                ", ".join(k for k, v in (("e-mail", fait["email"]), ("Telegram", fait["telegram"])) if v))
    return fait


# ---------------------------------------------------------------- Telegram

def _api(methode: str, **params) -> dict | None:
    """Un appel à l'API Telegram du robot. Le jeton ne sort jamais des journaux."""
    import httpx

    try:
        r = httpx.post(f"{TELEGRAM}/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{methode}", json=params, timeout=65 if methode == "getUpdates" else 20)
        corps = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram %s : %s", methode, type(exc).__name__)
        return None
    if not corps.get("ok"):
        logger.warning("Telegram %s refusé : %s", methode, str(corps.get("description"))[:120])
        return None
    return corps.get("result")


def clavier(decision_id: str) -> dict:
    return {"inline_keyboard": [[{"text": "✅ Approuver", "callback_data": f"d:{decision_id}:approuver"},
                                 {"text": "✖ Refuser", "callback_data": f"d:{decision_id}:refuser"}],
                                [{"text": "✎ Demander une modification", "callback_data": f"d:{decision_id}:a_modifier"}]]}


def envoyer_telegram(d: dict) -> bool:
    res = _api("sendMessage", chat_id=os.environ["TELEGRAM_CHAT_ID"], text=texte_decision(d)[:3900], reply_markup=clavier(d["id"]),
               disable_web_page_preview=True)
    return res is not None


def _chat_autorise(chat_id) -> bool:
    return str(chat_id) == str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()


def traiter_mise_a_jour(c: db.Connexion, maj: dict, *, api=_api) -> str:
    """Une mise à jour reçue du robot. Renvoie ce qui a été fait (pour le journal et les tests). Tout ce qui ne vient pas de la
    conversation du fondateur est ignoré ; un bouton pressé tranche par `gouvernance.decider`, rien d'autre."""
    cb = maj.get("callback_query")
    if cb:
        msg = cb.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        if not _chat_autorise(chat_id) or not _chat_autorise((cb.get("from") or {}).get("id")):
            api("answerCallbackQuery", callback_query_id=cb.get("id"), text="Cette conversation n'est pas autorisée.")
            return "refuse:conversation"
        donnees = str(cb.get("data") or "")
        if not donnees.startswith("d:") or donnees.count(":") != 2:
            api("answerCallbackQuery", callback_query_id=cb.get("id"))
            return "ignore"
        _, decision_id, action = donnees.split(":")
        row = c.une("SELECT org_id, etat FROM decisions WHERE id = ?", (decision_id,))
        if row is None or row["etat"] != "en_attente":
            api("answerCallbackQuery", callback_query_id=cb.get("id"), text="Cette décision est déjà prise.")
            api("editMessageReplyMarkup", chat_id=chat_id, message_id=msg.get("message_id"), reply_markup={"inline_keyboard": []})
            return "deja"
        f = next(iter(fondateurs(c, row["org_id"])), None)
        if f is None:
            api("answerCallbackQuery", callback_query_id=cb.get("id"), text="Aucun fondateur sur ce bureau.")
            return "refuse:fondateur"
        if action == "a_modifier":
            envoye = api("sendMessage", chat_id=chat_id, text=f"Quelle consigne pour l'agent ? Répondez à ce message.\n(décision : {decision_id[:8]})",
                         reply_markup={"force_reply": True, "input_field_placeholder": "votre consigne"})
            if envoye:
                _consignes_attendues[int(envoye["message_id"])] = decision_id
            api("answerCallbackQuery", callback_query_id=cb.get("id"))
            return "consigne_demandee"
        if action not in ACTIONS_LIEN:
            api("answerCallbackQuery", callback_query_id=cb.get("id"))
            return "ignore"
        try:
            d = _trancher(c, row["org_id"], decision_id, action, email=f["email"], canal="Telegram")
        except ValueError as exc:
            api("answerCallbackQuery", callback_query_id=cb.get("id"), text="Décision déjà prise ou refusée.")
            return f"erreur:{exc}"
        api("answerCallbackQuery", callback_query_id=cb.get("id"), text=gouvernance.ETATS[d["etat"]])
        api("editMessageText", chat_id=chat_id, message_id=msg.get("message_id"),
            text=(texte_decision(d)[:3600] + f"\n\n— {gouvernance.ETATS[d['etat']]} depuis Telegram, {db.maintenant()[:16].replace('T', ' ')} UTC"))
        return f"decide:{d['etat']}"
    m = maj.get("message")
    if m and (m.get("reply_to_message") or {}).get("message_id") in _consignes_attendues:
        chat_id = (m.get("chat") or {}).get("id")
        if not _chat_autorise(chat_id) or not _chat_autorise((m.get("from") or {}).get("id")):
            return "refuse:conversation"
        decision_id = _consignes_attendues.pop(int(m["reply_to_message"]["message_id"]))
        consigne = str(m.get("text") or "").strip()[:2000]
        row = c.une("SELECT org_id FROM decisions WHERE id = ?", (decision_id,))
        f = next(iter(fondateurs(c, row["org_id"])), None) if row else None
        if f is None:
            return "refuse:fondateur"
        try:
            d = _trancher(c, row["org_id"], decision_id, "a_modifier", email=f["email"], canal="Telegram", consigne=consigne)
        except ValueError as exc:
            api("sendMessage", chat_id=chat_id, text=f"Impossible : {exc}")
            return f"erreur:{exc}"
        api("sendMessage", chat_id=chat_id, text=f"Consigne transmise à l'agent : « {consigne[:200]} ». Décision : {gouvernance.ETATS[d['etat']]}.")
        return "decide:a_modifier"
    return "ignore"


def _boucle(arret: threading.Event) -> None:
    decalage = 0
    while not arret.is_set():
        res = _api("getUpdates", offset=decalage, timeout=50, allowed_updates=["callback_query", "message"])
        if res is None:
            time.sleep(10)
            continue
        for maj in res:
            decalage = int(maj.get("update_id", decalage - 1)) + 1
            try:
                with db.connexion() as c:
                    fait = traiter_mise_a_jour(c, maj)
                if fait.startswith("refuse"):
                    logger.warning("Telegram : mise à jour refusée (%s)", fait)
            except Exception:  # noqa: BLE001 — une mise à jour malformée n'arrête pas le fil
                logger.exception("Telegram : mise à jour %s non traitée", maj.get("update_id"))


def demarrer_fil() -> threading.Thread | None:
    """Le fil qui écoute le robot, seulement si le robot est configuré, jamais en démonstration, une seule fois."""
    from core import demo

    if not telegram_configure() or demo.actif() or getattr(demarrer_fil, "_lance", False):
        return None
    arret = threading.Event()
    t = threading.Thread(target=_boucle, args=(arret,), name="telegram-decisions", daemon=True)
    t.start()
    demarrer_fil._lance = True  # type: ignore[attr-defined]
    demarrer_fil._arret = arret  # type: ignore[attr-defined]
    return t


# ---------------------------------------------------------------- frein (mémoire du processus, borné)

def autorise(cle: str, maximum: int, fenetre_s: int, maintenant: float | None = None) -> bool:
    t = maintenant or time.time()
    if len(_demandes) > 5000:
        for k in [k for k, v in _demandes.items() if not v or t - v[-1] > fenetre_s]:
            _demandes.pop(k, None)
    recents = [x for x in _demandes.get(cle, []) if t - x < fenetre_s]
    if len(recents) >= maximum:
        _demandes[cle] = recents
        return False
    _demandes[cle] = recents + [t]
    return True


def resume_configuration() -> str:
    """Pour la page du bureau : ce qui est branché, sans secret."""
    canaux = []
    if email_configure():
        canaux.append("e-mail")
    if telegram_configure():
        canaux.append("Telegram")
    return ", ".join(canaux) if canaux else "aucun"


def json_court(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False)[:200]

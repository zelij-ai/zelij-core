"""Suivi des contacts, léger et conforme : une fiche par personne, l'historique des échanges, la base légale écrite, la durée
de conservation, les droits exercés. Minimum nécessaire, jamais d'enrichissement depuis des sources tierces. Un contact
opposé ne reçoit plus rien ; un contact arrivé au bout de sa durée est oublié (anonymisé), et le journal des droits reste."""
from __future__ import annotations

import hashlib
from datetime import date, timedelta

from core import db

ROLES = ("prospect", "client", "partenaire", "fournisseur", "autre")
BASES_LEGALES = {"contrat": "exécution d'un contrat ou mesures précontractuelles", "interet_legitime": "intérêt légitime (relation professionnelle)",
                 "consentement": "consentement donné"}
SENS = ("entrant", "sortant", "note")
DROITS = ("acces", "rectification", "effacement", "opposition")
CONSERVATION_MOIS_DEFAUT = 36


def email_normalise(email: str) -> str:
    return (email or "").strip().lower()


def creer_contact(c: db.Connexion, org_id: str, *, email: str, nom: str, entreprise: str, role: str, base_legale: str, source: str,
                  conservation_mois: int | str = CONSERVATION_MOIS_DEFAUT, par: str) -> str:
    """La base légale est obligatoire à la création : pas de fiche sans raison écrite de la tenir."""
    from core.gouvernance import journaliser

    e = email_normalise(email)
    if "@" not in e:
        raise ValueError("adresse e-mail invalide")
    if base_legale not in BASES_LEGALES:
        raise ValueError("base légale obligatoire : contrat, interet_legitime ou consentement")
    if role not in ROLES:
        raise ValueError("rôle inconnu")
    try:
        mois = max(1, min(int(conservation_mois), 120))
    except (TypeError, ValueError):
        mois = CONSERVATION_MOIS_DEFAUT
    if c.une("SELECT id FROM contacts WHERE org_id = ? AND email = ? AND oublie_le IS NULL", (org_id, e)):
        raise ValueError("ce contact existe déjà")
    cid, now = db.nouvel_id(), db.maintenant()
    c.executer("INSERT INTO contacts (id, org_id, email, nom, entreprise, role, base_legale, source, conservation_mois, opposition, cree_le, maj_le) "
               "VALUES (?,?,?,?,?,?,?,?,?,0,?,?)", (cid, org_id, e, (nom or "").strip()[:160], (entreprise or "").strip()[:160], role, base_legale,
                                                   (source or "").strip()[:200], mois, now, now))
    journaliser(c, org_id, par, "contact.creation", cid, f"{role} · {base_legale}")     # ni adresse ni nom dans le journal : la fiche les porte
    return cid


def ajouter_echange(c: db.Connexion, org_id: str, contact_id: str, *, sens: str, canal: str, resume: str, par: str, date_: str | None = None) -> str:
    """Un échange sortant vers un contact opposé est refusé : la règle vit dans le code, pas dans la bonne volonté."""
    from core.gouvernance import journaliser

    if sens not in SENS:
        raise ValueError("sens inconnu")
    contact = lire(c, org_id, contact_id)
    if contact is None or contact["oublie_le"]:
        raise LookupError("contact introuvable")
    if sens == "sortant" and contact["opposition"]:
        raise PermissionError("ce contact s'est opposé : aucun message sortant")
    eid = db.nouvel_id()
    jour = (date_ or date.today().isoformat())[:10]
    c.executer("INSERT INTO echanges (id, org_id, contact_id, date, sens, canal, resume, auteur, cree_le) VALUES (?,?,?,?,?,?,?,?,?)",
               (eid, org_id, contact_id, jour, sens, (canal or "")[:60], (resume or "").strip()[:2000], par, db.maintenant()))
    c.executer("UPDATE contacts SET maj_le = ? WHERE id = ?", (db.maintenant(), contact_id))
    journaliser(c, org_id, par, f"echange.{sens}", contact_id, (canal or "")[:60])      # le résumé reste sur la fiche, pas dans le journal
    return eid


def exercer_droit(c: db.Connexion, org_id: str, contact_id: str, *, type_: str, par: str, detail: str = "") -> dict:
    """Accès, rectification, effacement, opposition : chaque droit exercé est daté et conservé même après l'oubli."""
    from core.gouvernance import journaliser

    if type_ not in DROITS:
        raise ValueError("droit inconnu")
    contact = lire(c, org_id, contact_id)
    if contact is None:
        raise LookupError("contact introuvable")
    c.executer("INSERT INTO droits (id, org_id, contact_id, empreinte_email, type, date, par, detail) VALUES (?,?,?,?,?,?,?,?)",
               (db.nouvel_id(), org_id, contact_id, _empreinte(contact["email"]), type_, db.maintenant(), par, (detail or "")[:600]))
    if type_ == "opposition":
        c.executer("UPDATE contacts SET opposition = 1, maj_le = ? WHERE id = ?", (db.maintenant(), contact_id))
    if type_ == "effacement":
        oublier(c, org_id, contact_id, par=par, motif="demande d'effacement")
    journaliser(c, org_id, par, f"droit.{type_}", contact_id, "")       # le détail saisi vit dans le registre des droits, effacé à l'oubli
    return lire(c, org_id, contact_id) or {}


def _empreinte(email: str) -> str:
    return hashlib.sha256(email_normalise(email).encode()).hexdigest()[:24]


def oublier(c: db.Connexion, org_id: str, contact_id: str, *, par: str, motif: str) -> None:
    """Anonymise : e-mail remplacé par une empreinte, nom et entreprise effacés, résumés d'échanges supprimés. Les dates et le
    journal des droits restent, pour prouver ce qui a été fait."""
    from core.gouvernance import journaliser

    contact = c.une("SELECT * FROM contacts WHERE id = ? AND org_id = ?", (contact_id, org_id))
    if contact is None or contact["oublie_le"]:
        return
    c.executer("UPDATE contacts SET email = ?, nom = '', entreprise = '', source = '', oublie_le = ?, maj_le = ? WHERE id = ?",
               ("oublie:" + _empreinte(contact["email"]), db.maintenant(), db.maintenant(), contact_id))
    c.executer("UPDATE echanges SET resume = '', canal = '' WHERE contact_id = ? AND org_id = ?", (contact_id, org_id))
    # Le journal et le registre des droits gardent la trace (qui, quoi, quand), plus le contenu : une adresse ou un nom écrits
    # là par une version antérieure, ou dans le détail d'une demande, disparaissent avec la fiche.
    c.executer("UPDATE journal SET detail = '' WHERE org_id = ? AND cible = ?", (org_id, contact_id))
    c.executer("UPDATE droits SET detail = '' WHERE org_id = ? AND contact_id = ?", (org_id, contact_id))
    journaliser(c, org_id, par, "contact.oubli", contact_id, motif)


def lire(c: db.Connexion, org_id: str, contact_id: str) -> dict | None:
    return c.une("SELECT * FROM contacts WHERE id = ? AND org_id = ?", (contact_id, org_id))


def echanges(c: db.Connexion, org_id: str, contact_id: str) -> list[dict]:
    return c.lignes("SELECT * FROM echanges WHERE org_id = ? AND contact_id = ? ORDER BY date DESC, cree_le DESC", (org_id, contact_id))


def droits(c: db.Connexion, org_id: str, contact_id: str) -> list[dict]:
    return c.lignes("SELECT * FROM droits WHERE org_id = ? AND contact_id = ? ORDER BY date DESC", (org_id, contact_id))


def date_d_oubli(contact: dict, dernier_echange: str | None) -> date:
    """La durée court depuis le dernier échange, sinon depuis la création."""
    base = date.fromisoformat((dernier_echange or contact["cree_le"])[:10])
    return base + timedelta(days=int(contact["conservation_mois"]) * 30)


def liste(c: db.Connexion, org_id: str, *, filtre: str = "tous", aujourd_hui: date | None = None) -> list[dict]:
    aujourd_hui = aujourd_hui or date.today()
    rows = c.lignes("SELECT ct.*, (SELECT MAX(e.date) FROM echanges e WHERE e.contact_id = ct.id) AS dernier_echange, "
                    "(SELECT COUNT(*) FROM echanges e WHERE e.contact_id = ct.id) AS nb_echanges FROM contacts ct WHERE ct.org_id = ? ORDER BY ct.maj_le DESC", (org_id,))
    out = []
    for r in rows:
        r["oubli_prevu"] = date_d_oubli(r, r["dernier_echange"]).isoformat() if not r["oublie_le"] else ""
        r["a_oublier"] = bool(not r["oublie_le"] and date.fromisoformat(r["oubli_prevu"]) <= aujourd_hui)
        r["base_legale_libelle"] = BASES_LEGALES.get(r["base_legale"], r["base_legale"])
        out.append(r)
    if filtre == "actifs":
        return [r for r in out if not r["oublie_le"]]
    if filtre == "a_traiter":
        return [r for r in out if not r["oublie_le"] and (r["a_oublier"] or r["opposition"])]
    if filtre == "oublies":
        return [r for r in out if r["oublie_le"]]
    return out


def peut_contacter(c: db.Connexion, org_id: str, contact_id: str) -> tuple[bool, str]:
    ct = lire(c, org_id, contact_id)
    if ct is None or ct["oublie_le"]:
        return False, "contact inconnu ou oublié"
    if ct["opposition"]:
        return False, "opposition exercée"
    return True, ""


def faits_pour_agent(c: db.Connexion, org_id: str) -> dict:
    """Ce que l'agent Finances & clients reçoit : des comptes et des listes anonymisées, jamais de données au-delà du nécessaire."""
    tous = liste(c, org_id)
    actifs = [r for r in tous if not r["oublie_le"]]
    return {"contacts_actifs": len(actifs), "opposes": sum(1 for r in actifs if r["opposition"]),
            "a_oublier": [{"id": r["id"], "role": r["role"], "oubli_prevu": r["oubli_prevu"]} for r in actifs if r["a_oublier"]],
            "sans_echange_depuis_90_jours": sum(1 for r in actifs if not r["dernier_echange"] or (date.today() - date.fromisoformat(r["dernier_echange"])).days > 90),
            "oublies": len(tous) - len(actifs), "regle": "base légale écrite sur chaque fiche ; opposition = plus aucun sortant ; oubli à l'échéance"}

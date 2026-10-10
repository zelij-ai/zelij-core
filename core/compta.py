"""Comptabilité légère : ce que l'entreprise encaisse (confirmé par la plateforme de paiement), ce qu'elle paie (charges
déclarées), ce que coûtent les agents. Un journal par mois, un export CSV pour l'expert-comptable. Rien n'est déclaré ni
facturé ici : on prépare, on ne remplace personne.

Ventes : importées depuis Stripe (clé restreinte en lecture, variable STRIPE_SECRET_KEY) ou saisies à la main avec leur
preuve. Une vente n'existe que confirmée (`succeeded`) : la parole d'un client n'est pas un encaissement."""
from __future__ import annotations

import csv
import io
import math
import os
from datetime import date, datetime, timedelta, timezone

import httpx

from core import db, passerelle

CATEGORIES = ("abonnement", "hebergement", "domaine", "prestataire", "materiel", "autre")
PERIODICITES = ("unique", "mensuelle", "annuelle")
STRIPE_API = "https://api.stripe.com/v1/charges"
MONTANT_MAX_EUR = 1_000_000_000      # garde-fou de saisie : ni infini, ni « pas un nombre », ni faute de frappe à douze zéros


# ---------------------------------------------------------------- charges

def valider_charge(*, date_: str, libelle: str, montant_eur: str, categorie: str, periodicite: str, jusqu_a: str = "", piece: str = "") -> dict:
    erreurs = []
    try:
        d = date.fromisoformat((date_ or "").strip())
    except ValueError:
        erreurs.append("date invalide (AAAA-MM-JJ)")
        d = None
    try:
        montant = round(float(str(montant_eur).replace(",", ".").replace(" ", "")), 2)
        if not math.isfinite(montant) or montant <= 0 or montant > MONTANT_MAX_EUR:
            erreurs.append("montant positif attendu")
            montant = 0.0
    except ValueError:
        erreurs.append("montant invalide")
        montant = 0.0
    if not (libelle or "").strip():
        erreurs.append("libellé manquant")
    if categorie not in CATEGORIES:
        erreurs.append("catégorie inconnue")
    if periodicite not in PERIODICITES:
        erreurs.append("périodicité inconnue")
    fin = None
    if (jusqu_a or "").strip():
        try:
            fin = date.fromisoformat(jusqu_a.strip())
        except ValueError:
            erreurs.append("date de fin invalide")
    if erreurs:
        raise ValueError(" ; ".join(erreurs))
    return {"date": d.isoformat(), "libelle": libelle.strip()[:200], "montant_eur": montant, "categorie": categorie, "periodicite": periodicite,
            "jusqu_a": fin.isoformat() if fin else "", "piece": (piece or "").strip()[:200]}


def ajouter_charge(c: db.Connexion, org_id: str, charge: dict, *, par: str) -> str:
    from core.gouvernance import journaliser

    cid = db.nouvel_id()
    c.executer("INSERT INTO charges (id, org_id, date, libelle, montant_eur, categorie, periodicite, jusqu_a, piece, cree_le) VALUES (?,?,?,?,?,?,?,?,?,?)",
               (cid, org_id, charge["date"], charge["libelle"], charge["montant_eur"], charge["categorie"], charge["periodicite"], charge["jusqu_a"],
                charge["piece"], db.maintenant()))
    journaliser(c, org_id, par, "charge.ajout", cid, f"{charge['libelle']} {charge['montant_eur']:.2f} € ({charge['periodicite']})")
    return cid


def occurrences(charge: dict, mois: str) -> list[dict]:
    """Les échéances d'une charge qui tombent dans le mois AAAA-MM (une charge mensuelle revient chaque mois à sa date)."""
    debut = date.fromisoformat(charge["date"])
    fin = date.fromisoformat(charge["jusqu_a"]) if charge.get("jusqu_a") else None
    annee, m = int(mois[:4]), int(mois[5:7])
    premier = date(annee, m, 1)
    dernier = (date(annee + (m == 12), (m % 12) + 1, 1) - timedelta(days=1))
    if debut > dernier or (fin and fin < premier):
        return []
    if charge["periodicite"] == "unique":
        return [dict(charge)] if premier <= debut <= dernier else []
    if charge["periodicite"] == "mensuelle":
        jour = min(debut.day, dernier.day)
        echeance = date(annee, m, jour)
        return [{**charge, "date": echeance.isoformat()}] if (not fin or echeance <= fin) else []
    if debut.month == m:   # annuelle
        echeance = date(annee, m, min(debut.day, dernier.day))
        return [{**charge, "date": echeance.isoformat()}] if (not fin or echeance <= fin) else []
    return []


# ---------------------------------------------------------------- ventes

def ajouter_vente(c: db.Connexion, org_id: str, *, source: str, reference: str, date_: str, libelle: str, montant_eur: float, client: str, par: str) -> bool:
    """Idempotent sur (org, source, référence) : réimporter ne double jamais."""
    from core.gouvernance import journaliser

    if c.une("SELECT id FROM ventes WHERE org_id = ? AND source = ? AND reference = ?", (org_id, source, reference)):
        return False
    c.executer("INSERT INTO ventes (id, org_id, source, reference, date, libelle, montant_eur, client, statut, cree_le) VALUES (?,?,?,?,?,?,?,?,?,?)",
               (db.nouvel_id(), org_id, source, reference[:120], date_, libelle[:200], round(float(montant_eur), 2), (client or "")[:200], "confirmee", db.maintenant()))
    journaliser(c, org_id, par, "vente.ajout", reference[:60], f"{libelle[:80]} {float(montant_eur):.2f} € ({source})")
    return True


def importer_stripe(c: db.Connexion, org_id: str, *, par: str, depuis: date | None = None, client: httpx.Client | None = None, cle: str | None = None) -> dict:
    """Lit les paiements confirmés chez Stripe et les ajoute comme ventes. Clé restreinte en lecture, jamais stockée ici."""
    cle = cle if cle is not None else os.environ.get("STRIPE_SECRET_KEY", "")
    if not cle:
        return {"importees": 0, "lues": 0, "erreur": "clé Stripe absente (STRIPE_SECRET_KEY)"}
    depuis = depuis or (date.today() - timedelta(days=120))
    propre = client is None
    client = client or httpx.Client(timeout=30)
    importees = lues = 0
    try:
        params = {"limit": 100, "created[gte]": int(datetime(depuis.year, depuis.month, depuis.day).timestamp())}
        while True:
            r = client.get(STRIPE_API, params=params, auth=(cle, ""))
            if r.status_code != 200:
                return {"importees": importees, "lues": lues, "erreur": f"Stripe a répondu {r.status_code}"}
            corps = r.json()
            for ch in corps.get("data", []):
                lues += 1
                if ch.get("status") != "succeeded" or ch.get("refunded"):
                    continue
                jour = datetime.fromtimestamp(int(ch.get("created", 0)), timezone.utc).date().isoformat()
                montant = int(ch.get("amount_captured") or ch.get("amount") or 0) / 100
                if montant <= 0:
                    continue
                libelle = ch.get("description") or ch.get("statement_descriptor") or "Paiement Stripe"
                client_nom = (ch.get("billing_details") or {}).get("name") or ch.get("receipt_email") or ""
                if ajouter_vente(c, org_id, source="stripe", reference=str(ch.get("id")), date_=jour, libelle=str(libelle), montant_eur=montant,
                                 client=str(client_nom), par=par):
                    importees += 1
            if corps.get("has_more") and corps.get("data"):
                params["starting_after"] = corps["data"][-1]["id"]
            else:
                break
    except (httpx.HTTPError, ValueError) as exc:
        return {"importees": importees, "lues": lues, "erreur": f"Stripe injoignable : {str(exc)[:160]}"}
    finally:
        if propre:
            client.close()
    return {"importees": importees, "lues": lues, "erreur": None}


# ---------------------------------------------------------------- journal du mois

def journal(c: db.Connexion, org_id: str, mois: str) -> dict:
    ventes = c.lignes("SELECT * FROM ventes WHERE org_id = ? AND date LIKE ? ORDER BY date", (org_id, mois + "%"))
    charges = []
    for ch in c.lignes("SELECT * FROM charges WHERE org_id = ? ORDER BY date", (org_id,)):
        charges.extend(occurrences(ch, mois))
    charges.sort(key=lambda x: x["date"])
    agents = c.lignes("SELECT agent, COUNT(*) AS n, COALESCE(SUM(cout_usd), 0) AS usd FROM executions WHERE org_id = ? AND cree_le LIKE ? GROUP BY agent ORDER BY agent",
                      (org_id, mois + "%"))
    taux = passerelle.taux_usd_eur()
    for a in agents:
        a["eur"] = round(float(a["usd"]) * taux, 2)
    total_ventes = round(sum(float(v["montant_eur"]) for v in ventes), 2)
    total_charges = round(sum(float(ch["montant_eur"]) for ch in charges), 2)
    total_agents = round(sum(a["eur"] for a in agents), 2)
    return {"mois": mois, "ventes": ventes, "charges": charges, "agents": agents, "total_ventes": total_ventes, "total_charges": total_charges,
            "total_agents": total_agents, "solde": round(total_ventes - total_charges - total_agents, 2), "taux_usd_eur": taux}


def cellule_sure(v) -> str:
    """Un tableur exécute une cellule qui commence par = + - @ ou un caractère de contrôle : on la neutralise d'une apostrophe."""
    t = str(v if v is not None else "")
    return "'" + t if t[:1] in ("=", "+", "-", "@", "\t", "\r", "\n") else t


def export_csv(j: dict) -> str:
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["date", "type", "libelle", "montant_eur", "source", "reference"])
    for v in j["ventes"]:
        w.writerow([v["date"], "vente", cellule_sure(v["libelle"]), f"{float(v['montant_eur']):.2f}", cellule_sure(v["source"]), cellule_sure(v["reference"])])
    for ch in j["charges"]:
        w.writerow([ch["date"], "charge", cellule_sure(ch["libelle"]), f"{-float(ch['montant_eur']):.2f}", ch["categorie"], cellule_sure(ch.get("piece", ""))])
    for a in j["agents"]:
        w.writerow([j["mois"] + "-01", "agents", cellule_sure(f"coût des appels de {a['agent']} ({a['n']} exécution(s))"), f"{-a['eur']:.2f}", "modeles", ""])
    w.writerow([j["mois"] + "-01", "solde", "ventes - charges - agents", f"{j['solde']:.2f}", "", ""])
    return out.getvalue()


def faits_pour_agent(j: dict) -> dict:
    """Ce que l'agent Finances & clients reçoit : des totaux datés, jamais une estimation."""
    return {"mois": j["mois"], "ventes_confirmees_eur": j["total_ventes"], "nombre_ventes": len(j["ventes"]), "charges_eur": j["total_charges"],
            "cout_agents_eur": j["total_agents"], "solde_eur": j["solde"], "taux_usd_eur": j["taux_usd_eur"],
            "source": "ventes confirmées par la plateforme de paiement ou saisies avec preuve ; charges déclarées par le fondateur ; coût des agents mesuré"}

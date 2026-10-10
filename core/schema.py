"""Schéma du noyau, créé au démarrage. Même SQL pour PostgreSQL et SQLite. Les décisions et le journal ne sont jamais
modifiés après coup : seul l'état d'une décision change, et le changement est journalisé."""
from __future__ import annotations

from core import db

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS organisations (
        id TEXT PRIMARY KEY, nom TEXT NOT NULL, cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS utilisateurs (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL REFERENCES organisations(id), email TEXT NOT NULL UNIQUE,
        nom TEXT NOT NULL DEFAULT '', role TEXT NOT NULL DEFAULT 'fondateur', cree_le TEXT NOT NULL, derniere_connexion TEXT)""",
    """CREATE TABLE IF NOT EXISTS jetons_connexion (
        id TEXT PRIMARY KEY, email TEXT NOT NULL, empreinte TEXT NOT NULL UNIQUE, expire_le TEXT NOT NULL, utilise_le TEXT,
        org_id TEXT, cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS executions (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, agent TEXT NOT NULL, tache TEXT NOT NULL, statut TEXT NOT NULL,
        entree TEXT NOT NULL DEFAULT '', sortie TEXT NOT NULL DEFAULT '', outils TEXT NOT NULL DEFAULT '[]', modele TEXT NOT NULL DEFAULT '',
        tokens_entree INTEGER NOT NULL DEFAULT 0, tokens_sortie INTEGER NOT NULL DEFAULT 0, cout_usd REAL NOT NULL DEFAULT 0,
        tours INTEGER NOT NULL DEFAULT 0, detail TEXT NOT NULL DEFAULT '', cree_le TEXT NOT NULL, fini_le TEXT)""",
    """CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, demandeur TEXT NOT NULL, objectif TEXT NOT NULL, proposition TEXT NOT NULL DEFAULT '',
        pourquoi_maintenant TEXT NOT NULL DEFAULT '', options TEXT NOT NULL DEFAULT '[]', recommandation TEXT NOT NULL DEFAULT '',
        risques TEXT NOT NULL DEFAULT '[]', reversibilite TEXT NOT NULL DEFAULT 'reversible', plan TEXT NOT NULL DEFAULT '[]',
        retour_arriere TEXT NOT NULL DEFAULT '[]', impact_eur REAL NOT NULL DEFAULT 0, etat TEXT NOT NULL DEFAULT 'en_attente',
        consigne TEXT NOT NULL DEFAULT '', decidee_par TEXT, decidee_le TEXT, portee TEXT NOT NULL DEFAULT '', execution_id TEXT,
        agent_cible TEXT NOT NULL DEFAULT '', tache TEXT NOT NULL DEFAULT '', execution_apres TEXT,
        cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS journal (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, acteur TEXT NOT NULL, action TEXT NOT NULL, cible TEXT NOT NULL DEFAULT '',
        detail TEXT NOT NULL DEFAULT '', cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS modules (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, nom TEXT NOT NULL, version TEXT NOT NULL, type TEXT NOT NULL,
        interface TEXT NOT NULL, empreinte_cle TEXT NOT NULL DEFAULT '', installe_le TEXT NOT NULL, actif INTEGER NOT NULL DEFAULT 1)""",
    # Lot 3 : comptabilité légère et suivi des contacts.
    """CREATE TABLE IF NOT EXISTS ventes (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, source TEXT NOT NULL, reference TEXT NOT NULL, date TEXT NOT NULL, libelle TEXT NOT NULL,
        montant_eur REAL NOT NULL, client TEXT NOT NULL DEFAULT '', statut TEXT NOT NULL DEFAULT 'confirmee', cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS charges (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, date TEXT NOT NULL, libelle TEXT NOT NULL, montant_eur REAL NOT NULL, categorie TEXT NOT NULL,
        periodicite TEXT NOT NULL, jusqu_a TEXT NOT NULL DEFAULT '', piece TEXT NOT NULL DEFAULT '', cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS contacts (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, email TEXT NOT NULL, nom TEXT NOT NULL DEFAULT '', entreprise TEXT NOT NULL DEFAULT '',
        role TEXT NOT NULL, base_legale TEXT NOT NULL, source TEXT NOT NULL DEFAULT '', conservation_mois INTEGER NOT NULL DEFAULT 36,
        opposition INTEGER NOT NULL DEFAULT 0, cree_le TEXT NOT NULL, maj_le TEXT NOT NULL, oublie_le TEXT)""",
    """CREATE TABLE IF NOT EXISTS echanges (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, contact_id TEXT NOT NULL, date TEXT NOT NULL, sens TEXT NOT NULL, canal TEXT NOT NULL DEFAULT '',
        resume TEXT NOT NULL DEFAULT '', auteur TEXT NOT NULL, cree_le TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS droits (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, contact_id TEXT NOT NULL, empreinte_email TEXT NOT NULL, type TEXT NOT NULL, date TEXT NOT NULL,
        par TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '')""",
    # Lot 4 : publications proposées au site.
    """CREATE TABLE IF NOT EXISTS publications (
        id TEXT PRIMARY KEY, org_id TEXT NOT NULL, slug TEXT NOT NULL, titre TEXT NOT NULL, canal TEXT NOT NULL DEFAULT '', page TEXT NOT NULL,
        etat TEXT NOT NULL DEFAULT 'brouillon', reference TEXT NOT NULL DEFAULT '', detail TEXT NOT NULL DEFAULT '', decision_id TEXT,
        cree_le TEXT NOT NULL, publie_le TEXT)""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_ventes_ref ON ventes(org_id, source, reference)",
    "CREATE INDEX IF NOT EXISTS ix_contacts_org ON contacts(org_id, maj_le)",
    "CREATE INDEX IF NOT EXISTS ix_echanges_contact ON echanges(contact_id, date)",
    "CREATE INDEX IF NOT EXISTS ix_executions_org ON executions(org_id, cree_le)",
    "CREATE INDEX IF NOT EXISTS ix_decisions_org ON decisions(org_id, etat, cree_le)",
    "CREATE INDEX IF NOT EXISTS ix_journal_org ON journal(org_id, cree_le)",
]


# Colonnes ajoutées après la première version : posées si elles manquent (installations déjà en place).
AJOUTS = [
    ("decisions", "agent_cible", "TEXT NOT NULL DEFAULT ''"),
    ("decisions", "tache", "TEXT NOT NULL DEFAULT ''"),
    ("decisions", "execution_apres", "TEXT"),
    ("organisations", "jeton_public", "TEXT"),       # lot 4 : page publique « regardez nos agents travailler »
    ("utilisateurs", "session_n", "INTEGER NOT NULL DEFAULT 0"),   # 0.7.4 : la déconnexion révoque les cookies déjà émis
    ("decisions", "provenance", "TEXT NOT NULL DEFAULT ''"),         # 0.7.6 : ce que l'agent a lu au dehors en préparant la décision
]


def migrer() -> None:
    with db.connexion() as c:
        for sql in SCHEMA:
            c.executer(sql)
        for table, colonne, definition in AJOUTS:
            if colonne not in {r["nom"] for r in _colonnes(c, table)}:
                c.executer(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")


def _colonnes(c: db.Connexion, table: str) -> list[dict]:
    if c.postgres:
        return [{"nom": r["column_name"]} for r in c.lignes("SELECT column_name FROM information_schema.columns WHERE table_name = ?", (table,))]
    return [{"nom": r["name"]} for r in c.lignes(f"PRAGMA table_info({table})")]


if __name__ == "__main__":
    migrer()
    print("schéma Zelij Core à jour")

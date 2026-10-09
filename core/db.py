"""Accès aux données : PostgreSQL en production (psycopg), SQLite en local et dans les tests, avec le même SQL.
Les requêtes écrivent « ? » comme marqueur ; il devient « %s » pour psycopg. Identifiants : uuid4 hexadécimal ; dates : ISO 8601
UTC en texte. Toute requête métier filtre par `org_id`."""
from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./data/zelij-core.sqlite")


def maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def mois_courant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def nouvel_id() -> str:
    return uuid.uuid4().hex


class Connexion:
    def __init__(self, brute, postgres: bool):
        self._c = brute
        self.postgres = postgres

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.postgres else sql

    def executer(self, sql: str, params: tuple = ()) -> None:
        cur = self._c.cursor()
        cur.execute(self._sql(sql), params)
        cur.close()

    def lignes(self, sql: str, params: tuple = ()) -> list[dict]:
        cur = self._c.cursor()
        cur.execute(self._sql(sql), params)
        noms = [d[0] for d in cur.description]
        out = [dict(zip(noms, r)) for r in cur.fetchall()]
        cur.close()
        return out

    def une(self, sql: str, params: tuple = ()) -> dict | None:
        r = self.lignes(sql, params)
        return r[0] if r else None

    def commit(self) -> None:
        self._c.commit()

    def rollback(self) -> None:
        self._c.rollback()

    def fermer(self) -> None:
        self._c.close()


def _ouvrir() -> Connexion:
    u = url()
    if u.startswith("postgres"):
        import psycopg

        return Connexion(psycopg.connect(u), True)
    chemin = u.replace("sqlite:///", "", 1)
    if chemin != ":memory:":
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(chemin, check_same_thread=False)
    c.execute("PRAGMA foreign_keys = ON")
    return Connexion(c, False)


@contextmanager
def connexion():
    """Une connexion par requête : validée en sortie normale, annulée sur exception."""
    c = _ouvrir()
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.fermer()

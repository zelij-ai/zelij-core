"""Passerelle vers les modèles : la clé du fondateur, le coût de chaque appel, le plafond mensuel.

Tarifs publics par million de tokens, relevés le 10/10/2026 sur la page de tarifs de l'éditeur
(https://platform.claude.com/docs/en/about-claude/pricing) ; à mettre à jour avec la date du relevé. Le coût est calculé à partir de `usage` de chaque réponse et enregistré avec l'exécution. Le plafond
mensuel (en euros) bloque tout nouvel appel quand il est atteint : un agent qui coûte sans prévenir trahit la promesse."""
from __future__ import annotations

import os
from typing import Any

TARIFS_USD_PAR_MILLION = {   # (entrée, sortie, lecture de cache)
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-opus-5": (5.00, 25.00, 0.50),
    "claude-sonnet-5": (2.00, 10.00, 0.20),
}
# Palier : au-delà de ce nombre de tokens d'entrée dans une requête, le tarif de la requête change (entrée, sortie, lecture de cache).
PALIERS_USD_PAR_MILLION = {"claude-haiku-5-5": (100_000, (0.50, 2.50, 0.05))}
TARIFS_RELEVES_LE = "2026-10-10"


def taux_usd_eur() -> float:
    """Taux de conversion déclaré par le fondateur (variable TAUX_USD_EUR) ; 0,92 par défaut, à ajuster."""
    try:
        return float(os.environ.get("TAUX_USD_EUR", "0.92"))
    except ValueError:
        return 0.92


def plafond_mensuel_eur() -> float:
    try:
        return float(os.environ.get("PLAFOND_MENSUEL_EUR", "50"))
    except ValueError:
        return 50.0


def cout_usd(modele: str, usage: Any) -> float:
    """Coût d'une réponse d'après son `usage` (tokens d'entrée, de sortie, lus en cache)."""
    entree, sortie, cache = TARIFS_USD_PAR_MILLION.get(modele, TARIFS_USD_PAR_MILLION["claude-opus-5-5"])
    lire = (lambda k: getattr(usage, k, None) if not isinstance(usage, dict) else usage.get(k)) if usage is not None else (lambda k: 0)
    t_in = int(lire("input_tokens") or 0)
    t_out = int(lire("output_tokens") or 0)
    t_cache = int(lire("cache_read_input_tokens") or 0)
    seuil, tarif_haut = PALIERS_USD_PAR_MILLION.get(modele, (0, None))
    if tarif_haut and t_in + t_cache > seuil:
        entree, sortie, cache = tarif_haut
    return round((t_in * entree + t_out * sortie + t_cache * cache) / 1_000_000, 6)


def cout_du_mois_eur(c, org_id: str, mois: str) -> float:
    r = c.une("SELECT COALESCE(SUM(cout_usd), 0) AS total FROM executions WHERE org_id = ? AND cree_le LIKE ?", (org_id, mois + "%"))
    return round(float((r or {}).get("total") or 0) * taux_usd_eur(), 4)


def plafond_atteint(c, org_id: str, mois: str) -> tuple[bool, float, float]:
    depense = cout_du_mois_eur(c, org_id, mois)
    plafond = plafond_mensuel_eur()
    return depense >= plafond, depense, plafond


def client():
    """Le client officiel ; la clé vient de l'environnement (ANTHROPIC_API_KEY), jamais du code ni de la base."""
    import anthropic

    return anthropic.Anthropic()


def appeler(*, modele: str, system: str, messages: list, tools: list | None, max_tokens: int = 16000):
    """Un appel au modèle. Pas de `thinking` explicite : les modèles actuels raisonnent par défaut ; l'effort reste au défaut."""
    params: dict = {"model": modele, "max_tokens": max_tokens, "system": system, "messages": messages}
    if tools:
        params["tools"] = tools
    return client().messages.create(**params)

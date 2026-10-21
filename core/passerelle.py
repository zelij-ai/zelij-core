"""Passerelle vers les modèles : la clé du fondateur, le coût de chaque appel, le plafond mensuel.

Tarifs publics par million de tokens, relevés le 10/10/2026 sur la page de tarifs de l'éditeur
(https://platform.claude.com/docs/en/about-claude/pricing) ; à mettre à jour avec la date du relevé. Le coût est calculé à partir de `usage` de chaque réponse et enregistré avec l'exécution. Le plafond
mensuel (en euros) bloque tout nouvel appel quand il est atteint : un agent qui coûte sans prévenir trahit la promesse."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace
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


def tarifs_declares() -> dict[str, tuple[float, float, float]]:
    """Tarifs posés par le fondateur pour d'autres modèles (variable MODELE_TARIFS, JSON : {"nom": [entrée, sortie, cache]} en
    dollars par million de tokens). Un modèle local se déclare à zéro : {"llama3.3": [0, 0, 0]}."""
    try:
        brut = json.loads(os.environ.get("MODELE_TARIFS", "") or "{}")
    except ValueError:
        return {}
    out = {}
    for nom, t in (brut.items() if isinstance(brut, dict) else ()):
        try:
            e, s, c = (float(x) for x in (list(t) + [0, 0, 0])[:3])
        except (TypeError, ValueError):
            continue
        if min(e, s, c) >= 0:
            out[str(nom)] = (e, s, c)
    return out


def tarif_connu(modele: str) -> bool:
    return modele in tarifs_declares() or modele in TARIFS_USD_PAR_MILLION


def cout_usd(modele: str, usage: Any) -> float:
    """Coût d'une réponse d'après son `usage` (tokens d'entrée, de sortie, lus en cache). Un modèle dont le tarif n'est ni connu
    ni déclaré est compté au tarif le plus cher de la table : jamais zéro par oubli."""
    entree, sortie, cache = tarifs_declares().get(modele) or TARIFS_USD_PAR_MILLION.get(modele, TARIFS_USD_PAR_MILLION["claude-opus-5-5"])
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
    total = float((r or {}).get("total") or 0)
    try:   # 0.9.4 : l'avocat du diable coûte un appel par décision ; il compte dans le même plafond
        a = c.une("SELECT COALESCE(SUM(avocat_cout_usd), 0) AS total FROM decisions WHERE org_id = ? AND cree_le LIKE ?", (org_id, mois + "%"))
        total += float((a or {}).get("total") or 0)
    except Exception:  # noqa: BLE001 — base pas encore migrée
        pass
    return round(total * taux_usd_eur(), 4)


def plafond_atteint(c, org_id: str, mois: str) -> tuple[bool, float, float]:
    depense = cout_du_mois_eur(c, org_id, mois)
    plafond = plafond_mensuel_eur()
    return depense >= plafond, depense, plafond


def client():
    """Le client officiel ; la clé vient de l'environnement (ANTHROPIC_API_KEY), jamais du code ni de la base."""
    import anthropic

    return anthropic.Anthropic()


# ---------------------------------------------------------------- fournisseurs de modèles
# Claude par défaut. « openai » désigne toute interface compatible avec celle d'OpenAI : OpenAI lui-même, un modèle local
# (Ollama, LM Studio, vLLM), Mistral, OpenRouter… Le bureau ne change pas : mêmes agents, mêmes outils, mêmes garde-fous
# (ils sont dans le code, pas dans le modèle). Ce qui change : où partent vos données, et la qualité du travail des agents.
FOURNISSEURS = {"anthropic": "Claude (Anthropic)", "openai": "interface compatible OpenAI"}
OPENAI_URL = "https://api.openai.com/v1"


def fournisseur() -> str:
    f = os.environ.get("MODELE_FOURNISSEUR", "anthropic").strip().lower() or "anthropic"
    if f not in FOURNISSEURS:
        raise RuntimeError(f"MODELE_FOURNISSEUR inconnu : {f[:30]} (valeurs : {', '.join(FOURNISSEURS)})")
    return f


def adresse_openai() -> str:
    return (os.environ.get("OPENAI_BASE_URL", "").strip() or OPENAI_URL).rstrip("/")


def description() -> dict:
    """Ce que le bureau affiche : quel fournisseur, à quelle adresse, et si l'appel reste sur la machine."""
    f = fournisseur()
    if f == "anthropic":
        return {"fournisseur": f, "libelle": FOURNISSEURS[f], "adresse": "", "local": False}
    adresse = adresse_openai()
    hote = adresse.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0].lower()
    local = hote in ("localhost", "127.0.0.1", "::1", "host.docker.internal") or hote.endswith((".local", ".internal", ".lan"))
    return {"fournisseur": f, "libelle": "modèle local" if local else hote, "adresse": adresse, "local": local}


def _bloc(b, cle: str, defaut=None):
    return b.get(cle, defaut) if isinstance(b, dict) else getattr(b, cle, defaut)


def vers_openai(system: str, messages: list) -> list[dict]:
    """La conversation de l'exécuteur (texte, appels d'outils, résultats d'outils) dans la forme attendue par l'interface OpenAI."""
    out: list[dict] = [{"role": "system", "content": system}] if system else []
    for m in messages:
        contenu = m.get("content")
        if isinstance(contenu, str):
            out.append({"role": m["role"], "content": contenu})
        elif m["role"] == "assistant":
            texte = "".join(str(_bloc(b, "text", "") or "") for b in contenu if _bloc(b, "type") == "text")
            appels = [{"id": _bloc(b, "id"), "type": "function", "function": {"name": _bloc(b, "name"), "arguments": json.dumps(_bloc(b, "input") or {}, ensure_ascii=False)}}
                      for b in contenu if _bloc(b, "type") == "tool_use"]
            out.append({"role": "assistant", "content": texte or None, **({"tool_calls": appels} if appels else {})})
        else:
            for b in contenu:
                if _bloc(b, "type") == "tool_result":
                    out.append({"role": "tool", "tool_call_id": _bloc(b, "tool_use_id"), "content": str(_bloc(b, "content", ""))})
                elif _bloc(b, "type") == "text":
                    out.append({"role": "user", "content": str(_bloc(b, "text", ""))})
    return out


def outils_openai(tools: list | None) -> list[dict]:
    return [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}}
            for t in (tools or [])]


def depuis_openai(d: dict) -> SimpleNamespace:
    """La réponse d'une interface OpenAI dans la forme que lit l'exécuteur : blocs de texte et d'appels d'outils, raison d'arrêt, usage."""
    choix = (d.get("choices") or [{}])[0]
    msg = choix.get("message") or {}
    blocs: list = []
    if msg.get("content"):
        blocs.append(SimpleNamespace(type="text", text=str(msg["content"])))
    for i, tc in enumerate(msg.get("tool_calls") or []):
        f = tc.get("function") or {}
        try:
            entree = json.loads(f.get("arguments") or "{}")
        except ValueError:
            entree = {}
        blocs.append(SimpleNamespace(type="tool_use", id=str(tc.get("id") or f"appel-{i}"), name=str(f.get("name") or ""), input=entree if isinstance(entree, dict) else {}))
    appels = any(b.type == "tool_use" for b in blocs)
    if appels:
        arret = "tool_use"
    elif msg.get("refusal") and not msg.get("content"):
        arret = "refusal"
    elif choix.get("finish_reason") == "length":
        arret = "max_tokens"
    else:
        arret = "end_turn"
    u = d.get("usage") or {}
    cache = int(((u.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0)
    return SimpleNamespace(content=blocs, stop_reason=arret,
                           usage=SimpleNamespace(input_tokens=max(0, int(u.get("prompt_tokens") or 0) - cache), output_tokens=int(u.get("completion_tokens") or 0),
                                                 cache_read_input_tokens=cache))


def _appeler_openai(*, modele: str, system: str, messages: list, tools: list | None, max_tokens: int):
    import httpx

    if modele.startswith("claude-"):
        raise RuntimeError("fournisseur « openai » sans nom de modèle : renseignez MODELE_RAISONNEMENT, MODELE_EQUILIBRE et MODELE_RAPIDE (ou MODELE_<AGENT>)")
    adresse, cle = adresse_openai(), os.environ.get("OPENAI_API_KEY", "").strip()
    if adresse == OPENAI_URL and not cle:
        raise RuntimeError("OPENAI_API_KEY absente")
    corps: dict = {"model": modele, "messages": vers_openai(system, messages)}
    # OpenAI attend « max_completion_tokens » sur ses modèles récents ; les serveurs compatibles (Ollama…) attendent « max_tokens ».
    corps["max_completion_tokens" if adresse == OPENAI_URL else "max_tokens"] = max_tokens
    if tools:
        corps["tools"] = outils_openai(tools)
    try:
        delai = float(os.environ.get("MODELE_DELAI_S", "180"))
    except ValueError:
        delai = 180.0
    r = httpx.post(adresse + "/chat/completions", headers={"Authorization": f"Bearer {cle}"} if cle else {}, json=corps, timeout=delai)
    if r.status_code != 200:
        detail = r.text[:200].replace(cle, "***") if cle else r.text[:200]
        raise RuntimeError(f"le fournisseur de modèle a répondu {r.status_code} : {detail}")
    return depuis_openai(r.json())


def appeler(*, modele: str, system: str, messages: list, tools: list | None, max_tokens: int = 16000):
    """Un appel au modèle du fournisseur choisi (MODELE_FOURNISSEUR). Pas de `thinking` explicite : l'effort reste au défaut."""
    try:
        max_tokens = int(os.environ.get("MODELE_MAX_TOKENS", "") or max_tokens)
    except ValueError:
        pass
    if fournisseur() == "openai":
        return _appeler_openai(modele=modele, system=system, messages=messages, tools=tools, max_tokens=max_tokens)
    params: dict = {"model": modele, "max_tokens": max_tokens, "system": system, "messages": messages}
    if tools:
        params["tools"] = tools
    return client().messages.create(**params)

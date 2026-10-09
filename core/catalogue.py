"""Catalogue : ce que l'édition gratuite ne contient pas, nommé honnêtement, et les postes libres dessinés dans l'aquarium.
Aucun paiement ne se fait ici : l'achat se passe chez l'éditeur, qui remet un module signé ; le module s'installe dans le
bureau par son manifeste. Les prix ne sont pas écrits dans le code : ils vivent chez l'éditeur."""
from __future__ import annotations

import os
from urllib.parse import urlencode

EDITEUR_URL = "https://zelij.ai/"

PACKS: list[dict] = [
    {"id": "prospection", "nom": "Prospection", "type": "agent", "poste": True,
     "resume": "Un agent qui trouve des entreprises qui correspondent à votre cible, lit leur site, et prépare chaque premier message pour votre validation.",
     "fait": ["recherche de structures par cible et territoire", "lecture des sites pour relever l'adresse publiée", "message préparé, jamais envoyé sans vous", "suivi des réponses dans vos contacts"]},
    {"id": "seo-geo", "nom": "SEO et GEO", "type": "agent", "poste": True,
     "resume": "Un agent qui relit votre site comme un moteur de recherche et un moteur de réponse, et propose les pages qui manquent.",
     "fait": ["relecture des pages existantes", "questions des lecteurs non couvertes", "plan de pages proposé avec sources", "suivi mensuel des positions déclarées"]},
    {"id": "veille-prix", "nom": "Veille des prix", "type": "agent", "poste": True,
     "resume": "Un agent qui relève chaque jour les prix publics de vos concurrents ou fournisseurs, à la source, datés, et signale ce qui change.",
     "fait": ["relevé quotidien sur les pages officielles", "chaque chiffre daté et sourcé", "alerte sur un changement", "historique conservé"]},
    {"id": "surveillance", "nom": "Surveillance", "type": "agent", "poste": True,
     "resume": "Un veilleur qui regarde votre site et votre serveur en continu : certificat, DNS, réponse, dépendances vulnérables, et vous prévient.",
     "fait": ["sonde continue du domaine", "veille des vulnérabilités connues", "rapport quotidien", "première réponse à incident"]},
    {"id": "usine-logicielle", "nom": "Usine logicielle", "type": "pack", "poste": False,
     "resume": "Le Bâtisseur accompagné : un Tech Lead qui relit avec un badge de risque, une QA qui teste, un Product Owner qui découpe. Plusieurs dépôts, une application avec backend.",
     "fait": ["revue de chaque demande de fusion", "tests écrits et exécutés", "découpage en lots", "application avec backend et base"]},
    {"id": "infra-cloud", "nom": "Infra cloud", "type": "cible", "poste": False,
     "resume": "Déploiement sur un grand cloud (GCP d'abord) : base gérée, secrets gérés, recette et production séparées, sauvegarde hors machine.",
     "fait": ["projet et compte de service restreints", "base et secrets gérés", "environnements de recette et de production", "sauvegarde chiffrée hors machine"]},
    {"id": "zelij-cloud", "nom": "Zelij Cloud", "type": "pack", "poste": False,
     "resume": "Le même bureau, hébergé, sauvegardé et mis à jour par l'éditeur. Rien à installer, les modules compris.",
     "fait": ["hébergement et sauvegardes", "mises à jour du noyau", "modules inclus", "replay de la semaine et du mois dans l'aquarium"]},
]

POSTES_LIBRES = [p for p in PACKS if p["poste"]]


def lien_achat(pack_id: str, instance: str) -> str:
    """La page d'achat vit chez l'éditeur ; l'instance s'identifie pour que le module signé lui revienne."""
    base = os.environ.get("ZELIJ_CATALOGUE_URL", EDITEUR_URL + "core/catalogue/").rstrip("/") + "/"
    return base + "?" + urlencode({"pack": pack_id, "instance": instance})


def par_id(pack_id: str) -> dict | None:
    return next((p for p in PACKS if p["id"] == pack_id), None)

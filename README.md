# Zelij Core

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![licence](https://img.shields.io/badge/licence-AGPL--3.0-1c1917)](LICENSE)

**Montez votre startup 100 % native IA.** Un bureau où des agents travaillent pour vous : ils proposent, vous décidez.

> Dépôt privé de préparation (décision du 08/10/2026). Rien n'est publié tant que le contrôle de publication ne passe pas et que la publication n'est pas décidée. Licence : GNU AGPL v3.

## Ce que fait le noyau (lot 1)

- **Le bureau** : une page. Les décisions qui attendent, une demande au Chef de cabinet, les dernières exécutions avec leur coût, le journal, les agents, les modules installés.
- **Le paquet de décision** : objectif, proposition, pourquoi maintenant, options, recommandation, risques, réversibilité, plan, retour arrière, impact. Un paquet incomplet ne s'ouvre pas. Approuver, refuser, ou demander des changements avec une consigne obligatoire transmise à l'agent.
- **Les règles de la maison** : rien de ce qui engage (argent, exposition publique, suppression, irréversible) ne se fait sans décision ; un fait est daté et sourcé ou marqué « non vérifié » ; le journal ne s'efface pas.
- **La passerelle** : la clé Claude du fondateur, le coût de chaque appel calculé depuis l'usage et les tarifs publics datés, un plafond mensuel qui bloque.
- **L'exécuteur** : une boucle d'appel bornée (budget de tours par agent), des outils sobres (`lire_page`, `date_du_jour`), un refus du modèle traité comme un résultat.
- **Les modules** : la seule façon d'étendre le noyau. Interface stable, manifeste `pack.json` signé Ed25519 par l'éditeur, vérification avant installation. Les cibles de déploiement et les agents supplémentaires passent par là.
- **Finances** : ventes confirmées (import Stripe en lecture ou saisie avec preuve), charges déclarées qui reviennent chaque mois, coût des agents mesuré, journal du mois, export CSV pour l'expert-comptable. Rien n'est déclaré ni facturé.
- **Contacts** : une fiche par personne, base légale obligatoire, durée de conservation, échanges, droits exercés ; un contact opposé ne reçoit plus rien, un contact échu est oublié et seul le journal des droits reste.
- **Publication** : une page rédigée par Croissance devient un brouillon, puis une décision ; approuvée, elle est proposée au site comme demande de fusion GitHub ou brouillon WordPress. Le dernier geste, fusionner ou publier, est le vôtre.
- **Aquarium** : regardez vos agents travailler, chaque bulle est une action réelle des dernières 24 heures ; les silhouettes en pointillé sont des postes libres. Une page publique partageable, badge « by zelij.ai ».
- **Catalogue** : ce que l'édition gratuite ne contient pas, nommé honnêtement ; un module acheté chez l'éditeur s'installe ici, signé et vérifié. Aucun paiement ne passe par le bureau.
- **Software factory** : le Bâtisseur lit et propose sur un seul dépôt par demandes de fusion passées par la porte de sécurité (300 lignes, texte seulement, aucun secret, aucun fichier d'infrastructure, dépendances sans vulnérabilité connue via OSV) ; mise en ligne sur un serveur Linux en SSH ou chez OVH (domaine et DNS par l'API) avec bascule atomique, test de fumée et retour arrière ; sonde du domaine ; sauvegarde quotidienne du bureau. Il ne fusionne jamais, ne paie jamais, ne touche jamais au bureau.
- **Les agents** : un dossier par agent, un `agent.md` avec un en-tête simple et des consignes en français. Quatre agents : Camille Aubert (chef-de-cabinet), Élise Tanguy (croissance), Nour Bellamy (finances-clients), Sacha Ferrand (batisseur). Le fondateur s'adresse à chacun depuis le bureau ; un paquet approuvé qui désigne un agent et une tâche s'exécute aussitôt, dans les limites du plan. Les registres de compta et de contacts (lot 3) et les outils du Bâtisseur (lot 5) ne sont pas encore branchés : les fiches le disent et les agents ne prétendent pas faire ce qu'ils ne peuvent pas faire.

Guide : `docs/premiere-semaine.md`. English summary: `README.en.md`.

## Démarrer

```bash
cp .env.example .env     # clé Claude, plafond, SECRET_KEY, mot de passe de base
docker compose up -d --build
```

Le bureau répond sur `http://localhost:8000`. Sans SMTP, le lien de connexion est écrit dans les journaux du conteneur (`docker compose logs core-app`).

Guides complets : **[Installation](docs/INSTALLATION.md)** (machine vide → bureau en https, SMTP, Software factory, sauvegardes, dépannage), **[Mode d'emploi](docs/MODE-D-EMPLOI.md)** (chaque page, les agents, les décisions, le coût), [Première semaine](docs/premiere-semaine.md). Vos photos (fondateur, agents) se déposent dans [`portraits/`](portraits/README.md).

Depuis l'image publiée, sans construction locale (`CORE_IMAGE_TAG=v…` dans `.env` pour fixer la version) :

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

En local sans Docker :

```bash
pip install -r requirements.txt
uvicorn core.bureau.app:app --reload
```

## Clé publique de l'éditeur

Les modules du catalogue sont signés par zelij.ai. La clé publique à poser dans `ZELIJ_CLE_PUBLIQUE` (déjà renseignée dans `.env.example`) :

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Sécurité

Ce que le noyau garantit, et qui est testé (`tests/test_securite.py`) :

- **Modules** : un module ne s'installe et ne s'exécute que signé par l'éditeur (Ed25519), et la signature couvre l'empreinte SHA-256 de chaque fichier de code : un fichier modifié, ajouté ou retiré après la signature met le module hors jeu.
- **Connexion** : liens à usage unique de 20 minutes, hachés en base ; freins par adresse, par IP et global sur les demandes de lien, pour que le bureau ne serve jamais de relais de courriels ; sans SMTP configuré en production, aucun lien n'est créé ni journalisé.
- **Formulaires** : cookie de session HMAC `HttpOnly` `SameSite=Strict`, contrôle d'origine et jeton anti-CSRF par session sur chaque POST.
- **Pages** : politique de sécurité du contenu stricte (`default-src 'self'`, aucun script en ligne, aucun cadre), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS quand l'origine est en https.
- **Agents** : ce qu'un agent lit (page web, fichier du dépôt) lui arrive encadré comme contenu externe, jamais comme consigne ; il ne lit que des adresses https publiques (adresses privées, de boucle locale, de lien local et noms internes refusés à chaque saut de redirection, réponse plafonnée) ; la porte de sécurité bloque secrets, fichiers d'infrastructure, scripts, cadres et appels réseau vers des domaines tiers.
- **Conteneur** : utilisateur sans privilège, système de fichiers en lecture seule, aucune capacité, pas d'élévation ; la clé du serveur SSH peut être imposée (`SSH_CLE_HOTE`).
- **Export comptable** : les cellules qui ressemblent à une formule de tableur sont neutralisées.

Signaler une faille : `securite@zelij.ai`, sans la publier avant correction. Avant chaque publication, `pip-audit -r requirements.txt` et `bandit -r core scripts -ll` doivent être vides.

## Contribuer et suivre les versions

`CONTRIBUTING.md` dit comment une contribution arrive dans une version (et la règle : une cible de déploiement contribuée vaut le pack correspondant gratuit à vie). `SECURITY.md` dit comment signaler une faille. `CHANGELOG.md` dit ce que chaque version change et ce qu'il reste à faire au fondateur.

## Tests et contrôle de publication

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Le contrôle de publication refuse clés, adresses IP, codes d'agents de l'éditeur, adresses personnelles, mots de passe en clair, et les termes d'une liste privée (`ZELIJ_CORE_INTERDITS`) qui ne fait jamais partie du dépôt.

## Feuille de route

Lot 1 noyau (fait) · lot 2 les quatre agents (fait) · lot 3 compta et CRM light (fait) · lot 4 publication, aquarium, catalogue (fait) · lot 5 Software factory, cibles OVH / serveur SSH, porte de sécurité (fait) · lot 6 cible GCP, module payant signé (fait, hors dépôt public).

by zelij.ai — https://zelij.ai/

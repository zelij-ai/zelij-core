# Installer Zelij Core

Ce guide va de la machine vide au bureau en ligne, en https, avec vos agents, votre clé Claude et vos sauvegardes. Comptez une heure la première fois. Chaque étape dit ce qu'elle fait et comment vérifier qu'elle a marché.

Zelij Core tient dans deux conteneurs : le bureau (FastAPI, qui héberge aussi les agents) et une base PostgreSQL. Rien d'autre ne tourne : pas de file d'attente, pas de cache, pas de service tiers. Les agents parlent à Claude avec **votre** clé et n'écrivent rien ailleurs que dans votre base.

## 1. Ce qu'il vous faut

| Besoin | Pourquoi | Où l'obtenir |
|---|---|---|
| Une machine Linux avec Docker et Docker Compose (v2.24 ou plus) | Elle héberge le bureau | Un VPS à 2 Go de mémoire suffit ; en local, Docker Desktop convient |
| Une clé d'API Claude | Chaque appel d'agent est payé sur cette clé, le coût s'affiche dans le bureau | https://console.anthropic.com/ (créez la clé, posez un plafond de dépense côté console aussi) |
| Un nom de domaine pointant vers la machine (facultatif en local, obligatoire en production) | Le bureau en https, les liens de connexion qui marchent | Votre registraire : un enregistrement `A` vers l'adresse de la machine |
| Un compte SMTP (facultatif en local, obligatoire en production) | Les liens de connexion partent par e-mail ; sans SMTP, le bureau refuse de les envoyer en production | Votre hébergeur de mail, ou un service d'envoi avec identifiant et mot de passe |

Pas de compte à créer chez zelij.ai : l'édition gratuite ne téléphone à personne.

## 2. Récupérer le code

```bash
git clone https://github.com/zelij-ai/zelij-core.git
cd zelij-core
```

Ou téléchargez l'archive de la dernière version depuis la page des versions et dépliez-la.

## 3. Écrire la configuration

```bash
cp .env.example .env
```

Ouvrez `.env` et renseignez, dans cet ordre :

1. `ANTHROPIC_API_KEY` : votre clé Claude.
2. `PLAFOND_MENSUEL_EUR` : au-delà de ce montant dans le mois, aucun agent n'est plus appelé tant que vous ne relevez pas le plafond. Commencez à 20 ou 50.
3. `CORE_DB_PASSWORD` : un mot de passe pour la base, généré une fois et jamais retapé ailleurs :
   ```bash
   openssl rand -hex 24
   ```
4. `SECRET_KEY` : la clé qui signe vos sessions, 48 caractères aléatoires au moins, générée de la même façon. Sans elle, le conteneur refuse de démarrer.
5. `APP_ORIGIN` : l'adresse publique du bureau, par exemple `https://bureau.votre-domaine.fr`. En local, laissez `http://localhost:8000`. Elle sert aux liens de connexion et au contrôle d'origine des formulaires : si elle est fausse, les liens reçus par e-mail ne mènent nulle part.
6. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` : l'envoi des liens de connexion. L'adresse d'expédition doit appartenir au domaine que votre SMTP a le droit d'utiliser.
7. `ZELIJ_CLE_PUBLIQUE` : déjà renseignée. C'est la clé publique de l'éditeur des modules ; ne la changez que si vous installez des modules signés par quelqu'un d'autre.

Le reste (`SITE_*`, `SSH_*`, `OVH_*`, `GITHUB_TOKEN`) concerne la Software factory et se remplit plus tard, au chapitre 8.

Ne commitez jamais `.env` : il est dans `.gitignore`.

## 4. Démarrer en local (http)

```bash
docker compose up -d --build
docker compose logs -f core-app
```

Quand les journaux affichent `Uvicorn running on http://0.0.0.0:8000`, ouvrez http://localhost:8000. Vérification : http://localhost:8000/healthz répond `{"ok": true, "service": "zelij-core", "version": "…"}`.

Le port 8000 n'est joignable que depuis la machine elle-même (`127.0.0.1`) : en http, ni le lien de connexion ni la session ne doivent circuler sur un réseau. Pour ouvrir le bureau à d'autres, passez par le chapitre 5 (https). Si vous savez ce que vous faites (réseau privé de confiance), `CORE_ECOUTE=0.0.0.0` dans `.env` publie le port sur toutes les interfaces.

Sans SMTP, le lien de connexion est écrit dans les journaux du conteneur (jamais en production) : demandez un lien sur la page de connexion, puis copiez l'adresse `http://localhost:8000/connexion/…` depuis `docker compose logs core-app`.

### Sans construire l'image

Chaque version publie une image prête sur le registre GitHub. Pour l'utiliser au lieu de construire :

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Fixez la version dans `.env` avec `CORE_IMAGE_TAG=v0.7.2` : sans cela, `latest` suit la dernière version publiée à chaque redémarrage. Le fichier `docker-compose.image.yml` s'ajoute aussi à la commande du chapitre 5 pour l'https.

## 5. Mettre en ligne en https

Le fichier `docker-compose.tls.yml` ajoute un serveur Caddy devant le bureau : certificat automatique, renouvellement automatique, redirection de http vers https. Trois conditions : le domaine pointe vers la machine, les ports 80 et 443 sont ouverts, `CORE_DOMAINE` est renseigné dans `.env`.

```bash
# dans .env
CORE_DOMAINE=bureau.votre-domaine.fr
APP_ORIGIN=https://bureau.votre-domaine.fr
```

```bash
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

Vérification : https://bureau.votre-domaine.fr/healthz répond, le cadenas est présent, et http://bureau.votre-domaine.fr redirige vers https. Le port 8000 n'est plus publié sur la machine : seul Caddy parle au bureau.

Si vous avez déjà un serveur TLS (Nginx, Traefik, un autre Caddy), gardez le `docker-compose.yml` seul et faites pointer votre serveur vers `127.0.0.1:8000` avec les en-têtes `X-Forwarded-For` et `X-Forwarded-Proto`, et ajoutez `FORWARDED_ALLOW_IPS=*` dans `.env` : le bureau ne croit ces en-têtes que si vous le lui dites, et le port n'étant joignable que depuis la machine, seul votre serveur peut les poser.

## 6. Première connexion

1. Ouvrez le bureau, saisissez votre adresse e-mail, demandez le lien.
2. Ouvrez le lien reçu (il vaut vingt minutes, une seule fois) puis cliquez sur « Entrer dans le bureau » : ouvrir le lien ne suffit pas, pour qu'un antivirus de messagerie qui le visite ne le consomme pas à votre place. **La première adresse qui se connecte crée l'organisation et devient le fondateur ; ensuite, plus aucune adresse inconnue ne reçoit de lien.** Une installation porte une seule organisation : vos clés (modèle, paiement, dépôt, serveur) ne servent qu'à elle. Si le bureau est joignable avant votre première connexion, posez `FONDATEUR_EMAIL=vous@votre-domaine.fr` dans `.env` : seule cette adresse pourra créer l'organisation.
3. Vous arrivez sur le Bureau : le Chef de cabinet vous attend. Faites une demande simple pour vérifier que la clé Claude fonctionne : « Présente-moi l'équipe ». Le coût de l'appel s'affiche aussitôt dans le compteur du mois.

Pour inviter quelqu'un : la page Contacts ne sert pas à cela ; une invitation est un lien de connexion qui porte l'identifiant de votre organisation. Cette fonction arrive avec l'édition complète ; dans l'édition gratuite, le bureau est celui du fondateur.

## 7. Personnaliser : agents, portraits, langue

- **Les agents** vivent dans `agents/<identifiant>/agent.md` : un en-tête (`id`, `nom`, `fonction`, `classe_modele`, `outils`, `budget_tours`, `couloir`) et, en dessous, les consignes en français. Modifiez les consignes, le nom, la fonction ; ajoutez un agent en copiant un dossier. Le bureau relit les fiches à chaque page.
- **Le modèle** de chaque agent vient de sa classe (`raisonnement`, `equilibre`, `rapide`). Pour forcer un modèle précis : `MODELE_CHEF_DE_CABINET=claude-sonnet-5-5` dans `.env`.
- **Les portraits** : déposez une image carrée (256 px, `webp`, `png` ou `jpg`) dans `portraits/<identifiant>.webp` pour un agent, `portraits/fondateur.webp` pour vous. Sans photo, le bureau dessine un monogramme pour les agents et une silhouette pour le fondateur. Le dossier `portraits/README.md` détaille les formats. Avec Docker, montez le dossier : il est déjà déclaré dans `docker-compose.yml` (`./portraits:/srv/app/portraits:ro`).
- **La langue** : le bureau est en français ; les agents répondent en français par consigne. Pour une autre langue, modifiez les consignes des fiches et la règle 3 des règles de la maison dans `core/executeur.py`.

## 8. La Software factory (facultatif)

Le Bâtisseur lit et propose des modifications sur **un** dépôt GitHub (le site de l'entreprise), par demandes de fusion que vous relisez. Il met en ligne sur un serveur Linux (SSH) ou chez OVH, après votre approbation.

1. Créez un dépôt pour le site (un site statique : un `index.html` à la racine suffit pour commencer).
2. Créez un jeton GitHub à portée réduite, **limité à ce dépôt**, avec les droits `contents` et `pull requests` en écriture.
3. Dans `.env` : `SITE_DEPOT=votre-compte/votre-site`, `GITHUB_TOKEN=…`, `SITE_DOMAINE=https://www.votre-site.fr`.
4. Cible SSH : `SSH_HOTE`, `SSH_UTILISATEUR`, `SSH_PORT`, `SITE_DOSSIER` (le dossier des versions sur le serveur, par exemple `/var/www/site`) et `SSH_CLE`, chemin d'une clé privée **montée en lecture seule** dans le conteneur (déclarez le volume dans `docker-compose.yml`, par exemple `./secrets/deploiement:/run/secrets/ssh_cle:ro`, et `SSH_CLE=/run/secrets/ssh_cle`). Recommandé : `SSH_CLE_HOTE` avec la clé publique du serveur (`ssh-keyscan -t ed25519 votre-serveur`), pour refuser toute autre machine.
5. Cible OVH : `CIBLE=ovh` et les trois clés de l'API OVH (créées sur https://eu.api.ovh.com/createToken/ avec `GET`, `POST`, `PUT` sur `/domain/zone/*`).
6. Redémarrez (`docker compose up -d`), ouvrez la page Factory : « Sonder le domaine » doit rendre un relevé, « Proposer une mise en ligne » ouvre une décision.

Le Bâtisseur ne fusionne jamais, ne paie jamais, ne touche jamais au bureau. Sa porte de sécurité refuse les secrets, les fichiers d'infrastructure, les scripts et cadres tiers, les dépendances connues vulnérables.

## 9. Sauvegardes et restauration

Chaque nuit, le bureau écrit un export compressé de la base dans le volume `core-sauvegardes` (les quatorze derniers sont gardés, sauvegardes manuelles comprises ; ils ne sont pas chiffrés, protégez le volume comme la base). Pour les sortir de la machine :

```bash
docker compose cp core-app:/data/sauvegardes ./sauvegardes-$(date +%F)
```

Restaurer, depuis une sauvegarde `bureau-AAAAMMJJ-HHMMSS.sql.gz` :

```bash
docker compose stop core-app
gunzip -c bureau-AAAAMMJJ-HHMMSS.sql.gz | docker compose exec -T core-db psql -U core -d core
docker compose start core-app
```

Une sauvegarde manuelle se lance depuis la page Factory (« Sauvegarder le bureau »).

## 10. Mettre à jour

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

Le schéma de la base se met à jour tout seul au démarrage. Lisez le journal des versions avant de mettre à jour une version majeure : il dit si une variable change.

## 11. Installer un module

Le Catalogue du bureau renvoie vers zelij.ai pour les modules payants (déploiement cloud, agents supplémentaires). Un module arrive sous forme de colis : un dossier avec son code et un manifeste `pack.json` signé par l'éditeur.

1. Dépliez le colis dans le dossier des modules (`ZELIJ_MODULES_DIR`, par défaut le volume `core-modules` ; avec Docker : `docker compose cp ./cible_gcp core-app:/srv/app/modules/`).
2. Dans le bureau : Catalogue, « Installer un module signé », déposez le `pack.json`.
3. Suivez le README du module pour ses variables, redémarrez.

Le bureau refuse tout module non signé, signé pour une autre interface, ou dont un fichier diffère de ce que l'éditeur a signé.

## 12. Dépannage

| Symptôme | Cause probable | Remède |
|---|---|---|
| Le conteneur s'arrête avec `SECRET_KEY absente en production` | `.env` incomplet | Renseignez `SECRET_KEY` (48 caractères aléatoires) |
| Le lien reçu par e-mail renvoie sur « Ce lien n'est plus valable » | `APP_ORIGIN` faux, lien déjà utilisé ou vieux de plus de vingt minutes | Corrigez `APP_ORIGIN`, redemandez un lien |
| « L'envoi d'e-mails n'est pas configuré » | `SMTP_HOST` vide en production | Renseignez le SMTP ; en local, lisez le lien dans les journaux |
| « Trop de demandes » | Freins de connexion : 5 par adresse et 10 par adresse IP sur quinze minutes | Attendez un quart d'heure |
| « Plafond mensuel atteint » | `PLAFOND_MENSUEL_EUR` dépassé | Relevez le plafond dans `.env`, redémarrez |
| Le certificat n'arrive pas | Domaine ne pointant pas encore vers la machine, ou port 80 fermé | `dig +short bureau.votre-domaine.fr`, ouvrez 80 et 443, `docker compose logs caddy` |
| Un module est « ignoré » dans le compte rendu | Signature absente, interface incompatible ou fichier modifié | Reprenez le colis d'origine, ne modifiez pas son contenu |
| `origine refusée` sur un formulaire | Le bureau est appelé depuis une autre adresse que `APP_ORIGIN` | Utilisez l'adresse déclarée, ou corrigez-la |

Journaux : `docker compose logs -f core-app`. État : `/healthz`. Les journaux ne contiennent jamais un lien de connexion en production.

## 13. Désinstaller

```bash
docker compose -f docker-compose.yml -f docker-compose.tls.yml down
docker volume rm zelij-core_core-db zelij-core_core-sauvegardes zelij-core_core-modules zelij-core_caddy-data
```

La seconde commande efface la base, les sauvegardes et les modules : sortez d'abord une sauvegarde (chapitre 9).

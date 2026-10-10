# Journal des versions

Chaque version dit ce qui change pour le fondateur et ce qu'il doit faire, s'il y a quelque chose à faire. Les correctifs de sécurité sont marqués **sécurité**.

## 0.7.4 — 2026-10-10

Version de **sécurité**, issue d'une relecture complète du code. Mettez à jour si votre bureau est joignable depuis Internet.

- **sécurité, important** — Une installation porte désormais une seule organisation. Jusqu'à la 0.7.3, toute adresse e-mail pouvait demander un lien, créer sa propre organisation et utiliser les clés de l'installation (modèle, paiement, dépôt, serveur). Dès qu'un fondateur existe, une adresse inconnue ne reçoit plus rien. `FONDATEUR_EMAIL` (facultatif) réserve la création à une adresse.
- **sécurité** — La mise en ligne n'est possible que dans l'exécution d'une décision de mise en ligne approuvée ; aucune autre décision ne l'ouvre.
- **sécurité** — La page publique de l'aquarium ne montre plus l'objet des décisions.
- **sécurité** — Oublier un contact efface aussi son adresse et ses échanges du journal et du registre des droits ; le journal ne reçoit plus ni adresse ni résumé.
- **sécurité** — Le certificat du serveur de messagerie est vérifié (STARTTLS sur 587, TLS direct sur 465).
- **sécurité** — Se déconnecter révoque la session côté serveur : un cookie copié cesse de valoir.
- **sécurité** — Le port 8000 n'est publié que sur la machine (`127.0.0.1`) ; les en-têtes `X-Forwarded-*` ne sont crus que du serveur Caddy fourni.
- **sécurité** — Lecture de pages : nettoyage en temps proportionnel à la taille (une page piégée ne bloque plus un processeur). Sources des pages rédigées : `https` seulement.
- **sécurité** — Porte de sécurité du Bâtisseur : adresses sans protocole (`//…`), `compose.yaml` et variantes, scripts d'installation npm, tous les préfixes de jetons GitHub ; jsDelivr limité aux paquets npm.
- Le plafond mensuel se tient aussi pendant une exécution. Une décision ne se prend qu'une fois, même sur deux clics simultanés. Les montants infinis sont refusés. La jauge du budget s'affiche. Tarifs des modèles relevés le 10/10/2026.
- Image : dépendances épinglées, outils de test hors de l'image (`requirements-dev.txt`), `.dockerignore`. Sauvegarde : mot de passe de la base hors de la ligne de commande, copie SQLite cohérente.
- **À faire après mise à jour** : si vous accédiez au bureau par `http://<adresse-du-serveur>:8000`, passez à l'https (chapitre 5 du guide d'installation) ou posez `CORE_ECOUTE=0.0.0.0` en connaissance de cause. Derrière votre propre serveur TLS, ajoutez `FORWARDED_ALLOW_IPS=*`. Vérifiez sur la page Bureau que le journal ne montre aucune connexion que vous ne reconnaissez pas.

## 0.7.3 — 2026-10-09

- Le Chef de cabinet connaît le catalogue : une demande qui dépasse le bureau ouvre un paquet « construire soi-même ou installer le module », avec le temps du Bâtisseur en face du module de l'éditeur. Approuver l'option module conduit au catalogue, lien d'achat prêt ; rien ne s'achète dans le bureau.
- `SECURITY.md` : réponse à chaque signalement dans l'ordre d'arrivée, sans délai annoncé. README anglais complet.
- Rien à faire après mise à jour.

## 0.7.2 — 2026-10-09

- Dépôt public ouvert aux contributions : `CONTRIBUTING.md` (dont la règle « cible contribuée, pack gratuit à vie »), `SECURITY.md`, règles de bonne conduite, gabarits d'issues et de demandes de fusion.
- Intégration continue : tests, lint, audit des dépendances, scan du code, contrôle de publication et démarrage à blanc de l'image sur chaque demande de fusion.
- Versions : une étiquette `vX.Y.Z` publie l'image `ghcr.io/zelij-ai/zelij-core` et une version GitHub avec l'archive. `docker-compose.image.yml` démarre le bureau depuis l'image, sans construction locale.
- Rien à faire après mise à jour.

## 0.7.1 — 2026-10-09

- Guides complets, en français et en anglais : installation (de la machine vide au bureau en https) et mode d'emploi.
- Mise en https en une commande : `docker-compose.tls.yml` et `infra/Caddyfile` (certificat automatique pour `CORE_DOMAINE`).
- Portraits : dossier `portraits/` (photo du fondateur et des agents, silhouettes de remplacement), affichés dans l'en-tête, l'aquarium et la vitrine.
- À faire si vous passez en https : renseigner `CORE_DOMAINE` et `APP_ORIGIN` dans `.env`.

## 0.7.0 — 2026-10-09 — sécurité

- **Modules** : la signature couvre désormais l'empreinte de chaque fichier ; un module dont un fichier a été modifié, ajouté ou retiré est refusé.
- **Connexion** : freins par adresse, par IP et global sur les demandes de lien ; sans SMTP en production, aucun lien n'est créé ni journalisé.
- **Agents** : les adresses privées, de boucle locale, de lien local et les noms internes sont refusés à la lecture, à chaque saut de redirection ; le contenu lu est encadré comme donnée, jamais comme consigne.
- **Bureau** : en-têtes de sécurité et politique de contenu stricte, jeton anti-CSRF sur chaque formulaire, export CSV neutralisé, clé de session aléatoire hors production.
- **Conteneur** : utilisateur sans privilège, système de fichiers en lecture seule.
- **Dépendances** mises à jour (starlette, python-multipart, pytest).
- À faire : `docker compose up -d --build` ; si vous avez un module installé, réinstallez-le depuis son colis d'origine.

## 0.6.0 — 2026-10-08

- Première édition complète : bureau, quatre agents, gouvernance par paquet de décision, finances et contacts légers, publication par demande de fusion ou brouillon, aquarium et vitrine, catalogue de modules signés, Software factory (serveur SSH, OVH), sauvegardes.

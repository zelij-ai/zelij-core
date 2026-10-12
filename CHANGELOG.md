# Journal des versions

Chaque version dit ce qui change pour le fondateur et ce qu'il doit faire, s'il y a quelque chose à faire. Les correctifs de sécurité sont marqués **sécurité**.

## 0.9.0 — 2026-10-12

- **Dans la poche : décider depuis le téléphone.** Quand un agent ouvre une décision, le fondateur la reçoit par e-mail avec le
  paquet en clair et deux liens signés, « Approuver » et « Refuser » ; chaque lien ouvre une page de confirmation (un logiciel de
  messagerie qui suit les liens ne décide rien), ne sert qu'une fois et vaut sept jours. Avec un robot Telegram (`TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_CHAT_ID`), la décision arrive avec trois boutons ; « Demander une modification » attend votre consigne en réponse.
- La décision passe par la même porte que depuis le bureau, elle est journalisée avec son canal (« lien e-mail », « Telegram »), et ce
  qu'une approbation déclenche (agent, publication) est le même. Un bouton pressé depuis une autre conversation que la vôtre est refusé.
- Rien ne sort en mode démonstration.
- À faire après mise à jour : rien pour l'e-mail si `SMTP_HOST` est renseigné (`DECISIONS_PAR_EMAIL=0` le coupe) ; pour Telegram,
  créer un robot auprès de @BotFather, lui écrire une fois, et poser les deux variables (guide dans `docs/MODE-D-EMPLOI.md`).

## 0.8.1 — 2026-10-11

- **Autres fournisseurs de modèles.** Claude reste le choix par défaut. `MODELE_FOURNISSEUR=openai` branche toute interface compatible avec celle d'OpenAI : OpenAI, un modèle local (Ollama, LM Studio), Mistral, OpenRouter. On nomme les modèles par classe (`MODELE_RAISONNEMENT`, `MODELE_EQUILIBRE`, `MODELE_RAPIDE`) et on déclare leurs tarifs (`MODELE_TARIFS`) ; un modèle local se déclare à zéro.
- Les garde-fous du bureau ne dépendent pas du modèle : outils de la fiche, plus de sortie après une lecture privée, mise en ligne par sa seule décision, plafond mensuel. La qualité du travail des agents, elle, en dépend : le bureau est mis au point et éprouvé avec Claude.
- Un modèle sans tarif connu ni déclaré est compté au tarif le plus cher, et le bureau le signale : jamais de coût nul par oubli.
- Rien à faire après mise à jour : sans `MODELE_FOURNISSEUR`, rien ne change.

## 0.8.0 — 2026-10-11

- **Mode démonstration.** `docker compose -f docker-compose.demo.yml up --build` ouvre un bureau déjà rempli : une entreprise fictive, une journée de travail des agents dans l'aquarium, des décisions à prendre, des finances et des contacts. Aucune clé, aucun e-mail, aucun coût : les agents sont simulés d'après un scénario, rien ne part vers un modèle. Un bandeau le dit sur chaque page.
- Ce mode refuse de démarrer en production, sur PostgreSQL, ou sur une base qui porte une organisation réelle.
- Rien à faire après mise à jour : sans `CORE_DEMO=1`, rien ne change.

## 0.7.6 — 2026-10-10

- **sécurité** — Chaque décision préparée par un agent affiche sa provenance : pages lues, fichiers du dépôt lus, actions refusées par le bureau. Une décision dont la tâche est confiée à un autre agent après lecture de contenu externe, ou préparée avec un refus en route, est signalée « à relire avec attention » et demande une confirmation à l'approbation. L'essai du 10/10 a montré qu'une page de fournisseur pouvait faire ouvrir à un agent une décision dictée par elle : le fondateur le voit désormais avant d'approuver.
- La trace des outils d'une exécution reste lisible même après un très gros appel.
- Rien à faire après mise à jour. Les décisions déjà ouvertes n'ont pas de provenance ; les nouvelles l'affichent.

## 0.7.5 — 2026-10-10

Version de **sécurité** : ce que le bureau refuse à un agent trompé par une page ou un fichier piégé, et contrôle des accès.

- **sécurité, important** — Un agent n'exécute que les outils de sa fiche. Jusqu'à la 0.7.4, un outil demandé hors de la fiche était exécuté.
- **sécurité, important** — Dès qu'une exécution a lu une donnée privée (dépôt, finances, contacts), elle ne peut plus appeler que le site de l'entreprise (`SITE_DOMAINE`) : ni page, ni sonde de domaine ailleurs. Lire le web puis le dépôt reste permis.
- **sécurité** — Le cadre « contenu externe » porte un identifiant tiré au hasard et toute balise contenue dans une page est neutralisée : une page ne peut plus fermer son cadre.
- **sécurité** — La page qui part vers le site est celle de la décision approuvée, et aucune autre : une tâche de publication écrite par un agent est retirée.
- **sécurité** — Porte de sécurité : liens `javascript:`, `eval` et lecture des cookies, redirections, `meta refresh`, images, médias et feuilles de style d'un autre domaine.
- **sécurité** — Ouvrir le lien de connexion ne connecte plus : un bouton confirme l'entrée (un antivirus de messagerie qui visite le lien ne le consomme pas). L'envoi du lien part après la réponse.
- **sécurité** — Décider, installer un module, ouvrir une mise en ligne ou la page publique : réservé au fondateur. Un membre lit et demande.
- **sécurité** — `Cache-Control: no-store` sur tout ce qui n'est pas un fichier public ; requêtes plafonnées à 2 Mo ; l'adresse du fondateur n'est plus transmise au modèle.
- **sécurité** (essai d'intrusion du 10/10) — La porte de sécurité lit désormais les balises avec un analyseur et non des expressions régulières : un fichier fabriqué pour la ralentir (plus de cent secondes auparavant) est traité en une seconde au plus, et les attributs sans guillemets, les entités et les barres inversées sont vus. Balise `base` refusée.
- **sécurité** (essai d'intrusion) — En production, `SECRET_KEY` doit faire 32 caractères au moins : le bureau refuse de démarrer une session avec une clé plus courte. Plus d'en-tête `Server`. Caddy coupe les connexions lentes et plafonne les requêtes à 2 Mo.
- Corrigé : erreur 500 sur un mois hors de ce siècle dans la page Finances, et sur un manifeste de module qui n'est pas un objet JSON.
- **À faire après mise à jour** : vérifiez que `SECRET_KEY` fait 32 caractères au moins (`openssl rand -hex 32`). Si un agent vous répond « refus : cette exécution a lu des données privées », relancez la lecture du web dans une demande séparée.

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

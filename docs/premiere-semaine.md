# Votre première semaine avec Zelij Core

Un bureau, quatre agents, vous qui décidez. Voici ce qui se passe les sept premiers jours, sans rien promettre que le logiciel ne tienne pas.

## Jour 1 : installer et entrer

1. Copiez `.env.example` en `.env`. Remplissez au minimum : votre clé Claude (`ANTHROPIC_API_KEY`), un plafond mensuel (`PLAFOND_MENSUEL_EUR`, 50 € par défaut), une clé de session (`SECRET_KEY`, 48 caractères au hasard), un mot de passe de base (`CORE_DB_PASSWORD`).
2. `docker compose up -d --build`. Le bureau répond sur `http://localhost:8000`.
3. Entrez votre adresse e-mail. Sans SMTP, le lien de connexion s'affiche dans `docker compose logs core-app` ; avec SMTP (`SMTP_*`), il arrive par e-mail.
4. Première demande, à Camille Aubert (chef-de-cabinet) : « Qu'est-ce que vous pouvez faire pour moi cette semaine ? » Elle répond, et le coût de la réponse s'affiche en haut du bureau.

## Jour 2 : les finances

- Déclarez vos charges récurrentes (hébergement, domaine, abonnements) : elles reviendront chaque mois à leur date.
- Si vous encaissez par Stripe, posez une clé **restreinte en lecture** dans `STRIPE_SECRET_KEY` et importez : seuls les paiements confirmés entrent. Sinon, saisissez vos ventes avec leur preuve.
- Demandez à Nour Bellamy (finances-clients) : « Fais-moi le point du mois. » Elle lit le journal et répond avec des totaux datés.

## Jour 3 : les contacts

- Créez vos premières fiches. La base légale est obligatoire : contrat, intérêt légitime ou consentement. Notez d'où vient chaque contact.
- Ajoutez un échange quand vous parlez à quelqu'un. Si une personne s'oppose, exercez le droit sur sa fiche : plus aucun message sortant ne pourra être enregistré pour elle.

## Jour 4 : une page pour le site

- Demandez à Élise Tanguy (croissance) : « Rédige une page qui répond à la question que mes clients me posent le plus. »
- Elle rédige avec des sources lues et datées. La page devient un brouillon et une décision s'ouvre. Si vous approuvez, elle part vers votre site comme proposition : demande de fusion sur votre dépôt (`SITE_DEPOT`, `GITHUB_TOKEN` restreint à ce dépôt) ou brouillon WordPress (`WP_URL`, `WP_USER`, `WP_APP_PASSWORD`). Vous fusionnez ou publiez vous-même.

## Jour 5 : l'aquarium

- Ouvrez l'aquarium : chaque bulle est une action réelle des dernières 24 heures. Les silhouettes en pointillé sont des postes libres.
- Créez la page publique et mettez le lien sur votre site : « Regardez nos agents travailler ». Elle ne montre que les titres et les comptes.

## Jour 6 : le Bâtisseur

- Demandez à Sacha Ferrand (batisseur) de diagnostiquer votre site ou de proposer le contenu exact d'un fichier à changer. Ses outils de dépôt et de déploiement arrivent avec un prochain lot ; il vous dit clairement ce qu'il ne peut pas encore faire.

## Jour 7 : regarder le coût et décider

- Le bureau affiche la dépense du mois face au plafond. Les finances montrent le coût par agent.
- Les décisions récentes et le journal disent qui a fait quoi, quand. Rien ne s'efface.
- Si vous manquez d'un poste (prospection, SEO, veille des prix, surveillance), le catalogue dit ce que ferait l'agent et renvoie vers l'éditeur ; un module acheté s'installe ici, signé.

## Ce que Zelij Core ne fera jamais

Décider à votre place. Payer. Publier sans vous. Inventer un chiffre. Modifier son propre code.

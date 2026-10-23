# Mode d'emploi de Zelij Core

Zelij Core est un bureau : quatre agents d'IA y travaillent, et vous décidez. Ce guide décrit chaque page, ce que font les agents, ce qu'ils ne feront jamais, et comment tenir le coût. Pour l'installation, voir `INSTALLATION.md` ; pour un parcours guidé sur sept jours, `premiere-semaine.md`.

## Le principe

Les agents **proposent**, le fondateur **décide**. Tout ce qui engage de l'argent, expose quelque chose au public, supprime des données ou n'est pas réversible passe par un **paquet de décision** : objectif, proposition, pourquoi maintenant, options, recommandation, risques, réversibilité, plan, retour arrière, impact. Vous approuvez, refusez, ou demandez des changements avec une consigne. Rien ne se fait avant.

Un fait avancé par un agent est daté et sourcé (l'adresse lue), sinon il est marqué « non vérifié ». Les agents signent « Prénom Nom (identifiant), fonction ».

## L'équipe

| Agent | Identifiant | Ce qu'il fait | Outils |
|---|---|---|---|
| Camille Aubert, chef de cabinet | `chef-de-cabinet` | Reçoit vos demandes, prépare les paquets de décision, répartit le travail | lecture de pages, date |
| Élise Tanguy, responsable marketing et produits | `croissance` | Rédige des pages pour le site, propose des angles, relève des faits à la source | lecture de pages, date |
| Nour Bellamy, finances et clients | `finances-clients` | Lit le journal comptable et le suivi des contacts, fait le point, signale ce qui traîne | point finances, contacts à traiter |
| Sacha Ferrand, software factory | `batisseur` | Lit le dépôt du site, propose des modifications par demande de fusion, sonde le domaine, met en ligne après approbation | dépôt, porte de sécurité, sonde, mise en ligne, état de la cible |

Chaque agent a une fiche `agents/<identifiant>/agent.md` : modifiez-la pour changer son nom, sa fonction, ses consignes, son modèle ou son budget de tours. Un agent supplémentaire est un dossier de plus.

## Les pages du bureau

### Bureau
La page d'accueil. En haut, le **compteur du mois** : dépense des agents face au plafond. Au centre, les **décisions en attente**, chacune avec ses trois boutons : Approuver, Refuser, Demander des changements (la consigne est obligatoire : elle part à l'agent demandeur, qui revient avec une révision). En dessous, le formulaire **Demander** au Chef de cabinet (ou à un autre agent), les dernières exécutions avec leur coût, le journal, les agents, les modules installés.

Une demande qui dépasse ce bureau (déploiement cloud, prospection, SEO, veille des prix, surveillance, usine logicielle, hébergement) ouvre un paquet « construire soi-même ou installer le module » : le Chef de cabinet met en face le temps de construction par le Bâtisseur et le module du catalogue ; approuver l'option module vous conduit au catalogue, lien d'achat prêt. Une demande simple reçoit une réponse directe. Une demande qui engage ouvre un paquet. Une demande de page (« rédige une page Tarifs ») produit un brouillon et ouvre une décision de publication : la page ne part vers le site qu'après votre approbation, et seulement sous forme de demande de fusion ou de brouillon, jamais en ligne directement.

En bas à droite, un encart « Une étoile pour Zelij Core » renvoie au dépôt public ; la croix le ferme pour trente jours, `ETOILES_GITHUB=0` le retire.

### Finances
Un journal par mois : ventes confirmées, charges déclarées, coût des agents, solde. Une vente n'existe que confirmée par la plateforme de paiement (import Stripe avec une clé restreinte en lecture, `STRIPE_SECRET_KEY`) ou saisie à la main **avec sa preuve** (référence de virement, numéro de facture). Les charges récurrentes (abonnement, hébergement, domaine) se déclarent une fois avec leur périodicité. L'export CSV est fait pour l'expert-comptable ; les cellules qui ressembleraient à une formule sont neutralisées.

### Contacts
Un suivi de contacts léger, conforme au RGPD : chaque fiche a une base légale, un rôle, une source, une durée de conservation. Les échanges se notent sur la fiche. Un contact qui s'oppose ne reçoit plus rien. Les fiches arrivées au bout de leur durée sont listées « à oublier » et s'effacent en un clic, le journal des droits restant. Les quatre droits (accès, rectification, opposition, effacement) s'enregistrent depuis la fiche.

### Aquarium
« Regardez vos agents travailler » : chaque bulle est une action réelle des dernières vingt-quatre heures (une demande, un outil appelé, une décision proposée ou prise). Les couloirs correspondent aux fonctions ; les anneaux en pointillé sont des postes libres (ce que feraient les agents de l'édition complète). La ligne de temps rejoue la journée à la vitesse choisie ; « Direct » revient au présent. Survolez un agent pour son détail.

« Créer la page publique » ouvre une **vitrine** à partager : la même scène, sans rien d'interne (ni e-mails, ni montants, ni textes de décision), avec le nom de votre organisation et les prénoms des agents. « Couper le lien » la ferme ; l'ancien lien cesse de fonctionner. « Salle d'attente (TV) » ouvre la même page en plein écran pour une télé dans l'entrée : la scène, l'horloge, les chiffres du jour.

### Catalogue
Les modules qui s'ajoutent au bureau (déploiement cloud, agents supplémentaires, édition hébergée). Le bouton renvoie vers zelij.ai avec l'identifiant de votre installation. Un module reçu s'installe ici en déposant son `pack.json` signé ; le bureau vérifie la signature de l'éditeur, l'interface, et l'empreinte de chaque fichier.

### Factory
La Software factory : l'état de la cible de déploiement et du dépôt, les versions en ligne, les sauvegardes. « Sonder le domaine » relève DNS, certificat, réponse HTTP et en-têtes de sécurité, daté. « Sauvegarder le bureau » écrit une sauvegarde tout de suite. « Proposer une mise en ligne » ouvre une décision ; approuvée, le Bâtisseur déploie la branche principale avec bascule atomique, test de fumée et retour arrière automatique, puis relève le domaine.

### Publications
Les pages rédigées par les agents : brouillon, proposée (demande de fusion ouverte ou brouillon déposé chez l'hébergeur), publiée. Vous fusionnez vous-même.

## Travailler avec les agents

**Demander.** Écrivez comme à un collaborateur : « Prépare une page qui compare nos trois offres », « Fais le point du mois », « Relève les tarifs publics du concurrent X à leur source et date-les ». Plus la demande dit le résultat attendu, meilleure est la réponse.

**Décider.** Lisez la recommandation et les risques. « Demander des changements » avec une consigne précise (« budget 300 euros maximum, retirer l'option 2 ») vaut mieux qu'un refus sec : l'agent revient avec une révision.

**Suivre.** Chaque exécution est enregistrée : entrée, sortie, outils appelés, jetons, coût, durée. Le journal garde qui a fait quoi. Rien n'est effacé.

**Ce que renvoient les outils de lecture** (pages web, fichiers du dépôt) arrive aux agents encadré comme « contenu externe » : des données, jamais des consignes. Aucun modèle n'est à l'abri d'une page écrite pour le tromper ; le bureau ne compte donc pas sur sa seule vigilance. Trois règles tiennent dans le code, même si un agent se laisse convaincre : il n'exécute que les outils de sa fiche ; dès qu'il a lu une donnée privée (dépôt, finances, contacts), il ne peut plus appeler que votre site ; et rien ne part en ligne sans une décision de mise en ligne approuvée par vous.

**D'où vient une décision.** Chaque décision préparée par un agent affiche sa provenance : les pages et les fichiers du dépôt lus pendant sa préparation, et les actions que le bureau a refusées. Trois niveaux : « sans lecture de contenu externe », « après lecture de contenu externe » (relisez la tâche), « à relire avec attention » quand la tâche est confiée à un autre agent ou qu'une action a été refusée en route. Ce relevé vient du bureau, pas de l'agent : une page ne peut ni l'écrire ni l'effacer.

**Fondateur et membres.** Le fondateur décide, installe les modules, ouvre une mise en ligne et la page publique. Un membre rattaché à l'organisation lit et fait des demandes aux agents ; il ne décide pas.

## L'avocat du diable

Sous chaque recommandation, un encart plaide contre elle : trois objections au plus, la question à poser à l'agent avant
d'approuver, ce qui vous ferait changer d'avis, et un verdict (approuver, attendre, refuser). Ce n'est pas un cinquième agent :
il n'a aucun outil, ne lit que le paquet et ne décide rien. Quand il conclut « approuver », c'est qu'il n'a rien trouvé de
solide contre : c'est une information aussi. Il coûte un appel court par décision, compté dans votre plafond ; `AVOCAT_DU_DIABLE=0`
dans `.env` le retire.

## Décider depuis le téléphone

**En swipant.** Connecté au bureau depuis le téléphone, « Décider en swipant » (ou `/decider`) présente les décisions en attente une carte à la fois : à droite pour approuver, à gauche pour refuser, vers le haut pour passer, « M » pour demander une modification. Chaque geste demande une confirmation ; au-delà de `DECIDER_SEUIL_EUR` (200 € par défaut) ou pour une décision irréversible, une case « j'ai lu » s'ajoute.


**Par e-mail.** Dès que l'envoi d'e-mails est configuré (`SMTP_HOST`), chaque décision ouverte par un agent vous arrive en entier : objectif, proposition, options, recommandation, risques, réversibilité. Deux liens, « Approuver » et « Refuser ». Un lien ouvre une page qui rappelle le paquet et vous demande de confirmer : rien n'est décidé tant que vous n'avez pas pressé le bouton. Le lien ne sert qu'une fois et vaut sept jours ; dès que la décision est prise, par n'importe quel chemin, les liens tombent. Pour demander une modification avec une consigne, passez par le bureau. `DECISIONS_PAR_EMAIL=0` coupe ces e-mails.

**Par Telegram.** 1. Écrivez à @BotFather, `/newbot`, donnez-lui un nom : il vous rend un jeton. 2. Écrivez un premier message à votre robot. 3. Ouvrez `https://api.telegram.org/bot<jeton>/getUpdates` dans votre navigateur : le nombre après `"chat":{"id":` est l'identifiant de votre conversation. 4. Dans `.env` : `TELEGRAM_BOT_TOKEN=<jeton>` et `TELEGRAM_CHAT_ID=<identifiant>`, puis redémarrez. Chaque décision arrive alors avec trois boutons. « Demander une modification » vous fait écrire la consigne en réponse au message du robot ; elle est transmise à l'agent, comme depuis le bureau.

**Ce qui ne change pas.** C'est vous qui décidez, et vous seul : un bouton pressé depuis une autre conversation que la vôtre est refusé et journalisé. La décision passe par la même porte que depuis le bureau et le journal dit d'où elle vient (« lien e-mail », « Telegram »). Ce qu'une approbation déclenche est le même. En mode démonstration, rien ne sort.

## Tenir le coût

- Le **plafond mensuel** (`PLAFOND_MENSUEL_EUR`) bloque tout appel au-delà. Il se relève dans `.env`.
- Le **compteur** du Bureau montre la dépense du mois ; la page Finances l'intègre au journal.
- Les **classes de modèles** : `raisonnement` (le plus capable, le plus cher), `equilibre`, `rapide`. Un agent qui ne fait que résumer ou relever peut passer en `rapide` dans sa fiche.
- Le **budget de tours** (`budget_tours`) borne le nombre d'allers-retours avec le modèle par tâche.
- Les tarifs utilisés pour le calcul sont datés dans `core/passerelle.py` ; mettez-les à jour quand l'éditeur du modèle les change.

## Les portraits

Déposez des images carrées (256 px, `webp`, `png` ou `jpg`) dans `portraits/` : `portraits/<identifiant>.webp` pour un agent, `portraits/fondateur.webp` pour vous. Elles apparaissent dans l'aquarium, sur la vitrine et dans l'en-tête du bureau. Les quatre agents de l'édition arrivent avec le portrait d'un personnage fictif (`agents/<identifiant>/portrait.webp`) ; votre fichier dans `portraits/` passe devant. Sans aucune photo, un agent a un monogramme et le fondateur une silhouette. Voir `portraits/README.md`.

## Frugal par construction

Le Bâtisseur et les autres agents obéissent à une échelle avant d'écrire la moindre ligne : est-ce que ça doit exister, le
dépôt l'a-t-il déjà, la bibliothèque standard le fait-elle, une fonction native de la plateforme, une dépendance déjà installée,
une seule ligne suffit-elle, sinon le minimum qui marche. Jamais au détriment de la validation, des erreurs, de la sécurité ou de
l'accessibilité. Toute logique à risque part avec un petit test, et chaque réponse se termine par ce qui n'a pas été vérifié. Les
raccourcis assumés sont marqués « raccourci : » dans le code, avec le moment où y revenir. Résultat attendu : moins de code,
moins de jetons, des demandes de fusion que vous pouvez lire en entier.

## Ce que Zelij Core ne fera jamais

- Payer, acheter, engager une dépense : il n'a aucun moyen de paiement.
- Publier ou mettre en ligne sans votre approbation explicite.
- Fusionner une demande de fusion : c'est vous.
- Envoyer un e-mail à un contact : le suivi note les échanges, il ne les envoie pas (cette fonction appartient aux modules payants, avec une porte de validation).
- Appeler une adresse privée, interne ou de boucle locale ; lire autre chose que des pages https publiques.
- Téléphoner à zelij.ai : l'édition gratuite ne remonte rien.

## En cas de problème

`INSTALLATION.md`, chapitre « Dépannage », couvre la connexion, les e-mails, le certificat, le plafond et les modules. Une faille de sécurité se signale à `securite@zelij.ai`, sans la publier avant correction.

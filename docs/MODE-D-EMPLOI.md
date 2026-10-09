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

### Finances
Un journal par mois : ventes confirmées, charges déclarées, coût des agents, solde. Une vente n'existe que confirmée par la plateforme de paiement (import Stripe avec une clé restreinte en lecture, `STRIPE_SECRET_KEY`) ou saisie à la main **avec sa preuve** (référence de virement, numéro de facture). Les charges récurrentes (abonnement, hébergement, domaine) se déclarent une fois avec leur périodicité. L'export CSV est fait pour l'expert-comptable ; les cellules qui ressembleraient à une formule sont neutralisées.

### Contacts
Un suivi de contacts léger, conforme au RGPD : chaque fiche a une base légale, un rôle, une source, une durée de conservation. Les échanges se notent sur la fiche. Un contact qui s'oppose ne reçoit plus rien. Les fiches arrivées au bout de leur durée sont listées « à oublier » et s'effacent en un clic, le journal des droits restant. Les quatre droits (accès, rectification, opposition, effacement) s'enregistrent depuis la fiche.

### Aquarium
« Regardez vos agents travailler » : chaque bulle est une action réelle des dernières vingt-quatre heures (une demande, un outil appelé, une décision proposée ou prise). Les couloirs correspondent aux fonctions ; les anneaux en pointillé sont des postes libres (ce que feraient les agents de l'édition complète). La ligne de temps rejoue la journée à la vitesse choisie ; « Direct » revient au présent. Survolez un agent pour son détail.

« Créer la page publique » ouvre une **vitrine** à partager : la même scène, sans rien d'interne (ni e-mails, ni montants, ni textes de décision), avec le nom de votre organisation et les prénoms des agents. « Couper le lien » la ferme ; l'ancien lien cesse de fonctionner.

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

**Ce que renvoient les outils de lecture** (pages web, fichiers du dépôt) arrive aux agents encadré comme « contenu externe » : des données, jamais des consignes. Une page qui contiendrait des instructions destinées aux agents ne les fera pas agir.

## Tenir le coût

- Le **plafond mensuel** (`PLAFOND_MENSUEL_EUR`) bloque tout appel au-delà. Il se relève dans `.env`.
- Le **compteur** du Bureau montre la dépense du mois ; la page Finances l'intègre au journal.
- Les **classes de modèles** : `raisonnement` (le plus capable, le plus cher), `equilibre`, `rapide`. Un agent qui ne fait que résumer ou relever peut passer en `rapide` dans sa fiche.
- Le **budget de tours** (`budget_tours`) borne le nombre d'allers-retours avec le modèle par tâche.
- Les tarifs utilisés pour le calcul sont datés dans `core/passerelle.py` ; mettez-les à jour quand l'éditeur du modèle les change.

## Les portraits

Déposez des images carrées (256 px, `webp`, `png` ou `jpg`) dans `portraits/` : `portraits/<identifiant>.webp` pour un agent, `portraits/fondateur.webp` pour vous. Elles apparaissent dans l'aquarium, sur la vitrine et dans l'en-tête du bureau. Sans photo, les agents ont un monogramme et le fondateur une silhouette. Voir `portraits/README.md`.

## Ce que Zelij Core ne fera jamais

- Payer, acheter, engager une dépense : il n'a aucun moyen de paiement.
- Publier ou mettre en ligne sans votre approbation explicite.
- Fusionner une demande de fusion : c'est vous.
- Envoyer un e-mail à un contact : le suivi note les échanges, il ne les envoie pas (cette fonction appartient aux modules payants, avec une porte de validation).
- Appeler une adresse privée, interne ou de boucle locale ; lire autre chose que des pages https publiques.
- Téléphoner à zelij.ai : l'édition gratuite ne remonte rien.

## En cas de problème

`INSTALLATION.md`, chapitre « Dépannage », couvre la connexion, les e-mails, le certificat, le plafond et les modules. Une faille de sécurité se signale à `securite@zelij.ai`, sans la publier avant correction.

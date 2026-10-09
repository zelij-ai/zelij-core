# Contribuer à Zelij Core

Merci de vouloir améliorer le noyau. Voici comment une contribution arrive jusque dans une version, et ce qui fait qu'elle est acceptée.

## Avant d'écrire du code

- **Une issue d'abord** pour tout ce qui dépasse une correction évidente : dites le problème, ce que vous proposez, ce que ça change pour un fondateur qui utilise le bureau. On se met d'accord sur l'approche avant que vous passiez du temps dessus.
- **Le périmètre de l'édition libre est stable** : quatre agents, un dépôt, un serveur ou OVH, compta et contacts légers. Les agents supplémentaires, les cibles cloud et l'hébergement sont des modules de l'éditeur. Une contribution qui élargit ce périmètre est discutée en issue ; elle peut devenir un module.
- **Le principe ne se négocie pas** : les agents proposent, le fondateur décide. Rien de ce qui engage de l'argent, expose au public, supprime ou n'est pas réversible ne contourne le paquet de décision.

## Proposer une cible de déploiement ou un module

Vous avez construit une cible (un hébergeur, un cloud) ou un module avec la Software factory ? Proposez-la ici plutôt que de la garder dans votre coin : si elle est reprise dans le noyau ou dans le catalogue, **vous êtes crédité** dans le fichier `CHANGELOG.md` et dans le module, et le pack correspondant du catalogue est **gratuit pour vous, à vie**. Ouvrez une issue « Proposition de module » avec le dépôt, ce que la cible sait faire, et ce qu'elle exige du fondateur (comptes, clés, coûts).

## Écrire la contribution

1. Forkez, créez une branche nommée par ce qu'elle fait (`correctif-export-csv`, `cible-hetzner`).
2. Installez : `pip install -r requirements.txt`, puis `python -m pytest -q` doit être vert avant de toucher quoi que ce soit.
3. **Un test par changement.** Une correction vient avec le test qui échouait ; une fonction vient avec son test. Pas de test, pas de fusion.
4. Respectez la maison : français dans les noms, les messages et les commentaires ; pas de bibliothèque ajoutée sans l'avoir dit dans l'issue ; aucun appel réseau dans les tests (les clients `httpx` sont injectables, servez-vous-en) ; aucune donnée réelle (adresses, noms, clés) dans le code ni dans les tests.
5. Avant d'ouvrir la demande de fusion :
   ```bash
   python -m pytest -q
   pyflakes core scripts tests
   python scripts/controle_publication.py
   ```
6. Ouvrez la demande de fusion vers `main` avec le gabarit proposé : ce que ça change, pourquoi, comment vous l'avez vérifié.

## Ce qui arrête une contribution

- Un secret, une clé, une adresse réelle dans le diff.
- Un script ou une ressource chargée depuis un domaine tiers dans le bureau.
- Un appel du modèle qui n'est pas borné par le plafond et le budget de tours.
- Une action d'agent qui engage sans paquet de décision.
- Un changement de dépendance sans justification, ou vers une version avec un avis de sécurité connu (`pip-audit`).

## Relecture et fusion

L'éditeur relit chaque demande de fusion ; la CI doit être verte. Attendez-vous à des questions courtes et précises. Une fois fusionnée, la contribution part dans la version suivante, mentionnée dans `CHANGELOG.md` avec votre nom (ou votre pseudonyme GitHub, à votre choix).

## Licence

Le noyau est sous AGPL-3.0. En contribuant, vous acceptez que votre contribution soit publiée sous cette licence. Vous gardez vos droits d'auteur.

## Support

Les issues servent aux bogues et aux propositions. Le guide d'installation (`docs/INSTALLATION.md`) et le mode d'emploi (`docs/MODE-D-EMPLOI.md`) répondent aux questions d'usage ; il n'y a pas de support individuel en dehors d'eux dans l'édition libre.

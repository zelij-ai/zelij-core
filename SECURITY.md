# Sécurité

## Signaler une faille

Écrivez à **securite@zelij.ai** avec ce que vous avez vu, comment le reproduire et, si vous l'avez, un correctif. N'ouvrez pas d'issue publique avant que la correction soit publiée : une faille décrite en public avant son correctif met en danger toutes les installations.

Vous recevrez un accusé de réception sous cinq jours ouvrés, puis un échange jusqu'à la correction. Les correctifs de sécurité sortent dans une version dédiée, signalée dans `CHANGELOG.md`, avec votre nom si vous le souhaitez.

Pas de programme de récompense : un merci public et une mention dans le journal des versions.

## Versions suivies

Seule la dernière version publiée reçoit des correctifs. Mettez à jour avec `git pull` puis `docker compose up -d --build` (voir `docs/INSTALLATION.md`).

## Ce que le noyau garantit

Chaque point ci-dessous est testé dans `tests/test_securite.py` ; un changement qui le casse ne passe pas la CI.

- **Modules** : rien ne s'installe ni ne s'exécute sans la signature Ed25519 de l'éditeur, et la signature couvre l'empreinte SHA-256 de chaque fichier du module.
- **Connexion** : liens à usage unique de vingt minutes, hachés en base ; freins par adresse, par IP et global ; en production, aucun lien n'est créé ni journalisé si l'envoi d'e-mails n'est pas configuré.
- **Formulaires** : cookie de session HMAC `HttpOnly` `SameSite=Strict`, contrôle d'origine et jeton anti-CSRF sur chaque POST.
- **Pages** : politique de sécurité du contenu stricte, aucun script en ligne, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS en https.
- **Agents** : ce qu'un agent lit arrive encadré comme contenu externe, jamais comme consigne ; il ne lit que des adresses https publiques (adresses privées, de boucle locale, de lien local et noms internes refusés à chaque saut) ; la porte de sécurité bloque secrets, fichiers d'infrastructure, scripts, cadres et appels réseau tiers dans ce qu'il propose.
- **Conteneur** : utilisateur sans privilège, système de fichiers en lecture seule, aucune capacité, pas d'élévation.
- **Exports** : les cellules des CSV qui ressemblent à une formule de tableur sont neutralisées.

## Ce que le noyau ne protège pas

La clé Claude du fondateur, le `.env`, la clé SSH de déploiement et la base vivent sur la machine du fondateur : leur protection dépend de cette machine (mises à jour, pare-feu, accès). Le guide d'installation dit comment les tenir hors du dépôt et hors des journaux.

## Vérifications avant chaque version

`python -m pytest -q`, `pyflakes core scripts tests`, `pip-audit -r requirements.txt` (aucun avis), `bandit -r core scripts -ll` (aucun constat moyen ou haut), `python scripts/controle_publication.py` (rien d'interne). La CI les exécute sur chaque demande de fusion.

# Installing Zelij Core

This guide takes you from a bare machine to an office running over https, with your agents, your Claude key and your backups. Allow an hour the first time. Every step says what it does and how to check that it worked.

Zelij Core is two containers: the office (FastAPI, which also hosts the agents) and a PostgreSQL database. Nothing else runs: no queue, no cache, no third-party service. The agents talk to Claude with **your** key and write nowhere but your database.

## 1. What you need

| Need | Why | Where to get it |
|---|---|---|
| A Linux machine with Docker and Docker Compose (v2.24 or later) | It hosts the office | A 2 GB VPS is enough; locally, Docker Desktop works |
| A Claude API key | Every agent call is billed to this key; the cost shows in the office | https://console.anthropic.com/ (create the key, set a spending limit on the console side too) |
| A domain name pointing to the machine (optional locally, required in production) | The office over https, login links that work | Your registrar: an `A` record to the machine's address |
| An SMTP account (optional locally, required in production) | Login links go out by e-mail; without SMTP the office refuses to send them in production | Your mail host, or a sending service with a username and password |

No account to create at zelij.ai: the free edition phones nobody.

## 2. Get the code

```bash
git clone https://github.com/zelij-ai/zelij-core.git
cd zelij-core
```

Or download the latest release archive and unpack it.

## 3. Write the configuration

```bash
cp .env.example .env
```

Open `.env` and fill in, in this order:

1. `ANTHROPIC_API_KEY`: your Claude key.
2. `PLAFOND_MENSUEL_EUR`: the monthly ceiling in euros; beyond it no agent is called until you raise it. Start at 20 or 50.
3. `CORE_DB_PASSWORD`: a database password, generated once and never typed anywhere else:
   ```bash
   openssl rand -hex 24
   ```
4. `SECRET_KEY`: the key that signs your sessions, at least 48 random characters, generated the same way. Without it the container refuses to start.
5. `APP_ORIGIN`: the public address of the office, e.g. `https://office.your-domain.com`. Locally, leave `http://localhost:8000`. It is used for login links and the origin check on forms: if it is wrong, the links you receive lead nowhere.
6. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`: how login links are sent. The sender address must belong to a domain your SMTP is allowed to use.
7. `ZELIJ_CLE_PUBLIQUE`: already filled in. It is the public key of the module publisher; change it only if you install modules signed by someone else.

The rest (`SITE_*`, `SSH_*`, `OVH_*`, `GITHUB_TOKEN`) belongs to the Software factory and is filled in later, in chapter 8.

Never commit `.env`: it is in `.gitignore`.

## 4. Start locally (http)

```bash
docker compose up -d --build
docker compose logs -f core-app
```

When the logs show `Uvicorn running on http://0.0.0.0:8000`, open http://localhost:8000. Check: http://localhost:8000/healthz answers `{"ok": true, "service": "zelij-core", "version": "…"}`.

Port 8000 is reachable from the machine itself only (`127.0.0.1`): over plain http, neither the login link nor the session should travel on a network. To open the office to others, go through chapter 5 (https). If you know what you are doing (trusted private network), `CORE_ECOUTE=0.0.0.0` in `.env` publishes the port on every interface.

Without SMTP, the login link is written to the container logs (never in production): request a link on the login page, then copy the `http://localhost:8000/connexion/…` address from `docker compose logs core-app`.

### Without building the image

Every release publishes a ready image on the GitHub registry. To use it instead of building:

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Pin the version in `.env` with `CORE_IMAGE_TAG=v0.7.2`; without it, `latest` follows the newest release at every restart. `docker-compose.image.yml` can also be added to the chapter 5 command for https.

## 5. Go live over https

`docker-compose.tls.yml` adds a Caddy server in front of the office: automatic certificate, automatic renewal, http redirected to https. Three conditions: the domain points to the machine, ports 80 and 443 are open, `CORE_DOMAINE` is set in `.env`.

```bash
# in .env
CORE_DOMAINE=office.your-domain.com
APP_ORIGIN=https://office.your-domain.com
```

```bash
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

Check: https://office.your-domain.com/healthz answers, the padlock is there, and http://office.your-domain.com redirects to https. Port 8000 is no longer published on the machine: only Caddy talks to the office.

If you already run a TLS server (Nginx, Traefik, another Caddy), keep `docker-compose.yml` alone and point your server to `127.0.0.1:8000` with the `X-Forwarded-For` and `X-Forwarded-Proto` headers, and add `FORWARDED_ALLOW_IPS=*` to `.env`: the office trusts these headers only when you tell it to, and since the port is reachable from the machine only, your server alone can set them.

## 6. First login

1. Open the office, type your e-mail address, request the link.
2. Click the link you receive (valid twenty minutes, once). **The first address that logs in creates the organisation and becomes the founder; after that, no unknown address receives a link.** An installation holds a single organisation: your keys (model, payments, repository, server) serve it alone. If the office is reachable before your first login, set `FONDATEUR_EMAIL=you@your-domain.com` in `.env`: only that address will be able to create the organisation.
3. You land on the Office: the chief of staff is waiting. Make a simple request to check the Claude key works: "Introduce me to the team". The cost of the call shows immediately in the monthly counter.

Inviting someone: the Contacts page is not for that; an invitation is a login link carrying your organisation's identifier. That feature comes with the full edition; in the free edition the office is the founder's.

## 7. Customise: agents, portraits, language

- **Agents** live in `agents/<identifier>/agent.md`: a header (`id`, `nom`, `fonction`, `classe_modele`, `outils`, `budget_tours`, `couloir`) and, below it, the instructions. Edit the instructions, the name, the role; add an agent by copying a folder. The office re-reads the cards on every page.
- **The model** of each agent comes from its class (`raisonnement`, `equilibre`, `rapide`). To force a specific model: `MODELE_CHEF_DE_CABINET=claude-sonnet-5-5` in `.env`.
- **Portraits**: drop a square image (256 px, `webp`, `png` or `jpg`) at `portraits/<identifier>.webp` for an agent, `portraits/fondateur.webp` for yourself. Without a photo the office draws a monogram for agents and a silhouette for the founder. `portraits/README.md` details the formats. With Docker the folder is already mounted (`./portraits:/srv/app/portraits:ro`).
- **Language**: the office is in French; the agents answer in French by instruction. For another language, edit the agent cards and rule 3 of the house rules in `core/executeur.py`.

## 8. The Software factory (optional)

The Builder reads and proposes changes on **one** GitHub repository (the company site), through pull requests you review. It deploys to a Linux server (SSH) or to OVH, after your approval.

1. Create a repository for the site (a static site: an `index.html` at the root is enough to start).
2. Create a fine-grained GitHub token, **limited to that repository**, with `contents` and `pull requests` write permissions.
3. In `.env`: `SITE_DEPOT=your-account/your-site`, `GITHUB_TOKEN=…`, `SITE_DOMAINE=https://www.your-site.com`.
4. SSH target: `SSH_HOTE`, `SSH_UTILISATEUR`, `SSH_PORT`, `SITE_DOSSIER` (the versions folder on the server, e.g. `/var/www/site`) and `SSH_CLE`, the path of a private key **mounted read-only** in the container (declare the volume in `docker-compose.yml`, e.g. `./secrets/deploy:/run/secrets/ssh_cle:ro`, and `SSH_CLE=/run/secrets/ssh_cle`). Recommended: `SSH_CLE_HOTE` with the server's public host key (`ssh-keyscan -t ed25519 your-server`), to refuse any other machine.
5. OVH target: `CIBLE=ovh` and the three OVH API keys (created at https://eu.api.ovh.com/createToken/ with `GET`, `POST`, `PUT` on `/domain/zone/*`).
6. Restart (`docker compose up -d`), open the Factory page: "Probe the domain" must return a report, "Propose a release" opens a decision.

The Builder never merges, never pays, never touches the office. Its security gate refuses secrets, infrastructure files, third-party scripts and frames, and dependencies with known vulnerabilities.

## 9. Backups and restore

Every night the office writes a compressed export of the database to the `core-sauvegardes` volume (the last fourteen are kept, manual backups included; they are not encrypted, protect the volume like the database). To get them off the machine:

```bash
docker compose cp core-app:/data/sauvegardes ./backups-$(date +%F)
```

Restore from a `bureau-YYYYMMDD-HHMMSS.sql.gz` backup:

```bash
docker compose stop core-app
gunzip -c bureau-YYYYMMDD-HHMMSS.sql.gz | docker compose exec -T core-db psql -U core -d core
docker compose start core-app
```

A manual backup runs from the Factory page ("Back up the office").

## 10. Update

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

The database schema updates itself at startup. Read the release notes before a major version: they say whether a variable changes.

## 11. Install a module

The office Catalogue links to zelij.ai for paid modules (cloud deployment, extra agents). A module arrives as a parcel: a folder with its code and a `pack.json` manifest signed by the publisher.

1. Unpack the parcel in the modules folder (`ZELIJ_MODULES_DIR`, by default the `core-modules` volume; with Docker: `docker compose cp ./cible_gcp core-app:/srv/app/modules/`).
2. In the office: Catalogue, "Install a signed module", drop the `pack.json`.
3. Follow the module's README for its variables, restart.

The office refuses any module that is unsigned, signed for another interface, or whose files differ from what the publisher signed.

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The container stops with `SECRET_KEY absente en production` | Incomplete `.env` | Set `SECRET_KEY` (48 random characters) |
| The e-mailed link lands on "This link is no longer valid" | Wrong `APP_ORIGIN`, link already used, or older than twenty minutes | Fix `APP_ORIGIN`, request a new link |
| "E-mail sending is not configured" | `SMTP_HOST` empty in production | Configure SMTP; locally, read the link in the logs |
| "Too many requests" | Login brakes: 5 per address and 10 per IP address over fifteen minutes | Wait a quarter of an hour |
| "Monthly ceiling reached" | `PLAFOND_MENSUEL_EUR` exceeded | Raise the ceiling in `.env`, restart |
| No certificate | Domain not yet pointing to the machine, or port 80 closed | `dig +short office.your-domain.com`, open 80 and 443, `docker compose logs caddy` |
| A module is "ignored" in the report | Missing signature, incompatible interface or modified file | Use the original parcel, do not edit its contents |
| `origine refusée` on a form | The office is called from an address other than `APP_ORIGIN` | Use the declared address, or fix it |

Logs: `docker compose logs -f core-app`. Status: `/healthz`. Logs never contain a login link in production.

## 13. Uninstall

```bash
docker compose -f docker-compose.yml -f docker-compose.tls.yml down
docker volume rm zelij-core_core-db zelij-core_core-sauvegardes zelij-core_core-modules zelij-core_caddy-data
```

The second command erases the database, the backups and the modules: take a backup first (chapter 9).

# Zelij Core

**Build your startup 100 % AI-native.** One office, four agents working for you, and you make every decision that matters.

> Private preparation repository (decision of 8 October 2026). Nothing is published until the publication control passes and publication is decided. Licence: GNU AGPL v3. French is the working language of the product; this file is a short English summary.

## What the core does

- **The office**: one page. Pending decisions, a request to the Chief of staff, the latest runs with their cost, the journal, the agents, the installed modules.
- **The decision packet**: objective, proposal, why now, options, recommendation, risks, reversibility, plan, rollback, impact. An incomplete packet never opens. Approve, reject, or ask for changes with a mandatory instruction sent back to the agent.
- **House rules**: nothing that commits the company (money, public exposure, deletion, irreversible) happens without a decision; a fact is dated and sourced or marked "unverified"; the journal is never erased.
- **The gateway**: the founder's Claude key, the cost of every call computed from usage and dated public prices, a monthly cap that blocks.
- **The runner**: a bounded tool loop on the official SDK, sober tools, a model refusal handled as a result.
- **Modules**: the only way to extend the core. Stable interface, `pack.json` manifest signed with Ed25519 by the publisher, verified before installation.
- **Four agents**: Chief of staff, Growth, Finance & clients, Builder. Written limits: the Builder never merges, never edits the office itself, never pays.
- **Finance**: confirmed sales (read-only Stripe import or manual entry with proof), recurring declared expenses, agent cost, monthly journal, CSV export. Nothing is declared or invoiced.
- **Contacts**: one record per person, mandatory legal basis, retention period, exchanges, exercised rights; an opposed contact receives nothing, an expired contact is forgotten and only the rights log remains.
- **Publication**: a page written by Growth becomes a draft, then a decision; approved, it is proposed to your site as a GitHub pull request or a WordPress draft. The last gesture is yours.
- **Aquarium**: watch your agents work. Every bubble is a real action from the last 24 hours. Dotted silhouettes are open positions. A public page can be shared with the "by zelij.ai" badge.

## Run

```bash
cp .env.example .env
docker compose up -d --build
```

Then open `http://localhost:8000`. Tests: `python -m pytest -q`. Publication control: `python scripts/controle_publication.py`.

Full guides: **[Installation](docs/INSTALLATION.en.md)** (bare machine → office over https, SMTP, Software factory, backups, troubleshooting), **[User guide](docs/MODE-D-EMPLOI.en.md)** (every page, the agents, decisions, cost). Photos of the founder and agents go in [`portraits/`](portraits/README.md).

by zelij.ai — https://zelij.ai/

# Zelij Core user guide

Zelij Core is an office: four AI agents work in it, and you decide. This guide describes every page, what the agents do, what they will never do, and how to keep the cost in check. For installation see `INSTALLATION.en.md`.

## The principle

The agents **propose**, the founder **decides**. Anything that commits money, exposes something publicly, deletes data or cannot be undone goes through a **decision packet**: objective, proposal, why now, options, recommendation, risks, reversibility, plan, rollback, impact. You approve, refuse, or request changes with an instruction. Nothing happens before.

A fact stated by an agent is dated and sourced (the address it read), otherwise it is marked "unverified". Agents sign "First name Last name (identifier), role".

## The team

| Agent | Identifier | What they do | Tools |
|---|---|---|---|
| Camille Aubert, chief of staff | `chef-de-cabinet` | Receives your requests, prepares decision packets, dispatches the work | page reading, date |
| Élise Tanguy, marketing and products | `croissance` | Writes pages for the site, proposes angles, collects facts at the source | page reading, date |
| Nour Bellamy, finance and clients | `finances-clients` | Reads the ledger and the contact follow-up, reports, flags what is stalling | finance report, contacts to handle |
| Sacha Ferrand, software factory | `batisseur` | Reads the site repository, proposes changes through pull requests, probes the domain, deploys after approval | repository, security gate, probe, release, target status |

Each agent has a card at `agents/<identifier>/agent.md`: edit it to change the name, role, instructions, model or turn budget. An extra agent is one more folder.

## The office pages

### Office
The home page. At the top, the **monthly counter**: agent spend against the ceiling. In the middle, **pending decisions**, each with three buttons: Approve, Refuse, Request changes (the instruction is mandatory: it goes to the requesting agent, who comes back with a revision). Below, the **Ask** form to the chief of staff (or another agent), the latest runs with their cost, the journal, the agents, the installed modules.

A request beyond this office (cloud deployment, prospecting, SEO, price watch, monitoring, software factory, hosting) opens a 'build it yourself or install the module' packet: the chief of staff weighs the Builder's build time against the catalogue module; approving the module option takes you to the catalogue with the purchase link ready. A simple request gets a direct answer. A request that commits something opens a packet. A page request ("write a Pricing page") produces a draft and opens a publication decision: the page only goes to the site after your approval, and only as a pull request or a draft, never live directly.

### Finance
One ledger per month: confirmed sales, declared expenses, agent cost, balance. A sale only exists once confirmed by the payment platform (Stripe import with a read-only restricted key, `STRIPE_SECRET_KEY`) or entered by hand **with its proof** (transfer reference, invoice number). Recurring expenses (subscription, hosting, domain) are declared once with their periodicity. The CSV export is meant for the accountant; cells that would look like a formula are neutralised.

### Contacts
A light, GDPR-compliant contact follow-up: every card has a legal basis, a role, a source, a retention period. Exchanges are noted on the card. A contact who objects receives nothing more. Cards past their retention are listed "to forget" and erased in one click, the rights journal remaining. The four rights (access, rectification, objection, erasure) are recorded from the card.

### Aquarium
"Watch your agents work": every bubble is a real action from the last twenty-four hours (a request, a tool call, a decision proposed or taken). Lanes match roles; dotted rings are open positions (what the full edition's agents would do). The timeline replays the day at the chosen speed; "Live" returns to the present. Hover an agent for details.

"Create the public page" opens a **showcase** to share: the same scene, with nothing internal (no e-mails, amounts or decision texts), with your organisation's name and the agents' first names. "Cut the link" closes it; the old link stops working.

### Catalogue
The modules that extend the office (cloud deployment, extra agents, hosted edition). The button links to zelij.ai with your installation identifier. A received module is installed here by dropping its signed `pack.json`; the office checks the publisher's signature, the interface, and the hash of every file.

### Factory
The Software factory: the state of the deployment target and the repository, the versions online, the backups. "Probe the domain" reports DNS, certificate, HTTP response and security headers, dated. "Back up the office" writes a backup now. "Propose a release" opens a decision; once approved, the Builder deploys the main branch with an atomic switch, a smoke test and automatic rollback, then probes the domain.

### Publications
The pages written by the agents: draft, proposed (pull request open or draft deposited at the host), published. You merge yourself.

## Working with the agents

**Ask.** Write as you would to a colleague: "Prepare a page comparing our three offers", "Give me the monthly report", "Collect competitor X's public prices at their source and date them". The more the request states the expected result, the better the answer.

**Decide.** Read the recommendation and the risks. "Request changes" with a precise instruction ("budget 300 euros maximum, drop option 2") beats a flat refusal: the agent comes back with a revision.

**Follow.** Every run is recorded: input, output, tools called, tokens, cost, duration. The journal keeps who did what. Nothing is erased.

**What reading tools return** (web pages, repository files) reaches the agents framed as "external content": data, never instructions. No model is immune to a page written to deceive it, so the office does not rely on its vigilance alone. Three rules hold in the code even if an agent is talked into something: it only runs the tools on its sheet; once it has read private data (repository, finances, contacts) it can only call your own site; and nothing goes live without a go-live decision approved by you.

**Where a decision comes from.** Every decision prepared by an agent shows its provenance: the pages and repository files read while preparing it, and the actions the office refused. Three levels: "no external content read", "after reading external content" (re-read the task), "read carefully before approving" when the task is handed to another agent or an action was refused along the way. This record comes from the office, not from the agent: a page can neither write nor erase it.

**Founder and members.** The founder decides, installs modules, opens a go-live and the public page. A member attached to the organisation reads and makes requests to the agents; a member does not decide.

## Keeping the cost in check

- The **monthly ceiling** (`PLAFOND_MENSUEL_EUR`) blocks every call beyond it. Raise it in `.env`.
- The **counter** on the Office shows the month's spend; the Finance page folds it into the ledger.
- **Model classes**: `raisonnement` (most capable, most expensive), `equilibre`, `rapide`. An agent that only summarises or collects can switch to `rapide` in its card.
- The **turn budget** (`budget_tours`) caps the number of round trips with the model per task.
- The prices used for the calculation are dated in `core/passerelle.py`; update them when the model publisher changes them.

## Portraits

Drop square images (256 px, `webp`, `png` or `jpg`) in `portraits/`: `portraits/<identifier>.webp` for an agent, `portraits/fondateur.webp` for yourself. They appear in the aquarium, on the showcase and in the office header. Without a photo, agents get a monogram and the founder a silhouette. See `portraits/README.md`.

## What Zelij Core will never do

- Pay, buy, commit an expense: it has no means of payment.
- Publish or deploy without your explicit approval.
- Merge a pull request: that is you.
- E-mail a contact: the follow-up records exchanges, it does not send them (that belongs to the paid modules, behind a validation gate).
- Call a private, internal or loopback address; read anything but public https pages.
- Phone zelij.ai: the free edition reports nothing.

## When something goes wrong

`INSTALLATION.en.md`, "Troubleshooting", covers login, e-mail, certificate, ceiling and modules. Report a security issue to `securite@zelij.ai` without publishing it before it is fixed.

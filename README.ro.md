# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · **Română**

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Construiește-ți startup-ul 100 % nativ IA.** Un birou în care patru agenți lucrează pentru tine: ei propun, tu decizi. Mașina ta, cheia ta Claude, datele tale; nimic nu „sună acasă”.

![Acvariul Zelij Core: fondatorul și patru agenți discută, propun decizii și execută ce a fost aprobat](docs/img/aquarium.gif)

*Acvariul într-o zi simulată (aici în franceză). În instalarea ta, fiecare card este o acțiune reală a agenților tăi, în direct și cu redare pe douăzeci și patru de ore. Auriul ești tu: nimic angajant nu se întâmplă înaintea deciziei tale. Chipurile aparțin unor personaje fictive.*

## Ce face nucleul

- **Biroul**: o pagină. Deciziile în așteptare, o cerere către șeful de cabinet, ultimele execuții cu costul lor, jurnalul, agenții, modulele instalate.
- **Pachetul de decizie**: obiectiv, propunere, de ce acum, opțiuni, recomandare, riscuri, reversibilitate, plan, revenire, impact. Un pachet incomplet nu se deschide. Aprobi, refuzi sau ceri modificări cu o instrucțiune obligatorie transmisă agentului.
- **Regulile casei**: nimic angajant (bani, expunere publică, ștergere, ireversibil) nu se face fără decizie; un fapt este datat și are sursă sau este marcat „neverificat”; jurnalul nu se șterge niciodată.
- **Poarta**: cheia Claude a fondatorului, costul fiecărui apel calculat din utilizare și din tarifele publice datate, un plafon lunar care blochează.
- **Executorul**: o buclă de apeluri limitată (buget de ture per agent), unelte sobre, un refuz al modelului tratat ca rezultat.
- **Modulele**: singura cale de a extinde nucleul. Interfață stabilă, manifest `pack.json` semnat Ed25519 de editor, amprenta fiecărui fișier acoperită de semnătură, verificare înainte de instalare. Țintele de deploy și agenții suplimentari trec pe aici.
- **Finanțe**: vânzări confirmate (import Stripe doar în citire sau înregistrare cu dovadă), cheltuieli declarate care revin lunar, costul agenților măsurat, jurnalul lunii, export CSV pentru contabil. Nimic nu este declarat sau facturat.
- **Contacte**: o fișă per persoană, temei legal obligatoriu, durată de păstrare, schimburi, drepturi exercitate; un contact care se opune nu mai primește nimic, un contact expirat este uitat și rămâne doar jurnalul drepturilor.
- **Publicare**: o pagină scrisă de agentul de marketing devine ciornă, apoi decizie; aprobată, este propusă site-ului ca pull request pe GitHub sau ciornă WordPress. Ultimul gest, îmbinarea sau publicarea, îți aparține.
- **În buzunar**: fiecare decizie ajunge pe telefonul tău, prin e-mail cu două linkuri semnate de unică folosință sau prin Telegram cu trei butoane. Aprobi din coada de la metrou; acvariul se mișcă imediat ce răspunzi. Aceeași ușă, același jurnal ca de la birou.
- **Acvariu**: privește-ți agenții lucrând; fiecare bulă este o acțiune reală din ultimele 24 de ore, inelele punctate sunt posturi libere. O pagină publică partajabilă, cu insigna „by zelij.ai”.
- **Catalog**: ce nu conține ediția liberă, numit cinstit; un modul cumpărat de la editor se instalează aici, semnat și verificat. Nicio plată nu trece prin birou.
- **Software factory**: Constructorul citește și propune într-un singur depozit, prin pull request-uri care trec poarta de securitate (300 de linii, doar text, niciun secret, niciun fișier de infrastructură, dependențe fără vulnerabilități cunoscute conform OSV); punere în producție pe un server Linux prin SSH sau la OVH (domeniu și DNS prin API) cu comutare atomică, test de fum și revenire; sondă de domeniu; backup zilnic al biroului. Nu îmbină niciodată, nu plătește niciodată, nu atinge niciodată biroul.
- **Agenții**: un dosar per agent, un `agent.md` cu un antet simplu și instrucțiuni în franceză. Patru agenți: Camille Aubert (șefă de cabinet), Élise Tanguy (creștere, marketing și produse), Nour Bellamy (finanțe și clienți), Sacha Ferrand (constructor, software factory). Fondatorul i se adresează fiecăruia din birou; un pachet aprobat care desemnează un agent și o sarcină se execută imediat, în limitele planului.

## Încearcă într-un minut, fără cheie

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Deschide `http://localhost:8000` și intră în demonstrație: o companie fictivă, patru agenți simulați, decizii de aprobat, acvariul care le redă ziua. Nicio cheie, niciun cont, niciun cost; nimic nu este trimis unui model și totul dispare la oprire. Când ești convins, treci la instalarea reală de mai jos. Biroul în sine este în franceză.

## Pornire

```bash
cp .env.example .env     # cheia Claude, plafonul, SECRET_KEY, parola bazei de date
docker compose up -d --build
```

Biroul răspunde la `http://localhost:8000`. Fără SMTP, linkul de conectare este scris în jurnalele containerului (`docker compose logs core-app`).

Ghiduri complete (în engleză): **[Instalare](docs/INSTALLATION.en.md)** (mașină goală → birou pe https, SMTP, software factory, backup-uri, depanare), **[Manual de utilizare](docs/MODE-D-EMPLOI.en.md)** (fiecare pagină, agenții, deciziile, costul). Fotografiile fondatorului și ale agenților se pun în [`portraits/`](portraits/README.md) (descriere în franceză).

Din imaginea publicată, fără build local (`CORE_IMAGE_TAG=v…` în `.env` fixează versiunea):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Local, fără Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Cheia publică a editorului

Modulele din catalog sunt semnate de zelij.ai. Cheia publică de pus în `ZELIJ_CLE_PUBLIQUE` (deja completată în `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Securitate

Ce garantează nucleul, și ce este testat (`tests/test_securite.py`):

- **Module**: un modul se instalează și rulează doar semnat de editor (Ed25519), iar semnătura acoperă amprenta SHA-256 a fiecărui fișier de cod: un fișier modificat, adăugat sau eliminat după semnare scoate modulul din joc.
- **Conectare**: linkuri de unică folosință de 20 de minute, cu hash în bază; frâne per adresă, per IP și globale pe cererile de link, ca biroul să nu devină niciodată releu de e-mail; fără SMTP configurat în producție, niciun link nu este creat sau jurnalizat.
- **Formulare**: cookie de sesiune HMAC `HttpOnly` `SameSite=Strict`, control al originii și token anti-CSRF per sesiune la fiecare POST.
- **Pagini**: politică strictă de securitate a conținutului (`default-src 'self'`, niciun script inline, niciun cadru), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS când originea este https.
- **Agenți**: ce citește un agent (pagină web, fișier din depozit) îi ajunge încadrat drept conținut extern, niciodată ca instrucțiune; un agent rulează doar uneltele din fișa sa și, de îndată ce a citit o dată privată, nu mai poate apela decât site-ul companiei; citește doar adrese https publice (adrese private, loopback, link-local și nume interne refuzate la fiecare salt de redirecționare, răspuns plafonat); poarta de securitate blochează secrete, fișiere de infrastructură, scripturi terțe, cadre și apeluri de rețea.
- **Container**: utilizator fără privilegii, sistem de fișiere doar în citire, nicio capabilitate, fără escaladare; cheia de host a serverului SSH poate fi fixată (`SSH_CLE_HOTE`).
- **Export contabil**: celulele care seamănă cu o formulă de foaie de calcul sunt neutralizate.

Raportează o vulnerabilitate la `securite@zelij.ai`, fără a o publica înainte de corectare. Înaintea fiecărei versiuni, `pip-audit -r requirements.txt` și `bandit -r core scripts -ll` trebuie să revină goale.

## Contribuție și versiuni

`CONTRIBUTING.md` (în franceză) explică cum ajunge o contribuție într-o versiune, inclusiv regula: o țintă de deploy contribuită valorează pachetul corespunzător gratuit pe viață. `SECURITY.md` explică cum se raportează o vulnerabilitate. `CHANGELOG.md` spune ce schimbă fiecare versiune și ce îi rămâne de făcut fondatorului.

## Teste și control de publicare

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Controlul de publicare refuză chei, adrese IP, coduri interne, adrese de e-mail personale, parole în clar și termenii unei liste private (`ZELIJ_CORE_INTERDITS`) care nu face niciodată parte din depozit.

## Licență

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Poți folosi, modifica și redistribui nucleul, cu condiția să-ți publici modificările sub aceeași licență. Ediția completă care face să funcționeze zelij.ai rămâne a editorului.

by zelij.ai — https://zelij.ai/

# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · **Roman Urdu** · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Apna 100 % AI-native startup banayein.** Ek daftar jahan chaar agents aap ke liye kaam karte hain: woh tajweez dete hain, aap faisla karte hain. Aap ki machine, aap ki Claude key, aap ka data; kuch bhi bahar kisi ko report nahi karta.

![Zelij Core ka aquarium: bani (founder) aur chaar agents baat karte hain, faisle tajweez karte hain aur manzoor shuda kaam anjaam dete hain](docs/img/aquarium.gif)

*Ek simulated din ka aquarium (yahan French mein). Aap ki installation mein har card aap ke agents ka asli amal hai, live aur chaubees ghante tak replay ke qabil. Sunehra rang aap hain: aap ke faisle se pehle koi pabandi wala kaam nahi hota. Chehre farzi kirdaron ke hain.*

## Core kya karta hai

- **Daftar**: ek page. Intezar mein faisle, chief of staff ko ek darkhwast, aakhri runs apni laagat ke saath, journal, agents, installed modules.
- **Faisle ka packet**: maqsad, tajweez, abhi kyun, options, sifarish, khatraat, wapsi ki gunjaish, mansooba, rollback, asar. Adhoora packet khulta nahi. Manzoor karein, radd karein, ya tabdeeli maangein ek lazmi hidayat ke saath jo agent ko bheji jati hai.
- **Ghar ke qawaneen**: koi bhi pabandi wala kaam (paisa, awami numaish, deletion, na-qabil-e-wapsi) bina faisle ke nahi hota; har haqeeqat tareekh aur source ke saath hoti hai ya «ghair tasdeeq shuda» likhi jati hai; journal kabhi mitaya nahi jata.
- **Gateway**: bani ki Claude key, har call ki laagat istemaal aur tareekh wali awami qeematon se hisab ki jati hai, mahana had jo pahunchne par rok deti hai.
- **Executor**: mehdood call loop (har agent ke liye turn budget), kifayati tools, model ka inkaar ek nateeje ki tarah liya jata hai.
- **Modules**: core ko barhane ka wahid tareeqa. Mustahkam interface, publisher ka Ed25519 se dastakhat shuda `pack.json` manifest, har file ka hash dastakhat ke andar, installation se pehle tasdeeq. Deployment targets aur izafi agents sab isi raaste se aate hain.
- **Maaliyat**: tasdeeq shuda farokht (Stripe ka read-only import ya saboot ke saath manual entry), elaan shuda akhrajaat jo har mahine dohraye jate hain, agents ki napi gayi laagat, mahine ka journal, accountant ke liye CSV export. Kuch bhi declare ya invoice nahi hota.
- **Rabte (contacts)**: har shakhs ka ek card, lazmi qanooni buniyad, rakhne ki muddat, baat-cheet, istemaal shuda huqooq; aitraaz karne wale rabte ko kuch nahi bheja jata, muddat khatam hone wala rabta bhula diya jata hai aur sirf huqooq ka journal baqi rehta hai.
- **Ishaat (publishing)**: marketing agent ka likha page pehle draft, phir faisla banta hai; manzoori ke baad site ko GitHub pull request ya WordPress draft ke taur par tajweez hota hai. Aakhri qadam, merge ya publish, aap ka hai.
- **Jeb mein**: har faisla aap ke phone par pahunchta hai, e-mail se do dastakhat shuda single-use links ke saath, ya Telegram se teen buttons ke saath. Aap metro ki line mein manzoor karte hain; aquarium jawab milte hi harkat karta hai. Wahi darwaza, wahi journal jo desk se hai.
- **Aquarium**: apne agents ko kaam karte dekhein; har bubble pichhle 24 ghanton ka asli amal hai, dotted rings khali jagahein hain. «by zelij.ai» badge ke saath share hone wala awami page.
- **Catalogue**: jo free edition mein nahi, imaandari se naam diya gaya; publisher se khareeda module yahan dastakhat shuda aur tasdeeq shuda install hota hai. Koi adaigi daftar se nahi guzarti.
- **Software factory**: Builder sirf ek repository par parhta aur tajweez deta hai, aise pull requests ke zariye jo security gate se guzarte hain (300 lines, sirf text, koi raaz nahi, koi infrastructure file nahi, OSV ke mutabiq maloom kamzori ke baghair dependencies); SSH se Linux server par ya OVH par (domain aur DNS API se) atomic switch, smoke test aur rollback ke saath deployment; domain probe; daftar ka rozana backup. Yeh kabhi merge nahi karta, kabhi adaigi nahi karta, kabhi daftar ko haath nahi lagata.
- **Agents**: har agent ka ek folder, saada header aur French hidayaat wala `agent.md`. Chaar agents: Camille Aubert (chief of staff), Élise Tanguy (growth, marketing aur products), Nour Bellamy (maaliyat aur clients), Sacha Ferrand (builder, software factory). Bani daftar se har ek se baat karta hai; agent aur kaam batane wala manzoor shuda packet mansoobe ki hadood mein foran chalta hai.

## Ek minute mein aazmayein, bina key

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

`http://localhost:8000` kholein aur demo mein dakhil hon: ek farzi company, chaar simulated agents, manzoori ke liye faisle, un ka din replay karta aquarium. Na key, na account, na laagat; kisi model ko kuch nahi bheja jata aur band karne par sab ghayab ho jata hai. Jab yaqeen ho jaye, neeche asli installation par jayein. Daftar khud French mein hai.

## Shuru karein

```bash
cp .env.example .env     # Claude key, had, SECRET_KEY, database ka password
docker compose up -d --build
```

Daftar `http://localhost:8000` par jawab deta hai. SMTP ke baghair login link container logs mein likha jata hai (`docker compose logs core-app`).

Mukammal guides (English mein): **[Installation](docs/INSTALLATION.en.md)** (khali machine se https par daftar tak, SMTP, software factory, backups, masail ka hal), **[User guide](docs/MODE-D-EMPLOI.en.md)** (har page, agents, faisle, laagat). Bani aur agents ki tasveerein [`portraits/`](portraits/README.md) mein rakhi jati hain (wazahat French mein).

Shaya shuda image se, bina local build (version fix karne ke liye `.env` mein `CORE_IMAGE_TAG=v…`):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Docker ke baghair local:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Publisher ki public key

Catalogue ke modules zelij.ai ke dastakhat shuda hain. `ZELIJ_CLE_PUBLIQUE` mein rakhi jane wali public key (`.env.example` mein pehle se maujood):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Security

Jo core zamanat deta hai aur jo test hota hai (`tests/test_securite.py`):

- **Modules**: module sirf publisher ke dastakhat (Ed25519) ke saath install aur chalta hai, aur dastakhat har code file ke SHA-256 hash ko cover karta hai: dastakhat ke baad badli, shamil ya hataee gayi file module ko na-qabil-e-istemaal bana deti hai.
- **Login**: 20 minute ke single-use links, database mein hashed; link ki darkhwaston par har address, har IP aur majmooi breaks, taake daftar kabhi e-mail relay na bane; production mein SMTP set na ho to koi link na banta hai na log hota hai.
- **Forms**: HMAC session cookie `HttpOnly` `SameSite=Strict`, har POST par origin check aur har session ka anti-CSRF token.
- **Pages**: sakht content security policy (`default-src 'self'`, koi inline script nahi, koi frame nahi), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, origin https ho to HSTS.
- **Agents**: agent jo bhi parhta hai (web page, repository file) use bahar ke mawad ke taur par frame kar ke milta hai, kabhi hidayat ke taur par nahi; agent sirf apne card ke tools chalata hai aur nijee data parhne ke baad sirf company ki apni site call kar sakta hai; sirf awami https addresses parhta hai (private, loopback, link-local addresses aur andaruni naam har redirect par radd, jawab ki had muqarrar); security gate raaz, infrastructure files, third-party scripts, frames aur network calls rokta hai.
- **Container**: ghair-mumtaz user, read-only file system, koi capability nahi, koi privilege escalation nahi; SSH server ki host key fix ki ja sakti hai (`SSH_CLE_HOTE`).
- **Accounting export**: spreadsheet formula jaise dikhne wale cells be-asar kar diye jate hain.

Kamzori ki ittila `securite@zelij.ai` par dein, theek hone se pehle shaya kiye baghair. Har release se pehle `pip-audit -r requirements.txt` aur `bandit -r core scripts -ll` khali aane chahiye.

## Hissa lena aur versions

`CONTRIBUTING.md` (French mein) batata hai ke koi contribution release mein kaise pahunchti hai, is qaide samet: diya gaya deployment target mutabiq pack zindagi bhar muft deta hai. `SECURITY.md` batata hai kamzori kaise report karein. `CHANGELOG.md` batata hai har version kya badalta hai aur bani ke liye kya baqi hai.

## Tests aur ishaat ka control

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Ishaat ka control keys, IP addresses, andaruni codes, zaati e-mail addresses, saaf text passwords aur ek nijee fehrist (`ZELIJ_CORE_INTERDITS`) ke alfaz radd karta hai jo kabhi repository ka hissa nahi hoti.

## License

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Aap core ko istemaal, tabdeel aur dobara taqseem kar sakte hain, is shart par ke apni tabdeelian isi license ke tehat shaya karein. zelij.ai ko chalane wala mukammal edition publisher ka rehta hai.

by zelij.ai — https://zelij.ai/

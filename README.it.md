# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · **Italiano** · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Costruisci la tua startup al 100 % nativa in IA.** Un ufficio dove quattro agenti lavorano per te: loro propongono, tu decidi. La tua macchina, la tua chiave Claude, i tuoi dati; niente telefona a casa.

![L'acquario di Zelij Core: il fondatore e quattro agenti dialogano, propongono decisioni ed eseguono ciò che è stato approvato](docs/img/aquarium.gif)

*L'acquario in una giornata simulata (qui in francese). Nella tua installazione, ogni scheda è un'azione reale dei tuoi agenti, in diretta e riproducibile su ventiquattro ore. L'oro sei tu: niente di vincolante accade prima della tua decisione. I volti sono di personaggi di fantasia.*

## Cosa fa il nucleo

- **L'ufficio**: una pagina. Le decisioni in attesa, una richiesta al capo di gabinetto, le ultime esecuzioni con il loro costo, il diario, gli agenti, i moduli installati.
- **Il pacchetto di decisione**: obiettivo, proposta, perché adesso, opzioni, raccomandazione, rischi, reversibilità, piano, ritorno indietro, impatto. Un pacchetto incompleto non si apre. Approvare, rifiutare o chiedere modifiche con un'indicazione obbligatoria trasmessa all'agente.
- **Le regole della casa**: niente di vincolante (denaro, esposizione pubblica, cancellazione, irreversibile) si fa senza decisione; un fatto è datato e con fonte oppure segnato «non verificato»; il diario non si cancella.
- **Il gateway**: la chiave Claude del fondatore, il costo di ogni chiamata calcolato dall'uso e dai prezzi pubblici datati, un tetto mensile che blocca.
- **L'esecutore**: un ciclo di chiamate limitato (budget di turni per agente), strumenti sobri, un rifiuto del modello trattato come un risultato.
- **I moduli**: l'unico modo per estendere il nucleo. Interfaccia stabile, manifesto `pack.json` firmato Ed25519 dall'editore, impronta di ogni file coperta dalla firma, verifica prima dell'installazione. Le destinazioni di deploy e gli agenti aggiuntivi passano di qui.
- **Finanze**: vendite confermate (import Stripe in sola lettura o inserimento con prova), spese dichiarate che tornano ogni mese, costo degli agenti misurato, diario del mese, export CSV per il commercialista. Niente viene dichiarato né fatturato.
- **Contatti**: una scheda per persona, base giuridica obbligatoria, durata di conservazione, scambi, diritti esercitati; un contatto che si oppone non riceve più nulla, un contatto scaduto viene dimenticato e resta solo il diario dei diritti.
- **Pubblicazione**: una pagina scritta dall'agente marketing diventa una bozza, poi una decisione; approvata, viene proposta al sito come pull request GitHub o bozza WordPress. L'ultimo gesto, unire o pubblicare, è tuo.
- **In tasca**: ogni decisione arriva sul tuo telefono, via e-mail con due link firmati monouso, o via Telegram con tre pulsanti. Approvi dalla fila della metro; l'acquario si muove appena rispondi. Stessa porta, stesso diario della scrivania.
- **Acquario**: guarda i tuoi agenti lavorare; ogni bolla è un'azione reale delle ultime 24 ore, gli anelli tratteggiati sono posti liberi. Una pagina pubblica condivisibile, con il badge «by zelij.ai».
- **Catalogo**: ciò che l'edizione libera non contiene, nominato onestamente; un modulo acquistato dall'editore si installa qui, firmato e verificato. Nessun pagamento passa dall'ufficio.
- **Software factory**: il Costruttore legge e propone su un solo repository, tramite pull request che passano la porta di sicurezza (300 righe, solo testo, nessun segreto, nessun file di infrastruttura, dipendenze senza vulnerabilità note via OSV); messa in linea su un server Linux via SSH o su OVH (dominio e DNS via API) con commutazione atomica, smoke test e ritorno indietro; sonda del dominio; backup quotidiano dell'ufficio. Non unisce mai, non paga mai, non tocca mai l'ufficio.
- **Gli agenti**: una cartella per agente, un `agent.md` con un'intestazione semplice e indicazioni in francese. Quattro agenti: Camille Aubert (capo di gabinetto), Élise Tanguy (crescita, marketing e prodotti), Nour Bellamy (finanze e clienti), Sacha Ferrand (costruttore, software factory). Il fondatore si rivolge a ciascuno dall'ufficio; un pacchetto approvato che indica un agente e un compito viene eseguito subito, nei limiti del piano.

## Provare in un minuto, senza chiave

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Apri `http://localhost:8000` ed entra nella dimostrazione: un'azienda immaginaria, quattro agenti simulati, decisioni da approvare, l'acquario che riproduce la loro giornata. Nessuna chiave, nessun account, nessun costo; niente viene inviato a un modello e tutto sparisce all'arresto. Quando sei convinto, passa all'installazione reale qui sotto. L'ufficio in sé è in francese.

## Avviare

```bash
cp .env.example .env     # chiave Claude, tetto, SECRET_KEY, password del database
docker compose up -d --build
```

L'ufficio risponde su `http://localhost:8000`. Senza SMTP, il link di accesso viene scritto nei log del container (`docker compose logs core-app`).

Guide complete (in inglese): **[Installazione](docs/INSTALLATION.en.md)** (macchina vuota → ufficio in https, SMTP, software factory, backup, risoluzione dei problemi), **[Manuale d'uso](docs/MODE-D-EMPLOI.en.md)** (ogni pagina, gli agenti, le decisioni, il costo). Le foto del fondatore e degli agenti vanno in [`portraits/`](portraits/README.md) (descrizione in francese).

Dall'immagine pubblicata, senza build locale (`CORE_IMAGE_TAG=v…` in `.env` fissa la versione):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

In locale senza Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Chiave pubblica dell'editore

I moduli del catalogo sono firmati da zelij.ai. La chiave pubblica da mettere in `ZELIJ_CLE_PUBLIQUE` (già inserita in `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Sicurezza

Ciò che il nucleo garantisce, e che è testato (`tests/test_securite.py`):

- **Moduli**: un modulo si installa e si esegue solo se firmato dall'editore (Ed25519), e la firma copre l'impronta SHA-256 di ogni file di codice: un file modificato, aggiunto o rimosso dopo la firma mette il modulo fuori gioco.
- **Accesso**: link monouso di 20 minuti, con hash nel database; freni per indirizzo, per IP e globali sulle richieste di link, perché l'ufficio non serva mai da relay di posta; senza SMTP configurato in produzione, nessun link viene creato né registrato.
- **Moduli web**: cookie di sessione HMAC `HttpOnly` `SameSite=Strict`, controllo dell'origine e token anti-CSRF per sessione su ogni POST.
- **Pagine**: content security policy rigorosa (`default-src 'self'`, nessuno script inline, nessun frame), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS quando l'origine è https.
- **Agenti**: ciò che un agente legge (pagina web, file del repository) gli arriva incorniciato come contenuto esterno, mai come indicazione; un agente esegue solo gli strumenti della sua scheda e, appena ha letto un dato privato, può chiamare solo il sito dell'azienda; legge solo indirizzi https pubblici (indirizzi privati, di loopback, link-local e nomi interni rifiutati a ogni salto di reindirizzamento, risposta limitata); la porta di sicurezza blocca segreti, file di infrastruttura, script di terzi, frame e chiamate di rete.
- **Container**: utente senza privilegi, file system in sola lettura, nessuna capability, nessuna elevazione; la chiave host del server SSH può essere fissata (`SSH_CLE_HOTE`).
- **Export contabile**: le celle che sembrano una formula di foglio di calcolo vengono neutralizzate.

Segnalare una vulnerabilità: `securite@zelij.ai`, senza pubblicarla prima della correzione. Prima di ogni versione, `pip-audit -r requirements.txt` e `bandit -r core scripts -ll` devono essere vuoti.

## Contribuire e seguire le versioni

`CONTRIBUTING.md` (in francese) spiega come un contributo entra in una versione, compresa la regola: una destinazione di deploy contribuita vale il pack corrispondente gratis a vita. `SECURITY.md` spiega come segnalare una vulnerabilità. `CHANGELOG.md` dice cosa cambia ogni versione e cosa resta da fare al fondatore.

## Test e controllo di pubblicazione

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Il controllo di pubblicazione rifiuta chiavi, indirizzi IP, codici interni, indirizzi e-mail personali, password in chiaro e i termini di una lista privata (`ZELIJ_CORE_INTERDITS`) che non fa mai parte del repository.

## Licenza

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Puoi usare, modificare e ridistribuire il nucleo, a condizione di pubblicare le tue modifiche sotto la stessa licenza. L'edizione completa che fa funzionare zelij.ai resta quella dell'editore.

by zelij.ai — https://zelij.ai/

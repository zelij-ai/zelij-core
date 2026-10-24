# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · **Deutsch** · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Bauen Sie Ihr zu 100 % KI-natives Start-up.** Ein Büro, in dem vier Agenten für Sie arbeiten: Sie schlagen vor, Sie entscheiden. Ihr Rechner, Ihr Claude-Schlüssel, Ihre Daten; nichts telefoniert nach Hause.

![Das Aquarium von Zelij Core: der Gründer und vier Agenten tauschen sich aus, schlagen Entscheidungen vor und führen aus, was genehmigt wurde](docs/img/aquarium.gif)

*Das Aquarium an einem simulierten Tag (hier auf Französisch). In Ihrer Installation ist jede Karte eine echte Handlung Ihrer Agenten, live und über vierundzwanzig Stunden abspielbar. Gold sind Sie: Nichts Verbindliches geschieht vor Ihrer Entscheidung. Die Gesichter gehören fiktiven Figuren.*

## Was der Kern leistet

- **Das Büro**: eine Seite. Die wartenden Entscheidungen, eine Anfrage an den Kabinettschef, die letzten Läufe mit ihren Kosten, das Journal, die Agenten, die installierten Module.
- **Das Entscheidungspaket**: Ziel, Vorschlag, warum jetzt, Optionen, Empfehlung, Risiken, Umkehrbarkeit, Plan, Rücknahme, Wirkung. Ein unvollständiges Paket öffnet sich nicht. Genehmigen, ablehnen oder Änderungen verlangen, mit einer verpflichtenden Anweisung, die an den Agenten weitergegeben wird.
- **Die Hausregeln**: Nichts Verbindliches (Geld, Öffentlichkeit, Löschung, Unumkehrbares) geschieht ohne Entscheidung; ein Fakt ist datiert und belegt oder als „nicht geprüft“ markiert; das Journal wird nie gelöscht.
- **Das Gateway**: der Claude-Schlüssel des Gründers, die Kosten jedes Aufrufs aus Verbrauch und datierten öffentlichen Preisen berechnet, eine monatliche Obergrenze, die blockiert.
- **Der Ausführer**: eine begrenzte Aufrufschleife (Zugbudget pro Agent), sparsame Werkzeuge, eine Verweigerung des Modells wird als Ergebnis behandelt.
- **Die Module**: der einzige Weg, den Kern zu erweitern. Stabile Schnittstelle, `pack.json`-Manifest vom Herausgeber mit Ed25519 signiert, der Hash jeder Datei durch die Signatur abgedeckt, Prüfung vor der Installation. Deployment-Ziele und zusätzliche Agenten kommen nur auf diesem Weg.
- **Finanzen**: bestätigte Verkäufe (Stripe-Import nur lesend oder Erfassung mit Beleg), gemeldete monatlich wiederkehrende Ausgaben, gemessene Agentenkosten, Monatsjournal, CSV-Export für den Steuerberater. Nichts wird gemeldet oder in Rechnung gestellt.
- **Kontakte**: eine Karte pro Person, verpflichtende Rechtsgrundlage, Aufbewahrungsdauer, Austausch, ausgeübte Rechte; ein widersprechender Kontakt erhält nichts mehr, ein abgelaufener Kontakt wird vergessen, nur das Rechtejournal bleibt.
- **Veröffentlichung**: eine vom Marketing-Agenten verfasste Seite wird zum Entwurf, dann zur Entscheidung; genehmigt, wird sie der Website als GitHub-Pull-Request oder WordPress-Entwurf vorgeschlagen. Der letzte Schritt, Mergen oder Veröffentlichen, gehört Ihnen.
- **In der Tasche**: jede Entscheidung erreicht Ihr Telefon, per E-Mail mit zwei signierten Einmal-Links oder per Telegram mit drei Knöpfen. Sie genehmigen in der U-Bahn-Schlange; das Aquarium bewegt sich, sobald Sie antworten. Dieselbe Tür, dasselbe Journal wie vom Schreibtisch.
- **Aquarium**: Sehen Sie Ihren Agenten bei der Arbeit zu; jede Blase ist eine echte Handlung der letzten 24 Stunden, die gepunkteten Ringe sind offene Stellen. Eine teilbare öffentliche Seite mit dem Abzeichen „by zelij.ai“.
- **Katalog**: Was die freie Ausgabe nicht enthält, ehrlich benannt; ein beim Herausgeber gekauftes Modul wird hier installiert, signiert und geprüft. Keine Zahlung läuft über das Büro.
- **Software factory**: der Baumeister liest und schlägt in einem einzigen Repository vor, über Pull-Requests, die das Sicherheitstor passieren (300 Zeilen, nur Text, keine Geheimnisse, keine Infrastrukturdateien, Abhängigkeiten ohne bekannte Schwachstelle laut OSV); Deployment auf einen Linux-Server per SSH oder zu OVH (Domain und DNS über die API) mit atomarem Umschalten, Rauchtest und Rücknahme; Domain-Sonde; tägliche Sicherung des Büros. Er merged nie, zahlt nie, rührt das Büro nie an.
- **Die Agenten**: ein Ordner pro Agent, eine `agent.md` mit einfachem Kopf und Anweisungen auf Französisch. Vier Agenten: Camille Aubert (Kabinettschefin), Élise Tanguy (Wachstum, Marketing und Produkte), Nour Bellamy (Finanzen und Kunden), Sacha Ferrand (Baumeister, Software factory). Der Gründer spricht jeden vom Büro aus an; ein genehmigtes Paket, das einen Agenten und eine Aufgabe nennt, wird sofort ausgeführt, in den Grenzen des Plans.

## In einer Minute ausprobieren, ohne Schlüssel

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Öffnen Sie `http://localhost:8000` und betreten Sie die Demonstration: eine fiktive Firma, vier simulierte Agenten, Entscheidungen zum Genehmigen, das Aquarium, das ihren Tag abspielt. Kein Schlüssel, kein Konto, keine Kosten; nichts wird an ein Modell gesendet, und alles verschwindet beim Stoppen. Wenn Sie überzeugt sind, gehen Sie zur echten Installation unten über. Das Büro selbst ist auf Französisch.

## Starten

```bash
cp .env.example .env     # Claude-Schlüssel, Obergrenze, SECRET_KEY, Datenbankpasswort
docker compose up -d --build
```

Das Büro antwortet auf `http://localhost:8000`. Ohne SMTP wird der Anmeldelink in die Container-Logs geschrieben (`docker compose logs core-app`).

Vollständige Anleitungen (auf Englisch): **[Installation](docs/INSTALLATION.en.md)** (leerer Rechner → Büro über https, SMTP, Software factory, Sicherungen, Fehlerbehebung), **[Benutzerhandbuch](docs/MODE-D-EMPLOI.en.md)** (jede Seite, die Agenten, die Entscheidungen, die Kosten). Fotos von Gründer und Agenten kommen nach [`portraits/`](portraits/README.md) (Beschreibung auf Französisch).

Aus dem veröffentlichten Image, ohne lokalen Build (`CORE_IMAGE_TAG=v…` in `.env` fixiert die Version):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Lokal ohne Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Öffentlicher Schlüssel des Herausgebers

Die Module des Katalogs sind von zelij.ai signiert. Der öffentliche Schlüssel für `ZELIJ_CLE_PUBLIQUE` (in `.env.example` bereits eingetragen):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Sicherheit

Was der Kern garantiert und was getestet wird (`tests/test_securite.py`):

- **Module**: Ein Modul wird nur installiert und ausgeführt, wenn es vom Herausgeber signiert ist (Ed25519), und die Signatur deckt den SHA-256-Hash jeder Codedatei ab: Eine nach der Signatur geänderte, hinzugefügte oder entfernte Datei setzt das Modul außer Kraft.
- **Anmeldung**: Einmal-Links mit 20 Minuten Gültigkeit, gehasht in der Datenbank; Bremsen pro Adresse, pro IP und global bei Linkanfragen, damit das Büro nie als E-Mail-Relay dient; ohne konfiguriertes SMTP in Produktion wird kein Link erzeugt oder protokolliert.
- **Formulare**: HMAC-Sitzungscookie `HttpOnly` `SameSite=Strict`, Origin-Prüfung und Anti-CSRF-Token pro Sitzung bei jedem POST.
- **Seiten**: strenge Content Security Policy (`default-src 'self'`, kein Inline-Skript, keine Frames), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS bei https-Origin.
- **Agenten**: Was ein Agent liest (Webseite, Repository-Datei), erreicht ihn als gerahmter externer Inhalt, nie als Anweisung; ein Agent führt nur die Werkzeuge seiner Karte aus und darf, sobald er private Daten gelesen hat, nur noch die Website des Unternehmens aufrufen; er liest nur öffentliche https-Adressen (private, Loopback- und Link-Local-Adressen sowie interne Namen werden bei jedem Redirect-Sprung abgelehnt, Antwort begrenzt); das Sicherheitstor blockiert Geheimnisse, Infrastrukturdateien, Drittskripte, Frames und Netzwerkaufrufe.
- **Container**: unprivilegierter Benutzer, schreibgeschütztes Dateisystem, keine Capabilities, keine Rechteausweitung; der Host-Schlüssel des SSH-Servers kann festgelegt werden (`SSH_CLE_HOTE`).
- **Buchhaltungsexport**: Zellen, die wie eine Tabellenformel aussehen, werden neutralisiert.

Eine Schwachstelle melden: `securite@zelij.ai`, ohne sie vor der Behebung zu veröffentlichen. Vor jeder Version müssen `pip-audit -r requirements.txt` und `bandit -r core scripts -ll` leer bleiben.

## Beitragen und Versionen verfolgen

`CONTRIBUTING.md` (auf Französisch) erklärt, wie ein Beitrag in eine Version gelangt, einschließlich der Regel: Ein beigetragenes Deployment-Ziel bringt das entsprechende Paket lebenslang kostenlos. `SECURITY.md` erklärt, wie eine Schwachstelle gemeldet wird. `CHANGELOG.md` sagt, was jede Version ändert und was dem Gründer noch zu tun bleibt.

## Tests und Veröffentlichungskontrolle

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Die Veröffentlichungskontrolle weist Schlüssel, IP-Adressen, interne Codes, persönliche E-Mail-Adressen, Klartextpasswörter und die Begriffe einer privaten Liste (`ZELIJ_CORE_INTERDITS`) zurück, die nie Teil des Repositorys ist.

## Lizenz

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Sie dürfen den Kern nutzen, verändern und weitergeben, sofern Sie Ihre Änderungen unter derselben Lizenz veröffentlichen. Die vollständige Ausgabe, die zelij.ai betreibt, bleibt die des Herausgebers.

by zelij.ai — https://zelij.ai/

# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · **Polski** · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Zbuduj swój startup w 100 % natywny dla AI.** Jedno biuro, w którym czterech agentów pracuje dla Ciebie: oni proponują, Ty decydujesz. Twoja maszyna, Twój klucz Claude, Twoje dane; nic nie „dzwoni do domu”.

![Akwarium Zelij Core: założyciel i czterech agentów rozmawiają, proponują decyzje i wykonują to, co zatwierdzono](docs/img/aquarium.gif)

*Akwarium w symulowanym dniu (tutaj po francusku). W Twojej instalacji każda karta to prawdziwe działanie Twoich agentów, na żywo i z odtwarzaniem z dwudziestu czterech godzin. Złoto to Ty: nic wiążącego nie dzieje się przed Twoją decyzją. Twarze należą do postaci fikcyjnych.*

## Co robi rdzeń

- **Biuro**: jedna strona. Oczekujące decyzje, prośba do szefa gabinetu, ostatnie uruchomienia z ich kosztem, dziennik, agenci, zainstalowane moduły.
- **Pakiet decyzji**: cel, propozycja, dlaczego teraz, opcje, rekomendacja, ryzyka, odwracalność, plan, wycofanie, wpływ. Niekompletny pakiet się nie otwiera. Zatwierdź, odrzuć lub poproś o zmiany z obowiązkową instrukcją przekazywaną agentowi.
- **Zasady domu**: nic wiążącego (pieniądze, publiczna ekspozycja, usunięcie, nieodwracalne) nie dzieje się bez decyzji; fakt ma datę i źródło albo jest oznaczony „niezweryfikowane”; dziennik nigdy nie jest kasowany.
- **Brama**: klucz Claude założyciela, koszt każdego wywołania obliczony z użycia i datowanych cen publicznych, miesięczny limit, który blokuje.
- **Wykonawca**: ograniczona pętla wywołań (budżet tur na agenta), oszczędne narzędzia, odmowa modelu traktowana jako wynik.
- **Moduły**: jedyny sposób rozszerzenia rdzenia. Stabilny interfejs, manifest `pack.json` podpisany przez wydawcę kluczem Ed25519, skrót każdego pliku objęty podpisem, weryfikacja przed instalacją. Cele wdrożenia i dodatkowi agenci przychodzą tylko tą drogą.
- **Finanse**: potwierdzona sprzedaż (import Stripe tylko do odczytu albo wpis ręczny z dowodem), zadeklarowane wydatki powtarzające się co miesiąc, zmierzony koszt agentów, dziennik miesiąca, eksport CSV dla księgowego. Nic nie jest deklarowane ani fakturowane.
- **Kontakty**: jedna karta na osobę, obowiązkowa podstawa prawna, okres przechowywania, wymiana, wykonane prawa; kontakt, który wniósł sprzeciw, nie otrzymuje już niczego, kontakt wygasły jest zapominany i pozostaje tylko dziennik praw.
- **Publikacja**: strona napisana przez agenta marketingu staje się szkicem, potem decyzją; zatwierdzona, jest proponowana witrynie jako pull request na GitHubie albo szkic WordPressa. Ostatni ruch, scalenie lub publikacja, należy do Ciebie.
- **W kieszeni**: każda decyzja trafia na Twój telefon, e-mailem z dwoma podpisanymi jednorazowymi linkami albo przez Telegram z trzema przyciskami. Zatwierdzasz w kolejce do metra; akwarium rusza, gdy tylko odpowiesz. Te same drzwi, ten sam dziennik co z biurka.
- **Akwarium**: patrz, jak pracują Twoi agenci; każdy bąbelek to prawdziwe działanie z ostatnich 24 godzin, kropkowane pierścienie to wolne stanowiska. Publiczna strona do udostępniania, z odznaką „by zelij.ai”.
- **Katalog**: to, czego nie zawiera wolna edycja, nazwane uczciwie; moduł kupiony u wydawcy instaluje się tutaj, podpisany i zweryfikowany. Żadna płatność nie przechodzi przez biuro.
- **Software factory**: Budowniczy czyta i proponuje w jednym repozytorium, przez pull requesty przechodzące bramę bezpieczeństwa (300 linii, tylko tekst, żadnych sekretów, żadnych plików infrastruktury, zależności bez znanych podatności według OSV); wdrożenie na serwer Linux przez SSH albo do OVH (domena i DNS przez API) z atomowym przełączeniem, testem dymnym i wycofaniem; sonda domeny; codzienna kopia zapasowa biura. Nigdy nie scala, nigdy nie płaci, nigdy nie dotyka biura.
- **Agenci**: jeden folder na agenta, plik `agent.md` z prostym nagłówkiem i instrukcjami po francusku. Czterech agentów: Camille Aubert (szefowa gabinetu), Élise Tanguy (wzrost, marketing i produkty), Nour Bellamy (finanse i klienci), Sacha Ferrand (budowniczy, software factory). Założyciel zwraca się do każdego z biura; zatwierdzony pakiet wskazujący agenta i zadanie wykonuje się natychmiast, w granicach planu.

## Wypróbuj w minutę, bez klucza

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Otwórz `http://localhost:8000` i wejdź do demonstracji: fikcyjna firma, czterech symulowanych agentów, decyzje do zatwierdzenia, akwarium odtwarzające ich dzień. Bez klucza, bez konta, bez kosztów; nic nie jest wysyłane do modelu i wszystko znika po zatrzymaniu. Gdy będziesz przekonany, przejdź do prawdziwej instalacji poniżej. Samo biuro jest po francusku.

## Uruchomienie

```bash
cp .env.example .env     # klucz Claude, limit, SECRET_KEY, hasło bazy danych
docker compose up -d --build
```

Biuro odpowiada pod `http://localhost:8000`. Bez SMTP link logowania zapisywany jest w logach kontenera (`docker compose logs core-app`).

Pełne przewodniki (po angielsku): **[Instalacja](docs/INSTALLATION.en.md)** (pusta maszyna → biuro po https, SMTP, software factory, kopie zapasowe, rozwiązywanie problemów), **[Instrukcja użytkowania](docs/MODE-D-EMPLOI.en.md)** (każda strona, agenci, decyzje, koszt). Zdjęcia założyciela i agentów trafiają do [`portraits/`](portraits/README.md) (opis po francusku).

Z opublikowanego obrazu, bez lokalnego budowania (`CORE_IMAGE_TAG=v…` w `.env` przypina wersję):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Lokalnie bez Dockera:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Klucz publiczny wydawcy

Moduły katalogu są podpisane przez zelij.ai. Klucz publiczny do ustawienia w `ZELIJ_CLE_PUBLIQUE` (już wpisany w `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Bezpieczeństwo

Co rdzeń gwarantuje i co jest testowane (`tests/test_securite.py`):

- **Moduły**: moduł instaluje się i uruchamia tylko podpisany przez wydawcę (Ed25519), a podpis obejmuje skrót SHA-256 każdego pliku kodu: plik zmieniony, dodany lub usunięty po podpisaniu wyłącza moduł z gry.
- **Logowanie**: jednorazowe linki ważne 20 minut, zapisane w bazie jako skróty; hamulce na adres, na IP i globalne dla żądań linków, aby biuro nigdy nie stało się przekaźnikiem poczty; bez skonfigurowanego SMTP w produkcji żaden link nie jest tworzony ani logowany.
- **Formularze**: ciasteczko sesji HMAC `HttpOnly` `SameSite=Strict`, kontrola pochodzenia i token anty-CSRF na sesję przy każdym POST.
- **Strony**: ścisła polityka bezpieczeństwa treści (`default-src 'self'`, żadnych skryptów inline, żadnych ramek), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS, gdy pochodzenie jest https.
- **Agenci**: to, co agent czyta (strona WWW, plik repozytorium), dociera do niego obramowane jako treść zewnętrzna, nigdy jako instrukcja; agent uruchamia tylko narzędzia ze swojej karty i, gdy tylko odczyta dane prywatne, może wywoływać wyłącznie witrynę firmy; czyta tylko publiczne adresy https (adresy prywatne, pętli zwrotnej, link-local i nazwy wewnętrzne odrzucane przy każdym skoku przekierowania, odpowiedź ograniczona); brama bezpieczeństwa blokuje sekrety, pliki infrastruktury, skrypty zewnętrzne, ramki i wywołania sieciowe.
- **Kontener**: użytkownik bez uprawnień, system plików tylko do odczytu, żadnych capabilities, bez podnoszenia uprawnień; klucz hosta serwera SSH można przypiąć (`SSH_CLE_HOTE`).
- **Eksport księgowy**: komórki wyglądające jak formuła arkusza są neutralizowane.

Zgłoś podatność na `securite@zelij.ai`, nie publikując jej przed poprawką. Przed każdą wersją `pip-audit -r requirements.txt` i `bandit -r core scripts -ll` muszą zwracać pusty wynik.

## Współtworzenie i wersje

`CONTRIBUTING.md` (po francusku) wyjaśnia, jak wkład trafia do wersji, w tym zasadę: wniesiony cel wdrożenia daje odpowiadający mu pakiet za darmo dożywotnio. `SECURITY.md` wyjaśnia, jak zgłosić podatność. `CHANGELOG.md` mówi, co zmienia każda wersja i co pozostaje do zrobienia założycielowi.

## Testy i kontrola publikacji

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Kontrola publikacji odrzuca klucze, adresy IP, kody wewnętrzne, prywatne adresy e-mail, hasła jawnym tekstem oraz terminy z prywatnej listy (`ZELIJ_CORE_INTERDITS`), która nigdy nie jest częścią repozytorium.

## Licencja

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Możesz używać, modyfikować i rozpowszechniać rdzeń pod warunkiem publikacji swoich zmian na tej samej licencji. Pełna edycja napędzająca zelij.ai pozostaje własnością wydawcy.

by zelij.ai — https://zelij.ai/

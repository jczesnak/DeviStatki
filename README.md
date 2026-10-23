# Kreślarnia Morska

Strona internetowa twórcy materiałów o tematyce morskiej: gazet, filmów, artykułów i rysunków statków.
Zbudowana na **Django + Wagtail (CMS)**. Autor dodaje nowe wydania w panelu administracyjnym, bez programowania.

Na stronie są trzy zakładki:

- **Strona główna** – najnowsze wydanie jako główny materiał oraz 3 poprzednie wydania,
- **Wydania** – lista wszystkich wydań z filtrem po typie (gazeta / film / artykuł / rysunek) i stronicowaniem,
- **O nas** – opis twórcy.

## Technologie

| Co | Wersja |
|---|---|
| Python | 3.12 lub nowszy |
| Django | 6.0 |
| Wagtail | 7.4 |
| Baza danych | SQLite (plik `db.sqlite3`, tworzony automatycznie) |

## Uruchomienie lokalne

Wszystkie polecenia wykonujemy w folderze projektu (tam, gdzie jest `manage.py`).

### 1. Środowisko wirtualne i zależności

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Jeśli PowerShell zablokuje skrypt `Activate.ps1`, wykonaj raz:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Baza danych

```bash
python manage.py migrate
```

Tworzy plik `db.sqlite3` ze stroną główną i nazwą serwisu.

### 3. Przykładowe treści (opcjonalnie)

```bash
python manage.py zaladuj_przyklady
```

Dodaje zakładki „Wydania” i „O nas” oraz 6 przykładowych wydań z rysunkami statków.
Polecenie można uruchomić wielokrotnie – jeśli dane już są, nic nie zmienia.

### 4. Konto administratora

```bash
python manage.py createsuperuser
```

Podaj login, e-mail (może być pusty) i hasło.

### 5. Start serwera

```bash
python manage.py runserver
```

- strona: <http://127.0.0.1:8000/>
- panel administracyjny: <http://127.0.0.1:8000/admin/>

Przy kolejnych uruchomieniach wystarczy aktywować środowisko (krok 1, druga linijka) i wykonać `python manage.py runserver`.

## Jak dodać nowe wydanie

1. Zaloguj się w panelu `/admin/`.
2. **Strony → Strona główna → Wydania → Dodaj stronę podrzędną → Wydanie**.
3. Uzupełnij tytuł, typ, datę, okładkę i opis. Opcjonalnie podaj link (np. do filmu lub sklepu).
4. Kliknij **Opublikuj**. Wydanie z najnowszą datą automatycznie pojawi się na stronie głównej.

## Testy

```bash
python manage.py test home
```

Testy sprawdzają m.in. wybór aktualnego wydania, ukrywanie szkiców, filtr i stronicowanie listy wydań
oraz to, że polecenie `zaladuj_przyklady` można bezpiecznie uruchomić dwa razy.

## Struktura projektu

```
manage.py
requirements.txt
kreslarnia/                  ustawienia projektu
├── settings/
│   ├── base.py              wspólne ustawienia
│   ├── dev.py               lokalnie (domyślne, DEBUG=True)
│   └── production.py        serwer (DEBUG=False, sekrety ze zmiennych środowiskowych)
├── templates/               base.html (menu, stopka), 404.html, 500.html
└── static/css/              arkusz stylów
home/                        aplikacja z typami stron
├── models.py                HomePage, IssueIndexPage (Wydania), IssuePage (wydanie), AboutPage (O nas)
├── templates/home/          szablony poszczególnych stron
├── management/commands/     polecenie zaladuj_przyklady
├── przyklady/               rysunki do przykładowych treści
└── tests.py
```

## Docker (opcjonalnie)

Obraz używa ustawień produkcyjnych, więc wymaga zmiennej `SECRET_KEY`:

```bash
docker build -t kreslarnia .
docker run -p 8000:8000 -e SECRET_KEY=wpisz-dlugi-losowy-klucz -e ALLOWED_HOSTS=localhost kreslarnia
```

> Uwaga: przy `DEBUG=False` serwer gunicorn nie udostępnia plików statycznych (CSS) ani wgranych obrazów.
> Do prawdziwego wdrożenia potrzebny jest np. WhiteNoise albo serwer nginx.

## Źródła ilustracji

Przykładowe rysunki w `home/przyklady/` pochodzą z Wikimedia Commons i są w domenie publicznej
(zbiory NARA, HAER / Library of Congress, Royal Museums Greenwich, U.S. Coast Guard).

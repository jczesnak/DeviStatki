from datetime import date
from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images.models import Image

from home.models import AboutPage, HomePage, IssueIndexPage, IssuePage

# Folder z przykładowymi rysunkami (domena publiczna, Wikimedia Commons)
FOLDER = Path(__file__).resolve().parents[2] / "przyklady"

# Przykładowe wydania – słowniki z nazwanymi polami, żeby nie pomylić kolejności
WYDANIA = [
    {
        "tytul": "Szkuner C.A. Thayer – widok burtowy",
        "typ": "rysunek", "numer": "6", "data": date(2026, 10, 14), "plik": "thayer.png",
        "zajawka": "Trzymasztowy szkuner drewniany z 1895 roku rozrysowany linia po linii.",
        "zrodlo": "HAER, Library of Congress",
    },
    {
        "tytul": "Gazeta Morska nr 12 – Kutry parowe",
        "typ": "gazeta", "numer": "12", "data": date(2026, 9, 30), "plik": "tallapoosa.jpg",
        "zajawka": "W numerze: kuter parowy z USS Tallapoosa, przekroje i wymiary z 1886 roku.",
        "zrodlo": "NARA",
    },
    {
        "tytul": "Film: Jak czytać plan ożaglowania",
        "typ": "film", "numer": "4", "data": date(2026, 9, 2), "plik": "ozaglowanie.jpg",
        "zajawka": "Krok po kroku: maszty, reje i liny na planie żaglowca z 1913 roku.",
        "zrodlo": "Illustreret norsk konversationsleksikon, 1913",
    },
    {
        "tytul": "Fregata HMS Rosario (1800)",
        "typ": "artykul", "numer": "21", "data": date(2026, 7, 18), "plik": "rosario.jpg",
        "zajawka": "Historia brytyjskiej fregaty i analiza jej oryginalnego planu.",
        "zrodlo": "Royal Museums Greenwich",
    },
    {
        "tytul": "Gazeta Morska nr 11 – Statki służb przybrzeżnych",
        "typ": "gazeta", "numer": "11", "data": date(2026, 6, 25), "plik": "red_beech.png",
        "zajawka": "Statki obsługi oznakowania nawigacyjnego – od kadłuba po dźwig.",
        "zrodlo": "U.S. Coast Guard",
    },
    {
        "tytul": "Linie teoretyczne kadłuba – Mary Taylor",
        "typ": "rysunek", "numer": "5", "data": date(2026, 5, 9), "plik": "mary_taylor.jpg",
        "zajawka": "Plan linii teoretycznych szkunera pilotowego wzorowanego na jachcie America.",
        "zrodlo": "Royal Museums Greenwich",
    },
]

# Ten rysunek trafia też na stronę "O nas" – używamy tego samego obrazu, bez ponownego wgrywania
PLIK_O_NAS = "mary_taylor.jpg"


def wgraj_obraz(nazwa_pliku, tytul):
    """
    Zapisuje plik z folderu 'przyklady' jako obraz w bibliotece Wagtaila.
    Wejście: nazwa pliku i tytuł obrazu. Zwraca: obiekt Image.
    """
    with open(FOLDER / nazwa_pliku, "rb") as plik:
        obraz = Image(title=tytul, file=ImageFile(plik, name=nazwa_pliku))
        obraz.save()
    return obraz


class Command(BaseCommand):
    """Polecenie: python manage.py zaladuj_przyklady – tworzy przykładowe strony i wydania."""

    help = "Tworzy przykładowe strony: Wydania, O nas oraz kilka wydań z rysunkami."

    # Wszystko albo nic: błąd w połowie (np. brak pliku) cofa wszystkie zmiany w bazie
    @transaction.atomic
    def handle(self, *args, **options):
        if IssueIndexPage.objects.exists():
            self.stdout.write("Przykładowe dane już istnieją – pomijam.")
            return

        glowna = HomePage.objects.first()
        if glowna is None:
            raise CommandError("Brak strony głównej – uruchom najpierw: python manage.py migrate")

        glowna.wstep = (
            "<p>Gazety, filmy i rysunki o statkach – od drewnianych szkunerów "
            "po współczesne jednostki. Przy każdym rysunku podajemy, skąd pochodzi.</p>"
        )
        glowna.save()

        # Kolejność dodawania podstron strony głównej = kolejność zakładek w menu
        lista = glowna.add_child(instance=IssueIndexPage(
            title="Wydania",
            slug="wydania",
            show_in_menus=True,
            wstep="<p>Wszystkie nasze gazety, filmy, artykuły i rysunki – od najnowszych.</p>",
        ))

        obraz_o_nas = None
        for wydanie in WYDANIA:
            okladka = wgraj_obraz(wydanie["plik"], wydanie["tytul"])
            if wydanie["plik"] == PLIK_O_NAS:
                obraz_o_nas = okladka
            lista.add_child(instance=IssuePage(
                title=wydanie["tytul"],
                typ=wydanie["typ"],
                numer=wydanie["numer"],
                data=wydanie["data"],
                okladka=okladka,
                zajawka=wydanie["zajawka"],
                opis=(
                    "<p>Przykładowy opis wydania – w panelu administracyjnym "
                    "można go dowolnie zmienić, dodać link do filmu lub sklepu.</p>"
                    f"<p><i>Ilustracja: {wydanie['zrodlo']}, domena publiczna (Wikimedia Commons).</i></p>"
                ),
            ))

        glowna.add_child(instance=AboutPage(
            title="O nas",
            slug="o-nas",
            show_in_menus=True,
            zdjecie=obraz_o_nas,
            tresc=(
                "<p>Kreślarnia Morska to niezależna pracownia, która od lat zajmuje się "
                "historią i techniką okrętową. Wydajemy gazetę, nagrywamy filmy i tworzymy "
                "rysunki techniczne statków.</p>"
                "<p>Na planach pokazujemy, jak zbudowano statek: kształt kadłuba, ożaglowanie "
                "i wymiary. Przy każdym rysunku podajemy jego źródło.</p>"
            ),
        ))

        self.stdout.write(self.style.SUCCESS("Dodano przykładowe strony i wydania."))

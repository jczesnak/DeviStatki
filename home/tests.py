import tempfile
from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings

from home.models import HomePage, IssueIndexPage, IssuePage


def dodaj_wydanie(lista, tytul, data_wydania, opublikowane=True):
    """
    Pomocnicza: dodaje wydanie pod listą wydań.
    Wejście: strona listy, tytuł, data, czy opublikowane. Zwraca: utworzone IssuePage.
    """
    return lista.add_child(instance=IssuePage(title=tytul, data=data_wydania, live=opublikowane))


class AktualneWydanieTests(TestCase):
    """Sprawdza, co strona główna pokazuje jako aktualne i poprzednie wydania."""

    def setUp(self):
        # Strona główna istnieje już dzięki migracji 0002 – dokładamy tylko listę wydań
        self.glowna = HomePage.objects.get()
        self.lista = self.glowna.add_child(instance=IssueIndexPage(title="Wydania"))

    def kontekst(self):
        """Zwraca kontekst szablonu strony głównej (bez renderowania HTML)."""
        return self.glowna.get_context(request=None)

    def test_aktualne_to_najnowsze_wydanie(self):
        """Aktualne = wydanie z najnowszą datą, niezależnie od kolejności dodania."""
        dodaj_wydanie(self.lista, "Stare", date(2026, 1, 1))
        najnowsze = dodaj_wydanie(self.lista, "Najnowsze", date(2026, 9, 1))
        dodaj_wydanie(self.lista, "Środkowe", date(2026, 5, 1))

        self.assertEqual(self.kontekst()["aktualne"], najnowsze)

    def test_szkic_nie_jest_pokazywany(self):
        """Nieopublikowane wydanie (szkic) nie może trafić na stronę, nawet gdy jest najnowsze."""
        opublikowane = dodaj_wydanie(self.lista, "Opublikowane", date(2026, 1, 1))
        dodaj_wydanie(self.lista, "Szkic", date(2026, 12, 1), opublikowane=False)

        kontekst = self.kontekst()
        self.assertEqual(kontekst["aktualne"], opublikowane)
        self.assertEqual(list(kontekst["poprzednie"]), [])

    def test_poprzednie_maksymalnie_trzy(self):
        """Poprzednich wydań jest co najwyżej 3 i nie zawierają aktualnego."""
        for miesiac in range(1, 7):
            dodaj_wydanie(self.lista, f"Wydanie {miesiac}", date(2026, miesiac, 1))

        kontekst = self.kontekst()
        poprzednie = list(kontekst["poprzednie"])
        self.assertEqual(len(poprzednie), 3)
        self.assertNotIn(kontekst["aktualne"], poprzednie)


class ListaWydanTests(TestCase):
    """Sprawdza filtr po typie, stronicowanie i nawigację starsze/nowsze."""

    def setUp(self):
        self.glowna = HomePage.objects.get()
        self.lista = self.glowna.add_child(instance=IssueIndexPage(title="Wydania"))

    def kontekst_listy(self, parametry):
        """Zwraca kontekst listy wydań dla adresu z podanymi parametrami GET."""
        zapytanie = RequestFactory().get("/wydania/", parametry)
        return self.lista.get_context(zapytanie)

    def test_filtr_po_typie(self):
        """?typ=film pokazuje tylko filmy, a nieznany typ – wszystkie wydania."""
        self.lista.add_child(instance=IssuePage(title="Gazeta", typ="gazeta", data=date(2026, 1, 1)))
        film = self.lista.add_child(instance=IssuePage(title="Film", typ="film", data=date(2026, 2, 1)))

        self.assertEqual(list(self.kontekst_listy({"typ": "film"})["wydania"]), [film])
        nieznany = self.kontekst_listy({"typ": "cokolwiek"})
        self.assertEqual(nieznany["wybrany_typ"], "")
        self.assertEqual(len(nieznany["wydania"]), 2)

    def test_stronicowanie_po_12(self):
        """13 wydań = 2 strony; zły numer strony nie powoduje błędu."""
        for dzien in range(1, 14):
            dodaj_wydanie(self.lista, f"Wydanie {dzien}", date(2026, 1, dzien))

        self.assertEqual(len(self.kontekst_listy({})["wydania"]), 12)
        self.assertEqual(len(self.kontekst_listy({"strona": "2"})["wydania"]), 1)
        self.assertEqual(self.kontekst_listy({"strona": "abc"})["wydania"].number, 1)

    def test_starsze_i_nowsze(self):
        """Środkowe wydanie wskazuje na starsze i nowsze; skrajne – tylko na jedno."""
        stare = dodaj_wydanie(self.lista, "Stare", date(2026, 1, 1))
        srodkowe = dodaj_wydanie(self.lista, "Środkowe", date(2026, 5, 1))
        nowe = dodaj_wydanie(self.lista, "Nowe", date(2026, 9, 1))

        kontekst = srodkowe.get_context(request=None)
        self.assertEqual(kontekst["starsze"], stare)
        self.assertEqual(kontekst["nowsze"], nowe)
        self.assertIsNone(nowe.get_context(request=None)["nowsze"])

    def test_strony_renderuja_sie_bez_okladki(self):
        """Strona główna, lista i wydanie bez okładki ani zajawki wyświetlają się bez błędu."""
        wydanie = dodaj_wydanie(self.lista, "Bez okładki", date(2026, 1, 1))
        dodaj_wydanie(self.lista, "Drugie", date(2025, 1, 1))

        for adres in [self.glowna.url, self.lista.url, self.lista.url + "?typ=film", wydanie.url]:
            self.assertEqual(self.client.get(adres).status_code, 200, adres)


# Obrazy z testu zapisujemy do katalogu tymczasowego, żeby nie śmiecić w media/
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ZaladujPrzykladyTests(TestCase):
    """Sprawdza polecenie wgrywające przykładowe dane."""

    def test_dwukrotne_uruchomienie_jest_bezpieczne(self):
        """Drugie uruchomienie niczego nie dubluje."""
        call_command("zaladuj_przyklady", stdout=StringIO())
        liczba_wydan = IssuePage.objects.count()

        call_command("zaladuj_przyklady", stdout=StringIO())

        self.assertEqual(IssueIndexPage.objects.count(), 1)
        self.assertEqual(IssuePage.objects.count(), liczba_wydan)
        self.assertGreater(liczba_wydan, 0)

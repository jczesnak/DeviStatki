from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    """
    Strona główna serwisu.
    Pokazuje wstęp, aktualne (najnowsze) wydanie i kilka poprzednich.
    """

    wstep = RichTextField(blank=True, verbose_name="Wstęp")

    content_panels = Page.content_panels + [FieldPanel("wstep")]
    subpage_types = ["home.IssueIndexPage", "home.AboutPage"]
    max_count = 1

    class Meta:
        verbose_name = "Strona główna"

    def get_context(self, request):
        """
        Dodaje do szablonu wydania.
        Wejście: zapytanie HTTP. Zwraca: słownik kontekstu z kluczami
        'aktualne' (najnowsze wydanie), 'poprzednie' (kolejne 3)
        i 'lista_wydan' (strona "Wydania" – do linku "Wszystkie wydania").
        """
        context = super().get_context(request)
        # "Aktualne wydanie" = opublikowane wydanie z najnowszą datą.
        # Przy tej samej dacie wygrywa później dodane (wyższe id) – wynik zawsze ten sam.
        wydania = IssuePage.objects.live().order_by("-data", "-id")
        context["aktualne"] = wydania.first()
        context["poprzednie"] = wydania[1:4]
        context["lista_wydan"] = IssueIndexPage.objects.live().first()
        return context


class IssueIndexPage(Page):
    """
    Zakładka "Wydania" – lista wszystkich wydań (od najnowszego).
    """

    wstep = RichTextField(blank=True, verbose_name="Wstęp")

    content_panels = Page.content_panels + [FieldPanel("wstep")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.IssuePage"]
    max_count = 1

    class Meta:
        verbose_name = "Lista wydań"

    def get_context(self, request):
        """
        Dodaje do szablonu listę opublikowanych wydań: przefiltrowaną po typie
        (parametr ?typ=) i podzieloną na strony po 12 (parametr ?strona=).
        Wejście: zapytanie HTTP. Zwraca: kontekst z kluczami 'wydania' (bieżąca strona),
        'typy' (lista typów do filtra) i 'wybrany_typ' (pusty tekst = wszystkie).
        """
        context = super().get_context(request)
        wydania = IssuePage.objects.child_of(self).live().order_by("-data", "-id")

        wybrany_typ = request.GET.get("typ", "")
        # Przyjmujemy tylko znane typy – dowolny inny tekst w adresie traktujemy jak "wszystkie"
        if wybrany_typ in dict(IssuePage.TYPY):
            wydania = wydania.filter(typ=wybrany_typ)
        else:
            wybrany_typ = ""

        # get_page() przy złym numerze (np. ?strona=abc albo za dużym) zwraca pierwszą/ostatnią stronę zamiast błędu
        context["wydania"] = Paginator(wydania, 12).get_page(request.GET.get("strona"))
        context["typy"] = IssuePage.TYPY
        context["wybrany_typ"] = wybrany_typ
        return context


class IssuePage(Page):
    """
    Pojedyncze wydanie: numer gazety, film, artykuł albo rysunek.
    Przechowuje tylko informację o wydaniu (opis, okładka, opcjonalny link).
    """

    TYPY = [
        ("gazeta", "Gazeta"),
        ("film", "Film"),
        ("artykul", "Artykuł"),
        ("rysunek", "Rysunek"),
    ]

    typ = models.CharField("Typ", max_length=20, choices=TYPY, default="gazeta")
    numer = models.CharField("Numer wydania", max_length=20, blank=True)
    data = models.DateField("Data wydania")
    okladka = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Okładka",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    zajawka = models.CharField("Zajawka", max_length=250, blank=True)
    opis = RichTextField("Opis", blank=True)
    link = models.URLField("Link (np. do filmu lub sklepu)", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("typ"),
        FieldPanel("numer"),
        FieldPanel("data"),
        FieldPanel("okladka"),
        FieldPanel("zajawka"),
        FieldPanel("opis"),
        FieldPanel("link"),
    ]
    parent_page_types = ["home.IssueIndexPage"]
    subpage_types = []

    # Tekst przycisku z linkiem zewnętrznym – zależny od typu wydania
    NAPISY_LINKU = {
        "gazeta": "Czytaj numer",
        "film": "Obejrzyj film",
        "artykul": "Czytaj artykuł",
        "rysunek": "Zobacz rysunek",
    }

    class Meta:
        verbose_name = "Wydanie"
        verbose_name_plural = "Wydania"

    def napis_linku(self):
        """Zwraca tekst przycisku z linkiem zewnętrznym, dopasowany do typu wydania."""
        return self.NAPISY_LINKU.get(self.typ, "Przejdź do wydania")

    def get_context(self, request):
        """
        Dodaje do szablonu sąsiednie wydania (do nawigacji "starsze / nowsze").
        Wejście: zapytanie HTTP. Zwraca: kontekst z kluczami 'starsze' i 'nowsze' (mogą być None).
        """
        context = super().get_context(request)
        rodzenstwo = IssuePage.objects.sibling_of(self, inclusive=False).live()
        # Ta sama kolejność co na liście wydań: data, a przy tej samej dacie id
        context["starsze"] = rodzenstwo.filter(
            Q(data__lt=self.data) | Q(data=self.data, id__lt=self.id)
        ).order_by("-data", "-id").first()
        context["nowsze"] = rodzenstwo.filter(
            Q(data__gt=self.data) | Q(data=self.data, id__gt=self.id)
        ).order_by("data", "id").first()
        return context


class AboutPage(Page):
    """
    Zakładka "O nas" – zwykła strona z tekstem i zdjęciem.
    """

    tresc = RichTextField("Treść", blank=True)
    zdjecie = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Zdjęcie",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [FieldPanel("tresc"), FieldPanel("zdjecie")]
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    class Meta:
        verbose_name = "O nas"

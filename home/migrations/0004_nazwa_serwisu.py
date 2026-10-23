from django.conf import settings
from django.db import migrations


def ustaw_nazwe_serwisu(apps, schema_editor):
    """
    Przepisuje nazwę serwisu z WAGTAIL_SITE_NAME (jedyne źródło) do Site.site_name
    i nadaje stronie głównej polski tytuł. Wejście: rejestr modeli migracji. Nic nie zwraca.
    """
    Site = apps.get_model("wagtailcore", "Site")
    HomePage = apps.get_model("home", "HomePage")

    Site.objects.filter(is_default_site=True).update(site_name=settings.WAGTAIL_SITE_NAME)
    HomePage.objects.filter(title="Home").update(title="Strona główna", draft_title="Strona główna")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0003_issueindexpage_alter_homepage_options_homepage_wstep_and_more"),
    ]

    operations = [
        migrations.RunPython(ustaw_nazwe_serwisu, migrations.RunPython.noop),
    ]

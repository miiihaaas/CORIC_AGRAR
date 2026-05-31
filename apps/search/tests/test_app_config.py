"""Story 2.13 — AC1 app registracija + INSTALLED_APPS + URL reverse (TEA RED phase).

Pokriva AC1: apps/search/ app kreiran i registrovan; `django.contrib.postgres` u
INSTALLED_APPS; `apps.search` POSLE `apps.products`; config/urls.py uključuje
apps.search.urls; `reverse("search:dropdown")`/`reverse("search:results")` rade
(locale-aware); `manage.py check` exit 0.

TEA RED phase: SVI testovi MORAJU pasti — apps.search ne postoji, NIJE u INSTALLED_APPS,
urls nisu registrovani.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_app_config.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC1 + Task 1 + SM-D1/D2/D6
- 2-13-interface-contract.md § 1 (apps.py) + § 2 (INSTALLED_APPS)
"""

from __future__ import annotations

from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate


# AC1: SearchConfig.name == "apps.search" (sa prefiksom; mirror Gotcha PR-1)
def test_search_config_name_is_apps_search():
    from apps.search.apps import SearchConfig

    assert SearchConfig.name == "apps.search", (
        f"SearchConfig.name mora biti 'apps.search' (sa apps. prefiksom), "
        f"dobio: {SearchConfig.name!r}."
    )


# AC1: SearchConfig.default_auto_field == BigAutoField
def test_search_config_default_auto_field_is_bigautofield():
    from apps.search.apps import SearchConfig

    assert SearchConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"SearchConfig.default_auto_field mora biti BigAutoField, "
        f"dobio: {SearchConfig.default_auto_field!r}."
    )


# AC1: "apps.search" registrovan u INSTALLED_APPS
def test_apps_search_in_installed_apps():
    assert "apps.search" in settings.INSTALLED_APPS, (
        "'apps.search' MORA biti u INSTALLED_APPS (SM-D2)."
    )


# AC1: "django.contrib.postgres" u INSTALLED_APPS (SM-D6 — SearchVectorField + GinIndex checks)
def test_django_contrib_postgres_in_installed_apps():
    assert "django.contrib.postgres" in settings.INSTALLED_APPS, (
        "'django.contrib.postgres' MORA biti u INSTALLED_APPS (SM-D6) — potreban za "
        "SearchVectorField + GinIndex system check validacije."
    )


# AC1: "apps.search" POSLE "apps.products" (jednosmerna zavisnost search → products, SM-D2)
def test_apps_search_after_apps_products_in_installed_apps():
    apps_list = list(settings.INSTALLED_APPS)
    assert "apps.search" in apps_list and "apps.products" in apps_list, (
        "Oba apps.search i apps.products moraju biti u INSTALLED_APPS."
    )
    assert apps_list.index("apps.search") > apps_list.index("apps.products"), (
        "'apps.search' MORA biti POSLE 'apps.products' u INSTALLED_APPS (SM-D2 — "
        "search importuje Product, jednosmerna dep mirror PR-D1)."
    )


# AC1: app_name = "search" na urls modulu
def test_search_urls_app_name_is_search():
    from apps.search import urls as search_urls

    assert getattr(search_urls, "app_name", None) == "search", (
        "apps/search/urls.py MORA imati `app_name = 'search'`."
    )


# AC1: reverse("search:dropdown") → /sr/htmx/pretraga/ (locale-aware, i18n_patterns)
def test_reverse_search_dropdown_is_locale_aware():
    activate("sr")
    url = reverse("search:dropdown")
    assert url == "/sr/htmx/pretraga/", (
        f"reverse('search:dropdown') treba '/sr/htmx/pretraga/', dobio {url!r}. "
        "URL MORA biti unutar i18n_patterns (locale prefiks)."
    )


# AC1: reverse("search:results") → /sr/pretraga/ (locale-aware)
def test_reverse_search_results_is_locale_aware():
    activate("sr")
    url = reverse("search:results")
    assert url == "/sr/pretraga/", (
        f"reverse('search:results') treba '/sr/pretraga/', dobio {url!r}."
    )


# AC1: manage.py check exit 0 SA registrovanim search infra (postgres app + GinIndex valid)
def test_manage_check_passes_with_search_infra_registered():
    """`manage.py check` mora biti čist DOK su apps.search + django.contrib.postgres
    registrovani i GinIndex validan.

    Prvo asertuje da je infra prisutna (fails u RED — nije instalirana), ZATIM check
    exit 0. Bez infra-asercije, gol `check` bi lažno prošao na trenutnom (još-bez-search)
    code-base-u → false green.
    """
    from io import StringIO

    from django.core.management import call_command

    # Infra MORA biti prisutna — inače „check passes" je trivijalno tačno bez search-a.
    assert "django.contrib.postgres" in settings.INSTALLED_APPS, (
        "Pre check-a: django.contrib.postgres MORA biti registrovan (AC1/SM-D6)."
    )
    assert "apps.search" in settings.INSTALLED_APPS, (
        "Pre check-a: apps.search MORA biti registrovan (AC1/SM-D2)."
    )

    out = StringIO()
    # call_command raise-uje SystemCheckError ako ima error-level poruka (npr. models.E033
    # za predugačko GIN ime, postgres.E*).
    call_command("check", stdout=out, stderr=out)
    output = out.getvalue()
    assert "Error" not in output or "0 issues" in output or "no issues" in output.lower(), (
        f"`manage.py check` MORA biti čist (exit 0) sa GIN indeksom + postgres app. "
        f"Output: {output!r}."
    )

"""Root URLconf za config projekat.

`set_language` view se EKSPLICITNO definiše PRE locale prefix bloka jer mora biti
dostupan na fiksnoj URL-i (`/i18n/setlang/`) bez lokal prefiksa — Django
`set_language` POST handler sam handluje redirect na ekvivalentnu URL-u u novoj
lokali (`/sr/proizvodi/` → `/hu/proizvodi/`).

`prefix_default_language=True` eksplicitno postavljeno radi čitljivosti — to znači
da root `/` redirektuje na `/sr/` (default lang prefiks dobija svoj URL prostor).
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.i18n import set_language

from apps.core.views import healthz  # Story 9.4 — /healthz/ liveness probe (UptimeRobot)
from apps.seo.sitemaps import sitemaps as sitemaps_dict  # alias da ne shadow-uje `sitemap` view
from apps.seo.views import robots_txt

# URL-ovi BEZ lokal prefiksa
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
    # Story 6.2 — sitemap.xml VAN i18n_patterns (NIJE locale-prefiksovan; jedan
    # /sitemap.xml lista sve locale alternate kroz i18n=True — SM-D2/AC7).
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps_dict},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Story 6.3 — robots.txt VAN i18n_patterns (NO-PREFIX; bot ga traži na root-u
    # → /robots.txt, NE /sr/robots.txt). Sitemap: linija referencira /sitemap.xml
    # (SM-D4/SEO3-7).
    path("robots.txt", robots_txt, name="robots_txt"),
    # Story 8.1 (SM-D1/G-3) — admin VAN i18n_patterns na bare `/admin-coric/`
    # (security-through-obscurity; admin NE treba locale prefiks; arch:964
    # „middleware ne procesira /admin-coric/"). Non-i18n urlpatterns se
    # evaluiraju PRE i18n_patterns → `/admin-coric/` rezolvira bez locale
    # prefiksa. `/admin/` i `/sr/admin/` → 404 (uklonjeno iz i18n_patterns).
    path("admin-coric/", admin.site.urls),
    # Story 9.4 (SM-D2/G-1) — /healthz/ VAN i18n_patterns (NO-PREFIX). UptimeRobot
    # pinga GOLU putanju `/healthz/` (NE `/sr/healthz/`); monitor ne zna za locale
    # prefikse. Non-i18n blok se evaluira PRE i18n_patterns → `/healthz/` rezolvira
    # bez prefiksa (reverse("healthz") == "/healthz/"). Da je u i18n_patterns dao bi
    # `/sr/healthz/` i ostavio `/healthz/` na 404 → monitor bi odmah pao.
    path("healthz/", healthz, name="healthz"),
]

# URL-ovi SA lokal prefiksom (`/sr/...`, `/hu/...`, `/en/...`)
urlpatterns += i18n_patterns(
    # Story 8.1 (SM-D1): admin PREMEŠTEN iz i18n_patterns na bare `/admin-coric/`
    # (gore, non-i18n blok). `/admin/` i `/sr/admin/` sada → 404.
    path("", include("apps.brands.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.search.urls")),  # NOVO Story 2.13 — pretraga/ + htmx/pretraga/ (SM-D2)
    path("", include("apps.forms.urls")),  # NOVO Story 4.2 — htmx/forme/kontakt/ (kontakt forma submit)
    path("", include("apps.blog.urls")),  # NOVO Story 5.2 — /sr/blog/ + /sr/blog/<slug>/
    path("", include("apps.gdpr.urls")),  # NOVO Story 7.1 — /sr/politika-kolacica/ (CookiePolicy javna strana, G-5)
    # Story 7.4 CRITICAL-1 (SM-D11): pages include MORA biti POSLEDNJI — pages
    # catch-all `<slug:slug>/` (1-segment) bi inače shadow-ovao /sr/blog/ (blog) i
    # /sr/politika-kolacica/ (gdpr) PREKO include granica (resolver first-match-wins
    # preko jedne sploštene liste). pages.urls poseduje root `""` → home; prazan path
    # matchuje TAČNO prazan path, nijedan drugi include ne polaže pravo na goli "".
    path("", include("apps.pages.urls")),  # NOVO Story 3.1 — root `/` → HomeView; POSLEDNJI (CRITICAL-1)
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

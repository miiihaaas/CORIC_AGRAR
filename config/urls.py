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
]

# URL-ovi SA lokal prefiksom (`/sr/...`, `/hu/...`, `/en/...`)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.brands.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.search.urls")),  # NOVO Story 2.13 — pretraga/ + htmx/pretraga/ (SM-D2)
    path("", include("apps.pages.urls")),  # NOVO Story 3.1 — root `/` → HomeView (pages:home); zamenjuje core:home
    path("", include("apps.forms.urls")),  # NOVO Story 4.2 — htmx/forme/kontakt/ (kontakt forma submit)
    path("", include("apps.blog.urls")),  # NOVO Story 5.2 — /sr/blog/ + /sr/blog/<slug>/
    path("", include("apps.gdpr.urls")),  # NOVO Story 7.1 — /sr/politika-kolacica/ (CookiePolicy javna strana, G-5)
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

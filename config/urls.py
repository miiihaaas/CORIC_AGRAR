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
from django.urls import include, path
from django.views.i18n import set_language

# URL-ovi BEZ lokal prefiksa
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
]

# URL-ovi SA lokal prefiksom (`/sr/...`, `/hu/...`, `/en/...`)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

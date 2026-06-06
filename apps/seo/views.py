"""Story 6.3 — robots.txt endpoint (SM-D4 / AC1).

PRVI view u apps.seo. Renderuje `templates/seo/robots.txt` kao `text/plain` sa
apsolutnom (build_absolute_uri) reverse-based /sitemap.xml URL-om (jedini 6-2→6-3
ugovor). Registrovan VAN i18n_patterns (NO-PREFIX) → /robots.txt, NE /sr/robots.txt.
"""

from django.shortcuts import render
from django.urls import reverse


def robots_txt(request):
    """GET /robots.txt → text/plain sa Sitemap: apsolutni reverse-based URL."""
    sitemap_url = request.build_absolute_uri(
        reverse("django.contrib.sitemaps.views.sitemap")
    )
    return render(
        request,
        "seo/robots.txt",
        {"sitemap_url": sitemap_url},
        content_type="text/plain",
    )

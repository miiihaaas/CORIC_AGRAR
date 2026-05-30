"""Placeholder view za product detail — Story 2.6 (C8 fix).

Story 2.7 zameni `placeholder_view` sa pravim `ProductDetailView` CBV-om.
Placeholder spečuje NoReverseMatch kad brand listing kartice linkuju ka
`{% url 'products:detail' slug=... %}` pre nego što Story 2.7 implementira
pun view.
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def placeholder_view(request: HttpRequest, slug: str) -> HttpResponse:
    """Render minimal "Stranica još nije dostupna" placeholder (HTTP 200).

    Ne radi DB query za Product lookup — slug se ignoriše (FBV se zameni u
    Story 2.7 sa pravim DetailView).
    """
    return render(request, "products/_placeholder.html")

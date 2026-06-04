"""Story 4.2 — URL routing za apps.forms (HTMX kontakt endpoint).

`app_name = "forms"`; HTMX prefix konvencija (mirror apps/search/urls.py):
`htmx/forme/kontakt/` → sa i18n prefiksom postaje `/sr/htmx/forme/kontakt/`.
"""

from __future__ import annotations

from django.urls import path

from apps.forms import views

app_name = "forms"

urlpatterns = [
    path("htmx/forme/kontakt/", views.contact_submit, name="contact_submit"),
    path(
        "htmx/forme/upit-za-model/",
        views.model_inquiry_submit,
        name="model_inquiry_submit",
    ),
    path(
        "htmx/forme/servis/",
        views.service_request_submit,
        name="service_request_submit",
    ),
]

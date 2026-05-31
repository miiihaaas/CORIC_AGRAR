"""URL routing za apps.brands — Story 2.6 + Story 2.10."""

from django.urls import path

from apps.brands.views import BrandDetailView, JeegeePrikljucnaView

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
    path(
        "mehanizacija/prikljucna/",
        JeegeePrikljucnaView.as_view(),
        name="jeegee_prikljucna",
    ),
]

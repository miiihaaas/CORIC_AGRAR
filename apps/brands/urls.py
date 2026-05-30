"""URL routing za apps.brands — Story 2.6."""

from django.urls import path

from apps.brands.views import BrandDetailView

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
]

"""URL routing za apps.products — Story 2.7 ProductDetailView + Story 2.8 TractorListView."""

from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    # Story 2.8 — SM-D1: `traktori/` (bez slug-a) NE shadow-uje
    # `apps/brands/urls.py:10` `traktori/<slug:slug>/` (BrandDetailView). Django
    # URL resolver iterira u redu — slug converter zahteva content posle `traktori/`.
    path("traktori/", views.TractorListView.as_view(), name="tractor_list"),
]

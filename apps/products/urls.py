"""URL routing za apps.products — Story 2.7 ProductDetailView + Story 2.8 TractorListView + Story 2.9 UsedMachineryListView."""

from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    # Story 2.8 — SM-D1: `traktori/` (bez slug-a) NE shadow-uje
    # `apps/brands/urls.py:10` `traktori/<slug:slug>/` (BrandDetailView). Django
    # URL resolver iterira u redu — slug converter zahteva content posle `traktori/`.
    path("traktori/", views.TractorListView.as_view(), name="tractor_list"),
    # Story 2.9 — SM-D1: `mehanizacija/polovna/` je statički dvoslojni path bez
    # slug-a; ne shadow-uje nijedan postojeći pattern (traktori/<slug>/,
    # proizvod/<slug>/, traktori/).
    path(
        "mehanizacija/polovna/",
        views.UsedMachineryListView.as_view(),
        name="used_machinery_list",
    ),
]

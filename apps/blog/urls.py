"""URL routing za apps.blog — Story 5.2 + 5.3 arhive.

`app_name="blog"` → `blog:index` (`/sr/blog/`), `blog:category`
(`/sr/blog/kategorija/<slug>/`), `blog:tag` (`/sr/blog/tag/<slug>/`),
`blog:detail` (`/sr/blog/<slug>/`).

Gotcha BL2-4: `blog/` (index, bez slug-a) MORA biti PRE `blog/<slug>/`. SM-D3:
2-segmentne arhive (`blog/kategorija/<slug>/`, `blog/tag/<slug>/`) registrovane
PRE 1-segmentnog catch-all `blog/<slug>/` (kanonska higijena — specifične-PRE-
catch-all; 2-segment i 1-segment se strukturno ne preklapaju, IMP-5).
"""

from django.urls import path

from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("blog/", views.BlogIndexView.as_view(), name="index"),  # PRE slug (Gotcha BL2-4)
    path("blog/kategorija/<slug:slug>/", views.BlogCategoryView.as_view(), name="category"),  # 5-3 PRE catch-all
    path("blog/tag/<slug:slug>/", views.BlogTagView.as_view(), name="tag"),  # 5-3 PRE catch-all
    path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="detail"),  # catch-all LAST
]

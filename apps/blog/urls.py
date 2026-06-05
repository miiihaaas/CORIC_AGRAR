"""URL routing za apps.blog — Story 5.2 BlogIndexView + BlogPostDetailView placeholder.

`app_name="blog"` → `blog:index` (`/sr/blog/`) + `blog:detail` (`/sr/blog/<slug>/`).
SM-D11: registracija `blog:detail` aktivira 5-1 `Post.get_absolute_url()` (više NE
raise NoReverseMatch). Gotcha BL2-4: `blog/` (index, bez slug-a) MORA biti PRE
`blog/<slug>/` (statički-pre-slug, mirror products urls.py).
"""

from django.urls import path

from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("blog/", views.BlogIndexView.as_view(), name="index"),  # PRE slug (Gotcha BL2-4)
    path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="detail"),
]

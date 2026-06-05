"""Blog views — Story 5.2 BlogIndexView + BlogPostDetailView placeholder.

Story 5.2 — javna blog INDEX strana `/sr/blog/` (`BlogIndexView(ListView)`):
listira OBJAVLJENE „Priče sa polja" kroz `Post.published` manager (NIKAD
`Post.objects` — draft/future NEVIDLJIV javno; SM-D2 / Gotcha BL2-1), kao kartice
(main_image/datum/title/perex/„SAZNAJ VIŠE"), paginacija 10/strani, HTMX category
filter `?kategorija=<slug>` (request.htmx branching + OOB aria-live guard +
push-url — mirror 2-8/2-9), Paginator.get_page() overflow safety, N+1 lock
`select_related("category")` (BEZ tags prefetch — IMP-1).

`BlogPostDetailView(DetailView)` je MINIMALAN placeholder (SM-D11) koju Story 5.3
OBOGAĆUJE (slične objave, social share, kategorija/tag linkovi, meta). Registruje
`blog:detail` URL tako da 5-1 `Post.get_absolute_url()` razrešava i kartice
linkuju ispravno.

NEMA model promene / NEMA migracije — 5-2 čist view/template/URL sloj nad 5-1 šemom.
Pattern REUSE: mirror `apps/products/views.py` TractorListView (2-8) /
UsedMachineryListView (2-9).
"""

from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView

from apps.blog.models import Category, Post

_POSTS_PER_PAGE = 10  # AC3 — epics.md:875 (SM-D3)


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogIndexView(ListView):
    """Blog index strana sa HTMX category filterom — Story 5.2.

    Mirror 2-8/2-9 single-view request.htmx branching: full page (non-HTMX) vs
    results partial (HTMX). queryset bazira na `Post.published` (draft-not-leaked
    granica — SM-D2). `select_related("category")` N+1 lock (AC2); BEZ
    `prefetch_related("tags")` (kartica ne renderuje tagove — IMP-1).
    """

    model = Post
    context_object_name = "posts"
    paginate_by = _POSTS_PER_PAGE

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["blog/partials/_post_results.html"]
        return ["blog/blog_index.html"]

    def get_queryset(self):
        # SM-D2 / Gotcha BL2-1: NIKAD Post.objects (draft/future bi procurili javno).
        qs = Post.published.select_related("category")
        kategorija = self.request.GET.get("kategorija", "").strip()
        if kategorija:
            qs = qs.filter(category__slug=kategorija)
        return qs  # default ordering iz Meta (najnovije prvo)

    def paginate_queryset(self, queryset, page_size):
        # SM-D25 overflow safety — Paginator.get_page() clamp invalid/out-of-range
        # page numbers na poslednju/prvu stranu (NE 404 EmptyPage).
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        page_obj = paginator.get_page(page)
        return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["categories_for_dropdown"] = Category.objects.order_by("name")

        active_filters = {"kategorija": self.request.GET.get("kategorija", "")}
        # IMP-3 normalizacija: invalid kategorija slug → reset na "" za dropdown
        # koherenciju (queryset i dalje vraća 0 rezultata → empty state handluje).
        valid_slugs = {c.slug for c in ctx["categories_for_dropdown"]}
        if active_filters["kategorija"] and active_filters["kategorija"] not in valid_slugs:
            active_filters["kategorija"] = ""
        ctx["active_filters"] = active_filters

        ctx["count"] = ctx["paginator"].count  # OOB aria-live announcement
        return ctx


class BlogPostDetailView(DetailView):
    """Placeholder blog detail strana — Story 5.2 (SM-D11; 5.3 OBOGAĆUJE).

    MINIMALAN render (naslov + datum + telo) iz `Post.published` queryset
    (draft/future detail → 404). 5-3 proširuje get_context_data (slične objave) +
    template (social share, kategorija/tag linkovi, meta) BEZ menjanja URL
    signature/queryset baze. `context_object_name="post"` je 5-3 ugovor (IMP-5).

    FORWARD-NOTE (5-3): kad 5-3 doda render autora/tagova, MORA proširiti
    get_queryset() sa select_related("author") / prefetch_related("tags")
    (sprečava 5-3 N+1). 5-2 ih NE dodaje (placeholder ih ne renderuje — YAGNI).
    """

    model = Post
    context_object_name = "post"
    template_name = "blog/post_detail.html"

    def get_queryset(self):
        # SM-D2: Post.published → draft/future detail → 404. SAMO category (5-2).
        return Post.published.select_related("category")

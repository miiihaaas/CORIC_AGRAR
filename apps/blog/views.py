"""Blog views — Story 5.2 BlogIndexView + Story 5.3 enriched detail & archives.

Story 5.2 — javna blog INDEX strana `/sr/blog/` (`BlogIndexView(ListView)`):
listira OBJAVLJENE „Priče sa polja" kroz `Post.published` manager (NIKAD
`Post.objects` — draft/future NEVIDLJIV javno; SM-D2 / Gotcha BL2-1), kao kartice
(main_image/datum/title/perex/„SAZNAJ VIŠE"), paginacija 10/strani, HTMX category
filter `?kategorija=<slug>` (request.htmx branching + OOB aria-live guard +
push-url — mirror 2-8/2-9), Paginator.get_page() overflow safety, N+1 lock
`select_related("category")` (BEZ tags prefetch — IMP-1).

`BlogPostDetailView(DetailView)` je Story 5.3 OBOGAĆEN detail (slične objave,
social share, kategorija/tag linkovi, meta) nad 5-2 placeholder-om. Registruje
`blog:detail` URL tako da 5-1 `Post.get_absolute_url()` razrešava i kartice
linkuju ispravno. Story 5.3 dodaje i kategorija/tag arhive (`_BlogArchiveListView`
baza → `BlogCategoryView` / `BlogTagView`).

NEMA model promene / NEMA migracije — 5-2 čist view/template/URL sloj nad 5-1 šemom.
Pattern REUSE: mirror `apps/products/views.py` TractorListView (2-8) /
UsedMachineryListView (2-9).
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView

from apps.blog.models import Category, Post, Tag

_POSTS_PER_PAGE = 10  # AC3 — epics.md:875 (SM-D3)
_SIMILAR_POSTS_LIMIT = 4  # epics.md:889 (2-4); mirror 2-7 _SIMILAR_PRODUCTS_LIMIT


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
    """Obogaćen blog detail strana — Story 5.3 (nad 5-2 placeholder-om; SM-D11).

    Pun render: naslovna slika + meta (datum + autor NULL-guard + kategorija link)
    + naslov + telo `|linebreaks` (auto-escape, NIKAD `|safe`) + tag linkovi +
    „Slične objave" + social share. Queryset bazira na `Post.published`
    (draft/future detail → 404). `context_object_name="post"` (IMP-5).

    get_queryset() select_related("category","author") + prefetch_related("tags")
    (autor meta + tag-link render N+1 lock — SM-D2). get_context_data postavlja
    `similar_posts` (SM-D8) + `share_url` (IMP-2).
    """

    model = Post
    context_object_name = "post"
    template_name = "blog/post_detail.html"

    def get_queryset(self):
        # SM-D2 / IMP-5: Post.published → draft/future detail → 404.
        # select_related("category","author") (meta render N+1 lock) +
        # prefetch_related("tags") (tag-link render N+1 lock).
        return Post.published.select_related("category", "author").prefetch_related(
            "tags"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        # SM-D8: „Slične objave" — published-only (draft-not-leaked), ISTA kategorija,
        # exclude-self, bounded. post.category None (SET_NULL) → prazna (NE crash).
        if post.category_id:
            similar = (
                Post.published.filter(category=post.category)
                .exclude(pk=post.pk)
                .select_related("category")[:_SIMILAR_POSTS_LIMIT]
            )
            ctx["similar_posts"] = list(similar)
        else:
            ctx["similar_posts"] = []
        # IMP-2: apsolutni share URL izračunat u view-u (template {{ }} ne može
        # metodi proslediti argument).
        ctx["share_url"] = self.request.build_absolute_uri(post.get_absolute_url())
        return ctx


class _BlogArchiveListView(ListView):
    """Zajednička baza za kategorija/tag arhive — mirror BlogIndexView (SM-D4/SM-D9).

    Paginate_by=10 + Paginator.get_page() overflow clamp + HTMX template branching
    + @vary_on_headers (per-podklasa). Podklase definišu `archive_kind`, resolve
    `archive_object` u setup() (404 bad slug) i `get_queryset()` (Post.published).
    """

    model = Post
    context_object_name = "posts"
    paginate_by = _POSTS_PER_PAGE
    archive_kind = ""

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["blog/partials/_post_results.html"]
        return ["blog/blog_archive.html"]

    def paginate_queryset(self, queryset, page_size):
        # SM-D9 — REUSE BlogIndexView Paginator.get_page() overflow clamp.
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
        ctx["archive_object"] = self.archive_object
        ctx["archive_kind"] = self.archive_kind
        ctx["count"] = ctx["paginator"].count  # OOB aria-live announcement
        # IMP-1: arhive REUSE _post_results.html → _blog_empty_state.html grana na
        # {% if active_filters.kategorija %} → arhiva-prikladna „Nema objava…" + „prikaži
        # sve" → blog:index. Bez ovoga empty render-uje pogrešnu generičku home CTA.
        ctx["active_filters"] = {"kategorija": self.kwargs["slug"]}
        return ctx


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogCategoryView(_BlogArchiveListView):
    """Kategorija arhiva `/sr/blog/kategorija/<slug>/` — Story 5.3 (AC3/SM-D4)."""

    archive_kind = "category"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.archive_object = get_object_or_404(Category, slug=kwargs["slug"])

    def get_queryset(self):
        return Post.published.select_related("category").filter(
            category__slug=self.kwargs["slug"]
        )


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogTagView(_BlogArchiveListView):
    """Tag arhiva `/sr/blog/tag/<slug>/` — Story 5.3 (AC4/SM-D4)."""

    archive_kind = "tag"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.archive_object = get_object_or_404(Tag, slug=kwargs["slug"])

    def get_queryset(self):
        # IMP-6a — .distinct() kanonski M2M join-dup guard (Gotcha BL3-4).
        return (
            Post.published.select_related("category")
            .filter(tags__slug=self.kwargs["slug"])
            .distinct()
        )

"""Blog views — Story 5.2 BlogIndexView + Story 5.3 enriched detail & archives.

Category je UKLONJEN (post-launch odluka) — blog objave se više ne kategorišu;
jedina preostala taksonomija je Tag (arhiva + detail linkovi).

Story 5.2 — javna blog INDEX strana `/sr/blog/` (`BlogIndexView(ListView)`):
listira OBJAVLJENE „Priče sa polja" kroz `Post.published` manager (NIKAD
`Post.objects` — draft/future NEVIDLJIV javno; SM-D2 / Gotcha BL2-1), kao kartice
(main_image/datum/title/perex/„SAZNAJ VIŠE"), paginacija 10/strani,
Paginator.get_page() overflow safety.

`BlogPostDetailView(DetailView)` je Story 5.3 OBOGAĆEN detail (social share, tag
linkovi, meta) nad 5-2 placeholder-om. Registruje `blog:detail` URL tako da 5-1
`Post.get_absolute_url()` razrešava i kartice linkuju ispravno. `BlogTagView` je
tag arhiva (mirror 2-8/2-9 request.htmx branching + OOB aria-live guard).

NEMA model promene / NEMA migracije — 5-2 čist view/template/URL sloj nad 5-1 šemom.
Pattern REUSE: mirror `apps/products/views.py` TractorListView (2-8) /
UsedMachineryListView (2-9).
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView

from apps.blog.models import Post, Tag

_POSTS_PER_PAGE = 10  # AC3 — epics.md:875 (SM-D3)


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogIndexView(ListView):
    """Blog index strana — Story 5.2.

    Mirror 2-8/2-9 single-view request.htmx branching: full page (non-HTMX) vs
    results partial (HTMX). queryset bazira na `Post.published` (draft-not-leaked
    granica — SM-D2). BEZ `prefetch_related("tags")` (kartica ne renderuje
    tagove — IMP-1).
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
        return Post.published.all()  # default ordering iz Meta (najnovije prvo)

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
        ctx["count"] = ctx["paginator"].count  # OOB aria-live announcement
        return ctx


class BlogPostDetailView(DetailView):
    """Obogaćen blog detail strana — Story 5.3 (nad 5-2 placeholder-om; SM-D11).

    Pun render: naslovna slika + meta (datum + autor NULL-guard + kategorija link)
    + naslov + telo `|linebreaks` (auto-escape, NIKAD `|safe`) + tag linkovi +
    „Slične objave" + social share. Queryset bazira na `Post.published`
    (draft/future detail → 404). `context_object_name="post"` (IMP-5).

    get_queryset() select_related("author") + prefetch_related("tags") (autor
    meta + tag-link render N+1 lock — SM-D2). get_context_data postavlja
    `share_url` (IMP-2).
    """

    model = Post
    context_object_name = "post"
    template_name = "blog/post_detail.html"

    def get_queryset(self):
        # SM-D2 / IMP-5: Post.published → draft/future detail → 404.
        # select_related("author") (meta render N+1 lock) + prefetch_related("tags")
        # (tag-link render N+1 lock).
        return Post.published.select_related("author").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # IMP-2: apsolutni share URL izračunat u view-u (template {{ }} ne može
        # metodi proslediti argument).
        ctx["share_url"] = self.request.build_absolute_uri(
            self.object.get_absolute_url()
        )
        return ctx


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogTagView(ListView):
    """Tag arhiva `/sr/blog/tag/<slug>/` — Story 5.3 (AC4/SM-D4), mirror BlogIndexView.

    Paginate_by=10 + Paginator.get_page() overflow clamp + HTMX template branching.
    404 na nepostojeći tag slug (setup()).
    """

    model = Post
    context_object_name = "posts"
    paginate_by = _POSTS_PER_PAGE

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.archive_object = get_object_or_404(Tag, slug=kwargs["slug"])

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["blog/partials/_post_results.html"]
        return ["blog/blog_archive.html"]

    def get_queryset(self):
        # IMP-6a — .distinct() kanonski M2M join-dup guard (Gotcha BL3-4).
        return Post.published.filter(tags__slug=self.kwargs["slug"]).distinct()

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
        ctx["count"] = ctx["paginator"].count  # OOB aria-live announcement
        # IMP-1: arhiva REUSE _post_results.html → _blog_empty_state.html grana na
        # {% if is_archive %} → arhiva-prikladna „Nema objava…" + „prikaži sve" →
        # blog:index. Bez ovoga empty render-uje pogrešnu generičku home CTA.
        ctx["is_archive"] = True
        return ctx

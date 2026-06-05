"""Story 5.4 — Footer „Najnovije vesti" context processor.

`latest_blog_posts(request)` exposes ≤3 NAJNOVIJE PUBLISHED objave svim
template-ima (footer kolona 3 u base.html → radi na SVAKOM renderu).

SM-D2 (lazy): `SimpleLazyObject` → DB upit puca SAMO kad template iterira
`latest_blog_posts` (full-page render sa footerom). HTMX partial koji NE
renderuje footer → lazy se NE razrešava → 0 upita.

SM-D2 (list): `list(...)` UNUTAR lambda → lazy kešira listu posle prvog poziva
→ template re-iteracija NE re-query (1 upit ukupno; Gotcha BL4-1).

SM-D1 (ordering): EKSPLICITAN `.order_by("-published_at", "-created_at")` —
published_at je user-facing recency. NE oslanja se na Meta.ordering.

SM-D3 (draft-not-leaked): `Post.published` (NIKAD `Post.objects`) —
status="published" AND published_at__lte=now. Footer je svuda → Post.objects bi
procurio nacrt/zakazanu objavu na CEO sajt.

SM-D4 (query shape): BEZ `.only()` — `title` je modeltranslation → .only() bi
deferovao → per-row deferred N+1. Plain [:3] queryset je već minimalan.

BL4-6: prost callable BEZ try/except — context processor radi sitewide; defensive
try/except bi sakrio realne greške. Blast radius svesno prihvaćen.
"""

from __future__ import annotations

from django.utils.functional import SimpleLazyObject

from apps.blog.models import Post


def latest_blog_posts(request) -> dict:
    """Exposes ≤3 NAJNOVIJE PUBLISHED objave svim template-ima (footer kolona 3)."""
    return {
        "latest_blog_posts": SimpleLazyObject(
            lambda: list(
                Post.published.order_by("-published_at", "-created_at")[:3]
            )
        )
    }

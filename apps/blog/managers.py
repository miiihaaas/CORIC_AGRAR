"""Story 5.1 — Blog-specific managers.

`PublishedManager` (SM-D5) — javni opt-in queryset koji filtrira SAMO objavljene
objave: `status="published"` AND `published_at__lte=timezone.now()`.

Gotcha BL-1: NE importuje `Post` na vrhu modula (managers ↔ models kružna
zavisnost). Status filter koristi STRING LITERAL `"published"` (NE
`Post.Status.PUBLISHED` import) — DB vrednost je locked ugovor (IMP-3 test
asertuje `Post.Status.PUBLISHED.value == "published"`).

`timezone.now()` se evaluira PER-QUERY (poziv UNUTAR `get_queryset`, NE
module-level konstanta — inače zamrznuto vreme).
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone


class PublishedManager(models.Manager):
    """Vraća SAMO objave sa status='published' i published_at <= now (per-query)."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(status="published", published_at__lte=timezone.now())
        )

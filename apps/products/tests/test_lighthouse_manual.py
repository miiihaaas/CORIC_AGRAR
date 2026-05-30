"""Story 2.7 — AC9 manual Lighthouse audit placeholder (1 xfail test).

Subtask 12.7: AC9 je MANUELNI smoke check (Dev izvršava lokalno + Lighthouse CLI).
Automated tests covers AC1-AC8 programmatic requirements; Lighthouse audit + prefers-reduced-motion
+ FR-20 hibrid manual override/auto fallback paths + variant zoom no-state-change su
**out-of-scope za TEA/Dev automation** (Story 9.8 Playwright UJ-1 + Story 9.9 a11y audit-gate scope).

Ovaj fajl drži 1 `xfail`-marked test kao placeholder za AC9 manual smoke compliance.
Test će uvek `xfail` jer ne moramo automatizovati manual smoke; svrha je da TEA tally
testova uključuje AC9 (transparency za QA gate).

Refs:
- 2-7-product-detail-strana.md (AC9 + Subtask 11.x + 12.4 + SM-D18)
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="manual smoke per AC9 — Dev izvršava Lighthouse audit lokalno; ne automatizujemo")
def test_lighthouse_a11y_score_above_95_manual_placeholder():
    """AC9: Lighthouse a11y skor ≥ 95 (manuelni Dev smoke check).

    Dev verifikuje:
    - Hero sekcija renderuje (brand logo + naziv + bullets + watermark + responzivan na 375px)
    - Opis sekcija renderuje sa linebreaks filter (paragrafima razdvojen)
    - Galerija karusel renderuje sa <picture> srcset + GLightbox modal otvori na klik
    - Akordion 4 sekcije (Motor open default + +/- toggle + empty section skip)
    - Brošure card sa cover thumbnail + size label + PDF download CTA
    - Slični modeli FR-20 hibrid (manual override + auto fallback paths)
    - Testimonijali slider (auto-advance + pause na fokus + lightbox-open event pause)
    - Variants selektor (klik → GLightbox zoom, bez state change/URL change/form submit)
    - prefers-reduced-motion respect (DevTools Rendering panel toggle)
    - Single h1 verifikacija (`document.querySelectorAll('h1').length === 1`)
    - Lighthouse CLI: a11y ≥ 95, performance ≥ 75, SEO ≥ 90

    JSON artifact: `_bmad-output/implementation-artifacts/2-7-lighthouse-YYYYMMDD.json`

    Ovaj test je xfail-marked — neće blokirati CI, ali tally u test count
    reflektuje AC9 obavezu (QA gate transparency).
    """
    # Manual smoke = NIJE automatable; tačno tu se za sada zaustavlja
    raise NotImplementedError(
        "AC9 manual Lighthouse smoke — Dev/Mihas izvršava lokalno per AC9 checklist + "
        "Subtask 11.1-11.9; rezultati u Dev Agent Record § Completion Notes."
    )

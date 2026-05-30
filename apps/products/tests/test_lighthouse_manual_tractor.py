"""Story 2.8 — AC9 manual Lighthouse audit placeholder (1 xfail test).

Subtask 9.7: AC9 je MANUELNI smoke check (Dev izvršava lokalno + Lighthouse CLI).
Automated tests cover AC1-AC8 programmatic requirements; Lighthouse a11y ≥ 95 +
prefers-reduced-motion + slider keyboard navigation + NVDA aria-live verification
su **out-of-scope za TEA/Dev automation** (Story 9.8 Playwright UJ-1 + Story 9.9
a11y audit-gate scope).

Ovaj fajl drži 1 `xfail`-marked test kao placeholder za AC9 manual smoke compliance.
Test će uvek `xfail` jer ne moramo automatizovati manual smoke; svrha je da TEA tally
testova uključuje AC9 (transparency za QA gate).

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC9 + Subtask 9.7)
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="manual smoke per AC9 — Dev izvršava Lighthouse audit lokalno; ne automatizujemo")
def test_lighthouse_a11y_score_above_95_manual_placeholder():
    """AC9: Lighthouse a11y skor ≥ 95 (manuelni Dev smoke check).

    Dev verifikuje:
    - Brand header renderuje SVE brendove sa is_coming_soon=False kao klikabilne logo-e;
      klik vodi na Story 2.6 brands:detail; brand bez logo-a renderuje text fallback
    - Page heading je TAČNO 1 `<h1>` ('Traktori')
    - Filter form renderuje 2 range slidera (Snaga + Cena) sa min/max thumb-ovima
    - HTMX swap radi: pomeranje slider-a → 300ms debounce → spinner se pojavi → grid se
      ažurira (BEZ full page reload); aria-live region najavi novi count („Pronađeno 12 modela")
    - URL push: posle slider change, URL u browser-u sadrži query params; copy link otvara
      novi tab sa istom filtriranom listom
    - Empty state markup + RESETUJ FILTERE CTA pri 0 rezultata
    - RESETUJ FILTERE CTA: full reload na `/sr/traktori/`
    - Filter restore na reload (SR3 4 scenarija)
    - Browser back-button posle filter promene (HIST fix — historyRestore JS)
    - Keyboard navigation: Tab kroz slider thumb + arrow keys
    - prefers-reduced-motion: reduce respect (DevTools Rendering panel toggle)
    - Single h1 + single main DOM verifikacija
    - Lighthouse CLI: a11y ≥ 95, performance ≥ 75, SEO ≥ 90

    JSON artifact: `_bmad-output/implementation-artifacts/2-8-lighthouse-YYYYMMDD.json`

    Ovaj test je xfail-marked — neće blokirati CI, ali tally u test count
    reflektuje AC9 obavezu (QA gate transparency).
    """
    raise NotImplementedError(
        "AC9 manual Lighthouse smoke — Dev/Mihas izvršava lokalno per AC9 checklist + "
        "Subtask 9.7; rezultati u Dev Agent Record § Completion Notes."
    )

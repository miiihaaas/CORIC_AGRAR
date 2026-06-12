"""Story 9.10 — Lighthouse hard-gate + conversion command + audit sign-off (RED, TEA).

Import-light: json parse `lighthouserc.json`, yaml parse `lighthouse.yml`, pathlib+re
parse command source + AUDIT-REPORT. NE Lighthouse run, NE Docker, NE Django registry.

Pokreni:
    python -m pytest tests/test_lighthouse_gate_9_10.py -p no:django -q

RED: best-practices/seo asserti fale; lighthouse.yml autorun još ima continue-on-error;
convert_static_images command ne postoji; AUDIT-REPORT nema final sign-off. (RED korektan.)

Pokriva: AC5, AC6, AC7, AC10 (+ varijante size/format co-located file-stat AC1/AC8).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
LIGHTHOUSERC = REPO_ROOT / "lighthouserc.json"
LIGHTHOUSE_YML = REPO_ROOT / ".github" / "workflows" / "lighthouse.yml"
CONVERT_CMD = (
    REPO_ROOT
    / "apps"
    / "media_pipeline"
    / "management"
    / "commands"
    / "convert_static_images.py"
)
AUDIT_REPORT = REPO_ROOT / "ops" / "quality" / "AUDIT-REPORT.md"
STATIC_HOME = REPO_ROOT / "static" / "img" / "home"
JPG = STATIC_HOME / "home-hero-1.jpg"
AVIF = STATIC_HOME / "home-hero-1.avif"
WEBP = STATIC_HOME / "home-hero-1.webp"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def lighthouserc() -> dict:
    """Parsiran lighthouserc.json. Fail-uje ako fajl ne postoji."""
    if not LIGHTHOUSERC.exists():
        pytest.fail(f"Missing required file: {LIGHTHOUSERC}")
    return json.loads(LIGHTHOUSERC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lighthouse_yml() -> dict:
    """Parsiran lighthouse.yml. Fail-uje ako fajl ne postoji."""
    if not LIGHTHOUSE_YML.exists():
        pytest.fail(f"Missing required file: {LIGHTHOUSE_YML}")
    return yaml.safe_load(LIGHTHOUSE_YML.read_text(encoding="utf-8"))


def _assertions(rc: dict) -> dict:
    return rc.get("ci", {}).get("assert", {}).get("assertions", {})


def _all_steps(yml: dict) -> list[dict]:
    steps: list[dict] = []
    for job in (yml.get("jobs", {}) or {}).values():
        if isinstance(job, dict):
            for s in job.get("steps", []) or []:
                if isinstance(s, dict):
                    steps.append(s)
    return steps


def _step_by_name_contains(yml: dict, needle: str) -> dict | None:
    for s in _all_steps(yml):
        if needle.lower() in str(s.get("name", "")).lower():
            return s
    return None


# =============================================================================
# AC6 — lighthouserc.json: best-practices + seo dodato, 4 postojeća očuvana
# =============================================================================


def test_lighthouserc_has_best_practices_assert(lighthouserc):
    """AC6: categories:best-practices assert dodat sa minScore >= 0.90."""
    a = _assertions(lighthouserc)
    bp = a.get("categories:best-practices")
    assert bp is not None, (
        "lighthouserc.json NEMA 'categories:best-practices' assert (Task 4.1). RED."
    )
    assert isinstance(bp, list) and bp[0] == "error", (
        f"'categories:best-practices' mora biti ['error', {{...}}], dobijeno {bp!r}"
    )
    min_score = bp[1].get("minScore") if len(bp) > 1 and isinstance(bp[1], dict) else None
    assert min_score == 0.90, (
        f"'categories:best-practices' minScore = {min_score!r}, ocekivano 0.90."
    )


def test_lighthouserc_has_seo_assert(lighthouserc):
    """AC6: categories:seo assert dodat sa minScore >= 0.95."""
    a = _assertions(lighthouserc)
    seo = a.get("categories:seo")
    assert seo is not None, (
        "lighthouserc.json NEMA 'categories:seo' assert (Task 4.1). RED."
    )
    assert isinstance(seo, list) and seo[0] == "error", (
        f"'categories:seo' mora biti ['error', {{...}}], dobijeno {seo!r}"
    )
    min_score = seo[1].get("minScore") if len(seo) > 1 and isinstance(seo[1], dict) else None
    assert min_score == 0.95, (
        f"'categories:seo' minScore = {min_score!r}, ocekivano 0.95."
    )


def test_lighthouserc_preserves_existing_four_asserts(lighthouserc):
    """AC6: postojeća 4 asserta (a11y/LCP/TTFB/total-byte) NETAKNUTA."""
    a = _assertions(lighthouserc)
    expected = {
        "categories:accessibility": ("minScore", 0.95),
        "largest-contentful-paint": ("maxNumericValue", 2500),
        "server-response-time": ("maxNumericValue", 600),
        "total-byte-weight": ("maxNumericValue", 1572864),
    }
    for key, (param, value) in expected.items():
        rule = a.get(key)
        assert rule is not None, (
            f"lighthouserc.json izgubio postojeci assert '{key}' (NE diraj 4 postojeća). "
        )
        assert rule[0] == "error", f"'{key}' mora biti ['error', ...], dobijeno {rule!r}"
        assert rule[1].get(param) == value, (
            f"'{key}' {param} = {rule[1].get(param)!r}, ocekivano {value}."
        )


def test_lighthouserc_collect_urls_unchanged(lighthouserc):
    """AC6: collect.url lista (5 URL-ova) + numberOfRuns:3 NETAKNUTI."""
    collect = lighthouserc.get("ci", {}).get("collect", {})
    urls = collect.get("url", [])
    assert isinstance(urls, list) and len(urls) == 5, (
        f"collect.url mora ostati lista od 5 URL-ova, dobijeno {len(urls) if isinstance(urls, list) else urls!r}."
    )
    assert collect.get("numberOfRuns") == 3, (
        f"collect.numberOfRuns = {collect.get('numberOfRuns')!r}, ocekivano 3."
    )


def test_lighthouserc_is_valid_json():
    """AC6/Task 4.3: lighthouserc.json je parse-able JSON."""
    if not LIGHTHOUSERC.exists():
        pytest.fail(f"Missing required file: {LIGHTHOUSERC}")
    try:
        json.loads(LIGHTHOUSERC.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"lighthouserc.json nije valid JSON: {exc}")


# =============================================================================
# AC7 — lighthouse.yml: autorun korak ENFORCED; axe korak zadržava continue-on-error
# =============================================================================


def test_lighthouse_autorun_step_no_continue_on_error(lighthouse_yml):
    """AC7: 'Lighthouse CI autorun' korak NEMA continue-on-error: true (gate ENFORCED)."""
    step = _step_by_name_contains(lighthouse_yml, "Lighthouse CI autorun")
    assert step is not None, (
        "Nije pronadjen step sa name koji sadrži 'Lighthouse CI autorun'."
    )
    coe = step.get("continue-on-error")
    assert coe is not True, (
        f"'Lighthouse CI autorun' korak JOŠ ima continue-on-error: {coe!r}. "
        f"9.10 Task 5.1: ukloni → budget miss SADA obara job (ENFORCED). RED."
    )


def test_axe_run_at_least_once_keeps_continue_on_error(lighthouse_yml):
    """AC7 (negativna): axe 'run-at-least-once' korak ZADRŽAVA continue-on-error (NE diraj)."""
    step = _step_by_name_contains(lighthouse_yml, "run-at-least-once")
    assert step is not None, (
        "Nije pronadjen axe 'run-at-least-once' korak (mora ostati netaknut)."
    )
    assert step.get("continue-on-error") is True, (
        f"axe 'run-at-least-once' korak MORA zadržati continue-on-error: true "
        f"(a11y je već u Lighthouse categories:accessibility assertu; ne dupliraj). "
        f"Dobijeno: {step.get('continue-on-error')!r}"
    )


def test_lighthouse_yml_is_valid_yaml():
    """AC7/Task 5.4: lighthouse.yml je valid YAML."""
    if not LIGHTHOUSE_YML.exists():
        pytest.fail(f"Missing required file: {LIGHTHOUSE_YML}")
    try:
        yaml.safe_load(LIGHTHOUSE_YML.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        pytest.fail(f"lighthouse.yml nije valid YAML: {exc}")


def test_lighthouse_yml_trigger_unchanged(lighthouse_yml):
    """AC7: on.push.branches:[staging] + workflow_dispatch NETAKNUTI (gate ne crveni master PR)."""
    on_block = lighthouse_yml.get(True, lighthouse_yml.get("on", {}))
    push_branches = (on_block.get("push", {}) or {}).get("branches", [])
    assert "staging" in push_branches, (
        f"on.push.branches mora ostati [staging], dobijeno {push_branches!r}."
    )
    assert "workflow_dispatch" in on_block, (
        "on.workflow_dispatch mora ostati prisutan."
    )


# =============================================================================
# AC5 — convert_static_images management command: postoji + guard-ovi u source-u
# =============================================================================


def test_convert_command_file_exists():
    """AC5: management command postoji na contract path-u."""
    assert CONVERT_CMD.exists(), (
        f"Konverzioni command ne postoji: {CONVERT_CMD}. "
        f"9.10 Task 1.1: kreiraj convert_static_images management command. RED."
    )


def test_convert_command_has_pil_features_guard():
    """AC5: command source koristi PIL.features.check('avif')/('webp') guard (fail-loud)."""
    if not CONVERT_CMD.exists():
        pytest.fail(f"Konverzioni command ne postoji: {CONVERT_CMD} (RED).")
    src = CONVERT_CMD.read_text(encoding="utf-8")
    assert "features.check" in src or "check('avif')" in src or 'check("avif")' in src, (
        "Command MORA imati PIL.features.check('avif')/('webp') guard "
        "(fail-loud ako format nedostaje, NE tiho preskoči)."
    )
    assert "avif" in src.lower() and "webp" in src.lower(), (
        "Command MORA referencirati i avif i webp format."
    )


def test_convert_command_has_size_guard_and_allow_larger():
    """AC1/AC5: command ima size-guard (>= source fail-loud) + --allow-larger override flag."""
    if not CONVERT_CMD.exists():
        pytest.fail(f"Konverzioni command ne postoji: {CONVERT_CMD} (RED).")
    src = CONVERT_CMD.read_text(encoding="utf-8")
    assert "allow-larger" in src or "allow_larger" in src, (
        "Command MORA imati --allow-larger override flag (size-guard escape, AC1). "
        "Bez override-a varijanta >= source-a se NE komituje."
    )


def test_convert_command_has_skip_if_exists_and_force():
    """AC5: idempotency = skip-if-exists + --force regen flag (NE bit-reproducibilnost)."""
    if not CONVERT_CMD.exists():
        pytest.fail(f"Konverzioni command ne postoji: {CONVERT_CMD} (RED).")
    src = CONVERT_CMD.read_text(encoding="utf-8")
    assert re.search(r"add_argument\([^)]*--force", src, re.DOTALL), (
        "Command MORA --force flag ZAISTA ožičiti preko add_argument(...--force...) "
        "(ne samo pomenuti reč 'force' u komentaru/docstring-u)."
    )
    assert re.search(r"exists|skip", src, re.IGNORECASE), (
        "Command MORA imati skip-if-exists idempotency logiku (exists()/skip wording)."
    )


# =============================================================================
# AC10 — AUDIT-REPORT.md final sign-off
# =============================================================================


def test_audit_report_exists():
    """AC10: ops/quality/AUDIT-REPORT.md postoji."""
    assert AUDIT_REPORT.exists(), f"Missing required file: {AUDIT_REPORT}"


def _signoff_section(text: str) -> str | None:
    """Vrati telo NOVE final sign-off sekcije (heading pominje 'Final Lighthouse' /
    'sign-off' / 'signoff'), DISTINKTNO od postojeće '(e) NOTE za 9.10' deferral note.

    Vraća None ako takva sekcija ne postoji. Postojeća '(e) NOTE za 9.10'
    (scope-defer) heading se EKSPLICITNO ne računa kao sign-off (NE pominje
    'Final Lighthouse'/'sign-off' — samo 'NOTE za 9.10').
    """
    lines = text.splitlines()
    heading_idxs = [
        i for i, ln in enumerate(lines) if re.match(r"^#{1,6}\s", ln)
    ]
    for pos, i in enumerate(heading_idxs):
        h = lines[i].lower()
        is_signoff = (
            "final lighthouse" in h or "sign-off" in h or "signoff" in h
        )
        # "(e) NOTE za 9.10" sadrži '9.10' ali NIJE sign-off — preskoči je.
        if not is_signoff:
            continue
        end = heading_idxs[pos + 1] if pos + 1 < len(heading_idxs) else len(lines)
        return "\n".join(lines[i:end])
    return None


def test_audit_report_has_final_signoff_section():
    """AC10: AUDIT-REPORT.md ima NOVU final sign-off sekciju (distinktna od (e) NOTE deferral).

    Postojeća '(e) NOTE za 9.10 (scope-defer)' sekcija NE računa se — sign-off je
    nova sekcija (Task 6.1, npr. '(g) Final Lighthouse pass / sign-off') koja MORA
    dokumentovati ENFORCED gate. RED: nova sekcija još ne postoji.
    """
    if not AUDIT_REPORT.exists():
        pytest.fail(f"Missing required file: {AUDIT_REPORT}")
    text = AUDIT_REPORT.read_text(encoding="utf-8")
    section = _signoff_section(text)
    assert section is not None, (
        "AUDIT-REPORT.md NEMA NOVU final sign-off sekciju (heading 'Final Lighthouse' / "
        "'sign-off'). Postojeća '(e) NOTE za 9.10' deferral note se NE računa. Task 6.1. RED."
    )
    assert re.search(r"enforced", section, re.IGNORECASE), (
        "Final sign-off sekcija MORA dokumentovati da je Lighthouse gate ENFORCED."
    )


def _note_e_section(text: str) -> str | None:
    """Vrati telo postojeće '(e) NOTE za 9.10' deferral sekcije (heading sadrži '(e)'
    i 'NOTE za 9.10'). Vraća None ako ne postoji."""
    lines = text.splitlines()
    heading_idxs = [i for i, ln in enumerate(lines) if re.match(r"^#{1,6}\s", ln)]
    for pos, i in enumerate(heading_idxs):
        h = lines[i].lower()
        if "(e)" in h and "note za 9.10" in h:
            end = heading_idxs[pos + 1] if pos + 1 < len(heading_idxs) else len(lines)
            return "\n".join(lines[i:end])
    return None


def test_audit_report_note_e_resolved():
    """AC10: '(e) NOTE za 9.10' deferral sekcija je MARKIRANA kao razrešena (DONE) u 9.10.

    Implementacija ima inline '✅ DONE u 9.10' marker u (e) sekciji, ali nijedan
    test ga ne čuva. Ovaj test guarduje da (e) NOTE eksplicitno beleži razrešenje
    (DONE/resolved marker u blizini '9.10', ili referenca na (g) sign-off sekciju).
    Tolerantno na tačan tekst — asertuje da resolution marker POSTOJI.
    """
    if not AUDIT_REPORT.exists():
        pytest.fail(f"Missing required file: {AUDIT_REPORT}")
    text = AUDIT_REPORT.read_text(encoding="utf-8")
    section = _note_e_section(text)
    assert section is not None, (
        "AUDIT-REPORT.md NEMA '(e) NOTE za 9.10' sekciju — ne mogu proveriti razrešenje."
    )
    sect = section.lower()
    # DONE/resolved/razrešen marker u (e) sekciji...
    has_done_marker = bool(
        re.search(r"\bdone\b|resolved|razre[sš]en|sign-off", sect)
    )
    # ...vezan za 9.10 (referenca na story / sign-off sekciju).
    references_910 = "9.10" in sect or "(g)" in sect
    assert has_done_marker and references_910, (
        "'(e) NOTE za 9.10' sekcija MORA biti markirana kao razrešena u 9.10 "
        "(npr. '✅ DONE u 9.10' ili referenca na (g) Final Lighthouse sign-off). "
        f"has_done_marker={has_done_marker}, references_910={references_910}."
    )


def test_audit_report_records_task3_outcome():
    """AC10: sign-off sekcija eksplicitno beleži Task 3 ishod (responsive_picture WebP: impl/deferred).

    Provera je u OKVIRU nove sign-off sekcije (NE u staroj (e) NOTE koja već pominje
    responsive_picture+DEFERRED) — named-condition, NE tiho preskoči.
    """
    if not AUDIT_REPORT.exists():
        pytest.fail(f"Missing required file: {AUDIT_REPORT}")
    text = AUDIT_REPORT.read_text(encoding="utf-8")
    section = _signoff_section(text)
    if section is None:
        pytest.fail(
            "Nema final sign-off sekcije — Task 3 ishod ne može biti zabeležen. RED."
        )
    sect = section.lower()
    mentions_rp = "responsive_picture" in sect or "responsive picture" in sect
    mentions_outcome = (
        "deferred" in sect or "implementiran" in sect or "implemented" in sect
    )
    assert mentions_rp and mentions_outcome, (
        "Final sign-off sekcija MORA eksplicitno zabeležiti Task 3 ishod "
        "(responsive_picture WebP source: IMPLEMENTIRAN ILI DEFERRED)."
    )


# =============================================================================
# AC1/AC8 — co-located variant size + format file-stat (drugi vektor pristupa)
# =============================================================================


def test_variants_exist_and_smaller_than_jpg():
    """AC1: .avif + .webp postoje I STRIKTNO manji od .jpg (os.stat) — co-located guard."""
    if not JPG.exists():
        pytest.fail(f"Source JPG ne postoji: {JPG}.")
    missing = [p.name for p in (AVIF, WEBP) if not p.exists()]
    assert not missing, (
        f"Varijante ne postoje: {missing}. 9.10 Task 1.3: generiši + komituj. RED."
    )
    jpg_size = os.stat(JPG).st_size
    for variant in (AVIF, WEBP):
        vsize = os.stat(variant).st_size
        assert vsize < jpg_size, (
            f"{variant.name} ({vsize} B) MORA biti STRIKTNO manji od JPG ({jpg_size} B). AC1."
        )


def test_variants_format_correct():
    """AC8: PIL format AVIF/WEBP ispravan (hvata bytes-na-pogrešnoj-ekstenziji mismatch)."""
    missing = [p.name for p in (AVIF, WEBP) if not p.exists()]
    if missing:
        pytest.fail(f"Varijante ne postoje: {missing} (RED — Task 1.3).")
    from PIL import Image

    with Image.open(AVIF) as im:
        assert im.format == "AVIF", f"{AVIF.name} format = {im.format!r}, mora 'AVIF'."
    with Image.open(WEBP) as im:
        assert im.format == "WEBP", f"{WEBP.name} format = {im.format!r}, mora 'WEBP'."

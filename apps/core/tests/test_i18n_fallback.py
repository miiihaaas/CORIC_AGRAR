"""Story 6.5 — {% translated_field obj 'field' %} i18n fallback marker tag (TEA RED).

PETA story Epic 6 (SEO & Discoverability). JEDAN deliverable: NOVI
`apps/core/templatetags/i18n_fallback.py` sa `{% translated_field obj 'name' %}`
`simple_tag(takes_context=True)` koji DETEKTUJE da li je translated polje fallback-ovano
na sr za aktivnu locale i — ako jeste — renderuje diskretan `coric-fallback-marker`
span (sr tekst + inline ⓘ SVG + CSS-only tooltip „Sadržaj na srpskom — još nije
preveden", lokalizovan), sa `lang="sr"` atributom na fallback tekstu.

CRUX (SM-D1, G1): fallback se NE detektuje kroz `obj.field` (jer
`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` čini da `obj.name` na /hu/ VEĆ tiho
vrati sr vrednost). Tag MORA čitati SIROVI per-locale accessor
`getattr(obj, f"{field}_{lang}", _UNSET)` i testirati da li je TA kolona prazna.

⚠️ {% load i18n_fallback %} fail-uje pri render-u sa TemplateSyntaxError
('i18n_fallback' is not a registered tag library) dok Dev ne kreira
apps/core/templatetags/i18n_fallback.py = TAČAN RED razlog. {% load %} je UNUTAR
test body-ja (lazy) → čist per-test FAIL, NE collection-abort.

HTML parsing: regex (NIKAD BeautifulSoup — project-context). Render kroz Template +
Context sa request (per-request id counter `request._coric_fallback_counter`).

Refs:
- 6-5-i18n-fallback-marker-tooltip.md AC1-AC7 + Tasks 1-3 + SM-D1..D7 + G1..G10
  + Testing #1..#13, #16
- 6-5-interface-contract.md § templatetags/i18n_fallback.py
- apps/seo/templatetags/seo_meta.py (_display_title duck-typing + format_html pattern)
"""

from __future__ import annotations

import re

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


# ── Render helpers ────────────────────────────────────────────────────────────

# Match-id pattern shared by all id/aria assertions (AC3 — pattern, NE hardkodiran).
_TOOLTIP_ID_RE = re.compile(r"fallback-tooltip-\d+")
_MARKER_CLASS = 'class="coric-fallback-marker"'


def _render(template_string: str, ctx: dict, *, request=None) -> str:
    """Render template string sa request u contextu (per-request id counter).

    request=None → kreiraj svež RequestFactory().get("/") (HTTP context za counter).
    Prosleđen request → deli per-request counter kroz više render-a (test #8).
    """
    if request is None:
        request = RequestFactory().get("/")
    context = Context({**ctx, "request": request})
    return Template(template_string).render(context)


def _render_field(obj, field: str, locale: str, *, request=None) -> str:
    """Convenience: activate locale + render `{% translated_field obj field %}`."""
    activate(locale)
    try:
        return _render(
            "{% load i18n_fallback %}{% translated_field obj '" + field + "' %}",
            {"obj": obj},
            request=request,
        )
    finally:
        activate("sr")


# ── Lightweight duck-typed stub (tag duck-tipuje — NE import modeltranslation) ──


class _FieldStub:
    """Plain objekat sa per-locale accessor-ima (`name_sr/_hu/_en`) + rešena `name`.

    Mirror modeltranslation surface BEZ DB: tag čita `getattr(obj, f"name_{lang}")`
    (per-locale kolona) i `getattr(obj, "name")` (rešena vrednost). Ovaj stub dozvoljava
    da unit-testovi izoluju detekciju bez Product/Post DB round-trip-a; integration
    testovi (#14b/#14c) koriste realni Product preko URL routing-a.

    `name` (rešena) simulira modeltranslation fallback: vrati `_<lang>` ako popunjen,
    inače `_sr` (silent fallback — to je CRUX koji tag NE sme da koristi za detekciju).
    """

    def __init__(self, *, sr="", hu="", en="", field="name"):
        self._field = field
        setattr(self, f"{field}_sr", sr)
        setattr(self, f"{field}_hu", hu)
        setattr(self, f"{field}_en", en)

    def __getattr__(self, item):
        # Rešena vrednost `name` (bez suffiksa) = modeltranslation fallback chain.
        # __getattr__ se zove SAMO za atribute koji ne postoje kao instance attr —
        # per-locale `name_sr/_hu/_en` su set-ovani u __init__ pa NE prolaze ovuda.
        if item == self._field:
            from django.utils.translation import get_language

            lang = (get_language() or "sr").split("-")[0]
            per_locale = self.__dict__.get(f"{item}_{lang}", "")
            if per_locale:
                return per_locale
            return self.__dict__.get(f"{item}_sr", "")
        raise AttributeError(item)


# =============================================================================
# AC1 — Detekcija kroz per-locale accessor (NE obj.field)
# =============================================================================


# AC1: sr locale → NIKAD marker (sr je izvor)
def test_no_marker_on_sr_locale():
    """#1 — `activate("sr")`, objekat sa praznim name_hu → plain name_sr, NEMA markera."""
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "sr")
    assert "Agri-Tracking TB804" in out, (
        "Na /sr/ tag MORA vratiti plain name_sr vrednost (sr je izvorni jezik)."
    )
    assert "coric-fallback-marker" not in out, (
        "Na /sr/ tag NIKAD ne sme renderovati marker (sr je izvor, nema fallback-a; AC1)."
    )


# AC1/AC2: hu locale + prazan name_hu → MARKER sa sr tekstom + lang="sr" + <svg
def test_marker_when_locale_field_empty():
    """#2 — `activate("hu")`, name_sr popunjen, name_hu prazan → marker."""
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "hu")
    assert _MARKER_CLASS in out, (
        "Na /hu/ sa praznim name_hu (a popunjenim name_sr) → MORA renderovati "
        'class="coric-fallback-marker" (fallback detektovan kroz name_hu=="" ; AC1/AC2).'
    )
    assert "Agri-Tracking TB804" in out, (
        "Marker MORA sadržati sr fallback tekst (name_sr), NE prazan string (AC2)."
    )
    assert 'lang="sr"' in out, (
        'Fallback tekst MORA imati lang="sr" (WCAG 3.1.2 Language of Parts; AC2).'
    )
    assert "<svg" in out, (
        "Marker MORA sadržati inline <svg> ⓘ ikonu (NE bi-info-circle klasu; SM-D5/AC2)."
    )


# AC1: hu locale + popunjen name_hu → NO marker, plain hu vrednost
def test_no_marker_when_locale_field_populated():
    """#3 — `activate("hu")`, name_hu="Traktor" → plain „Traktor", NEMA markera."""
    obj = _FieldStub(sr="Tractor SR", hu="Traktor")
    out = _render_field(obj, "name", "hu")
    assert "Traktor" in out, (
        "Sa popunjenim name_hu tag MORA vratiti hu vrednost (NEMA fallback-a; AC1)."
    )
    assert "coric-fallback-marker" not in out, (
        "Sa popunjenim name_hu NEMA fallback-a → NE sme biti markera (AC1)."
    )


# AC1/G1 — CRUX: detekcija čita name_<lang> accessor, NE obj.name==name_sr
def test_detection_uses_per_locale_accessor_not_resolved():
    """#4 — KONKLUZIVAN dokaz: signal je „je li name_hu PRAZNA", NE „obj.name==name_sr".

    (a) name_sr="X", name_hu="X" (oba popunjena, slučajno identična) → NEMA markera
        (da algoritam poredi obj.name==name_sr, LAŽNO bi markirao jer obj.name==name_sr).
    (b) name_sr="X", name_hu="" (hu prazan) → MARKER (per-locale kolona prazna).
    Par (a)+(b) dokazuje per-locale-accessor detekciju (G1).
    """
    # (a) hu == sr (identičan validan prevod) → name_hu popunjen → NEMA markera
    obj_a = _FieldStub(sr="Univerzal", hu="Univerzal")
    out_a = _render_field(obj_a, "name", "hu")
    assert "coric-fallback-marker" not in out_a, (
        "name_hu POPUNJEN (čak i ako == name_sr) → NEMA markera. Da algoritam poredi "
        "obj.name==name_sr, ovde bi LAŽNO markirao (G1 — to je zabranjeni test)."
    )

    # (b) name_hu prazan → MARKER (jedini ispravan signal: prazna per-locale kolona)
    obj_b = _FieldStub(sr="Univerzal", hu="")
    out_b = _render_field(obj_b, "name", "hu")
    assert _MARKER_CLASS in out_b, (
        "name_hu PRAZAN + name_sr popunjen → MORA marker (per-locale kolona prazna = "
        "fallback; AC1/G1)."
    )


# AC1/G9 — BCP-47 region locale normalizacija (en-us → en)
def test_bcp47_region_locale_resolves_to_base():
    """#4b — `activate("en-us")`, name_en prazan → MARKER (en-us→en normalizacija).

    Bez `.split("-")[0]` normalizacije, accessor `name_en-us` UVEK promaši (_UNSET) →
    marker se TIHO nikad ne pojavi za engleski (najgori silent-failure; G9).
    """
    obj = _FieldStub(sr="Serbian text", en="")
    out = _render_field(obj, "name", "en-us")
    assert _MARKER_CLASS in out, (
        "activate('en-us') + prazan name_en → tag MORA normalizovati en-us→en, čitati "
        "name_en (prazan) → MARKER. Bez normalizacije name_en-us promaši → nema markera "
        "(G9 silent-failure)."
    )
    assert "Serbian text" in out, "Marker MORA nositi sr fallback tekst (AC1/AC2)."


# G7 — whitespace-only prevod = prazno → fallback
def test_whitespace_only_treated_as_empty():
    """#5 — name_hu="   " na /hu/ → marker (whitespace nije validan prevod; G7)."""
    obj = _FieldStub(sr="Pravi naziv", hu="   ")
    out = _render_field(obj, "name", "hu")
    assert _MARKER_CLASS in out, (
        'name_hu="   " (samo whitespace) NIJE validan prevod → MORA pasti na fallback '
        "(marker). str(current).strip() ga tretira kao prazno (G7)."
    )
    assert "Pravi naziv" in out, "Marker nosi sr tekst (G7)."


# =============================================================================
# AC7 — Security: XSS escape + graceful edge-cases
# =============================================================================


# AC7: vrednost polja autoescaped (NEMA XSS)
def test_xss_field_value_escaped():
    """#6 — name_sr="<script>...", name_hu="" na /hu/ → &lt;script&gt;, NE izvršni tag."""
    obj = _FieldStub(sr="<script>alert(1)</script>", hu="")
    out = _render_field(obj, "name", "hu")
    assert "&lt;script&gt;" in out, (
        "sr fallback tekst MORA biti HTML-escaped (&lt;script&gt;) kroz format_html "
        "autoescape (AC7)."
    )
    assert "<script>alert(1)</script>" not in out, (
        "Sirov <script> NE sme procureti u izlaz (XSS granica — NIKAD |safe na obj "
        "content; AC7)."
    )


# AC7: obj=None → graceful (prazan/plain, NE 500)
def test_graceful_obj_none():
    """#10 — translated_field(ctx, None, "name") → prazan/plain string, NE 500."""
    activate("hu")
    try:
        out = _render(
            "{% load i18n_fallback %}{% translated_field obj 'name' %}",
            {"obj": None},
        )
    finally:
        activate("sr")
    assert "coric-fallback-marker" not in out, (
        "obj=None → graceful prazan/plain, NIKAD marker (AC7)."
    )
    # Eksplicitno: obj=None → tag vraća "" (NE 'None' literal, NE bilo kakav markup).
    assert out.strip() == "", (
        f"obj=None render MORA biti prazan string (tag vraća ''; AC7). Pronađeno: {out!r}"
    )


# AC1/AC7: ne-translated polje (nema _<lang> accessor) → graceful plain, NE 500
def test_graceful_nonexistent_field():
    """#11 — objekat bez slug_hu accessora → plain obj.slug, NE 500 (AC1/AC7).

    Stub ima `slug` ali NEMA `slug_hu`/`slug_sr` (ne-translated) → getattr → _UNSET
    → tag tretira kao „popunjeno" (graceful) → plain `obj.slug`, NE marker, NE crash.
    """

    class _NonTranslated:
        slug = "agri-tracking-tb804"

    obj = _NonTranslated()
    activate("hu")
    try:
        out = _render(
            "{% load i18n_fallback %}{% translated_field obj 'slug' %}",
            {"obj": obj},
        )
    finally:
        activate("sr")
    assert "coric-fallback-marker" not in out, (
        "Ne-translated polje (nema slug_hu accessor → _UNSET) → graceful plain, "
        "NIKAD marker (AC1/AC7)."
    )
    assert "agri-tracking-tb804" in out, (
        "Ne-translated polje → plain obj.slug vrednost (graceful, NE 500; AC1/AC7)."
    )


# AC1: name_sr="" i name_hu="" → plain (nema teksta za markirati), NEMA markera
def test_graceful_no_sr_value():
    """#12 — name_sr="" i name_hu="" na /hu/ → plain, NEMA markera (AC1)."""
    obj = _FieldStub(sr="", hu="")
    out = _render_field(obj, "name", "hu")
    assert "coric-fallback-marker" not in out, (
        "Ni name_hu ni name_sr nemaju vrednost → nema teksta za markirati → "
        "plain, NE marker (AC1)."
    )


# =============================================================================
# AC2/AC3 — Markup, a11y atributi, jedinstveni id-evi
# =============================================================================


# AC3: aria-describedby vrednost == tooltip id (PARNOST + PATTERN, NE hardkodirano)
def test_aria_describedby_matches_tooltip_id():
    """#7 — marker render → aria-describedby == tooltip id; oba match-uju pattern."""
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "hu")

    descby = re.search(r'aria-describedby="(fallback-tooltip-\d+)"', out)
    assert descby, (
        'Marker MORA imati aria-describedby="fallback-tooltip-N" (AC2/AC3). Nije '
        f"pronađen u izlazu: {out!r}"
    )
    tooltip_id = re.search(r'role="tooltip"[^>]*\bid="(fallback-tooltip-\d+)"', out) or \
        re.search(r'\bid="(fallback-tooltip-\d+)"[^>]*role="tooltip"', out)
    assert tooltip_id, (
        'Tooltip span MORA imati id="fallback-tooltip-N" + role="tooltip" (AC2/AC3). '
        f"Nije pronađen u izlazu: {out!r}"
    )
    assert descby.group(1) == tooltip_id.group(1), (
        f"aria-describedby ({descby.group(1)!r}) MORA TAČNO match-ovati tooltip id "
        f"({tooltip_id.group(1)!r}) — par (AC3). NE hardkodiramo tačnu vrednost, samo parnost."
    )


# AC3: dva markera u istom request-u → RAZLIČITI id-evi (jedinstvenost + pattern)
def test_unique_ids_for_multiple_markers():
    """#8 — dva fallback render-a u ISTOM request-u → različiti id-evi.

    Asertuj JEDINSTVENOST + `fallback-tooltip-\\d+` pattern + per-marker aria↔id par
    — NE tačne -1/-2 vrednosti (modul-level fallback putanja čini tačnu vrednost
    brittle; AC3/G5).
    """
    obj1 = _FieldStub(sr="Prvi naziv", hu="")
    obj2 = _FieldStub(sr="Drugi naziv", hu="")
    request = RequestFactory().get("/")  # ISTI request → deljen per-request counter

    # locale je sr po default-u → markera ne bi bilo; aktiviramo hu eksplicitno tako da
    # OBA fallback marker-a izađu u istom request-u (deljen per-request counter).
    activate("hu")
    try:
        out = _render(
            "{% load i18n_fallback %}"
            "{% translated_field a 'name' %}{% translated_field b 'name' %}",
            {"a": obj1, "b": obj2},
            request=request,
        )
    finally:
        activate("sr")

    # Sakupi SVE tooltip id-eve iz oba moguća redosleda atributa (role-pre-id i
    # id-pre-role). Po tooltip span-u TAČNO JEDAN od dva pattern-a matchuje (redosled
    # atributa je fiksan u jednom span-u) → NEMA dupliranja iste vrednosti od strane
    # dva regex-a. NE de-dup-ujemo — uniqueness assertion mora videti SIROVU listu
    # (de-dup bi neutralisao proveru kolizije: dva markera sa istim id-em bi se
    # stopila u jedan unos i assertion bi vacuous prošao; AC3/G5).
    ids = re.findall(r'role="tooltip"[^>]*\bid="(fallback-tooltip-\d+)"', out)
    ids += re.findall(r'\bid="(fallback-tooltip-\d+)"[^>]*role="tooltip"', out)
    assert len(ids) >= 2, (
        f"Dva fallback markera MORAJU dati ≥2 tooltip id-eva. Pronađeno: {ids!r} u "
        f"izlazu: {out!r}"
    )
    assert len(set(ids)) == len(ids), (
        f"Tooltip id-evi MORAJU biti JEDINSTVENI (NE kolizija) — pronađeno (sirova "
        f"lista): {ids!r} (AC3/G5 — kolizija lomi aria-describedby asocijaciju; dva "
        "markera sa istim id-em = slomljena SR asocijacija)."
    )
    for id_ in ids:
        assert _TOOLTIP_ID_RE.fullmatch(id_), (
            f"id {id_!r} MORA match-ovati `fallback-tooltip-\\d+` pattern (AC3)."
        )
    # PER-MARKER parnost: svaki marker-ov aria-describedby MORA referencirati id
    # SVOG SOPSTVENOG tooltip span-a (NE set==set — cross-wired impl gde marker A
    # pokazuje na tooltip B bi prošao set-jednakost; AC3/G5). Ekstraktuj (aria, id)
    # par iz SVAKOG markera ponaosob i asertuj jednakost po-paru.
    pairs = re.findall(
        r'<span class="coric-fallback-marker"[^>]*'
        r'aria-describedby="(fallback-tooltip-\d+)"'
        r'.*?<span class="coric-fallback-marker__tooltip"[^>]*'
        r'\bid="(fallback-tooltip-\d+)"',
        out,
        re.DOTALL,
    )
    assert len(pairs) >= 2, (
        f"MORAJU se ekstraktovati ≥2 (aria, id) para iz markera. Pronađeno: {pairs!r} "
        f"u izlazu: {out!r}"
    )
    for aria, tip_id in pairs:
        assert aria == tip_id, (
            f"Marker aria-describedby ({aria!r}) MORA referencirati id SVOG SOPSTVENOG "
            f"tooltip span-a ({tip_id!r}) — par-po-marker, NE cross-wired (AC3/G5)."
        )


# AC3/G5 — request=None fallback putanja (modul-level itertools.count)
def test_unique_ids_without_request_uses_module_counter():
    """#8b — render BEZ request-a u context-u → modul-level itertools.count fallback.

    `_next_tooltip_id` ima dve grane: per-request counter (request u context-u) i
    modul-level `itertools.count(1)` fallback kad request=None (shell / management /
    izolovan render). Ova grana je inače nepokrivena. Render dva markera BEZ request-a
    → MORAJU dobiti JEDINSTVENE id-eve koji match-uju pattern (AC3/G5).
    """
    obj = _FieldStub(sr="Fallback bez request-a", hu="")
    activate("hu")
    try:
        # NAMERNO bez "request" u Context-u → forsira modul-level brojač granu.
        out = Template(
            "{% load i18n_fallback %}"
            "{% translated_field obj 'name' %}{% translated_field obj 'name' %}"
        ).render(Context({"obj": obj}))
    finally:
        activate("sr")

    ids = re.findall(r'\bid="(fallback-tooltip-\d+)"', out)
    assert len(ids) == 2, (
        f"Dva markera BEZ request-a MORAJU dati TAČNO 2 tooltip id-a (modul-level "
        f"brojač grana). Pronađeno: {ids!r} u izlazu: {out!r}"
    )
    assert len(set(ids)) == 2, (
        f"Modul-level itertools.count MORA dati JEDINSTVENE id-eve (NE kolizija); "
        f"pronađeno: {ids!r} (AC3/G5)."
    )
    for id_ in ids:
        assert _TOOLTIP_ID_RE.fullmatch(id_), (
            f"id {id_!r} (request=None grana) MORA match-ovati `fallback-tooltip-\\d+` "
            "pattern (AC3)."
        )


# AC2/SM-D5: ikona je inline <svg> sa aria-hidden + focusable=false, NE bi-* klasa
def test_icon_is_inline_svg_not_bootstrap_class():
    """#13 — izlaz sadrži <svg aria-hidden="true" focusable="false">, NE bi-info-circle."""
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "hu")
    assert "<svg" in out, "Ikona MORA biti inline <svg> (SM-D5)."
    assert 'aria-hidden="true"' in out, (
        'SVG ikona MORA imati aria-hidden="true" (dekorativna; AC2/SM-D5).'
    )
    assert 'focusable="false"' in out, (
        'SVG ikona MORA imati focusable="false" (IE/legacy SVG fokus; AC2/SM-D5).'
    )
    assert "bi-info-circle" not in out, (
        "NE sme koristiti class=\"bi-info-circle\" — Bootstrap Icons NIJE vendirana "
        "→ bio bi nevidljiv prazan element (SM-D5/G3)."
    )


# AC2: tooltip span ima tabindex + role="tooltip" + marker je keyboard-focusable
def test_marker_structure_tabindex_and_role():
    """#16 — marker span ima tabindex="0"; tooltip dete ima role="tooltip" (AC2/a11y)."""
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "hu")
    assert 'tabindex="0"' in out, (
        'Marker MORA imati tabindex="0" (keyboard-focusable za CSS-only tooltip; AC2).'
    )
    assert 'role="tooltip"' in out, (
        'Tooltip span MORA imati role="tooltip" (SR najavljuje opis; AC2).'
    )
    # Tooltip span je DETE markera (UNUTAR .coric-fallback-marker) — NE adjacent sibling.
    # Regex: marker open tag ... tooltip span ... </span></span> (dva zatvaranja na kraju).
    # Dokaz strukture: tooltip <span class="coric-fallback-marker__tooltip" je posle
    # otvaranja .coric-fallback-marker i PRE njegovog zatvaranja (nested).
    marker_block = re.search(
        r'<span class="coric-fallback-marker"[^>]*>.*?'
        r'<span class="coric-fallback-marker__tooltip"[^>]*role="tooltip"[^>]*>'
        r'.*?</span>\s*</span>',
        out,
        re.DOTALL,
    )
    assert marker_block, (
        "Tooltip span MORA biti DETE .coric-fallback-marker (UNUTAR njega, pre "
        "zatvaranja) — NE adjacent sibling. Descendant reveal selektor radi SAMO za "
        f"dete (G4/AC2). Izlaz: {out!r}"
    )


# =============================================================================
# AC4 — Tooltip tekst lokalizovan po visitor locale
# =============================================================================


# AC4: tooltip msgid sa punim dijakritikama prisutan (runtime gettext)
def test_tooltip_text_localized_msgid_present():
    """#9 — tooltip tekst = gettext("Sadržaj na srpskom — još nije preveden").

    Na /sr/ tooltip se ne renderuje (nema markera na sr). Na /hu/ bez kompajliranog
    hu prevoda → sr msgid fallback je prihvatljiv RED-state. Lock-ujemo da je TEKST
    prisutan (msgid sa punim dijakritikama) ILI hu prevod ako .po kompajliran.
    """
    obj = _FieldStub(sr="Agri-Tracking TB804", hu="")
    out = _render_field(obj, "name", "hu")

    sr_msgid = "Sadržaj na srpskom — još nije preveden"
    hu_translation = "A tartalom szerb nyelven — még nincs lefordítva"
    assert (sr_msgid in out) or (hu_translation in out), (
        "Tooltip tekst MORA biti gettext rezultat — ili hu prevod "
        f"({hu_translation!r} ako .po kompajliran) ili sr msgid fallback "
        f"({sr_msgid!r}). Nije pronađen u izlazu: {out!r}"
    )
    # Pune dijakritike u sr msgid (project-context: NIKAD šišana latinica) — verifikuj
    # da, ako je sr msgid prisutan, ima dijakritike (č/š/đ gde treba).
    if sr_msgid in out:
        assert "Sadržaj" in out and "još" in out, (
            "sr msgid MORA imati pune dijakritike (Sadržaj / još) — project-context "
            "anti-šišana-latinica (AC4)."
        )


def _tooltip_text(out: str) -> str | None:
    """Ekstraktuj tekst iz <span ... role="tooltip" ...>TEKST</span> (oba redosleda)."""
    m = re.search(r'role="tooltip"[^>]*>(.*?)</span>', out, re.DOTALL) or re.search(
        r'class="coric-fallback-marker__tooltip"[^>]*>(.*?)</span>', out, re.DOTALL
    )
    return m.group(1).strip() if m else None


# AC4: tooltip tekst reaguje na aktivnu locale po request-u (runtime gettext, NE lazy)
def test_tooltip_text_runtime_per_locale():
    """#9b — render istog objekta pod hu i en → tooltip tekst je TAČAN prevod locale.

    hu/en .po su kompajlirani → pod activate("hu") tooltip MORA biti hu prevod, pod
    activate("en") en prevod. Ekstraktuj tekst tooltip span-a i asertuj tačan match
    (runtime gettext per-request, NE import-cached / lazy; AC4).
    """
    obj_hu = _FieldStub(sr="Agri-Tracking TB804", hu="")
    obj_en = _FieldStub(sr="Agri-Tracking TB804", en="")
    out_hu = _render_field(obj_hu, "name", "hu")
    out_en = _render_field(obj_en, "name", "en")

    assert 'role="tooltip"' in out_hu, (
        "Na /hu/ marker MORA imati tooltip span (runtime gettext per-request; AC4)."
    )
    assert 'role="tooltip"' in out_en, (
        "Na /en/ marker MORA imati tooltip span (runtime gettext per-request; AC4)."
    )

    hu_text = _tooltip_text(out_hu)
    en_text = _tooltip_text(out_en)
    assert hu_text == "A tartalom szerb nyelven — még nincs lefordítva", (
        "Pod activate('hu') tooltip tekst MORA biti TAČAN hu prevod (runtime gettext; "
        f"AC4). Pronađeno: {hu_text!r}"
    )
    assert en_text == "Content in Serbian — not yet translated", (
        "Pod activate('en') tooltip tekst MORA biti TAČAN en prevod (runtime gettext; "
        f"AC4). Pronađeno: {en_text!r}"
    )


# =============================================================================
# Regression guard — 0 model promene
# =============================================================================


# Testing #15: makemigrations --check → No changes detected (0 model promene)
def test_makemigrations_clean():
    """#15 — 6.5 je 0-migration (tag SAMO čita _sr/_hu/_en); makemigrations čist."""
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command(
            "makemigrations", "--check", "--dry-run", stdout=out, stderr=out
        )
        exit_code = 0
    except SystemExit as exc:
        exit_code = exc.code or 0
    assert exit_code == 0, (
        "makemigrations --check --dry-run MORA biti cist (exit 0 / No changes "
        f"detected) — 6.5 je 0-migration. Output: {out.getvalue()!r}"
    )

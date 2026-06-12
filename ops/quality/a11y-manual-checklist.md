# Manuelni A11y checklist — WCAG 2.1 AA (Story 9.9)

**Manuelni go-live gate (OQ-3).** Automatizovani axe (`tests/e2e/test_a11y_audit.py`) pokriva
samo ~30–40% WCAG kriterijuma. Stavke ispod **NE dokazuje axe** — zahtevaju ljudsku proveru
(tastatura, fokus, kontrast, screen-reader). Tester (Mihas ili imenovani) prolazi listu pred
go-live i upisuje rezultat u [`AUDIT-REPORT.md`](./AUDIT-REPORT.md).

- Tester: ______________________   Datum: __________   Browser/OS: ______________________
- Verdikt: ☐ PASS  ☐ PASS sa napomenama  ☐ FAIL (vidi remediation Issue-e)

3 ključna user-journey-ja (UJ) za proveru:
- **UJ-1** — Marko kupuje traktor: `/` → `/sr/traktori/` → filter → `/sr/proizvod/agri-tracking-tb804/` → model-inquiry forma.
- **UJ-2** — Stojan šalje servisni zahtev (MOBILNI): hamburger meni → `/sr/servis/` → forma + upload.
- **UJ-3** — Marijana dodaje proizvod: `/admin-coric/` login → Dodaj proizvod → publish.

---

## (a) Tastatura — Tab navigacija i Esc (WCAG 2.1.1, 2.1.2)

- [ ] **UJ-1** prolazi cео tok **samo tastaturom** (Tab/Shift+Tab/Enter) — svi linkovi, dugmad, slider i polja forme dostupni. Očekivano: ništa nije „zarobljeno", red fokusa je logičan.
- [ ] **UJ-2** prolazi samo tastaturom uključujući otvaranje hamburger menija i upload polje.
- [ ] **UJ-3** admin login + forma prolaze samo tastaturom.
- [ ] **Esc** zatvara: mobilni nav (hamburger collapse), pretragu (search panel), Lightbox galeriju (GLightbox), Bootstrap dropdown „Mehanizacija". Očekivano: fokus se vraća na trigger.
- [ ] **Nema keyboard trap-a** (WCAG 2.1.2) — iz svakog widgeta se može izaći tastaturom.
- [ ] **Vidljiv fokus** (`:focus-visible`) na svim interaktivnim elementima — fokus prsten je jasno vidljiv (WCAG 2.4.7).
- [ ] **Skip-link** „Preskoči na sadržaj" radi (Tab na prvi element → Enter skače na `#main-content`).

## (b) Focus management posle HTMX swap-a (WCAG 2.4.3)

> Project-context #3: focus management posle HTMX swap-a = jedan od najvećih a11y rizika projekta.

- [ ] **Kontakt/model-inquiry forma**: posle submit-a (HTMX outerHTML swap → success kartica), fokus se smisleno premešta na success poruku (`role="status"`) — korisnik tastature/screen-readera ne ostaje „izgubljen" na zamenjenom DOM-u.
- [ ] **Traktori filter** (HTMX innerHTML swap `#tractor-results`): posle filtriranja, red fokusa i dalje ima smisla; nema gubitka fokusa u „prazninu".
- [ ] **Paginacija** (HTMX): posle promene strane, fokus/kontekst je očuvan.
- [ ] **aria-live** announcement (`#aria-live` OOB region) izgovara broj rezultata posle filtera/paginacije.

## (c) prefers-reduced-motion (WCAG 2.3.3)

- [ ] Sa OS podešavanjem **„reduce motion"** uključenim: testimonials slider, statistic counter, hero/scroll animacije, sticky-nav tranzicije se **gase ili svode na minimum**. Očekivano: nema auto-pokretnog/parallax kretanja koje nije isključeno.

## (d) Kontrast 4.5:1 (WCAG 1.4.3)

Spot-check ključnih parova (DESIGN.md / `tokens.css`) alatom (npr. browser DevTools contrast, axe DevTools, ili WebAIM Contrast Checker):

- [ ] Telo teksta na beloj pozadini ≥ **4.5:1**.
- [ ] Beli tekst preko hero foto-pozadine (`coric-home-hero__title` / `__lead`) ≥ **4.5:1** (proveri preko najsvetlijeg dela slike).
- [ ] CTA dugmad (`coric-button--primary`) — tekst vs pozadina ≥ **4.5:1**.
- [ ] Linkovi u footer-u (svetli tekst na tamnoj pozadini) ≥ **4.5:1**.
- [ ] Tekst polja forme / label / placeholder ≥ **4.5:1** (placeholder ≥ 4.5:1 ili ne nosi suštinsku info).
- [ ] Stanje fokusa/hover ne pada ispod 4.5:1.

## (e) NVDA screen-reader prolaz — bar 1 UJ (WCAG 1.3.1, 4.1.2, 4.1.3)

Sa **NVDA** (Windows) proći **najmanje UJ-1** (traktori → model-inquiry):

- [ ] **Heading struktura** — jedan `<h1>` po strani, logična h2/h3 hijerarhija; NVDA heading-navigacija (H) ima smisla.
- [ ] **Form labels** — svako polje forme je najavljeno sa svojom labelom (name/email/message/telefon); nijedno polje nije „bezimeno edit polje".
- [ ] **Greške forme** su najavljene (validaciona poruka vezana za polje).
- [ ] **aria-live announcement** (4.1.3) — posle filtera/submit-a NVDA izgovori promenu (broj rezultata / „upit je primljen").
- [ ] **Ikon-only dugmad** (hamburger, pretraga, social) imaju razumljiv `aria-label` koji NVDA čita (NE „dugme" bez imena).
- [ ] **Slike** — informativne slike imaju smislen `alt`; dekorativne (hero pozadina) su `alt=""`/`aria-hidden` i NVDA ih preskače.
- [ ] **Jezik strane** — `<html lang>` je tačan (sr/hu/en po lokalu) → NVDA koristi pravu glasovnu sintezu.

---

### Napomene / nalazi

> Svaki FAIL → unesi u [`AUDIT-REPORT.md`](./AUDIT-REPORT.md) „fail → GitHub Issue" sekciju
> (strana + WCAG kriterijum + opis + predlog fix-a). „0 critical axe violation" je **nužan ali NE
> dovoljan** uslov za WCAG 2.1 AA — ovaj manuelni prolaz + NVDA su obavezni za AA tvrdnju.

---
title: EXPERIENCE — Ćorić Agrar
status: final
created: 2026-05-27
updated: 2026-05-27
project: CORIC_AGRAR
sources:
  - ../../prds/prd-CORIC_AGRAR-2026-05-27/prd.md
  - ../../briefs/brief-CORIC_AGRAR-2026-05-27/brief.md
  - docs/Dizajn/_HTML/
  - docs/Dizajn/_Prikazi strana/
design_spine: ./DESIGN.md
---

# EXPERIENCE — Ćorić Agrar

Peer spine sa `DESIGN.md`. Drži *kako sajt radi* — IA, ponašanja, stanja, interakcije, dostupnost i ključne tokove. Referencira DESIGN tokens kroz `{path.to.token}` sintaksu (npr. `{colors.brand.green-800}`). Oba spine-a imaju prednost u sukobu sa bilo kojim mockup-om ili PRD specifikacijom (PRD se ažurira ako se pojavi nesaglasnost).

## Foundation

### Form-factor

**Web responzivan sajt** — desktop / tablet / mobile. Bez nativne aplikacije.

**Breakpoint-i** (vidi `DESIGN.md § Layout & Spacing`):
- **mobile:** < 768px — hamburger meni, kondenzovan top header, single-column layouts
- **tablet:** 768–1199px — primarna navigacija, 2-3 col grid-ovi
- **desktop:** ≥ 1200px — pun sticky nav sa pretragom, 3-4 col grid-ovi, hero overlay card visible

### UI system

**Bootstrap 5.3** kao osnova (iz tech stack-a fiksiranog u Product Brief addendum-u). DESIGN tokens nadjačavaju Bootstrap default-ove — custom CSS sloj iznad. HTMX za sve dinamičke interakcije (filteri, paginacija, slanje formi) bez ponovnog učitavanja cele strane.

### Input modaliteti

- **Mouse** (primarno desktop)
- **Touch** (mobile, tablet) — sve interaktivne mete min 44×44px
- **Keyboard** (a11y, primarno desktop) — svi interaktivni elementi navigabilni kroz Tab; vidljivi focus indikatori (vidi § Accessibility Floor)
- **Screen reader** (NVDA, VoiceOver, JAWS) — ARIA atributi na akordionu, formama i modal-ima

## Information Architecture

### Glavna navigacija (header)

```
Početna
Traktori                                       [dropdown]
  ├── Wuzheng
  ├── Agri Tracking
  └── Saillong by Maki
Mehanizacija                                   [dropdown / mrtav link]
  ├── Priključna mehanizacija (Jeegee)
  ├── Radne mašine (HZM)
  ├── MIX prikolice (Tulip)
  └── Polovna mehanizacija
Servis                                         [dropdown]
  ├── Servisna podrška
  └── Rezervni delovi
Priče sa polja
O nama
Kontakt
                                          [Search ikona] [SR/HU/EN]
```

### Top header (iznad menija, desktop & tablet)
Adresa | Telefon prodaja | Telefon servis | Social ikone. Na **mobile**: samo telefonska ikona (klik proširi panel sa ostalim informacijama).

### Footer

4 kolone (desktop), stacked (mobile):

| Kolona 1 | Kolona 2 | Kolona 3 | Kolona 4 |
|---|---|---|---|
| **Logo + slogan** | **Proizvodi** | **Najnovije vesti** (dinamička, 3 najnovije iz bloga) | **Kontakt + Social** |

Ispod: tanka bela linija → `© 2026 Ćorić Agrar. Sva prava zadržana.`

### Sitemap

```
/                                    Početna
/o-nama
/traktori                            Listing svih traktora + filteri
/traktori/wuzheng
/traktori/agri-tracking
/traktori/saillong-by-maki
/proizvod/{slug}                     Stranica pojedinačnog modela (univerzalni template)
/mehanizacija/prikljucna             Jeegee — kategorije
/mehanizacija/prikljucna/{kategorija}/{podkategorija?}/{grupa?}
/mehanizacija/radne-masine           HZM — potkategorije
/mehanizacija/radne-masine/{podkategorija}
/mehanizacija/mix-prikolice          Tulip
/mehanizacija/polovna                Polovna sa filterima
/servis                              Servisna podrška + forma
/servis/rezervni-delovi              Rezervni delovi + forma
/blog                                Indeks „Priče sa polja"
/blog/{slug}                         Pojedinačna objava
/blog/kategorija/{slug}              Filter po kategoriji
/blog/tag/{slug}                     Filter po tagu
/kontakt                             Info + forma + Google Maps
/politika-kolacica                   Static (admin uređuje)
/politika-privatnosti                Static (Lorem Ipsum baseline)
/admin                               Admin panel (login-only)
```

**Lokalizacija:** URL prefiks `/sr/`, `/hu/`, `/en/`. Default `/` preusmerava na `/sr/` (detekcija jezika pretraživača u v1 `[ASSUMPTION]` — fallback je sr).

### Početna — sekcijski raspored

1. **Hero** (`{colors.brand.green-800}` overlay card preko foto-pozadine traktora) — slogan *„Prijatelj koji razume zemlju!"*, brand lockup, ikona pretrage u nav-u
2. **„O nama" intro** — pun blok sa naslovom, kratkim tekstom i CTA *Saznaj više* → `/o-nama` (mockup potvrđen)
3. **Traktori** — sekcija sa brendovima, svaki kao kartica (logo + reprezentativni model) + CTA *OPŠIRNIJE*. Brendovi sa oznakom *Uskoro* su prikazani sa pill-badge-om
4. **Priključna mehanizacija (Jeegee)** — banner sa CTA → `/mehanizacija/prikljucna`
5. **Radne mašine (HZM)** — sekcija sa kategorijama (utovarivači, telehendleri) — koristi *Ponavljajući element* kao vizuelni motiv (jedan po kategoriji)
6. **Polovna mehanizacija** — banner sa CTA → `/mehanizacija/polovna`
7. **Priče sa polja preview** — wave divider gore, slika kao pozadina, 2 najnovije blog kartice (bez naslovne slike na karticama)
8. **Footer**

> **Vizuelna referenca:** [Početna 4.0 mockup](../../../docs/Dizajn/_Prikazi%20strana/Ćorić%20Agrar%20-%20Početna%204.0.jpg).

## Voice and Tone

DESIGN.md drži brand voice (ozbiljno, prizemljeno, agrarno). Ovde su konvencije mikrokopije.

### Mikrokopija konvencije

| Lokacija | Konvencija | Primer |
|---|---|---|
| CTA dugmadi | **Imperativ, uppercase, tracking-wide** | *PREUZMI BROŠURU*, *SAZNAJ VIŠE*, *POŠALJI UPIT* |
| Linkovi van CTA | Mixed case, bez uppercase | *Vidi sve modele*, *Preuzmi katalog* |
| Section title (h2) | UPPERCASE preko eyebrow lente | *PROIZVODI*, *NAŠA PRIČA* |
| Card title (h3) | Title Case, bez uppercase | *Agri Tracking TB804* |
| Labele forme | UPPERCASE caption | *IME I PREZIME*, *EMAIL* |
| Placeholder | Mala slova, light gray (`{colors.neutral.gray-700}`) | *„npr. Marko Marković"* |
| Helper tekst | Sentence case ispod polja | *„Unesi makar 2 znaka"* |
| Success potvrda | Topla, ljudska | *„Hvala! Vaš upit je primljen. Javićemo se u najkraćem mogućem roku."* |
| Greška forme | Konkretna, ne tehnička | *„Email format nije ispravan"*, ne *„Validation failed"* |

> Mikrokopija za empty state — vidi § State Patterns → *Empty states (po kontekstu)* (kanonski izvor).

### Lokalizacija tone

- **Srpski (primarni)** — direktan, ljudski, sa povremenim *ti-formom* za blog („Probaj", „Pogledaj"), ali *Vi-formom* u formama i poslovnim kontekstima („Vaš upit", „Vaše ime").
- **Mađarski / engleski** — neutralan poslovni ton; uniformno *Vi/Sie/You*.

## Component Patterns (behavioral)

Vizuelne specifikacije su u `DESIGN.md § Components`. Ovde — kako rade.

### Button
- **Hover (desktop):** tranzicija boje 200ms ease — primary green → lime green
- **Active (click):** scale 0.98, 100ms
- **Disabled:** opacity 0.5, cursor not-allowed, bez hover state-a
- **Loading state** (HTMX slanje): tekst se zamenjuje malom spinner ikonom; klik je onemogućen dok je zahtev u toku

### Card (Product, Blog)
- **Hover (desktop):** suptilno podizanje — translateY(-2px), shadow se pojačava (0 4px 12px), 200ms ease
- **Touch (mobile):** bez hover; tap → navigacija
- **Klik pokriva celu karticu** — cela kartica je link, ne samo CTA dugme (klik na sliku ili naslov takođe vodi)

### Accordion (Specifikacije proizvoda)
- **Default-open:** Stranica proizvoda (FR-17) — prva sekcija (Motor) je otvorena na učitavanju, ostale zatvorene (`{components.accordion.default-open}`). Brand stranica (FR-8 Extended) — **sve zatvorene** (korisnik je već u skrolu pregleda; otvaranje je opcionalno).
- **Klik na header:** toggle open/close, animacija 250ms ease (height transition)
- **Ikona promene:** `+` (zatvoren) ↔ `−` (otvoren), bez rotacije; `aria-hidden="true"` (stanje signalizuje `aria-expanded` na header dugmetu)
- **Više sekcija može biti otvoreno istovremeno** — nije strogo accordion-pravilo
- **Prazna sekcija** (npr. Hidraulika bez podataka): u potpunosti se sakriva (header + sadržaj)

### Lightbox (Galerija, Brošura preview, Varijante)
- Trigger: klik na sliku u karusel galeriji ili na varijantnoj kartici
- **Backdrop:** `rgba(15,15,15,0.85)`, klik na njega zatvara lightbox
- **Navigacija:** strelice prev/next (desktop), swipe (touch), Tab i strelice (keyboard)
- **Esc** zatvara; focus trap dok je otvoren; pri zatvaranju focus se vraća na element koji ga je otvorio

### Forma (univerzalna)
- **Field focus:** border → `{colors.brand.green-800}`, suptilan ring `{colors.brand.green-400}` opacity 0.3
- **Validacija:**
  - Client-side: HTML5 validacioni atributi (required, type=email, pattern)
  - Trigger: na blur (kad polje izgubi focus), ne na svaki taster
  - Server-side: HTMX response sa parcijalnim ažuriranjem polja označenih greškom
- **Slanje:**
  - Klik → dugme prelazi u Loading state
  - Uspeh: cela forma se zamenjuje success karticom (`„Hvala! Vaš upit je primljen."` sa zelenom ikonom check-a)
  - Greška: forma ostaje, polja sa greškom dobijaju `error` state i helper tekst ispod
- **Foto upload (FR-22 servisni zahtev):** drag-and-drop površina + klik za file picker; preview thumbnail nakon izbora, X za uklanjanje

### HTMX dinamičke izmene & screen reader feedback

Svaka HTMX izmena DOM-a — filter rezultati, search dropdown, uspeh/greška forme, paginacija — mora biti najavljena tehnologijama za pomoć (screen reader-ima).

- **Aria-live region:** stranica drži `<div aria-live="polite" aria-atomic="true">` blizu glavnog sadržaja (ne u DOM-u koji se zamenjuje); HTMX response servira kratku poruku u taj region (npr. „12 rezultata pronađeno", „Forma poslata", „Greška pri slanju").
- **Loading states:** elementi u toku obrade imaju `aria-busy="true"`; uklanja se po završetku.
- **Filter rezultati:** aria-live obaveštava o broju rezultata posle promene filtera (debounced — najavljuje se tek nakon stabilnog stanja, ne za svaki taster).
- **Search dropdown:** aria-live obaveštava o broju predloga; svaki predlog je u `<ul role="listbox">` sa odgovarajućim ARIA atributima.
- **Greške forme:** umesto generičnog „validation failed", konkretna poruka po polju + `aria-live="assertive"` rezime iznad forme.
- **Upravljanje fokusom pri HTMX swap-u:** ako swap u potpunosti menja sekciju (npr. cela kartica → success), fokus se programatski pomera na novi element (`hx-on::after-swap`).

### Filter (Traktori, Polovna mehanizacija)
- **HTMX live-filter:** promena slider-a ili dropdown-a → debounce 300ms → zahtev → rezultati se ažuriraju u mestu
- **Loading state:** područje rezultata dobija opacity 0.5 dok je zahtev u toku
- **URL state:** svi aktivni filteri se odražavaju u URL query parametrima (deljivo)
- **Reset:** dugme *Resetuj filtere* vraća sve na default vrednosti i čisti URL

### Slider (Testimonijali)
- **Auto-advance:** 6 sekundi po slajdu (`[ASSUMPTION]`)
- **Pauza:** hover na slider pauzira auto-advance (desktop)
- **Indikatori:** klikabilni; klik skače na taj slajd
- **Swipe:** podržan na touch uređajima
- **Pauza/play kontrola** (WCAG 2.2.2): vidljivo pause/play dugme uz indikatore, dostupno preko tastature (Tab → Space toggle). Zaustavlja auto-advance dok ga korisnik ne pokrene ponovo.
- **Reduced motion:** ako korisnik ima `prefers-reduced-motion: reduce`, auto-advance je **isključen** podrazumevano — korisnik ručno prelazi indikatorima ili strelicama.
- **Tab order:** prev → indikatori → next → pause/play.

### Sticky nav
- Default state: full-height nav sa adresom u top header-u
- **Na skrol nadole (>100px):** nav se kondenzuje (shrunk state, ~60px visine, manji logo); top header je sakriven
- **Na skrol nagore:** nav se širi nazad u full state
- Animacija: 200ms ease, samo transform i height
- Footer/dno strane: nav je uvek u full state (vidi § Open Decisions)

### Search
- **Trigger:** klik na ikonu pretrage u nav-u → širi se u inline tekstualno polje (slide-in s desna, 200ms)
- **Kucanje:** minimum 2 znaka pre nego što HTMX zahtev krene (debounce 300ms)
- **Dropdown rezultati:** grupisani po tipu (Proizvodi | Objave), maksimum 5 po grupi, sa „Vidi sve" linkom ka dedikovanoj strani sa rezultatima pretrage
- **Klik van:** zatvara pretragu
- **Esc:** zatvara i fokus se vraća na ikonu pretrage

## State Patterns

Stanja za svaki interaktivni element. Definicije su globalne.

| State | Vizuelni indikator (token reference) | Uslov za pokretanje |
|---|---|---|
| **Default** | Element u nominalnoj boji | Inicijalno renderovanje |
| **Hover** (desktop) | Svetliji ton / podizanje / underline | `:hover` |
| **Focus** (keyboard) | Vidljivi ring (2px `{colors.semantic.focus-ring}`, postiže 3:1 kontrast prema podlozi — WCAG 1.4.11) | `:focus-visible` |
| **Active** | Scale 0.98 / tamnija pozadina | `:active` / mousedown |
| **Disabled** | Opacity 0.5, cursor not-allowed | `aria-disabled` ili `disabled` |
| **Loading** | Spinner unutar elementa, sadržaj opacity 0.5, `aria-busy="true"` na kontejneru | HTMX `htmx-request` |
| **Error** | Crveni border + helper tekst | Validacija nije prošla |
| **Empty** | Pattern: ikona + naslov + opis + CTA ka rešenju | 0 rezultata |
| **Selected** (tab, toggle) | Pozadina → `{colors.brand.green-800}`, tekst → white | Izbor korisnika |

### Empty states (po kontekstu)

| Mesto | Poruka | CTA |
|---|---|---|
| Filter ne vraća rezultate | „Nema rezultata sa trenutnim filterima." | *RESETUJ FILTERE* |
| Pretraga: 0 rezultata | „Nema rezultata za '{query}'." | Lista popularnih kategorija i brendova |
| Pretraga: <2 znaka | „Unesi makar 2 znaka." | (nema CTA) |
| Blog: nema objava | „Uskoro nove priče sa polja." | *POVRATAK NA POČETNU* |
| Polovna mehanizacija prazna | „Trenutno nemamo polovne mehanizacije u ponudi." | *POGLEDAJ NOVE TRAKTORE* |

## Interaction Primitives

### Click i Tap mete
- Minimalna veličina mete: **44 × 44px** (touch a11y baseline)
- Kartice (proizvod, blog): cela površina je klikabilna; CTA dugme unutra je vizuelni indikator, ne jedina meta za klik

### Skrol
- **Smooth scroll** za anchor linkove (`#section-id`)
- **Scroll restoration** pri back/forward navigaciji — default pretraživača
- **Reduced motion (a11y):** ako korisnik ima `prefers-reduced-motion: reduce`, smooth scroll postaje trenutan; count-up animacije se zamenjuju finalnim brojem; height transition akordiona se ubrzava (50ms ili trenutno)

### Animacije
| Animacija | Trigger | Trajanje | Easing |
|---|---|---|---|
| Count-up statistike | Scroll-into-view (Intersection Observer) | 1500ms | ease-out |
| Vremenska lenta (SVG/CSS) | Scroll-into-view | 800ms po segmentu | ease-in-out |
| Slider auto-advance | Tajmer | 600ms slide tranzicija | ease-in-out |
| Accordion expand/collapse | Klik | 250ms | ease |
| Nav shrink na skrol | Pozicija skrola | 200ms | ease |
| Lightbox fade in | Klik | 200ms | ease |
| Card hover lift | Hover | 200ms | ease |
| HTMX forma/filter | Slanje/promena | (varira, server) | — |

### HTMX timeout
Mehanika slanja i filtera je u § Component Patterns (Forma, HTMX dinamičke izmene). Ovde samo: network timeout (10s `[ASSUMPTION]`) → generička greška „Slanje nije uspelo, probajte ponovo."

### Lokalizacija switcher
- **Trigger:** klik na prekidač jezika (SR/HU/EN, desni kraj nav-a)
- **Akcija:** preusmerenje na ekvivalentni URL u novom locale-u (`/sr/...` → `/hu/...`)
- **Strukturna pozicija se čuva** — ako sam na `/sr/traktori/agri-tracking/tb804`, prelazak na *hu* vodi na `/hu/traktori/agri-tracking/tb804` (ne na početnu)
- **Marker za fallback sadržaj:** pored polja koje koristi fallback prikazuje se mala `ⓘ` ikona. Hover/klik → tooltip *„Sadržaj na srpskom — još nije preveden"*. Ikona je u boji `{colors.semantic.text-muted}`, suptilna.

## Accessibility Floor

Baseline: **WCAG 2.1 nivo AA** (PRD § 5.2). Konkretni zahtevi:

### Kontrasti
- Tekst nad svetlom pozadinom: min 4.5:1 (mali tekst), 3:1 (veliki 18px+ ili 14px bold)
- `green-900 (#1f3f2f)` na `white` = ~12.6:1 ✓
- `white` na `green-800 (#25402f)` = ~11.1:1 ✓
- `gold-500 (#e7af12)` na `green-900` = ~5.8:1 ✓
- **Rizik:** `lime-500 (#c8d32c)` na bilo čemu — proveriti svaki slučaj upotrebe; verovatno se ne koristi za body tekst

### Navigacija tastaturom
- Sve interaktivne mete su navigabilne kroz Tab (logičan red, ne nasumičan)
- Vidljiv focus ring (vidi State Patterns) — **ne uklanjati `outline`** ni na jednom interaktivnom elementu
- Skip link „Preskoči na sadržaj" na vrhu strane (vidljiv pri Tab focusu)
- Esc zatvara modal-e i Lightbox

### ARIA atributi
- Akordion: `aria-expanded` na headeru, `aria-controls` na sadržaju
- Forme: `aria-required`, `aria-invalid`, `aria-describedby` za helper i error tekst
- Slider: `aria-roledescription="carousel"`, `aria-label` za svaki slajd, ARIA live region za auto-advance
- Lightbox: `role="dialog"`, `aria-modal="true"`, focus trap

### Alt tekst
- Sve slike imaju `alt` atribut
- Dekorativne slike: `alt=""` (NE izostaviti atribut)
- Slike proizvoda: opisni alt — *„Agri Tracking TB804 traktor u radu na polju"*
- **Repeating Element corner motif** (`{components.repeating-element}`): dekorativan grafem (točak/brazda) — uvek `aria-hidden="true"` na SVG ili `alt=""` na slici. Bez čitanja od strane screen reader-a.

### Reduced motion
- `prefers-reduced-motion: reduce` se poštuje za sve animacije navedene u § Interaction Primitives → Animacije
- Esencijalne animacije (load state spinner) ostaju, dekorativne (count-up, slide) se pojednostavljuju ili izvršavaju trenutno
- **Budžet istovremenog pokreta:** sticky nav shrink + count-up statistike + slider auto-advance + accordion expand mogu se izvršiti istovremeno na učitavanju. Pri `prefers-reduced-motion: reduce`, **isključuje se auto-advance slidera i count-up** (trenutno finalno stanje); accordion i nav-shrink ostaju, ali ubrzani (50ms umesto 200-250ms).

### Internacionalizacija & screen reader

- **`<html lang>` atribut** se ažurira pri promeni jezika (sr/hu/en) — ne samo URL prefiks. Screen reader tako pravilno čita izgovor.
- **Polja sa fallback sadržajem** (FR-32) imaju `lang` atribut na konkretnom polju koje koristi srpski fallback, dok je ostatak strane na drugom locale-u; npr. `<p lang="sr">Lorem ipsum...</p>` unutar `/hu/` strane.
- **Prekidač jezika** ima `aria-label="Izaberi jezik"` (sr) / „Válassz nyelvet" (hu) / „Choose language" (en), kao i `aria-current="page"` za trenutni jezik.
- **RTL podrška:** nije u opsegu za v1 (sva tri jezika su LTR). Beleška za v2: ako se doda arapski ili hebrejski, treba bidi podrška.

### Forme
- Sve labele su vidljive (ne samo placeholder)
- Obavezna polja: vizuelno (`*`) **i** programski (`aria-required`)
- Greške se prijavljuju i kroz ARIA live region (vidi § Component Patterns → HTMX dinamičke izmene)

## Key Flows

3 ključna toka iz PRD § 2.3, ovde fokusirani na UX/IA odluke (ne na scenarije sadržaja).

### Flow 1 — Marko bira novi traktor (UJ-1)

**Cilj:** Marko nalazi i kontaktira Ćorić Agrar za konkretni model.

**Surfaces redom:**
1. `/` Početna → Marko klikće *Traktori* u nav-u
2. `/sr/traktori` Listing → koristi filter (range slider snaga > 60 KS, range slider cena ≤ 25.000 €) sa HTMX live ažuriranjem
3. Klikće na Agri Tracking TB804 karticu (Grid layout) → svaka kartica je klikabilna celom površinom
4. `/sr/proizvod/agri-tracking-tb804` Stranica proizvoda
   - Hero overlay card sa imenom modela + 3 bullet ključne karakteristike
   - Galerija — karusel, klik otvara Lightbox
   - Specifikacije akordion — Motor podrazumevano otvoren
   - Brošura kartica — preuzima PDF
   - Slični modeli (hibrid auto+manual)
5. Skroluje do *„Imate pitanja?"* forme — polje *Model* je automatski popunjeno
6. Popunjava 5 polja (Ime, Email, Telefon, Model, Poruka) i šalje
7. **Climax:** forma se zamenjuje success karticom *„Hvala! Vaš upit je primljen."* + telefonski kontakt za hitne slučajeve

> **Vizuelne reference:** Početna ([Početna 4.0](../../../docs/Dizajn/_Prikazi%20strana/Ćorić%20Agrar%20-%20Početna%204.0.jpg)) → Listing ([traktori.html prototip](../../../docs/Dizajn/_HTML/traktori.html)) → Brand ([Stranica brenda 4.0](../../../docs/Dizajn/_Prikazi%20strana/Stranica%20brenda%20-%204.0.jpg)) → Proizvod ([Stranica proizvoda 1.0](../../../docs/Dizajn/_Prikazi%20strana/Stranica%20proizvoda%201.0.jpg)).

**Edge cases:**
- Filter 0 rezultata → empty state sa CTA *RESETUJ FILTERE*
- Server greška pri slanju forme → forma ostaje, generička greška iznad
- Spora mreža → loading state na dugmetu, ostatak forme onemogućen

**Cross-spine references:**
- `{colors.brand.green-800}` hero overlay
- `{components.accordion.default-open}` Motor sekcija
- `{components.brošura card}` PDF preuzimanje

### Flow 2 — Stojan prijavljuje servisni zahtev (UJ-2)

**Cilj:** Stojan podnosi servisni zahtev sa mobilnog tokom sezone setve.

**Surfaces redom:**
1. `/` Početna (sa mobilnog) — hamburger meni
2. `/sr/servis` Servisna podrška
   - Hero (kompresovan na mobile)
   - Info: brendovi koji se servisiraju, lokacija, radno vreme i kontakt
   - Forma servisnog zahteva
3. Popunjava polja: Ime, Telefon, Email (opciono), Vrsta mehanizacije (dropdown), Brend i model (slobodan unos), Opis kvara, Foto (opciono)
4. Klikće *Dodaj sliku* → file picker mobilnog (kamera ili galerija)
5. Slika je otpremljena → thumbnail preview, X za uklanjanje
6. Šalje formu
7. **Climax:** success kartica *„Vaš servisni zahtev je primljen. Pozvaćemo vas u najkraćem mogućem roku."* + telefon servisa za hitne slučajeve

**Edge cases:**
- Slika veća od limita (5 MB `[ASSUMPTION]`) → greška PRE otpremanja sa konkretnim limitom
- Slabija mobilna veza → forma ostaje, ponovni pokušaj na klik dugmeta

**Mobile-specific UX:**
- Top header je kondenzovan (samo ikona telefona)
- Polja forme su naslagana, min 44px visine
- Submit dugme je full-width
- Loading state je vidljiv

### Flow 3 — Marijana dodaje novi proizvod (UJ-3) — Admin

**Cilj:** Marijana unosi novi HZM 812T sa potpunim podacima.

**Surfaces redom:**
1. `/admin/login` → Email + lozinka
2. `/admin/dashboard` Dashboard
   - Statistike (posete, lead-ovi segmentovani po formi, ukupno proizvoda i blog objava)
   - Brze akcije: *DODAJ PROIZVOD*, *DODAJ BLOG OBJAVU*
3. Klikće *DODAJ PROIZVOD* → `/admin/proizvodi/novo`
4. Tabovi i sekcije u formi:
   - **Osnovno:** Naziv, opis, kategorija, brend, serija, ključne karakteristike (3 bullet polja)
   - **Specifikacije:** 4 sekcije akordiona (Motor / Transmisija / Hidraulika / Ostalo) sa key-value parovima
   - **Galerija:** drag-and-drop multi-upload, redosled se može menjati prevlačenjem
   - **Brošura:** PDF upload
   - **Testimonijali:** ponovljiva grupa (slika + citat + ime/lokacija)
   - **Slični modeli:** lookup-search za marker (zamenjuje auto-suggest)
   - **Varijante:** ponovljiva grupa (slika + naziv + šifra + opis)
   - **Lokalizacija:** dropdown SR/HU/EN, prebacivanje jezičkih taba
5. Marijana unosi sve na **SR**, a HU/EN ostavlja prazno
6. Status: **Skica**, klik **Sačuvaj**
7. Indikator auto-save („Sačuvano u 14:23")
8. **Climax 1:** vraća se posle ručka, otvara isti proizvod i prebacuje status na **Objavljeno**
9. **Validacija pre objave:** sistem proverava da SR ima Naziv + barem 1 sliku galerije + barem 1 sekciju specifikacija. Ako nešto fali — prikazuje konkretno polje sa greškom
10. **Climax 2:** uspeh — toast notifikacija *„Proizvod 'HZM 812T' je objavljen."*

**Edge cases:**
- Nepravilan format upload-ovanog fajla → greška sa listom dozvoljenih formata
- Fajl veći od limita → greška sa konkretnim limitom
- Pokušaj objave bez SR sadržaja → blokirano sa linkom na polja koja nedostaju

**Admin-specific UX:**
- Top header je **bez** site nav-a (admin nav je odvojen)
- Side nav: Dashboard | Proizvodi | Brendovi | Kategorije | Blog | Statičke strane | Korisnici | SEO | Podešavanja
- Logout u top-right
- Auto-save na mestu sa indikatorom

## Inspiration & Anti-patterns

### Inspiracija — Lemken (lemken.com)

**Šta uzimamo:**
- **Pattern filtering navigacije** — left rail filter sa kolapsibilnim grupama (može se replicirati za polovnu mehanizaciju i Jeegee kategorije)
- **Veliki bold sekcijski naslovi** — h2 weight 700 sa eyebrow lentom (Lemken-style ozbiljnost)
- **Strukturna hijerarhija proizvoda** — Brend → Kategorija → Model — sa breadcrumb navigacijom
- **„Highlights" pattern na stranici proizvoda** — kratke bullet karakteristike pre detaljnijeg pregleda (već u FR-14 hero bullets)

**Šta NE uzimamo:**
- Lemken-ovu gustinu informacija — naša interpretacija je 30-40% manje gusta po stranici
- Lemken-ov fiksirani levi nav u proizvodu — umesto njega koristimo accordion

### Anti-patterns (izričito izbegavati)

| Anti-pattern | Zašto ne | Šta umesto toga |
|---|---|---|
| **Pop-up newsletter overlay** | Agrarni sektor; previše agresivno za poverenje | Stilizovan input u footer-u (ako uopšte) |
| **Auto-play video sa zvukom** | Nepristupačno; iritantno na mobilnom | Hero video je opcionalan, **bez zvuka**, podrazumevano utišan |
| **„NOVO!" / „AKCIJA!" pulsirajući badge-ovi** | Suprotan osećaj agrarnom tonu | Tihi pill-badge u zlatnoj boji za *Uskoro* i *Novo* |
| **Kritične informacije samo u tooltip-u** | Problem na mobile-u i za a11y | Informacija je inline ili u akordionu |
| **Navigacija samo na hover** | Loše za touch | Klik otvara dropdown, hover je sekundarni mehanizam |
| **Lazy-loading bez placeholder-a** | Loš LCP | Skeleton placeholder za sav lazy-loaded sadržaj |
| **Mali touch targets (<44px)** | A11y propust, loš UX na mobile-u | Sve interaktivne mete ≥44px |

## Responzivan dizajn & platforme

### Mobile (< 768px)
- Hamburger meni (top-left), logo je centriran, ikona pretrage top-right
- Top header kondenzovan: samo ikona telefona; klik → širi se sa adresom i social linkovima
- Hero: visina ~60vh; overlay card pomeren u centar-bottom; manji tekst
- Strane sa listingom: 1 kolona kartica; filter u kolapsibilnom drawer-u na vrhu
- Akordion sekcije: full-width
- Forme: stack, full-width, submit dugme full-width
- Footer: 4 kolone naslagane u jedan red

### Tablet (768–1199px)
- Pun nav je vidljiv, ikona pretrage
- Top header je pun (adresa + telefon + social)
- Hero: ~70vh
- Strane sa listingom: 2 kolone kartica; filter u sidebar-u ili top-bar-u
- Forme: 1-2 kolone polja

### Desktop (≥ 1200px)
- Pun nav sa pretragom kao ikonom (klik je širi)
- Hero: ~80vh; overlay card u lower-left
- Strane sa listingom: 3-4 kolone kartica
- Sticky nav sa shrunk state-om pri skrolu nadole
- Hover state-ovi su aktivni

### Touch i Mouse
- Hover state-ovi se primenjuju samo unutar `@media (hover: hover)`
- Tap mete su uvek najmanje 44×44px — i na desktop-u, radi konzistentnosti

## Open Decisions

Svi `[ASSUMPTION]` i `[NOTE FOR UX]` tagovi za potvrdu u dev fazi:

- **`[ASSUMPTION]`** Auto-advance testimonijala = 6 sekundi po slajdu
- **`[ASSUMPTION]`** HTMX network timeout = 10s
- **`[ASSUMPTION]`** Limit za foto upload u servisnom zahtevu = 5 MB
- **`[ASSUMPTION]`** Default `/` preusmerava na `/sr/`; detekcija jezika pretraživača u v1
- **`[ASSUMPTION]`** Footer nav je uvek u full state-u pri približavanju dnu
- **`[ASSUMPTION]`** Social share dugmad na blog post-u — sticky leva strana na desktop-u, ispod naslova na mobile-u
- **`[NOTE FOR UX]`** Print stylesheet — odložiti za v2
- **`[OPEN]`** Skeleton loading patterns za listinge — definisati u dev fazi
- **`[OPEN]`** Renderovanje PDF cover-thumbnail-a — server-side (Ghostscript, pdf-image) ili pre-generated; tehnički izbor `→ Architecture`

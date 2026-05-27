---
title: Addendum — Ćorić Agrar Product Brief
status: ready
created: 2026-05-27
updated: 2026-05-27
parent: brief.md
---

# Addendum — Ćorić Agrar Product Brief

Referentni dokument za downstream faze (PRD, arhitektura, epics). Drži detalje koji ne pripadaju brief-u: tech stack, proizvodnu hijerarhiju, scope admin panela, dizajnerske odluke i otvorena pitanja. Izvor: Projektni zadatak i odluke donete tokom Discovery faze.

## Tech Stack (fiksirano)

### Backend
- **Django** (Python framework) — aplikacioni sloj, rutiranje, autentifikacija, ORM
- **PostgreSQL** — relaciona baza
- **django-modeltranslation** — višejezični sadržaj u bazi
- **Gunicorn + Nginx** — aplikacioni i web server u produkciji

### Frontend
- **HTML5 / CSS3 / JavaScript** — custom kod, bez generičkih šablona
- **Bootstrap 5** — grid + osnovne UI komponente (akordioni, slideri, modali)
- **HTMX** — dinamičke interakcije bez ponovnog učitavanja stranice (filtriranje proizvoda, paginacija, slanje formi)
- **Font Awesome 6** — ikonografija
- **Responzivan dizajn** za desktop / tablet / mobilni
- Lightbox + masonry galerija (O nama)

### Lokalizacija
- Srpski (primarni), mađarski, engleski
- Prebacivanje jezika dostupno sa svih strana

### DevOps
- **3 okruženja:** lokalno (development), staging (testiranje), produkcija
- **uv** — Python package manager + virtualno okruženje
- **Docker** — kontejnerizacija za produkciju (reproducibilan deploy, jednostavniji rollback)
- **Hetzner VPS** — hosting
- **Git** — verzionisanje
- **SSL** — Let's Encrypt
- **Bekap:** automatski dnevni bekap baze i sajta (stavka „bekap pre migracije" iz zadatka **otpada** — nema starog sajta)

### Integracije i SEO
- Google Search Console, Google Analytics, Facebook Pixel
- GDPR baner sa upravljanjem kolačićima
- sitemap.xml, robots.txt
- Meta naslovi/opisi po stranici i proizvodu
- 301 redirect manager (za buduće potrebe, ne za migraciju)

## Mapa proizvoda i brendova

### Traktori (3 brenda)
| Brend | Status | Modeli / serije |
|---|---|---|
| **Wuzheng** | aktivan | (detalji u kasnijim fazama) |
| **Agri Tracking** | aktivan | TB serija, TD serija, TC serija |
| **Saillong by Maki** | aktivan | (detalji u kasnijim fazama) |

> Pojedini brendovi mogu nositi oznaku „Uskoro" ako još nisu dostupni u ponudi.

### Priključna mehanizacija — Jeegee
Tri glavne kategorije, sa daljom hijerarhijom po nameni:

**1. Osnovna obrada zemljišta**
- Plugovi
  - Plugovi ravnjaci: KJ-tip
  - Plugovi obrtači (po debljini grede):
    - 90×90: 1LF-KP331
    - 100×100: 1LF-435C
    - 120×120: 1LF-L450F, 1LF-L350
    - 140×140: 1LF-LKX450
    - 160×160: 1LF-LKX550A
  - Plug obrtač ima dodatni prikaz **izbora daske** (puna i rešetkasta, sa prostorom za još jedan tip)
- Podrivači: JMA300
- Gruberi (nošeni): KX300, KX350

**2. Priprema zemljišta**
- Tanjirače
  - Nošene Vega 9: kratka tanjirača 250, kratka tanjirača 300
  - Vučene 1BYQ tip: 330, 380, 430, 530, 630
  - Vučene Vega 9: 400, 500, 600
  - Vučene Vega 12: 400, 500, 600
  - Svaka tanjirača nudi **izbor rotora**: dupli cevasti ili kembridž valjak (sa bočnim prikazom slike)
- Setvospremači
  - Hermes vučni: H255-15.7m, H255-12.4m
  - SKS kombinator: SKS 300, SKS 400, SKS 500

**3. Mašine za setvu**
- Precizne sejalice za žito sa rotodrljačom: 2BG-250, 2BG-300

### Radne mašine — HZM
- Mini utovarivači: HZM 1100
- Utovarivači bez teleskopa: HZM 925
- Teleskopski utovarivači: HZM 810T, HZM 812T, HZM 816T, HZM 825T
- Telehendleri: HZM 7335

### MIX prikolice — Tulip
- 6 kubika
- 8 kubika
- Dimenziona tabela: Projektni zadatak § 2.1.4.3

### Polovna mehanizacija
Otvoreni inventar (varira tokom vremena). Kategorije: TRAKTORI / PRIKLJUČNA MEHANIZACIJA / RADNA MAŠINA / OSTALO. Detalji o filterima u sekciji "Filtriranje i pretraga".

## Filtriranje i pretraga

- **Traktori (svi brendovi zajedno ili pojedinačno po brendu):** konjska snaga, godište, cena → HTMX live filter
- **Polovna mehanizacija:** kategorija, brend, cenovni rang (slider min–max), godina proizvodnje, stanje mašine
- **Globalna pretraga:** polje za pretragu u meniju (full-site search nad proizvodima i blogom; PostgreSQL FTS — `[ASSUMPTION]`, potvrđuje se u arhitekturi)

## Inventar formi (sve se procesiraju kroz HTMX)

| Forma | Lokacija | Polja | Cilj email |
|---|---|---|---|
| **Opšti kontakt** | `/kontakt` | Ime i prezime, Email, Telefon, Poruka | TBD od klijenta `[PLACEHOLDER]` |
| **Upit za model** | stranica proizvoda | Ime, Email, Telefon, Model (auto-popunjen), Poruka | TBD `[PLACEHOLDER]` |
| **Servisni zahtev** | `/servis` | Ime, Telefon, Email, Vrsta mehanizacije (dropdown), Brend+model, Opis kvara, Foto (opciono) | TBD `[PLACEHOLDER]` |
| **Upit za rezervni deo** | `/servis/rezervni-delovi` | Model traktora, Rezervni deo, Dodatni opis (opc.), Slika (opc.), Ime, Telefon, Email, Način plaćanja (pouzeće / predračun), Način preuzimanja (dostava / lično), Napomena (opc.) | TBD `[PLACEHOLDER]` |

`[PLACEHOLDER]` označava da email adresu konfigurišemo putem env-var ili admin podešavanja, a klijent je unosi naknadno.

## Admin panel — scope detalj

### Dashboard
- Statistike: posete za 7/30 dana (GA integracija), broj poruka u tekućem mesecu, broj servisnih zahteva u tekućem mesecu, ukupan broj proizvoda, ukupan broj blog objava
- Brze akcije: Dodaj proizvod, Dodaj blog objavu

### Upravljanje proizvodima
- CRUD: naziv, opis, kategorija, brend, serija
- Galerija fotografija
- Tehničke specifikacije po sekcijama (Motor / Transmisija / Hidraulika / Ostalo)
- Upload PDF brošure
- Testimonijali za proizvod
- Status: objavljeno / skica / arhivirano
- Slični modeli (manual marking)
- Trojezični unos (sr / hu / en)

### Upravljanje brendovima i kategorijama
- Brendovi: naziv, logo, opis, hero slika, statistike (count-up brojevi), katalog PDF
- Kategorije i potkategorije mehanizacije
- Redosled prikaza

### Blog objave
- CRUD sa WYSIWYG editorom (slike, video unutar teksta)
- Kategorije i tagovi (klijent naknadno definiše kategorije, `[PLACEHOLDER]`)
- Status: objavljeno / skica / arhivirano
- Trojezični unos

### Korisnici i pristup
- Superadmin / editor uloge
- Kreiranje, izmena, promena lozinke

### Sadržaj stranica
- Statičke strane: O nama, Servis, itd.
- Galerija O nama
- Kontakt podaci, radno vreme

### SEO modul
- Meta naslov / opis po stranici i proizvodu
- sitemap.xml upravljanje
- 301 redirect manager
- Google Search Console pregled

### Podešavanja
- Opšte: naziv sajta, kontakt, logotip, favicon
- Navigacioni meni
- GDPR baner i politika kolačića

## Dizajnerske odluke iz zadatka (vredne pamćenja za UX fazu)

- **Boje:** zelena + tamna paleta (agrarni sektor)
- **Meni:** transparentan na hero sekcijama, tanki elegantni fontovi
- **Top header:** adresa + telefon iznad menija
- **Polje za pretragu:** na kraju menija
- **Ponavljajući element:** pravougaonik širi nego viši, sa malim radijusom i **tankim belim koncentričnim linijama u uglu** (točkovi i brazde). Boja varira po brendu (zelena kao podrazumevana, plava za Jeegee).
- **Footer:** zeleni gradijent (tamnija → svetlija), logo centriran iznad navigacije, copyright odvojen tankom belom linijom
- **Statistike brenda:** count-up animacija pri skrolovanju
- **Hero „Priče sa polja":** slika u pozadini, zatalasana gornja ivica
- **Lemken kao referenca** za organizaciju kategorija mehanizacije (u pojednostavljenoj formi)
- **HTML prototip postoji:** `docs/Dizajn/_HTML/` (`index.html`, `traktori.html` + assets) — koristi se kao osnova za frontend
- **JPG vizuali strana:** `docs/Dizajn/_Prikazi strana/`

## Otvorena pitanja za PRD fazu

Konsolidovana lista. Inline tagovi (`[OPEN]`, `[ASSUMPTION]`) u sekcijama iznad referenciraju ovde nabrojane stavke.

### Infrastruktura i performans
1. **Email / SMTP servis** za forme — Mailgun, SendGrid, Hetzner SMTP ili Django SMTP backend nad Hetzner box-om? `[OPEN]`
2. **Performance budget** — gornja granica za page weight, LCP, TTFB? Nije eksplicitno definisano u zadatku. `[OPEN]`

### Frontend / tech izbori (rešavaju se u arhitekturi)
3. **Lightbox library** — vanilla JS ili biblioteka (PhotoSwipe, GLightbox)? `[ASSUMPTION]`
4. **Search backend** — PostgreSQL `tsvector` ili Django `Q`-based pretraga? `[ASSUMPTION]` PostgreSQL FTS.
5. **Vremenska lenta (O nama)** — animirana SVG, CSS-only, JS biblioteka ili statički HTML?

### Sadržajne i UX odluke
6. **Trojezičnost — fallback strategija** — ako mađarska ili engleska verzija polja nije popunjena, prikazujemo srpsku verziju ili prazan sadržaj?
7. **Kategorije bloga** — klijent ih definiše naknadno (zajedno sa tekstovima); šema mora ostati otvorena.
8. **Slični modeli** — automatski (po brendu ili seriji) ili ručno markiranje od strane admina? Zadatak navodi „manual" — potvrditi u PRD-u.
9. **Filteri „polovna mehanizacija" — godišta** — slider, dropdown ili oba? `[OPEN]`
10. **Polovna mehanizacija — obim inventara** — koliki je realan broj? (Utiče na paginaciju i sortiranje.)

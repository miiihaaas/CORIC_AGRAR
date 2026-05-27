---
title: Product Brief — Ćorić Agrar veb sajt
status: ready
created: 2026-05-27
updated: 2026-05-27
project: CORIC_AGRAR
mode: fast-path
audience: internal-dev (Mihas)
---

# Product Brief: Ćorić Agrar — Veb sajt

## Executive Summary

Green-field **custom Django sajt** za Ćorić Agrar — kompaniju koja je nedavno dobila status uvoznika traktora i priključne mehanizacije više brendova za srpsko i regionalno tržište. Portfolio: traktori (3 brenda), priključna mehanizacija (Jeegee), radne mašine (HZM), MIX prikolice (Tulip), polovna mehanizacija.

Sajt je **prezentaciono-katalog rešenje sa lead-gen funkcionalnošću** (bez online prodaje): pretraga kataloga, tehničke specifikacije, kontaktne/servisne forme. Trojezičan (sr/hu/en), pun admin panel, SEO + osnovne analitike (GA, GSC, FB Pixel), GDPR.

Brief je interni input za PRD u BMad flow-u (PRD → UX → Architecture → Epics). Solo dev (Mihas) jedini čitalac i izvršilac.

## The Problem

- **Status quo:** Sajt ne postoji. Svaki upit ide telefonom — ne skalira na portfolio od ~100 proizvoda kroz više brendova.
- **Konkurencija:** Moderni katalog-orijentisani sajtovi (Lemken kao referenca u zadatku).
- **Šta ciljna publika traži:** brz pronalazak modela po snazi/nameni, tehničke specifikacije bez zvanja, PDF brošure za offline, servisne zahteve i upite za rezervne delove bez telefoniranja.

## The Solution

**Custom katalog-orijentisan sajt.** Ključne sposobnosti (detalji u Scope i `addendum.md`):

- **Strukturni katalog:** Traktori → Brend → Model; Mehanizacija → Kategorija → Brend → Model. Stranica modela: galerija, akordion-tabela specifikacija (Motor / Transmisija / Hidraulika / Ostalo), PDF brošura.
- **HTMX filteri:** konjska snaga / godište / cena za traktore; više filtera za polovnu.
- **Kontekstualne lead-gen forme:** opšti kontakt, upit za model (auto-popunjen), servisni zahtev, upit za rezervni deo.
- **Blog "Priče sa polja"** sa kategorijama i WYSIWYG editorom.
- **Trojezičnost** kroz `django-modeltranslation`.
- **Admin panel** za potpun CMS (proizvodi, brendovi, blog, statičke strane, SEO, korisnici, redirect manager, GDPR).
- **SEO + analitika:** GSC, GA, FB Pixel, sitemap, robots, meta po strani.

**Tech stack fiksiran** (vidi `addendum.md` § Tech Stack) — nije otvoren za diskusiju.

## Who This Serves

- **Eksterno:** poljoprivrednici / gazdinstva (biraju traktor po snazi i ceni), postojeći kupci (servis, rezervni delovi), B2B partneri — distributeri i zadruge (pregled portfolija).
- **Interno:** admin Ćorić Agrar-a — CRUD proizvoda, blog, forme/upiti.
- **Dev:** Mihas — brief postoji da PRD i arhitektura krenu iz čvrste tačke.

## Scope

### In (MVP / prvi launch — sve odjednom)

**Korisnički deo:**
- Početna sa svim sekcijama iz zadatka (Hero, O nama, Traktori, Priključna, Radne mašine, Polovna, Priče sa polja preview, Footer)
- O nama (hero video/slika, tekst, vremenska lenta, masonry galerija + lightbox)
- Traktori — listing sa filterima + brend strane (Wuzheng, Agri Tracking, Saillong by Maki)
- Mehanizacija — 4 podstrane (Jeegee priključna sa svim potkategorijama, HZM radne mašine, Tulip MIX prikolice, Polovna sa filterima)
- Stranica proizvoda (zajednički template sa varijantama)
- Servis (servisna podrška + rezervni delovi, obe sa formama)
- Priče sa polja (blog index + post + kategorije)
- Kontakt (info + forma + Google Maps)
- Responzivnost (desktop / tablet / mobile), trojezičnost sa prebacivanjem jezika

**Admin deo:**
- Dashboard sa statistikama i brzim akcijama
- CRUD: proizvodi, brendovi, kategorije, blog, statičke strane
- Uloge (superadmin / editor)
- SEO modul (meta, sitemap, redirect manager)
- Podešavanja (kontakti, navigacija, GDPR baner)

**Infra & integracije:**
- Lokalno / staging / produkcija (Docker, Hetzner VPS)
- Automatski dnevni bekap baze i sajta, SSL (Let's Encrypt)
- Google Analytics, Search Console, Facebook Pixel, GDPR baner

### Out (eksplicitno van obima)

- **Online prodaja / e-commerce** — nema checkout-a, plaćanja ni korpe
- **Korisnički nalozi za kupce** — samo admin; posetioci ne registruju nalog
- **Migracija sa starog sajta** — ne postoji; otpadaju 301 redirects, URL preserving i bekap pre migracije
- **Live chat / WhatsApp, mobilna aplikacija, inventory tracking, multi-tenant** — van obima

## Constraints & Assumptions

- **Tech stack fiksiran:** Django + PostgreSQL + HTMX + Bootstrap 5 + Docker + Hetzner. Rationale u `addendum.md` § Tech Stack.
- **Obim sadržaja:** do 100 proizvoda inicijalno. Fotografije iz Envato stock-a ili od klijenta.
- **Sadržaj nije blokator dev-a:** nedostajući tekstovi su **Lorem Ipsum placeholderi**; klijent unosi realan sadržaj kroz admin nakon dev faze. `[DECISION]`
- **Open-ended timeline:** nema fiksnog launch datuma, nema MVP cut-eva iznuđenih deadline-om — sve se isporučuje odjednom.
- **Solo dev:** Mihas implementira sve faze, nema paralelizacije.
- **Lokalizacija:** srpski (latinica) primarni; mađarski + engleski pune lokalizacije (ne mašinski prevod), klijent dostavlja prevode kroz admin. `[ASSUMPTION]` — potvrditi u PRD-u

## Success Criteria

`[DEFERRED]` — označeno kao nebitno u ovoj fazi. Baseline za iteraciju kasnije:

- Sve forme funkcionišu pouzdano, emailovi stižu adresatima
- Sajt indeksiran u Google-u; ključne strane (brendovi, modeli) pokrivene sitemap-om sa validnim meta podacima
- Admin samostalno unosi proizvod / blog post bez dev intervencije
- Sve tri jezičke verzije rade bez fallback-a na primarni jezik (osim za eksplicitno neunesen sadržaj)
- Sajt prolazi osnovni Google PageSpeed / Lighthouse za responsive i performance `[ASSUMPTION]`

## Vision

**Sajt v1.0:** definitivna i pouzdana online tačka za poljoprivrednika koji bira mehanizaciju u Srbiji i regionu — pun katalog + tehnički podaci + jednostavan put do kontakta, bez online checkout-a.

Prirodni pravci rasta posle launch-a (van obima, samo za kontekst): prošireni filteri (namena, regija, dostupnost), personalizovan blog + newsletter, integracija sa CRM/ERP, online katalog rezervnih delova sa pretragom po šifri.

---

**Vezani fajlovi:**
- `addendum.md` — Tech Stack rationale, kompletna mapa proizvoda i brendova, inventar formi, scope admin panela
- `.decision-log.md` — audit trail svih odluka
- Izvorni materijal: `docs/Projektni zadatak - Ćorić agrar.md`, `docs/Dizajn/`

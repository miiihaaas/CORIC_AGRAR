# Reconciliation — PRD vs Product Brief

## Coverage summary

PRD pokriva sve In-Scope stavke iz brief-a kroz FR-1..FR-47, mirror-uje sve Out stavke u §9 Non-Goals, i poštuje sve tech/process constraints. Otvorena pitanja iz addendum-a su delom rešena u FR-ovima (slični modeli, fallback), delom prebačena u PRD §12 (proširena sa novim UX/arch pitanjima), uz dva sitnija drift-a oko brendskog naziva i konsolidacije liste.

## Scope IN coverage (brief.md § Scope/In → PRD FRs)

**Korisnički deo:**
- Početna sa svim sekcijama (Hero, O nama, Traktori, Priključna, Radne mašine, Polovna, Priče sa polja preview, Footer) → FR-1, FR-2, FR-3, FR-30 (footer); O nama preview je integrisana kao deo strane O nama (FR-4), bez zasebne home preview kartice → minor drift, vidi Gaps
- O nama (hero video/slika, tekst, vremenska lenta, masonry galerija + lightbox) → FR-4
- Traktori — listing sa filterima + brend strane (Wuzheng, Agri Tracking, Saillong by Maki) → FR-6 (listing), FR-7 (brand nav), FR-8 (brand page)
- Mehanizacija — 4 podstrane (Jeegee, HZM, Tulip, Polovna) → FR-9, FR-10, FR-11, FR-12, FR-13
- Stranica proizvoda (zajednički template) → FR-14..FR-21
- Servis (servisna podrška + rezervni delovi, obe sa formama) → FR-22, FR-23
- Priče sa polja (blog index + post + kategorije) → FR-24, FR-25, FR-26
- Kontakt (info + forma + Google Maps) → FR-5, integracija FR-5 sa Google Maps i §7.5
- Responzivnost (desktop/tablet/mobile) → §5.6 (browser support), pojedinačni FR-ovi pokrivaju mobilna ponašanja (FR-16 swipe, FR-17 vertical render, FR-28 hamburger)
- Trojezičnost sa prebacivanjem jezika → FR-31, FR-32, FR-33

**Admin deo:**
- Dashboard sa statistikama i brzim akcijama → FR-35
- CRUD proizvoda → FR-36
- CRUD brendova → FR-37
- CRUD kategorija → FR-38
- CRUD blog → FR-39
- CRUD statičkih strana → FR-40
- Uloge (superadmin / editor) → FR-41, definisane u Glossary §3
- SEO modul (meta, sitemap, redirect) → FR-42, FR-43, FR-44
- Podešavanja (kontakti, navigacija, GDPR) → FR-45, FR-46, FR-47

**Infra & integracije:**
- Lokalno/staging/produkcija + Docker + Hetzner → §8 (Operational)
- Dnevni bekap baze i sajta, SSL Let's Encrypt → §8
- GA, GSC, FB Pixel, GDPR baner → §7.2, §7.3, §7.4, FR-47

## Scope OUT alignment (brief.md § Scope/Out → PRD § Non-Goals)

- Online prodaja / e-commerce (nema checkout/korpe/plaćanja) → §9 "Online prodaja / e-commerce" match
- Korisnički nalozi za kupce → §9 "Korisnički nalozi za posetioce sajta" match
- Migracija sa starog sajta (otpadaju 301 redirects za migraciju, URL preserving, bekap pre migracije) → §9 "Migracija sa starog sajta" match
- Live chat / WhatsApp → §9 "Live chat / WhatsApp button" match
- Mobilna native aplikacija → §9 "Mobilna native aplikacija" match
- Inventory tracking → §9 "Inventory tracking / stock management" match
- Multi-tenant → §9 "Multi-tenant arhitektura" match

PRD dodaje 4 dodatna eksplicitna Non-Goals (PDF generisanje, javni API, mašinski prevod, AI ranking) — pojašnjenja koja su konzistentna sa duhom brief-a; nije drift, već pojačavanje.

## Constraints alignment

- **Tech stack fiksiran** (Django/PostgreSQL/HTMX/Bootstrap 5/Docker/Hetzner) → PRD eksplicitno ne ponavlja stack (§0 navodi da je addendum izvor), ali pominje Django default-e u §5.3 i HTMX u FR-6, FR-13, §5.1 — konzistentno sa brief-om
- **Obim sadržaja:** ~100 proizvoda → PRD ne navodi eksplicitan target (impliciran u §12 OQ #2 za search backend); minor drift — vidi Gaps
- **Content placeholder strategy** (Lorem Ipsum baseline, klijent unosi naknadno) `[DECISION]` → PRD §6.1 "politika privatnosti `[OPEN]` — Lorem Ipsum baseline za v1"; §12 OQ #15 (privacy), #16 (blog categories), #17 (email addresses). Pokriveno, ali brief-ov opštiji `[DECISION]` o Lorem Ipsum kao strategiji nije eksplicitno re-stated kao decision u PRD-u — vidi Gaps
- **Open-ended timeline** → PRD nema rok-blokove, podržava jednim launch-om (§10.1 "sve odjednom — jedan launch") match
- **Solo dev (Mihas)** → PRD §0 i §2.1 eksplicitno "Mihas" / "solo dev" match
- **Lokalizacija** (sr primarni, hu+en pune lokalizacije, ne mašinski prevod, klijent unosi kroz admin) `[ASSUMPTION]` → FR-31, FR-32, FR-36 (validacija sr obavezna; hu/en opciona), §9 "Mašinski prevod sadržaja" Non-Goal — pokriveno

**Decisions/Assumptions/Deferred tagovi iz brief-a:**
- `[DECISION]` Lorem Ipsum content strategy → impliciran u §6.1 i §10, nije eksplicitno tagovan kao `[DECISION]` u PRD-u
- `[ASSUMPTION]` lokalizacija (klijent dostavlja prevode) → §12 OQ #16, FR-36 validacija sr-only; pokriveno (zadržan kao operativni assumption u FR-36 fallback ponašanju)
- `[DEFERRED]` Success Criteria → PRD §11 eksplicitno tagovan `[DEFERRED]` match

## Open Questions from Brief addendum → PRD §12

Addendum lista 10 pitanja u 3 klastera. Mapiranje:

**Infrastruktura i performans:**
1. Email / SMTP servis → PRD §12 OQ #1 (SMTP / email servis) match
2. Performance budget → PRD §12 OQ #5 (Performance budget) match

**Frontend / tech izbori:**
3. Lightbox library → PRD §12 OQ #3 (Lightbox biblioteka) match
4. Search backend (PostgreSQL FTS) → PRD §12 OQ #2 (Search backend) match
5. Vremenska lenta (SVG/CSS/JS lib/static) → PRD §12 OQ #4 (Vremenska lenta) match

**Sadržajne i UX odluke:**
6. Trojezičnost fallback strategija → **RESOLVED in FR-32** (fallback je polje-po-polje na sr sa diskretnim markerom)
7. Kategorije bloga (klijent definiše naknadno) → PRD §12 OQ #16 (Blog kategorije inicijalna lista) match
8. Slični modeli (auto vs manual) → **RESOLVED in FR-20** (hibrid: auto default, admin override u celini zamenjuje auto)
9. Filteri "polovna mehanizacija" godišta → PRD §12 OQ #12 (Filteri godišta i cene — slider/dropdown/oba) match (proširen na sve range filtere)
10. Polovna mehanizacija obim inventara → PRD FR-13 navodi "nema fiksan obim — admin upravlja; sistem ne pretpostavlja gornju granicu" — **partially resolved**, ali addendum-ovo pitanje o paginaciji/sortiranju nije eksplicitno adresirano u FR-13 → vidi Gaps

PRD dodaje 7 novih OQ koje nisu bile u addendum-u (monitoring stack OQ#6, backup retention OQ#7, image pipeline OQ#8, fallback marker UX OQ#9, sticky meni OQ#10, top header mobile OQ#11, OG/Twitter slike OQ#13, social share OQ#14) — to su FR-derived OQs, ne brief drift.

## Product/brand hierarchy from addendum → PRD Glossary §3

- **Wuzheng** → Glossary §3 "Brend (npr. Wuzheng, ...)" match
- **Agri Tracking** (TB / TD / TC serije) → Glossary "Brend (npr. ... Agri Tracking ...)", "Serija — grupa modela istog brenda (npr. TB / TD / TC serija kod Agri Tracking)" match; UJ-1 koristi "Agri Tracking TB804" kao primer
- **Saillong by Maki** → **NOT in PRD Glossary** (Wuzheng/Agri Tracking/Jeegee/HZM/Tulip su nabrojani, Saillong nije) → vidi Gaps
- **Jeegee** sa svim potkategorijama (Osnovna obrada / Priprema / Setva → plugovi/podrivači/gruberi/tanjirače/setvospremači/sejalice) → FR-9 navodi 3 kategorije eksplicitno, FR-10 pominje primere ("Plugovi", "Obrtači 120×120"); Glossary "Brend" lista Jeegee match. Detalji potkategorija (KJ-tip, 1LF-KP331, JMA300, KX300/350, Vega 9, SKS, Hermes, 2BG-250/300) **nisu u Glossary-ju** — to je očekivano (Glossary je vokabular, ne katalog); FR-10 deferruje hijerarhiju "do 3 nivoa", što obuhvata sve to. OK.
- **HZM** (mini/bez-teleskopa/teleskopski/telehendleri sa modelima HZM 1100, 925, 810T/812T/816T/825T, 7335) → FR-11 navodi 4 potkategorije match; Glossary "Brend (npr. ... HZM ...)" match
- **Tulip** (6 kubika / 8 kubika) → FR-12 eksplicitno "2 modela (6 kubika / 8 kubika)" match; Glossary "Brend (npr. ... Tulip)" match

## Gaps & drift

1. **Saillong by Maki nije u Glossary §3.** Brief In Scope eksplicitno nabraja "Wuzheng, Agri Tracking, Saillong by Maki" kao 3 traktor brenda, addendum tabela ima Saillong. PRD Glossary nabraja "Wuzheng, Agri Tracking, Jeegee, HZM, Tulip" — preskočio Saillong. Posledica: arhitektura/UX faza može da previdi treći traktor brend. **Akcija:** dopuniti Glossary "Brend" primere sa Saillong by Maki ili eksplicitno listati sva 3 traktor brenda u FR-7/FR-8 kontekstu.

2. **`[DECISION]` Lorem Ipsum content placeholder strategy nije eksplicitno re-tagovana u PRD-u.** Brief je tag-ovao kao `[DECISION]` da nedostajući tekstovi nisu blokator. PRD spominje "Lorem Ipsum baseline za v1" samo za politiku privatnosti (§6.1) — ne za sav sadržaj uopšte. Akcija: dodati u §6 Constraints ili §10 eksplicitnu stavku "Content placeholder strategy `[DECISION from Brief]` — Lorem Ipsum baseline, klijent puni kroz admin posle dev faze".

3. **Obim sadržaja "~100 proizvoda inicijalno" nije eksplicitno u PRD-u.** Brief constraint navodi tu cifru kao planning hint (utiče na izbor search backend-a). PRD §12 OQ #2 referencira "~100 proizvoda" parenthetički ali ne kao formalni planning input. Akcija: dodati u §6 Constraints ili §8 Operational stavku "Inicijalni obim sadržaja: do ~100 proizvoda (planning hint za search/storage)".

4. **Addendum OQ #10 (Polovna inventar obim — utiče na paginaciju/sortiranje) je samo delimično razrešen.** FR-13 navodi da nema gornje granice ali ne specifikuje paginaciju (npr. items per page) ni default sortiranje. Akcija: dodati u FR-13 paginaciju kao `[ASSUMPTION]` (npr. 20 po strani) ili eksplicitno deferrovati u §12.

5. **Početna §4.1 nema posebnu O nama preview sekciju.** Brief In Scope lista "Hero, O nama, Traktori, Priključna, Radne mašine, Polovna, Priče sa polja preview, Footer" kao home sekcije — to sugeriše da O nama ima preview na home stranici. PRD FR-1/FR-2/FR-3 navodi Hero + 4 kategorije + blog preview, ali ne i O nama preview sekciju na home strani. Minor: može biti da je brief samo nabrojao "ima i O nama strana" a ne preview. Ako je preview namera — gap; ako nije — brief formulacija je dvosmislena. Akcija: potvrditi sa UX fazom da li home traži zaseban "O nama" preview blok ili samo link kroz meni.

**Verdict:** strong alignment. Sve major scope stavke su pokrivene, sve Non-Goals mirror-ovane, sve open questions iz addendum-a su ili razrešene u FR-ovima ili prosleđene u §12. Tri gap-a (Saillong, Lorem Ipsum tag, ~100 proizvoda) su lako otklonjive ispravke; dva (polovna paginacija, home O nama preview) traže UX/arch potvrdu.

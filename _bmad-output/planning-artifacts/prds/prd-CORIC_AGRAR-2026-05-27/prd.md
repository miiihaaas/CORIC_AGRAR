---
title: PRD — Ćorić Agrar veb sajt
status: final
created: 2026-05-27
updated: 2026-05-27
project: CORIC_AGRAR
mode: fast-path
parent_brief: ../briefs/brief-CORIC_AGRAR-2026-05-27/brief.md
---

# PRD: Ćorić Agrar — Veb sajt

## 0. Document Purpose

Interni PRD za **custom Django veb sajt** Ćorić Agrar-a — green-field katalog traktora i poljoprivredne mehanizacije sa lead-gen funkcionalnošću (bez online prodaje). Input za naredne BMad faze (UX → Architecture → Epics & Stories); jedini čitalac i izvršilac je solo dev (Mihas).

Vokabular je ukotvljen u **§3 Glossary**; FR-ovi su globalno numerisani (FR-1..FR-N) radi stabilnih referenci u downstream artefaktima; pretpostavke su sumirane u **§13 Assumptions Index**; tech-how (Django/HTMX/Hetzner) živi u **Product Brief addendum-u** (`../briefs/brief-CORIC_AGRAR-2026-05-27/addendum.md`) i ne ponavlja se ovde.

## 1. Vision

Ćorić Agrar je nedavno dobio status uvoznika traktora i priključne mehanizacije više brendova za srpsko i regionalno tržište — ali nema veb prisustvo srazmerno tom obimu. Ovaj sajt je **online katalog i lead-gen kanal**: poljoprivrednik može da uporedi modele po snazi i ceni, pogleda tehničke specifikacije, preuzme PDF brošuru i pošalje upit ili servisni zahtev bez telefoniranja. Klijent (Ćorić Agrar admin) samostalno održava sadržaj — proizvode, blog, statičke strane, SEO meta podatke — bez dev intervencije.

Sajt je trojezičan (srpski, mađarski, engleski), responzivan, indeksabilan u Google-u i usklađen sa GDPR-om za upravljanje kolačićima. Pun admin panel pokriva CMS, SEO modul, korisničke uloge i dnevni bekap.

Ovo je **launch v1.0** — bez online prodaje, bez korisničkih naloga za kupce, bez integracije sa CRM-om ili ERP-om. Vizija posle launch-a opisana je u Product Brief-u, § Vision.

## 2. Target User

### 2.1 Jobs To Be Done

**Eksterni korisnici (posetioci sajta):**
- Brzo pronaći pravi model traktora ili priključne mašine po snazi, nameni ili ceni
- Pregledati tehničke specifikacije bez potrebe da zove prodavca
- Preuzeti PDF brošuru ili katalog za pregled van mreže ili razgovor sa partnerom
- Podneti servisni zahtev ili upit za rezervni deo van radnog vremena, sa mobilnog telefona
- Pratiti edukativne i iskustvene priče i savete (blog) bez naloga ili pretplate

**Interni korisnik (admin Ćorić Agrar-a):**
- Samostalno dodati novi proizvod kroz strukturirani unos (specifikacije po sekcijama, galerija, brošura)
- Objaviti blog objavu bez tehničke pomoći
- Izmeniti kontakt informacije, navigaciju i GDPR baner kroz UI
- Videti broj poslatih formi i servisnih zahteva na dashboard-u
- Upravljati SEO meta podacima po stranici

**Dev korisnik (interno):**
- Mihas: ovaj PRD daje stabilne FR reference za arhitekturu i razlaganje na priče

### 2.2 Non-Users (v1)

- **Kupci koji žele online checkout** — sajt nije e-commerce; korpa i plaćanje su van obima
- **Korisnici koji žele nalog na sajtu** — postoje samo admin korisnici; posetioci se ne registruju
- **Korisnici mobilne native aplikacije** — samo responzivan web, nema iOS/Android aplikacije
- **B2B partneri sa potrebom za API integracijom** — sajt nema javni API u v1

### 2.3 Key User Journeys

- **UJ-1. Marko (poljoprivrednik, 30ha gazdinstvo) bira novi traktor.**
  > Marko ima 18 godina star traktor i razmišlja o zameni. Subota je uveče i otvara sajt sa laptopa. Klikne **Traktori** u meniju i vidi listing svih brendova sa filterom na vrhu. Postavlja **konjska snaga > 60 KS** i **cena do 25.000 €**. Lista se filtrira HTMX-om bez ponovnog učitavanja. Vidi 3-4 modela i klikne na karticu **Agri Tracking TB804**. Stranica proizvoda: hero sa modelom, otvara akordion **Motor** pa **Transmisija**, preuzima PDF brošuru. Skroluje do forme **Imate pitanja?** — polje *Model* je auto-popunjeno vrednošću „Agri Tracking TB804". Unosi ime, telefon i kratku poruku, šalje. Vidi potvrdu i zatvara sajt.
  > **Edge case:** filter ne vraća rezultate — sistem prikazuje poruku „Nema rezultata, probajte da opustite filtere" sa dugmetom *Resetuj filtere*.

- **UJ-2. Stojan (postojeći kupac) prijavljuje servisni zahtev tokom sezone.**
  > Stojanov Wuzheng se pokvario, sezona setve je u toku. Otvara sajt sa mobilnog telefona, klikne **Servis** u meniju i dolazi na **Servisnu podršku**. Skroluje do forme: unosi ime, telefon i email, bira **Vrsta mehanizacije: Traktor** iz padajuće liste, kuca „Wuzheng" i model u tekstualnom polju i opisuje kvar. Klikne **Dodaj sliku**, fotografiše kvarno mesto i otprema fotografiju. Šalje formu. Vidi potvrdu prijema i kontakt telefon servisa za hitne slučajeve.
  > **Edge case:** ako je slika veća od dozvoljenog limita, sistem prikazuje grešku sa konkretnim limitom (npr. „Maks. 5 MB") pre slanja, a ne nakon.

- **UJ-3. Marijana (sadržaj-admin Ćorić Agrar-a) dodaje novi proizvod.**
  > Stigla je nova isporuka teleskopskog utovarivača HZM 812T. Marijana se prijavljuje u admin panel sa desktop računara. Iz **Dashboard**-a klikne brzu akciju **Dodaj proizvod**. Unosi naziv i opis (na srpskom), bira kategoriju *Teleskopski utovarivači* i brend *HZM*. Otvara sekciju **Specifikacije** i unosi vrednosti za **Motor / Transmisija / Hidraulika / Ostalo** (akordion). Otprema 8 fotografija (prevlačenjem) za galeriju i PDF brošuru. Označava 3 **slična modela** ručno (override automatskih predloga). Mađarsku i englesku verziju ostavlja prazno za sada. Status: **Skica**. Sačuva. Posle ručka se vraća radi pravopisne provere i postavlja status **Objavljeno**.
  > **Edge case:** ako Marijana pokuša da postavi *Objavljeno* dok je obavezno polje *Naziv* prazno, sistem joj javlja koje polje konkretno nedostaje.

## 3. Glossary

Termini koje downstream artefakti (UX, Architecture, Epics) i sav PRD koriste verbatim. Sinonimi nisu dozvoljeni.

**Sadržaj kataloga**
- **Proizvod** — pojedinačan model traktora ili mehanizacije. Pripada tačno jednom Brendu i jednoj Kategoriji.
- **Brend** — proizvođač (npr. Wuzheng, Agri Tracking, Saillong by Maki, Jeegee, HZM, Tulip). Brend može da ima više **Modela**.
- **Model** — sinonim za Proizvod u kontekstu navigacije; tehnički isti entitet.
- **Serija** — grupa modela istog brenda (npr. TB / TD / TC serija kod Agri Tracking). Nivo između Brenda i Modela kod traktora.
- **Kategorija** — primarna klasifikacija proizvoda: *Traktori*, *Priključna mehanizacija*, *Radne mašine*, *MIX prikolice*, *Polovna mehanizacija*.
- **Potkategorija** — dalja klasifikacija unutar Kategorije po nameni (npr. *Plugovi*, *Tanjirače*, *Telehendleri*).

**Stranica proizvoda**
- **Specifikacije** — strukturirani tehnički podaci, organizovani u 4 sekcije akordiona: *Motor*, *Transmisija*, *Hidraulika*, *Ostalo*. Svaka sekcija ima slobodne par-vrednosti.
- **Galerija** — niz fotografija proizvoda prikazan kao karusel; klik otvara **Lightbox**.
- **Lightbox** — modal prikaz pojedinačne fotografije sa navigacijom prethodna/sledeća.
- **Akordion** — UI komponenta sa proširi/skupi sekcijama.
- **Brošura** — PDF dokument modela, dostupan za preuzimanje sa stranice proizvoda.
- **Katalog** — PDF dokument brenda (ne modela), dostupan sa stranice brenda.
- **Testimonijal** — citat kupca, ime, lokacija i fotografija, vezan za proizvod ili brend; prikazuje se u slider sekciji *Iz prve ruke* (proizvod) ili *Zadovoljni kupci* (brend).
- **Slični modeli** — 2-4 modela srodna trenutnom; izvor: hibrid (auto po brendu/seriji + admin override).
- **Serija layout** — vizuelni način prikaza modela na stranici brenda po seriji: *Grid* (2-col kartice) ili *Extended* (1 red po modelu sa akordion-tabelom specifikacija). Admin označava layout po seriji.
- **Varijanta proizvoda** — pod-element proizvoda koji prikazuje alternative dela (npr. tip daske za plug obrtač, tip rotora za tanjiraču). Informativna, ne transakciona.

**Specifični elementi**
- **Hero sekcija** — full-width gornja sekcija na većini strana, sa slikom ili video pozadinom.
- **Ponavljajući element** — vizuelni motiv: pravougaonik širi nego viši, sa malim radijusom i tankim belim koncentričnim linijama u uglu (simbolika točkova/brazdi). Boja varira po brendu.
- **Vremenska lenta** — vizuelna komponenta na stranici *O nama* koja prikazuje ključne momente u razvoju firme hronološki.
- **Masonry** — galerija sa slikama različitih visina zbijenih bez razmaka; koristi se na stranici *O nama*.
- **Statistike brenda** — 4 numeričke vrednosti na stranici brenda (ikona + broj) sa count-up animacijom pri skrolovanju.

**Lead-gen**
- **Forma** — opšti termin za bilo koju kontaktnu ili zahtevnu formu na sajtu. Sve forme se procesiraju kroz HTMX.
- **Kontakt forma** — opšta forma za upite, smeštena na strani *Kontakt*.
- **Upit za model** — forma na stranici proizvoda sa auto-popunjenim poljem *Model*.
- **Servisni zahtev** — forma za prijavu kvara, smeštena na strani *Servis*.
- **Upit za rezervni deo** — forma za naručivanje rezervnih delova, smeštena na strani *Rezervni delovi*.
- **Lead** — bilo koja popunjena forma koja generiše email klijentu; predstavlja zainteresovanog potencijalnog kupca.

**Blog**
- **Priče sa polja** — blog sekcija sajta. (Naziv brenda; vizuelno različito od termina „Blog" u admin panelu, radi jasnoće.)
- **Objava** — pojedinačan blog post.
- **Kategorija (bloga)** — taksonomija blog objava (npr. *Saveti*, *Vesti*, *Iskustva kupaca*). Definiše admin naknadno.
- **Tag** — slobodna oznaka koja se može vezati za više objava, nezavisno od kategorije.

**Admin / autorizacija**
- **Admin** — korisnik admin panela; uvek tip *Superadmin* ili *Editor*. Posetioci sajta nisu Admin.
- **Superadmin** — najviša uloga; ima sve permisije, uključujući upravljanje korisnicima.
- **Editor** — uloga sa pristupom CRUD-u sadržaja, ali bez upravljanja korisnicima.
- **Status (sadržaja)** — *Objavljeno* / *Skica* / *Arhivirano*. Primenjuje se na Proizvod i Objavu.
- **WYSIWYG editor** — bogati tekst editor u admin panelu za blog objave.

**SEO i analitika**
- **SEO meta** — *meta title* i *meta description* po stranici i po proizvodu.
- **Sitemap** — `sitemap.xml` koji generiše sistem na osnovu objavljenog sadržaja.
- **Redirect (301)** — pravilo trajnog preusmeravanja sa stare na novu URL putanju; admin može da ga kreira i da njime upravlja.
- **Hreflang** — HTML atribut koji označava jezičku verziju strane (sr / hu / en) za pretraživače.

**Lokalizacija**
- **Locale** — jedna od tri jezičke verzije: *sr* (primarni), *hu*, *en*.
- **Fallback** — kada neki jezik nema unesen sadržaj polja, sistem prikazuje srpsku verziju sa diskretnim markerom *(automatski prevod nije dostupan — ovo je fallback na sr)*.

**Privacy / GDPR**
- **GDPR baner** — UI komponenta koja se prikazuje pri prvoj poseti i traži saglasnost za kolačiće.
- **Kolačić** — HTTP cookie; klasifikovan kao *Neophodan*, *Analitički*, *Marketing*.
- **Tracking pixel** — Facebook Pixel skripta; aktivira se samo posle saglasnosti za *Marketing* kolačiće.

## 4. Features

### 4.1 Početna strana

**Description:** Početna je reprezentativna strana koja vodi posetioca kroz kompaniju, brendove i ključne kategorije proizvoda. Strukturira posetu u sekcije sa jasnim CTA dugmadima ka dubljim stranama. Realizuje deo UJ-1 (orijentacija pre filtera traktora) i privlači organski saobraćaj ka brend stranama kroz SEO.

#### FR-1: Hero sekcija sa pretragom i top headerom

Posetilac vidi full-width hero blok sa slikom traktora i naslovom kao prvi sadržaj.

**Consequences (testable):**
- Hero zauzima najmanje 70% visine viewporta na desktopu (lg breakpoint i veći)
- Top header (adresa i telefon) je vidljiv iznad menija
- Polje za pretragu nalazi se na desnom kraju glavnog menija
- Hero pozadina koristi sliku ili video iz admin podešavanja (može se promeniti bez deploy-a)

#### FR-2: Sekcije Traktori / Priključna mehanizacija / Radne mašine / Polovna mehanizacija

Posetilac vidi posebnu sekciju za svaku od 4 kategorije proizvoda, sa kratkim opisom i CTA dugmetom ka odgovarajućoj strani.

**Consequences (testable):**
- Sekcija Traktori prikazuje sve aktivne brendove sa logom i slikom reprezentativnog modela; brendovi sa flagom *Uskoro* prikazuju se sa odgovarajućom oznakom
- Klik na logo, sliku ili CTA dugme vodi na stranicu brenda (sve tri zone su klikabilne)
- Sekcije *Priključna mehanizacija*, *Radne mašine* i *Polovna mehanizacija* — baner format sa CTA dugmetom ka odgovarajućoj strani

#### FR-3: Sekcija Priče sa polja preview

Posetilac vidi 2 najnovije blog objave kao kartice na pozadinskoj slici sa zatalasanom gornjom ivicom.

**Consequences (testable):**
- Kartice prikazuju naslov, kratak izvod (perex) i CTA *SAZNAJ VIŠE*
- Kartice **ne** prikazuju naslovnu sliku objave (radi vizuelne čistoće zbog pozadine)
- Klik vodi na pojedinačnu objavu


### 4.2 Statičke strane

**Description:** Strane sa relativno stabilnim sadržajem koje admin uređuje kroz CMS. Pokriva *O nama* i *Kontakt*. Realizuje sekundarne potrebe posetioca (poverenje, kontakt informacije).

#### FR-4: Stranica O nama

Posetilac vidi predstavljanje kompanije u sledećoj strukturi: hero (slika ili video), tekst, vremenska lenta, masonry galerija.

**Consequences (testable):**
- Hero podržava i sliku i video kao pozadinu (admin bira)
- Vremenska lenta prihvata 3-N događaja, svaki sa godinom + naslovom + kratkim opisom
- Masonry galerija prihvata 6-N fotografija različitih dimenzija; render je bez razmaka
- Klik na sliku u galeriji otvara Lightbox sa navigacijom prethodna/sledeća

#### FR-5: Stranica Kontakt

Posetilac vidi kontakt informacije, kontakt formu i mapu lokacije.

**Consequences (testable):**
- Prikazane informacije: adresa, telefoni (prodaja i servis odvojeno), email, radno vreme, linkovi ka društvenim mrežama
- Kontakt forma je opisana u FR-19 (Kontakt forma)
- Mapa je ugrađena Google Maps karta sa pinom na lokaciji kompanije
- Sve informacije se uređuju kroz Admin → Podešavanja sajta

### 4.3 Katalog traktora

**Description:** Glavna prodajna strana — listing svih modela traktora kroz sve brendove, sa filterima i navigacijom ka brend stranama. Realizuje UJ-1.


#### FR-6: Listing modela sa filterima

Posetilac filtrira traktore po konjskoj snazi, godištu i ceni; rezultati se ažuriraju bez ponovnog učitavanja stranice.

**Consequences (testable):**
- Filter polja: *Konjska snaga* (klizač ili min/max), *Godište* (raspon), *Cena* (klizač min/max)
- Filtriranje se izvršava preko HTMX-a (sa strane servera, bez ponovnog učitavanja cele strane)
- Rezultati su prikazani kao kartice (slika, naziv, kratak opis, CTA *OPŠIRNIJE*); jedan model = jedna kartica; maksimalna širina kartice je responzivna
- Kartice su grupisane po brendu (vizuelno odvojene) na podrazumevanom listingu
- Ako filter ne vraća rezultate, prikazuje se poruka *Nema rezultata* sa CTA *Resetuj filtere*
- URL parametri reflektuju aktivne filtere (omogućava deljenje linka)

#### FR-7: Logotipi brendova kao navigacija

Posetilac vidi logotipe svih aktivnih brendova na vrhu strane Traktori; klik vodi na stranicu brenda.

**Consequences (testable):**
- Brendovi sa flagom *Uskoro* su prikazani sa oznakom i nemaju aktivnu navigaciju
- Klik na logo vodi na stranicu brenda

#### FR-8: Stranica brenda traktora

Posetilac na stranici brenda vidi: hero brenda, statistike (4 brojke), citat/banner, modele grupisane po seriji, slider zadovoljnih kupaca, preuzmi katalog banner.

**Consequences (testable):**
- Hero koristi *Ponavljajući element* (vidi Glossary) za naslov i kratak opis; boja elementa se definiše po brendu u admin panelu
- Statistike sa count-up animacijom pri skrolovanju
- Modeli su grupisani po seriji. Admin može po seriji da označi **Serija layout**: *Grid* (2-col kartice sa slikom, nazivom, kratkim opisom i CTA *OPŠIRNIJE*) ili *Extended* (1 red po modelu sa krupnom slikom levo i akordion-tabelom specifikacija desno, plus CTA *OPŠIRNIJE*). Podrazumevano je *Grid*; *Extended* se koristi za serije sa složenijim specifikacijama
- Akordion (samo u layoutu *Extended*) ima 4 sekcije: Motor / Transmisija / Hidraulika / Ostalo
- Slider testimonijala sa indikatorima
- CTA *Preuzmi katalog* pokreće preuzimanje PDF kataloga brenda

### 4.4 Katalog mehanizacije

**Description:** Sekcija *Mehanizacija* u meniju je neaktivan link (`#`); klik otvara padajuću listu sa 4 podstrane. Svaka podstrana ima sopstvenu strukturu, prilagođenu brendu i kategoriji.

#### FR-9: Stranica Priključna mehanizacija (Jeegee)

Posetilac vidi hero brenda Jeegee i 3 kategorije (Osnovna obrada zemljišta / Priprema zemljišta / Mašine za setvu) kao kartice ka odgovarajućim potkategorijama.

**Consequences (testable):**
- Hero koristi plavu varijantu *Ponavljajućeg elementa* (Jeegee boja)
- 3 kategorije su prikazane kao kartice sa ikonom, nazivom i kratkim opisom
- Klik vodi na podstranu kategorije

#### FR-10: Potkategorije priključne mehanizacije

Posetilac na podstrani kategorije vidi modele iz te potkategorije (npr. *Plugovi* podstrana prikazuje plugove ravnjake i plugove obrtače dalje organizovane po debljini grede).

**Consequences (testable):**
- Hijerarhija je duboka do **4 nivoa** (Kategorija → Podkategorija → Pod-podkategorija → grupisanje po atributu); npr. *Priključna mehanizacija* → *Osnovna obrada* → *Plugovi obrtači* → grupisanje po debljini grede (*90×90*, *100×100*, *120×120*, *140×140*, *160×160*)
- Svaki model je prikazan kao kartica sa CTA dugmetom ka stranici proizvoda

#### FR-11: Stranica Radne mašine (HZM)

Posetilac vidi hero brenda HZM i 4 potkategorije (Mini utovarivači / Utovarivači bez teleskopa / Teleskopski utovarivači / Telehendleri).

**Consequences (testable):**
- Struktura je analogna FR-9 (Jeegee); boja brenda primenjuje se na *Ponavljajući element*
- Listing modela po potkategoriji

#### FR-12: Stranica MIX prikolice (Tulip)

Posetilac vidi hero brenda Tulip i 2 modela (6 kubika / 8 kubika).

**Consequences (testable):**
- Struktura: hero, listing modela, sekcija zadovoljni kupci i preuzmi katalog
- Uporedna tabela dva modela (dimenzije) prikazana je na stranici

#### FR-13: Stranica Polovna mehanizacija sa filterima

Posetilac filtrira polovnu mehanizaciju po kategoriji, brendu, ceni, godini, stanju mašine.

**Consequences (testable):**
- Filter polja: *Kategorija* (padajuća lista: Traktori / Priključna / Radna mašina / Ostalo), *Brend* (padajuća lista), *Cena* (klizač min/max), *Godina* (raspon), *Stanje* (padajuća lista)
- Filtriranje preko HTMX-a (bez ponovnog učitavanja)
- Kartica sadrži sliku, naziv, godinu, stanje i cenu
- URL parametri reflektuju aktivne filtere
- Polovna mehanizacija nema fiksan obim — admin upravlja inventarom; sistem ne pretpostavlja gornju granicu broja stavki
- Paginacija: 12 stavki po strani `[ASSUMPTION]`
- Podrazumevano sortiranje: po datumu dodavanja (najnovije prvo); posetilac može da bira: cena (rastuće/opadajuće), godina (opadajuće)

### 4.5 Stranica pojedinačnog proizvoda

**Description:** Zajednički template za sve modele (traktori i mehanizacija). Realizuje detaljan deo UJ-1 (donošenje odluke) i generiše većinu lead-ova.

#### FR-14: Hero proizvoda sa ključnim karakteristikama

Posetilac vidi full-width hero sa fotografijom proizvoda, logom brenda, nazivom modela i do 3 ključne karakteristike u bullet formatu na *Ponavljajućem elementu*.

**Consequences (testable):**
- Hero podržava sliku (statičnu)
- Do 3 bullet karakteristike — admin može da unese 0-3; sistem renderuje samo unete

#### FR-15: Sekcija Opis proizvoda

Posetilac vidi duži tekstualni opis modela ispod hero-a.

**Consequences (testable):**
- Polje prima rich text (paragrafi, bold, italic, liste) — bez slika u opisu
- Sadržaj se uređuje u admin panelu po lokalizaciji

#### FR-16: Galerija proizvoda sa Lightbox-om

Posetilac vidi horizontalan karusel fotografija; klik na sličicu otvara Lightbox sa navigacijom.

**Consequences (testable):**
- Karusel podržava prevlačenje na touch uređajima
- Lightbox podržava prethodnu/sledeću i zatvaranje
- Esc zatvara Lightbox
- Galerija prima 1-N fotografija po proizvodu

#### FR-17: Tabela tehničkih specifikacija u akordionu

Posetilac vidi tehničke specifikacije organizovane u 4 sekcije akordiona: Motor / Transmisija / Hidraulika / Ostalo.

**Consequences (testable):**
- Svaka sekcija je nezavisno proširiva/skupljiva
- Sekcija ima parove ključ–vrednost (slobodan unos u adminu)
- Tabele su responzivne; na mobilnim ekranima se renderuju vertikalno (oznaka iznad vrednosti)
- Prazne sekcije se ne prikazuju (ako *Hidraulika* nema unete podatke, sekcija se sakriva)

#### FR-18: Preuzimanje PDF brošure

Posetilac može da preuzme PDF brošuru modela.

**Consequences (testable):**
- Brošura se prikazuje sa minijaturom naslovne strane i dugmetom *PREUZMI*
- Klik pokreće preuzimanje ili otvara PDF u novom tabu (po podrazumevanom ponašanju browsera)
- Ako brošura nije otpremljena, sekcija se ne prikazuje

#### FR-19: Forma "Upit za model" sa auto-popunjenim modelom

Posetilac šalje upit direktno sa stranice proizvoda; polje *Model* je auto-popunjeno.

**Consequences (testable):**
- Polja: Ime i prezime *, Email *, Telefon, Model (auto-popunjen, samo za čitanje), Poruka
- Validacija sa strane klijenta (HTML5) i sa strane servera
- Posle uspešnog slanja: vidljiva potvrda na ekranu (toast ili modal)
- Email se šalje na konfigurisanu adresu (admin podešavanja) — sa naslovom koji uključuje naziv modela
- Realizuje vrhunac UJ-1

#### FR-20: Slični modeli (hibrid auto + admin override)

Posetilac vidi 2-4 slična modela na dnu stranice.

**Consequences (testable):**
- Podrazumevani izvor: automatski izbor 2-4 modela iz iste serije ili istog brenda
- Admin može u proizvodu ručno da označi listu sličnih modela; admin override **u celini zamenjuje** automatske predloge
- Prikazani su kao kartice (slika, naziv, kratak opis, CTA *OPŠIRNIJE*)

#### FR-21: Sekcija Iz prve ruke (testimonijali za proizvod)

Posetilac vidi slider testimonijala vezanih za konkretan proizvod.

**Consequences (testable):**
- Slider sa indikatorima prethodna/sledeća
- Svaki slajd: fotografija, citat, ime i lokacija
- Ako proizvod nema testimonijala, sekcija se ne prikazuje

#### FR-48: Variant selektor proizvoda

Proizvod može da ima 0-N **Varijanti proizvoda** — alternativne komponente koje se prikazuju informativno (npr. tip daske za plugove obrtače, tip rotora za tanjirače). Posetilac vidi blok *Varijante* ako proizvod ima ≥1 varijantu; klik na varijantu otvara Lightbox sa zoom slikom.

**Consequences (testable):**
- Varijantni blok se prikazuje samo ako proizvod ima ≥1 varijantu (nema praznog kontejnera)
- Svaka varijanta: slika, naziv, šifra (opciono) i kratak opis (opciono)
- Varijante prikazane u responzivnom redu kartica: 1-4 po redu, zavisno od širine ekrana
- Klik na karticu varijante otvara Lightbox sa zoom slikom (čista vizuelna inspekcija, **bez sporednih efekata** — ne menja stanje stranice i ne pokreće formu)
- Varijante su **informativne** — ne biraju se za kupovinu (nema dodavanja u korpu, nema cene zavisne od varijante)
- Admin definiše varijante po proizvodu kroz namensku sekciju u CRUD-u proizvoda (proširenje FR-36)

### 4.6 Servis

**Description:** Sekcija Servis pruža informacije o servisnoj podršci i omogućava prijavu servisnog zahteva i upita za rezervni deo. Realizuje UJ-2.

#### FR-22: Stranica Servisna podrška sa formom

Posetilac vidi opis servisne podrške i podnosi servisni zahtev kroz formu.

**Consequences (testable):**
- Informacioni deo: brendovi koji se servisiraju, lokacija, radno vreme, kontakt
- Polja forme: Ime i prezime *, Telefon *, Email, Vrsta mehanizacije (padajuća lista: Traktor / Priključna / Radna mašina / Ostalo), Brend i model (slobodan tekst), Opis kvara/usluge *, Foto (opciono, više fajlova)
- Otpremanje fotografije prihvata JPG/PNG; maksimalna veličina po fajlu validira se pre slanja, sa konkretnom porukom
- Posle slanja: potvrda na ekranu i email na serviserskoj adresi (admin konfiguriše)
- Realizuje vrhunac UJ-2

#### FR-23: Stranica Rezervni delovi sa formom

Posetilac podnosi upit za rezervni deo kroz formu.

**Consequences (testable):**
- Polja forme: Model traktora *, Rezervni deo *, Dodatni opis (opc.), Slika (opc.), Ime i prezime *, Telefon *, Email *, Način plaćanja (padajuća lista: pouzeće / predračun), Način preuzimanja (padajuća lista: dostava / lično), Napomena (opc.)
- Posle slanja: potvrda i email klijentu

### 4.7 Blog (Priče sa polja)

**Description:** Blog sekcija sa indeksom, pojedinačnim objavama, kategorijama i tagovima. Edukativni, iskustveni i vesti sadržaj.

#### FR-24: Indeks blog objava

Posetilac vidi listu objava sortiranih od najnovije ka starijoj.

**Consequences (testable):**
- Svaka objava je prikazana kao kartica sa: naslovna slika, datum, naslov, kratki izvod (perex), CTA *SAZNAJ VIŠE*
- Paginacija (podrazumevano 10 objava po strani — `[ASSUMPTION]`)
- Filter po kategoriji (padajuća lista ili tabovi)

#### FR-25: Stranica pojedinačne objave

Posetilac čita pojedinačnu objavu.

**Consequences (testable):**
- Prikaz: naslovna slika, datum, naslov, telo (rich text sa inline slikama i ugrađenim video sadržajem)
- Sekcija *Slične objave* na dnu (2-4 objave iz iste kategorije)
- Dugmad za deljenje na društvenim mrežama `[ASSUMPTION]` — potvrditi u UX fazi

#### FR-26: Kategorije i tagovi bloga

Posetilac može da filtrira objave po kategoriji ili tagu.

**Consequences (testable):**
- Klik na kategoriju vodi na listing samo te kategorije
- Klik na tag vodi na listing svih objava sa tim tagom
- Kategorije i tagovi su slobodni — admin definiše šemu naknadno (vidi FR-39 Blog admin)

### 4.8 Pretraga i navigacija

#### FR-27: Globalna pretraga

Posetilac koristi polje za pretragu u meniju za pretragu sajta.

**Consequences (testable):**
- Pretraga obuhvata: nazive proizvoda, opise proizvoda, naslove blog objava i perex i telo blog objava
- Rezultati su grupisani po tipu (Proizvodi / Objave)
- Pretraga uvažava aktivnu lokalizaciju (rezultati na trenutnom jeziku posetioca)
- **Otpornost na dijakritike** — `ž/š/č/ć/đ` i njihove varijante bez dijakritika daju iste rezultate; otpornost na velika i mala slova
- **Minimalna dužina upita: 2 znaka** `[ASSUMPTION]`; kraći upit prikazuje napomenu *„Unesi makar 2 znaka"*
- **Rangiranje:** po relevance score-u (broj i pozicija pojavljivanja — pogodak u nazivu rangira više od pogotka u telu); tie-break po datumu (najnoviji prvi za blog, po datumu dodavanja za proizvode)
- **Prazno stanje:** ako 0 rezultata, prikazuje se poruka *„Nema rezultata za '{query}'"* i CTA blok sa najpopularnijim kategorijama i brendovima

#### FR-28: Glavni meni i navigacija

Posetilac koristi glavni meni za navigaciju kroz sajt.

**Consequences (testable):**
- Meni je transparentan na hero sekcijama (preliva se sa slikom u pozadini)
- Lepljivi (sticky) meni pri skrolovanju `[ASSUMPTION]` — potvrditi u UX fazi
- Mehanizacija je padajuća lista ka 4 podstrane (FR-9 do FR-13)
- Hamburger meni na mobilnim ekranima
- Polje za pretragu integrisano je na desnom kraju

#### FR-29: Top header

Posetilac vidi top header iznad glavnog menija sa adresom i telefonom.

**Consequences (testable):**
- Adresa i telefon su vidljivi na desktopu i tabletu
- Na mobilnim ekranima top header se kondenzuje ili sakriva `[ASSUMPTION]`

#### FR-30: Footer

Posetilac vidi footer na dnu svake strane.

**Consequences (testable):**
- Sadržaj: navigacioni linkovi po kategorijama (Proizvodi / O nama / Najnovije vesti), logo (centriran iznad navigacije), linkovi ka društvenim mrežama, kontakt informacije
- Pozadina: zeleni gradijent (tamnija → svetlija)
- Tanka bela linija odvaja oznaku autorskih prava od ostatka

### 4.9 Trojezičnost

#### FR-31: Prebacivanje jezika

Posetilac može da prebaci jezik (sr / hu / en) sa bilo koje strane.

**Consequences (testable):**
- Prekidač jezika je vidljiv u headeru ili meniju na svim stranama
- Promena jezika čuva trenutnu strukturnu poziciju (npr. ako sam na `/sr/traktori/agri-tracking`, prelaskom na *hu* idem na `/hu/traktori/agri-tracking`, a ne na početnu)
- URL prefiks reflektuje lokalizaciju (`/sr/`, `/hu/`, `/en/`)

#### FR-32: Fallback strategija

Posetilac vidi srpski sadržaj kao fallback kada izabrana lokalizacija nije popunjena.

**Consequences (testable):**
- Ako Title na *hu* nije unesen, prikazuje se *sr* verzija
- Sistem prikazuje diskretni vizuelni marker da je sadržaj na drugom jeziku (bedž ili tooltip — UX odluka)
- Fallback je polje po polje (a ne strana po strana)
- Fallback se ne primenjuje na URL slug-ove (oni moraju biti specifični po jeziku ili podrazumevano koriste *sr* — `[ASSUMPTION]` — potvrditi u arhitekturi)

#### FR-33: SEO hreflang oznake

Sistem označava jezičke verzije svake strane sa hreflang atributima.

**Consequences (testable):**
- Svaka strana ima `<link rel="alternate" hreflang="..."` tagove za sve tri lokalizacije
- `x-default` ukazuje na *sr* verziju
- Sitemap takođe lista sve jezičke varijante

### 4.10 Admin panel — Dashboard i upravljanje sadržajem

**Description:** Admin panel je dostupan isključivo autorizovanim korisnicima na zasebnom URL prefiksu. Realizuje UJ-3 i sve ostale autorske i uredničke tokove.

#### FR-34: Login i autentikacija admin-a

Admin se prijavljuje email-om i lozinkom.

**Consequences (testable):**
- Login forma sa poljima za email i lozinku
- Sesija ističe nakon perioda neaktivnosti (`[ASSUMPTION]` — 4h, potvrditi)
- Neuspešni pokušaji prijave su rate-limited (`[ASSUMPTION]` — 5 pokušaja / 15 min IP, potvrditi)
- Reset lozinke se obavlja preko link-a u email-u

#### FR-35: Dashboard

Admin vidi pregled stanja sajta po prijavi.

**Consequences (testable):**
- Prikazane statistike:
  - Posete za 7/30 dana (iz GA)
  - **Lead-ovi tekućeg meseca, segmentovani po vrsti forme:** Opšti kontakt | Upit za model | Servisni zahtev | Upit za rezervni deo (sa ukupnim zbirom)
  - Ukupan broj objavljenih proizvoda
  - Ukupan broj objavljenih blog objava
- Brze akcije: *Dodaj proizvod*, *Dodaj blog objavu*

#### FR-36: CRUD proizvoda

Admin (Superadmin ili Editor) može da dodaje, menja, briše proizvode.

**Consequences (testable):**
- Polja: naziv, opis, kategorija, brend, serija, ključne karakteristike (do 3), specifikacije (4 sekcije), galerija (otpremanje više fajlova), brošura (PDF), testimonijali (više), slični modeli (ručna oznaka, FR-20), **varijante** (0-N, FR-48)
- Status: Objavljeno / Skica / Arhivirano
- Unos po lokalizaciji (sr / hu / en) — sr je obavezan; hu/en su opcioni (fallback radi)
- Validacija: pre prelaska u *Objavljeno*, sr verzija mora imati naziv, sliku galerije i barem jednu sekciju specifikacija
- Realizuje UJ-3

#### FR-37: CRUD brendova

Admin upravlja brendovima.

**Consequences (testable):**
- Polja: naziv, logo, opis, hero slika, statistike (do 4, ikona + broj + oznaka), katalog PDF, boja brenda (za *Ponavljajući element*), flag *Uskoro*
- Brend može imati 0-N Serija (kao dečji entiteti)
- Unos po lokalizaciji

#### FR-38: CRUD kategorija i potkategorija

Admin upravlja taksonomijom kategorija mehanizacije.

**Consequences (testable):**
- Hijerarhija do 3 nivoa
- Polja: naziv, slug, slika ili ikona, kratak opis, redosled prikaza
- Unos po lokalizaciji

#### FR-39: CRUD blog objava sa WYSIWYG editorom

Admin piše i objavljuje blog objave.

**Consequences (testable):**
- WYSIWYG editor podržava: paragrafe, naslove, bold i italic, link, listu, sliku unutar teksta, ugrađen video
- Polja: naslov, slug, naslovna slika, perex, telo (WYSIWYG), kategorija (vezivanje), tagovi (slobodni — kreiraju se u liniji), status, datum objave
- Unos po lokalizaciji

#### FR-40: CRUD statičkih strana

Admin uređuje statički sadržaj strana O nama, Servis, itd.

**Consequences (testable):**
- WYSIWYG editor za telo
- Sekcije se uređuju nezavisno (npr. vremenska lenta je zaseban widget na strani O nama)
- Galerija O nama otprema se kao set fotografija

### 4.11 Admin panel — Korisnici i pristup

#### FR-41: Upravljanje admin korisnicima

Superadmin kreira, menja, briše admin korisnike.

**Consequences (testable):**
- Polja: ime, email, uloga (Superadmin / Editor), aktivan/neaktivan
- Uloga Editor ima sve permisije osim upravljanja korisnicima
- Superadmin može da promeni lozinku drugog korisnika (resetuje je na privremenu)

### 4.12 Admin panel — SEO

#### FR-42: SEO meta po stranici i proizvodu

Admin unosi meta title i meta description za svaku stranu i proizvod.

**Consequences (testable):**
- Polje *meta title* (limit 60 karaktera, blago upozorenje iznad)
- Polje *meta description* (limit 160 karaktera, blago upozorenje iznad)
- Unos po lokalizaciji
- Ako nije unet, sistem koristi podrazumevani (naziv stranice + naziv firme)

#### FR-43: Upravljanje sitemap-om

Sistem generiše `sitemap.xml` automatski; admin može da isključi pojedinačne strane iz sitemap-a.

**Consequences (testable):**
- Sitemap sadrži sve objavljene proizvode, brendove, kategorije, statičke strane i blog objave
- Sitemap lista sve 3 jezičke varijante svake stavke (sa hreflang)
- Admin može da postavi flag *isključi iz sitemap-a* na pojedinačnoj strani ili proizvodu

#### FR-44: Redirect manager (301)

Admin može da kreira pravila trajnog preusmeravanja.

**Consequences (testable):**
- Polja po pravilu: stari URL, novi URL, datum kreiranja
- Sistem primenjuje pravilo na sve zahteve ka starom URL-u sa statusom 301
- Lista postojećih pravila vidljiva je u tabeli sa pretragom i sortiranjem

### 4.13 Admin panel — Podešavanja sajta

#### FR-45: Opšta podešavanja

Admin uređuje globalna podešavanja: naziv sajta, kontakt informacije, logotip, favicon, hero pozadine.

**Consequences (testable):**
- Polja: naziv sajta, telefoni (prodaja, servis), email, adresa, radno vreme, linkovi društvenih mreža, logotip (otpremanje), favicon (otpremanje)
- Email adrese za prijem formi konfigurišu se ovde (mogu biti različite po vrsti forme)

#### FR-46: Navigacioni meni

Admin upravlja glavnim menijem.

**Consequences (testable):**
- Stavke menija sa: oznaka (po lokalizaciji), URL ili link na unutrašnji entitet, redosled
- Padajuće podstavke (npr. Mehanizacija)
- Aktivacija ili deaktivacija pojedinačnih stavki

#### FR-47: GDPR baner i politika kolačića

Admin uređuje sadržaj GDPR banera i politike kolačića.

**Consequences (testable):**
- GDPR baner se prikazuje pri prvoj poseti
- Posetilac može da: prihvati sve, odbije sve (osim neophodnih) ili podesi po kategoriji (Neophodan / Analitički / Marketing)
- Izbor se čuva u kolačiću (dugog veka)
- Tracking pixel (FB) aktivira se samo posle prihvatanja *Marketing*
- GA aktivira se samo posle prihvatanja *Analitički*
- Stranica *Politika kolačića* je dostupna; sadržaj se uređuje u admin panelu

## 5. Cross-Cutting NFRs

### 5.1 Performance

- Sajt mora učitavati ključne strane (Početna, listing proizvoda, stranica proizvoda) u **realističnom vremenu na 4G mobilnoj vezi** — konkretni LCP/TTFB ciljevi definišu se u **arhitekturi**. `[OPEN → arhitektura]`
- HTMX filter zahtevi odgovaraju u manje od 500ms na nekeširane upite `[ASSUMPTION]` — potvrditi u arhitekturi
- Slike proizvoda i galerije serviraju se u responzivnim veličinama (srcset / picture); originalna rezolucija ne ide direktno u browser

### 5.2 Pristupačnost (Accessibility)

- Sajt prati **WCAG 2.1 nivo AA** kao polaznu osnovu `[ASSUMPTION]`
- Sve forme imaju vidljive labele i ARIA atribute
- Akordion i Lightbox su navigabilni tastaturom
- Kontrasti boja se proveravaju (zelena paleta na tamnoj pozadini je rizična)

### 5.3 Sigurnost (Security)

- Admin panel zahteva HTTPS (automatska redirekcija sa HTTP)
- Lozinke su hešovane (Django default — koristi bcrypt/argon2)
- CSRF zaštita na svim formama (Django default)
- Rate limiting na forme (FR-19, FR-22, FR-23, FR-5) radi sprečavanja zloupotrebe `[ASSUMPTION]` — 10 zahteva / 15 min IP, potvrditi
- Otpremljeni fajlovi: validacija MIME tipa i veličine; samo PDF i slike
- Admin sesija ističe nakon neaktivnosti (FR-34)

### 5.4 SEO i indeksabilnost

- Sve objavljene strane su indeksabilne sa validnim title-om, meta opisom i hreflang-om
- `robots.txt` postoji i dozvoljava ključne strane
- `sitemap.xml` se generiše dinamički (FR-43)
- URL-ovi su čitljivi i uvažavaju lokalizaciju
- Open Graph i Twitter Card meta tagovi za blog objave i proizvode `[ASSUMPTION]` — potvrditi

### 5.5 Pouzdanost (Reliability)

- Sajt mora biti dostupan **24/7** sa razumnim ciljem dostupnosti (target u arhitekturi) `[OPEN → arhitektura]`
- Bekap se izvršava dnevno (operational)

### 5.6 Browser podrška

- Najnovije 2 verzije Chrome-a, Firefox-a, Safari-ja i Edge-a
- iOS Safari i Android Chrome u poslednje 2 verzije
- IE i legacy Edge nisu podržani `[ASSUMPTION]`

## 6. Constraints & Guardrails

### 6.1 Privacy / GDPR

- Sajt ne čuva PII (Personally Identifiable Information) o neprijavljenim posetiocima osim u kontekstu formi koje su oni svesno popunili
- Forme čuvaju polja samo dok email ne bude uspešno poslat administratoru — daljinska perzistencija (npr. ticket sistem) nije u v1
- GDPR baner traži saglasnost za nepotrebne kolačiće pre aktivacije tracking-a (FR-47)
- Politika kolačića je javno dostupna; politika privatnosti `[OPEN]` — sadržaj treba da dostavi klijent (Lorem Ipsum kao polazna osnova za v1)

### 6.2 Sigurnost

- Admin korisnici se ne registruju automatski — kreira ih isključivo Superadmin
- Ostali sigurnosni zahtevi (HTTPS, CSRF, hešovanje, rate-limiting, validacija otpremanja) su u §5.3

### 6.3 Content placeholder strategija `[DECISION]`

- Svi tekstualni placeholderi (statičke strane, opisi proizvoda, blog objave, politika privatnosti, slogani) idu kao **Lorem Ipsum** u dev fazi; klijent unosi pravi sadržaj posle završetka dev faze kroz admin panel
- Slike kao placeholder: kombinacija Envato stock fotografija i brand materijala iz `docs/Dizajn/`
- **Sadržaj nije blokator** za isporuku dev faze; svaki FR mora da radi sa praznim ili placeholder sadržajem

### 6.4 Sadržajni volumen

- Inicijalni katalog: do **100 proizvoda** kroz sve brendove i kategorije (ograničenje iz planiranja, vidi Brief)
- Inicijalne blog objave: 0+ (klijent definiše posle launch-a)
- Inicijalna polovna mehanizacija: 0-20 stavki `[ASSUMPTION]` — varira po sezoni

## 7. Integration & Dependencies

### 7.1 Email isporuka (SMTP)

- Forme generišu email-ove ka konfigurisanim adresama (admin podešavanja)
- SMTP servis ili provajder još nije izabran `[OPEN → arhitektura]` — kandidati: Mailgun, SendGrid, Resend, Hetzner SMTP
- Email šabloni: jedan po vrsti forme; podržavaju i lokalizovan naslov po jeziku posetioca `[ASSUMPTION]`

### 7.2 Google Analytics 4

- Prati preglede stranica, događaje za slanje formi i preuzimanja (brošure, katalozi)
- Aktivira se samo posle saglasnosti *Analitički* (GDPR baner)

### 7.3 Google Search Console

- Verifikacija domena
- Integracija u admin dashboard radi pregleda indeksacije `[OPEN]` — može biti samo spoljašnji link u v1

### 7.4 Facebook Pixel

- Prati preglede stranica i ključne konverzije (slanje formi)
- Aktivira se samo posle saglasnosti *Marketing*

### 7.5 Google Maps

- Ugrađena mapa na stranici Kontakt (FR-5)
- API ključ se konfiguriše kroz env ili admin podešavanja

### 7.6 Externi PDF-ovi i Envato media

- Brošure i katalozi su PDF-ovi koje klijent ili admin otprema; sistem ne generiše PDF
- Slike mogu doći iz Envato stocka ili od klijenta — sistem ih tretira kao obične media fajlove

## 8. Operational Requirements

- **3 okruženja:** lokalno (dev), staging (testiranje pre produkcije), produkcija — sva tri reproducibilna kroz Docker
- **Bekap:** automatski **dnevni** bekap baze i media fajlova; retencija `[OPEN → arhitektura]` (predlog: 30 dana)
- **SSL:** Let's Encrypt sa automatskim obnavljanjem
- **Monitoring:** osnovni uptime monitoring `[OPEN]` — UptimeRobot ili sličan; konkretno se bira u arhitekturi
- **Praćenje grešaka:** Sentry ili sličan `[ASSUMPTION]` — potvrditi u arhitekturi
- **Logovi:** server logovi se rotiraju i čuvaju 14 dana `[ASSUMPTION]`

## 9. Non-Goals (Explicit)

- **Online prodaja / e-commerce** — nema korpe, checkout-a ni plaćanja
- **Korisnički nalozi za posetioce sajta** — postoje samo admin nalozi
- **Migracija sa starog sajta** — stari sajt ne postoji; 301 redirekcije, očuvanje URL-ova i bekap pre migracije **otpadaju**
- **Mobilna native aplikacija** — samo responzivan web
- **Live chat / WhatsApp dugme** — kontakt isključivo kroz forme i telefon
- **Praćenje zaliha / stock management** — proizvodi su katalog, nisu stok
- **Multi-tenant arhitektura** — jedan sajt, jedan brend (Ćorić Agrar)
- **Generisanje PDF-ova iz sistema** — brošure su statički otpremljeni fajlovi
- **Javni API** — sajt ne izlaže endpoint za treća lica
- **Mašinski prevod sadržaja** — sve lokalizacije unosi admin ručno
- **AI / preporuke proizvoda izvan FR-20** — slični modeli su hibrid auto i manual; bez ML rangiranja

## 10. MVP Scope

### 10.1 In Scope (sve odjednom — jedan launch)

Sve funkcionalnosti opisane u §4 Features (FR-1 do FR-48, uključujući variant selektor — FR-48 u §4.5), §5 NFRs i §7 Integration.

**Strategijska prioritizacija (unutar „sve odjednom"):** Lead-gen tok je teza ovog produkta (vidi §1 Vision). Forme **FR-5** (Kontakt), **FR-19** (Upit za model), **FR-22** (Servisni zahtev) i **FR-23** (Upit za rezervni deo) **moraju da rade od prvog dana** — ako bilo koja od njih ne radi pouzdano, MVP nije spreman za launch. Ostatak (katalog, blog, admin) je nužan kontekst, ali ne potvrđuje tezu.

### 10.2 Out of Scope (deferred)

Sve stavke iz §9 Non-Goals, plus:

- Preview blog kategorija u footer-u `[ASSUMPTION]` — nije pomenuto
- Prijava na newsletter `[NOTE FOR PM]` — može biti zanimljivo posle launch-a
- Profil/dashboard za posetioca radi praćenja sopstvenih poslatih formi `[NOTE FOR PM]` — bez toga je samo „pošalji i zaboravi"

## 11. Success Metrics

`[DEFERRED]` — Brief je ovo eksplicitno označio kao nebitno u trenutnoj fazi. Baseline lista koja se može iterirati posle launch-a:

**Funkcionalni (binary)**
- Sve 4 vrste formi šalju emailove i prikazuju potvrdu (FR-19, FR-22, FR-23, FR-5)
- Sajt indeksiran u Google-u, sitemap validan, hreflang ispravan
- Admin može samostalno da unese novi proizvod / blog post bez dev intervencije
- Sve tri jezičke verzije rade sa fallback ponašanjem

**Kvalitativni (posle launch-a)**
- Google PageSpeed / Lighthouse osnovni skor za responzivnost i performanse `[ASSUMPTION]`
- Mesečni broj poslatih formi (sve vrste zbirno) — za internu kalibraciju, bez ciljnog broja

**Kontra-metrike** (ne optimizovati)
- Broj pregleda stranica sam po sebi — nije cilj; cilj su lead-ovi, ne saobraćaj
- Vreme provedeno na sajtu — ne optimizovati; bolji lead je lead od 30 sekundi

## 12. Open Questions

Pitanja za sledeće faze — tagovana po cilju.

**Za arhitekturu**
1. **SMTP / email servis** — Mailgun, SendGrid, Resend ili Hetzner SMTP? Trade-off-i: cena, deliverability, lokalna data residency. `→ Architecture`
2. **Backend pretrage** — PostgreSQL FTS (pretpostavka iz Brief-a) ili Meilisearch/Elasticsearch? Obim sadržaja (~100 proizvoda + blog) sugeriše da je FTS dovoljan. `→ Architecture`
3. **Lightbox biblioteka** — vanilla custom, PhotoSwipe ili GLightbox? `→ Architecture`
4. **Vremenska lenta** — samo SVG/CSS, JS biblioteka (npr. Timeline.js) ili statički HTML? `→ UX + Architecture`
5. **Performance budget** — konkretni LCP / TTFB / ukupna težina strane. `→ Architecture`
6. **Monitoring i error tracking stek** — UptimeRobot + Sentry, Better Stack ili Hetzner native tooling? `→ Architecture`
7. **Retencija bekapa** — koliko dana, kompresija, sinhronizacija van lokacije? `→ Architecture`
8. **Pipeline za procesiranje slika** — django-imagekit, sorl-thumbnail, on-the-fly Pillow ili CDN sa transformacijama? `→ Architecture`

**Za UX**
9. **Vizuelni marker za fallback sadržaj** — bedž, tooltip ili nešto treće? `→ UX`
10. **Lepljivi (sticky) meni** — da li meni ostaje na vrhu pri skrolovanju ili nestaje? `→ UX`
11. **Top header na mobilnim ekranima** — kondenzovan ili sakriven? `→ UX`
12. **Filteri godišta i cene** — klizač, padajuća lista ili oba? `→ UX`
13. **Open Graph / Twitter Card slike** — automatski generisane ili ih admin otprema? `→ UX + Architecture`
14. **Dugmad za deljenje na blog stranama** — koje mreže i koja pozicija? `→ UX`
15. **„O nama" intro sekcija na Početnoj** — mockup (Početna 4.0) prikazuje intro blok između hero-a i sekcije Traktori; PRD §4.1 trenutno nema FR za njega. Dodati u UX kao novi blok ili izmeniti FR-1. `→ UX`
16. **Podrazumevano stanje Motor akordiona** na stranici proizvoda — mockup pokazuje sekciju *Motor* podrazumevano otvorenu, sa indikatorima `+/−`. Potvrditi UX odluku. `→ UX`
17. **Detalji kartice brošure (FR-18)** — mockup pokazuje prikaz veličine fajla (npr. „2.8 MB, PDF"), outlined karticu sa cover-thumbnail layoutom. Detaljisati u UX. `→ UX`
18. **Slogan i tipografija** — *„Prijatelj koji razume zemlju!"* (iz Projektnog zadatka, hero Početne); tipografija „tanka i elegantna" za meni — definisati u UX dizajn sistemu. `→ UX`
19. **Lemken kao referentni dizajn** za organizaciju kategorija mehanizacije — koje konkretne UX paterne posuditi (navigacioni filteri, kartice kategorija, vizuelne hijerarhije)? `→ UX`
20. **Footer kolona „Najnovije vesti"** — statična lista linkova ili dinamička iz bloga (poslednje 3 objave)? `→ UX`
21. **Mockup revizija za FR-19** — trenutna vizualizacija (Stranica proizvoda 1.0) prikazuje 3 polja; PRD specifikuje 5 polja (Ime / Email / Telefon / Model auto-popunjen / Poruka). UX faza ažurira mockup. `→ UX`

**Sadržaj / Klijent (vraćamo u Open Questions, ali ne blokira dev)**
22. **Politika privatnosti** — sadržaj treba da dostavi klijent; v1 koristi Lorem Ipsum
23. **Inicijalna lista blog kategorija** — klijent definiše posle dev-a
24. **Email adrese za 4 vrste formi** — konfigurišu se kroz admin posle dev faze (env-default baseline)

## 13. Assumptions Index

Sve `[ASSUMPTION]` oznake iz dokumenta — eksplicitno za potvrdu u sledećoj fazi:

- §4.5 FR-13: Paginacija polovne mehanizacije = 12 stavki po strani
- §4.5 FR-13: Sort opcije polovne — datum (default), cena asc/desc, godina silazno
- §4.7 FR-24: Paginacija bloga = 10 objava po strani
- §4.8 FR-27: Minimum query length za pretragu = 2 znaka
- §6.4: Initial polovna inventar 0-20 stavki
- §4.7 FR-25: Social share dugmad na blog stranama — potvrditi u UX
- §4.8 FR-28: Sticky meni
- §4.8 FR-29: Top header ponašanje na mobilnim ekranima
- §4.9 FR-32: URL slug-ovi koriste *sr* kao default za fallback ili specifični po jeziku — potvrditi u arhitekturi
- §4.10 FR-34: Session timeout = 4h
- §4.10 FR-34: Rate limit za login = 5 pokušaja / 15 min IP
- §5.1: HTMX filter response time < 500ms
- §5.2: WCAG 2.1 AA kao baseline pristupačnosti
- §5.3: Rate limit za forme = 10 zahteva / 15 min IP
- §5.4: Open Graph + Twitter Card meta tagovi
- §5.6: IE i legacy Edge nisu podržani
- §7.1: Email šabloni podržavaju lokalizovan subject po jeziku posetioca
- §8: Sentry kao error tracking
- §8: Log retencija = 14 dana
- §10.2: Newsletter signup deferred (note for PM)
- §11: Lighthouse osnovni skor kao baseline kriterijum

---

**Vezani fajlovi:**
- `addendum.md` (kreira se naknadno ako bude trebao za tech-how detail)
- `.decision-log.md` — audit trail svih odluka
- Parent brief: `../briefs/brief-CORIC_AGRAR-2026-05-27/brief.md` + `addendum.md`
- Izvorni materijal: `docs/Projektni zadatak - Ćorić agrar.md`, `docs/Dizajn/`

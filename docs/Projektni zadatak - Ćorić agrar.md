# 1\. Opis projekta

Projektni zadatak definiše opseg, strukturu i funkcionalne zahteve za izradu novog veb sajta kompanije Ćorić Agrar. Kompanija se bavi prodajom poljoprivredne mehanizacije, a novim statusom uvoznika traktora i mehanizacije više brendova nameće se potreba za savremenom, internet prezentacijom koja odgovara nivou ponude i ciljnom tržištu.

Veb sajt se razvija *custom* (po meri), sa sopstvenim dizajnom prilagođenim brendu Ćorić Agrar, uz primenu modernih tehnologija i standarda.

## 1.1. Cilj projekta

Primarni cilj projekta je uspostavljanje profesionalnog, modernog i funkcionalnog veb sajta koji će:

* Predstaviti kompaniju Ćorić Agrar kao pouzdanog uvoznika i distributera traktora i poljoprivredne mehanizacije na srpskom i regionalnom tržištu.  
* Prikazati kompletan spektar proizvoda po brendovima i kategorijama, sa detaljnim tehničkim specifikacijama, galerijom i pratećim dokumentima.  
* Osnažiti poverenje potencijalnih kupaca kroz prikaz referenci, korisničkih iskustava i blog sadržaja.  
* Omogućiti potencijalnim kupcima jednostavan kontakt radi inforimisanja i kupovine, prijavu za servis i preuzimanje kataloga.  
* Obezbediti jednostavno upravljanje sadržajem kroz administrativni panel.  
* Postići dobru vidljivost u pretraživačima (Google) kroz tehničku SEO optimizaciju i analitiku.

## 1.2. Tehničke karakteristike

Veb sajt se razvija korišćenjem sledećih tehnologija i standarda:

**Framework i backend:**

* Django (Python framework) — aplikacioni sloj, rutiranje, autentifikacija, ORM  
* PostgreSQL — relaciona baza podataka  
* django-modeltranslation — upravljanje višejezičnim sadržajem u bazi  
* Gunicorn \+ Nginx — aplikacioni i web server u produkciji

**Frontend:**

* HTML5, CSS3, JavaScript — custom kod bez generičkih šablona  
* Bootstrap 5 — grid sistem i osnovne UI komponente (akordioni, slideri, modali)  
* HTMX — dinamičke interakcije sa serverom bez page reload-a (filtriranje proizvoda, paginacija, slanje formi)  
* Font Awesome 6 — ikonografija  
* Responzivan dizajn prilagođen svim rezolucijama (desktop, tablet, mobilni)  
* Responzivne tabele tehničkih specifikacija proizvoda  
* Lightbox galerija sa masonry rasporedom (stranica O nama)

**Višejezičnost:**

* Srpski (primarni jezik)  
* Mađarski  
* Engleski  
* Prebacivanje između jezika dostupno sa svih strana sajta

**Razvojno okruženje i infrastruktura:**

* Tri odvojena okruženja: lokalno (development), staging (testiranje pre produkcije) i produkcija  
* uv — Python package manager i upravljanje virtualnim okruženjem  
* Docker — kontejnerizacija aplikacije za produkciju (reproducibilan deploy, lakši rollback)  
* Hetzner VPS — hosting infrastruktura  
* Git verzionisanje koda

**Integracije i SEO:**

* Google Search Console — indeksiranje i praćenje performansi pretrage  
* Google Analytics — praćenje poseta i ponašanja korisnika  
* Facebook Pixel — praćenje konverzija za potrebe oglašavanja  
* GDPR baner za upravljanje kolačićima sa opcijom izbora  
* Sitemap.xml i robots.txt — optimizacija za pretraživače  
* Bekap trenutnog sajta pre migracije  
* Automatski dnevni bekap baze podataka i izrađenog sajta  
* Zadržavanje ili preusmerenje postojećih URL adresa (301 redirect)  
* SSL sertifikat (Let's Encrypt)

**Sadržaj:**

* Unos do 100 proizvoda sa tehničkim specifikacijama  
* Opremanje sajta fotografijama (Envato stock ili materijal klijenta)  
* Popunjavanje strana tekstom, slikama, grafikama i video sadržajem

# 2\. Korisnički deo

Korisnički deo sajta obuhvata sve stranice i funkcionalnosti dostupne posetiocima. Dizajn je urađen *custom* prema vizuelnom identitetu Ćorić Agrar, u zelenoj i tamnoj paleti boja karakterističnoj za agrarni sektor. Sve stranice su responzivne i optimizovane za mobilne uređaje.

## 2.1. Strane

### 2.1.1. Početna

Početna strana je reprezentativna strana sajta i pruža pregled najznačajnijih stavki iz ponude Ćorić Agrar. Strukturirana je u sekcije koje vode korisnika kroz kompaniju, brendove i kategorije proizvoda.

**Hero sekcija:**

Na vrhu stranice nalazi se full-width hero blok sa slikom traktora u radu i natpisom “Prijatelj koji razume zemlju\!”. Hero sekcija treba da bude vizuelno upečatljiva i da odmah komunicira delatnost kompanije. Meni je transparentan. Fontovi koji se koriste u mniju su tanki i elegantni. Polje za pretragu nalzi se na kraju menija. Iznad menija nalazi se top heder sa informacijama o adresi i kontakt telefonu.

 

**O nama:**

Kratki uvodni tekst o kompaniji Ćorić Agrar sa CTA (call-to-action) dugmetom koji vodi na stranicu O nama. Iza teksta se nalazi transparentni, veliki logo kompanije kao dekorativni element. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)**treba da dostavi tekst.**

 

**Traktori:**

Sekcija prikazuje dostupne brendove traktora. Svaki brend je predstavljen logotipom i slikom reprezentativnog modela. CTA dugme vodi na stranicu brenda. Brendovi koji još nisu dostupni u ponudi označeni su labelom Uskoro. Pored dugmeta i slika i logo su linkovi ka strani brenda, kako bi se obezbedilo da korisnik lakše dolazi do ključnih prodajnih strana.

 

**Priključna mehanizacija:**

Banner sekcija koja prikazuje brendove priključne mehanizacije (npr. Jeegee) sa kratkim opisom i CTA dugmetom koji vodi na odgovarajuću stranicu brenda mehanizacije. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst.

 

**Radne mašine:**

Sekcija sa vizualnim prikazom kategorije radnih mašina (utovarivači, telehendleri) sa kratkim opisom i linkom na odgovarajuću podstranicu. Ova sekcija koristi element koji se ponavlja \- pravougaoni element (nešto širi nego što je viši), sa malim radijusima na ivicama i belim, tankim koncentričnim linijama u uglu koje simbolišu točkove i brazde. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst.

 

**Polovna mehanizacija:**

Baner sa kratkim opisom ponude polovne mehanizacije, odgovarajućom slikom i linkom na stranicu polovne mehanizacije.[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst.

 

**Priče sa polja (blog preview):**

Sekcija prikazuje 2 najnovija blog članka u formi kartica sa slikom, naslovom, kratkim opisom i linkom. Nazvana je Priče sa polja u skladu sa brendingom kompanije. Slika je pozadina sekcije, sa zatalasanom gornjom ivicom. Članci su prikazani u transparentnim boksovima sa naslovom veti, sižeom i dugmetom SAZNAJ VIŠE. Blog članke na naslovnoj strani ne prati slika, jer bi bilo previše šareno zbog slike koja se nalazi u pozadini bloka.

 

**Footer:**

Footer sadrži kontakt informacije, navigacione linkove po kategorijama (Proizvodi, O nama, Najnovije vesti), logo Ćorić Agrar i linkove ka društvenim mrežama. Logo je pozicioniran iznad navigacionih linkova, centrirano. Pozadina je zelena, sa gradijentom od tamnije ka svetlijoj. Na du futera je tanka bela linija koja odvaja copyright informacije od ostatka futera.

### 2.1.2. O nama

Stranica O nama predstavlja kompaniju Ćorić Agrar, njenu istoriju, vrednosti i tim. Dizajn treba da odišе autentičnošću i da izgradi poverenje kod potencijalnih kupaca.

**Hero sekcija:**

Na vrhu stranice nalazi se hero video ili hero slika punog ekrana. Preporučuje se video zapis koji prikazuje rad na terenu, traktore u polju ili tim kompanije, jer video bolje prenosi energiju i autentičnost brenda. Preko videa ili slike ispisan je slogan kompanije.[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst. 

**Tekst o kompaniji:**

Ispod hero bloka nalazi se duži tekst o istoriji, misiji i vrednostima kompanije Ćorić Agrar. Tekst je na beloj pozadini. Iza teksta, kao dekorativni element, postavlja se transparentni, uvećani logo kompanije — identično kao na početnoj strani.[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst. 

**Vremenska lenta:**

Ispod teksta o kompaniji postavlja se interaktivna ili animirana vremenska lenta koja prikazuje ključne momente u razvoju firme (osnivanje, proširenje delatnosti, uvoz prvih brendova, itd.). Lenta vizuelno komunicira rast i stabilnost kompanije.[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst i podatke za vremesnku lentu.

**Galerija:**

Ispod vremenske lente postavlja se galerija fotografija. Galerija koristi masonry raspored (različite visine slika, zbijene bez razmaka). Klikom na sliku otvara se lightbox prikaz sa opcijom listanja ostalih slika iz galerije.[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi izabrane fotografije za galeriju.

### 2.1.3. Traktori

Stranica Traktori služi kao pregled kompletne ponude traktora svih brendova koje Ćorić Agrar uvozi i distribuira. Dizajnirana je tako da korisnik brzo pronađe željeni brend i model.

 

**Preporučena struktura stranice:**

Stranica kombinuje dva nivoa preglednosti — brendove i modele. Na vrhu stranice prikazuju se logotipi brendova. Klikom na logotip, korisnik odlazi na stranicu tog brenda sa modelima isključivo tog brenda. Ispod logotipa brendova prikazuju se svi modeli svih brendova, vizuelno grupisani po brendu. Svaki model prikazan je kao kartica sa slikom, nazivom, kratkim opisom i CTA dugmetom ka stranici pojedinačnog proizvoda. Iznad modela nalazi se opcija za filtriranje. 

Filtriranje se može vržiti po sledećim paramterima:

- Konjska snaga  
- Godište  
- Cena

**Brendovi traktora:**

* Wuzheng  
* Agri Tracking  
* Saillong by Maki

#### 2.1.3.1. Agri Tracking

Stranica brenda Agri Tracking izrađena je prema predlogu dizajna i prati sledeće sekcije:

**Hero sekcija:**

Full-width hero sa slikom reprezentativnog Agri Tracking traktora u radu. Prikazan je logo brenda, slogan brenda i kratak uvodni tekst na ponavljajućem pravougaonom elementu zelene boje, malog radijusa ivica i sa neupadljivim tankim belim koncentričnim linijama u uglu elementa.

 

**Statistike brenda:**

Četiri istaknute numeričke statistike u ikona \+ broj formatu (npr. 1500 mašina, 100 zaposlenih, 13 tačaka servisa, 15 godina poslovanja). Statistike su vizuelno istaknute i animirane (count-up efekat pri scroll-u). Ikonice su tankih linija bele, na zelenoj pozadini.

 

**Citat/banner:**

Istaknuta rečenica ili kratki citat koji komunicira vrednosti brenda, na tamnoj pozadini sa slikom.

 

**Modeli po serijama:**

Proizvodi su grupisani po serijama:

* TB modeli  
* TD modeli  
* TC modeli


Svaka serija ima naslov i prikaz modela koji joj pripadaju. Svaki model prikazan je karticom sa slikom, nazivom, kratkim opisom i CTA dugmetom. U jednom redu prikazan je jedan model. Model ima krupnu sliku na levoj strani, odnosno levoj polovini. U desnoj polovini nalazi se naziv modela i tehnički podaci traktora, prikazani u 4 stavke akordiona (Motor, Transmisija, Hidraulika, Ostalo). Ispod akordiona nalzi se dugme OPŠIRNIJE koje vodi ka stranici izabranog modela.

 

**Zadovoljni kupci:**

Slideshow sekcija sa testimonijalom — fotografija korisnika, citat i ime/lokacija. Slider sa indikatorima koji omogućava listanje više testimonijala.

**Preuzmi katalog:**

CTA banner sa pozivom na preuzimanje PDF kataloga brenda. Dugme pokreće preuzimanje ili otvara PDF u novom tabu.

Ispod banera za preuzimanje kataloga nalazi se slika sa zatalasanom gornjom ivicom. Odmoh na sliku nadovezuje se futer.

#### 2.1.3.2. Wuzheng

Stranica brenda Wuzheng prati strukturu opisanu u poglavlju 2.1.3.1. Stranica brenda, prilagođenu vizuelnom identitetu i sadržaju brenda Wuzheng.

#### 2.1.3.3. Saillong by Maki

Stranica brenda Saillong by Maki prati istu strukturu kao Agri Tracking (opisanu u poglavlju 2.1.3.1), prilagođenu vizuelnom identitetu i sadržaju brenda Saillong.

### 2.1.4. Mehanizacija

Sekcija Mehanizacija u meniju obuhvata priključnu mehanizaciju, radne mašine, prikolice i polovnu mehanizaciju. Stranice su organizovane prema nameni mehanizacije, uz jasan vizuelni prikaz kategorija i proizvoda. Stranica Mehanizacija ne postoj (\# \- mrtav link), klik na Mehanizacija u meniju otvara potkategorije:

* Priključna mehanizacija  
* Radne mašine  
* MIX prikolice  
* Polovna mehanizacija

Referentni dizajn za organizaciju i prezentaciju kategorija je sajt kompanije Lemken (www.lemken.com), s tim da realizacija treba da bude jednostavnija i prilagođena obimu ponude Ćorić Agrar. Stranice kategorija imaju jasne ikonice ili ilustracije namene, kratke opise za svaku potkategoriju i CTA dugme koje vodi na listu proizvoda.

#### 2.1.4.1. Priključna mehanizacija Jeegee

Stranica prikazuje kompletnu ponudu priključne mehanizacije brenda Jeegee, organizovanu po nameni (kategorijama).

**Hero sekcija:**

Full-width hero sa slikom Jeegee mehanizacije u radu, logom brenda i kratkim sloganom prikazanim na ponavljajućem elementu. U slučaju Jeegee brenda ovaj element je plave boje u nijansi brenda Jeegee.

**Kategorije:**

Ispod hero slike prikazane su kategorije priključne mehanizacije u formi kartica ili banera sa ikonicom, nazivom i opisom. Svaka kategorija vodi na svoju podstranicu.

Postoje 3 kategorije priključne mehanizacije:

1. OSNOVNA OBRADA ZEMLJIŠTA   
2. PRIPREMA ZEMLJIŠTA   
3. MAŠINE ZA SETVU

##### 2.1.4.1.1. OSNOVNA OBRADA ZEMLJIŠTA

Stranica prikazuje plugove i slične mašine iz ponude Jeegee. Svaki proizvod prikazan je karticom sa slikom, nazivom, ključnim specifikacijama i CTA dugmetom ka stranici proizvoda.

Mehanizacija u kategoriji OSNOVNA OBRADA ZEMLJIŠTA je podeljena na:

- Plugovi  
- Podrivači  
- Gruberi

PLUGOVI

Plugovi dele na:

* plugovi ravnjaci  
* plugovi obrtači


Plugovi ravnjaci:

- KJ-tip

Plugove obrtače delimo po debljini grede: 90x90, 100x100, 120x120, 140x140 160x160

Plugovi obrtači: 

- 90x90: 1LF-KP331  
- 100x100: 1LF-435C  
- 120x120: 1LF-L450F i 1LF-L350  
- 140x140: 1LF-LKX450  
- 160x160: 1LF-LKX550A

Kod plugova obrtača dati na pojedinačnoj strani pluga prikaz izbora daske (puna i rešetkasta \- katalog strana 06\) Ostaviti prostor da može da se doda još jedan tip daske. Daske prikazati ilustrativno sa šifrom i nazivom.

 

PODRIVAČI

- JMA300

GRUBERI  

Nošeni:  

- KX300  
- KX350 

2.1.4.1.2. PRIPREMA ZEMLJIŠTA

Stranica prikazuje mašine za pripremu zemlje. Svaki proizvod prikazan je karticom sa slikom, nazivom, ključnim specifikacijama i CTA dugmetom ka stranici proizvoda.

Mašine za pripremu zemljišta delimo na:

- Tanjirače  
- Setvospremače

TANJIRAČE

Tanjirače mogu biti: 

NOŠENE

- Nošena Vega 9:   
  - Kratka tanjirača 250  
  - Kratka tanjirača 300

U okviru strane konkretne tanjirače korisnici imaju prikaz različitih rotora za tanjiraču: dupli cevasti ili kembridž valjak (uz prikaz slike oba rotora sa bočne strane).

VUČENE

* 1BYQ tip  
* Vega 9  
* Vega 12  
    
  1BYQ tip:   
- Tanjirača 330  
- Tanjirača 380  
- Tanjirača 430  
- Tanjirača 530  
- Tanjirača 630 (staviti label koliko ima modela)  
  Vega 9:   
- Tanjirača 400  
- Tanjirača 500  
- Tanjirača 600  
  Vega 12:   
- Tanjirača 400  
- Tanjirača 500  
- Tanjirača 600


U okviru strane konkretne tanjirače korisnici imaju prikaz različitih rotora za tanjiraču: dupli cevasti ili kembridž valjak (uz prikaz slike oba rotora sa bočne strane).

SETVOSPREMAČI

* Hermes tip vučni  
* SKS kombinator tip

  Hermes: 

- H255-15.7m  
- H255-12.4m  
  SKS tip:   
- SKS 300  
- SKS 400  
- SKS 500

##### 2.1.4.1.3. MAŠINE ZA SEJANJE

Stranica prikazuje sejalice i mašine za setvu iz ponude Jeegee. Svaki proizvod prikazan je karticom sa slikom, nazivom, ključnim specifikacijama i CTA dugmetom ka stranici proizvoda.

U ponudi se nalaze precizne sejalice za žito sa rotodrljačom: 

* 2BG-250  
* 2BG-300 

####  2.1.4.2. Radne mašine HZM

Stranica brenda HZM obuhvata radne mašine podeljene u tri potkategorije:

* Mini utovarivači   
* Utovarivači bez teleskopa  
* Teleskopski utovarivači  
* Telehendleri

Stranica prati analognu strukturu kao Jeegee stranica — hero sekcija brenda, prikaz kategorija i lista proizvoda po podkategorijama

Mini utovarivač: 

- HZM 1100

Utovarivači bez teleskopa: 

- HZM925

Teleskopski utovarivači:

- HZM 810T  
- HZM 812T  
- HZM 816T  
- HZM 825T

Telehendleri: 

- HZM 7335

#### 2.1.4.3. MIX prikolice

Stranica brenda Tulip ima 2 proizvoda:

* MIX prikolica 6 kubika  
* MIX prikolica 8 kubika

Stranica prati sledeću strukturu —hero sekcija brenda, lista proizvoda, zadovoljni kupci i preuzmi katalog. 

|  | 6 kubika (m³) |  8 kubika (m³) |
| :---- | :---- | :---- |
| Kapacitet (m³) | 6 (m³) | 8 (m³) |
| Dužina (mm) | 4035 | 4455 |
| Širina (mm) | 2045 | 2365 |
| Visina (mm) | 2595 | 2640 |
| Tezina prazne prikolice (kg) | 2690 | 3610 |
| Broj mešača  | 1 | 1 |
| Broj velikih/malih noževa | 5/4 | 6/6 |
| Obrtaji spirale | 28 | 28 |
| Debljina dna/ bočnog zida | 20/8 | 20/8 |
| Potrebna snaga (ks) | \>55 | 65 |

#### 2.1.4.4. Polovna mehanizacija

Stranica prikazuje trenutno dostupnu polovnu mehanizaciju u ponudi Ćorić Agrar. Ova sekcija je manje prioritetna u inicijalnoj fazi, ali se preporučuje implementacija sledećih elemenata:

**Lista proizvoda:**

Kartice sa slikom, nazivom, godinom, stanjem i cenom svake mašine u ponudi.

 

**Filteri:**

Sistem filtriranja koji korisniku omogućava sužavanje pretrage prema:

•   	Kategoriji:

- TRAKTORI  
- PRIKLJUČNA MEHANIZACIJA  
- RADNA MAŠINA  
- OSTALO  
  •   	Brendu  
  •   	Cenovnom rangu (klizač min–max)  
  •   	Godini proizvodnje  
  •   	Stanju mašine 


Filteri se preporučuju i za inicijalnu fazu, jer znatno poboljšavaju korisničko iskustvo i smanjuju napuštanje stranice kod korisnika koji traže specifičnu mašinu.

### 2.1.5. Stranica pojedinačnog proizvoda

Stranica pojedinačnog proizvoda detaljno predstavlja jedan model traktora ili mehanizacije. Struktura je zajednička za sve proizvode, uz prilagođavanja po tipu (traktor, mehanizacija, radna mašina).

 

**Hero sekcija:**

Full-width hero sa slikom ili fotografijom proizvoda, logom brenda, nazivom modela i do 3 ključne karakteristike u bullet formatu prikazane na ponavljajućem elementu zelene boje.

 

**Opis proizvoda:**

Duži tekstualni opis modela.

 

**Galerija:**

Horizontalni niz fotografija proizvoda u vidu karusela. Klikom na sličicu otvara se lightbox prikaz sa prelaskom na prethodnu/sledeću sliku.

 

**Tehnički podaci:**

Tabela tehničkih specifikacija organizovana u accordion sekcije (Motor, Transmisija, Hidraulika, Ostalo). Svaka sekcija se može proširiti/skupiti. Tabele su responzivne i čitljive na mobilnim uređajima.

 

**Brošura:**

Sekcija za preuzimanje PDF brošure modela sa prikazom naslovne strane i dugmetom PREUZMI.

 

**Iz prve ruke:**

Slideshow testimonijal — fotografija korisnika mašine, citat i ime/lokacija korisnika. Slider sa indikatorima za listanje.

 

**Slični modeli:**

Horizontalni prikaz 2–4 slična modela iz iste serije ili kategorije sa slikom, nazivom, kratkim opisom i CTA dugmetom.

 

**Imate pitanja?:**

Kontakt forma direktno na stranici proizvoda, sa automatski popunjenim poljem za model koji se gleda. Predviđena polja: 

* Ime i prezime  
* Email  
* Telefon  
* Model (prepopunjen podatak)  
* Poruka

### 2.1.6. Servis

Sekcija Servis pruža informacije o servisnoj podršci kompanije Ćorić Agrar i omogućava korisnicima prijavu servisnog zahteva direktno putem sajta.

#### 2.1.6.1. Servisna podrška

Stranica pruža informacije o servisnoj podršci — opis servisa, brendovi koji se servisiraju, lokacija servisa, radno vreme i kontakt podaci servisa.  [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi tekst i informacije

**Forma za servisni zahtev:**

Na stranici se nalazi jednostavna kontakt forma za prijavu servisnog zahteva. Forma sadrži sledeća polja:

* Ime i prezime  
* Kontakt telefon  
* Email  
* Vrsta mehanizacije (padajuća lista: traktor, priključna mehanizacija, radna mašina...)  
* Brend i model mehanizacije (tekstualno polje)  
* Opis kvara ili potrebne usluge (textarea)  
* Opciono: unos slike (foto kvara, ako je primenjivo)

Po slanju forme, korisniku se prikazuje potvrda prijema zahteva, a servis prima obaveštenje na email. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi mejl adresu za prijem servisnih zahteva

#### 2.1.6.2. Rezervni delovi

Stranica pruža informacije o dostupnosti rezervnih delova za brendove koje zastupa Ćorić Agrar. Sadrži kontakt informacije za upit o rezervnim delovima i po potrebi formu za slanje upita (analognu formi za servisni zahtev, sa prilagođenim poljima).


Forma sadrži sledća polja: 

* Model traktora  
* Rezervni deo za poručivanje  
* Dodatni opis rezervnog dela (opciono)  
* Slika rezervnog dela (opciono)  
* Ime i prezime  
* Kontakt telefon  
* Email adresa  
* Način plaćanja (opcije: pouzećem, predračun)  
* Način preuzimanja (opcije: dostava na kućnu adresu, lično preuzimanje)  
* Napomena (opciono)

### 2.1.7. Priče sa polja 

Priče sa polja je blog sekcija sajta namenjena objavljivanju edukativnih i informativnih tekstova, iskustava kupaca, agrarnih saveta i vesti iz sveta poljoprivredne mehanizacije.

 

**Lista objava (blog index):**

Stranica prikazuje sve objave u formi kartica organizovanih od najnovije ka starijoj. Svaka kartica sadrži:

•   	Naslovnu sliku članka

•   	Datum objave

•   	Naslov

•   	Kratki izvod teksta (perex)

•   	CTA dugme SAZNAJ VIŠE

Preporučuje se paginacija za navigaciju kroz starije objave. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi nekoliko početnih blog postova.

**Pojedinačna objava (blog post):**

Stranica pojedinačnog blog posta sadrži naslovnu sliku, datum, naslov, telo teksta sa mogućnošću umetanja slika i videa unutar teksta i sekciju sličnih objava na dnu stranice.

**Kategorije:**

Blog objave mogu biti kategorisane (npr. Saveti, Vesti, Iskustva kupaca, Agrotehnika) radi lakšeg filtriranja i navigacije. [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da definiše kategorije.

### 2.1.8. Kontakt 

Stranica Kontakt pruža sve potrebne informacije za stupanje u kontakt sa kompanijom Ćorić Agrar i sadrži obrazac za direktno slanje upita.

 

**Kontakt informacije:**

* Adresa kompanije  
* Broj telefona (prodaja, servis)  
* Email adresa  
* Radno vreme  
* Linkovi ka društvenim mrežama

 [marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi informacije

**Kontakt forma:**

Obrazac sa poljima: 

* Ime i prezime  
* Email  
* Telefon  
* Poruka

Po slanju, korisniku se prikazuje potvrda, a kompanija prima obaveštenje na email[marijana@kipetrol.rs](mailto:marijana@kipetrol.rs)treba da dostavi mejl adresu za prijem pošte

**Mapa:**

Ugrađena Google Maps mapa sa lokacijom kompanije.

# 3\. Administrativni deo 

Administrativni panel omogućava upravljanje sadržajem veb sajta. Panel je dostupan isključivo ovlašćenim korisnicima putem bezbedne prijave.

## 3.1. Dashboard 

Po prijavi, administrator vidi centralni pregled (dashboard) koji prikazuje ključne informacije o stanju sajta na jednom mestu:

 

**Statistike sajta:**

* Broj poseta u poslednjih 7/30 dana (integrisano sa Google Analytics)  
* Broj poruka/upita primljenih putem kontakt formi u tekućem mesecu  
* Broj servisnih zahteva u tekućem mesecu  
* Ukupan broj objavljenih proizvoda  
* Ukupan broj blog objava

 

**Brze akcije:**

* Dodaj novi proizvod  
* Dodaj novu blog objavu

## 3.2. Upravljanje proizvodima 

* Modul za upravljanje katalogom proizvoda:  
* Dodavanje, izmena i brisanje proizvoda  
* Unos naziva, opisa, kategorije, brenda i serije  
* Upload i upravljanje galerijom fotografija  
* Unos tehničkih specifikacija po sekcijama (Motor, Transmisija, Hidraulika, Ostalo)  
* Upload PDF brošure  
* Unos testimonijala za proizvod  
* Upravljanje statusom (objavljeno / skica / arhivirano)  
* Označavanje sličnih modela  
* Unos sadržaja na srpskom, mađarskom i engleskom jeziku

## 3.3. Upravljanje brendom i kategorijama 

* Dodavanje i izmena brendova (naziv, logo, opis, hero slika, statistike, katalog)  
* Upravljanje kategorijama i potkategorijama mehanizacije  
* Definisanje redosleda prikaza brendova i kategorija

## 3.4. Upravljanje blog objavama

* Dodavanje, izmena i brisanje blog objava  
* WYSIWYG editor za unos teksta sa podrškom za slike i video unutar teksta  
* Definisanje kategorija i tagova  
* Upravljanje statusom (objavljeno / skica / arhivirano)  
* Unos sadržaja na sva tri jezika

## 3.5. Upravljanje korisnicima i pristupom 

* Kreiranje i upravljanje administratorskim nalozima  
* Definisanje uloga i pristupa (superadmin, editor)  
* Promena lozinke i podešavanja naloga

## 3.6. Upravljanje sadržajem stranica

* Izmena tekstova na statičkim stranicama (O nama, Servis, itd.)  
* Upload i izmena galerije na stranici O nama  
* Izmena kontakt podataka i radnog vremena

## 3.7. SEO i analitika

* Unos meta naslova i meta opisa za svaku stranicu i proizvod  
* Upravljanje sitemap.xml fajlom  
* Upravljanje 301 preusmerenjima (redirect manager)  
* Pregled status indeksiranja kroz Google Search Console integraciju

## 3.8. Podešavanja

* Upravljanje opštim podešavanjima sajta (naziv, kontakt, logotip, favicon)  
* Upravljanje navigacionim menijem  
* Podešavanje GDPR banera i politike kolačića
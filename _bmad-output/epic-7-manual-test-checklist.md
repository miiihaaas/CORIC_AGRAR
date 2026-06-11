# Epic 7 (GDPR & Privacy) — Lista za ručno testiranje u pretraživaču

> Prolazi se stavku po stavku. URL-ovi su za `sr` lokalu; gde je bitno proveriti i `hu`/`en`, naznačeno je.
> Admin: `/sr/admin/` (superuser nalog).

---

## 7-1 — CookiePolicy (model + admin + javna strana)

**Javna strana**
- [ ] `/sr/politika-kolacica/` → 200, prikazuje naslov (h1) + telo politike
- [ ] `/hu/politika-kolacica/` i `/en/politika-kolacica/` → 200; pošto je seed samo `sr`, prikazuje **srpski fallback sadržaj**
- [ ] Prikazan red „Poslednja izmena" (auto timestamp)
- [ ] „Važi od" (effective_date) **NIJE** prikazan na seed politici (datum nije postavljen)

**Admin**
- [ ] `/sr/admin/` → postoji sekcija „GDPR i privatnost" → „Politika kolačića"
- [ ] Klik na nju vodi **pravo na izmenu** jedinog reda (nema changelist liste)
- [ ] Nema dugmeta „Add another" / „Dodaj"; nema „Delete" / „Obriši"
- [ ] Postoje jezički tabovi/polja za `title` i `body` (sr/hu/en)
- [ ] Postavi „Važi od" datum + sačuvaj → na javnoj strani se sad prikazuje „Važi od"

**XSS granica (brzi check)**
- [ ] U admin `body` ukucaj `<b>test</b>` i sačuvaj → na strani se posle 7-5 prikazuje **podebljano** (sanitizovano), ne kao tekst (vidi 7-5)

---

## 7-2 — GDPR baner + consent

> Pre testa: obriši `consent_state` kolačić (DevTools → Application → Cookies → obriši) ili otvori **incognito**.

**Prikaz banera**
- [ ] Otvori bilo koju stranu (npr. `/sr/`) bez kolačića → baner se prikazuje dole
- [ ] Baner ima 3 kategorije: **Neophodan** (čekiran + zaključan), **Analitički**, **Marketing**
- [ ] Analitički i Marketing su **odčekirani** po defaultu
- [ ] Postoje 3 dugmeta: **Prihvati sve**, **Odbij sve**, **Sačuvaj izbor** (sva tri izgledaju kao dugmad jednake veličine — „Odbij sve" NIJE bledi link)
- [ ] „Više info" link vodi na `/sr/politika-kolacica/`

**Funkcionalnost (klik)**
- [ ] „Prihvati sve" → baner nestaje, stranica ostaje gde je bila (redirect-back)
- [ ] Reload strane → baner se **više ne prikazuje**
- [ ] DevTools → Cookies → `consent_state` = `{"necessary":true,"analytical":true,"marketing":true}`, traje ~365 dana
- [ ] Obriši kolačić → „Odbij sve" → `consent_state` = samo `necessary:true`
- [ ] Obriši kolačić → čekiraj samo „Analitički" → „Sačuvaj izbor" → `analytical:true, marketing:false`

**A11y / tastatura**
- [ ] Tabom se može doći do checkbox-ova i dugmadi
- [ ] Kad je fokus u baneru, **Esc** okida „Odbij sve"
- [ ] Esc u nekom drugom polju (npr. search) **NE** okida „Odbij sve"
- [ ] Stranica je upotrebljiva dok je baner prikazan (može da se skroluje/klikće — nije blokirajući)

**Bez JS (opciono)**
- [ ] Isključi JavaScript → klik na „Prihvati sve" i dalje radi (plain form POST)

---

## 7-3 — GA4 + FB Pixel (conditional render)

> U dev-u su `GA_MEASUREMENT_ID` / `FB_PIXEL_ID` prazni → tragači se **ne učitavaju** ni uz pristanak. Za pravi test treba postaviti ID-jeve u `.env` (ili `override` u testu).

**Bez pristanka / prazan ID (default)**
- [ ] Otvori stranu, View Source (Ctrl+U) → **nema** `googletagmanager.com/gtag/js`, `gtag(`, `connect.facebook.net`, `fbq(`
- [ ] Nema `<link rel="preconnect">` ka tracker domenima u `<head>`

**Sa pristankom + postavljenim ID-jevima (ako testiraš realno)**
- [ ] Postavi `GA_MEASUREMENT_ID` i `FB_PIXEL_ID` u `.env`, restartuj server
- [ ] Bez consent kolačića → View Source → i dalje **nema** trackera
- [ ] „Prihvati sve" u baneru → reload → View Source sad **sadrži** `gtag(` i `fbq(`
- [ ] DevTools → Network → vidi se zahtev ka `googletagmanager.com` / `facebook.com/tr`
- [ ] Samo Analitički pristanak → ima GA, **nema** FB; samo Marketing → obrnuto

**Forged kolačić (fail-safe)**
- [ ] Ručno postavi `consent_state=garbage` → reload → **nema** nijednog trackera (default-deny)

---

## 7-4 — Politika privatnosti + footer linkovi

**Nova strana**
- [ ] `/sr/politika-privatnosti/` → 200, naslov + telo
- [ ] `/hu/politika-privatnosti/` i `/en/politika-privatnosti/` → 200 (sr fallback)
- [ ] Nepostojeći slug, npr. `/sr/nepostojeca-strana/` → 404

**Footer (na svakoj strani)**
- [ ] U footeru postoji „Politika privatnosti" → vodi na `/sr/politika-privatnosti/`
- [ ] U footeru postoji „Politika kolačića" → vodi na `/sr/politika-kolacica/` (7-1 ruta, ne duplikat)
- [ ] Postojeće 4 kolone footera + „Najnovije vesti" + copyright i dalje rade (nije ništa polomljeno)
- [ ] Copyright čita „Sva prava zadržana." (pune dijakritike)

**Cross-include regresija (KRITIČNO — catch-all ruta)**
- [ ] `/sr/politika-kolacica/` → i dalje **200** (nije ga pojeo pages catch-all)
- [ ] `/sr/blog/` → i dalje **200**
- [ ] `/sr/pretraga/` (search) → i dalje radi
- [ ] `/sr/` (home) → i dalje radi
- [ ] Footer link na slug `politika-kolacica` ne otvara generičku Page stranu (gdpr je vlasnik)

**Admin**
- [ ] `/sr/admin/` → „Statičke strane" (Page) → ima changelist sa „politika-privatnosti"
- [ ] Može se dodati nova Page; slug se auto-popunjava iz naslova
- [ ] Postoje jezički tabovi za title/body

---

## 7-5 — Sanitizovan rich-text (nh3) na pravnim stranama

> Render `body` na politici kolačića i privatnosti sada ide kroz `|legal_html` (nh3 sanitizacija) umesto `|linebreaks`.

**Dozvoljena struktura prolazi (u admin `body` zalepi pa pogledaj stranu)**
- [ ] `<h2>Naslov</h2>` → prikazan kao naslov
- [ ] `<ul><li>stavka</li></ul>` → prikazana lista
- [ ] `<table><thead><tr><th>Naziv</th></tr></thead><tbody><tr><td>_ga</td></tr></tbody></table>` → prava tabela
- [ ] `<a href="https://policies.google.com/privacy">link</a>` → klikabilan link
- [ ] Taj `<a>` ima `rel="noopener noreferrer"` (View Source)
- [ ] `<strong>` / `<em>` → podebljano / kurziv

**XSS se uklanja (STRIP, ne escape)**
- [ ] `<script>alert(1)</script>` u body → na strani **nema** `<script` tag-a, **nema** popup-a; alert se ne izvršava
- [ ] `<img src=x onerror="alert(1)">` → `<img` i `onerror=` uklonjeni
- [ ] `<a href="javascript:alert(1)">x</a>` → ostaje tekst „x", `href` uklonjen (nema `javascript:`)
- [ ] `<iframe>`, `<div style=...>` → uklonjeni

**Obe strane**
- [ ] Provera važi i za `/sr/politika-kolacica/` i za `/sr/politika-privatnosti/`
- [ ] `/hu/` i `/en/` verzije renderuju isti sanitizovan sadržaj (sr fallback)

---

## Brzi smoke (pre svega)
- [ ] Server diže se bez greške (`just run` / `docker compose up`)
- [ ] `/sr/` se otvara
- [ ] Login u `/sr/admin/` radi

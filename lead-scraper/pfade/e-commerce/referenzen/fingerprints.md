# Shopsystem-Erkennung (Fingerprints)

**Zweck:** woran man jedes Shopsystem mit wenigen, höflichen Abrufen erkennt und welche öffentlichen Endpunkte zusätzliche Daten liefern. Grundlage für einen künftigen Filter „nur Shopware/Shopify“.
**Für wen:** Entwickler und KI-Modelle, die den Erkennungs-Code bauen oder Fehlklassifizierungen untersuchen.
**Verwandt:** `../../../wissen/06_pfad-e-commerce.md` · `architektur.md` · `discovery-quellen.md`
**Stand:** 2026-10-08 · **Prüfen bis:** 2027-01-08 (Shopsysteme ändern Merkmale mit neuen Versionen)

Kennzeichnung:

- **beob.:** am 08.10.2026 selbst per passivem GET gesehen. Geprüft wurden paulaner-shop.de (Shopware 6), koro.com (Shopware 6 headless), snocks.com und hanfgefluester.de (Shopify), bergfreunde.de (OXID) und kochform.de (Eigenbau).
- **WA:** Regel aus `enthec/webappanalyzer`.
- **⚠:** unsicher oder ungeprüft.

## Inhalt

1. Erkennungsreihenfolge (≤ 3 Abrufe) · 1a. Regelstand fp v2 (gemessen)
2. Shopware 6 · 3. Shopware 5 · 4. Shopify · 4a. DNS-Regeln für gehostete Systeme · 5. weitere Systeme
6. Qualifizierungssignale · 7. Impressum finden
8. Open-Source-Regelsammlungen · 9. Wenn eine Regel nicht mehr stimmt


> **Einordnung:** Recherche vom 08.10.2026 für spätere Ausbaustufen. **Nicht Teil des aktuellen Pfads.** Der Pfad ist ein Nachbau des Clay-Workbooks ECOM 2.0 (`../ABLAUF.md`). Er erkennt das Shopsystem nicht und braucht eine fertige Shop-Liste.

---

## 1. Erkennungsreihenfolge (Ziel: ≤ 3 Abrufe)

1. **`GET /robots.txt`**. Das ist Pflicht für Höflichkeit und liefert gleichzeitig Signale:
   - Kommentar `# Shopify storefront.` ⇒ Shopify
   - `wp-admin` ⇒ WordPress/WooCommerce
   - Shopware-Fehlerseite „Sales Channel Not Found“ ⇒ Shopware 6
   - Sitemap-URL merken
2. **`GET /`**: Weiterleitungen folgen, Header, Cookies und die ersten ~1,5 MB HTML auswerten. Die schnellsten Treffer zuerst:
   1. **Header:** `powered-by: Shopify`, `X-Plenty-Shop`, `X-Wix-*`, `X-Jimdo-*`, `X-epages-*`, `server: Squarespace`, `x-powered-by: Next.js/Nuxt`
   2. **Asset-Pfade:**
      - `/theme/<32hex>/` ⇒ SW6
      - `/web/cache/\d{10}_` oder `themes/Frontend` ⇒ SW5
      - `cdn.shopify.com` ⇒ Shopify
      - `/wp-content/plugins/woocommerce` ⇒ WooCommerce
      - `/static/version\d+/frontend/` ⇒ Magento 2
      - `templates/NOVA` oder `JTLSHOP` ⇒ JTL-Shop
      - `templates/gambio` ⇒ Gambio
      - `/out/…/src/` oder `sid_key=oxid` ⇒ OXID
      - `/modules/ps_` ⇒ PrestaShop
      - `demandware.static` ⇒ Salesforce Commerce Cloud
      - `bigcommerce` ⇒ BigCommerce
   3. **JS-Variablen** und `<meta name="generator">`
   4. **Danach:** Werkzeug-Signale (Zahlung, Siegel, Tracking), Version und `hreflang` auslesen
3. **Ein systemspezifischer Abruf:**

| Ergebnis aus Schritt 2 | Abruf |
|---|---|
| Shopify | `/meta.json` |
| Shopware 6 klassisch | keiner nötig; optional `/sitemap.xml` für die Produktschätzung |
| Shopware 6 headless mit `SWSC…`-Schlüssel im HTML | `/store-api/context` mit diesem Schlüssel |
| unklar, aber Nuxt/Next und Pfade `/media/xx/` | `/store-api/context` ohne Schlüssel – Antwort 401 bestätigt Shopware 6 |
| WooCommerce | `/wp-json/wc/store/v1/products?per_page=1` |
| Magento | `/magento_version` |
| alles andere | Sitemap-Index |

**Bei 429, 430 oder 403:** abbrechen, nicht wiederholen, Status `manuell_pruefen`. Bot-Schutz wird nie umgangen (`architektur.md`).

**Erwartete Abdeckung** ⚠ (Schätzung): Schritt 2 erkennt im DACH-Mittelstand ~90 %, mit Schritt 3 ≥ 95 %. Rest:

- Eigenbauten (z. B. kochform.de, kein bekanntes Merkmal)
- Headless-Shops großer Händler
- Shops hinter Bot-Schutz (Cloudflare-Cookie `__cf_bm`, beob. bergfreunde.de)

---

## 1a. Regelstand fp v2 (Messung 08.10.2026)

Der Prototyp `../prototypen/classify.py` setzt die Regeln dieses Dokuments um und wurde an 25 echten Domains geprüft. Wo v2 von den Abschnitten 2–5 abweicht, **gilt v2**:

| Regel | Änderung gegenüber v1 | Beleg |
|---|---|---|
| Header `sw-language-id` / `sw-currency-id` | hochgestuft auf **sehr hoch** für SW6-Storefronts | 4/4 klassische SW6, auch hinter Cloudflare |
| `/bundles/storefront/` | NEU: SW6 auch mit eigenem Asset-Build (ohne `/theme/<hash>/`) | nomos-glashuette.com, bestätigt per 401 der Store-API |
| `window.features` | Ab 6.7 steht es als `JSON.parse('{\u0022V6_7_0_0…')`. **Zuerst `\uXXXX` decodieren**, dann höchstes `V6_X_0_0:true` = Unterversion | v1 fand 0/3 Versionen, v2 3/3 |
| `/store-api/context` → 401 mit `sw-access-key` | nur auf `sw-access-key` matchen. Gilt nur auf dem **API-Host**, Host aus `shopwareEndpoint` lesen | koro.com: Shop-Domain liefert 404, API liegt auf einem eigenen Host |
| `SWSC…`, `shopwareEndpoint` | stehen bei Headless-Shops erst ab Zeichen 1,3–2 Mio., also **nur im Vollabruf** | koro.com, yt-industries.com |
| Stufe 2 auslösen | an `/_nuxt/` bzw. `/_next/` koppeln (stehen in den ersten ~10 KB), **nicht** am Ergebnis „headless“ | Fehler im Prototyp, Gegenprüfung |
| SW5-Cookie `session-<Ziffern>` | nur zusammen mit einem HTML-Merkmal werten | an Nicht-Shopware-Seiten ungeprüft |
| Gambio | NEU `/GXModules/` und Cookie `GXsid_<hash>` (bestätigt) | metallparadies.de (GX4 ohne `templates/gambio`) |
| Shopify-Subdomain | CNAME `checkout.`/`shop.` → `shops.myshopify.com` = „nutzt Shopify“. Hauptsystem nur, wenn die Startseite kein anderes System zeigt. Vorher Wildcard-DNS mit einer Zufalls-Subdomain ausschließen | elgato.com richtig; carhartt-wip.com zeigt commercetools |
| WooCommerce | Das bloße Wort „WooCommerce“ zählt **nicht**; nur der Plugin-Pfad. Aktiv erst per Store-API (`X-WP-Total`) | 1und1.de nennt WooCommerce als Produkt |
| commercetools | NEU `\"type\":\"commercetools` im Next-Payload | carhartt-wip.com |
| robots.txt als Signal | SW6-Standard: `Allow: /widgets/cms/`, `Allow: /*theme/`. SW5-Standard: `Allow: /widgets/emotion` plus `Disallow: /note/ /ticket/ /listing/`. `sitemap_index.xml` allein ist **nicht** SW5-exklusiv. Shopify: Kommentar `# we use Shopify as our ecommerce platform` bzw. `# Shopify storefront.` | Common-Crawl-Archiv, gemessen |

**Grenzen der Messung:** 20/20 richtig, darunter 7/7 Shopware. Das gilt **in-sample**, also auf genau den Domains, an denen v2 entwickelt wurde. Unabhängig geprüft ist erst 1 Fall (paulaner-shop.de, gecachter SW6, aus 8 KB als 6.6 erkannt), Shopware 5 nur mit n = 1. Vor einer Quote gegenüber Nutzern v2 einfrieren und an ≥ 50 neuen, zufällig gezogenen Shops prüfen (`shop-katalog.md`, Phase B).

**Bereits 64 KB auf der Leitung** reichen für 17/20 Domains. Abweichend waren nur headless Seiten, die Stufe 2 brauchen. **Nur Header, Cookies und DNS:** 13/17 Shops richtig.

## 2. Shopware 6

| Merkmal | Wo | Beispiel | Zuverlässigkeit |
|---|---|---|---|
| `/theme/<32 hex>/js/storefront/storefront.js`, `/theme/<hash>/css/all.css` | HTML | beob. paulaner-shop.de | sehr hoch |
| `/bundles/<plugin>/…` | HTML | `/bundles/molliepayments/mollie-payments.js` (beob.) | hoch |
| `window.router` (Schlüssel `frontend.*`), `window.salesChannelId` (32 hex), `window.features`, `window.breakpoints`, `window.themeAssetsPublicPath` | Inline-Script | beob. | sehr hoch |
| `window.features` mit `V6_5_0_0` / `V6_6_0_0` / `V6_7_0_0` | Inline-Script | `V6_6_0_0:true, V6_7_0_0:false` ⇒ 6.6.x (beob.; WA nutzt dieselbe Logik) | hoch für die Unterversion |
| `GET /store-api/context` ohne Header ⇒ `401 {"detail":"Header \"sw-access-key\" is required."}` | 1 Abruf | beob. | sehr hoch, auch headless |
| Header `sw-context-token`, `sw-language-id`, `sw-version-id`, `sw-invalidation-states` | Header | WA | mittel: fehlt bei gecachter Startseite |
| Fehlerseite „Sales Channel Not Found“ | nicht konfigurierte Pfade | beob. | hoch, wenn sie auftritt |
| `window.shopwareAnalytics` | Inline-Script | beob. + WA | mittel–hoch |
| Cookies `session-…`, `sw-states`, `sw-cache-hash` | Set-Cookie | ⚠ auf der Startseite oft nicht gesetzt | niedrig |

**Achtung 6.7:** `window.features` wird ab 6.7 `\u`-codiert ausgeliefert, siehe 1a.

**Plugins ohne Zusatzabruf:** Jedes Plugin mit Storefront-JS hat einen eigenen Pfad, den dieser Regex findet:

```
/theme/[0-9a-f]{32}/js/([a-z0-9-]+)/
```

Beobachtet bei paulaner-shop.de: `swag-pay-pal`, `newsletter-sendinblue`, `swag-analytics`, `awmedia-age-verification-platform`.

**Aktualität:** Der Query-String der Assets ist ein Unix-Zeitstempel des letzten Theme-Builds. `?1791185518` = 05.10.2026 (beob.). Ein junges Datum heißt, dass der Shop gepflegt wird.

**Store API:**

- Der `sw-access-key` wählt nur den Verkaufskanal, er ist kein Passwort.
  - Klassische Storefront: Der Schlüssel steht nicht im HTML (beob.).
  - Headless (Shopware Frontends/Nuxt): Der Schlüssel steht öffentlich im Seiten-Payload. Muster `SWSC[A-Z0-9]{22}`, beob. koro.com mit 8 Schlüsseln für mehrere Länder.
- Mit Schlüssel:
  - `GET /store-api/context`, `/language`, `/currency`, `/country` liefern Sprachen, Währungen und Lieferländer.
  - `POST /store-api/product` mit `{"limit":1,"total-count-mode":1}` liefert `total` = Produktanzahl.
  - ⚠ Ob ein POST noch als „passiver“ Abruf gilt, ist eine Entscheidung des Betreibers. Ob es als GET mit Query-Parametern geht, ist versionsabhängig und ungeprüft.

**Cloud (SaaS) vs. selbst gehostet:**

- SaaS-Shops haben immer eine `*.shopware.store`-Domain, eigene Domains sind möglich (ab 6.7.12).
- ⚠ Erkennbar per DNS-CNAME. Ein sicheres HTML-Merkmal ist nicht bekannt.
- SaaS läuft immer auf der neuesten 6.7. Ein Shop auf 6.5 oder 6.6 ist also selbst gehostet.

**Versionen und Supportende** (endoflife.date/shopware, Stand 08.10.2026):

| Version | Sicherheitsupdates bis | Bedeutung für die Ansprache |
|---|---|---|
| 6.7 | aktuell (6.7.15.1 vom 02.10.2026) | – |
| 6.6 | 28.02.2028 | – |
| **6.5** | **28.02.2027** | Upgrade-Anlass |
| 6.4 und älter | abgelaufen | starker Anlass |

**Sitemap:** `/sitemap.xml` ist ein Index auf `.gz`-Dateien je Verkaufskanal und Sprache. Die Zahl der `<url>`-Einträge liefert eine grobe Produktschätzung; Kategorien und CMS-Seiten sind darin mitgezählt. ⚠ Pfadstruktur ungeprüft.

## 3. Shopware 5 (Supportende 31.07.2024)

| Merkmal | Wo | Beispiel | Zuverlässigkeit |
|---|---|---|---|
| `/web/cache/<10 Ziffern>_<hash>.js/.css` | HTML | WA-Regex `/web/cache/[0-9]{10}_.+` | sehr hoch |
| `/themes/Frontend/<Theme>/` (Responsive/Bare) | HTML | `themes/Frontend/Responsive/…` | hoch |
| `/engine/Shopware/`, `jquery.shopware.min.js` | HTML | WA | hoch |
| Cookies `session-1`, `__csrf_token-1` (Endung = Shop-ID) | Set-Cookie | Shopware-Forum | mittel |
| Header `X-Shopware-Cache-Id` | nur bei aktivem HTTP-Cache | Shopware-Doku | ⚠ niedrig |
| `<meta name="application-name" content="Shopware">` | HTML | WA | mittel |

Seit 31.07.2024 gibt es keine offiziellen Sicherheitsupdates mehr. Es bleibt nur ein kostenpflichtiger Langzeitsupport (SafeFive). ⚠ Ein Shopware-5-Live-Shop wurde nicht selbst geprüft; die Merkmale stammen aus WA und der Doku.

## 4. Shopify / Shopify Plus

| Merkmal | Wo | Beispiel | Zuverlässigkeit |
|---|---|---|---|
| `powered-by: Shopify` | Header | beob. | sehr hoch |
| `Link: </.well-known/ucp>; rel="ucp"` | Header | beob. | hoch (neu 2026) |
| `server-timing … theme;desc="<id>"`, `pageType` | Header | beob. | hoch |
| Cookies `_shopify_essential`, `localization`, `cart_currency` | Set-Cookie | beob. | hoch |
| `Shopify.shop = "x.myshopify.com"` | HTML | beob. `snockssocks.myshopify.com` | sehr hoch |
| `Shopify.theme = {name,id,schema_name,…,theme_store_id}` | HTML | `theme_store_id:null` ⇒ eigenes bzw. Agentur-Theme (beob.) | sehr hoch |
| `Shopify.locale`, `Shopify.country`, `Shopify.currency` | HTML | beob. | hoch |
| `cdn.shopify.com/s/files/…`, `cdn.shopify.com/extensions/<id>/<app-slug>` | HTML | App-Einbindungen beob. | hoch |
| `robots.txt` mit `# Shopify storefront.` | robots.txt | beob. | hoch |
| DNS: A-Record `23.227.38.x`, www-CNAME `shops.myshopify.com` | DNS | beob. snocks.com, hey-honey.de | hoch, braucht keinen HTTP-Abruf |
| `x-shopid`, `x-shopify-stage` | Header | stehen in WA, **2026 bei beiden geprüften Shops nicht vorhanden** | ⚠ veraltet, nicht verwenden |

**Öffentliche Endpunkte:**

- **`GET /meta.json`** ist das wertvollste Signal. Felder: `name`, `city`, `country`, `currency`, `domain`, `myshopify_domain`, `ships_to_countries[]`, `published_products_count`, `published_collections_count`, `offers_shop_pay_installments`. Beispiel snocks: 485 Produkte, 11 Lieferländer, Sitz Mannheim (beob.).
- `GET /products.json?limit=1` liefert Produktfelder (`vendor`, `product_type`, Preise, `updated_at`). Höchstens `limit=250`. Seitenweises Blättern ist nicht dokumentiert. Nur für Stichproben nutzen (Preisspanne, Eigenmarke), **nie den Katalog übernehmen**.
- `/sitemap.xml` ist ein Index mit `sitemap_products_N.xml` u. a. (beob.).

**Abrufgrenzen:** Shopify nennt für Shops keine festen Grenzen. Verdächtige Abrufe bekommen **430 Security Rejection**, oft ohne `Retry-After`. Bei 429/430 abbrechen, frühestens nach ≥ 60 s einmal wiederholen.

**Märkte:** `hreflang`-Links und `ships_to_countries` zeigen Sprachen und Länder. snocks.com hat 15 Locales (beob.).

**Shopify Plus** ⚠: Es gibt kein sicheres öffentliches Merkmal mehr, weil `checkout.liquid` seit 13.08.2024 abgeschaltet ist. Daraus nur einen Wert „Plus wahrscheinlich“ bilden, kein festes Label. Indizien:

- mehrere myshopify-Shops pro Marke, also eine andere `Shopify.shop` je Länderdomain
- eigenes Theme
- mehr als ~5 Länder
- B2B-Preise

## 4a. DNS-Regeln für gehostete Systeme (vor jedem HTTP-Abruf)

Gehostete Systeme lassen sich ohne Webseitenabruf erkennen. Shopify-IPs **nie** in Masse per HTTP abrufen, weil Shopify mit 430 sperrt.

| Merkmal (A-Record bzw. Alias-Kette aus `socket.gethostbyname_ex`) | System | Beleg |
|---|---|---|
| A 23.227.38.0/24 (PTR myshopify.com) oder CNAME `shops.myshopify.com` / `<handle>.myshopify.com` | Shopify | 5/5 bzw. 4/4 bekannte Shops [M]. In 3.000 CrUX-.de-Domains 97 Treffer (3,2 %) [M] |
| CNAME `shops.shopware.store` (→ Fastly 151.101.x.196) | Shopware SaaS | aus der Shopware-Doku, gemessen; in Stichproben 0 Kunden gefunden ⚠ |
| CNAME `cdn.shopware.shop` | Shopware PaaS | gemessen ⚠ |
| `pointing.wixdns.net` bzw. 185.230.63.0/24 | Wix | gemessen bzw. Anleitungen |
| `ext-cust.squarespace.com` bzw. 198.185.159.144/145, 198.49.23.144/145 | Squarespace | gemessen |
| `web.jimdosite.com` bzw. **162.159.128.70/129.70** (nur ~13 % der Jimdo-Seiten haben „jimdo“ in der Kette) | Jimdo | gemessen; IP vorher an 20 Hosts per Header `x-jimdo` bestätigen |
| `proxy.webflow.com` / 198.202.211.1 | Webflow | gemessen |

**Selbst gehostete Systeme** (Shopware 5/6, WooCommerce, JTL, Gambio, OXID, Magento) haben **kein** DNS-Merkmal. Spezial-Hoster (maxcluster, timmehosting, creoline) taugen nur zur Priorisierung (2/7 Shopware).

**Zertifikats-Logs:** Shopify-Shops mit eigener Domain bekommen einzelne Let's-Encrypt-Zertifikate und stehen damit einzeln in CT. Nur Subdomains unter `*.myshopify.com` bzw. `*.shopware.store` verstecken sich hinter Wildcard-Zertifikaten.

## 5. Weitere Systeme (Quelle WA, sofern nicht anders angegeben)

| System | Merkmale | Öffentlicher Endpunkt |
|---|---|---|
| **WooCommerce** | `/wp-content/plugins/woocommerce/`, JS `wc_add_to_cart_params`/`woocommerce_params`, Klasse `woocommerce-no-js`, `generator WooCommerce x.y` | `GET /wp-json/wc/store/v1/products?per_page=1` ⇒ Header `X-WP-Total` (Produktanzahl) |
| **Magento 2 / Adobe Commerce** | `/static/version<ts>/frontend/<Vendor>/<theme>/<locale>/`, `script[type="text/x-magento-init"]`, Cookie `mage-cache-storage`, Header `X-Magento-Vary` | `GET /magento_version` ⇒ „Magento/2.4 (Community)“ (abschaltbar) |
| **JTL-Shop** | Cookie `JTLSHOP`, `jtl_token`, `/templates/NOVA/` (Standard ab JTL-Shop 5), JS `JtlHelpers` | ⚠ keine öffentliche Katalog-API |
| **Gambio** | `templates/gambio/`, `gm_javascript.js.php`, Kommentar `Shopsoftware by Gambio GmbH`, NEU `/GXModules/` (GX4) | Cookie `GXsid_<hash>` bestätigt (2/2) |
| **OXID eShop** | Cookie `sid_key=oxid`, `/out/<theme>/src/` (beob. bergfreunde.de), HTML-Kommentar mit Edition/Version | – |
| **PrestaShop** | JS `prestashop`, `/modules/ps_*/`, Cookie `PrestaShop-<hash>`, `generator PrestaShop` | – |
| **plentyShop** | Header `X-Plenty-Shop: Ceres` (= plentyShop LTS), `plenty.shop.min.js` | LTS-Support bis Q1 2026 ⇒ Migrationsanlass ⚠ |
| **xt:Commerce** | `generator xt:Commerce`, JS `XT.version.version` | – |
| **modified eCommerce** | ⚠ noch keine geprüften Merkmale; in WA nachsehen | – |
| **BigCommerce** | `cdn11.bigcommerce.com`, JS `bigcommerce_config` | – |
| **Salesforce Commerce Cloud** | `/on/demandware.static/`, `/on/demandware.store/Sites-…`, Cookies `dwsid`, `dw_dnt` | – |
| **Headless (commercetools, eigene Next/Nuxt-Frontends)** | `/_next/static`, `x-powered-by: Next.js`/`Nuxt`, API-Hosts im JS-Bundle (`*.commercetools.com`) | headless Shopware: `/media/xx/` + `SWSC…`-Schlüssel |
| **Wix** | `X-Wix-Request-Id`, `static.parastorage.com`, Modul `wixstores` | – |
| **Squarespace** | `server: Squarespace`, `Static.SQUARESPACE_CONTEXT` | – |
| **Jimdo** | `X-Jimdo-Instance`, JS `jimdoDolphinData` | – |
| **ePages** | `X-epages-RequestId`, JS `epages` | – |

## 6. Qualifizierungssignale (für Prüfprofil und Personalisierung)

Die Spalte „Abruf“ nennt, woher das Signal kommt: S = Startseite, X = Sitemap, A = ein API-Abruf.

| Signal | Quelle | Abruf |
|---|---|---|
| Shopsystem, Version, Supportende | Abschnitte 2–5 | S |
| Produktanzahl | Shopify `meta.json`; WooCommerce `X-WP-Total`; SW6 `total` (nur mit Schlüssel); sonst Sitemap zählen | A oder X |
| Preisspanne, Eigenmarke vs. Handelsware | Shopify `products.json?limit=250` (`vendor` = Shopname ⇒ Eigenmarke); sonst JSON-LD `Product`/`Offer` ⚠ | A |
| Länder, Sprachen | `hreflang`, `ships_to_countries`, SW6-Schlüssel je Land | S/A |
| Zahlungsanbieter | Skript-Hosts und Plugin-Namen: `klarnaservices.com`, `js.stripe.com`, `/bundles/molliepayments/`, `swag-pay-pal` (beob.) | S |
| Bewertungen, Siegel | `widgets.trustedshops.com`, `cdn.judge.me`, `.ekomi-widget-container`, ShopVote ⚠ | S |
| Marketing-Werkzeuge | GTM `googletagmanager.com/gtm.js`, Meta `connect.facebook.net/…/fbevents.js`, TikTok `analytics.tiktok.com`, Klaviyo `klaviyo.com` (beob.) | S |
| Newsletter | Plugin-Namen wie `newsletter-sendinblue` (beob.), Klaviyo-Formulare | S |
| B2B-Funktionen | SW6 B2B-Suite ⚠ (Pfadname ungeprüft); BigCommerce B2B `cdn.bundleb2b.net` | S |
| Aktualität | SW6-Asset-Zeitstempel, `Shopify.theme.name` mit Datum, `<lastmod>` in Sitemaps. Das Copyright-Jahr ist ein schwaches Signal (bei 5 von 5 Shops nicht per Regex auffindbar) | S/X |
| Agentur-Indiz | eigenes Theme (`theme_store_id:null`), viele eigene Plugins | S |
| Traffic | Skael `webtraffic` (SimilarWeb-Daten; kleine Shops oft ohne Daten, dann kostenlos) | extern |

## 7. Impressum finden

1. **Footer-Links der Startseite** mit `impressum|imprint|anbieterkennzeichnung|legal-notice|legal` (ohne Groß-/Kleinschreibung) auslesen. Das traf bei allen 5 geprüften Shops (beob.).
2. **Fallback-Pfade** in dieser Reihenfolge:
   - `/impressum`
   - `/policies/legal-notice` (Shopify, native Seite, beob. HTTP 200)
   - `/pages/impressum` (Shopify, beob.)
   - `/imprint`
   - `/Impressum.html` (beob. kochform.de)
3. **Kontaktseite:** Nach der BGH-„Zwei-Klick“-Rechtsprechung darf das Impressum über „Kontakt“ erreichbar sein. Die Kontaktseite deshalb als letzten Fallback mitnehmen.
4. **Shopware 6:** Impressum ist eine CMS-Seite mit SEO-URL, z. B. `/de/Impressum/` (beob.). Manchmal öffnet es sich als Modal über `/widgets/cms/<id>`.
5. Kein Impressum im HTML (JS-gerenderter Headless-Footer) ⇒ Status `needs_js` (`architektur.md`).

## 8. Open-Source-Regelsammlungen (Stand 08.10.2026)

| Projekt | Lizenz | Letzter Commit | Nutzen |
|---|---|---|---|
| `enthec/webappanalyzer` | GPL-3.0 | 16.09.2026 | führt die Wappalyzer-Regeln weiter (~7.600 Technologien, `src/technologies/*.json`) |
| `projectdiscovery/wappalyzergo` | MIT (Code) | 04.10.2026, wöchentlich | Go-Umsetzung, Grundlage von `httpx -td` |
| `HTTPArchive/wappalyzer` | GPL-3.0 | 03.10.2026 | zweiter gepflegter Ableger, Grundlage der HTTP-Archive-Daten |
| `chorsley/python-Wappalyzer` | GPL-3.0 | **archiviert 2024** | nicht nutzen |

**Empfehlung:**

- Für das **Shopsystem** eigene, schlanke Regeln (dieses Dokument). Die Shop-Regeln in WA sind dünn: Shopify Plus fehlt, die Trennung SW5/SW6 klappt nur per Regex, `x-shopid` ist veraltet, `meta.json` und `/store-api` fehlen.
- Für **Zusatzwerkzeuge** (Zahlung, Siegel, Marketing) können die WA-Regeln zur Laufzeit geladen werden (Header-, Cookie-, Script-, Meta-, HTML-Regeln; JS/DOM-Regeln weglassen).
- **GPL beachten:** Die Daten nicht ins Paket einbetten, sondern laden. Vor einer Weitergabe des Pakets die Lizenzfolgen prüfen.

## 9. Wenn eine Regel nicht mehr stimmt

Shopsysteme ändern Merkmale. Ein Beispiel ist der Shopify-Header `x-shopid`, der 2026 nicht mehr gesendet wird. Vorgehen:

1. Den falsch erkannten Shop mit Datum und betroffener Regel in Abschnitt 2–5 eintragen und die Regel als ⚠ markieren.
2. Im Code die Regel ändern. Die Regeln haben eine Versionsnummer (`fp_version`), damit erkennbar bleibt, welcher Datensatz mit welchem Regelstand klassifiziert wurde.
3. Erkennung aus dem gespeicherten HTML neu laufen lassen, ohne neue Abrufe (`architektur.md`).
4. `Stand` oben aktualisieren und `python3 werkzeuge/wissen_pruefen.py` ausführen.

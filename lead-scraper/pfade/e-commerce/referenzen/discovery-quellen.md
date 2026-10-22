# Kandidatenquellen: Onlineshops nach Shopsystem finden

**Zweck:** woher die Shop-Liste kommen kann, die der Pfad als Eingabe braucht, wie groß der Markt ist, was die Quellen kosten und was ihre Lizenzen erlauben.
**Für wen:** Betreiber vor der Entscheidung für eine Quelle; KI-Modelle, die Kosten- und Lizenzfragen beantworten.
**Verwandt:** `../../../wissen/06_pfad-e-commerce.md` · `fingerprints.md` · `../../../wissen/08_versand-und-recht.md`
**Stand:** 2026-10-09 · **Prüfen bis:** 2027-01-09 (Preise und Zahlen der Anbieter ändern sich laufend)

Kennzeichnung:

- **[V]:** in der Primärquelle selbst gelesen oder selbst geprüft
- **[D]:** Drittquelle oder Herstellerangabe
- **[S]:** Schätzung

## Inhalt

0. Empfehlung: Listen über Anbieter mit Claude-Anbindung · 1. Kurzfassung · 2. Kommerzielle Verzeichnisse · 3. Freie Rohquellen · 4. Verzeichnisse von Händlern
5. Marktgrößen · 6. Empfohlener Mix und Kosten · 7. Lizenzen · 8. Offene Punkte


> **Einordnung:** Recherche vom 08.10.2026 für spätere Ausbaustufen. **Nicht Teil des aktuellen Pfads.** Der Pfad ist ein Nachbau des Clay-Workbooks ECOM 2.0 (`../ABLAUF.md`). Er erkennt das Shopsystem nicht und braucht eine fertige Shop-Liste.

---

## 0. Empfehlung: Listen über Anbieter mit Claude-Anbindung (Recherche 2026-10-09)

**Entscheidung des Betreibers (2026-10-09):** kein eigenes Crawlen von Hunderttausenden Websites (`shop-katalog.md` ist zurückgestellt). Die Shop-Liste kommt aus dem Index eines Technologie-Anbieters. Jeder Nutzer hat dort **ein eigenes Konto** und verbindet es in Claude. So crawlt niemand selbst, und es gibt kein Weiterverkaufsproblem.

**Ein „Oxylabs für Shopsysteme“ gibt es nicht.** Oxylabs, Bright Data, Apify und Firecrawl rufen nur Seiten ab, die man ihnen nennt. Sie eignen sich zum **Prüfen** einer vorhandenen Liste, nicht zum **Finden**.

| Quelle | Shopware DE | Kosten | Claude-Anbindung | Nutzungsbedingungen | Rolle |
|---|---|---|---|---|---|
| **DataForSEO** `domains_by_technology` | Filter Technologie + Land, keine SW5/SW6-Trennung. Abdeckung **ungeklärt** (Shopify DE: 26.872 gegen 101.951 bei StoreLeads) | 1,212 $ je 1.000 Domains + 0,012 $ je Abruf; 50 $ Mindestaufladung, kein Abo [V] | offizieller Connector mit OAuth: `https://mcp.dataforseo.com/v3/mcp` (nicht `/mcp`) [V] | keine Klausel gegen Weiterverkauf oder Kaltakquise (AGB 12.06.2026) [V] | Standard-Kandidat, **nach Abdeckungstest** |
| **PublicWWW** (Quelltext-Suche) | SW6 `"frontend.cart.offcanvas" site:de`, SW5 `"/web/cache/" site:de`; Land nur über die Endung | kostenlos (Top 3 Mio. Sites, 1.000 Zeilen); 49 $/Tag, 109 $/Monat [V] | offizieller Connector mit OAuth, auch mit Gratis-Konto [V] | „exploit for any commercial purposes“ mehrdeutig, schriftlich klären | günstige Alternative mit SW5/SW6 |
| **StoreLeads** | 20.137 (DE), beste Abdeckung | Pro 250 $/Monat, Elite 450 $ [V] | Connector `storeleads.app/mcp` ab Pro [V] | verbieten „mass mailings“ und „commercial electronic messages in bulk“, keine Weitergabe [V] | Premium, nur mit eigenem Konto des Nutzers |
| **BuiltWith** | SW5/SW6 getrennt, mit Firma/Ort/Kontakt | Basic 295 $ je 30 Tage [V] | Connector nur mit API-Schlüssel im Header | nur interne Nutzung, kein Spam, **keine Weitergabe an „third-party data provider“** [V] | strengste Bedingungen |
| **Vibe Prospecting** (Explorium) | ob Shopware als Wert existiert, unklar; max. 1.000 je Abfrage | 200 Credits/Monat gratis [V] | im Claude-Verzeichnis, OAuth [V] | keine „unsolicited emails“, außer rechtlich zulässig [V] | nur gratis testen |
| Bright Data / Oxylabs / Apify | finden keine Shops | Bright Data 5.000 Abrufe/Monat gratis, dann 1,50 $ je 1.000 [V] | Bright Data per Token-URL; Oxylabs in claude.ai nicht nutzbar | Kunde verantwortlich | nur Prüfen |

**Ablauf für Nutzer (Ziel):** Datenquelle in Claude verbinden → Claude zählt und nennt Kosten → Liste holen → `python3 -m ecom import` → Shop-Prüfung und Anreicherung wie gebaut.

**Erfahrungen mit einem BuiltWith-Export „Shopware websites in Germany“ (Stand 19.05.2026, 12.442 Zeilen):**

- ~20 % nach 5 Monaten offline oder nicht mehr Shopware (Stichprobe 200) [V]. Die Prüfung im Pfad (Stufe 1c) ist deshalb Pflicht.
- 7.809 Zeilen tragen SW5, 2.239 SW6; die SW5-Zahl enthält vermutlich alte Erkennungen [S].
- 794 Shops liegen auf einer anderen Adresse als die Hauptdomain (z. B. `shop.firma.de`). `ecom import` nimmt deshalb die Spalte `Location on Site`.
- Lizenz: Nutzung nur intern; die Weitergabe an einen „third-party data provider“ kollidiert dem Wortlaut nach mit der Anreicherung über Skael. Vor einem Lauf abwägen (keine Rechtsberatung).

**Offen:** Abdeckungstest DataForSEO (`technologies_summary` für Shopware, JTL Shop, Gambio, plentymarkets) · PublicWWW-Gratis-Test · Nutzungsbedingungen schriftlich klären · wie eine Liste aus claude.ai (Cloud-Sandbox) in den lokalen Pfad kommt.

Quellen: https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live/ · https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api · https://dataforseo.com/terms-of-service · https://publicwww.com/prices.html · https://publicwww.com/docs/mcp/claude/ · https://storeleads.app/terms · https://builtwith.com/terms · https://claude.com/marketplace/connectors/vibe-prospecting · https://brightdata.com/pricing/web-unlocker

## 1. Kurzfassung

> Stand 08.10.2026, vor der Entscheidung gegen eigenes Crawlen. Für die aktuelle Empfehlung gilt Abschnitt 0.

| Quelle | Rolle |
|---|---|
| **StoreLeads Pro** (250 $/Monat, 2 Plattformen) | Hauptquelle: einen Monat buchen, DACH exportieren, kündigen |
| **Eigene Erkennung** (`fingerprints.md`) | Pflicht: prüft, ob der Shop noch läuft, und bestimmt Version und Signale |
| **HTTP Archive × Chrome UX Report** | kostenlose Ergänzung für Shops mit Traffic, auch weitere Systeme |
| **Skael `google_search`** | Nischen (Sortiment + Region) |
| Common Crawl, PublicWWW | Long Tail, nur bei großer Lücke |

Grobkosten nur für die Kandidaten bei 5.000 Shopware-Shops DE: ~250 $ (≈0,05 € je Shop) [S].

## 2. Kommerzielle Verzeichnisse

| Anbieter | Shopware DE | Shopify DE | Preis (USD/Monat) | API | Nutzungsrechte |
|---|---|---|---|---|---|
| **StoreLeads** | 20.137 live (AT 1.171, CH 1.241), Stand 02.10.2026 [V] | 101.951 live [V] | Premium 75 (ohne Export/API), **Pro 250** (2 Plattformen, CSV, API), Elite 450 (alle Plattformen), Enterprise 950; −15 % jährlich [V/D] | ab Pro | Weiterverkauf/Veröffentlichung nur mit Erlaubnis; Klausel gegen Massen-Werbemails [V] |
| **BuiltWith** | widersprüchlich: 14.523 / 18.637 (SW6) / 17.022 (SW5), vermutlich inkl. historischer Shops [D] | – | Basic 295 (2 Technologien), Pro 495, Team 995 [V] | ja | kein Spam, Telefonnummern nicht für Marketing, kein Weiterverkauf (AGB 06.03.2026) [V] |
| **Wappalyzer** | ≈20.500 [S aus V] | ≈45.000 [S] | Pro 250 (5.000 Credits, verfallen nach 60 Tagen), Business 450 [V] | ja | keine Unterlizenz, kein Weiterverkauf, keine Einbindung in Kundenprodukte [V] |
| **TechnologyChecker.io** | 8.962 Firmen DE; ~66 % SW6 / ~34 % SW5 [V] | – | Free 100 Abfragen, Pro 89, Scale 249 [V] | ab Pro | nicht geprüft |
| SimilarTech | unbekannt | unbekannt | keine offiziellen Preise | – | – |
| TheirStack | **ungeeignet**: Technik aus Stellenanzeigen [V] | – | – | – | – |
| StoreCensus, StoreInspect | nur Shopify [D] | ja | ab 49 [D] | ja | – |

**StoreLeads-Felder [V]:**

- Produktanzahl, Umsatzschätzung, installierte Apps samt Änderungsverlauf, Mitarbeiterzahl, Social-Media-Profile
- nur **allgemeine** E-Mail-Adressen und Telefonnummern, keine Personen
- Anteil Shops mit E-Mail: 59 % bei Shopware, 77 % bei Shopify DE
- Shopware-Bestand Q3 2026: −3 % zum Vorjahr
- keine Trennung SW5/SW6 im öffentlichen Bericht

## 3. Freie Rohquellen

### HTTP Archive (BigQuery) – empfohlen als Ergänzung

- **Tabelle:** `httparchive.crawl.pages`. Das Feld `technologies` (`ARRAY<STRUCT<technology, categories, info>>`) enthält Wappalyzer-Treffer samt Version. `date` ist Pflichtfilter [V].
- **Abdeckung:** nur Origins aus dem Chrome UX Report, also Seiten mit genug Chrome-Traffic (2025: 16,2 Mio. Websites) [D]. Kleine Shops fehlen [S].
- **DACH-Filter:** Join mit `chrome-ux-report.country_de.YYYYMM` (bzw. `country_at`, `country_ch`) [D].
- **Kosten:** 6,25 $/TiB, das erste TiB im Monat ist frei. Nur die nötigen Spalten wählen und vorher einen Testlauf (`--dry_run`) machen; `LIMIT` spart nichts [V/D].
- ⚠ Prüfen, ob 2026 weiter monatlich gecrawlt wird.

```sql
SELECT DISTINCT p.root_page, t.technology, ARRAY_TO_STRING(t.info, ',') AS version
FROM `httparchive.crawl.pages` p, UNNEST(p.technologies) t
WHERE p.date = '2026-09-01' AND p.client = 'mobile' AND p.is_root_page
  AND t.technology IN ('Shopware','Shopify','WooCommerce','JTL Shop','Gambio','OXID eShop',
                       'Magento','PrestaShop','plentyShop LTS','xtCommerce')
-- danach JOIN auf rtrim(origin,'/') aus chrome-ux-report.country_de.202609
```

Exakte Namen per Tech-Report-API geprüft (08.10.2026): `JTL Shop`, `xtCommerce` (nicht „JTL-Shop“, „xt:Commerce“). Der Crawl läuft 2026 monatlich weiter.

**Kostenlose Zählung ohne Konto:** Die Technology-Report-API (`https://cdn.httparchive.org/v1/adoption?technology=Shopware,Shopify&geo=Germany&rank=ALL&start=latest`) liefert Origins je System und Land. Stand 08/2026, mobile: Shopware DE 6.452, AT 1.335, CH 522; Shopify DE 31.942 [V]. Die Zahlen schwanken stark (Shopware DE 9.801 → 4.227 → 6.452 ohne Regeländerung) und erkennen SW6 nur an Headern. Deshalb taugen sie nur als Warnsignal, nicht als Liste. Bewertung: `shop-katalog.md`, Abschnitt 7.

### Common Crawl

- **Columnar-Index** (Parquet auf S3, Abfrage per AWS Athena, ~5 $/TB gescannt). Ein Crawl dauert mit wenigen Spalten < 10 $ [D/S].
- **Kein HTML im Index**, deshalb Suche über URL-Muster, gefiltert auf `.de/.at/.ch` [S, nicht validiert]:
  - Shopware 5: `shopware.php`, `sViewport=`
  - JTL-Shop: `navi.php`, `bestellvorgang.php`
  - Gambio/modified/xt:Commerce: `product_info.php`
  - OXID: `?cl=details`
  - Shopify: `/collections/` + `/products/`
- Danach immer mit der eigenen Erkennung prüfen.

### Weitere

| Quelle | Befund |
|---|---|
| **DNS für Shopify** | A-Record `23.227.38.x`, www-CNAME `shops.myshopify.com` [V]. Sehr billig, braucht aber Kandidaten-Domains |
| **Tranco** (Top 1 Mio.) | Kandidatenliste, aber ohne Länderfilter [V] |
| **PublicWWW** | Suche im Quelltext (z. B. `/web/cache/`). Pro 109 $/Monat; Aktualität des Index unklar [V/S] |
| **SERP-APIs** | Skael `google_search` 1 Credit je Suche [V]; DataForSEO 0,0006 $ je Seite, ×5 bei `inurl:` [V]; SerpApi 75 $ für 5.000 [V]. Footprints wie „powered by Shopware“ stehen in modernen Themes selten, deshalb **für Nischen**, nicht für Massen-Discovery |
| Certificate Transparency | **Korrigiert 08.10.2026:** Shopify-Shops mit eigener Domain haben einzelne Let's-Encrypt-Zertifikate und stehen einzeln in CT (4/4 gemessen). Unbrauchbar ist CT nur für Subdomains unter `*.myshopify.com` (Wildcard). Live-Strom mit < 1 min Verzug gemessen; als Quelle bewertet in `shop-katalog.md` (Phase D) |
| Zonendateien | .de: DENIC gibt sie nicht heraus; .ch: nur für Forschung/Sicherheit [D] |
| Shodan, Censys | indexieren nach IP. Shop-Domains hinter Shopify-IPs finden sie schlecht; nachrangig [S] |

## 4. Verzeichnisse von Händlern

| Quelle | Befund |
|---|---|
| **Trusted Shops** | > 32.000 Shops in Europa [D]. `robots.txt` sperrt `/shoplist/` und mehrere Bots [V]. Datenbankschutz kann greifen. **Nicht systematisch auslesen** [S] |
| **Shopware-Showcases** | kuratiert, einige hundert Einträge, mit umsetzender Agentur. Von `robots.txt` nicht gesperrt [V]. Gut für Referenz- und Agentur-Ansprache |
| **EHI/ECDB Top 1000** | kostenpflichtig, nur große Shops [D] |
| idealo | Bot-Schutz schon bei `robots.txt` [V]. Nicht nutzen |
| billiger.de | Shopprofile nicht explizit gesperrt; AGB ungeprüft |
| Händlerbund, Google Merchant Center | keine öffentlichen Listen gefunden |

## 5. Marktgrößen (live Shops = Domains, nicht Firmen)

| System | DE | AT | CH | Quelle |
|---|---|---|---|---|
| Shopware gesamt | 20.137 | 1.171 | 1.241 | StoreLeads 02.10.2026 [V] |
| ↳ Anteil Shopware 5 | grob 25–35 % | | | TechnologyChecker 09/2026 ~34 % [V]; unsicher |
| Shopify | 101.951 | 11.134 | 22.763 | StoreLeads [V/D]; Wappalyzer schätzt DE nur ≈45.000 |
| Shopify Plus | – | – | – | 80.050 Domains weltweit [V] |
| WooCommerce | 115.088 | – | – | StoreLeads [V] |
| Magento / Adobe Commerce | 6.974 | – | – | StoreLeads [V] |
| JTL-Shop | 5.639 | 317 | 243 | StoreLeads [V] |
| Gambio | 4.866 | 392 | 346 | StoreLeads [V] |
| PrestaShop | 3.213 | – | 2.155 | StoreLeads [V] |
| modified eCommerce | 1.851 | 102 | 99 | StoreLeads [V] |
| OXID | 1.283 | 85 | 63 | StoreLeads [V] |
| plentymarkets | 1.261 | 26 | 27 | StoreLeads [V] |
| xt:Commerce | 605 | 54 | 33 | StoreLeads [V] |
| Salesforce Commerce Cloud | 161 | – | – | StoreLeads [V] |

Realistisch für Shopware DE: **15.000–20.000 eindeutige Händler** [S]. Länder-Domains desselben Händlers fallen beim Dedupe über die Firma zusammen.

## 6. Empfohlener Mix und Kosten

| Posten | A: Kauf + eigene Prüfung | B: nur freie Quellen |
|---|---|---|
| Kandidaten | StoreLeads Pro, 1 Monat: 250 $ | BigQuery 0–30 $, Athena < 10 $ |
| Prüfung (5.000–20.000 Abrufe) | eigener Rechner oder Server für 5–20 € | gleich |
| Entwicklungsaufwand | ~1 Tag (Import + Erkennung) | ~3–5 Tage (SQL, URL-Muster, Abgleich) |
| Ausbeute | ~20.000 Kandidaten, davon ~15.000+ geprüft | unsicher, eher Tausende mit Traffic |
| **Summe** | **~230–260 €** | **~10–50 €** |

**Empfehlung [S]:** Variante A als Grundbestand, Variante B als laufend kostenloser Zufluss für neue Shops und Systemwechsel. Ob A überhaupt in Frage kommt, hängt an der Lizenzfrage (Abschnitt 7).

**Überholt durch die Methodenwahl vom 08.10.2026:** Gewählt ist ein eigener Shop-Katalog aus den CrUX-Länderlisten mit eigener Erkennung (`shop-katalog.md`). Kaufquellen nur noch für die interne Kalibrierung.

## 7. Lizenzen – was mit den Daten erlaubt ist

- **StoreLeads, Wappalyzer, BuiltWith:**
  - kein Weiterverkauf
  - keine Weitergabe an Dritte
  - keine Einbindung in Produkte für Kunden
  - Klauseln gegen Spam und unzulässiges Marketing
- **Folgen für dieses Paket:**
  - Ein Nutzer, der den Pfad für sich selbst laufen lässt, braucht einen **eigenen** Zugang.
  - Listen, die der Betreiber für Kunden baut und ausliefert, sind sehr wahrscheinlich **nicht** gedeckt. Ausweg: Der Kunde bucht selbst, oder es gibt eine schriftliche Freigabe bzw. Enterprise-Lizenz [S].
- **Freie Quellen** (HTTP Archive, Common Crawl, eigene Erkennung) haben diese Einschränkung nicht. Für das Ansprechen gelten trotzdem UWG und DSGVO (`../../../wissen/08_versand-und-recht.md`).
- **GPL der Fingerprint-Regeln (WA):** siehe `fingerprints.md`, Abschnitt 8.

## 8. Offene Punkte

- BuiltWith blockiert automatisierte Abrufe; die Zahlen sind nur aus Suchtreffern und widersprüchlich.
- StoreLeads: Exportgrenzen je Tarif nicht gefunden. Vor der Buchung nachfragen.
- HTTP Archive: Crawl-Rhythmus 2026 und gescanntes Datenvolumen per Testlauf prüfen.
- AGB von Trusted Shops, idealo und billiger.de nicht gelesen.

## Quellen (Auswahl)

- StoreLeads: https://storeleads.app/reports/shopware · https://storeleads.app/reports/shopify · https://storeleads.app/terms
- BuiltWith: https://builtwith.com/plans · https://builtwith.com/terms
- Wappalyzer: https://www.wappalyzer.com/pricing/ · https://www.wappalyzer.com/terms/
- TechnologyChecker: https://technologychecker.io/technology/shopware
- HTTP Archive: https://httparchive.org/docs/reference/tables/pages/ · https://httparchive.org/docs/guides/minimizing-costs/
- CrUX: https://developer.chrome.com/docs/crux/bigquery
- Common Crawl: https://commoncrawl.org/blog/index-to-warc-files-and-urls-in-columnar-format
- Shopify-DNS: https://help.shopify.com/en/manual/domains/add-a-domain/connecting-domains/connect-domain-manual
- PublicWWW: https://publicwww.com/prices.html
- Shopware-Showcases: https://www.shopware.com/de/kunden/showcases/

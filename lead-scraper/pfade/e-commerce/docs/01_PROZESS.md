# Prozess: jede Clay-Spalte und wo sie im Code steht

**Zweck:** jede Clay-Spalte und ihre Code-Stelle zeigen, damit sich der Nachbau mit dem Workbook abgleichen lässt und bei Änderungen in Clay die passende Stelle schnell gefunden ist. Bausteine ohne Clay-Vorbild sind mit „neu, nicht in Clay“ markiert, bewusste Abweichungen stehen in `05_ABWEICHUNGEN.md`.
**Für wen:** Entwickler und KI-Modelle, die den Pfad ändern oder mit Clay abgleichen.
**Verwandt:** `05_ABWEICHUNGEN.md` · `clay_spalten_lesbar.md` (alle Formeln und Prompts im Wortlaut) · `clay_export_ecom_2_0.json` (Rohexport)
**Stand:** 2026-10-09 · Quelle: Clay-Workbook „Copy of Vorlage | ECOM 2.0“ (Export vom 2026-10-08, `docs/clay_export_ecom_2_0.json`). Bausteine ohne Clay-Vorbild sind mit **neu, nicht in Clay** markiert

---

## Das Prinzip in einem Satz

Eine fertige Liste von Shops (Firmenname und/oder Website) wird zuerst **billig geprüft**: Ist das ein aktiver Onlineshop, passt er zum Shop-Profil des Kunden (neu, nicht in Clay), und hat er messbare Besucher? Nur die Shops, die alles erfüllen, durchlaufen die **teure Anreicherung** (Impressum, Geschäftsführer-Mail, Anrede, Personalisierung, Videotitel).

```
Anforderungen ─► CSV ─► Stufe 1 (Clay Import) ─────────────────────────────────────────────────► Stufe 2 (Clay ANREICHERUNG) ─► Export (+ Mailtext)
(neu)                   Domain finden → Website abrufen → aktiver Shop? → Shop-Profil? → Traffic → SEND     Impressum → Dedupe → E-Mail → Anrede → Personalisierung → Videotitel → Ready to Send
```

## Vor dem Lauf: Anforderungen (neu, nicht in Clay)

In Clay gab es kein Shop-Profil und keinen Mailtext; der Personalisierungs-Prompt stand fest im Workbook. Im Nachbau klärt die KI diese drei Anforderungen im Gespräch (`../ABLAUF.md`, Phase 1) und speichert sie in der Datenbank, Tabelle `meta(key, value)` (`db.set_meta`, `db.get_meta`):

| Meta-Schlüssel | Inhalt | Setzen mit | Builder |
|---|---|---|---|
| `prompt_shopprofil` | Shop-Profil-Prompt. Schlüssel fehlt = noch nicht entschieden; leerer Wert = bewusst ohne Profil | `set-prompt shopprofil <datei>` bzw. `--ohne` | `prompts/shopprofil_builder.md` |
| `prompt_personalisierung` | Personalisierungs-Prompt des Auftrags | `set-prompt personalisierung <datei>` | `prompts/personalisierung_builder.md` |
| `mailtext` | Mailvorlage: `Betreff: …`, Leerzeile, Text mit Platzhaltern | `set-mailtext <datei>` | `prompts/personalisierung_builder.md`, Runde 2 |

**Sperre in `run`** (`pipeline.fehlende_anforderungen`): Vor der ersten Stufe prüft der Lauf die Anforderungen. Enthält er `1c`, `1d` oder `1e`, muss `prompt_shopprofil` existieren (leer erlaubt), denn Traffic und Übergabe hängen am Profil-Ergebnis. Enthält er `2e` und ist `DO_PERSONALISIERUNG=true`, müssen `prompt_personalisierung` und `mailtext` gesetzt sein. Sonst Abbruch mit Meldung und Exit-Code 2, bevor etwas kostet. `status` und `doctor` zeigen denselben Stand im Block „Anforderungen“.

## Stufe 1 – Clay-Tabelle „Import“

| Clay-Spalte | Typ in Clay | Laufbedingung (Run-If) | Code | Ergebnisfeld (`shops`) |
|---|---|---|---|---|
| `Firmenname`, `website` | Eingabe | – | `cli.cmd_import` | `firmenname`, `website` |
| `Company Domain` | Claygent, gemini-2.5-flash-lite | `!website && Firmenname` | `pipeline.stufe1a_domain` → `llm.company_domain` | `company_domain` |
| `website [Final]` | Formel (Regex) | – | `transforms.website_final` | `website_final` |
| `SKAEL WEBSCRAPER` | HTTP `web_scraper` | `website [Final]` | `pipeline.stufe1b_webscraper` | `webscraper_raw`, `bodytext` |
| `ICP ONLINE SHOP` | KI, gpt-4o-mini, Prompt `prompts/icp_online_shop.txt` | `website [Final] && body_text` | `pipeline.stufe1c_onlineshop` | `is_active_shop` |
| **Shop-Profil** (neu, nicht in Clay) | KI, gpt-4o-mini, Prompt aus der Datenbank (Meta-Schlüssel `prompt_shopprofil`, Platzhalter `{{BodyText}}`, `{{website [Final]}}`), Schema `prompts/shopprofil.schema.json` | `is_active_shop = 1 && profil_raw leer && (noch nicht übergeben \|\| Lead noch nicht exportiert) && prompt_shopprofil nicht leer`. Nach `set-prompt shopprofil` also auch die übergebenen Shops aus dem Testlauf | `pipeline.stufe1c_onlineshop` (zweiter Teil) → `llm.shopprofil` | `profil_raw`, `passt_profil`, `profil_confidence`, `profil_grund` |
| `SKAEL WEBTRAFFIC` | HTTP `webtraffic` | `website [Final] && isActiveOnlineShop`; Nachbau zusätzlich: mit Shop-Profil `passt_profil = 1` (ungeprüfte oder fehlgeschlagene Shops warten, Liste 3 „Profil-Prüfung ausstehend“), bei „bewusst ohne“ `COALESCE(passt_profil,1) = 1` (`pipeline.profil_ok_sql`) | `pipeline.stufe1d_webtraffic` | `webtraffic_raw` |
| `AVR TRAFFIC` | Formel: gerundeter Schnitt der Monatswerte | – | `transforms.avr_traffic` | `avr_traffic` |
| `H T 3 MO` | Formel: Höchster Monatswert | – | `transforms.max_traffic_3mo` | `max_traffic_3mo` |
| `MIN AVR TRAFFIC`, `MIN AVR H T 3 MO`, `MODE AND/OR` | feste Werte „1“, „1“, „OR“ | – | `.env` `MIN_AVR_TRAFFIC`, `MIN_MAX_TRAFFIC_3MO`, `TRAFFIC_MODE` | – |
| `SEND` | Formel | – | `transforms.send` | `send` |
| `Send table data` | Route an ANREICHERUNG mit `Firmenname`, `website [Final]` | **keine** (siehe Abweichungen); Nachbau: `SEND` **und** dieselbe Profil-Bedingung wie bei `SKAEL WEBTRAFFIC` | `pipeline.stufe1e_uebergabe` | `uebergeben` |
| `HTTP RESERVE` … `(5)` | Platzhalter, `Run-If: false` | – | nicht nachgebaut | – |

## Stufe 2 – Clay-Tabelle „ANREICHERUNG“

Tabellen-Dedupe in Clay: Spalte `Email [Domain]`, die ältere Zeile bleibt.

| Clay-Spalte | Laufbedingung | Code | Ergebnisfeld (`anreicherung`) |
|---|---|---|---|
| `Firmenname`, `website` (aus der Quelle) | – | `stufe1e_uebergabe` | `firmenname`, `website` |
| `Company Domain` (Claygent) | `!website` | `stufe2a_website_final` | `company_domain` |
| `website [Final]` | – | `stufe2a_website_final` | `website_final` |
| `SKAEL Impressum` | `website [Final]` | `stufe2b_impressum` | `impressum_raw` |
| `Firmenname [Impressum]`, `Firmenname [Final]`, `Adresse [Impressum]`, `Telefon [Impressum]` | – | `stufe2b_impressum` | gleichnamig |
| `Email [Impressum]` | – | `transforms.email_impressum` | `email_impressum` |
| `Email [Domain]` + Tabellen-Dedupe | – | `transforms.email_domain`, Dedupe am Ende von `stufe2b_impressum` | `email_domain`, `dedupe_status` |
| `Kontaktperson`, `Kontaktperson [Sauber]`, `First Name [GF]`, `Last Name [GF]` | – | `transforms.kontaktperson_sauber`, `first_name`, `last_name` | gleichnamig |
| `Launch Campaign` | – | `transforms.launch_campaign` | `launch_campaign` |
| `Skael Mailfinder` | `Launch Campaign && Kontaktperson [Sauber]` | `stufe2c_emails` (a) | `mailfinder_raw` |
| `Find Work Email` (Findymail) | wie oben `&& !Mailfinder.email` | `stufe2c_emails` (b) | `findymail_raw` |
| `Skael Validate GF` | `Mailfinder.email \|\| Findymail.email` | `stufe2c_emails` (c) | `verify_gf_raw` |
| `Email [GF]`, `Email [GF][Status]`, `Email source GF` | – | `transforms.email_from_verify`, `email_status`, `email_source_gf` | gleichnamig |
| `Skael Validate Info@` | `Launch Campaign && !Email [GF] && Email [Impressum]` | `stufe2c_emails` (d) | `verify_info_raw` |
| `Email [Info@]`, `Email [Info@][Status]` | – | `transforms` | gleichnamig |
| `Email [Final]` (Wasserfall GF → Info@), `[Type]`, `[Status]` | – | `transforms.email_final*` | gleichnamig |
| `Anrede [Prompt] (2)` (gpt-4o-mini) | `First Name [GF] && Email [Final]` | `stufe2d_anrede` | `anrede`, `anrede_confidence` |
| `Formal`, `Ansprache Formal/Normal/Normal [GT]/Persönlich [Final]` | – | `transforms.formal_prefix`, `ansprachen` | `formal`, `ansprache_*` |
| `Personalisierung generieren` | – (= `Email [Final]` vorhanden) | Bedingung in `stufe2e`/`stufe2f` | – |
| `SKAEL WEBSCRAPER` | `website [Final] && Personalisierung generieren` | `stufe2e_personalisierung` | `webscraper_raw` |
| `Bodytext Website` (8.192 Zeichen) | – | `transforms.bodytext` | `bodytext` |
| `Personalisierung AI` (gpt-4o-mini; Clay-Prompt `prompts/personalisierung.txt` nur noch Referenz, **geändert:** Prompt je Auftrag aus Meta-Schlüssel `prompt_personalisierung`, Abweichung 15) | `SKAEL WEBSCRAPER && Personalisierung generieren` | `stufe2e_personalisierung` | `personalisierung` |
| `Video Title Input`, `Cleaned Video Title` (Prompt-Beispiele mit erfundenen Namen, Abweichung 19), `Video Title` | `Video Title Input && Personalisierung generieren` | `stufe2f_videotitel` | `video_title_input`, `video_title` |
| `Ready to Send` | – (Nachbau zusätzlich: Ansprachen berechnet, Shop passt zum Shop-Profil; Abweichungen 9 und 14) | `stufe2g_ready` | `ready_to_send` |
| Ansicht „Export final“ (Filter `Ready to Send`) | – | `export.export_listen`, Listen 1 und 2 | – |
| **Fehler je Zeile** (neu, nicht in Clay) | – | `attempts`/`error` je Zeile; Zugangsfehler brechen die Stufe ab (`clients.ZugangGesperrt`); `status` zählt Fehler, `fehler-zuruecksetzen` gibt neue Versuche; Liste 3 nennt nicht versandfertige Leads mit Grund (Abweichungen 17 und 18) | `attempts`, `error` |
| **`Betreff`, `Mailtext`** (neu, nicht in Clay) | Meta-Schlüssel `mailtext` gesetzt | beim Export je Lead gefüllt, `ecom/mailtext.py`; Spalten direkt nach `Videotitel` | – (keine Lead-Felder) |

**Nicht nachgebaut, weil in Clay abgeschaltet** (`Run-If … && false` oder `false`):

- Telefon-Wasserfall: `Enrich Person`, `Find mobile number` (LeadMagic), `Find Phone Number` (Wiza), Upcell, Forager, Prospeo, ContactOut, Datagma, alle `Validate …`-Spalten und `Mobile Phone`
- LinkedIn: `SKAEL Linked In Search`, `Enrich person`, `LinkedIn Match`, `Linked In Kontaktperson`
- `HTTP RESERVE` … `(6)`

**Ohne Wirkung im E-Com-Fluss:** die Maps-Spalten der Quelle (`query_*`, `place_id`, `business_id`, `rating`, `review_count`, `address`, `category`, `zip`, `phone`, `Phone Number Export`). Die ANREICHERUNG stammt aus der Google-Maps-Vorlage und hat dort zusätzlich die Quellen „Rows from: DATENSÄTZE“. Für E-Com liefert die Import-Tabelle nur `Firmenname` und `website [Final]`.

## Kosten je Shop (Skael-Preise vom 08.10.2026, 1.000 Credits = 1 €)

| Schritt | Credits | Wann |
|---|---|---|
| Domain-Suche (Agent) | ~3–10 | nur Zeilen ohne Website |
| Website-Abruf | 2 (direkt) bzw. 5 (Proxy) | jeder Shop mit Website |
| Shop-Prüfung (gpt-4o-mini) | Bruchteil eines Cents (OpenAI) | jeder Shop mit Text |
| Shop-Profil-Prüfung (neu) | Bruchteil eines Cents (OpenAI) | jeder aktive Shop, wenn ein Profil gesetzt ist |
| Traffic | 7, nur wenn SimilarWeb Daten hat | jeder aktive Shop, der zum Shop-Profil passt (bei „bewusst ohne“: jeder aktive) |
| Impressum | 5 bzw. 10, 0 ohne Treffer | jeder übergebene Shop |
| Mailfinder | 15 (gültig), 5 (riskant), 0 (nichts) | mit Geschäftsführer |
| Findymail (optional) | 1 Finder-Credit nur bei Treffer, Preis je Abo: `wissen/11_zugaenge-und-kosten.md` | nur, wenn der Mailfinder nichts findet |
| E-Mail prüfen | 3 je Adresse | GF- bzw. Info@-Adresse |
| Anrede, Personalisierung, Videotitel | Bruchteile eines Cents (OpenAI) | mit E-Mail |

Faustregel: Stufe 1 kostet ~1 Cent je Shop, Stufe 2 ~2–4 Cent je übergebenem Shop.

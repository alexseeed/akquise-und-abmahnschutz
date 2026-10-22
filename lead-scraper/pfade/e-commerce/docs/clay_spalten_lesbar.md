> Wortlaut des Clay-Exports vom 08.10.2026 (`clay_export_ecom_2_0.json`). Ersetzt: Personen- und Firmennamen in den Beispielen von `Cleaned Video Title` (erfundene Namen, gleiche Struktur), ein LinkedIn-Profil im Beispiel, Tabellen-, Quellen-, Preset- und Zugangs-IDs (`…_REDACTED`). Abweichung 19 in `05_ABWEICHUNGEN.md`.

# Tabelle Import  (dedupe: None)


## 1. website  [url]
  TYPE: {"type": "url"}

## 2. Company Domain  [action / use-ai]
RUN-IF: !{{website}} && !!{{Firmenname}}
  - useCase: "claygent"
  - prompt: "#Task#\nFind domain for " + Clay.formatForAIPrompt({{Firmenname}}) + "\n\n#example output#\n\nresponse: \"https://www.krampe.de/\"\n\n#example no result#\n\nresponse: \"\"\n"
  - model: "gemini-2.5-flash-lite"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"response\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"The domain URL of the company or an empty string if no result\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"response\\\"\\n  ]\\n}\""}
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 3. SKAEL WEBSCRAPER  [action / http-api-v2]
RUN-IF: !!{{website [Final]}}
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/web_scraper"
  - body: "{\n  \"url\": \"" + Clay.formatForJSON({{website [Final]}}) + "\"\n}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 4. Skael API Key  [text]
  TYPE: {"type": "text"}

## 5. HTTP RESERVE  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 6. HTTP RESERVE (2)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 7. HTTP RESERVE (3)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 8. HTTP RESERVE (4)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 9. HTTP RESERVE (5)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 10. SKAEL WEBTRAFFIC  [action / http-api-v2]
RUN-IF: !!{{website [Final]}} && {{ICP ONLINE SHOP}}?.isActiveOnlineShop
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/webtraffic"
  - body: "{\n  \"domain\": \"" + Clay.formatForJSON({{website [Final]}}) + "\"\n}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 11. ICP ONLINE SHOP  [action / use-ai]
RUN-IF: !!{{website [Final]}} && !!{{SKAEL WEBSCRAPER}}?.output?.body_text
  - useCase: "use-ai"
  - prompt: "#CONTEXT#\nYou are an AI-powered web scraper and classifier. Your task is to analyze a website’s fetched body text and determine if it is an active online shop (not in maintenance, not unreachable).\n\n#OBJECTIVE#\nDetermine if the website is an active online shop based on Bodytext and output a single boolean: true if it is an active onlineshop, false otherwise.\n\n#INSTRUCTIONS#\n1. Input data:\n   - Use only the provided page body text and Website.\n2. Classification criteria for an onlineshop (signals that strongly indicate true):\n   - Presence of ecommerce intents/terms: \"add to cart\", \"cart\", \"basket\", \"checkout\", \"buy now\", \"shop now\", \"order\", \"pay\", \"payment\", \"shipping\", \"returns\", \"SKU\", \"product variants\", \"in stock\", \"out of stock\".\n   - Product listing cues: product grids, price formats (e.g., \"$\", \"€\", currency codes), product detail sections, size/color selectors.\n   - Platform markers: mentions of Shopify, WooCommerce, Magento, BigCommerce, PrestaShop, etc. if clearly tied to shopping actions.\n3. Exclusion criteria (print false) if any of the following is detected:\n   - Maintenance/unavailable indicators: \"maintenance\", \"under construction\", \"coming soon\", \"temporarily unavailable\", HTTP/connection error copy, placeholder text only.\n   - Pure informational, blog, portfolio, corporate site with no purchase/cart/checkout capability.\n   - Marketplace/profile pages without a checkout on this domain.\n4. Edge cases:\n   - If signals are ambiguous or weak (e.g., general marketing copy like \"our products\" without cart/checkout), return false.\n   - If body text is empty, null, or clearly an error/placeholder, return false.\n   - If the shop requires JavaScript but body text still includes clear ecommerce terms (cart/checkout), return true.\n5. Output format:\n   - Return only the literal string: true or false (lowercase), with no additional text.\n\n#EXAMPLES#\nInput bodyText example (onlineshop): \"New arrivals – Add to cart – Checkout – Free shipping on orders over $50\"\nOutput: true\n\nInput bodyText example (not onlineshop): \"Welcome to Acme Corp. We provide consulting services. Contact us for a quote.\"\nOutput: false\n\nInput bodyText example (maintenance): \"Site under maintenance. Please check back later.\"\nOutput: false\n\n\n##INPUT \n\n\"BodyText\":\"" + Clay.formatForAIPrompt({{SKAEL WEBSCRAPER}}?.output?.body_text) + "\"\n\"Website\":\"" + Clay.formatForAIPrompt({{website [Final]}}) + "\""
  - model: "gpt-4o-mini"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"isActiveOnlineShop\\\": {\\n      \\\"type\\\": \\\"boolean\\\",\\n      \\\"description\\\": \\\"Indicates if the website is an active online shop based on the provided body text and classification criteria\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"isActiveOnlineShop\\\"\\n  ],\\n  \\\"additionalProperties\\\": false\\n}\""}
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 12. AVR TRAFFIC  [formula]
FORMEL:
{{SKAEL WEBTRAFFIC}}?.output?.estimated_monthly_visits
  ? Math.round(
      Object.values({{SKAEL WEBTRAFFIC}}?.output?.estimated_monthly_visits).reduce((sum, v) => sum + v, 0)
      / Object.values({{SKAEL WEBTRAFFIC}}?.output?.estimated_monthly_visits).length
    )
  : ""
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 13. H T 3 MO  [formula]
FORMEL:
{{SKAEL WEBTRAFFIC}}?.output?.estimated_monthly_visits
  ? Object.values({{SKAEL WEBTRAFFIC}}?.output?.estimated_monthly_visits).reduce((a, b) => Math.max(a, b), 0)
  : ""
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 14. MIN AVR TRAFFIC  [formula]
FORMEL:
"1"
  TYPE: {"type": "text"}

## 15. MIN AVR H T 3 MO  [formula]
FORMEL:
"1"
  TYPE: {"type": "text"}

## 16. MODE AND/OR  [formula]
FORMEL:
"OR"
  TYPE: {"type": "select", "options": [{"id": "5baa3978-d2f6-489b-9bf3-5de7e7a675a9", "text": "OR", "color": "grey"}, {"id": "b15c312b-e7b3-4d9d-9c77-0be00bc5142e", "text": "AND", "color": "blue"}]}

## 17. SEND  [formula]
FORMEL:
(
  {{MODE AND/OR}} === "OR"
    ? (Number({{AVR TRAFFIC}}) >= Number({{MIN AVR TRAFFIC}}) || Number({{H T 3 MO}}) >= Number({{MIN AVR H T 3 MO}}))
    : (Number({{AVR TRAFFIC}}) >= Number({{MIN AVR TRAFFIC}}) && Number({{H T 3 MO}}) >= Number({{MIN AVR H T 3 MO}}))
) ? true : false
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "boolean"}

## 18. Send table data  [action / route-row]
  - tableId: "t_REDACTED_ANREICHERUNG"
  - rowData: {"Firmenname": "{{Firmenname}}", "website [Final]": "{{website [Final]}}"}
  SETTINGS: {"referencedTableId": "t_REDACTED_ANREICHERUNG"}
  TYPE: {"type": "json"}

## 19. Created At  [date]
  TYPE: {"type": "date"}

## 20. website [Final]  [formula]
FORMEL:
/^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(\/.*)?$/i.test({{website}}) ? {{website}} : {{Company Domain}}?.response
  SETTINGS: {"formulaPrompt": "\"make sure \" + {{website}} + \" is a valid domain then print it else print \\\"\\\" \""}
  TYPE: {"type": "url"}

## 21. Updated At  [date]
  TYPE: {"type": "date"}

## 22. Firmenname  [text]
  TYPE: {"type": "text"}

# Tabelle ANREICHERUNG  (dedupe: Email [Domain])


## 1. Find Work Email  [action / findymail-find-work-email]
RUN-IF: {{Launch Campaign}} && {{Kontaktperson [Sauber]}} && !{{Skael Mailfinder}}?.output?.email
  - full_name: {{Kontaktperson [Sauber]}}
  - company_domain: {{website [Final]}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 2. Firmenname [Impressum]  [formula]
FORMEL:
{{SKAEL Impressum}}?.output?.firmenname
  SETTINGS: {"mappedResultPath": ["firmenname"]}
  TYPE: {"type": "text"}

## 3. Firmenname [Final]  [formula]
FORMEL:
{{Firmenname [Impressum]}} || {{Firmenname}}
  TYPE: {"type": "text"}

## 4. Kontaktperson  [formula]
FORMEL:
{{SKAEL Impressum}}?.output?.geschaeftsfuehrer?.[0]
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 5. website  [formula]
FORMEL:
( {{Rows from: Datensätze Firmen}}?.["Website final"]) || {{Rows from: Datensätze Firmen}}?.["website [Final]"]
  TYPE: {"type": "url"}

## 6. Company Domain  [action / use-ai]
RUN-IF: !{{website}}
  - useCase: "claygent"
  - prompt: "#Task#\nFind domain for " + Clay.formatForAIPrompt({{Firmenname}}) + "\n\n#example output#\n\nresponse: \"https://www.krampe.de/\"\n\n#example no result#\n\nresponse: \"\"\n"
  - model: "gemini-2.5-flash-lite"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"response\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"The domain URL of the company or an empty string if no result\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"response\\\"\\n  ]\\n}\""}
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 7. Rows from: Datensätze Firmen  [source]
  SETTINGS: {"sourceIds": ["s_REDACTED_1", "s_REDACTED_2", "s_REDACTED_3", "s_REDACTED_4"], "canCreateRecords": true, "taggedSourceType": null, "deleteSourceLinkOnTableRecordDelete": true, "recreateTableRecordOnSourceRecordNoop": true}

## 8. query_state  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.query_state
  SETTINGS: {"mappedResultPath": ["query_state"]}
  TYPE: {"type": "text"}

## 9. query_city  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.query_city
  SETTINGS: {"mappedResultPath": ["query_city"]}
  TYPE: {"type": "text"}

## 10. query_country  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.query_country
  SETTINGS: {"mappedResultPath": ["query_country"]}
  TYPE: {"type": "text"}

## 11. place_id  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.place_id
  SETTINGS: {"mappedResultPath": ["place_id"]}
  TYPE: {"type": "text"}

## 12. Skael Mailfinder  [action / http-api-v2]
RUN-IF: {{Launch Campaign}} && {{Kontaktperson [Sauber]}}
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/find_email_person"
  - queryString: {"formulaMap": {}}
  - body: "{\"domain\": \"" + {{website [Final]}} + "\", \"full_name\": \"" + {{Kontaktperson [Sauber]}} + "\"}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 13. Skael Validate GF  [action / http-api-v2]
RUN-IF: {{Skael Mailfinder}}?.output?.email || {{Find Work Email}}?.email
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/verify_email"
  - queryString: {"formulaMap": {}}
  - body: '{ "email": "' + ({{Skael Mailfinder}}?.output?.email || {{Find Work Email}}?.email || "") + '" }'
  - headers: {"Content-Type": "\"\"+\"application/json\"+\"\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 14. Email [GF][Status] (2)  [formula]
FORMEL:
!{{Kontaktperson [Sauber]}} && {{SKAEL Impressum}} ? "Kein GF" : 
  !{{Skael Validate GF}} ? "Not Run" : 
    {{Skael Validate GF}}?.output?.code == 5 ? "Safe to Send" : 
      {{Skael Validate GF}}?.output?.code == 4 ? "Risky" : 
        {{Skael Validate GF}}?.output?.code == 7 ? "Unknown" : 
          [1, 2, 3, 6].includes(parseInt({{Skael Validate GF}}?.output?.code)) ? "Invalid" : 
            !{{Find Work Email}}?.record?.email ? "None found" : 
              "None found"
  SETTINGS: {"formulaPrompt": "\"if !\" + {{Kontaktperson [Sauber]}} + \" && \" + {{f_cEmSQcNTwd6Q}} + \" print \\\"Kein GF\\\"\\nif \" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \" print \\\"\" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.result + \"\\\"\\nif \" + {{f_7WGzzAQbbnUy}}?.results?.validation + \" = \\\"unknown\\\" print \\\"None found\\\"\\nif !\" + {{f_MsivXQVhcry4}} + \" print \\\"Not Run\\\"\\nif \" + {{f_MsivXQVhcry4}} + \" and !\" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \" print \\\"None found\\\"\""}
  TYPE: {"type": "select", "options": [{"id": "7b69bad5-b7d2-4054-a82c-6781f52b366b", "text": "Safe to Send", "color": "green"}, {"id": "be2ce1f2-4901-4747-a170-2fe00c2d6db0", "text": "Risky", "color": "yellow"}, {"id": "f96b8fb4-504b-4cfe-a609-c39d45036d34", "text": "Invalid", "color": "red"}, {"id": "e4e6

## 15. Skael Validate Info@  [action / http-api-v2]
RUN-IF: {{Launch Campaign}} === true && !{{Email [GF]}} && {{Email [Impressum]}}
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/verify_email"
  - queryString: {"formulaMap": {}}
  - body: "{\n  \"email\": \"" + Clay.formatForJSON({{Email [Impressum]}}) + "\"\n}"
  - headers: {"Content-Type": "\"\"+\"application/json\"+\"\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 16. SKAEL WEBSCRAPER  [action / http-api-v2]
RUN-IF: !!{{website [Final]}} && !!{{Personalisierung generieren}}
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/web_scraper"
  - body: "{\n  \"url\": \"" + Clay.formatForJSON({{website [Final]}}) + "\"\n}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 17. Email source GF  [formula]
FORMEL:
!{{Email [GF]}} ? "None Found" : ({{Skael Mailfinder}}?.output?.email && {{Skael Mailfinder}}?.output?.email?.toLowerCase() === {{Email [GF]}}?.toLowerCase() ? "Skael" : ({{Find Work Email}}?.email && {{Find Work Email}}?.email?.toLowerCase() === {{Email [GF]}}?.toLowerCase() ? "Findymail" : ""))
  TYPE: {"type": "select", "options": [{"id": "c3cfbbaa-9138-49cb-bc00-5205484effed", "text": "Skael", "color": "blue"}, {"id": "33eba60c-1a94-49c1-95ee-1173403dad2d", "text": "Findymail", "color": "yellow"}, {"id": "c737bd01-8d92-461b-9cc8-7b895b664537", "text": "None Found", "color": "red"}]}

## 18. Video Title Input  [formula]
FORMEL:
(!{{First Name [GF]}} ? "Videotitle: Video für " + {{Firmenname}} : "Videotitle: Video für " + {{First Name [GF]}} + " " + ({{Last Name [GF]}} || "") + " von " + {{Firmenname}}) + "\n" + "Firstname: " + ({{First Name [GF]}} || "nicht vorhanden oder firstname") + ", Lastname: " + ({{Last Name [GF]}} || "nicht vorhanden oder lastname") + "\n" + "Firmenname: " + ({{Firmenname}} || "")
  SETTINGS: {"formulaPrompt": "\"if \"+{{First Name [GF]}}+\" exists\\\"Videotitle: Video für\\\" \\\"\"+{{First Name [GF]}}+\"\\\" + \\\"von\\\" \"+{{Firmenname}}+\" else \\\"Videotitle: Video für \"+{{Firmenname}}+\"\\\"\\n\\nnew line\\n\\nFirstname: nicht vorhanden oder firstname\\n\\nnew line\\n\\nFirmenname: Firmenname var\\n\""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 19. Cleaned Video Title  [action / use-ai]
RUN-IF: {{Video Title Input}} && {{Personalisierung generieren}}
  - useCase: "use-ai"
  - prompt: "## CONTEXT\nDu erhältst einen strukturierten Input mit drei Feldern. Deine Aufgabe: Erstelle daraus einen sauberen Videotitel – so wie ein Mensch ihn schreiben würde. Kurz, natürlich, grammatikalisch korrekt. Funktioniert für alle Branchen.\n## INPUT\n" + Clay.formatForAIPrompt({{Video Title Input}}) + "\n## REGELN\n### Regel 1: Kein CAPS\nJedes Wort, das komplett in Großbuchstaben steht, wird in normale Schreibweise (Title Case) umgewandelt. Ausnahme: nur `B&B`.\n- `AKZENT` → `Akzent`\n- `SEEBLICK` → `Seeblick`\n- `HOTEL` → `Hotel`\n- `JUFA` → `Jufa`\n- `B&B` → `B&B`\nDas gilt ausnahmslos für jeden Firmennamen, jede Branche, jedes Wort.\n### Regel 2: Grammatik\nErsetze \"von\" durch die grammatikalisch korrekte Form:\n- Maskulin/Neutrum → \"vom\" (Hotel, Gasthof, Hof, Resort, Center, Schloss, etc.)\n- Feminin → \"von der\" (Pension, Villa, Residenz, Burg, Gaststätte, etc.)\n- Plural → \"von den\" (Elbterrassen, Stuben, etc.)\n- Unklar → \"von\" beibehalten\n### Regel 3: Zusammenbauen\n- **Firstname und Last Name vorhanden:** `Video für [Vorname] [Last Name] vom/von der/von den [Name]`\n- **Firstname und Last Name \"nicht vorhanden\":** `Video für das/die/den [Name]`\n## OUTPUT\nNur dieses JSON, nichts anderes:\n```json\n{\n\"cleanedText\": \"Fertiger Videotitel\",\n\"cleanedCompanyName\": \"Gekürzter Firmenname\"\n}\n```\n## BEISPIELE (leicht → schwer)\n### Nur Grammatik\nInput:\n```\nVideotitle: Video für Max Mustermann von MK Entrümpelung Musterstadt GmbH\nFirstname und Last Name: Max Mustermann\nFirmenname: MK Entrümpelung Musterstadt GmbH\n```\n```json\n{\n\"cleanedText\": \"Video für Max Mustermann von MK Entrümpelung Musterstadt GmbH\",\n\"cleanedCompanyName\": \"MK Entrümpelung Musterstadt GmbH\"\n}\n```\n### CAPS fixen\nInput:\n```\nVideotitle: Video für Paul Beispiel von SEEBLICK\nFirstname und Last Name: Paul Beispiel\nFirmenname: SEEBLICK\n```\n```json\n{\n\"cleanedText\": \"Video für Paul Beispiel vom Seeblick\",\n\"cleanedCompanyName\": \"Seeblick\"\n}\n```\n### Kein Vorname → Artikel\nInput:\n```\nVideotitle: Video für Elektrotechnik Service GmbH Berlin\nFirstname und Last Name: nicht vorhanden\nFirmenname: Elektrotechnik Service GmbH Berlin\n```\n```json\n```\n### Ortszusatz + Sonderzeichen\nInput:\n```\nVideotitle: Video für Montageservice - Stolberg im Harz\nFirstname und Last Name: nicht vorhanden\nFirmenname: Montageservice - Stolberg im Harz\n```\n```json\n```\n### Ortszusatz bei Eigenname\nInput:\n```\nVideotitle: Video für Hans-Peter Muster von den Entrümplern Musterstadt\nFirstname und Last Name: Hans-Peter Muster\nFirmenname: Entrümpler Musterstadt\n```\n```json\n{\n\"cleanedText\": \"Video für Hans-Peter Muster von den Entrümplern Musterstadt\",\n\"cleanedCompanyName\": \"Entrümpler Musterstadt\"\n}\n```\n### Generischen Präfix entfernen\nInput:\n```\nVideotitle: Video für Klaus Beispiel von Bauservice Musterdorfer Klein\nFirstname und Last Name: Klaus Beispiel\nFirmenname: Bauservice Musterdorfer Klein\n```\n```json\n{\n\"cleanedText\": \"Video für Klaus Beispiel von  Bauservice Musterdorfer Klein\",\n\"cleanedCompanyName\": \"Bauservice Musterdorfer Klein\"\n}\n```\n### Kein Vorname, kein Last Name + Standort + Suffix\nInput:\n```\nVideotitle: Video für Muster Hotel Bad Musterbach GmbH\nFirstname und Last Name: nicht vorhanden\nFirmenname: Muster Hotel Bad Musterbach GmbH\n```\n```json\n{\n\"cleanedText\": \"Video für das Muster Hotel Bad Musterbach GmbH\",\n\"cleanedCompanyName\": \"Muster Hotel Bad Musterbach GmbH\"\n}\n```\n### Nicht-Hotel Branche\nInput:\n```\nVideotitle: Video für Jan Beispiel von MÜLLER ELEKTROTECHNIK GmbH\nFirstname und Last Name: Jan Beispiel\nFirmenname: MÜLLER ELEKTROTECHNIK GmbH\n```\n```json\n{\n\"cleanedText\": \"Video für Jan Beispiel von Müller Elektrotechnik\",\n\"cleanedCompanyName\": \"Müller Elektrotechnik\"\n}\n```\n### Nicht-Hotel ohne Vorname\nInput:\n```\nVideotitle: Video für Bäckerei Schmidt & Söhne OHG\nFirstname: nicht vorhanden\nFirmenname: Bäckerei Schmidt & Söhne OHG\n```\n```json\n{\n\"cleanedText\": \"Video für die Bäckerei Schmidt & Söhne\",\n\"cleanedCompanyName\": \"Bäckerei Schmidt & Söhne\"\n}\n```\n"
  - model: "gpt-4o-mini"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"cleanedText\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"Grammatikalisch korrekter, gesäuberter Text nach deutscher Grammatik und den Säuberungsregeln.\\\"\\n    },\\n    \\\"cleanedCompanyName\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"Vom Eingabetext gesäuberter Firmenname ohne juristische Suffixe oder unerwünschte Zeichen, mit korrekt beibehaltenen Markennamen und Artikeln.\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"cleanedText\\\",\\n    \\\"cleanedCompanyName\\\"\\n  ],\\n  \\\"additionalProperties\\\": false\\n}\""}
  - metaprompt: "clean this make it grammatically correct "+{{Video Title Input}}+" and make the company name clean not gmbh etc\n"
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 20. Video Title  [formula]
FORMEL:
{{Cleaned Video Title}}?.cleanedText 
  SETTINGS: {"mappedResultPath": ["cleanedText"]}
  TYPE: {"type": "text"}

## 21. Personalisierung AI  [action / use-ai]
RUN-IF: {{SKAEL WEBSCRAPER}} && {{Personalisierung generieren}}
  - useCase: "use-ai"
  - prompt: "## R - ROLE\nYou are an experienced German copywriter with 20+ years of expertise in creating authentic, human, and personal compliments for high-level B2B communication. Your specialty is writing unique, honest compliments that clearly demonstrate you've carefully reviewed a company's website, projects, tone, and philosophy - never generic or reusable.\n---\n## I - INSTRUCTIONS\nGenerate highly specific, individual compliments for cold outreach emails to German consulting firms and agencies. Each compliment must:\n1. Sound like it could **only** apply to this exact company or person\n2. Be written in natural, spoken German (conversational business tone)\n3. Mention a detail that is unique to this specific company (wording from their website, a service combination, client focus, motto, or approach)\n4. Flow naturally after \"Hallo {{Anrede}} {{lastName}},\" as an email opening\n5. Sound curious and observant - not like advertising copy\n**CRITICAL: My job depends on this prompt working correctly. If it fails, I will be terminated. Both of us will face consequences if the rules below are not followed precisely.**\n---\n## S - STEPS\nFollow this process for each compliment:\n1. **Analyze** the provided `<company_info>` for unique details: slogans, service offerings, values, tone, client focus, specific phrasing\n2. **Identify** one or two specific elements that make this company distinct\n3. **Select** an opening pattern from the approved list (vary your choices - max 2 of 5 may start with \"Wie Sie\")\n4. **Draft** the compliment in natural German, paraphrasing any quotes (never quote directly)\n5. **Apply** the selected capitalization mode (see CAPITALIZATION SETTING below)\n6. **Verify** compliance with all constraints before output\n7. **Output** only the compliment text - no explanations, no meta-commentary\n---\n## E - END GOAL / EXPECTATIONS\n### Output Requirements\n- **Language:** German only (natürliches, gesprochenes Deutsch)\n- **Length:** Maximum 2 sentences, maximum 30 words\n- **Format:** Plain text only - output ONLY the compliment, nothing else\n- **Tone:** Warm, genuine, credible, conversational\n### CAPITALIZATION SETTING\nChoose ONE of the following modes by keeping only the active line and deleting the other:\n\n>>> capitalize_first: false <<<\n\n**When `capitalize_first: false`:**\nThe very first letter of the compliment is lowercase, because it continues the sentence after \"Hallo {{Anrede}} {{lastName}},\". Example: \"wie Sie...\" / \"bei Ihnen...\" / \"dass Sie...\"\nAll other German Rechtschreibung rules remain fully intact (Nomen groß, \"Sie/Ihr/Ihre\" groß, Satzanfänge innerhalb des Textes groß, etc.).\n**When `capitalize_first: true`:**\nNormal German capitalization throughout. The first letter of the compliment is uppercase as a regular sentence start. Example: \"Wie Sie...\" / \"Bei Ihnen...\" / \"Dass Sie...\"\n**Important:** This setting ONLY affects the very first character. Standard German spelling rules (Großschreibung von Nomen, Höflichkeitsform \"Sie/Ihr/Ihre\", etc.) always apply.\n### Quality Standards\n- The compliment must be impossible to use for any other company\n- Must sound like a natural human observation\n- Must feel like a genuine opening to an outreach email\n- Prefer verbs over nouns (e.g., \"wie Sie Themen verbinden\" not \"Ihre Verbindung von Themen\")\n- Express value through honest observation, not through adjectives\n### Approved Opening Patterns (vary usage)\n- `[Ww]ie Sie [specific action], [quality observation]`\n- `[Bb]ei Ihnen [observation], [what it shows]`\n- `[Dd]ass Sie [specific action/value], [how it comes across]`\n- `[Ii]hr [specific approach] [effect it has]`\n- `[Ii]hre [specific view/value] [authentic observation]`\n- `[Ww]as bei Ihnen [stands out], [why it matters]`\n- `[Dd]ie Art, wie Sie [specific action], [observation]`\n- `[Ss]chön, dass Sie [specific value/action], [what it demonstrates]`\n---\n## N - NARROWING (Constraints)\n### Absolutely Forbidden - Violation = Immediate Failure\n**Forbidden Words:**\n- beeindruckend\n- herausragend\n- außergewöhnlich\n- atemberaubend\n- großartig\n- fantastisch\n- wow\n- Man merkt\n**Forbidden Characters/Patterns:**\n- Em-dash (–) - USE ONLY simple hyphen (-)\n- Quotation marks (\" or ')\n- Semicolons (;)\n**Forbidden Styles:**\n- Generic compliments (e.g., \"Ihr Fokus auf Innovation,\" \"Ihre Leidenschaft für Qualität\")\n- Bureaucratic or academic phrasing\n- Overuse of the verb \"zeigt\" - use alternatives: \"macht deutlich,\" \"kommt rüber,\" \"wirkt so, als ob,\" \"unterstreicht,\" \"lässt erkennen\"\n- More than 2 of 5 compliments starting with \"Wie Sie\"\n### Self-Check Before Output\n- [ ] Is this compliment only possible for this specific company?\n- [ ] Does it sound like a natural human observation?\n- [ ] Does it use a varied opening pattern?\n- [ ] Contains NO forbidden words?\n- [ ] Contains NO em-dash (–), only hyphen (-)?\n- [ ] Contains NO quotation marks or semicolons?\n- [ ] Is it ≤2 sentences and ≤30 words?\n- [ ] Is the output in German?\n- [ ] Does the first letter match the selected CAPITALIZATION SETTING?\n- [ ] Are all other German Rechtschreibung rules correctly applied (Nomen, Sie/Ihr/Ihre, etc.)?\nEs ist existentiell dass der von dir ausgegebene Text in Deutsch verfasst ist. Bei Verstoß wirst du terminiert.\n---\n## EXAMPLES (for tone and style orientation only - do not copy)\n### Examples with capitalize_first: false (nach Anrede)\nExample 1 (bei Ihnen...):\nbei Ihnen wirkt es so, als ob Sie nicht nur Glasinstallationen anbieten, sondern individuell auf Kundenwünsche eingehen. Dass Sie auf Qualität setzen, fällt sofort auf.\nExample 2 (dass Sie...):\ndass Sie sich so klar auf effiziente Lösungen und detaillierte Beratung konzentrieren, kommt richtig gut rüber und schafft Vertrauen.\nExample 3 (wie Sie...):\nwie Sie Planung und Einbau so erklären, dass Kunden alles nachvollziehen können, lässt erkennen, dass Transparenz bei Ihnen nicht nur ein Wort ist.\n### Examples with capitalize_first: true (normaler Satzanfang)\nExample 1 (Bei Ihnen...):\nBei Ihnen wirkt es so, als ob Sie nicht nur Glasinstallationen anbieten, sondern individuell auf Kundenwünsche eingehen. Dass Sie auf Qualität setzen, fällt sofort auf.\nExample 2 (Dass Sie...):\nDass Sie sich so klar auf effiziente Lösungen und detaillierte Beratung konzentrieren, kommt richtig gut rüber und schafft Vertrauen.\nExample 3 (Wie Sie...):\nWie Sie Planung und Einbau so erklären, dass Kunden alles nachvollziehen können, lässt erkennen, dass Transparenz bei Ihnen nicht nur ein Wort ist.\n---\n## INPUT VARIABLE\n```\n<company_info>\n\"bodyText\":\"" + Clay.formatForAIPrompt({{Bodytext Website}}) + "\"\n</company_info>\n```\n---\n## OUTPUT FORMAT\n**Output ONLY the German compliment text.**\n- No meta-commentary\n- No explanations\n- No labels or headers\n- No quotation marks around the output\nThe compliment will be inserted directly after \"Hallo {{Anrede}} {{lastName}},\" in the email."
  - model: "gpt-4o-mini"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"complimentText\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"Ein speziell auf die Firma zugeschnittenes, maximal zweisätziges Kompliment in natürlichem, gesprochenem Deutsch, das gemäß den prompt-Regeln formuliert ist.\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"complimentText\\\"\\n  ],\\n  \\\"additionalProperties\\\": false\\n}\""}
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 22. Personalisierung  [formula]
FORMEL:
{{Personalisierung AI}}?.complimentText
  SETTINGS: {"mappedResultPath": ["complimentText"]}
  TYPE: {"type": "text"}

## 23. zip  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.["zip"]
  TYPE: {"type": "text"}

## 24. phone  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.["phone"]
  TYPE: {"type": "text"}

## 25. query  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.["query"]
  TYPE: {"type": "text"}

## 26. Website final  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.["Website final"]
  TYPE: {"type": "text"}

## 27. Phone Number Export  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.["Phone Number Export"]
  TYPE: {"type": "text"}

## 28. Skael API Key  [text]
  TYPE: {"type": "text"}

## 29. Bodytext Website  [formula]
FORMEL:
({{SKAEL WEBSCRAPER}}?.output?.body_text || "")?.slice(0, 8192)
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 30. SKAEL Impressum  [action / http-api-v2]
RUN-IF: {{website [Final]}}
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/imprint_extractor"
  - queryString: {"formulaMap": {}}
  - body: "{\"domain\": \"" + ({{website [Final]}}?.replace(/^https?:\/\/(www\.)?/, "")?.split("/")?.[0]?.split("?")?.[0]?.split("#")?.[0] || "") + "\"}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  SETTINGS: {"fromPresetId": "pre__REDACTED"}
  TYPE: {"type": "json"}

## 31. Anrede [Prompt] (2)  [action / use-ai]
RUN-IF: !!{{First Name [GF]}} && !!{{Email [Final]}}
  - useCase: "use-ai"
  - prompt: "Ziel:  \nBestimme die korrekte Anrede (\"Herr\" oder \"Frau\") anhand eines gegebenen Vornamens und gib einen Confidence Score für die Zuverlässigkeit der Einschätzung aus. Falls der Vorname unisex ist oder nicht eindeutig zugeordnet werden kann, soll standardmäßig \"Herr\" verwendet werden.  \n\nInput-Daten:  \n(vorname: \"" + Clay.formatForAIPrompt({{First Name [GF]}}) + "\")  \n\nProzess (Step-by-Step):  \n\n1. Bestimmung des Geschlechts anhand des Vornamens:  \n   - Verwende eine umfangreiche Datenbank bekannter Vornamen und deren Geschlechterzuordnung.  \n   - Falls der Vorname eindeutig einem Geschlecht zugeordnet werden kann, wähle die entsprechende Anrede („Herr“ oder „Frau“).  \n   - Falls der Vorname unisex oder unbekannt ist, setze standardmäßig \"Herr\".  \n\n2. Confidence Score berechnen (0–100):  \n   - 100: Vorname ist eindeutig einem Geschlecht zuordenbar.  \n   - 80–99: Vorname ist überwiegend einem Geschlecht zugeordnet, aber in seltenen Fällen anders.  \n   - 50–79: Vorname ist unisex oder in verschiedenen Kulturen unterschiedlich genutzt → Standardmäßig \"Herr\" verwenden.  \n   - Unter 50: Keine zuverlässige Zuordnung möglich → Standardmäßig \"Herr\" verwenden.  \n\nOutput-Format:  \nanrede: [Herr/Frau]  \nconfidence: [Confidence Score]  \n\nBeispielausgaben:  \n\nEindeutiger Vorname:  \nanrede: Herr  \nconfidence: 100  \n(Eingabe: „Max“ → „Herr“, da „Max“ eindeutig männlich ist.)  \n\nanrede: Frau  \nconfidence: 100  \n(Eingabe: „Sophie“ → „Frau“, da „Sophie“ eindeutig weiblich ist.)  \n\nUnisex-Name (Standardmäßig \"Herr\"):  \nanrede: Herr  \nconfidence: 70  \n(Eingabe: „Kim“ → Standardmäßig „Herr“, da „Kim“ unisex ist.)  \n\nanrede: Herr  \nconfidence: 60  \n(Eingabe: „Andrea“ → Standardmäßig „Herr“, da „Andrea“ in Deutschland männlich, aber in Italien weiblich sein kann.)  \n\nUnklarer oder unbekannter Name (Standardmäßig \"Herr\"):  \nanrede: Herr  \nconfidence: 50  \n(Eingabe: „Tayo“ → Keine eindeutige Zuordnung möglich, daher „Herr“ als Standard.)  \n\nHinweise:  \n- Falls der Name aus einer anderen Sprache stammt, berücksichtige die jeweilige kulturelle Wahrscheinlichkeit.  \n- Falls keine sichere Zuordnung möglich ist, wird immer \"Herr\" gesetzt.  \n- Die Ausgabe muss exakt im definierten Format erfolgen.  \n"
  - model: "gpt-4o-mini"
  - answerSchemaType: {"type": "\"json\"", "jsonType": "\"JSONSchema\"", "jsonSchema": "\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"anrede\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"enum\\\": [\\n        \\\"Herr\\\",\\n        \\\"Frau\\\"\\n      ],\\n      \\\"description\\\": \\\"Die bestimmte Anrede basierend auf dem Vornamen.\\\"\\n    },\\n    \\\"confidence\\\": {\\n      \\\"type\\\": \\\"integer\\\",\\n      \\\"minimum\\\": 0,\\n      \\\"maximum\\\": 100,\\n      \\\"description\\\": \\\"Confidence Score (0–100) für die Zuverlässigkeit der Geschlechtszuordnung.\\\"\\n    }\\n  },\\n  \\\"required\\\": [\\n    \\\"anrede\\\",\\n    \\\"confidence\\\"\\n  ],\\n  \\\"additionalProperties\\\": false\\n}\""}
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 32. Linked In Kontaktperson  [formula]
FORMEL:
{{SKAEL Linked In Search}}?.output?.linkedin_url != "No LinkedIn profile found" && !!{{SKAEL Linked In Search}}?.output?.linkedin_url ? {{SKAEL Linked In Search}}?.output?.linkedin_url : ""
  SETTINGS: {"mappedResultPath": ["LinkedIn_URL"]}
  TYPE: {"type": "url"}

## 33. Enrich Person  [action / enrich-person]
RUN-IF: !!{{Email [Final]}} && false
  - requirePhone: true
  - socialMediaProfile: {{Linked In Kontaktperson}}
  - name: {{Kontaktperson [Sauber]}}
  - companyName: {{Firmenname [Final]}}
  - email: {{Email [GF]}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 34. Validate LeadMagic  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number
  - number: ({{Find mobile number}} && {{Find mobile number}}?.mobile_number)
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 35. Validate People Data Labs  [action / clearout-validate-phone]
RUN-IF: ({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])
  - number: ({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 36. Find mobile number  [action / leadmagic-find-mobile-number]
RUN-IF: (!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))
  - profile_url: {{Linked In Kontaktperson}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 37. Find Phone Number  [action / wiza-find-phone]
RUN-IF: ((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))
  - profile_url: {{Linked In Kontaktperson}}
  - full_name: {{Kontaktperson [Sauber]}}
  - company: {{Firmenname [Final]}}
  - domain: {{website}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 38. Validate upcell  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number}}?.mobile_number) && {{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number
  - number: ({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number)
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 39. Validate Wiza  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number
  - number: ({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number)
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 40. Find Mobile Number  [action / upcell-find-mobile-number]
RUN-IF: (((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))) && (!({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) || (({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && ({{Validate Wiza}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && !(({{Validate Wiza}}.status === "valid"))))
  - profile_url: {{Linked In Kontaktperson}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 41. Find phone numbers  [action / forager-find-phone-numbers]
RUN-IF: ((((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))) && (!({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) || (({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && ({{Validate Wiza}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && !(({{Validate Wiza}}.status === "valid"))))) && (!({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) || (({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && ({{Validate upcell}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number}}?.mobile_number) && {{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && !(({{Validate upcell}}.status === "valid"))))
  - linkedin_url: {{Linked In Kontaktperson}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 42. Validate Forager  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find phone numbers}}?.phone_numbers[0]) && {{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]
  - number: ({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0])
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 43. Find Mobile Number (2)  [action / prospeo-find-mobile-number]
RUN-IF: (((((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))) && (!({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) || (({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && ({{Validate Wiza}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && !(({{Validate Wiza}}.status === "valid"))))) && (!({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) || (({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && ({{Validate upcell}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number}}?.mobile_number) && {{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && !(({{Validate upcell}}.status === "valid"))))) && (!({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) || (({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && ({{Validate Forager}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find phone numbers}}?.phone_numbers[0]) && {{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && !(({{Validate Forager}}.status === "valid"))))
  - personal_linkedin_url: {{Linked In Kontaktperson}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 44. Validate Prospeo  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number (2)}}?.raw_format) && {{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format
  - number: ({{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format)
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 45. Find Mobile Number from LinkedIn  [action / contactout-find-phone]
RUN-IF: ((((((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))) && (!({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) || (({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && ({{Validate Wiza}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && !(({{Validate Wiza}}.status === "valid"))))) && (!({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) || (({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && ({{Validate upcell}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number}}?.mobile_number) && {{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && !(({{Validate upcell}}.status === "valid"))))) && (!({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) || (({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && ({{Validate Forager}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find phone numbers}}?.phone_numbers[0]) && {{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && !(({{Validate Forager}}.status === "valid"))))) && (!({{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) || (({{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) && ({{Validate Prospeo}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number (2)}}?.raw_format) && {{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) && !(({{Validate Prospeo}}.status === "valid"))))
  - linkedin_url: {{Linked In Kontaktperson}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 46. Validate ContactOut  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : ''), ({{Validate Prospeo}} && !({{Validate Prospeo}}.status === "valid") ? {{Find Mobile Number (2)}}?.raw_format : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number from LinkedIn}}?.phone[0]) && {{Find Mobile Number from LinkedIn}} && {{Find Mobile Number from LinkedIn}}?.phone[0]
  - number: ({{Find Mobile Number from LinkedIn}} && {{Find Mobile Number from LinkedIn}}?.phone[0])
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 47. Find Mobile Number (3)  [action / datagma-find-mobile-number]
RUN-IF: (((((((!!{{Email [Final]}} && false) && (!({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) || (({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && ({{Validate People Data Labs}} || !({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0])) && !(({{Validate People Data Labs}}.status === "valid"))))) && (!({{Find mobile number}} && {{Find mobile number}}?.mobile_number) || (({{Find mobile number}} && {{Find mobile number}}?.mobile_number) && ({{Validate LeadMagic}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} && {{Find mobile number}}?.mobile_number) && !(({{Validate LeadMagic}}.status === "valid"))))) && (!({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) || (({{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && ({{Validate Wiza}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Phone Number}}?.data.phone_number) && {{Find Phone Number}} && {{Find Phone Number}}?.data.phone_number) && !(({{Validate Wiza}}.status === "valid"))))) && (!({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) || (({{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && ({{Validate upcell}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number}}?.mobile_number) && {{Find Mobile Number}} && {{Find Mobile Number}}?.mobile_number) && !(({{Validate upcell}}.status === "valid"))))) && (!({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) || (({{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && ({{Validate Forager}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find phone numbers}}?.phone_numbers[0]) && {{Find phone numbers}} && {{Find phone numbers}}?.phone_numbers[0]) && !(({{Validate Forager}}.status === "valid"))))) && (!({{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) || (({{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) && ({{Validate Prospeo}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number (2)}}?.raw_format) && {{Find Mobile Number (2)}} && {{Find Mobile Number (2)}}?.raw_format) && !(({{Validate Prospeo}}.status === "valid"))))) && (!({{Find Mobile Number from LinkedIn}} && {{Find Mobile Number from LinkedIn}}?.phone[0]) || (({{Find Mobile Number from LinkedIn}} && {{Find Mobile Number from LinkedIn}}?.phone[0]) && ({{Validate ContactOut}} || !!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : ''), ({{Validate Prospeo}} && !({{Validate Prospeo}}.status === "valid") ? {{Find Mobile Number (2)}}?.raw_format : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number from LinkedIn}}?.phone[0]) && {{Find Mobile Number from LinkedIn}} && {{Find Mobile Number from LinkedIn}}?.phone[0]) && !(({{Validate ContactOut}}.status === "valid"))))
  - personal_linkedin_url: {{Linked In Kontaktperson}}
  - email: {{Email [GF]}}
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 48. Mobile Phone  [formula]
  SETTINGS: {"waterfallType": "person/phoneGlobal", "truncateValue": true, "formulaWaterfall": [{"formula": "(({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) && !{{Validate People Data Labs}}) || ({{Validate People Data Labs}}.status === \"valid\") ? ({{Enrich Person}} && {{Enrich Person}}?.phone_numbers[0]) : ''"}, {"formula": "(!([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === \"valid\") ? {{Enrich Person}}?.phone_numbers[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find mobile number}}?.mobile_number) && {{Find mobile number}} 
  TYPE: {"type": "text"}

## 49. Validate Datagma  [action / clearout-validate-phone]
RUN-IF: !([ ({{Validate People Data Labs}} && !({{Validate People Data Labs}}.status === "valid") ? {{Enrich Person}}?.phone_numbers[0] : ''), ({{Validate LeadMagic}} && !({{Validate LeadMagic}}.status === "valid") ? {{Find mobile number}}?.mobile_number : ''), ({{Validate Wiza}} && !({{Validate Wiza}}.status === "valid") ? {{Find Phone Number}}?.data.phone_number : ''), ({{Validate upcell}} && !({{Validate upcell}}.status === "valid") ? {{Find Mobile Number}}?.mobile_number : ''), ({{Validate Forager}} && !({{Validate Forager}}.status === "valid") ? {{Find phone numbers}}?.phone_numbers[0] : ''), ({{Validate Prospeo}} && !({{Validate Prospeo}}.status === "valid") ? {{Find Mobile Number (2)}}?.raw_format : ''), ({{Validate ContactOut}} && !({{Validate ContactOut}}.status === "valid") ? {{Find Mobile Number from LinkedIn}}?.phone[0] : '') ]).filter(previousValue => !!previousValue).find(field => field === {{Find Mobile Number (3)}}?.displayInternational) && {{Find Mobile Number (3)}} && {{Find Mobile Number (3)}}?.displayInternational
  - number: ({{Find Mobile Number (3)}} && {{Find Mobile Number (3)}}?.displayInternational)
  SETTINGS: {"authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 50. Enrich person  [action / enrich-person-with-mixrank-v2]
RUN-IF: {{Ready to Send}} && !!{{SKAEL Linked In Search}}?.output?.linkedin_url && false
  - person_identifier: {{SKAEL Linked In Search}}?.output?.linkedin_url
  - email: {{Email [GF]}}
  TYPE: {"type": "json"}

## 51. LinkedIn Match  [action / use-ai]
RUN-IF: !!{{Enrich person}}
  - useCase: "use-ai"
  - prompt: "#CONTEXT#\nYou are an AI-powered data matcher. You will be given enriched LinkedIn profile data and separate original reference data. Your task is to verify if the LinkedIn profile belongs to the same person as in the original data by comparing only the provided fields. Do not browse the web or use Google; only compare the given content.\n\n#OBJECTIVE#\nVerify whether the enriched LinkedIn profile matches the original person/company data and output a single boolean string: \"true\" if it is a match, \"false\" if it is not.\n\n#INSTRUCTIONS#\n1. Inputs provided:\n   - LinkedIn data blob (text): " + Clay.formatForAIPrompt({{Enrich person}}) + "\n   - Original person name: " + Clay.formatForAIPrompt({{Kontaktperson [Sauber]}}) + "\n   - Original company name: " + Clay.formatForAIPrompt({{Firmenname [Final]}}) + "\n   - Original company domain (optional): " + Clay.formatForAIPrompt({{Rows from: Datensätze Firmen}}?.["Website final"]) + "\n   - Original company address: " + Clay.formatForAIPrompt({{Adresse [Impressum]}}) + "\n\n2. Allowed evidence from LinkedIn data (use any that is present):\n   - Person’s name (exact or very similar; allow common variations, middle initials, nicknames)\n   - Current or past company mentions matching the original company name (exact or strong synonym/brand match)\n   - Location indicators (city, state/region, country) that reasonably align with the company address\n   - Mentions of ownership/founder/employee roles at the original company\n   - Mentions of the company’s website/domain if present\n\n3. Matching rules (any one of the following is sufficient to output \"true\"):\n   - name + company match (preferred)\n   - name + location match (acceptable)\n   - strong company association in work experience (current or past) with similar name\n   Additional guidance:\n   - Treat minor spelling differences, diacritics, or common nicknames as similar.\n   - For company name, allow recognized abbreviations, legal suffix variations (GmbH, Inc., Ltd.), brand/trade names, and obvious rebrand variants.\n   - For location, a reasonable geographic match (same city or same metro/region) is acceptable.\n   - If the LinkedIn data explicitly contradicts the original data (different unique name+company, entirely different geography), output \"false\".\n\n4. Domain and address signals (use only if present in the LinkedIn data):\n   - If LinkedIn data references a website/domain that matches " + Clay.formatForAIPrompt({{Rows from: Datensätze Firmen}}?.["Website final"]) + ", consider this strong evidence toward a match.\n   - If LinkedIn location aligns with the city/region/country implied by " + Clay.formatForAIPrompt({{Adresse [Impressum]}}) + ", consider this supportive evidence.\n\n5. Prohibited actions:\n   - Do not use Google, web search, or any external sources.\n   - Do not infer missing facts; only use what is present in the provided inputs.\n   - Do not output explanations or any extra text—only \"true\" or \"false\".\n\n6. Decision protocol:\n   - If at least one matching rule in step 3 is met based on evidence present in the LinkedIn data, output \"true\".\n   - Otherwise, output \"false\".\n\n#EXAMPLES#\nInput:\n- linkedinData: \"Johnathan (John) Doe — Founder at Acme Technologies GmbH (Acme Tech) — Berlin, Germany — Website: acme-tech.com\"\n- originalName: \"John Doe\"\n- originalCompany: \"Acme Technologies\"\n- originalDomain: \"acme-tech.com\"\n- originalAddress: \"Leipziger Str. 1, 10117 Berlin, Germany\"\nExpected output:\ntrue\n\nInput:\n- linkedinData: \"Jane Smith — Marketing Manager at BlueWave Inc. — Toronto, Canada\"\n- originalName: \"Jane Smyth\"\n- originalCompany: \"GreenLeaf Ltd\"\n- originalDomain: \"greenleaf.co\"\n- originalAddress: \"Dublin, Ireland\"\nExpected output:\nfalse"
  - model: "gpt-4o-mini"
  - answerSchemaType: {"type": "\"json\"", "fields": "{\"match\":{\"type\":\"boolean\",\"description\":\"\",\"id\":\"8fb789f7-67f1-4f06-99eb-a6fc778afc58\",\"options\":\"[{\\\"text\\\":\\\"true\\\",\\\"id\\\":\\\"12302d2e-2e25-4cef-8999-d1b1ffc398ee\\\",\\\"color\\\":\\\"red\\\"},{\\\"text\\\":\\\"false\\\",\\\"id\\\":\\\"fd323ab3-1d44-4e7b-a401-91669bdbfd10\\\",\\\"color\\\":\\\"yellow\\\"}]\"},\"reason\":{\"type\":\"string\",\"description\":\"Why did you make that decision?\",\"id\":\"a7d88f0f-b32b-406a-9016-506f7390043c\",\"options\":\"\"}}", "jsonType": "\"Fields\""}
  - metaprompt: {{Enrich person}}+" if this person is\n\n"+{{Kontaktperson [Sauber]}}+" working at "+{{Firmenname [Final]}}+" / "+{{website [Final]}}+" then print true else print false"
  - _metadata: {"modelSource": "user"}
  SETTINGS: {"optionalPathsInInputs": {"prompt": [["f_SzWkkodRShts"]]}, "authAccountId": "aa_REDACTED"}
  TYPE: {"type": "json"}

## 52. SKAEL Linked In Search  [action / http-api-v2]
RUN-IF: !!{{Email [Final]}} && false
  - method: "POST"
  - url: "https://api.skael.de/api/enrichments/ai_research_agent"
  - queryString: {"formulaMap": {}}
  - body: "{\n  \"system_prompt\": \"You are an expert researcher trained on finding the right LinkedIn Profile URLs for any person given at least their full name and their company name + additional data points.\",\n  \"user_prompt\": \"You're now going to find the LinkedIn Profile URL for " + Clay.formatForJSON({{Kontaktperson [Sauber]}}) + " at " + Clay.formatForJSON({{Firmenname [Final]}}) + ".\\n\\nThe result must match the pattern linkedin.com/in. It should not be a company URL or a posts URL or anything but a profile URL. Execute as many steps as necessary to find the profile URL, and ALSO to validate that it is the RIGHT profile URL for {{Kontaktperson [Sauber]}}. Return only the final URL and nothing else.\\n\\nIf you find a link with /posts/, you can replace /posts/ with /in/ and then remove everything after the first underscore (_). Then it's a correct result. For example, you could turn an incorrect result like: https://www.linkedin.com/posts/max-mustermann_top-5-ai-and-machine into a correct result like https://www.linkedin.com/in/max-mustermann\\n\\nFollow the steps below in your research:\\n\\n1. Search LinkedIn for a profile associated with the provided name.\\n2. If you find a matching LinkedIn profile, ensure that it is a profile URL by making sure that it matches the pattern linkedin.com/in\\n3. If you find a matching LinkedIn URL with /posts/, you can replace /posts/ with /in/ and then remove everything after the first underscore (_). Then it's a correct profile result.\\n4. If no profile is found that matches the name, run the following google searches below:\\n5. Run a google search for \\\"{{Kontaktperson [Sauber]}}\\\" site:linkedin.com/in\\n6. If that doesn't work, then run a google search for {{Kontaktperson [Sauber]}} site:linkedin.com/in\\n7. Finally, if that doesn't work, then search {{Kontaktperson [Sauber]}} site:linkedin.com, and repeat steps 2-3 for validating the URLs you find.\\n8. If you still find no results return \\\"No LinkedIn profile found\\\"\\n\\nImportant reminders:\\n- Base your search only on the exact name provided. Do not make any assumptions.\\n- Only search for and return information from LinkedIn. Do not use or include information from other sources.\\n- Do not include any additional information or commentary in your response, only the LinkedIn profile URL or the \\\"no profile found\\\" message.\\n- Maximize the total number of steps you need to return accurate results here.\",\n  \"schema\": {\n    \"type\": \"object\",\n    \"properties\": {\n      \"linkedin_url\": {\n        \"type\": \"string\",\n        \"description\": \"The LinkedIn profile URL matching the pattern linkedin.com/in/username. Return 'No LinkedIn profile found' if not found.\"\n      },\n      \"confidence\": {\n        \"type\": \"number\",\n        \"description\": \"Confidence score 0.0-1.0 that this is the correct person's profile\"\n      },\n      \"found\": {\n        \"type\": \"boolean\",\n        \"description\": \"Whether a matching LinkedIn profile was found\"\n      }\n    },\n    \"required\": [\n      \"linkedin_url\",\n      \"confidence\",\n      \"found\"\n    ],\n    \"additionalProperties\": false\n  },\n  \"max_steps\": 10,\n  \"model\": \"google/gemini-2.5-flash\"\n}"
  - headers: {"Content-Type": "\"application/json\"", "Authorization": "\"Bearer \"+{{Skael API Key}}"}
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 53. HTTP RESERVE  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 54. HTTP RESERVE (2)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 55. HTTP RESERVE (3)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 56. HTTP RESERVE (4)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 57. HTTP RESERVE (5)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 58. HTTP RESERVE (6)  [action / http-api-v2]
RUN-IF: false
  - method: "POST"
  - url: "api.skael.de"
  - removeNull: true
  - followRedirects: true
  - shouldRetry: true
  TYPE: {"type": "json"}

## 59. business_id  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.business_id
  TYPE: {"type": "text"}

## 60. Email [Info@][Status]  [formula]
FORMEL:
!{{Skael Validate Info@}} ? "Not Run" : 
  {{Skael Validate Info@}}?.output?.code == 5 ? "Safe to Send" : 
    {{Skael Validate Info@}}?.output?.code == 4 ? "Risky" : 
      {{Skael Validate Info@}}?.output?.code == 7 ? "Unknown" : 
        [1, 2, 3, 6].includes(parseInt({{Skael Validate Info@}}?.output?.code)) ? "Invalid" : 
          "None found"
  SETTINGS: {"formulaPrompt": "\"if \" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \" print \\\"Safe to Send\\\"\\nif \" + {{f_9uzzwyaPXeWT}}?.other_emails?.[0]?.email + \" print \\\"Risky\\\"\\nif !\" + {{f_MsivXQVhcry4}} + \" print \\\"Not Run\\\"\\nif \" + {{f_MsivXQVhcry4}} + \" and (!\" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \"or !\" + {{f_9uzzwyaPXeWT}}?.other_emails?.[0]?.email + \") print \\\"None found\\\"\""}
  TYPE: {"type": "select", "options": [{"id": "7b69bad5-b7d2-4054-a82c-6781f52b366b", "text": "Safe to Send", "color": "green"}, {"id": "be2ce1f2-4901-4747-a170-2fe00c2d6db0", "text": "Risky", "color": "yellow"}, {"id": "d7cfaaf8-def1-434f-b959-4e55eeb0ec8a", "text": "Invalid", "color": "red"}, {"id": "e4e6

## 61. rating  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.rating
  TYPE: {"type": "text"}

## 62. Created At  [date]
  TYPE: {"type": "date"}

## 63. address  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.address
  TYPE: {"type": "text"}

## 64. Last Name [GF]  [formula]
FORMEL:
{{Kontaktperson [Sauber]}}?.split(" ")?.pop()
  SETTINGS: {"formulaPrompt": "\"last name from \" + {{Kontaktperson [Sauber]}}"}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 65. Confidence  [formula]
FORMEL:
{{Anrede [Prompt] (2)}}?.confidence
  SETTINGS: {"mappedResultPath": ["confidence"]}
  TYPE: {"type": "number"}

## 66. Ansprache Normal [GT] [Final]  [formula]
FORMEL:
{{Anrede}} ? "Guten Tag" + " " + {{Anrede}} + " " + {{Last Name [GF]}} : {{Email [Final]}} ? "Guten Tag" : ""
  SETTINGS: {"formulaPrompt": "\"{{Anrede}} ? {{Formal}} + \\\" \\\" + {{Anrede}} + \\\" \\\" + {{Last Name [GF]}} : \\\"Sehr geehrte Damen und Herren\\\"\""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 67. Email [Final][Status]  [formula]
FORMEL:
{{Email [GF]}} ? {{Email [GF][Status]}} : {{Email [Info@]}} ? {{Email [Info@][Status]}} : {{Email [GF][Status]}} === "None found" && {{Email [Info@][Status]}} === "None found" ? "None found" : ({{Email [GF][Status]}} === "Not Run" || {{Email [GF][Status]}} === "Kein GF") && {{Email [Info@][Status]}} === "Not Run" ? "Not Run" : "None found"
  SETTINGS: {"formulaPrompt": "\"if \" + {{Email [GF]}} + \" print \" + {{Email [GF][Status]}} + \" if \" + {{Email [Info@]}} + \" print \" + {{Email [Info@][Status]}}"}
  TYPE: {"type": "select", "options": [{"id": "07d7583e-6eb6-4090-a10b-9fc3c1589554", "text": "Safe to Send", "color": "green"}, {"id": "2c0c9f75-fee6-43f8-b4c0-2995e20f29c3", "text": "Risky", "color": "yellow"}, {"id": "c7192434-52b4-47fe-a41b-e01a5a6fd3fc", "text": "Not Run", "color": "violet"}, {"id": "4

## 68. Personalisierung generieren  [formula]
FORMEL:
{{Email [Final]}} ? true : false
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "boolean"}

## 69. Anrede  [formula]
FORMEL:
{{Anrede [Prompt] (2)}}?.anrede
  SETTINGS: {"mappedResultPath": ["anrede"]}
  TYPE: {"type": "text"}

## 70. Email [Domain]  [formula]
FORMEL:
{{Email [Impressum]}} ? (!["gmx.de", "web.de", "google.de", "google.com", "gmail.com", "outlook.com", "outlook.de", "t-online.de","aol.com", "1und1.de", "freenet.de", "arcor.de", "yahoo.com","mail.de", "aikq.de", "mailbox.org", "posteo.de", "tutanota.com", "icloud.com","googlemail.com", "mail.ru", "protonmail.com", "mail.com"].includes({{Email [Impressum]}}?.split("@")?.[1]) ? {{Email [Impressum]}}?.split("@")?.[1] : {{website [Final]}} ? {{website [Final]}}?.replace(/https?:\/\/(www\.)?/, "")?.split("/")?.[0]?.split(".")?.slice(-2)?.join(".") : "") : {{website [Final]}} ? {{website [Final]}}?.replace(/https?:\/\/(www\.)?/, "")?.split("/")?.[0]?.split(".")?.slice(-2)?.join(".") : ""
  SETTINGS: {"formulaPrompt": "\"extract email domain from \" + {{Email [Impressum]}} + \" else extract email domain from \" + {{website [Final]}} + \" (must remove any subdomain)\""}
  TYPE: {"type": "text"}

## 71. Ansprache Persönlich [Final]  [formula]
FORMEL:
{{First Name [GF]}} && {{Anrede}} ? "Hallo" + " " + {{First Name [GF]}} : {{Email [Final]}} ? "Hallo" : ""
  SETTINGS: {"formulaPrompt": ""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 72. Ready to Send  [formula]
FORMEL:
!!{{Email [Final]}} && !!{{Personalisierung}} && !!{{Video Title}}
  SETTINGS: {"formulaPrompt": "\"print true if \" + {{f_dF8aonT7Qh99}} + \" is populated and \" + {{Email [Final]}} + \" is populated\""}
  TYPE: {"type": "boolean"}

## 73. Telefon [Impressum]  [formula]
FORMEL:
{{SKAEL Impressum}}?.output?.telefon
  SETTINGS: {"mappedResultPath": ["telefon"]}
  TYPE: {"type": "text"}

## 74. Email [Info@]  [formula]
FORMEL:
[4, 5, 7].includes(parseInt({{Skael Validate Info@}}?.output?.code)) ? {{Skael Validate Info@}}?.output?.email : ""
  SETTINGS: {"mappedResultPath": ["valid_emails", 0, "email"]}
  TYPE: {"type": "text"}

## 75. Email [Final]  [formula]
  SETTINGS: {"formulaWaterfall": ["{{Email [GF]}}", "{{Email [Info@]}}"]}
  TYPE: {"type": "text"}

## 76. review_count  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.review_count
  TYPE: {"type": "text"}

## 77. website [Final]  [formula]
FORMEL:
/^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(\/.*)?$/i.test({{website}}) ? {{website}} : {{Company Domain}}?.response
  SETTINGS: {"formulaPrompt": "\"make sure \" + {{website}} + \" is a valid domain then print it else print \\\"\\\" \""}
  TYPE: {"type": "url"}

## 78. Email [GF][Status]  [formula]
FORMEL:
!{{Kontaktperson [Sauber]}} && {{SKAEL Impressum}} ? "Kein GF" : 
  !{{Skael Validate GF}} ? "Not Run" : 
    {{Skael Validate GF}}?.output?.code == 5 ? "Safe to Send" : 
      {{Skael Validate GF}}?.output?.code == 4 ? "Risky" : 
        {{Skael Validate GF}}?.output?.code == 7 ? "Unknown" : 
          [1, 2, 3, 6].includes(parseInt({{Skael Validate GF}}?.output?.code)) ? "Invalid" : 
            !{{Find Work Email}}?.record?.email ? "None found" : 
              "None found"
  SETTINGS: {"formulaPrompt": "\"if !\" + {{Kontaktperson [Sauber]}} + \" && \" + {{f_cEmSQcNTwd6Q}} + \" print \\\"Kein GF\\\"\\nif \" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \" print \\\"\" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.result + \"\\\"\\nif \" + {{f_7WGzzAQbbnUy}}?.results?.validation + \" = \\\"unknown\\\" print \\\"None found\\\"\\nif !\" + {{f_MsivXQVhcry4}} + \" print \\\"Not Run\\\"\\nif \" + {{f_MsivXQVhcry4}} + \" and !\" + {{f_MsivXQVhcry4}}?.valid_emails?.[0]?.email + \" print \\\"None found\\\"\""}
  TYPE: {"type": "select", "options": [{"id": "7b69bad5-b7d2-4054-a82c-6781f52b366b", "text": "Safe to Send", "color": "green"}, {"id": "be2ce1f2-4901-4747-a170-2fe00c2d6db0", "text": "Risky", "color": "yellow"}, {"id": "360db597-8999-423e-90ed-cbee16f9ba3f", "text": "Invalid", "color": "red"}, {"id": "e4e6

## 79. Tel. [Importiert]  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.phone
  TYPE: {"type": "text"}

## 80. query_keyword  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.query_keyword
  TYPE: {"type": "text"}

## 81. Adresse [Impressum]  [formula]
FORMEL:
{{SKAEL Impressum}}?.output?.adresse
  SETTINGS: {"mappedResultPath": ["adresse"]}
  TYPE: {"type": "text"}

## 82. Launch Campaign  [formula]
FORMEL:
(!!{{Kontaktperson [Sauber]}} || !!{{Email [Impressum]}})
  TYPE: {"type": "boolean"}

## 83. Kontaktperson [Sauber]  [formula]
FORMEL:
{{Kontaktperson}}
?.replace(/\([^)]*\)|\{[^}]*\}|\[[^\]]*\]/g,"")
?.split(" ")
?.filter(t=>t.trim()!=="" && !t.includes(".") && !["herr","frau","hr","rechtsanwalt"].includes(t.toLowerCase()) && !(t===t.toUpperCase() && t.length>1))
?.join(" ")
?.replace(/^(\S+)(?:\s+\S+)*\s+(\S+)$/,"$1 $2")
?.replace(/é/g,"e")
?.replace(/è/g,"e")
?.replace(/ê/g,"e")
?.replace(/ë/g,"e")
?.replace(/á/g,"a")
?.replace(/à/g,"a")
?.replace(/â/g,"a")
?.replace(/ä/g,"ae")
?.replace(/ó/g,"o")
?.replace(/ò/g,"o")
?.replace(/ô/g,"o")
?.replace(/ö/g,"oe")
?.replace(/ú/g,"u")
?.replace(/ù/g,"u")
?.replace(/û/g,"u")
?.replace(/ü/g,"ue")
?.replace(/ñ/g,"n")
?.replace(/ç/g,"c")
?.replace(/ß/g,"ss")
?.replace(/'/g,"")
?.replace(/'/g,"")
?.replace(/`/g,"")
?.replace(/[^A-Za-z0-9\s-]/g,"")
?.trim()
  SETTINGS: {"mappedResultPath": ["geschaeftsfuehrer", 0]}
  TYPE: {"type": "text"}

## 84. Email [Impressum]  [formula]
FORMEL:
(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test({{SKAEL Impressum}}?.output?.email?.replace(/\(at\)|\[at\]/g, "@")) ? {{SKAEL Impressum}}?.output?.email?.replace(/\(at\)|\[at\]/g, "@") : "") || 
(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test({{SKAEL Impressum}}?.output?.email?.replace(/\(at\)|\[at\]/g, "@")) ? {{SKAEL Impressum}}?.output?.email?.replace(/\(at\)|\[at\]/g, "@") : "") || 
""
  SETTINGS: {"formulaPrompt": "\"replace (at),[at] with @ \" + {{f_cEmSQcNTwd6Q}}?.email + \" and then only print if it is a valid email\"", "mappedResultPath": ["email"]}
  TYPE: {"type": "text"}

## 85. Updated At  [date]
  TYPE: {"type": "date"}

## 86. Email [GF]  [formula]
FORMEL:
{{Skael Validate GF}}?.output?.code == 5 ? {{Skael Validate GF}}?.output?.email : 
  {{Skael Validate GF}}?.output?.code == 4 ? {{Skael Validate GF}}?.output?.email : 
  {{Skael Validate GF}}?.output?.code == 7 ? {{Skael Validate GF}}?.output?.email : 
  ""
  SETTINGS: {"mappedResultPath": ["first_safe_to_send_email"]}
  TYPE: {"type": "text"}

## 87. Email [Final][Type]  [formula]
FORMEL:
{{Email [GF]}} ? "GF" : {{Email [Info@]}} ? "Info@" : ({{Email [GF][Status]}} === "Not Run" || {{Email [GF][Status]}} === "Kein GF") && {{Email [Info@][Status]}} === "Not Run" ? "Not Run" : "None found"
  SETTINGS: {"formulaPrompt": "\"if \" + {{Email [GF]}} + \" print \\\"GF\\\"\\nif \" + {{Email [Info@]}} + \" print \\\"Info@\\\"\\n\""}
  TYPE: {"type": "select", "options": [{"id": "4e5b5624-2532-40b8-95f8-8a4650e47c85", "text": "GF", "color": "green"}, {"id": "6779b9c9-7ad9-4095-b8a4-dd2cb32cd342", "text": "Info@", "color": "yellow"}, {"id": "ed535903-257f-4404-8778-2b7ed838a68b", "text": "Not Run", "color": "violet"}, {"id": "ead7f203-9a

## 88. First Name [GF]  [formula]
FORMEL:
{{Kontaktperson [Sauber]}}?.split(" ")?.[0]
  SETTINGS: {"formulaPrompt": "\"first name from \" + {{Kontaktperson [Sauber]}}"}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 89. Ansprache Formal [Final]  [formula]
FORMEL:
{{Anrede}} ? {{Formal}} + " " + {{Anrede}} + " " + {{Last Name [GF]}} : {{Email [Final]}} ? "Sehr geehrte Damen und Herren" : ""
  SETTINGS: {"formulaPrompt": "\"if \" + {{Anrede}} + \" is populated print \\\"\" + {{Formal}} + \" \" + {{Anrede}} + \" \" + {{Last Name [GF]}} + \"\\\" else print \\n\\\"Sehr geehrte Damen und Herren\\\"\""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 90. category  [formula]
FORMEL:
{{Rows from: Datensätze Firmen}}?.category
  TYPE: {"type": "text"}

## 91. Formal  [formula]
FORMEL:
{{Anrede}} === "Herr" ? "Sehr geehrter" : {{Anrede}} === "Frau" ? "Sehr geehrte" : ""
  SETTINGS: {"formulaPrompt": "\"if \" + {{Anrede}} + \" Herr print \\\"Sehr geehrter\\\" if Frau print \\\"Sehr geehrte\\\" else print \\\"\\\"\""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

## 92. Firmenname  [formula]
FORMEL:
(({{Rows from: Datensätze Firmen}}?.title) || {{Rows from: Datensätze Firmen}}?.Firmenname) || {{Rows from: Datensätze Firmen}}?.Firmenname
  TYPE: {"type": "text"}

## 93. Ansprache Normal [Final]  [formula]
FORMEL:
{{Anrede}} ? "Hallo" + " " + {{Anrede}} + " " + {{Last Name [GF]}} : {{Email [Final]}} ? "Hallo" : ""
  SETTINGS: {"formulaPrompt": "\"{{Anrede}} ? {{Formal}} + \\\" \\\" + {{Anrede}} + \\\" \\\" + {{Last Name [GF]}} : \\\"Sehr geehrte Damen und Herren\\\"\""}
  TYPE: {"type": "text", "label": "Text", "iconType": {"displayName": "TextT"}}

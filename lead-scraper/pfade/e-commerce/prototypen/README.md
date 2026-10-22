# Prototypen aus der Recherche „Shops ohne Liste finden“ (08.10.2026)

**Nicht Teil des Pfads.** Diese Skripte sind Messwerkzeuge aus der Recherche, kein Produktcode. Sie belegen die Zahlen in `../referenzen/shop-katalog.md` und sind Ausgangspunkt für den Bau des Shop-Katalogs. Alles ist Python-Standardbibliothek.

| Datei | Was es tut | Hinweise |
|---|---|---|
| `fetch.py` | höflicher Abruf je Domain: `robots.txt` + Startseite; speichert Rohantworten unter `raw/` | Eigener robots-Prüfer nach RFC 9309. **Nicht für Massenläufe vom eigenen Anschluss.** Vor dem Produktiveinsatz härten: 64 KB, Grenze je /24, 2. Versuch, 5xx-robots = alles verboten (siehe `shop-katalog.md`, Abschnitt „Härtung“) |
| `classify.py` | Shopsystem-Erkennung, Regelstand **fp v2** (`--fp 1` = alter Stand aus `fingerprints.md`) | 20/20 auf der Entwicklungsstichprobe, **in-sample**; unabhängig erst 1 Fall. Bekannter Fehler: Stufe 2 muss an `/_nuxt/`/`/_next/` hängen, nicht an `headless` |
| `dnsprobe.py`, `dnssub.py` | DNS-Vorstufe: A/CNAME/NS/MX/PTR; Shop-Subdomains (`checkout.`, `shop.`) mit Wildcard-Test | ruft `dig` auf |
| `ctparse.py` | Parser für Certificate-Transparency-Kacheln (static-ct-api) und RFC-6962-Einträge, zieht die SAN-Namen | an 5.120 Einträgen getestet |
| `crux_hosts.py`, `crux_hostplan.py` | Größe der CrUX-Länderlisten DE/AT/CH und Abrufplan auf Host-Ebene | vereinfachte Public Suffix List; für den Bau die echte PSL nehmen |
| `sample.csv` | die 25 Testdomains mit erwartetem System und Quelle | 6 der 25 Quell-Etiketten waren falsch oder veraltet |

Rohdaten (`raw/`, `*.jsonl`) werden nicht mitgeliefert. Sie enthalten fremdes HTML und bleiben außerhalb des Pakets.

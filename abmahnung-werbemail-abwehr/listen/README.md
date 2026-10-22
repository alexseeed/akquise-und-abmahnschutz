# Feste Referenzlisten

Diese Listen sind Teil des Skills und ändern sich nur mit neuen Skill-Versionen. Die Liste der bekannten **Abmahner** liegt nicht hier, sondern in der Community-Sperrliste (GitHub-Repository, siehe `references/06_community-sperrliste.md`), weil sie laufend wächst.

## drittanbieter.csv

Bekannte Drittserver, die auf Websites nachgeladen werden. Trennzeichen `;`, UTF-8.

| Spalte | Bedeutung |
|---|---|
| host_endung | Endung des Hostnamens (Abgleich per „endet auf“); bei Einträgen mit `/` zusätzlich Pfadanfang |
| anbieter | Unternehmen bzw. Dienst |
| kategorie | Funktion auf der Website |
| sitz | Sitz bzw. Hauptverarbeitungsort laut öffentlichen Angaben |
| drittland_usa | ja = Übermittlung in die USA wahrscheinlich; DPF-Zertifizierung im Einzelfall prüfen |
| endgeraetezugriff_typisch | setzt der Dienst typischerweise Cookies/localStorage (§ 25 TDDDG)? |
| einwilligung_typisch_noetig | übliche Bewertung; „umstritten“ = Einzelfall prüfen |
| hinweis | Besonderheiten |

Die Einträge sind typische Bewertungen und ersetzen nicht die Prüfung des Einzelfalls. Unbekannte Hosts per Websuche zuordnen und dem Skill-Betreiber zur Aufnahme melden.

## consent-tools.csv

Verbreitete Consent-Tools und woran man im Browser erkennt, dass eine Ablehnung gespeichert wurde. Damit lässt sich in Szenario B belegen: „Die Ablehnung wurde nachweislich gespeichert – und trotzdem wurde geladen.“

Spalte `sicherheit`: **getestet** = an einer echten Website mit dem Sicherungsskript geprüft; **bekannt** = aus Herstellerdokumentation und Praxis bekannt; **Schlüssel im Browser prüfen** = Schlüsselname variiert nach Version oder Konfiguration, vor Verwendung in `_zustand.json` nachsehen.

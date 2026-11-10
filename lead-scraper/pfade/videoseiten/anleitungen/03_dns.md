# Anleitung 3: Eine Subdomain auf deinen Server zeigen lassen (A-Record)

> **Für den Agenten:** Lies diese Anleitung dem Nutzer Schritt für Schritt vor. Nach jedem Schritt wartest du auf seine Rückmeldung, bevor du weitermachst. Lies nur den Abschnitt seines Anbieters vor (Teil C), nicht alle. Die Befehle in Teil A und D führst du selbst aus, der Nutzer muss nichts eintippen außer in der Oberfläche seines Anbieters.
>
> Vorher brauchst du zwei Werte: die **IP-Adresse des Servers** und die **Subdomain**, die der Nutzer möchte (Vorschlag: `angebot`). Trag beide unten in die Wertetabelle ein, bevor du vorliest.

Alle Quellen wurden am **25.10.2026** abgerufen. Anbieter ändern ihre Oberflächen manchmal. Wenn ein Knopf anders heißt als hier beschrieben, ist das kein Fehler von dir: Sag dem Agenten, was du stattdessen siehst.

---

## Worum geht es?

Deine Angebotsseiten sollen unter einer Adresse wie `angebot.deine-firma.de` erreichbar sein. Damit das klappt, muss das Internet wissen, auf welchem Rechner diese Adresse liegt.

Das regelt ein **DNS-Eintrag**. DNS ist das Telefonbuch des Internets: Es übersetzt einen Namen wie `angebot.deine-firma.de` in eine Nummer, die **IP-Adresse** (die Anschrift des Servers, z. B. `203.0.113.10`).

Der Eintrag, den wir anlegen, heißt **A-Record** (der Eintragstyp „A“ steht für „Address“, also Adresse). Er sagt: „`angebot` gehört zur IP-Adresse X.“

Mehr nicht. Du änderst nichts an deiner bestehenden Website und nichts an deinen E-Mails.

### Die Werte, die du gleich einträgst

| Feld (heißt je nach Anbieter anders) | Was du einträgst | Erklärung |
|---|---|---|
| **Typ** | `A` | Der Eintragstyp für eine IPv4-Adresse (die klassische Zahlen-Adresse mit vier Blöcken). |
| **Name / Host / Hostname / Subdomain** | `angebot` | **Nur** das Wort vor deiner Domain, nicht `angebot.deine-firma.de`. |
| **Wert / Zeigt auf / Points to / IPv4-Adresse** | `___.___.___.___` *(trägt der Agent ein)* | Die IP-Adresse deines Servers. |
| **TTL** | nichts ändern | TTL („Time to live“) sagt, wie lange sich andere Rechner den Eintrag merken. Der vorgeschlagene Standardwert passt. |

Fast alle Anbieter wollen im Namensfeld nur das Präfix (das Wort vor der Domain). Das steht so bei Hostinger, IONOS, GoDaddy und Namecheap (Quellen siehe Teil C).

**Einen AAAA-Record brauchst du nicht.** Ein AAAA-Record ist dasselbe für die neuere IPv6-Adresse. Wichtig ist eher das Gegenteil: Falls für `angebot` schon ein AAAA-Record existiert, der auf einen anderen Rechner zeigt, muss er weg (siehe „Häufige Probleme“).

### Warum eine Subdomain und nicht deine Hauptdomain?

- Deine Hauptdomain (`deine-firma.de`) zeigt auf deine bestehende Website. Würdest du dort die IP ändern, wäre die Website weg. GoDaddy warnt ausdrücklich, dass Änderungen an einem bestehenden A-Record Website oder E-Mail stören können ([GoDaddy: Add or edit an A record](https://www.godaddy.com/help/add-or-edit-an-a-record-42546)).
- Eine neue Subdomain (`angebot.deine-firma.de`) ist ein zusätzlicher Name. Sie stört nichts, was es schon gibt.
- Wenn du die Angebotsseiten irgendwann nicht mehr brauchst, löschst du nur diesen einen Eintrag.

---

## Teil A: Vorbereitung (macht der Agent)

### Schritt 1: Herausfinden, wo deine DNS-Einträge verwaltet werden

Die Domain kann bei einem Anbieter gekauft sein, die DNS-Einträge aber bei einem anderen liegen (zum Beispiel Domain bei STRATO, DNS bei Cloudflare). Eingetragen wird immer dort, wo die **Nameserver** liegen (die Rechner, die das „Telefonbuch“ für deine Domain führen).

> **Agent:** Führe `dig +short NS deine-firma.de` aus (oder `nslookup -type=NS deine-firma.de`). Sag dem Nutzer, welcher Anbieter das ist. Halte außerdem den Ist-Zustand fest, damit ihr hinterher vergleichen könnt: `dig +short A deine-firma.de`, `dig +short A www.deine-firma.de`, `dig +short MX deine-firma.de`, `dig +short A angebot.deine-firma.de`, `dig +short AAAA angebot.deine-firma.de`.

**Was du dem Agenten zurückmeldest:** „Ja, bei diesem Anbieter habe ich einen Login“ oder „Den Anbieter kenne ich nicht“. Im zweiten Fall frag deine Webagentur oder schau in deine Rechnungen, bei wem du die Domain bezahlst.

GoDaddy weist zum Beispiel darauf hin, dass ein A-Record dort nur wirkt, wenn die Domain die GoDaddy-Nameserver nutzt. Sonst muss er beim eigentlichen DNS-Anbieter angelegt werden ([GoDaddy: Add an A record](https://www.godaddy.com/help/add-an-a-record-19238)). Namecheap sagt dasselbe für seine eigenen DNS-Dienste ([Namecheap: A record](https://www.namecheap.com/support/knowledgebase/article.aspx/319/2237/how-can-i-set-up-an-a-address-record-for-my-domain/)).

---

## Teil B: Der Ablauf bei jedem Anbieter

Egal welcher Anbieter, es ist immer dasselbe Muster:

1. Beim Anbieter einloggen.
2. Die Domain auswählen.
3. Die DNS-Einstellungen öffnen.
4. Neuen Eintrag hinzufügen, Typ **A**.
5. Name `angebot`, Wert = IP-Adresse, TTL so lassen.
6. Speichern.

Vor dem Speichern prüfst du: Gibt es für `angebot` schon einen Eintrag (A, AAAA oder CNAME)? Dann sag es dem Agenten, bevor du etwas löschst. Hostinger, IONOS und Namecheap raten, widersprüchliche alte Einträge für denselben Namen zu entfernen (Quellen siehe Teil C).

---

## Teil C: Klickfolge je Anbieter

Lies nur den Abschnitt, den der Agent dir nennt.

### Hostinger

Quellen: [How to use Hostinger's DNS zone editor](https://www.hostinger.com/support/how-to-use-hostingers-dns-zone-editor/) und [How to manage A records at Hostinger](https://www.hostinger.com/support/4468886-how-to-manage-a-records-at-hostinger/), abgerufen 25.10.2026. Die Hilfe ist englisch, die Knopfnamen unten stehen deshalb englisch.

1. Bei Hostinger einloggen (hPanel, das ist die Verwaltungsoberfläche von Hostinger).
2. **Wenn du dort ein Hosting-Paket hast:** Klicke auf **Websites**, wähle deine Website, dann **Advanced** und **DNS Zone Editor**.
   **Wenn du dort nur die Domain hast:** Klicke auf **Domains**, wähle deine Domain, dann **DNS / Nameservers**.
3. Du siehst den Bereich **Manage DNS Records**.
4. Bei **Type** wählst du **A**.
5. Bei **Name** tippst du `angebot`.
6. Bei **Points to** tippst du die IP-Adresse.
7. **TTL** lässt du stehen (Hostinger schlägt 14400 Sekunden vor, das sind 4 Stunden).
8. Klicke auf **Add Record**.

**Was du danach siehst:** Der neue Eintrag steht in der Liste darunter.
**Was du dem Agenten meldest:** „Hostinger: Eintrag gespeichert.“ Hostinger nennt bis zu 24 Stunden, bis die Änderung überall angekommen ist.

### IONOS

Quelle: [IONOS-Hilfe: Ändern der IPv4/IPv6-Adresse einer Domain (A/AAAA-Record)](https://www.ionos.de/hilfe/domains/ip-adresse-konfigurieren/domain-mit-statischer-ip-adresse-verbinden/), abgerufen 25.10.2026.

1. Bei IONOS einloggen und die Domain-Übersicht öffnen. *(ungeprüft: Die Hilfeseite beschreibt den Weg erst ab der Domainliste. Wie der Menüpunkt dorthin heißt, steht dort nicht; vermutlich „Domains & SSL“.)*
2. Bei deiner Domain unter **Aktionen** auf das Symbol mit den **drei Punkten** klicken, dann auf **DNS**.
3. Auf **Record hinzufügen** klicken.
4. Bei **Typ** **A** wählen.
5. Bei **Hostname** `angebot` eintragen.
6. Bei **Zeigt auf** die IP-Adresse eintragen.
7. **TTL** so lassen.
8. Auf **Speichern** klicken.

**Was du danach siehst:** Der neue A-Eintrag für `angebot` steht in der DNS-Liste.
**Was du dem Agenten meldest:** „IONOS: Eintrag gespeichert.“ Laut IONOS wirkt die Änderung sofort, weltweit kann es bis zu etwa einer Stunde dauern.

Hinweis von IONOS: Für einen Namen sollte nur ein A-Record existieren, sonst antwortet das DNS mal mit der einen, mal mit der anderen Adresse. Einen Hostnamen kann man bei IONOS nicht umbenennen, nur neu anlegen und den alten löschen.

### STRATO

Quellen: [STRATO FAQ: Subdomains anlegen und löschen](https://www.strato.de/faq/domains/subdomains-anlegen-und-loeschen/) und [STRATO FAQ: Wie kann ich bei STRATO meine DNS-Einträge verwalten?](https://www.strato.de/faq/domains/wie-kann-ich-bei-strato-meine-dns-eintraege-verwalten/), abgerufen 25.10.2026.

Bei STRATO legst du zuerst die Subdomain an und stellst dann ihre Adresse um.

**Subdomain anlegen:**

1. Im **STRATO Kunden-Login** mit Kundennummer und Kundenpasswort anmelden.
2. Auf **Domains** klicken. In der Domainübersicht bei deiner Domain auf das **Zahnrad** klicken.
3. In der Domainverwaltung auf **Webserver** klicken.
4. In das Eingabefeld `angebot` tippen.
5. Unten rechts auf **Subdomain anlegen** klicken.

**Adresse der Subdomain setzen:**

6. Zurück in **Domains** → **Domainverwaltung**. Unter deiner Domain **Subdomains anzeigen** aufklappen und `angebot` auswählen.
7. Den Bereich **DNS-Verwaltung** aufklappen.
8. Neben **A-Record** auf **verwalten** klicken.
9. Den Schalter auf **Eigene IP-Adresse** stellen und die IP-Adresse eintragen.
10. Auf **Einstellungen übernehmen** klicken.

**Was du dem Agenten meldest:** „STRATO: Subdomain angelegt und IP eingetragen.“ STRATO nennt bis zu 24 Stunden Wartezeit.

*Ungeprüft:* Ob STRATO für eine neue Subdomain automatisch auch einen AAAA-Record (IPv6) auf STRATO-Server setzt, steht in der Hilfe nicht. Der Agent prüft das nach dem Speichern (siehe Teil D).

### GoDaddy

Quelle: [GoDaddy: Add an A record](https://www.godaddy.com/help/add-an-a-record-19238), abgerufen 25.10.2026. Die deutschen Knopfnamen stammen aus der deutschen Fassung derselben Hilfeseite.

1. Bei GoDaddy einloggen und dein **Domain-Portfolio** öffnen.
2. Auf deine Domain klicken. Es öffnen sich die **Domain-Einstellungen**.
3. Auf **DNS** klicken.
4. Auf **Neuen Datensatz hinzufügen** klicken und bei **Typ** **A** wählen.
5. Bei **Name** `angebot` eintragen.
6. Bei **Wert** die IP-Adresse eintragen.
7. **TTL** so lassen (Standard: 1 Stunde).
8. Auf **Speichern** klicken.
9. Falls GoDaddy einen Bestätigungscode verlangt (bei aktivem „Domain Protection“): den Code aus SMS, Authenticator-App oder E-Mail eingeben. **Den Code tippst du selbst ein, nicht der Agent.**

**Was du dem Agenten meldest:** „GoDaddy: Eintrag gespeichert.“ Laut GoDaddy wirken die meisten Änderungen innerhalb einer Stunde, im Einzelfall dauert es bis zu 48 Stunden.

### united-domains

Quellen: [united-domains: Eigener Mailserver einrichten](https://www.united-domains.de/help/faq-article/ich-betreibe-einen-eigenen-mailserver/) (dort steht die Klickfolge für einen A-Eintrag auf einer Subdomain) und [united-domains: Wie kann ich die DNS-Einträge wieder aktivieren?](https://www.united-domains.de/help/faq-article/wie-kann-ich-die-united-domains-dns-eintraege-wieder-aktivieren/), abgerufen 25.10.2026.

1. Auf united-domains.de oben rechts auf das **Benutzer-Symbol** klicken, E-Mail und Passwort eingeben, auf **Login** klicken.
2. Neben deiner Domain auf das Symbol **DNS** klicken.
3. **DNS-Einträge** wählen.
4. Den Bereich **A (IPv4)** öffnen und auf **Hinzufügen** klicken.
5. Im Feld **Subdomain** `angebot` eintragen.
6. Im Feld **IPv4 Adresse** die IP-Adresse eintragen.
7. Speichern. *(ungeprüft: Die Hilfe sagt nur „speichern“, nicht wie der Knopf genau heißt.)*

**Was du dem Agenten meldest:** „united-domains: Eintrag gespeichert.“ united-domains nennt bis zu 24 Stunden, bis die Änderung weltweit angekommen ist.

**Wichtig bei united-domains:** Laut Hilfe entfernt united-domains seine Standard-Einträge, sobald du eigene A-Einträge speicherst. Ob das nur für `angebot` gilt oder für die ganze Domain, sagt die Hilfe nicht (*ungeprüft*). Deshalb vergleicht der Agent danach, ob deine Hauptwebsite und deine E-Mail-Einträge unverändert sind (Teil D, Schritt 3). Falls doch etwas fehlt: Im selben Bereich **A (IPv4 Adressen)** gibt es den Link **auf Standard setzen**. Den erst nach Rücksprache mit dem Agenten klicken, denn er setzt alle eigenen A-Einträge zurück.

### Namecheap

Quelle: [Namecheap: How can I set up an A (address) record for my domain?](https://www.namecheap.com/support/knowledgebase/article.aspx/319/2237/how-can-i-set-up-an-a-address-record-for-my-domain/), abgerufen 25.10.2026. Die Oberfläche ist englisch.

1. Bei Namecheap einloggen.
2. Links auf **Domain List** klicken, dann neben deiner Domain auf **Manage**.
3. Den Reiter **Advanced DNS** öffnen.
4. Im Bereich **Host Records** auf **Add New Record** klicken.
5. Bei **Type** **A Record** wählen.
6. Bei **Host** `angebot` eintragen.
7. Im Wertfeld die IP-Adresse eintragen.
8. Auf das grüne Häkchen-Symbol (**Save changes**) klicken.

**Was du dem Agenten meldest:** „Namecheap: Eintrag gespeichert.“ Laut Namecheap dauert es normalerweise etwa 30 Minuten.

Namecheap-Hinweis: Wenn es für `angebot` schon eine Weiterleitung („Redirect“) oder einen A- oder CNAME-Eintrag gibt, muss der weg. Lösch ihn erst nach Rücksprache mit dem Agenten.

### Cloudflare

Quellen: [Cloudflare: Create DNS records](https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/), [Cloudflare: Proxy status](https://developers.cloudflare.com/dns/proxy-status/), [Cloudflare: ERR_TOO_MANY_REDIRECTS](https://developers.cloudflare.com/ssl/troubleshooting/too-many-redirects/), [Caddy: Automatic HTTPS](https://caddyserver.com/docs/automatic-https), abgerufen 25.10.2026. Die Oberfläche ist englisch.

1. Bei Cloudflare einloggen und deine Domain auswählen.
2. Die Seite **DNS** → **Records** öffnen.
3. Auf **Add record** klicken.
4. Bei **Type** **A** wählen.
5. Bei **Name** `angebot` eintragen. *(ungeprüft: Die Cloudflare-Hilfe nennt die Feldnamen für Name und IP nicht wörtlich.)*
6. Im Feld für die **IPv4-Adresse** die IP-Adresse eintragen. *(ungeprüft, siehe oben)*
7. **Proxy status: ausschalten.** Die Wolke muss **grau** sein („DNS only“), nicht orange („Proxied“). Klick auf den Schalter, bis „DNS only“ dasteht.
8. **TTL** so lassen.
9. Auf **Save** klicken.

**Was du dem Agenten meldest:** „Cloudflare: Eintrag gespeichert, Wolke ist grau.“

**Warum die Wolke für den Start grau sein muss:**

- Dein Server holt sich sein Sicherheitszertifikat (das Schloss im Browser, „HTTPS“) selbst. Das Programm dafür heißt Caddy. Caddy setzt voraus, dass der A-Record auf deinen Server zeigt ([Caddy: Automatic HTTPS](https://caddyserver.com/docs/automatic-https)).
- Mit oranger Wolke zeigt der Name aber nicht mehr auf deinen Server, sondern auf Cloudflare. Laut Cloudflare antwortet das DNS dann mit Cloudflare-Adressen statt mit deiner Server-IP ([Cloudflare: Proxy status](https://developers.cloudflare.com/dns/proxy-status/)).
- Dazu kommt: Caddy leitet Aufrufe ohne Schloss automatisch auf die Version mit Schloss um. Steht Cloudflare auf der Verschlüsselungsstufe „Flexible“, entsteht laut Cloudflare eine Endlosschleife („ERR_TOO_MANY_REDIRECTS“) ([Cloudflare: Too many redirects](https://developers.cloudflare.com/ssl/troubleshooting/too-many-redirects/)).

Ob das Zertifikat mit oranger Wolke im Einzelfall trotzdem klappt, hängt von weiteren Cloudflare-Einstellungen ab. Mit grauer Wolke gibt es diese Fragen nicht. Wenn du den Cloudflare-Schutz später einschalten willst, besprich das mit dem Agenten. Cloudflare nennt als Lösung für die Schleife die Stufe „Full“ oder höher.

---

## Teil D: Prüfen (macht der Agent, du wartest)

### Schritt 2: Warten

DNS-Änderungen brauchen Zeit, bis sie überall angekommen sind. Die Anbieter nennen:

| Anbieter | Angegebene Wartezeit |
|---|---|
| Namecheap | normalerweise ca. 30 Minuten |
| IONOS | sofort, weltweit bis ca. 1 Stunde |
| GoDaddy | meist bis 1 Stunde, im Einzelfall bis 48 Stunden |
| Hostinger, STRATO, united-domains | bis zu 24 Stunden |
| Cloudflare | *in den gelesenen Hilfeseiten keine Angabe* |

Oft geht es viel schneller. Mach in der Zwischenzeit etwas anderes.

### Schritt 3: Prüfen, ob es angekommen ist

> **Agent:** Prüfe nach 10 Minuten zum ersten Mal, danach alle 15 bis 30 Minuten:
>
> - `dig +short A angebot.deine-firma.de` → muss **genau** die Server-IP liefern, nichts anderes.
> - `dig +short AAAA angebot.deine-firma.de` → sollte **leer** sein. Steht dort eine IPv6-Adresse, die nicht zum Server gehört: siehe „Häufige Probleme“.
> - Zum Gegencheck bei einem öffentlichen DNS-Server: `dig +short A angebot.deine-firma.de @1.1.1.1` und `@8.8.8.8`.
> - Vergleich mit dem Ist-Zustand aus Schritt 1: A-Record der Hauptdomain, `www` und MX müssen unverändert sein.
>
> Wenn die IP stimmt, sag dem Nutzer Bescheid und mach mit der Server-Einrichtung weiter (Zertifikat holen). Ohne Terminal geht auch [dnschecker.org](https://dnschecker.org); IONOS empfiehlt diese Seite selbst zur Kontrolle.

**Was du dem Agenten meldest:** nichts, bis er sich meldet. Er sagt dir „Die Adresse ist angekommen“ oder „noch nicht, ich schaue in 30 Minuten wieder“.

---

## Häufige Probleme

| Symptom | Lösung |
|---|---|
| Ich finde den Knopf aus der Anleitung nicht. | Sag dem Agenten, was du auf dem Bildschirm siehst (Menüpunkte vorlesen oder Bildschirmfoto). Anbieter benennen Menüs um. Die Hilfeseite in der Quellenangabe zeigt meist die aktuelle Version. |
| Der Anbieter lässt mich keine DNS-Einträge bearbeiten, oder die Änderung wirkt nie. | Die Nameserver liegen woanders (Teil A, Schritt 1). Der Agent prüft das mit `dig NS`. Eintragen musst du beim Anbieter, der dort genannt wird. GoDaddy und Namecheap schreiben das ausdrücklich in ihre Hilfe. |
| Ich habe `angebot.deine-firma.de` ins Namensfeld getippt. | Ändern auf nur `angebot`. Die Hilfeseiten von Hostinger, IONOS und GoDaddy verlangen ausdrücklich nur das Präfix. Ob ein Anbieter die volle Eingabe still korrigiert, ist *ungeprüft*; der Agent sieht bei der Prüfung, ob der Name stimmt. |
| Nach einer Stunde liefert die Prüfung noch die alte oder keine Adresse. | Bei Hostinger, STRATO und united-domains bis zu 24 Stunden warten, bei GoDaddy bis zu 48 Stunden. Vorher im Anbieter nachsehen, ob der Eintrag wirklich gespeichert ist (er muss in der Liste stehen). |
| Die Prüfung liefert zwei verschiedene IP-Adressen. | Es gibt einen zweiten, alten A-Record für `angebot`. Den alten löschen, den neuen behalten. IONOS beschreibt genau dieses Problem (wechselnde Antworten). |
| Die IP stimmt, aber das Zertifikat (HTTPS) klappt nicht. | 1. Der Agent prüft `dig AAAA angebot.deine-firma.de`. Steht dort eine IPv6-Adresse, die nicht zum Server gehört, diesen AAAA-Eintrag löschen. Grund: Let's Encrypt (die Stelle, die das Zertifikat ausstellt) versucht es zuerst über IPv6 ([Let's Encrypt: IPv6 Support](https://letsencrypt.org/docs/ipv6-support/)). 2. Bei Cloudflare: Wolke grau? 3. Bei Hostinger: Hinweis aus der Hilfe beachten, dass widersprüchliche A- und AAAA-Einträge entfernt werden sollen. |
| Bei Cloudflare: Browser meldet „Zu viele Weiterleitungen“ (ERR_TOO_MANY_REDIRECTS). | Die Wolke ist orange. Auf grau („DNS only“) stellen. Quelle: Cloudflare-Seite zu ERR_TOO_MANY_REDIRECTS. |
| Nach dem Speichern ist meine Hauptwebsite oder E-Mail gestört. | Sofort dem Agenten sagen. Er vergleicht mit dem Ist-Zustand aus Schritt 1. Bei united-domains gibt es den Link **auf Standard setzen** (siehe dort). Im Zweifel den Support des Anbieters anrufen und sagen: „Ich habe einen A-Record für die Subdomain angebot angelegt, seitdem ist X gestört.“ |
| GoDaddy fragt nach einem Code. | Das ist die Zusatzprüfung bei „Domain Protection“. Den Code aus SMS, App oder E-Mail selbst eintippen. Nie dem Agenten geben. |

---

## Quellen (alle abgerufen am 25.10.2026)

- Hostinger: https://www.hostinger.com/support/how-to-use-hostingers-dns-zone-editor/
- Hostinger: https://www.hostinger.com/support/4468886-how-to-manage-a-records-at-hostinger/
- IONOS: https://www.ionos.de/hilfe/domains/ip-adresse-konfigurieren/domain-mit-statischer-ip-adresse-verbinden/
- STRATO: https://www.strato.de/faq/domains/subdomains-anlegen-und-loeschen/
- STRATO: https://www.strato.de/faq/domains/wie-kann-ich-bei-strato-meine-dns-eintraege-verwalten/
- GoDaddy: https://www.godaddy.com/help/add-an-a-record-19238
- GoDaddy: https://www.godaddy.com/help/add-or-edit-an-a-record-42546
- united-domains: https://www.united-domains.de/help/faq-article/ich-betreibe-einen-eigenen-mailserver/
- united-domains: https://www.united-domains.de/help/faq-article/wie-kann-ich-die-united-domains-dns-eintraege-wieder-aktivieren/
- Namecheap: https://www.namecheap.com/support/knowledgebase/article.aspx/319/2237/how-can-i-set-up-an-a-address-record-for-my-domain/
- Cloudflare: https://developers.cloudflare.com/dns/manage-dns-records/how-to/create-dns-records/
- Cloudflare: https://developers.cloudflare.com/dns/proxy-status/
- Cloudflare: https://developers.cloudflare.com/ssl/troubleshooting/too-many-redirects/
- Caddy: https://caddyserver.com/docs/automatic-https
- Let's Encrypt: https://letsencrypt.org/docs/ipv6-support/

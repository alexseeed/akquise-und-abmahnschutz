# 02 – Server bei Hostinger mieten

Damit die persönlichen Seiten für deine Leads im Internet erreichbar sind, brauchst du einen eigenen kleinen Server (ein „VPS“). Du erledigst nur vier Dinge: **kaufen, Ubuntu auswählen, einen API-Schlüssel erzeugen und in eine Datei einfügen.** Den Rest macht dein Agent (Claude Code oder Codex).

Dauer: etwa 15 Minuten. Du brauchst eine E-Mail-Adresse und ein Zahlungsmittel.

> **Drei Regeln, die immer gelten**
> 1. Schreib **niemals** ein Passwort oder den API-Schlüssel in den Chat mit dem Agenten.
> 2. Zahlungsdaten und Passwörter gibst du **nur selbst** auf der Hostinger-Seite ein.
> 3. Wenn etwas anders aussieht als hier beschrieben: Mach ein Bildschirmfoto, schick es dem Agenten und frag nach. Schritte, die mit **(ungeprüft)** markiert sind, konnten wir in der offiziellen Hilfe nicht Klick für Klick bestätigen. Die Beschriftungen können bei dir leicht anders heißen.

---

## Was es kostet

Stand **25.10.2026**, Quelle: <https://www.hostinger.com/de/vps-hosting>

| Tarif | Einstiegspreis | Verlängerung | Leistung |
|---|---|---|---|
| **KVM 1** (reicht für die Seiten) | 5,49 € / Monat | 11,99 € / Monat (für 2 Jahre) | 1 vCPU, 4 GB RAM, 50 GB NVMe, 4 TB Datenvolumen |

- Hostinger schreibt dazu: „Preisangaben ohne Mehrwertsteuer“. Alle Tarife werden **im Voraus** für die gewählte Laufzeit bezahlt; der Monatspreis ist der Gesamtpreis geteilt durch die Monate. Den Einstiegspreis gibt es nur bei der längsten Laufzeit. **Den Endbetrag siehst du im Warenkorb, bevor du bezahlst.**
- Laut Seite: 30 Tage Geld-zurück-Garantie.
- Preise ändern sich oft. Maßgeblich ist, was im Warenkorb steht.

---

## Schritt 1 – Hostinger öffnen und den Tarif KVM 1 wählen

1. Öffne diesen Link: **`<Hostinger-Ref-Link>`**
2. Du siehst eine Seite mit VPS-Tarifen (KVM 1, KVM 2, KVM 4, KVM 8).
3. Klicke bei **KVM 1** auf **„Plan wählen“**.

**Danach siehst du:** den Warenkorb mit „KVM 1“ und einer Auswahl der Laufzeit (z. B. 12 oder 24 Monate).

## Schritt 2 – Laufzeit wählen, Konto anlegen, bezahlen

1. Wähle die Laufzeit. Der Agent empfiehlt keine bestimmte Laufzeit; kürzere Laufzeiten kosten im Monat mehr, längere binden dich länger.
2. Falls angeboten: **Zusatzoptionen** (z. B. tägliche Backups) brauchst du für die Seiten nicht. **(ungeprüft)**
3. Lege ein Hostinger-Konto an (E-Mail und Passwort) oder melde dich an, falls du schon eins hast.
4. Gib deine Zahlungsdaten ein und schließe den Kauf ab.

**Danach siehst du:** eine Bestätigung und meistens direkt den Einrichtungsassistenten für den VPS. Falls nicht: Öffne <https://hpanel.hostinger.com>, klicke links auf **„VPS“** und beim neuen Server auf **„Einrichten“** bzw. **„Setup“**. **(ungeprüft)**

**Dem Agenten schreibst du:** „VPS gekauft.“

## Schritt 3 – VPS einrichten: Standort, Ubuntu 24.04, Root-Passwort  **(ungeprüft)**

Der Einrichtungsassistent fragt mehrere Dinge nacheinander ab. Die Reihenfolge kann bei dir anders sein.

1. **Standort (Rechenzentrum):** Wähle ein Rechenzentrum in **Deutschland**, falls angeboten, sonst eines in der **EU** (z. B. Frankreich, Niederlande, Litauen). Kein Standort außerhalb der EU.
2. **Betriebssystem:** Wähle die Variante **ohne Control Panel**. Sie heißt z. B. „Einfaches Betriebssystem“ / „Plain OS“ / „Nur Betriebssystem“. Dort wählst du **Ubuntu 24.04** (manchmal „Ubuntu 24.04 LTS“).
   - **Nicht** wählen: Varianten mit „Panel“, „CyberPanel“, „cPanel“, „Coolify“, „Docker“, „n8n“ oder Ähnlichem.
3. **Root-Passwort:** Denk dir ein langes Passwort aus und gib es **nur in dieses Hostinger-Feld** ein. Speichere es in deinem Passwort-Manager. Der Agent braucht es **nicht**; schick es ihm nie.
4. **SSH-Schlüssel:** Falls ein Feld dafür erscheint: **leer lassen.** Der Agent hinterlegt seinen eigenen Schlüssel später automatisch.
5. Weitere Fragen (z. B. Malware-Scanner, Hostname): Standard lassen.
6. Klicke auf **„Einrichtung abschließen“** bzw. **„Finish setup“**.

**Danach siehst du:** eine Meldung, dass der Server eingerichtet wird. Das dauert ein paar Minuten. Wenn der Server fertig ist, zeigt die VPS-Übersicht den Status **„Läuft“** bzw. **„Running“** und eine IP-Adresse (z. B. `203.0.113.10`).

**Dem Agenten schreibst du:** „VPS läuft.“ (Die IP darfst du mitschicken, sie ist kein Geheimnis.)

## Schritt 4 – API-Schlüssel erzeugen

Mit dem API-Schlüssel kann der Agent deinen Server einrichten, ohne dass du dich mit Technik beschäftigen musst. Der Schlüssel ist so geheim wie ein Passwort.

Laut offizieller Hostinger-Hilfe geht das so (Quellen unten):

1. Öffne direkt: <https://hpanel.hostinger.com/api>
   - Alternativ im hPanel in der linken Leiste: im Bereich **„Dev“**/Entwickler-Werkzeuge auf **„API“** klicken. **(ungeprüft, die Beschriftung kann abweichen)**
2. Klicke auf **„Neues Token“** bzw. **„Generate new token“** / **„New token“**. (Die offizielle Hilfe nennt beide Beschriftungen.)
3. Gib als Namen ein: `videoseiten`
4. Wähle ein **Ablaufdatum**, z. B. in einem Jahr. Merk dir das Datum: Danach muss ein neuer Schlüssel her (dann wiederholst du Schritt 4 und 5).
5. Klicke auf **„Generate“** bzw. **„Erzeugen“**.
6. Der Schlüssel erscheint (eine lange Zeichenkette). Klicke auf **„Kopieren“** oder markiere ihn komplett und kopiere ihn (Mac: `Cmd + C`, Windows: `Strg + C`).
   - **Wichtig:** Hostinger zeigt den Schlüssel **nur einmal**. Lass die Seite offen, bis Schritt 5 erledigt ist.

**Dem Agenten schreibst du:** „Schlüssel ist kopiert.“ **Nicht den Schlüssel selbst!**

## Schritt 5 – Schlüssel in die Datei `.env` einfügen

1. Der Agent öffnet jetzt die Datei `pfade/videoseiten/.env` in einem einfachen Texteditor. (Gibt es sie noch nicht, legt er sie vorher an.) Darin steht eine Zeile:
   ```
   HOSTINGER_API_TOKEN=
   ```
2. Klicke direkt **hinter das `=`** und füge den Schlüssel ein (Mac: `Cmd + V`, Windows: `Strg + V`). Kein Leerzeichen, keine Anführungszeichen, alles in **einer** Zeile. Fertig sieht es so aus (mit deinem Schlüssel statt `abc…`):
   ```
   HOSTINGER_API_TOKEN=abc123def456…
   ```
3. Speichern (Mac: `Cmd + S`, Windows: `Strg + S`) und den Editor schließen.

**Danach siehst du:** nichts Besonderes. Die Datei bleibt nur auf deinem Rechner und wird nicht ins Git-Repository hochgeladen.

**Dem Agenten schreibst du:** „Gespeichert.“

Ab hier macht der Agent alles Weitere. Du wirst nur noch gefragt, falls deine Domain **nicht** bei Hostinger liegt. Dann hilft dir `anleitungen/03_dns.md`, einen Eintrag bei deinem Domain-Anbieter zu setzen.

---

## Wenn etwas schiefgeht

| Was du siehst / was der Agent meldet | Was zu tun ist |
|---|---|
| „Hostinger lehnt den API-Schlüssel ab“ | Schlüssel abgelaufen oder unvollständig kopiert. Schritt 4 und 5 wiederholen und den alten Eintrag in `.env` ersetzen. |
| Du hast den Schlüssel aus Versehen in den Chat geschrieben | Auf <https://hpanel.hostinger.com/api> den Schlüssel löschen, einen neuen erzeugen und Schritt 5 wiederholen. |
| „Kein VPS in diesem Konto“ | Kauf noch nicht abgeschlossen oder Server noch in Arbeit. 10 Minuten warten. Hast du mehrere Hostinger-Konten, muss der Schlüssel aus dem Konto mit dem VPS stammen. |
| „noch nicht eingerichtet“ | Schritt 3 ist nicht abgeschlossen. Im hPanel bei VPS auf „Einrichten“ klicken. |
| „Betriebssystem ist …, erwartet wird Ubuntu 24.04“ | Im hPanel beim VPS **„Betriebssystem & Panel“** → **„Betriebssystem ändern“** öffnen und Ubuntu 24.04 ohne Panel wählen. **Achtung: Das löscht alles auf dem Server.** Ist der Server neu, ist das kein Problem. **(ungeprüft)** |

---

## Für den Agenten

Werkzeug: `python3 pfade/videoseiten/werkzeuge/hostinger.py` (Python ≥ 3.10, nur Standardbibliothek, braucht lokal `ssh`, `scp`, `ssh-keygen` und `tar`). Exit-Code 0 = ok, 1 = Fehler, 2 = Nutzer muss etwas tun. Fehler kommen immer als `FEHLER:` und `WAS TUN:`.

1. Vor Schritt 5: `pfade/videoseiten/.env` mit der Zeile `HOSTINGER_API_TOKEN=` anlegen, falls die Datei fehlt (vorhandene Zeilen nicht anfassen), und im Editor öffnen (`open -e` auf dem Mac, `notepad` auf Windows). Den Inhalt nie ausgeben, nie `cat .env`.
2. `pruefen`: Zeigt VPS-ID, IP, Status, Betriebssystem, Standort. Erwartet: Status „läuft“ und Ubuntu 24.04.
3. `schluessel --vm <ID>`: Legt `arbeit/ssh/id_ed25519` an, hinterlegt den öffentlichen Teil bei Hostinger und testet SSH.
4. `dns --domain <kunde.de> --name <angebot> --ip <IP>`: Setzt den A-Record, wenn die Domain bei Hostinger liegt. Exit 2 bedeutet: Der Nutzer setzt den Eintrag selbst, mit `anleitungen/03_dns.md`.
5. `einrichten --vm <ID> --domain <angebot.kunde.de>`: Richtet Caddy, Firewall, Dienst und Aufräum-Cron ein und kann wiederholt werden. Ist `SKAEL_WEBHOOK_SECRET` (bzw. `MELDUNG_URL`) in `.env` gesetzt, wird es nach `/etc/seiten.env` übertragen.
6. Seiten lokal mit `server/generator.py --ziel <ordner>` erzeugen, dann `hochladen --vm <ID> --seiten <ordner>`. Seiten, denen widersprochen wurde, und abgelaufene Seiten werden übersprungen.
7. `status --vm <ID> --domain <angebot.kunde.de>`: Prüft DNS, HTTPS, `X-Robots-Tag`, `/api/m` sowie die Dienste `seiten-server` und `caddy`.
8. Webhook-Geheimnis erst später aus Skael? Der Nutzer trägt es in `.env` ein, danach `geheimnis --vm <ID>`.

---

## Quellen (abgerufen am 25.10.2026)

- Preise KVM 1: <https://www.hostinger.com/de/vps-hosting>
- API-Schlüssel erzeugen: <https://docs.hostinger.com/account/security.md> (Abschnitt „API tokens“: hPanel → API → „Generate new token“, Name, kopieren, „nur einmal angezeigt“) und <https://www.hostinger.com/support/10840865-what-is-hostinger-api/> (Seitenleiste „Dev“ → „API“ → „API tokens“ → „New token“, Name und Ablaufdatum, „Generate“; aktualisiert 07.10.2026)
- API-Grundlagen (Bearer-Token, Basis-URL, 90 Anfragen/Minute): <https://docs.hostinger.com/api-reference/overview.md>
- Betriebssystem wechseln („OS & Panel“ → „Change OS“): <https://www.hostinger.com/support/9901438-how-to-set-up-ubuntu-remote-desktop-hostinger-vps/>
- Einrichtungsassistent (Standort, „Plain OS“, Root-Passwort): keine offizielle Schritt-für-Schritt-Quelle gefunden, daher **ungeprüft**.

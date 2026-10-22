# Weitergabe an Dritte

Was mitgeht, was besser nicht, und was der Empfänger tun muss.

---

## 1. Was der Empfänger braucht

**Technisch:**

* Python **3.10 oder neuer** (`python3 --version`). Keine Bibliotheken zu installieren —
  der Scraper nutzt ausschließlich die Standardbibliothek.
* `sqlite3` auf der Kommandozeile, nur für die Kontroll-Abfragen im Dry-Run
  (auf macOS und den meisten Linux-Systemen vorinstalliert; optional).

**Zugänge — muss er selbst beschaffen:**

| Zugang | Wofür | Pflicht |
|---|---|---|
| Skael API Key | alle Scraping- und Anreicherungs-Endpunkte, https://api.skael.de | ✅ |
| OpenAI API Key | die vier KI-Schritte | ✅ |
| Findymail API Key | Fallback-Mailfinder | optional |

**Vorwissen:** keins. `CLAUDE.md` führt Claude Code durch die Einrichtung,
`docs/00_ANLEITUNG.md` führt den Menschen durch den Ablauf.

---

## 2. Ablauf beim Empfänger

1. Ordner entpacken, in Claude Code öffnen (oder `claude` im Ordner starten).
2. `CLAUDE.md` wird automatisch gelesen — Claude Code kennt danach Aufbau, Befehle,
   Konventionen und Fallstricke.
3. Sagen: *„Richte den Scraper ein"* → Claude legt `.env` aus `.env.example` an und
   fragt die Keys ab.
4. `python3 -m scraper doctor` bestätigt, dass alles steht.
5. Sagen: *„Ich will [Zielgruppe] scrapen"* → Claude geht Runde 0 und die drei
   ICP-Runden durch, baut den Prompt und fährt Dry-Run und Vollstart.

Ohne Claude Code funktioniert derselbe Weg über `docs/00_ANLEITUNG.md` von Hand.

---

## 3. Der Skill

Dieser Ordner ist Teil des Claude-Skills `lead-scraper` (Pfad „Google Maps“). Im Gesamtpaket
liegt der Skill unter `skills/lead-scraper.zip` zum Hochladen (Claude → Einstellungen →
Funktionen → Skills). Ohne Skill reicht `CLAUDE.md`: Claude Code liest sie beim Öffnen des
Ordners und weiß, wie es weitergeht.

---

## 4. Vor einer Weitergabe

`.env`, `data/` und `exports/` nie mitgeben: Sie enthalten eigene Schlüssel bzw. gescrapte
Firmen- und Personendaten. Alle drei stehen in `.gitignore`.

Prüfen, dass kein Schlüssel durchgerutscht ist:

```bash
grep -rIn "eak_[A-Za-z0-9]\{8,\}\|sk-[A-Za-z0-9_-]\{20,\}" . \
  | grep -v "eak_\.\.\.\|eak_…\|eak_dein_key\|sk-\.\.\.\|sk-dein_key"
```

Keine Ausgabe = keine echten Keys im Ordner.

---

## 5. Was der Empfänger anpassen sollte

| Punkt | Warum |
|---|---|
| `EXCLUDED_TLDS` in `.env` | Default `.fr,.nl,.it` — passt nur für DACH-Kampagnen |
| `CITIES_LIMIT` | `5000` kappt Deutschland bei ~7.600 Orten |
| `DO_PERSONALISIERUNG` / `DO_VIDEO_TITLE` | beide `true` — nur sinnvoll bei Video-Outreach |
| `MAX_CONCURRENCY` / `SKAEL_RATE_LIMIT_PER_SEC` | je nach Skael-Tarif |
| Beispiel-ICP-Prompt | `prompts/icp_beispiel_metallbau.txt` ist ein Muster, kein Standard |

---

## 6. Rechtliches — kurz

Der Scraper sammelt Geschäftskontaktdaten aus öffentlichen Quellen (Google Maps,
Impressen) und bereitet sie für Kaltakquise auf. Das ist in der EU nicht
automatisch zulässig.

Der Empfänger sollte vor dem ersten Versand klären:

* **DSGVO:** Rechtsgrundlage für die Verarbeitung (i. d. R. berechtigtes Interesse
  nach Art. 6 Abs. 1 lit. f), Informationspflicht nach Art. 14, Löschkonzept
* **UWG § 7:** E-Mail-Werbung an Unternehmen ohne vorherige Einwilligung ist in
  Deutschland grundsätzlich unzulässig; die Ausnahmen sind eng
* **Nutzungsbedingungen** der eingesetzten APIs
* **Community-Sperrliste:** Firmen aus `5_gesperrt_…csv` nie anschreiben. Kommt trotzdem eine
  Abmahnung, hilft der Skill `abmahnung-werbemail-abwehr` und meldet den Abmahner an die Liste.

Das ist keine Rechtsberatung — bei ernsthafter Nutzung im Zweifel anwaltlich prüfen lassen.

# Learnings aus dem ersten echten Videoseiten-Lauf (Oktober 2026)

**Zweck:** Was beim ersten echten Durchlauf (ein Lead, ein Skael-Video, eine Seite im Branding des Absenders) schiefging und wie es jetzt geregelt ist. So läuft der nächste Aufbau ohne dieselben Umwege.
**Für wen:** KI-Modelle und Betreiber, die `pfade/videoseiten/` für einen Nutzer einrichten.
**Verwandt:** `16_videoseiten.md` · `pfade/videoseiten/ABLAUF.md` · `pfade/videoseiten/anleitungen/01_skael-video-aufnehmen.md` · `pfade/videoseiten/anleitungen/05_datenschutzerklaerung.md`

Stand: Oktober 2026. Alle Punkte sind im Code oder in den Anleitungen umgesetzt. Diese Datei erklärt das Warum.

---

## 1. Skael

| Beobachtung | Folge | Jetzt geregelt |
|---|---|---|
| Viele Kampagnen bestehen nur aus einer Facecam über dem Website-Screenshot, ohne Bildschirmaufnahme. | `videos.py` hielt die Kampagne für leer und konnte keine Kosten nennen. | Facecam allein zählt als Aufnahme. Kosten richten sich nach ihrer Länge. |
| Neue Kampagnen haben die Player-Farbe Lila (`#6366f1`). | Auf der Seite wirkt der Player fremd. | `videos.py pruefen` warnt. Anleitung 01, Schritt 3 lässt die Markenfarbe eintragen. |
| Cloudflare vor Skael lehnt den Standard-User-Agent von Python mit 403 ab. | Vorschaubilder fehlten, die Seite zeigte das Standardbild. | Der Generator sendet einen eigenen User-Agent. |
| Skael liefert Vorschaubilder als JPEG unter einer `.png`-Adresse. | Falsche Dateiendung. | Die Endung kommt aus dem Content-Type. |
| `warten` kennt kein `--leads`. | Abbruch mit Fehlermeldung. | Aufruf: `warten --kampagne <id>`. |

Kosten des Laufs: ein Video bis 2 Minuten = 110 Credits (0,11 €).

## 2. Video-Start auf der Seite

- **Ein Klick muss reichen.** Der Skael-Player nimmt den Play-Befehl erst an, wenn er `skaelreach:ready` gemeldet hat. Wird vorher gesendet, zeigt er seinen eigenen Play-Knopf und der Besucher muss zweimal klicken.
- **Schnell laden.** Browser erlauben Ton nur kurz nach dem Klick (etwa 5 Sekunden). Der Player lädt deshalb sofort beim Klick, parallel zur Zoom-Animation. Gemessen: rund 1 Sekunde vom Klick bis zum Abspielen, vorher über 3 Sekunden.
- **Prüfen ohne Bildschirm:** Im versteckten Browserfenster bleiben Screenshots des laufenden Videos schwarz. Ob es läuft, zeigen die Nachrichten des Players (`skaelreach:ready`, `skaelreach:playing`), nicht der Screenshot.

## 3. Seite gestalten

- **Keine freigegebenen Kundenstimmen?** Dann keine Zitate erfinden. Belegte Ergebnisse ohne Zitat zeigen und `stimmen_hinweis` auf die Quelle der Zahlen ändern (`ABLAUF.md`, Teil A).
- **Kein Testimonial-Video?** Ein vorhandenes Video des Nutzers (z. B. Erklärvideo von der Website) kann als `video_datei` in einer Ergebniskarte laufen. Es liegt dann auf dem eigenen Server und lädt nichts von Dritten.
- **Lange Wörter** in Überschriften und Angebotstiteln brachen mitten im Wort um. Jetzt mit automatischer Silbentrennung.
- **Kontrast:** Textfarbe für Akzente leitet sich aus der kontrastgeprüften Akzentfarbe ab. Helle Markenfarben (z. B. Lime) bleiben lesbar.

## 4. Texte im Datenschutz-Block

Der Block „Woher wir Ihre Daten haben“ soll informieren, ohne Angriffsfläche zu bieten. Festgelegt nach dem Testlauf:

- **Quelle allgemein halten:** „Öffentlich zugängliche Angaben, insbesondere das Impressum der Firma, sowie weitere öffentlich zugängliche Quellen.“ Nicht behaupten, die E-Mail-Adresse stamme aus dem Impressum. Das stimmt nicht immer.
- **Suchweg nie nennen** (z. B. „Google-Maps-Suche nach …“). `quelle` und `quelle_url` bleiben als interner Nachweis im Lead und werden nicht mehr in die Seite geschrieben, auch nicht in den Quelltext.
- **Keine Rechte-Aufzählung und kein IP-Satz auf der Seite.** Beides steht in der Datenschutzerklärung, auf die die Seite verlinkt. Der Knopf „Keine weiteren Nachrichten – Datenlöschung vornehmen“ bleibt.
- Ob der Verweis auf die Datenschutzerklärung für Art. 14 DSGVO genügt, steht als offener Punkt in Anleitung 05. Kein Rechtsrat.

## 5. Seiten erneut erzeugen

Nach einer Textänderung wird der Generator erneut ausgeführt. Früher bekam dabei jeder Lead eine neue Adresse, und schon verschickte Links wären ins Leere gelaufen. Jetzt behält eine vorhandene Seite im `--ziel`-Ordner ihre Adresse und ihr Löschdatum. Seiten mit Datenlöschung überspringt `hostinger.py hochladen` weiterhin.

## 6. Vorschau ohne eigenen Server

Für einen ersten Blick vor dem Hostinger-Server lässt sich der `seiten`-Ordner auch kurz auf einem statischen Hoster zeigen. Dabei gilt:

- `ergebnis.json` und `.meta.json` nicht mit hochladen (interne Daten).
- `noindex` setzen. Die Vorlage hat das Meta-Tag schon, zusätzlich den Header `X-Robots-Tag`.
- Nur zum Ansehen, nicht für den Versand. Datenlöschung und Zählung brauchen den eigenen Server.
- Nach einem neuen Upload zeigt der Browser oft noch die alte Fassung aus dem Cache. Vor dem Urteil neu laden.

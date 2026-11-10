# Videoseiten

Nach dem Scrape: ein persönliches Video je Lead (Skael) und eine eigene Landingpage im Branding des Nutzers, auf seinem eigenen Server (Hostinger), plus Versandliste fürs Mailtool.

**Ablauf für den Agenten:** `ABLAUF.md` · **Wissen und Rückfragen:** `../../wissen/16_videoseiten.md`

```
pfade/videoseiten/
├── ABLAUF.md        Teile A–F: Seite, Videos, Server, Hochladen, Versand, Betrieb
├── vorlage/         neutrale Landingpage (wird je Nutzer nach arbeit/<kampagne>/seite kopiert)
├── server/          generator.py (Seite je Lead), server.py (Messung, Datenlöschung, Webhook),
│                    Caddyfile, seiten-server.service, einrichten.sh
├── werkzeuge/       videos.py (Skael), branding.py (Website → Farben, Schriften, Logo),
│                    hostinger.py (Server per API), versandliste.py (Links, Datenlöschungen)
├── anleitungen/     Schritt-für-Schritt für alles, was der Nutzer selbst tun muss
├── tests/           Offline-Tests: python3 -m unittest discover -s tests -v
├── arbeit/          je Kampagne: Seite, Branding, Video-Stand, erzeugte Seiten (nie weitergeben)
└── .env.example     Zugänge (Skael, Hostinger, Webhook-Geheimnis)
```

Alles läuft mit Python ab 3.10 ohne zusätzliche Pakete, in Claude Code und in Codex gleich.

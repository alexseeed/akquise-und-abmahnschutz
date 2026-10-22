#!/usr/bin/env python3
"""Netzwerk-Mitschnitt einer Website in drei Szenarien (jeweils frisches, leeres Browserprofil).

A  Startseite aufrufen, warten, keine Interaktion
B  Startseite, Klick auf die Ablehnen-Schaltfläche, danach Startseite und Folgeseiten
C  erste angegebene Unterseite direkt, keine Interaktion (nur wenn Unterseiten angegeben)

Aufruf:
  python3 sicherung_netzwerk.py https://www.domain.de "Ablehnen" ausgabe/01_netzwerk /kontakt /datenschutz

Ergebnis je Szenario: <name>.har, <name>_requests.csv, Screenshots, <name>_zustand.json
sowie netzwerk_meta.json (Zeiten, Browser, Ausgangs-IP).
"""
import argparse, csv, datetime, json, os, sys, urllib.request
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Playwright fehlt: pip install playwright && playwright install chromium")


def jetzt():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def ausgangs_ip():
    try:
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=10) as r:
            d = json.loads(r.read().decode())
            return {k: d.get(k) for k in ("ip", "country", "region", "city", "org")}
    except Exception as e:
        return {"fehler": str(e)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("basis_url")
    p.add_argument("ablehnen_text", help='Beschriftung der Ablehnen-Schaltfläche, z. B. "Ablehnen"')
    p.add_argument("ausgabe")
    p.add_argument("seiten", nargs="*", help="Pfade der Folgeseiten, z. B. /kontakt")
    p.add_argument("--ignore-https-errors", action="store_true", help="nur bei TLS-terminierendem Proxy; im Protokoll vermerken")
    p.add_argument("--warte-start", type=int, default=8000)
    p.add_argument("--warte-seite", type=int, default=6000)
    a = p.parse_args()

    base = a.basis_url.rstrip("/")
    os.makedirs(a.ausgabe, exist_ok=True)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    meta = {"start_utc": jetzt(), "basis_url": base, "ablehnen_text": a.ablehnen_text, "seiten": a.seiten,
            "ignore_https_errors": a.ignore_https_errors, "proxy_gesetzt": bool(proxy), "ausgangs_ip": ausgangs_ip(),
            "szenarien": {}}

    def szenario(pw, name, ablehnen, start="/"):
        b = pw.chromium.launch(proxy={"server": proxy} if proxy else None)
        meta["browser"] = f"Chromium {b.version} (headless, Playwright)"
        c = b.new_context(locale="de-DE", timezone_id="Europe/Berlin", viewport={"width": 1440, "height": 900},
                          ignore_https_errors=a.ignore_https_errors,
                          record_har_path=f"{a.ausgabe}/{name}.har", record_har_content="embed")
        pg, log, phase = c.new_page(), [], ["vor_interaktion"]
        pg.on("request", lambda r: log.append([jetzt(), phase[0], pg.url, urlparse(r.url).netloc, r.method,
                                               r.resource_type, r.url]))
        info = {"start_utc": jetzt()}
        pg.goto(base + start, wait_until="load", timeout=60000)
        pg.wait_for_timeout(a.warte_start)
        pg.screenshot(path=f"{a.ausgabe}/{name}_1_erstaufruf.png")
        if ablehnen:
            knopf = pg.get_by_role("button", name=a.ablehnen_text).first
            if knopf.count() == 0:
                knopf = pg.get_by_text(a.ablehnen_text, exact=True).first
            info["klick_ablehnen_utc"] = jetzt()
            knopf.click(timeout=15000)
            pg.wait_for_timeout(2500)
            phase[0] = "nach_ablehnen"
            pg.screenshot(path=f"{a.ausgabe}/{name}_2_nach_ablehnen.png")
            for i, s in enumerate(["/"] + a.seiten, 1):
                phase[0] = f"nach_ablehnen {s}"
                pg.goto(base + s, wait_until="load", timeout=60000)
                pg.wait_for_timeout(a.warte_seite)
                pg.screenshot(path=f"{a.ausgabe}/{name}_3_{i}_{s.strip('/').replace('/', '_') or 'start'}.png")
        zustand = {"cookies": c.cookies(),
                   "localStorage": pg.evaluate("Object.assign({}, localStorage)"),
                   "dataLayer": pg.evaluate("JSON.parse(JSON.stringify(window.dataLayer || []))")}
        with open(f"{a.ausgabe}/{name}_zustand.json", "w", encoding="utf-8") as f:
            json.dump(zustand, f, ensure_ascii=False, indent=1, default=str)
        with open(f"{a.ausgabe}/{name}_requests.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["zeit_utc", "phase", "seite", "host", "methode", "typ", "url"])
            w.writerows(log)
        info["ende_utc"] = jetzt()
        info["anfragen"] = len(log)
        meta["szenarien"][name] = info
        c.close(); b.close()
        print(f"{name}: {len(log)} Anfragen gesichert")

    with sync_playwright() as pw:
        szenario(pw, "A_ohne_einwilligung", False)
        szenario(pw, "B_nach_ablehnen", True)
        if a.seiten:
            szenario(pw, "C_unterseite_ohne_einwilligung", False, a.seiten[0])

    meta["ende_utc"] = jetzt()
    with open(f"{a.ausgabe}/netzwerk_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

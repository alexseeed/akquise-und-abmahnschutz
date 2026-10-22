#!/usr/bin/env python3
"""Sichert Seiteninhalte: je Seite Roh-HTML (Serverauslieferung + Header), Ganzseiten-Screenshot,
PDF mit URL und Sicherungszeit in der Kopfzeile und MHTML-Webarchiv. Downloads zusätzlich per curl.

Aufruf:
  python3 sicherung_seiten.py https://www.domain.de "Ablehnen" ausgabe/02_seiteninhalte \
      /datenschutz /impressum /agb --download https://www.domain.de/formular.pdf
"""
import argparse, datetime, json, os, re, subprocess, sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Playwright fehlt: pip install playwright && playwright install chromium")


def jetzt():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def dateiname(pfad):
    n = re.sub(r"[^A-Za-z0-9_-]+", "_", pfad.strip("/")) or "start"
    return n[:80]


def curl(url, ziel, header, unsicher):
    cmd = ["curl", "-sS", "-L", "--max-time", "60", "-D", header, "-o", ziel, "-A", "Mozilla/5.0 (Beweissicherung)", url]
    if unsicher:
        cmd.insert(1, "-k")
    subprocess.run(cmd, check=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("basis_url"); p.add_argument("ablehnen_text"); p.add_argument("ausgabe")
    p.add_argument("seiten", nargs="*")
    p.add_argument("--download", action="append", default=[])
    p.add_argument("--ignore-https-errors", action="store_true")
    a = p.parse_args()

    base = a.basis_url.rstrip("/")
    os.makedirs(a.ausgabe, exist_ok=True)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    index = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(proxy={"server": proxy} if proxy else None)
        c = b.new_context(locale="de-DE", timezone_id="Europe/Berlin", viewport={"width": 1440, "height": 900},
                          ignore_https_errors=a.ignore_https_errors)
        pg = c.new_page()
        pg.goto(base + "/", wait_until="load", timeout=60000)
        pg.wait_for_timeout(4000)
        try:
            pg.get_by_role("button", name=a.ablehnen_text).first.click(timeout=10000)
            banner = "mit „%s“ geschlossen" % a.ablehnen_text
        except Exception:
            banner = "nicht geschlossen (Schaltfläche nicht gefunden)"
        pg.wait_for_timeout(1500)
        cdp = c.new_cdp_session(pg)
        for nr, pfad in enumerate(a.seiten or ["/"], 1):
            url = base + pfad
            stem = f"{a.ausgabe}/{nr:02d}_{dateiname(pfad)}"
            t0 = jetzt()
            curl(url, stem + "_server_roh.html", stem + "_server_header.txt", a.ignore_https_errors)
            pg.goto(url, wait_until="load", timeout=60000)
            pg.wait_for_timeout(4000)
            pg.evaluate("""async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) {
                window.scrollTo(0, y); await new Promise(r => setTimeout(r, 150)); } window.scrollTo(0, 0); }""")
            pg.wait_for_timeout(1500)
            pg.screenshot(path=stem + "_screenshot_ganzseite.png", full_page=True)
            pg.emulate_media(media="screen")
            pg.pdf(path=stem + "_seite.pdf", format="A4", print_background=True, display_header_footer=True,
                   header_template=f'<div style="font-size:7px;width:100%;padding:0 10mm;">{url} | gesichert {t0} UTC</div>',
                   footer_template='<div style="font-size:7px;width:100%;text-align:right;padding:0 10mm;">Seite <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
                   margin={"top": "14mm", "bottom": "12mm", "left": "8mm", "right": "8mm"})
            with open(stem + "_webarchiv.mhtml", "w", encoding="utf-8") as f:
                f.write(cdp.send("Page.captureSnapshot", {"format": "mhtml"})["data"])
            index.append({"nr": f"{nr:02d}", "url": url, "titel": pg.title(), "zeit_utc": t0, "praefix": os.path.basename(stem)})
            print(f"{nr:02d} {url} gesichert")
        b.close()
    start = len(index)
    for i, url in enumerate(a.download, start + 1):
        name = f"{i:02d}_download_{dateiname(url.split('/')[-1])}"
        t0 = jetzt()
        kopf = f"{a.ausgabe}/{name}_server_header.txt"
        curl(url, f"{a.ausgabe}/{name}", kopf, a.ignore_https_errors)
        typ = open(kopf, encoding="latin-1").read().lower() if os.path.exists(kopf) else ""
        for mime, endung in (("application/pdf", ".pdf"), ("image/png", ".png"), ("image/jpeg", ".jpg"),
                             ("application/vnd.openxmlformats-officedocument.wordprocessingml", ".docx"), ("text/html", ".html")):
            if "content-type: " + mime in typ and not name.endswith(endung):
                os.rename(f"{a.ausgabe}/{name}", f"{a.ausgabe}/{name}{endung}")
                name += endung
                break
        index.append({"nr": f"{i:02d}", "url": url, "titel": "Download", "zeit_utc": t0, "praefix": name})
        print(f"{i:02d} {url} heruntergeladen")
    with open(f"{a.ausgabe}/seiten_index.json", "w", encoding="utf-8") as f:
        json.dump({"cookie_banner": banner, "seiten": index}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wertet den Netzwerk-Mitschnitt aus sicherung_netzwerk.py aus.

- ordnet Drittserver über listen/drittanbieter.csv zu (unbekannte werden markiert)
- listet Drittserver je Szenario/Phase mit erster Anfrage und CSV-Zeile
- erkennt das Consent-Tool über listen/consent-tools.csv und zeigt den gespeicherten Status

Aufruf: python3 auswertung.py <ordner 01_netzwerk> --eigene-domain abmahner.de > auswertung.md
"""
import argparse, csv, glob, json, os, re
from urllib.parse import urlparse

HIER = os.path.dirname(os.path.abspath(__file__))
LISTEN = os.path.join(HIER, "..", "listen")


def lade_anbieter():
    with open(os.path.join(LISTEN, "drittanbieter.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def lade_cmp():
    with open(os.path.join(LISTEN, "consent-tools.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def zuordnen(url, anbieter):
    u = urlparse(url)
    host, pfad = u.netloc.lower(), u.path
    bester = None
    for e in anbieter:
        muster = e["host_endung"].lower()
        if "/" in muster:
            mh, mp = muster.split("/", 1)
            ok = (host == mh or host.endswith("." + mh)) and pfad.lstrip("/").startswith(mp)
        else:
            ok = host == muster or host.endswith("." + muster)
        if ok and (bester is None or len(muster) > len(bester["host_endung"])):
            bester = e
    return bester


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ordner")
    p.add_argument("--eigene-domain", required=True)
    a = p.parse_args()
    eigen = a.eigene_domain.lower().removeprefix("www.")
    anbieter, cmps = lade_anbieter(), lade_cmp()

    print(f"# Auswertung Netzwerk-Mitschnitt – {eigen}\n")
    meta_pfad = os.path.join(a.ordner, "netzwerk_meta.json")
    if os.path.exists(meta_pfad):
        m = json.load(open(meta_pfad, encoding="utf-8"))
        ip = m.get("ausgangs_ip", {})
        print(f"Zeitraum (UTC): {m.get('start_utc')} bis {m.get('ende_utc')}  ")
        print(f"Browser: {m.get('browser')}  ")
        print(f"Ausgangs-IP: {ip.get('ip')} ({ip.get('country')}, {ip.get('org')})  ")
        print(f"TLS-Fehler ignoriert: {'ja' if m.get('ignore_https_errors') else 'nein'}\n")

    unbekannt = set()
    alle_hosts = set()
    for csv_pfad in sorted(glob.glob(os.path.join(a.ordner, "*_requests.csv"))):
        name = os.path.basename(csv_pfad).replace("_requests.csv", "")
        rows = list(csv.DictReader(open(csv_pfad, encoding="utf-8"), delimiter=";"))
        print(f"## Szenario {name}\n")
        phasen = {}
        for zeile, r in enumerate(rows, start=2):
            host = (r["host"] or "").lower()
            if not host or host == eigen or host.endswith("." + eigen):
                continue
            alle_hosts.add(host)
            ph = phasen.setdefault(r["phase"], {})
            if host not in ph:
                ph[host] = (r["zeit_utc"][11:23], zeile, r["url"])
        for phase, hosts in phasen.items():
            print(f"### Phase: {phase}\n")
            print("| Drittserver | Anbieter | Kategorie | USA | Einwilligung typisch | erste Anfrage (UTC) | Beleg |")
            print("|---|---|---|---|---|---|---|")
            for host, (zeit, zeile, url) in sorted(hosts.items(), key=lambda x: x[1][0]):
                e = zuordnen(url, anbieter)
                if e is None:
                    unbekannt.add(host)
                    print(f"| {host} | **unbekannt – zuordnen** | | | | {zeit} | {os.path.basename(csv_pfad)} Z. {zeile} |")
                else:
                    print(f"| {host} | {e['anbieter']} | {e['kategorie']} | {e['drittland_usa']} | "
                          f"{e['einwilligung_typisch_noetig']} | {zeit} | {os.path.basename(csv_pfad)} Z. {zeile} |")
            print()
        collect = [r["url"] for r in rows if re.search(r"/(g/)?collect\b|facebook\.com/tr|px\.ads\.linkedin", r["url"])]
        print(f"Messaufrufe (Analytics/Pixel) beobachtet: {len(collect)}\n")

        zpfad = os.path.join(a.ordner, f"{name}_zustand.json")
        if os.path.exists(zpfad):
            z = json.load(open(zpfad, encoding="utf-8"))
            ls = z.get("localStorage", {}) or {}
            cookies = {c["name"]: c.get("value", "") for c in z.get("cookies", [])}
            gefunden = False
            for c in cmps:
                hinweis_host = c["erkennung_host_oder_skript"].split(" ")[0].split("/")[0]
                if hinweis_host and "." in hinweis_host and not any(h.endswith(hinweis_host) for h in alle_hosts):
                    continue
                keys = [k.strip().rstrip("*").split(" ")[0] for k in re.split(r"[,/]| bzw\. |\(", c["schluessel"]) if k.strip()]
                treffer = {}
                for k in keys:
                    if not k or len(k) < 3:
                        continue
                    for quelle, d in (("localStorage", ls), ("Cookie", cookies)):
                        for name_k, wert in d.items():
                            if name_k.startswith(k):
                                treffer[f"{quelle}:{name_k}"] = str(wert)[:400]
                if treffer:
                    gefunden = True
                    print(f"**Consent-Tool erkannt: {c['tool']}** (Ablehnung erkennbar an: {c['ablehnung_erkennbar_an']})\n")
                    for k, v in treffer.items():
                        print(f"- `{k}` = `{v}`")
                    print()
            dl = [d for d in z.get("dataLayer", []) if isinstance(d, dict) and
                  (d.get("0") == "consent" or "consentStateChanged" in str(d.get("event", "")))]
            for d in dl:
                print(f"- dataLayer: `{json.dumps(d, ensure_ascii=False)[:400]}`")
            if not gefunden and not dl:
                print("Kein Consent-Status gefunden (Szenario ohne Interaktion oder unbekanntes Tool).")
            print()

    if unbekannt:
        print("## Nicht zugeordnete Drittserver\n")
        print("Per Websuche zuordnen und ggf. dem Skill-Betreiber zur Aufnahme in listen/drittanbieter.csv melden:\n")
        for h in sorted(unbekannt):
            print(f"- {h}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Gleicht eine beliebige Leadliste (CSV) mit der Community-Sperrliste ab.

    python3 werkzeuge/sperrliste_abgleich.py liste.csv [--spalten "E-Mail,Website"]

Schreibt neben die Liste:
    <liste>_bereinigt.csv   → für die Ansprache
    <liste>_gesperrt.csv    → nie anschreiben (mit Spalte „Sperrgrund“)

Abgeglichen werden alle Spalten, deren Name nach E-Mail, Website, Domain oder URL aussieht
(Amazon-Storefront-Links ausgenommen), oder die mit --spalten genannten. Eine gesperrte Domain
gilt mitsamt allen Subdomains und E-Mail-Adressen.

Die Liste wird online geladen (SPERRLISTE_URL, Standard unten) und als Kopie in
~/.cache/werbemail-sperrliste.txt abgelegt. Offline wird die Kopie verwendet. Gibt es keine,
bricht das Skript ab – außer mit --ohne-liste (dann wird nichts abgeglichen, nur gewarnt).

Nur Python-Standardbibliothek.
"""
import argparse, csv, os, re, sys, urllib.error, urllib.request
from datetime import datetime
from pathlib import Path

STANDARD_URL = "https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt"
CACHE = Path.home() / ".cache" / "werbemail-sperrliste.txt"
SPALTEN_MUSTER = re.compile(r"mail|website|webseite|domain|url|homepage", re.I)
AUSNAHMEN = re.compile(r"storefront|amazon|linkedin|maps|bild|image|logo", re.I)


def norm_domain(wert):
    d = str(wert or "").strip().lower()
    if not d or " " in d.strip():
        return ""
    if "@" in d:
        d = d.rsplit("@", 1)[1]
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split("?")[0].split("#")[0].split(":")[0].rstrip(".")
    d = re.sub(r"^www\d?\.", "", d)
    return d if "." in d else ""


def treffer(domain, sperre):
    teile = domain.split(".")
    for i in range(len(teile) - 1):
        if ".".join(teile[i:]) in sperre:
            return ".".join(teile[i:])
    return None


def parse(text):
    return {z.strip().lower() for z in text.splitlines() if z.strip() and not z.lstrip().startswith("#")}


# shortcut: vier identische Kopien (zwei Pfade, zwei Werkzeuge), weil es kein gemeinsames Paket gibt; zusammenlegen, sobald es eines gibt
_ZAHL_TELEFON_ZEICHEN = frozenset("0123456789+-().,/ ")


def _ist_zahl_oder_telefon(text: str) -> bool:
    """Reine Zahl oder Telefonnummer (z. B. -12,5 oder +41 (0)44 …): kein Buchstabe, kein =, kein Rechenzeichen innen."""
    if not any(ch.isdigit() for ch in text):
        return False
    if any(ch not in _ZAHL_TELEFON_ZEICHEN for ch in text):
        return False
    rest = text[1:]
    if not rest or rest[0] in "+-" or "+" in rest:
        return False
    return text[0] == "+" or "-" not in rest  # Minus innen nur bei +… (Telefon), sonst Ausdruck wie -2-3


def csv_zelle(wert) -> str:
    """Macht eine Datenzelle formelsicher: führende = + - @ Tab CR neutralisieren, Zahlen/Telefone bleiben."""
    if wert is None:
        return ""
    text = wert if isinstance(wert, str) else str(wert)
    if not text or text[0] not in "=+-@\t\r":
        return text
    if text[0] in "+-" and _ist_zahl_oder_telefon(text):
        return text
    return "'" + text


def lade(url, ohne_liste):
    fehler = ""
    if url and "OWNER" not in url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sperrliste-abgleich", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
            try:  # the local copy is a convenience: a read-only home folder must not stop the check
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                CACHE.write_text(text, encoding="utf-8")
            except OSError:
                pass
            return parse(text), f"online ({datetime.now():%d.%m.%Y %H:%M})"
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as e:
            fehler = f"nicht erreichbar ({getattr(e, 'reason', e)})"
    else:
        fehler = "SPERRLISTE_URL nicht eingerichtet (enthält noch OWNER)"
    if CACHE.exists():
        stand = datetime.fromtimestamp(CACHE.stat().st_mtime)
        return parse(CACHE.read_text(encoding="utf-8")), f"lokale Kopie vom {stand:%d.%m.%Y} – online {fehler}"
    if ohne_liste:
        print(f"WARNUNG: Sperrliste {fehler}. Es wird NICHT abgeglichen (--ohne-liste).")
        return None, "nicht geladen"
    sys.exit(f"Sperrliste {fehler}. Ohne Abgleich keine Ausgabe.\n"
             "Internetverbindung bzw. SPERRLISTE_URL prüfen. Nur bewusst ohne Abgleich: --ohne-liste.")


def lies_csv(pfad):
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        probe = f.read(16384)
        f.seek(0)
        try:
            trenner = csv.Sniffer().sniff(probe, delimiters=",;\t").delimiter
        except csv.Error:
            trenner = ","
        # only the delimiter comes from the sniffer: its guessed quoting breaks on a quote character further down
        r = csv.DictReader(f, delimiter=trenner)
        return list(r.fieldnames or []), list(r), trenner


def main():
    p = argparse.ArgumentParser(description="Leadliste mit der Community-Sperrliste abgleichen")
    p.add_argument("liste")
    p.add_argument("--spalten", help="kommagetrennte Spaltennamen; Standard: automatisch erkennen")
    p.add_argument("--url", default=os.environ.get("SPERRLISTE_URL", STANDARD_URL))
    p.add_argument("--ohne-liste", action="store_true", help="weiterarbeiten, wenn die Liste nicht ladbar ist")
    a = p.parse_args()

    for strom in (sys.stdout, sys.stderr):  # Windows with redirected output: never crash on a character
        try:
            strom.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    felder, zeilen, trenner = lies_csv(a.liste)
    if a.spalten:
        spalten = [s.strip() for s in a.spalten.split(",") if s.strip()]
        fehlend = [s for s in spalten if s not in felder]
        if fehlend:
            sys.exit(f"Spalte(n) nicht gefunden: {', '.join(fehlend)}. Vorhanden: {', '.join(felder)}")
    else:
        spalten = [f for f in felder if f and SPALTEN_MUSTER.search(f) and not AUSNAHMEN.search(f)]
    if not spalten:
        sys.exit(f"Keine E-Mail-/Website-Spalte erkannt. Mit --spalten angeben. Vorhanden: {', '.join(felder)}")

    sperre, quelle = lade(a.url, a.ohne_liste)
    gesperrt, frei, ohne_domain = [], [], 0
    for z in zeilen:
        domains = [d for d in (norm_domain(z.get(s)) for s in spalten) if d]
        if not domains:
            ohne_domain += 1
        grund = next((t for t in (treffer(d, sperre) for d in domains) if t), None) if sperre else None
        if grund:
            z = dict(z)
            z["Sperrgrund"] = f"Community-Sperrliste: {grund}"
            gesperrt.append(z)
        else:
            frei.append(z)

    basis = os.path.splitext(a.liste)[0]
    for name, daten, extra in ((f"{basis}_bereinigt.csv", frei, []), (f"{basis}_gesperrt.csv", gesperrt, ["Sperrgrund"])):
        with open(name + ".tmp", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=felder + extra, delimiter=trenner, lineterminator="\r\n", extrasaction="ignore")
            w.writeheader()
            w.writerows([{k: csv_zelle(v) for k, v in z.items()} for z in daten])
        os.replace(name + ".tmp", name)  # never leave a truncated list behind

    print(f"Sperrliste: {len(sperre) if sperre else 0} Domains, {quelle}")
    print(f"Abgeglichene Spalten: {', '.join(spalten)}")
    print(f"{len(zeilen)} Zeilen: {len(frei)} frei, {len(gesperrt)} gesperrt, {ohne_domain} ohne Domain (nicht prüfbar)")
    print(f"  {basis}_bereinigt.csv  -> für die Ansprache")
    print(f"  {basis}_gesperrt.csv   -> nie anschreiben")
    return 0


if __name__ == "__main__":
    sys.exit(main())

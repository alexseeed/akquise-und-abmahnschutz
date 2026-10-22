#!/usr/bin/env python3
"""Werbe-E-Mail-Sperrliste (Community, GitHub) – Abgleich, Meldung, Kampagnen-Abgleich.

Befehle:
  pruefen   --domain D [D …] [--kanzlei-domain K] [--json]
            Ist der Abmahner (oder eine seiner Domains) schon gemeldet? Wie wurde vorgegangen, wie ging es aus?
  melden    --domains D [D …] --monat JJJJ-MM --melder-domain EIGENE.DE [--kanzlei-domain K]
            [--forderung SPANNE] [--art82 ja|nein] [--vorgehen CODE,CODE] [--status STATUS] [--dry-run]
            Meldet die Domains des Abmahners an die Community-Sperrliste (über das Relay, ohne Token beim Nutzer).
            Ist kein Relay erreichbar, wird ein vorausgefüllter GitHub-Issue-Link ausgegeben.
  laden     [--out sperrliste.txt] [--format txt|csv]
            Lädt die aktuelle Sperrliste (eine Domain je Zeile) zum Import in Versand-/CRM-/Lead-Tools.
  abgleich  --kontakte kontakte.csv [--spalte email|website|domain] [--out-praefix kontakte]
            Gleicht eine Kontaktliste ab: schreibt <präfix>_gesperrt.csv und <präfix>_bereinigt.csv.

Konfiguration: scripts/community.json  {"repo": "alexseeed/werbemail-sperrliste", "branch": "main", "relay_url": "…/exec"}
Umgebung (für Tests/Spiegel): SPERRLISTE_DATA_URL (Basis-URL des data/-Ordners), SPERRLISTE_RELAY_URL.

Nur Python-Standardbibliothek.
"""
import argparse, csv, io, json, os, re, sys, urllib.error, urllib.parse, urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
VERSION = "skill-3.0"

FORDERUNG = ["unbekannt", "0", "1-500", "500-1000", "1000-2000", "2000-5000", ">5000"]
STATUS = ["offen", "keine_reaktion", "erledigt_ohne_zahlung", "erledigt_mit_zahlung", "vergleich",
          "mahnbescheid", "klage", "unbekannt"]
VORGEHEN = ["UE_MODIFIZIERT", "UE_ORIGINAL", "UE_VERWEIGERT", "ART82_ABGELEHNT", "ART82_GEZAHLT",
            "KOSTEN_ABGELEHNT", "KOSTEN_GEZAHLT", "KOSTEN_VERGLEICH", "AUSKUNFT_ERTEILT", "WEBSITE_BLOCK",
            "ANWALT_BEAUFTRAGT"]
RE_DOMAIN = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
RE_MONAT = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")
MAX_DOMAINS = 15
# Mindestschutz, falls data/geschuetzt.txt nicht geladen werden kann (die Repo-Liste ist maßgeblich)
GESCHUETZT_MIN = {"gmail.com", "googlemail.com", "web.de", "gmx.de", "gmx.net", "t-online.de", "outlook.com",
                  "hotmail.com", "hotmail.de", "live.de", "yahoo.com", "yahoo.de", "icloud.com", "me.com",
                  "aol.com", "freenet.de", "posteo.de", "mailbox.org", "proton.me", "protonmail.com", "gmx.at",
                  "gmx.ch", "bluewin.ch", "outlook.de", "msn.com", "co.uk", "com.au"}


# ---------------------------------------------------------------- Grundlagen

def konfig():
    pfad = os.path.join(HIER, "community.json")
    k = {"repo": "", "branch": "main", "relay_url": ""}
    try:
        with open(pfad, encoding="utf-8") as f:
            k.update(json.load(f))
    except (OSError, ValueError):
        pass
    k["relay_url"] = os.environ.get("SPERRLISTE_RELAY_URL", k.get("relay_url") or "")
    basis = os.environ.get("SPERRLISTE_DATA_URL")
    if not basis:
        if not k.get("repo") or "OWNER" in k["repo"]:
            basis = ""
        else:
            basis = f"https://raw.githubusercontent.com/{k['repo']}/{k.get('branch') or 'main'}/data/"
    k["data_url"] = basis.rstrip("/") + "/" if basis else ""
    return k


def holen(k, name):
    if not k["data_url"]:
        raise RuntimeError("Sperrliste nicht konfiguriert (scripts/community.json: repo fehlt oder enthält OWNER)")
    req = urllib.request.Request(k["data_url"] + name, headers={"User-Agent": VERSION, "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{name} nicht abrufbar (HTTP {e.code})")
    except urllib.error.URLError as e:
        raise RuntimeError(f"{name} nicht abrufbar ({e.reason}) – Netzwerkfreigabe für raw.githubusercontent.com prüfen")


def norm_domain(d):
    d = str(d or "").strip().lower()
    if "@" in d:
        d = d.rsplit("@", 1)[1]
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split("?")[0].split("#")[0].split(":")[0].rstrip(".")
    d = re.sub(r"^www\d?\.", "", d)
    try:
        d = d.encode("idna").decode("ascii") if d and not d.isascii() else d
    except UnicodeError:
        pass
    return d


def eltern(d):
    """d selbst und alle Elterndomains (a.b.example.de → a.b.example.de, b.example.de, example.de, de)."""
    teile = d.split(".")
    return [".".join(teile[i:]) for i in range(len(teile))]


def geschuetzt_fuer(d, geschuetzt):
    return any(e in geschuetzt for e in eltern(d)[:-1])


def lade_geschuetzt(k):
    try:
        text = holen(k, "geschuetzt.txt")
        menge = {z.strip().lower() for z in text.splitlines() if z.strip() and not z.lstrip().startswith("#")}
        return menge | GESCHUETZT_MIN, True
    except RuntimeError:
        return set(GESCHUETZT_MIN), False


def lade_sperrliste(k):
    """{domain: zeile} aus sperrliste.csv."""
    text = holen(k, "sperrliste.csv")
    return {z["domain"].strip().lower(): z for z in csv.DictReader(io.StringIO(text)) if z.get("domain")}


def treffer_fuer(d, liste):
    for e in eltern(d)[:-1]:
        if e in liste:
            return e
    return None


# ---------------------------------------------------------------- pruefen

def cmd_pruefen(a):
    k = konfig()
    liste = lade_sperrliste(k)
    try:
        statistik = json.loads(holen(k, "statistik.json"))
    except (RuntimeError, ValueError):
        statistik = {"gruppen": {}}
    gruppen = statistik.get("gruppen", {})

    ergebnis = {"domains": {}, "gruppen": {}, "kanzlei": None}
    for roh in a.domain:
        d = norm_domain(roh)
        t = treffer_fuer(d, liste)
        ergebnis["domains"][d] = {"gelistet": bool(t), "ueber": t, "gruppe": liste[t]["gruppe"] if t else None}
        if t:
            g = liste[t]["gruppe"]
            ergebnis["gruppen"][g] = gruppen.get(g, {"domains": [x for x, z in liste.items() if z["gruppe"] == g]})
    if a.kanzlei_domain:
        kd = norm_domain(a.kanzlei_domain)
        faelle = {g: s for g, s in gruppen.items() if kd in (s.get("kanzlei_domains") or [])}
        ergebnis["kanzlei"] = {"domain": kd, "gruppen": len(faelle), "abmahner_gruppen": sorted(faelle)}

    if a.json:
        print(json.dumps(ergebnis, ensure_ascii=False, indent=1))
        return 0

    print(f"Sperrliste: {statistik.get('domains_gesamt', len(liste))} Domains aus {statistik.get('meldungen_gueltig', '?')} Meldungen")
    for d, info in ergebnis["domains"].items():
        if info["gelistet"]:
            zusatz = f" (über {info['ueber']})" if info["ueber"] != d else ""
            print(f"  GELISTET  {d}{zusatz} → Gruppe {info['gruppe']}")
        else:
            print(f"  neu       {d}")
    for g, s in ergebnis["gruppen"].items():
        print(f"\nGruppe {g}")
        print(f"  Domains:            {', '.join(s.get('domains', []))}")
        if "melder" in s:
            print(f"  Unabhängige Melder: {s['melder']} ({'bestätigt' if s.get('bestaetigt') else 'unbestätigt'})")
            print(f"  Zeitraum:           {s.get('erste_meldung', '?')} bis {s.get('letzte_meldung', '?')}")
        for feld, titel in (("kanzlei_domains", "Kanzleien"), ("forderung", "Forderung (€)"),
                            ("art82_gefordert", "Art. 82 gefordert"), ("vorgehen", "Vorgehen"), ("status", "Ausgang")):
            werte = s.get(feld)
            if isinstance(werte, list) and werte:
                print(f"  {titel + ':':<20}" + ", ".join(werte))
            elif werte:
                print(f"  {titel + ':':<20}" + ", ".join(f"{w} ×{n}" for w, n in sorted(werte.items(), key=lambda x: -x[1])))
    if ergebnis["kanzlei"]:
        kz = ergebnis["kanzlei"]
        print(f"\nKanzlei {kz['domain']}: bei {kz['gruppen']} gemeldeten Abmahner-Gruppe(n) beteiligt"
              + (f": {', '.join(kz['abmahner_gruppen'])}" if kz["abmahner_gruppen"] else ""))
    if not ergebnis["gruppen"]:
        print("\nKein Treffer – Abmahner ist neu. Meldung am Ende des Falls (Phase 9).")
    print("\nHinweis: Erfahrungswerte aus Nutzermeldungen, ungeprüft. Keine Prognose, keine Aussage über die Berechtigung.")
    return 0


# ---------------------------------------------------------------- melden

def baue_meldung(a, geschuetzt):
    fehler = []
    domains = []
    for roh in a.domains:
        for teil in re.split(r"[\s,;]+", roh):
            if not teil:
                continue
            if "@" in teil:
                fehler.append(f"„{teil}“ ist eine E-Mail-Adresse – nur Domains melden (z. B. {norm_domain(teil)})")
                continue
            d = norm_domain(teil)
            if not RE_DOMAIN.match(d):
                fehler.append(f"ungültige Domain: {teil}")
            elif geschuetzt_fuer(d, geschuetzt):
                fehler.append(f"{d} ist geschützt (Freemail/Plattform/Behörde) – nie melden")
            elif d not in domains:
                domains.append(d)
    if not domains:
        fehler.append("keine meldefähige Domain")
    if len(domains) > MAX_DOMAINS:
        fehler.append(f"höchstens {MAX_DOMAINS} Domains je Meldung")

    kanzlei = ""
    if a.kanzlei_domain:
        if "@" in a.kanzlei_domain:
            fehler.append("Kanzlei: nur die Domain, keine E-Mail-Adresse")
        kanzlei = norm_domain(a.kanzlei_domain)
        if not RE_DOMAIN.match(kanzlei):
            fehler.append("Kanzlei-Domain ungültig")
        elif geschuetzt_fuer(kanzlei, geschuetzt):
            kanzlei = ""   # Kanzlei mit Freemail-Adresse: Angabe weglassen
    melder = norm_domain(a.melder_domain)
    if not RE_DOMAIN.match(melder):
        fehler.append("--melder-domain (Domain des eigenen Unternehmens) fehlt oder ungültig")
    elif melder in domains or any(treffer_fuer(melder, {d: 1}) for d in domains):
        fehler.append("Die eigene Domain kann nicht gemeldet werden")
    if not RE_MONAT.match(a.monat or ""):
        fehler.append("--monat muss JJJJ-MM sein")
    vorgehen = [v.strip().upper() for v in (a.vorgehen or "").split(",") if v.strip()]
    for v in vorgehen:
        if v not in VORGEHEN:
            fehler.append(f"unbekannter Vorgehen-Code {v} (erlaubt: {', '.join(VORGEHEN)})")
    m = {"domains": domains, "kanzlei_domain": kanzlei, "monat": a.monat, "forderung": a.forderung,
         "art82": a.art82, "vorgehen": vorgehen, "status": a.status, "melder_domain": melder, "client": VERSION}
    return m, fehler


def issue_link(k, m):
    if not k.get("repo") or "OWNER" in k["repo"]:
        return None
    q = {"template": "meldung.yml", "title": "Meldung " + ", ".join(m["domains"][:3]),
         "domains": "\n".join(m["domains"]), "kanzlei_domain": m["kanzlei_domain"], "monat": m["monat"],
         "vorgehen": ",".join(m["vorgehen"])}
    return f"https://github.com/{k['repo']}/issues/new?" + urllib.parse.urlencode({x: y for x, y in q.items() if y})


def zusammenfassung(m):
    teile = [f"Domains: {', '.join(m['domains'])}"]
    if m["kanzlei_domain"]:
        teile.append(f"Kanzlei-Domain: {m['kanzlei_domain']}")
    teile.append(f"Monat {m['monat']}, Forderung {m['forderung']} €, Art. 82 gefordert: {m['art82']}")
    teile.append(f"Vorgehen: {', '.join(m['vorgehen']) or '–'}, Status: {m['status']}")
    teile.append(f"Eigene Domain {m['melder_domain']} nur zur Berechnung eines anonymen Schlüssels (nicht gespeichert)")
    return "\n  ".join(teile)


def cmd_melden(a):
    k = konfig()
    geschuetzt, geladen = lade_geschuetzt(k)
    m, fehler = baue_meldung(a, geschuetzt)
    if fehler:
        print("Meldung nicht möglich:\n  - " + "\n  - ".join(fehler))
        return 2
    print("Meldung an die Werbe-E-Mail-Sperrliste:\n  " + zusammenfassung(m))
    if not geladen:
        print("  (Schutzliste nicht abrufbar – nur Mindestschutz lokal geprüft; das Relay prüft vollständig)")
    if a.dry_run:
        print("\nTrockenlauf – nichts gesendet. Nutzlast:\n" + json.dumps(m, ensure_ascii=False, indent=1))
        return 0

    if k["relay_url"]:
        daten = json.dumps(m).encode("utf-8")
        req = urllib.request.Request(k["relay_url"], data=daten, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": VERSION})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                antwort = json.loads(r.read().decode("utf-8") or "{}")
            if antwort.get("ok"):
                print(f"\nGesendet. Meldungs-ID {antwort.get('id')}. Übernahme in die Liste in wenigen Minuten.")
                return 0
            print(f"\nRelay hat abgelehnt: {antwort.get('fehler', 'unbekannter Fehler')}")
            if "existiert nicht" in str(antwort.get("fehler", "")) or "ungültig" in str(antwort.get("fehler", "")):
                return 3
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            print(f"\nRelay nicht erreichbar ({getattr(e, 'reason', e)}).")
    else:
        print("\nKein Relay konfiguriert.")

    link = issue_link(k, m)
    if link:
        print("Ersatzweise über GitHub melden (Formular öffnen, Forderung/Art. 82/Status wählen, absenden;"
              " der GitHub-Name ist dabei öffentlich):\n" + link)
        return 4
    print("Weder Relay noch Repository konfiguriert (scripts/community.json).")
    return 5


# ---------------------------------------------------------------- laden / abgleich

def cmd_laden(a):
    k = konfig()
    name = "sperrliste.csv" if a.format == "csv" else "sperrliste.txt"
    text = holen(k, name)
    out = a.out or name
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    anzahl = len([z for z in text.splitlines() if z.strip() and not z.startswith("#")]) - (1 if a.format == "csv" else 0)
    print(f"{max(anzahl, 0)} Domains → {out}")
    return 0


def lies_csv(pfad):
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        probe = f.read(8192)
        f.seek(0)
        try:
            dialekt = csv.Sniffer().sniff(probe, delimiters=",;\t")
        except csv.Error:
            dialekt = csv.excel
        r = csv.DictReader(f, dialect=dialekt)
        return r.fieldnames or [], list(r), dialekt


def cmd_abgleich(a):
    k = konfig()
    sperre = {z.strip().lower() for z in holen(k, "sperrliste.txt").splitlines()
              if z.strip() and not z.startswith("#")}
    felder, zeilen, dialekt = lies_csv(a.kontakte)
    spalte = a.spalte
    if spalte not in felder:
        kandidaten = [f for f in felder if f and f.strip().lower() in ("email", "e-mail", "mail", "website", "domain", "url", "webseite")]
        if not kandidaten:
            print(f"Spalte „{spalte}“ nicht gefunden. Vorhanden: {', '.join(felder)}")
            return 2
        spalte = kandidaten[0]
        print(f"Verwende Spalte „{spalte}“.")
    praefix = a.out_praefix or os.path.splitext(a.kontakte)[0]
    gesperrt, frei = [], []
    for z in zeilen:
        d = norm_domain(z.get(spalte, ""))
        (gesperrt if d and treffer_fuer(d, sperre) else frei).append(z)
    for name, daten in ((f"{praefix}_gesperrt.csv", gesperrt), (f"{praefix}_bereinigt.csv", frei)):
        with open(name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=felder, dialect=dialekt)
            w.writeheader()
            w.writerows(daten)
    print(f"{len(zeilen)} Kontakte geprüft: {len(gesperrt)} gesperrt, {len(frei)} frei.")
    print(f"  {praefix}_bereinigt.csv  → für den Versand verwenden")
    print(f"  {praefix}_gesperrt.csv   → nicht anschreiben")
    return 0


# ---------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description="Werbe-E-Mail-Sperrliste (Community)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("pruefen")
    s.add_argument("--domain", nargs="+", required=True)
    s.add_argument("--kanzlei-domain")
    s.add_argument("--json", action="store_true")

    s = sub.add_parser("melden")
    s.add_argument("--domains", nargs="+", required=True)
    s.add_argument("--kanzlei-domain", default="")
    s.add_argument("--monat", required=True)
    s.add_argument("--forderung", choices=FORDERUNG, default="unbekannt")
    s.add_argument("--art82", choices=["ja", "nein"], required=True)
    s.add_argument("--vorgehen", default="")
    s.add_argument("--status", choices=STATUS, default="offen")
    s.add_argument("--melder-domain", required=True)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("laden")
    s.add_argument("--out")
    s.add_argument("--format", choices=["txt", "csv"], default="txt")

    s = sub.add_parser("abgleich")
    s.add_argument("--kontakte", required=True)
    s.add_argument("--spalte", default="email")
    s.add_argument("--out-praefix")

    a = p.parse_args()
    try:
        return {"pruefen": cmd_pruefen, "melden": cmd_melden, "laden": cmd_laden, "abgleich": cmd_abgleich}[a.cmd](a)
    except RuntimeError as e:
        print(f"Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

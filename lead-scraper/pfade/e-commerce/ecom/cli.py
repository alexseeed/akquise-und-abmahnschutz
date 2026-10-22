"""Kommandozeile — bildet die Clay-Spalten als einzeln aufrufbare Stufen ab.

Beispiele:
    python3 -m ecom import beispiel/shops_beispiel.csv
    python3 -m ecom set-prompt shopprofil ../../auftraege/<auftrag>_shopprofil.txt   # oder: --ohne
    python3 -m ecom set-mailtext ../../auftraege/<auftrag>_mailtext.txt
    python3 -m ecom set-prompt personalisierung ../../auftraege/<auftrag>_personalisierung.txt
    python3 -m ecom run --stage 1 --limit 10     # Testlauf: 10 Shops prüfen
    python3 -m ecom run --stage all
    python3 -m ecom status                       # --shops 20: die ersten Shops mit Ergebnis und Grund
    python3 -m ecom fehler-zuruecksetzen         # liegen gebliebenen Zeilen neue Versuche geben
    python3 -m ecom export

`run` startet erst, wenn die Anforderungen für die gewählten Stufen geklärt sind (Exit-Code 2).
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from . import db, export as export_mod, mailtext as mailtext_mod, pipeline, transforms as T
from .clients import FindymailClient, SkaelClient, ZugangGesperrt, zugangsfehler
from .config import CONFIG, PROMPTS_DIR, ROOT
from .llm import LLM, PROMPT_PLATZHALTER, platzhalter

# Spaltennamen, die beim Import als Firmenname bzw. Website erkannt werden
# Erkannt werden auch die Exporte gängiger Technologie-Verzeichnisse (z. B. BuiltWith: "Root Domain", "Company")
NAME_SPALTEN = ("firmenname", "firma", "company", "company name", "company_name", "name", "shop", "shop name",
                "store", "store name", "store_name", "merchant name", "merchant_name", "brand", "brand name",
                "unternehmen", "title")
WEB_SPALTEN = ("website", "webseite", "domain", "url", "homepage", "website [final]", "website final",
               "shop url", "store url", "location on site", "root domain", "primary domain", "domain name", "shop domain",
               "store domain", "website url", "web site", "site")

STUFEN_1 = ("1a", "1b", "1c", "1d", "1e")
STUFEN_2 = ("2a", "2b", "2c", "2d", "2e", "2f", "2g")
# Welche Stufen welchen Schlüssel brauchen; 1e und 2g rechnen nur mit vorhandenen Daten
SKAEL_STUFEN = {"1a", "1b", "1d", "2a", "2b", "2c", "2e"}
OPENAI_STUFEN = {"1c", "2d", "2e", "2f"}

# Schlüssel, die noch aus .env.example stammen (z. B. eak_dein_key_hier)
PLATZHALTER_SCHLUESSEL = ("dein_key", "your_api_key", "...", "…", "xxx", "hier_eintragen", "changeme")

# Tabellendateien, die `import` nicht lesen kann – sie müssen erst als CSV gespeichert werden
EXCEL_ENDUNGEN = {".xlsx", ".xlsm", ".xls", ".ods", ".numbers"}
EXCEL_SIGNATUREN = (b"PK\x03\x04", b"\xd0\xcf\x11\xe0")   # ZIP-Container (xlsx/ods/numbers), altes .xls


def _ist_platzhalter(wert: str) -> bool:
    return bool(wert) and any(p in wert.lower() for p in PLATZHALTER_SCHLUESSEL)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s", datefmt="%H:%M:%S")


def _abbruch(meldung: str) -> None:
    """Klartext-Fehler für den Nutzer, Exit-Code 2 (fehlende oder fehlerhafte Angabe)."""
    print(meldung, file=sys.stderr)
    raise SystemExit(2)


def _datei(name: str) -> Path:
    """Pfad wie angegeben; sonst relativ zu diesem Pfad, zum Arbeitsordner (Pfad dorthin kopiert)
    oder zum Skill-Ordner – in den beiden letzten liegt auftraege/."""
    pfad = Path(name).expanduser()
    if pfad.exists() or pfad.is_absolute():
        return pfad
    for basis in (ROOT, ROOT.parent, ROOT.parent.parent):
        if (basis / pfad).exists():
            return basis / pfad
    return pfad


def _text_lesen(pfad: Path) -> tuple[str, str]:
    """Text und erkannte Kodierung: UTF-8 (mit/ohne BOM), UTF-16 mit BOM (Excel „Unicode-Text“),
    sonst Windows-1252 (Excel „CSV (Trennzeichen-getrennt)“, Windows-Editor „ANSI“)."""
    roh = pfad.read_bytes()
    if roh.startswith((b"\xff\xfe", b"\xfe\xff")):
        return roh.decode("utf-16"), "UTF-16"
    try:
        return roh.decode("utf-8-sig"), "UTF-8"
    except UnicodeDecodeError:
        return roh.decode("cp1252", errors="replace"), "Windows-1252"


def _lesen(pfad: Path) -> str:
    if not pfad.is_file():
        _abbruch(f"Datei nicht gefunden: {pfad}")
    text, kodierung = _text_lesen(pfad)
    if kodierung != "UTF-8":
        print(f"Hinweis: {pfad.name} ist nicht UTF-8, gelesen als {kodierung}. Umlaute bitte prüfen.")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", text)


def _spalte(header: list[str], kandidaten: tuple[str, ...], explizit: str | None) -> str | None:
    if explizit:
        if explizit not in header:
            raise SystemExit(f"Spalte {explizit!r} nicht in der CSV. Vorhanden: {', '.join(header)}")
        return explizit
    normiert = {h.strip().lower(): h for h in header}
    for k in kandidaten:
        if k in normiert:
            return normiert[k]
    return None


def cmd_import(args: argparse.Namespace) -> None:
    """Clay: CSV in die Tabelle Import laden (Spalten Firmenname und website)."""
    pfad = Path(args.csv)
    if not pfad.is_file():
        raise SystemExit(f"Datei nicht gefunden: {pfad}")
    with pfad.open("rb") as fh:
        anfang = fh.read(8)
    if pfad.suffix.lower() in EXCEL_ENDUNGEN or anfang.startswith(EXCEL_SIGNATUREN):
        _abbruch(f"{pfad.name} ist eine Excel- bzw. Tabellendatei, keine CSV. Es wurde nichts importiert.\n"
                 "In Excel: Datei → Speichern unter → Dateityp „CSV UTF-8 (durch Trennzeichen getrennt)“; "
                 "in Numbers: Ablage → Exportieren → CSV. Dann die CSV importieren.")
    text, kodierung = _text_lesen(pfad)
    if kodierung != "UTF-8":
        print(f"Hinweis: Datei ist nicht UTF-8, gelesen als {kodierung} (z. B. Excel „CSV (Trennzeichen-getrennt)“). "
              "Umlaute in den Firmennamen bitte prüfen.")
    try:
        dialect = csv.Sniffer().sniff(text[:16384], delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    header = reader.fieldnames or []
    name_col = _spalte(header, NAME_SPALTEN, args.name_spalte)
    web_col = _spalte(header, WEB_SPALTEN, args.website_spalte)
    if not name_col and not web_col:
        raise SystemExit("Weder Firmenname- noch Website-Spalte erkannt. Mit --name-spalte / "
                         f"--website-spalte angeben. Vorhanden: {', '.join(header)}")

    conn = db.connect()
    db.init(conn)
    neu = doppelt = leer = ohne_web = 0
    for zeile in reader:
        name = (zeile.get(name_col) or "").strip() if name_col else ""
        web = (zeile.get(web_col) or "").strip() if web_col else ""
        # BuiltWith "Location on Site": "shop.de/*" bedeutet die ganze Domain
        web = web[:-2] if web.endswith("/*") else web
        key = T.import_key(web, name)
        if not key:
            leer += 1
            continue
        if db.insert_ignore(conn, "shops", {"import_key": key, "firmenname": name, "website": web,
                                            "quelle": pfad.name}):
            neu += 1
            ohne_web += 0 if web else 1
        else:
            doppelt += 1
    print(f"Spalten erkannt: Firmenname = {name_col or '–'}, Website = {web_col or '–'}")
    print(f"{neu} Shops neu angelegt, {doppelt} schon vorhanden, {leer} leere Zeilen übersprungen.")
    print(f"Davon ohne Website: {ohne_web}"
          + (" – für diese sucht die KI die Website (kostet etwas mehr)." if ohne_web else "."))
    print(f"Datenbank: {CONFIG.db_path}")


def cmd_run(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    stage = args.stage
    stufen = set(STUFEN_1 + STUFEN_2) if stage == "all" else \
        set(STUFEN_1) if stage == "1" else set(STUFEN_2) if stage == "2" else {stage}

    # Erst die Anforderungen, dann die Schlüssel: so meldet sich eine offene Frage auch ohne .env
    fehlt = pipeline.fehlende_anforderungen(conn, stufen)
    if fehlt:
        _abbruch("Anforderung fehlt – der Lauf startet nicht. Erst klären "
                 "(es wurde nichts abgefragt, es sind keine Kosten entstanden):\n  ✗ "
                 + "\n  ✗ ".join(fehlt))

    # Schlüssel nur für Stufen, die einen Dienst abfragen; Platzhalter aus .env.example wie in `doctor` abweisen,
    # sonst ginge der Platzhalter an den Dienst und jede Zeile verbrauchte einen Fehlversuch
    noetig = (["skael_api_key"] if stufen & SKAEL_STUFEN else []) + \
             (["openai_api_key"] if stufen & OPENAI_STUFEN else [])
    CONFIG.require(*noetig)
    if "2c" in stufen and CONFIG.use_findymail and CONFIG.findymail_api_key:
        noetig.append("findymail_api_key")
    platzhalter_keys = [k.upper() for k in noetig if _ist_platzhalter(getattr(CONFIG, k))]
    if platzhalter_keys:
        _abbruch(f"{', '.join(platzhalter_keys)} in .env ist noch der Platzhalter aus .env.example – "
                 "der Lauf startet nicht (es wurde nichts abgefragt). Echten Schlüssel eintragen und mit "
                 "`python3 -m ecom doctor` prüfen.")

    skael = SkaelClient()
    llm = LLM(skael=skael)
    findymail = FindymailClient()
    pipeline.BILANZ.clear()
    try:
        _stufen_ausfuehren(conn, stufen, args.limit, skael, llm, findymail)
    except ZugangGesperrt as exc:
        _abbruch(f"Lauf abgebrochen: {exc}\nFür die offenen Zeilen wurde kein Fehlversuch gezählt. Nach der "
                 "Korrektur denselben run-Befehl erneut ausführen; Erledigtes wird übersprungen.")
    cmd_status(args)

    gescheitert = [(desc, n, grund) for desc, n, fehler, grund in pipeline.BILANZ if n and fehler == n]
    if gescheitert:
        for desc, n, grund in gescheitert:
            print(f"{desc}: alle {n} Zeilen fehlgeschlagen – häufigster Grund: {grund}", file=sys.stderr)
        print("Ursache beheben (z. B. Internetverbindung, Dienst gestört). Nach drei Fehlversuchen bleibt eine "
              "Zeile liegen: dann `python3 -m ecom fehler-zuruecksetzen` und denselben run-Befehl erneut.",
              file=sys.stderr)
        raise SystemExit(1)


def _stufen_ausfuehren(conn, stufen: set[str], limit: int | None, skael: SkaelClient, llm: LLM,
                       findymail: FindymailClient) -> None:
    if "1a" in stufen:
        pipeline.stufe1a_domain(conn, llm, limit)
    if "1b" in stufen:
        pipeline.stufe1b_webscraper(conn, skael, limit)
    if "1c" in stufen:
        pipeline.stufe1c_onlineshop(conn, llm, limit)
    if "1d" in stufen:
        pipeline.stufe1d_webtraffic(conn, skael, limit)
    if "1e" in stufen:
        pipeline.stufe1e_uebergabe(conn)
    if "2a" in stufen:
        pipeline.stufe2a_website_final(conn, llm)
    if "2b" in stufen:
        pipeline.stufe2b_impressum(conn, skael)
    if "2c" in stufen:
        pipeline.stufe2c_emails(conn, skael, findymail)
    if "2d" in stufen:
        pipeline.stufe2d_anrede(conn, llm)
    if "2e" in stufen:
        pipeline.stufe2e_personalisierung(conn, skael, llm)
    if "2f" in stufen:
        pipeline.stufe2f_videotitel(conn, llm)
    if "2g" in stufen:
        pipeline.stufe2g_ready(conn)


def _kurz(text: str, laenge: int = 60) -> str:
    return text if len(text) <= laenge else text[: laenge - 1].rstrip() + "…"


def _anforderungen(conn) -> list[tuple[str, str]]:
    """Block „Anforderungen“ für status und doctor: (Bezeichnung, Zustand)."""
    profil = db.get_meta(conn, db.META_SHOPPROFIL)
    if profil is None:
        shop = f"✗ fehlt — Builder: {pipeline.BUILDER_SHOPPROFIL}"
    elif profil.strip():
        shop = f"✓ gesetzt ({len(profil)} Zeichen)"
    else:
        shop = "✓ bewusst ohne"

    if not CONFIG.do_personalisierung:
        pers = "– nicht nötig (DO_PERSONALISIERUNG=false)"
    elif (db.get_meta(conn, db.META_PERSONALISIERUNG) or "").strip():
        pers = "✓ gesetzt"
    else:
        pers = f"✗ fehlt — Builder: {pipeline.BUILDER_PERSONALISIERUNG}"

    vorlage = (db.get_meta(conn, db.META_MAILTEXT) or "").strip()
    if vorlage:
        fehler, _ = mailtext_mod.pruefen(vorlage)
        betreff, _ = mailtext_mod.zerlegen(vorlage)
        mail = (f"✗ hat Fehler: {fehler[0]} Neu setzen mit `python3 -m ecom set-mailtext <datei>`" if fehler
                else f"✓ gesetzt (Betreff: {_kurz(betreff or '')})")
    elif CONFIG.do_personalisierung:
        mail = f"✗ fehlt — Builder: {pipeline.BUILDER_PERSONALISIERUNG}, Runde 2"
    else:
        mail = "– nicht nötig"
    return [("Shop-Profil", shop), ("Personalisierung", pers), ("Mailtext", mail)]


def _anforderungen_drucken(conn) -> None:
    print("\n  Anforderungen")
    for bezeichnung, zustand in _anforderungen(conn):
        print(f"    {bezeichnung:<18} {zustand}")


def cmd_status(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    s = db.stats(conn)
    _anforderungen_drucken(conn)
    print()
    print("  Stufe 1  Shops importiert          ", s["shops"])
    print("           mit Website               ", s["mit_website"])
    print("           Website mit Text          ", s["gescrapt"])
    print("           aktiver Onlineshop / nein ", f"{s['aktiver_shop']} / {s['kein_shop']}")
    print("           Shop-Profil passt / nein  ", f"{s['profil_passt']} / {s['profil_passt_nicht']}")
    print("           mit Traffic               ", s["mit_traffic"])
    print("           an Anreicherung übergeben ", s["uebergeben"])
    print("           mit Fehler / liegen gebl. ", _fehler_text(conn, "shops"))
    print("  Stufe 2  Leads in Anreicherung     ", s["anreicherung"])
    print("           Duplikate (E-Mail-Domain) ", s["duplikate"])
    print("           mit E-Mail                ", s["mit_email"])
    print("           Ready to Send             ", s["ready_to_send"])
    print("           mit Fehler / liegen gebl. ",
          _fehler_text(conn, "anreicherung", "AND COALESCE(bereits_exportiert,0)=0"))
    print()
    if conn.execute("SELECT 1 FROM shops WHERE error IS NOT NULL AND attempts >= ? UNION ALL "
                    "SELECT 1 FROM anreicherung WHERE error IS NOT NULL AND attempts >= ? "
                    "AND COALESCE(bereits_exportiert,0)=0 LIMIT 1",
                    (pipeline.MAX_ATTEMPTS, pipeline.MAX_ATTEMPTS)).fetchone():
        print(f"  Liegen geblieben = {pipeline.MAX_ATTEMPTS} Fehlversuche, wird nicht mehr versucht. Ursache beheben, "
              "dann `python3 -m ecom fehler-zuruecksetzen` und denselben run-Befehl erneut.\n")
    if getattr(args, "shops", None):
        _shops_drucken(conn, args.shops)


def _fehler_text(conn, tabelle: str, bedingung: str = "") -> str:
    """„n / m“ (Zeilen mit Fehler / davon liegen geblieben) und der häufigste Grund."""
    zeilen = conn.execute(f"SELECT error, attempts FROM {tabelle} WHERE error IS NOT NULL {bedingung}").fetchall()
    if not zeilen:
        return "0 / 0"
    liegen = sum(1 for z in zeilen if z["attempts"] >= pipeline.MAX_ATTEMPTS)
    grund, anzahl = Counter(_kurz(z["error"], 70) for z in zeilen).most_common(1)[0]
    return f"{len(zeilen)} / {liegen}   häufigster Grund: {grund} ({anzahl}×)"


def _shops_drucken(conn, anzahl: int) -> None:
    """Die ersten Shops mit Prüfergebnis und Grund (ersetzt die sqlite3-Kommandozeile, die unter Windows fehlt)."""
    profil_aktiv = bool((db.get_meta(conn, db.META_SHOPPROFIL) or "").strip())
    zeilen = conn.execute("SELECT * FROM shops ORDER BY id LIMIT ?", (anzahl,)).fetchall()
    print(f"  Die ersten {len(zeilen)} Shops (Shop = aktiver Onlineshop, Profil = passt zum Shop-Profil)\n")
    ja_nein = {1: "ja", 0: "nein", None: "–"}
    for r in zeilen:
        profil = ja_nein[r["passt_profil"]]
        if r["profil_confidence"] is not None:
            profil += f" ({r['profil_confidence']:.2f})"
        print(f"  {_kurz(r['firmenname'] or '–', 40)} · {_kurz(r['website_final'] or r['website'] or '–', 45)}")
        print(f"      Shop {ja_nein[r['is_active_shop']]} · Profil {profil} · Besuche/Monat "
              f"{r['avr_traffic'] if r['avr_traffic'] is not None else '–'} · übergeben "
              f"{'ja' if r['uebergeben'] else 'nein'}")
        if r["profil_grund"] and r["passt_profil"] != 0:   # abgelehnte: Grund steht unter „Stand“
            print(f"      Profil-Grund: {_kurz(r['profil_grund'], 100)}")
        if not r["uebergeben"]:
            print(f"      Stand: {export_mod.grund_shop(r, profil_aktiv)}")
        if r["error"]:
            print(f"      Fehler ({r['attempts']}/{pipeline.MAX_ATTEMPTS}): {_kurz(r['error'], 100)}")
    print()


def cmd_fehler_zuruecksetzen(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Fehlversuche und Fehlermeldungen löschen, damit liegen gebliebene Zeilen erneut laufen. Kostet nichts."""
    conn = db.connect()
    db.init(conn)
    with db.write(conn):
        shops = conn.execute("UPDATE shops SET attempts=0, error=NULL "
                             "WHERE attempts > 0 OR error IS NOT NULL").rowcount
        leads = conn.execute("UPDATE anreicherung SET attempts=0, error=NULL WHERE COALESCE(bereits_exportiert,0)=0 "
                             "AND (attempts > 0 OR error IS NOT NULL)").rowcount
    print(f"{shops} Shops und {leads} Leads bekommen neue Versuche (Fehlversuche und Fehlermeldung gelöscht, "
          "nichts abgefragt).")
    print("Jetzt denselben run-Befehl erneut ausführen. Erledigtes wird übersprungen, nur die offenen Zeilen laufen.")


def cmd_export(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    print()
    ergebnis = export_mod.export_listen(conn, only_ready=not args.all)
    for bezeichnung, pfad, anzahl in ergebnis:
        print(f"  {anzahl:>6} Zeilen  {bezeichnung}")
        print(f"                 {pfad}")
    print()
    if args.mark:
        markiert = export_mod.mark_exported(conn)
        if args.all:
            print(f"{markiert} Leads mit „Ready to Send“ als 'bereits exportiert' markiert.")
        else:
            # ohne --all sind das genau die Leads aus Liste 1, 2 und 4
            gesperrt = next((n for b, _, n in ergebnis if b.startswith("Gesperrt")), 0)
            print(f"{markiert} Leads als 'bereits exportiert' markiert: {markiert - gesperrt} versandfertige "
                  f"(Liste 1 und 2) und {gesperrt} gesperrte (Liste 4, nie anschreiben).")


def _profil_zuruecksetzen(conn) -> int:
    """Profil-Ergebnisse aktiver Shops löschen, die noch nicht übergeben oder noch nicht exportiert sind.

    Stufe 1c prüft sie neu – auch die Shops aus dem Testlauf, die schon in der Anreicherung sind.
    Deren Leads verlieren „Ready to Send“, bis 1c und 2g gelaufen sind. `attempts` und `error`
    starten neu, damit auch Shops, deren Prüfung schon dreimal scheiterte, wieder geprüft werden.
    """
    betroffen = (f"is_active_shop=1 AND {pipeline.SHOP_NOCH_OFFEN} AND (profil_raw IS NOT NULL "
                 "OR passt_profil IS NOT NULL OR attempts > 0 OR error IS NOT NULL)")
    with db.write(conn):
        conn.execute("UPDATE anreicherung SET ready_to_send=0 WHERE COALESCE(bereits_exportiert,0)=0 "
                     f"AND shop_id IN (SELECT id FROM shops WHERE {betroffen})")
        cur = conn.execute(
            "UPDATE shops SET profil_raw=NULL, passt_profil=NULL, profil_confidence=NULL, profil_grund=NULL, "
            f"attempts=0, error=NULL WHERE {betroffen}")
    return cur.rowcount


def cmd_set_prompt(args: argparse.Namespace) -> None:
    """Auftragsspezifischen Prompt hinterlegen (Shop-Profil bzw. Personalisierung)."""
    conn = db.connect()
    db.init(conn)
    if args.art == "shopprofil" and args.ohne:
        if args.datei:
            _abbruch("Entweder eine Datei oder --ohne angeben, nicht beides.")
        db.set_meta(conn, db.META_SHOPPROFIL, "")
        anzahl = _profil_zuruecksetzen(conn)
        print("Shop-Profil: bewusst ohne gespeichert – jeder aktive Onlineshop zählt.")
        if anzahl:
            print(f"{anzahl} noch nicht übergebene oder noch nicht exportierte Shops: altes Profil-Ergebnis "
                  "gelöscht. Danach run --stage 1d, 1e und 2g.")
        return
    if args.ohne:
        _abbruch("--ohne gibt es nur beim Shop-Profil. Die Personalisierung braucht eine Datei "
                 f"(Builder: {pipeline.BUILDER_PERSONALISIERUNG}).")
    if not args.datei:
        builder = pipeline.BUILDER_SHOPPROFIL if args.art == "shopprofil" else pipeline.BUILDER_PERSONALISIERUNG
        _abbruch(f"Datei fehlt: python3 -m ecom set-prompt {args.art} <datei> (Builder: {builder})")

    pfad = _datei(args.datei)
    text = _lesen(pfad).strip()
    if not text:
        _abbruch(f"Die Datei ist leer: {pfad}")
    pflicht, bekannt = PROMPT_PLATZHALTER[args.art]
    genutzt = platzhalter(text)
    if pflicht not in genutzt:
        _abbruch(f"In {pfad.name} fehlt der Platzhalter {{{{{pflicht}}}}} – dort wird der Text der "
                 "Startseite eingesetzt. Nicht gespeichert.")
    for name in genutzt:
        if name not in bekannt:
            print(f"Hinweis: {{{{{name}}}}} wird nicht ersetzt und bleibt wörtlich stehen. Ersetzt werden: "
                  + ", ".join(f"{{{{{n}}}}}" for n in sorted(bekannt)))

    if args.art == "shopprofil":
        db.set_meta(conn, db.META_SHOPPROFIL, text)
        anzahl = _profil_zuruecksetzen(conn)
        print(f"Shop-Profil gespeichert aus {pfad} ({len(text)} Zeichen).")
        print(f"{anzahl} noch nicht übergebene oder noch nicht exportierte Shops zurückgesetzt – Stufe 1c "
              "prüft sie beim nächsten Lauf neu. Danach run --stage 1c, 1d, 1e und 2g.")
        return

    db.set_meta(conn, db.META_PERSONALISIERUNG, text)
    with db.write(conn):
        # attempts/error neu: sonst schreibt 2e den Satz eines Leads mit 3 Fehlversuchen nie neu
        cur = conn.execute("UPDATE anreicherung SET personalisierung=NULL, ready_to_send=0, attempts=0, error=NULL "
                           "WHERE COALESCE(bereits_exportiert,0)=0 AND personalisierung IS NOT NULL")
    print(f"Personalisierung gespeichert aus {pfad} ({len(text)} Zeichen).")
    print(f"{cur.rowcount} noch nicht exportierte Leads zurückgesetzt – ihr persönlicher Satz wird neu "
          "geschrieben (run --stage 2e, danach --stage 2g).")
    if "Mailtext" not in genutzt:
        print("Hinweis: {{Mailtext}} kommt im Prompt nicht vor – die KI sieht dann nicht, was nach ihrem "
              "Satz in der Mail steht, und wiederholt es leichter.")


def cmd_set_mailtext(args: argparse.Namespace) -> None:
    """Mailtext prüfen, speichern und an einem erfundenen Beispiel-Lead zeigen."""
    pfad = _datei(args.datei)
    text = mailtext_mod.normalisieren(_lesen(pfad))
    fehler, hinweise = mailtext_mod.pruefen(text)
    if fehler:
        _abbruch("Mailtext nicht gespeichert – bitte korrigieren:\n  - " + "\n  - ".join(fehler)
                 + "".join(f"\nHinweis: {h}" for h in hinweise))

    conn = db.connect()
    db.init(conn)
    db.set_meta(conn, db.META_MAILTEXT, text)
    print(f"Mailtext gespeichert aus {pfad}.")
    for hinweis in hinweise:
        print(f"Hinweis: {hinweis}")

    betreff, body = mailtext_mod.rendern(text, mailtext_mod.BEISPIEL_LEAD)
    linie = "─" * 60
    print("\nSo sieht eine fertige Mail aus (erfundenes Beispiel: Herr Max Mustermann, Beispiel Shop GmbH):")
    print(linie)
    print(f"Betreff: {betreff}\n")
    print(body)
    print(linie)

    if "Mailtext" in platzhalter(db.get_meta(conn, db.META_PERSONALISIERUNG) or ""):
        anzahl = conn.execute(
            "SELECT COUNT(*) FROM anreicherung WHERE COALESCE(bereits_exportiert,0)=0 "
            "AND COALESCE(personalisierung,'') <> ''").fetchone()[0]
        if anzahl:
            print(f"\nHinweis: {anzahl} persönliche Sätze wurden mit dem alten Mailtext geschrieben. Damit sie "
                  "zum neuen Text passen: `python3 -m ecom set-prompt personalisierung <datei>` erneut "
                  "ausführen (setzt sie zurück), danach `run --stage 2e` und `run --stage 2g`.")


def cmd_doctor(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Prüft Zugangsdaten, Prompts und Erreichbarkeit, bevor ein Lauf Geld kostet."""
    print("\n  Zugangsdaten")
    for label, value in (("SKAEL_API_KEY", CONFIG.skael_api_key), ("OPENAI_API_KEY", CONFIG.openai_api_key),
                         ("FINDYMAIL_API_KEY (optional)", CONFIG.findymail_api_key)):
        if _ist_platzhalter(value):
            mark, hint = "✗", "noch Platzhalter aus .env.example"
        elif value:
            mark, hint = "✓", f"…{value[-6:]}"
        else:
            mark, hint = "✗", "nicht gesetzt"
        print(f"    {mark} {label:<30} {hint}")

    print("\n  Prompt-Dateien")
    for name in ("company_domain.txt", "company_domain.schema.json", "icp_online_shop.txt",
                 "icp_online_shop.schema.json", "anrede.txt", "anrede.schema.json", "personalisierung.txt",
                 "personalisierung.schema.json", "video_title_cleanup.txt", "video_title_cleanup.schema.json",
                 "shopprofil.schema.json", "shopprofil_builder.md", "personalisierung_builder.md"):
        print(f"    {'✓' if (PROMPTS_DIR / name).exists() else '✗'} {name}")

    conn = db.connect()
    db.init(conn)
    _anforderungen_drucken(conn)

    print("\n  Traffic-Filter (Clay: MIN AVR TRAFFIC / MIN AVR H T 3 MO / MODE)")
    print(f"    Schnitt ≥ {CONFIG.min_avr_traffic:g}  {CONFIG.traffic_mode}  Höchstwert ≥ {CONFIG.min_max_traffic:g}")

    print("\n  Erreichbarkeit")
    if CONFIG.skael_api_key and not _ist_platzhalter(CONFIG.skael_api_key):
        try:
            out = SkaelClient().webtraffic("skael.de")
            print(f"    ✓ Skael API erreichbar (Testabfrage webtraffic: found={out.get('found')})")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Skael API: {zugangsfehler(exc) or exc}")
    else:
        print("    – Skael übersprungen (kein Key)")

    if CONFIG.findymail_api_key and not _ist_platzhalter(CONFIG.findymail_api_key):
        try:
            guthaben = FindymailClient().credits()
            print(f"    ✓ Findymail erreichbar ({guthaben.get('credits', '?')} Finder-Credits, "
                  f"{guthaben.get('verifier_credits', '?')} Verifier-Credits übrig)")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Findymail: {zugangsfehler(exc) or exc}")
    else:
        print("    – Findymail übersprungen (kein Key; nur Skael sucht Geschäftsführer-Adressen)")

    from . import sperrliste as sperrliste_mod
    try:
        sperre = sperrliste_mod.laden(pflicht=False)
    except SystemExit:
        sperre = None
    if sperre is None and not sperrliste_mod.konfiguriert():
        print("    ✗ Community-Sperrliste nicht eingerichtet — SPERRLISTE_URL enthält noch den Platzhalter OWNER. "
              "Die Adresse kommt vom Betreiber des Pakets; ohne sie bricht der Export ab. Nicht abschalten")
    elif sperre is None:
        print("    ✗ Community-Sperrliste nicht ladbar — Internetverbindung bzw. SPERRLISTE_URL in .env prüfen "
              "(Export bricht sonst ab)")
    else:
        print(f"    ✓ Community-Sperrliste: {len(sperre)} gesperrte Domains, {sperre.quelle}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecom", description="E-Commerce-Lead-Scraper (Clay-Nachbau ECOM 2.0)")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_imp = sub.add_parser("import", help="Shop-Liste (CSV mit Firmenname und/oder Website) laden")
    p_imp.add_argument("csv")
    p_imp.add_argument("--name-spalte", help="Spaltenname für den Firmennamen, falls nicht erkannt")
    p_imp.add_argument("--website-spalte", help="Spaltenname für die Website, falls nicht erkannt")
    p_imp.set_defaults(func=cmd_import)

    p_run = sub.add_parser("run", help="Pipeline ausführen")
    p_run.add_argument("--stage", default="all", choices=["all", "1", "2", *STUFEN_1, *STUFEN_2])
    p_run.add_argument("--limit", type=int, help="Stufe 1a–1d nur für n Shops (Testlauf)")
    p_run.set_defaults(func=cmd_run)

    p_st = sub.add_parser("status", help="Fortschritt, Fehler und offene Anforderungen anzeigen")
    p_st.add_argument("--shops", type=int, nargs="?", const=20, metavar="N",
                      help="zusätzlich die ersten N Shops (Standard 20) mit Ergebnis und Grund")
    p_st.set_defaults(func=cmd_status)

    sub.add_parser("fehler-zuruecksetzen",
                   help="liegen gebliebenen Zeilen (3 Fehlversuche) neue Versuche geben; kostet nichts").set_defaults(
        func=cmd_fehler_zuruecksetzen)

    p_sp = sub.add_parser("set-prompt", help="Shop-Profil bzw. Personalisierung für diesen Auftrag hinterlegen")
    p_sp.add_argument("art", choices=["shopprofil", "personalisierung"])
    p_sp.add_argument("datei", nargs="?", help="Textdatei aus dem Builder (z. B. auftraege/<auftrag>_shopprofil.txt)")
    p_sp.add_argument("--ohne", action="store_true",
                      help="nur shopprofil: bewusst ohne Shop-Profil, jeder aktive Onlineshop zählt")
    p_sp.set_defaults(func=cmd_set_prompt)

    p_mt = sub.add_parser("set-mailtext", help="Mailtext (Betreff + Text mit Platzhaltern) prüfen und hinterlegen")
    p_mt.add_argument("datei")
    p_mt.set_defaults(func=cmd_set_mailtext)

    p_exp = sub.add_parser("export", help="CSV-Listen exportieren")
    p_exp.add_argument("--all", action="store_true", help="Auch nicht versandfertige Leads")
    p_exp.add_argument("--mark", action="store_true", help="Exportierte Leads markieren")
    p_exp.set_defaults(func=cmd_export)

    sub.add_parser("doctor", help="Zugänge, Prompts, Anforderungen und Erreichbarkeit prüfen").set_defaults(
        func=cmd_doctor)
    return parser


def _check_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit(
            f"Python 3.10 oder neuer nötig — gefunden: {sys.version.split()[0]}\n"
            "macOS/Linux:  brew install python@3.12   bzw.  apt install python3.12\n"
            "Windows:      winget install Python.Python.3.12\n"
            "Danach denselben Befehl mit python3.12 (Windows: py -3.12) statt python3 aufrufen."
        )


def _ausgabe_absichern() -> None:
    """✓, ✗, ─ und ≥ auch ausgeben, wenn die Ausgabe nicht UTF-8 ist (Windows, umgeleitet oder per Pipe:
    dort gilt cp1252, und `print` bräche mit UnicodeEncodeError ab)."""
    for stream in (sys.stdout, sys.stderr):
        kodierung = (getattr(stream, "encoding", None) or "").lower().replace("-", "").replace("_", "")
        if kodierung not in ("utf8", "cp65001") and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _ausgabe_absichern()
    _check_python()
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

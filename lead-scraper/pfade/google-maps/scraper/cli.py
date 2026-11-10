"""Kommandozeile — bildet die Clay-Stufen als einzeln aufrufbare Schritte ab.

Beispiele:
    python -m scraper init --keywords "Metallbau,Schlosserei" --countries DE,AT,CH \
                           --min-population 1 --icp-prompt prompts/icp_beispiel_metallbau.txt
    python -m scraper run --stage all
    python -m scraper run --stage 2 --limit 5      # Dry-Run über 5 Städte
    python -m scraper status
    python -m scraper export

    # Recruiting: Firmen über Maps, offene Stelle auf der Firmen-Website erkennen
    python -m scraper --kampagne <name> init --pfad recruiting --keywords Spedition --countries DE \
                           --berufe "Berufskraftfahrer,Disponent" [--nk]

    # Stellensuche: konkrete Anzeigen in Jobportalen (Indeed, Stepstone, Arbeitsagentur, Kununu)
    python -m scraper --kampagne <name> stellensuche --suche "Berufskraftfahrer,LKW-Fahrer" \
                           --orte "Stuttgart,Ulm" [--nur-stellen]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import db, export as export_mod, pipeline
from .clients import ApiError, FindymailClient, SkaelClient
from .config import CONFIG, PORTALE, ROOT, ist_platzhalter
from .llm import LLM


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def _liste(text: str | None) -> list[str]:
    return [t.strip() for t in (text or "").split(",") if t.strip()]


def _prompt_datei(pfad: str) -> Path:
    """Prompt-Datei relativ zur Kampagne, sonst zum Projektordner."""
    path = Path(pfad)
    if not path.is_absolute():
        from .config import KAMPAGNE_DIR
        path = (KAMPAGNE_DIR / path) if KAMPAGNE_DIR and (KAMPAGNE_DIR / path).exists() else ROOT / path
    if not path.exists():
        raise SystemExit(f"Prompt-Datei nicht gefunden: {path}")
    return path


def _kosten_erfassen(conn) -> None:
    """Echte Skael-Credits je fertigem Auftrag buchen und das Budget prüfen (pipeline.kostenzaehler_starten)."""
    pipeline.kostenzaehler_starten(conn)


def _llm_schluessel_pruefen(stufen_mit_ki: bool) -> None:
    """Skael ist die Standard-KI — ein OpenAI-Schlüssel ist nur für LLM_PROVIDER=openai bzw.
    DOMAINSUCHE=openai nötig (vorher verlangte `run` ihn immer)."""
    if not stufen_mit_ki:
        return
    if CONFIG.llm_provider == "openai" or CONFIG.domainsuche == "openai":
        CONFIG.require("openai_api_key")


def cmd_init(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    db.setze_pfad(conn, args.pfad)
    if args.nk:
        db.set_meta(conn, "nk_on", "true")
    if args.berufe is not None:
        # eine Zeile je Beruf, Reihenfolge = Priorität (Platzhalter {{Gesuchte Berufe}} in stellenanalyse.txt)
        db.set_meta(conn, "berufe", "\n".join(_liste(args.berufe)))
    if args.pfad == "recruiting" and not (db.get_meta(conn, "berufe", "") or ""):
        print("Hinweis: keine --berufe angegeben — die Stellen-Erkennung zählt dann jede offene Stelle.")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    if not keywords or not countries:
        raise SystemExit("Mindestens ein Keyword und ein Land angeben.")

    for keyword in keywords:
        for country in countries:
            db.upsert(conn, "eingabe", {
                "keyword": keyword,
                "country_code": country,
                "min_population": args.min_population,
            }, conflict=("keyword", "country_code", "min_population"))

    icp_datei = args.icp_prompt
    if not icp_datei:
        from .llm import prompt_pfad
        try:
            icp_datei = str(prompt_pfad("icp.txt"))
        except FileNotFoundError:
            icp_datei = None
    if icp_datei and not args.icp_prompt and "[[" in Path(icp_datei).read_text(encoding="utf-8"):
        print(f"Hinweis: {icp_datei} enthält noch [[Platzhalter]] — ohne Prüfprofil angelegt.")
        icp_datei = None
    if icp_datei:
        path = Path(icp_datei)
        if not path.is_absolute():
            from .config import KAMPAGNE_DIR
            path = (KAMPAGNE_DIR / path) if KAMPAGNE_DIR and (KAMPAGNE_DIR / path).exists() else ROOT / path
        if not path.exists():
            raise SystemExit(f"ICP-Prompt-Datei nicht gefunden: {path}")
        db.set_meta(conn, "icp_prompt", path.read_text(encoding="utf-8"))
        print(f"ICP-Prompt übernommen aus {path}")

    db.set_meta(conn, "keywords", keywords)
    db.set_meta(conn, "countries", countries)
    print(f"Kampagnen-Art: {args.pfad}" + (" (mit NK-Strecke: passende Firmen ohne Stelle)" if args.nk else ""))
    print(f"{len(keywords)} Keywords × {len(countries)} Länder = "
          f"{len(keywords) * len(countries)} Kombinationen angelegt.")
    print(f"Datenbank: {CONFIG.db_path}")


def cmd_stellensuche(args: argparse.Namespace) -> None:
    """Stellensuche über Jobportale anlegen: Portal × Suchbegriff × Ort."""
    conn = db.connect()
    db.init(conn)
    db.setze_pfad(conn, "stellensuche")

    begriffe = _liste(args.suche)
    land = args.land.strip().upper()
    portale = [p.lower() for p in _liste(args.portale)]
    unbekannt = [p for p in portale if p not in PORTALE]
    vorhandene = conn.execute("SELECT COUNT(*) FROM stellen_suche").fetchone()[0]
    if not begriffe and not vorhandene:
        raise SystemExit("Mindestens einen Suchbegriff angeben, z. B. --suche \"Berufskraftfahrer\".")
    if unbekannt:
        raise SystemExit(f"Unbekannte Portale: {', '.join(unbekannt)} — möglich: {', '.join(PORTALE)}")

    if not begriffe:
        orte = []   # nur Einstellungen ändern, keine neuen Suchen
    elif args.orte:
        orte = _liste(args.orte)
    elif args.min_population:
        CONFIG.require("skael_api_key")
        _kosten_erfassen(conn)
        try:
            out = SkaelClient().find_cities(land, args.min_population, CONFIG.cities_limit)
        except ApiError as exc:
            raise SystemExit(f"Städteliste nicht abrufbar ({exc}) — später erneut versuchen "
                             "oder --orte angeben.") from None
        orte = [c["name"] for c in out.get("cities") or [] if c.get("name")]
        print(f"{len(orte)} Städte in {land} ab {args.min_population:,} Einwohnern".replace(",", "."))
    else:
        orte = [""]   # landesweit, ohne Ortsangabe

    passend = [p for p in portale if PORTALE[p]["laender"] is None or land in PORTALE[p]["laender"]]
    for p in sorted(set(portale) - set(passend)):
        print(f"Hinweis: {p} gibt es nicht für {land} — übersprungen.")
    if not passend and begriffe:
        raise SystemExit("Kein gewähltes Portal deckt dieses Land ab.")

    for portal in passend:
        for begriff in begriffe:
            for ort in orte:
                db.upsert(conn, "stellen_suche", {"portal": portal, "suchbegriff": begriff,
                                                  "ort": ort, "land": land},
                          conflict=("portal", "suchbegriff", "ort", "land"))

    for key, wert in (("stellen_max_alter", args.max_alter), ("stellen_max_seiten", args.max_seiten),
                      ("stellen_umkreis", args.umkreis)):
        if wert is not None:
            db.set_meta(conn, key, str(wert))
    if args.nur_stellen is not None:
        db.set_meta(conn, "nur_stellen", "true" if args.nur_stellen else "false")
    if args.groessen_check is not None:
        db.set_meta(conn, "groessen_check", "true" if args.groessen_check else "false")
    if args.titel_ausschluss is not None:
        db.set_meta(conn, "titel_ausschluss", ",".join(_liste(args.titel_ausschluss)))
    if args.titel_pflicht is not None:
        db.set_meta(conn, "titel_pflicht", ",".join(_liste(args.titel_pflicht)))
    icp_datei = args.icp_prompt
    if not icp_datei and not db.get_meta(conn, "icp_prompt"):
        from .llm import prompt_pfad
        try:
            icp_datei = str(prompt_pfad("icp.txt"))   # icp.txt der Kampagne, falls vorhanden
        except FileNotFoundError:
            icp_datei = None
        if icp_datei and "[[" in Path(icp_datei).read_text(encoding="utf-8"):
            # unveränderte Vorlage aus neue-kampagne — kein Prüfprofil (Stellensuche braucht keins)
            print(f"Hinweis: {icp_datei} enthält noch [[Platzhalter]] — ohne Prüfprofil angelegt.")
            icp_datei = None
    if icp_datei:
        db.set_meta(conn, "icp_prompt", _prompt_datei(icp_datei).read_text(encoding="utf-8"))
        print(f"Prüfprofil übernommen aus {icp_datei}")
    if args.opener_prompt:
        from .llm import prompt_pfad
        name = Path(args.opener_prompt).name
        try:
            herkunft = prompt_pfad(name)
        except FileNotFoundError:
            raise SystemExit(f"Opener-Prompt nicht gefunden: {name} (Kampagne/prompts/ oder prompts/)") from None
        db.set_meta(conn, "opener_prompt", name)
        print(f"Opener-Prompt: {herkunft}")

    anzahl = conn.execute("SELECT COUNT(*) FROM stellen_suche WHERE status != 'done'").fetchone()[0]
    max_seiten = pipeline.einstellung(conn, "stellen_max_seiten", CONFIG.stellen_max_seiten)
    # Erledigte Suchen mit weiteren Seiten blättern bei höherer Seitenzahl weiter (siehe stufe1j)
    weiter = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(? - seiten + CASE WHEN portal='indeed' AND cursor IS NULL "
        "THEN seiten ELSE 0 END), 0) FROM stellen_suche WHERE status='done' AND seiten < ? "
        "AND (weiter = 1 OR (weiter IS NULL AND treffer >= seiten * 100))",
        (max_seiten, max_seiten)).fetchone()
    print(f"Kampagne: stellensuche ({'nur Stellenliste' if pipeline.nur_stellen(conn) else 'mit Anreicherung'})")
    if begriffe:
        print(f"{len(passend)} Portale × {len(begriffe)} Suchbegriffe × {len(orte)} Orte "
              f"→ {anzahl} offene Suchen, höchstens {anzahl * max_seiten} Seiten à 1 Credit")
    elif anzahl:
        print(f"{anzahl} offene Suchen, höchstens {anzahl * max_seiten} Seiten à 1 Credit")
    if weiter[0]:
        print(f"{weiter[0]} erledigte Suchen blättern weiter bis Seite {max_seiten}: "
              f"höchstens {weiter[1]} Seiten à 1 Credit")
    if not pipeline.nur_stellen(conn):
        print("Größen-Check vor der Website-Suche: " + (
            "an (Konzerne, öffentliche Hand/Verbände, IT-Wettbewerber fallen raus)"
            if pipeline.groessen_check(conn) else "aus"))
    print("Anzeigen nicht älter als {} Tage, Umkreis {} km".format(
        pipeline.einstellung(conn, "stellen_max_alter", CONFIG.stellen_max_alter),
        pipeline.einstellung(conn, "stellen_umkreis", CONFIG.stellen_umkreis)))
    if pipeline.titel_ausschluss(conn):
        print(f"Stellen mit diesen Wörtern im Titel fallen raus: {', '.join(pipeline.titel_ausschluss(conn))}")
    if pipeline.titel_ausschluss(conn, "titel_pflicht"):
        print(f"Im Titel muss einer dieser Begriffe stehen: {', '.join(pipeline.titel_ausschluss(conn, 'titel_pflicht'))}")
    print(f"Datenbank: {CONFIG.db_path}")


def cmd_run(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)

    stage = args.stage
    skael = SkaelClient()
    llm = LLM()
    findymail = FindymailClient()
    icp_prompt = db.get_meta(conn, "icp_prompt", "") or ""

    CONFIG.require("skael_api_key")
    if args.budget is not None:
        db.set_meta(conn, "budget_credits", str(int(args.budget * pipeline.CREDITS_JE_EURO)))
    _kosten_erfassen(conn)
    _llm_schluessel_pruefen(stage in ("all", "3", "3a", "3e", "3g", "4", "4a", "4d", "4e", "4f")
                            and not pipeline.nur_stellen(conn))

    pipeline.BILANZ.clear()
    fehler = 0
    if stage in ("all", "1"):
        fehler += not pipeline.stufe_sicher("1", pipeline.stufe1_staedte, conn, skael)
    if stage in ("all", "1", "1j"):
        fehler += not pipeline.stufe_sicher("1j", pipeline.stufe1j_stellensuche, conn, skael, limit=args.limit)
    if stage in ("all", "1", "1j", "1k"):
        fehler += not pipeline.stufe_sicher("1k", pipeline.stufe1k_firmen, conn)
    if stage in ("all", "2"):
        fehler += not pipeline.stufe_sicher("2", pipeline.stufe2_maps, conn, skael, limit=args.limit)
    if stage in ("all", "3", "3g"):
        # Stellensuche: Konzerne & Co. vor der bezahlten Website-Suche aussortieren
        fehler += not pipeline.stufe_sicher("3g", pipeline.stufe3g_groesse, conn, llm)
    if stage in ("all", "3", "3a"):
        # --limit nur bei ausdrücklichem Aufruf von 3a (Testlauf der Website-Suche)
        fehler += not pipeline.stufe_sicher("3a", pipeline.stufe3a_domains, conn, llm, skael, limit=args.limit if stage == "3a" else None)
    if stage in ("all", "3", "3b"):
        fehler += not pipeline.stufe_sicher("3b", pipeline.stufe3b_dedupe, conn)
    if stage in ("all", "3", "3c"):
        fehler += not pipeline.stufe_sicher("3c", pipeline.stufe3c_icp, conn, skael, icp_prompt)
    if stage in ("all", "3", "3e"):
        fehler += not pipeline.stufe_sicher("3e", pipeline.stufe3e_stellen, conn, skael, llm)
    if stage in ("all", "3", "3d"):
        fehler += not pipeline.stufe_sicher("3d", pipeline.stufe3d_uebergabe, conn)
    if stage in ("all", "4", "4a"):
        fehler += not pipeline.stufe_sicher("4a", pipeline.stufe4a_website_final, conn, llm, skael)
    if stage in ("all", "4", "4b"):
        fehler += not pipeline.stufe_sicher("4b", pipeline.stufe4b_impressum, conn, skael)
    if stage in ("all", "4", "4c"):
        fehler += not pipeline.stufe_sicher("4c", pipeline.stufe4c_emails, conn, skael, findymail)
    if stage in ("all", "4", "4d"):
        fehler += not pipeline.stufe_sicher("4d", pipeline.stufe4d_anrede, conn, llm)
    if stage in ("all", "4", "4e"):
        fehler += not pipeline.stufe_sicher("4e", pipeline.stufe4e_personalisierung, conn, skael, llm)
    if stage in ("all", "4", "4f"):
        fehler += not pipeline.stufe_sicher("4f", pipeline.stufe4f_videotitel, conn, llm)
    if stage in ("all", "4", "4g"):
        fehler += not pipeline.stufe_sicher("4g", pipeline.stufe4g_linkedin, conn, skael)
    if stage in ("all", "4", "4h"):
        fehler += not pipeline.stufe_sicher("4h", pipeline.stufe4h_ready, conn)

    cmd_status(args)

    gescheitert = [(desc, n, grund) for desc, n, n_fehler, grund in pipeline.BILANZ if n and n_fehler == n]
    if gescheitert:
        for desc, n, grund in gescheitert:
            print(f"{desc}: alle {n} Zeilen fehlgeschlagen – häufigster Grund: {grund}", file=sys.stderr)
        print("Ursache beheben (z. B. Internetverbindung, Dienst gestört) und denselben run-Befehl "
              "erneut ausführen; Erledigtes wird übersprungen.", file=sys.stderr)
    if fehler:
        raise SystemExit(f"{fehler} Stufe(n) mit Fehler abgebrochen (Details im Log oben) — "
                         "denselben Befehl erneut starten, erledigte Zeilen werden übersprungen.")
    if gescheitert:
        raise SystemExit(1)


def cmd_status(args: argparse.Namespace) -> None:  # noqa: ARG001
    conn = db.connect()
    db.init(conn)
    s = db.stats(conn)
    pfad = db.pfad(conn)
    print()
    print(f"  Kampagnen-Art: {pfad}   ({CONFIG.db_path})")
    if pfad == "stellensuche":
        print("  Stufe 1j Suchen in Portalen   ", f"{s['suchen_done']}/{s['suchen']} erledigt "
                                                 f"({s['suchen_seiten']} Seiten abgefragt)")
        print("           Anzeigen gefunden    ", s["stellen"])
        for grund, anzahl in s["stellen_ausschluss"].items():
            print(f"             raus: {grund:<22}", anzahl)
        print("           übernommen           ", s["stellen_ok"])
    else:
        print("  Stufe 1  Keyword × Land       ", f"{s['eingabe_done']}/{s['eingabe']} erledigt")
        print("  Stufe 2  Städte-Queries       ", f"{s['verarbeitung_done']}/{s['verarbeitung']} erledigt")
    print("  Stufe 3  Firmen gefunden      ", s["datensaetze"])
    print("           nach Dedupe          ", s["datensaetze_kept"])
    if pfad == "stellensuche":
        if s["groesse_geprueft"]:
            raus = ", ".join(f"{bezeichnung} {s['groesse_raus'].get(k, 0)}"
                             for k, bezeichnung in pipeline.GROESSE_AUSSCHLUSS.items())
            print("           Größen-Check         ", f"{s['groesse_geprueft']} geprüft, raus: {raus}")
        print("           mit eigener Website  ", s["firmen_mit_website"])
    if pipeline.nur_stellen(conn):
        print("  (nur Stellenliste — keine Anreicherung)")
    else:
        print("           ICP true / false     ", f"{s['icp_true']} / {s['icp_false']}")
        if pfad == "recruiting":
            print("           Stelle geprüft / ja  ", f"{s['stelle_geprueft']} / {s['stelle_ja']}")
        print("  Stufe 4  Leads in Anreicherung", s["anreicherung"],
              f"(RC {s['strecke_rc']}, NK {s['strecke_nk']})" if pfad == "recruiting" else "")
        print("           mit E-Mail           ", s["mit_email"])
        print("           Ready to Send        ", s["ready_to_send"])
    budget = float(db.get_meta(conn, "budget_credits", 0) or 0)
    if budget:
        print("  Budget (Skael)                ", f"{budget / pipeline.CREDITS_JE_EURO:,.2f} €".replace(".", ","))
    if s["kosten_credits"]:
        print("  Skael-Kosten bisher           ", f"{s['kosten_credits']:,.0f} Credits ≈ "
              f"{s['kosten_credits'] / 1000:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
              "(ohne KI-Schritte)")
    print()


def cmd_export(args: argparse.Namespace) -> None:
    if args.einzeln and args.lead_format:
        raise SystemExit("--lead-format braucht die getrennten Listen 1 und 2 – ohne --einzeln aufrufen.")
    conn = db.connect()
    db.init(conn)
    if args.einzeln:
        path = export_mod.export_csv(conn, only_ready=not args.all)
        print(f"Export geschrieben: {path}")
    else:
        print()
        for bezeichnung, pfad, anzahl in export_mod.export_listen(conn, only_ready=not args.all,
                                                                   lead_format=args.lead_format):
            print(f"  {anzahl:>6} Zeilen  {bezeichnung}")
            print(f"                 {pfad}")
        print()
    if args.mark:
        count = export_mod.mark_exported(conn)
        print(f"{count} Leads als 'bereits exportiert' markiert.")


def cmd_blockliste_import(args: argparse.Namespace) -> None:
    from . import blockliste as blockliste_mod
    path = Path(args.file).expanduser()
    if not path.exists():
        raise SystemExit(f"Datei nicht gefunden: {path}")
    zeilen, neu, spalten = blockliste_mod.importieren(path)
    print(f"{zeilen} Zeilen gelesen (Spalten: {', '.join(spalten)})")
    print(f"{neu} neue Einträge, insgesamt {len(blockliste_mod.laden())} auf der Blockliste")
    print(f"Datei: {blockliste_mod.DATEI}")


def cmd_testballon_lauf(args: argparse.Namespace) -> None:
    """Testballon in der aktuellen Kampagne: bis --ziel versandfertige Leads, Budget oder Markt erschöpft."""
    from . import testballon
    conn = db.connect()
    db.init(conn)
    CONFIG.require("skael_api_key")
    if args.budget is not None:
        db.set_meta(conn, "budget_credits", str(int(args.budget * pipeline.CREDITS_JE_EURO)))
    _kosten_erfassen(conn)
    _llm_schluessel_pruefen(not args.nur_marktprobe)
    ergebnis = testballon.lauf(conn, SkaelClient(), LLM(), FindymailClient(),
                               ziel=args.ziel, nur_marktprobe=args.nur_marktprobe)
    print(f"Testballon {CONFIG.db_path.parent.parent.name}: {ergebnis['ready']} versandfertige Leads "
          f"({testballon.GRUND_TEXT.get(ergebnis['grund'], ergebnis['grund'])}, {ergebnis['runden']} Runden), "
          f"Skael-Kosten {db.kosten_summe(conn) / pipeline.CREDITS_JE_EURO:.2f} €".replace(".", ","))


# kampagne.env für Testballon-Kampagnen: Recruiting braucht weder Videotitel noch Einordnung
_BALLON_ENV = """# Testballon „{name}“ – Weg {weg} (angelegt von `scraper testballon`)
# Diese Datei überschreibt die .env im Projektordner. Zugangsschlüssel gehören NICHT hierher.
EXCLUDED_TLDS=.fr,.nl,.it
DOMAINSUCHE=aus
ABSATZ_EINLEITUNG=
ABSATZ_FOLGESATZ=
ABSATZ_STANDARD=
DO_PERSONALISIERUNG=true
DO_VIDEO_TITLE=false
"""


def _ballon_kampagne(name: str, weg: str, args: argparse.Namespace) -> Path:
    """kampagnen/<name>-<weg>/ aus der Vorlage, mit passender kampagne.env und Prompts."""
    import shutil
    from .config import KAMPAGNEN_ROOT
    ordner = KAMPAGNEN_ROOT / f"{name}-{weg}"
    if ordner.exists():
        return ordner   # weiterlaufen lassen: erledigte Schritte werden nicht noch einmal bezahlt
    shutil.copytree(KAMPAGNEN_ROOT / "_vorlage", ordner)
    (ordner / "kampagne.env").write_text(_BALLON_ENV.format(name=name, weg=weg), encoding="utf-8")
    prompts = ordner / "prompts"
    for vorlage in ("icp.txt", "personalisierung.txt", "pain_kategorie.txt", "pain_kategorie.schema.json"):
        (prompts / vorlage).unlink(missing_ok=True)   # Google-Maps-Vorlagen mit [[Platzhaltern]]
    if args.icp_prompt:
        shutil.copyfile(_prompt_datei(args.icp_prompt), prompts / "icp.txt")
    if args.opener_prompt:
        shutil.copyfile(_prompt_datei(args.opener_prompt), prompts / "personalisierung_stellenanzeige.txt")
    if args.stellen_prompt and weg == "website":
        shutil.copyfile(_prompt_datei(args.stellen_prompt), prompts / "stellenanalyse.txt")
    return ordner


def _scraper(kampagne: str, *befehl: str) -> int:
    """Einen Scraper-Befehl in einer anderen Kampagne ausführen (eigener Prozess: eigene Konfiguration)."""
    import subprocess
    print(f"\n$ scraper --kampagne {kampagne} {' '.join(befehl)}", flush=True)
    return subprocess.run([sys.executable, "-m", "scraper", "--kampagne", kampagne, *befehl],
                          cwd=ROOT, check=False).returncode


def cmd_testballon(args: argparse.Namespace) -> None:
    """Beide Recruiting-Wege mit je bis zu --ziel Leads fahren und vergleichen."""
    from datetime import datetime
    from . import testballon
    from .config import EXPORT_DIR, KAMPAGNE, KAMPAGNEN_ROOT
    if KAMPAGNE:
        raise SystemExit("testballon ohne --kampagne aufrufen – er legt seine zwei Kampagnen selbst an.")
    name = args.name.strip().lower().replace(" ", "-")
    wege = [w.strip().lower() for w in args.wege.split(",") if w.strip()]
    if not wege or set(wege) - set(testballon.WEGE):
        raise SystemExit(f"--wege: {', '.join(testballon.WEGE)}")
    if "website" in wege and not args.keywords:
        print("Hinweis: ohne --keywords (Branche für Google Maps) läuft nur der Weg „portale“.")
        wege = [w for w in wege if w != "website"]
    if not wege:
        raise SystemExit("Kein Weg übrig – --keywords angeben oder --wege portale.")
    db_pfade = {w: KAMPAGNEN_ROOT / f"{name}-{w}" / "data" / "leads.db" for w in wege}

    if not args.nur_bericht:
        print(f"Testballon „{name}“: {', '.join(testballon.WEG_NAME[w] for w in wege)} · Ziel {args.ziel} Leads "
              f"je Weg · Budget {args.budget:.2f} € Skael-Credits je Weg".replace(".", ","))
        for weg in wege:
            kampagne = _ballon_kampagne(name, weg, args).name
            if weg == "website":
                einrichten = ["init", "--pfad", "recruiting", "--keywords", args.keywords, "--countries", args.land,
                              "--min-population", str(args.min_population), "--berufe", args.suche]
            else:
                einrichten = ["stellensuche", "--suche", args.suche, "--land", args.land]
                einrichten += ["--orte", args.orte] if args.orte else ["--min-population", str(args.min_population)]
                for option, wert in (("--titel-pflicht", args.titel_pflicht),
                                     ("--titel-ausschluss", args.titel_ausschluss)):
                    if wert:
                        einrichten += [option, wert]
            if _scraper(kampagne, *einrichten) != 0:
                print(f"Weg {weg}: Einrichtung fehlgeschlagen – übersprungen.")
                continue
            lauf = ["testballon-lauf", "--ziel", str(args.ziel), "--budget", str(args.budget)]
            if args.nur_marktprobe:
                lauf.append("--nur-marktprobe")
            if _scraper(kampagne, *lauf) != 0:
                print(f"Weg {weg}: Lauf abgebrochen – Bericht zeigt den Stand bis dahin.")
            if not args.nur_marktprobe:
                _scraper(kampagne, "export")

    text = testballon.bericht(name, db_pfade, args.ziel)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ziel = EXPORT_DIR / f"testballon_{name}_{datetime.now():%Y%m%d_%H%M%S}.md"
    ziel.write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"Bericht: {ziel}")


def cmd_neue_kampagne(args: argparse.Namespace) -> None:
    """Legt kampagnen/<name>/ aus der Vorlage an."""
    import shutil
    from .config import KAMPAGNEN_ROOT
    name = args.name.strip().lower().replace(" ", "-")
    ziel = KAMPAGNEN_ROOT / name
    if ziel.exists():
        raise SystemExit(f"Kampagne existiert schon: {ziel}")
    shutil.copytree(KAMPAGNEN_ROOT / "_vorlage", ziel)
    print(f"Kampagne angelegt: {ziel}")
    print("Jetzt ausfüllen: kampagne.env und prompts/*.txt (alle [[Platzhalter]] ersetzen).")
    print(f"Prüfen mit:  python3 -m scraper --kampagne {name} doctor")


def _offene_firmen(conn, reihenfolge: str) -> list[int]:
    """Ungeprüfte Firmen mit Website, sortiert nach Ortsgröße (groß zuerst) oder zufällig."""
    sortierung = "RANDOM()" if reihenfolge == "zufall" else "p DESC, d.id"
    return [r[0] for r in conn.execute(f"""
        WITH pop AS (SELECT input_city c, input_country l, MAX(population) p FROM verarbeitung GROUP BY 1, 2)
        SELECT d.id, COALESCE(pop.p, 0) p FROM datensaetze d
          LEFT JOIN pop ON pop.c = d.query_city AND pop.l = d.query_country
         WHERE d.dedupe_status = ? AND d.icp_raw IS NULL AND COALESCE(d.website_final, '') <> ''
         ORDER BY {sortierung}""", ("kept",)).fetchall()]


def cmd_auswahl(args: argparse.Namespace) -> None:
    """Nur N ungeprüfte Firmen behalten, den Rest zurückstellen (Zielmenge statt Marktgröße)."""
    conn = db.connect()
    db.init(conn)
    ids = _offene_firmen(conn, args.reihenfolge)
    rest = ids[args.firmen:]
    with db.write(conn):
        conn.executemany("UPDATE datensaetze SET dedupe_status='deferred_menge' WHERE id=?", [(i,) for i in rest])
    print(f"{min(len(ids), args.firmen)} Firmen bleiben für die Prüfung, {len(rest)} zurückgestellt "
          f"(Reihenfolge: {args.reihenfolge}). Nachholen mit: scraper nachziehen --firmen N")


def cmd_nachziehen(args: argparse.Namespace) -> None:
    """Holt N zurückgestellte Firmen zurück in die Prüfung."""
    conn = db.connect()
    db.init(conn)
    with db.write(conn):
        conn.execute("UPDATE datensaetze SET dedupe_status='kept' WHERE id IN ("
                     "SELECT id FROM datensaetze WHERE dedupe_status='deferred_menge' ORDER BY id LIMIT ?)",
                     (args.firmen,))
    rest = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='deferred_menge'").fetchone()[0]
    print(f"{args.firmen} Firmen zurückgeholt, noch {rest} zurückgestellt. Weiter mit: scraper run --stage all")


# Gemessene Skael-Credits je fertigem Lead (wissen/15_learnings…): ICP-Check ist auf die
# Trefferquote umgelegt, deshalb wird er hier getrennt mit der echten Quote gerechnet.
_CREDITS_JE_PRUEFUNG = 1.85
_CREDITS_ANREICHERUNG_JE_LEAD = 15.4      # Impressum 4,9 + E-Mail 8,2 + Website-Text 2,0 + Puffer
_EMAIL_QUOTE = 0.88


def cmd_schaetzen(args: argparse.Namespace) -> None:
    """Kostenschätzung für eine Zielmenge, mit der echten Trefferquote der Kampagne, sofern vorhanden."""
    conn = db.connect()
    db.init(conn)
    geprueft = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE is_icp IS NOT NULL").fetchone()[0]
    treffer = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE is_icp=1").fetchone()[0]
    quote = treffer / geprueft if geprueft >= 100 else 0.6
    pruefungen = args.leads / _EMAIL_QUOTE / quote
    credits = pruefungen * _CREDITS_JE_PRUEFUNG + args.leads / _EMAIL_QUOTE * _CREDITS_ANREICHERUNG_JE_LEAD
    print(f"Zielmenge {args.leads} Leads · Trefferquote {quote:.0%}"
          f"{' (gemessen an ' + str(geprueft) + ' Firmen)' if geprueft >= 100 else ' (Annahme)'}")
    print(f"  zu prüfende Firmen   ca. {pruefungen:,.0f}".replace(",", "."))
    print(f"  Skael                ca. {credits:,.0f} Credits = {credits / 1000:,.0f} €".replace(",", "."))
    print("  KI-Schritte          je nach Modell 0,03–0,5 Cent je Lead (siehe wissen/15)")
    print("  Danach:  scraper auswahl --firmen", f"{pruefungen * 1.1:.0f}", "(10 % Puffer)")


def cmd_icp(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    path = Path(args.file)
    if not path.is_absolute():
        path = ROOT / path
    db.set_meta(conn, "icp_prompt", path.read_text(encoding="utf-8"))
    print(f"ICP-Prompt gesetzt aus {path}")


def cmd_doctor(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Prüft Zugangsdaten und Erreichbarkeit, bevor ein teurer Lauf startet."""
    from .config import KAMPAGNE, KAMPAGNE_DIR
    print()
    print(f"  Kampagne: {KAMPAGNE + '  (' + str(KAMPAGNE_DIR) + ')' if KAMPAGNE else '– keine (Standardordner)'}")
    print(f"  KI-Anbieter: {CONFIG.llm_provider} · Modelle: {CONFIG.model_default} / Satz: "
          f"{CONFIG.model_personalisierung} · Domainsuche: {CONFIG.domainsuche}")
    print()
    print("  Zugangsdaten")
    schluessel = [("SKAEL_API_KEY", CONFIG.skael_api_key)]
    if CONFIG.llm_provider == "openai" or CONFIG.domainsuche == "openai":
        schluessel += [("OPENAI_API_KEY", CONFIG.openai_api_key),
                       ("OPENAI_API_KEY_FALLBACK (optional)", CONFIG.openai_api_key_fallback)]
    schluessel.append(("FINDYMAIL_API_KEY (optional)", CONFIG.findymail_api_key))
    for label, value in schluessel:
        if ist_platzhalter(value):
            mark, hint = "✗", "noch Platzhalter aus .env.example"
        elif value:
            mark, hint = "✓", f"…{value[-6:]}"
        else:
            mark, hint = "✗", "nicht gesetzt"
        print(f"    {mark} {label:<30} {hint}")

    if KAMPAGNE_DIR and "[[" in (KAMPAGNE_DIR / "kampagne.env").read_text(encoding="utf-8"):
        print("    ✗ kampagne.env enthält noch [[Platzhalter]] aus der Vorlage")
    print()
    print("  Prompt-Dateien (Kampagne vor Standard)")
    from .llm import prompt_pfad

    conn_pfad = db.connect()
    db.init(conn_pfad)
    art = db.pfad(conn_pfad)
    print(f"    Kampagnen-Art: {art}")
    namen = ["icp.txt", "anrede.txt", "anrede.schema.json", "company_domain.txt"]
    if art == "google-maps":
        namen += ["personalisierung.txt", "personalisierung.schema.json", "pain_kategorie.txt",
                  "pain_kategorie.schema.json", "video_title_cleanup.txt", "video_title_cleanup.schema.json"]
    else:
        opener = db.get_meta(conn_pfad, "opener_prompt", "") or "personalisierung_stellenanzeige.txt"
        namen += ["jobtitel_normalisierung.txt", "jobtitel_normalisierung.schema.json", opener,
                  "personalisierung.schema.json"]
        namen += (["stellenanalyse.txt", "stellenanalyse.schema.json", "personalisierung_website.txt"]
                  if art == "recruiting" else ["groessen_check.txt", "groessen_check.schema.json"])
    for name in namen:
        if not CONFIG.do_personalisierung and name.startswith(("personalisierung", "pain_kategorie")):
            print(f"    – {name:<34} nicht nötig (DO_PERSONALISIERUNG=false)")
            continue
        try:
            pfad = prompt_pfad(name)
        except FileNotFoundError:
            print(f"    {'–' if name == 'icp.txt' else '✗'} {name}")
            continue
        offen = "[[" in pfad.read_text(encoding="utf-8")
        herkunft = "Kampagne" if KAMPAGNE_DIR and KAMPAGNE_DIR in pfad.parents else "Standard"
        print(f"    {'✗' if offen else '✓'} {name:<34} {herkunft}"
              + ("  — enthält noch [[Platzhalter]] aus der Vorlage" if offen else ""))

    conn = db.connect()
    db.init(conn)
    icp = db.get_meta(conn, "icp_prompt", "") or ""
    print()
    print(f"  ICP-Prompt: {'✓ hinterlegt (' + str(len(icp)) + ' Zeichen)' if icp else '✗ fehlt — `scraper set-icp <datei>`'}")

    print()
    print("  Erreichbarkeit")
    if CONFIG.skael_api_key and not ist_platzhalter(CONFIG.skael_api_key):
        try:
            out = SkaelClient().find_cities("LU", 100000, limit=1)
            print(f"    ✓ Skael API erreichbar (Testabfrage lieferte {out.get('total', '?')} Städte für LU)")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Skael API: {exc}")
    else:
        print("    – Skael übersprungen (kein Key)")
    if CONFIG.findymail_api_key and not ist_platzhalter(CONFIG.findymail_api_key):
        try:
            guthaben = FindymailClient().credits()
            print(f"    ✓ Findymail erreichbar ({guthaben.get('credits', '?')} Finder-Credits, "
                  f"{guthaben.get('verifier_credits', '?')} Verifier-Credits übrig)")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Findymail: {exc}")
    else:
        print("    – Findymail übersprungen (kein Key; nur Skael sucht Geschäftsführer-Adressen)")
    try:
        from .clients import OpenAIClient
        antwort = OpenAIClient().complete("Antworte nur mit: ok", model=CONFIG.model_default, temperature=0)
        print(f"    ✓ KI ({CONFIG.llm_provider}, {CONFIG.model_default}) antwortet: {str(antwort).strip()[:20]}")
    except Exception as exc:  # noqa: BLE001
        print(f"    ✗ KI ({CONFIG.llm_provider}): {exc}")

    from . import sperrliste as sperrliste_mod
    try:
        sperre = sperrliste_mod.laden(pflicht=False)
    except SystemExit:
        sperre = None
    if sperre is None:
        print("    ✗ Community-Sperrliste nicht ladbar — SPERRLISTE_URL in .env prüfen (Export bricht sonst ab)")
    else:
        print(f"    ✓ Community-Sperrliste: {len(sperre)} gesperrte Domains, {sperre.quelle}")
    from . import blockliste as blockliste_mod
    print(f"    ✓ Eigene Blockliste: {len(blockliste_mod.laden())} Einträge (bereits kontaktiert)")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraper", description="Lead-Scraper (Clay-Nachbau)")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Keywords, Länder und ICP-Prompt anlegen")
    p_init.add_argument("--keywords", required=True, help="Kommagetrennt, z. B. 'Metallbau,Schlosserei'")
    p_init.add_argument("--countries", required=True, help="Kommagetrennt, z. B. 'DE,AT,CH'")
    p_init.add_argument("--min-population", type=int, default=1)
    p_init.add_argument("--icp-prompt", help="Pfad zur ICP-Prompt-Datei")
    p_init.add_argument("--pfad", choices=["google-maps", "recruiting"], default="google-maps",
                        help="Kampagnen-Art (Stellensuche startet mit dem Befehl stellensuche)")
    p_init.add_argument("--berufe", help="Recruiting: gesuchte Berufe, kommagetrennt, Reihenfolge = Priorität")
    p_init.add_argument("--nk", action="store_true",
                        help="Recruiting: passende Firmen OHNE offene Stelle auch anreichern (Satz zur Website)")
    p_init.set_defaults(func=cmd_init)

    p_tb = sub.add_parser("testballon",
                          help="Recruiting: beide Wege (Firmen-Website, Jobportale) mit je ~100 Leads vergleichen")
    p_tb.add_argument("--name", required=True, help="Name; legt kampagnen/<name>-website und <name>-portale an")
    p_tb.add_argument("--suche", required=True,
                      help="Gesuchte Berufe, kommagetrennt (Portale: Suchbegriffe, Website: --berufe)")
    p_tb.add_argument("--keywords", help="Branche(n) für Google Maps (Weg Firmen-Website), kommagetrennt")
    p_tb.add_argument("--land", default="DE")
    p_tb.add_argument("--min-population", type=int, default=50000, help="Städte ab dieser Einwohnerzahl (Standard 50.000)")
    p_tb.add_argument("--orte", help="Nur Portale: feste Orte statt --min-population")
    p_tb.add_argument("--ziel", type=int, default=100, help="Versandfertige Leads je Weg (Standard 100)")
    p_tb.add_argument("--budget", type=float, default=20.0, help="Höchstens so viele Euro Skael-Credits je Weg (Standard 20)")
    p_tb.add_argument("--wege", default="website,portale", help="website,portale (Standard: beide)")
    p_tb.add_argument("--icp-prompt", help="Optional: Prüfprofil für beide Wege (sonst: offene Stelle ist das Kriterium)")
    p_tb.add_argument("--opener-prompt", help="Optional: eigener Opener-Prompt für beide Wege")
    p_tb.add_argument("--stellen-prompt", help="Optional: eigene Stellenanalyse für den Weg Firmen-Website")
    p_tb.add_argument("--titel-pflicht", help="Nur Portale: siehe stellensuche --titel-pflicht")
    p_tb.add_argument("--titel-ausschluss", help="Nur Portale: siehe stellensuche --titel-ausschluss")
    p_tb.add_argument("--nur-marktprobe", action="store_true",
                      help="Nur die günstigen Suchen (Maps bzw. Portale) für eine Marktgröße, ohne Anreicherung")
    p_tb.add_argument("--nur-bericht", action="store_true", help="Nichts abfragen, nur den Vergleich neu schreiben")
    p_tb.set_defaults(func=cmd_testballon)

    p_tbl = sub.add_parser("testballon-lauf",
                           help="Testballon in dieser Kampagne (wird von testballon aufgerufen)")
    p_tbl.add_argument("--ziel", type=int, default=100)
    p_tbl.add_argument("--budget", type=float, help="Euro Skael-Credits für diese Kampagne (gilt dauerhaft)")
    p_tbl.add_argument("--nur-marktprobe", action="store_true")
    p_tbl.set_defaults(func=cmd_testballon_lauf)

    p_job = sub.add_parser("stellensuche",
                           help="Stellensuche: konkrete Stellen in Jobportalen suchen (Indeed, Stepstone, …)")
    p_job.add_argument("--suche", help="Suchbegriffe, kommagetrennt, z. B. 'Berufskraftfahrer,LKW-Fahrer' "
                                       "(weglassen = nur Einstellungen der Kampagne ändern)")
    p_job.add_argument("--orte", help="Orte oder PLZ, kommagetrennt, z. B. 'Stuttgart,Ulm' (ohne: landesweit)")
    p_job.add_argument("--min-population", type=int,
                       help="Statt --orte: alle Städte des Landes ab dieser Einwohnerzahl")
    p_job.add_argument("--land", default="DE", help="Land (Standard DE)")
    p_job.add_argument("--portale", default=",".join(PORTALE),
                       help=f"Kommagetrennt, Standard: {','.join(PORTALE)}")
    p_job.add_argument("--max-alter", type=int, help="Nur Anzeigen der letzten n Tage (Standard 30)")
    p_job.add_argument("--max-seiten", type=int, help="Höchstens n Ergebnisseiten à 100 je Suche (Standard 3)")
    p_job.add_argument("--umkreis", type=int, help="Umkreis um jeden Ort in km (Standard 25)")
    p_job.add_argument("--nur-stellen", action=argparse.BooleanOptionalAction, default=None,
                       help="Nur Stellen- und Firmenliste, ohne Website-Suche, Kontaktdaten und Texte")
    p_job.add_argument("--groessen-check", action=argparse.BooleanOptionalAction, default=None,
                       help="Konzerne, öffentliche Hand/Verbände und IT-Wettbewerber vor der Website-Suche "
                            "aussortieren (Standard: an; --no-groessen-check schaltet ab)")
    p_job.add_argument("--titel-ausschluss",
                       help="Wortteile, die in der Stellenbezeichnung nicht vorkommen dürfen, z. B. 'SPS,Elektro' "
                            "(wirkt ohne neue Abfrage beim nächsten run --stage 1k)")
    p_job.add_argument("--titel-pflicht",
                       help="Mindestens einer dieser Begriffe muss in der Stellenbezeichnung stehen, z. B. 'KI,AI,RPA' "
                            "(bis 3 Zeichen nur als ganzes Wort; wirkt ohne neue Abfrage beim nächsten run --stage 1k)")
    p_job.add_argument("--icp-prompt", help="Optional: Prüfprofil für die Firmen-Websites (Standard: icp.txt der Kampagne)")
    p_job.add_argument("--opener-prompt",
                       help="Opener-Prompt (Kampagne/prompts/ oder prompts/), Standard personalisierung_stellenanzeige.txt")
    p_job.set_defaults(func=cmd_stellensuche)

    p_run = sub.add_parser("run", help="Pipeline ausführen")
    p_run.add_argument("--stage", default="all",
                       choices=["all", "1", "1j", "1k", "2", "3", "3g", "3a", "3b", "3c", "3e", "3d",
                                "4", "4a", "4b", "4c", "4d", "4e", "4f", "4g", "4h"])
    p_run.add_argument("--budget", type=float,
                       help="Höchstens so viele Euro Skael-Credits für diese Kampagne (gilt dauerhaft; 0 = ohne Deckel)")
    p_run.add_argument("--limit", type=int,
                       help="Nur n Zeilen verarbeiten (Dry-Run; Stellensuche: n Suchen, mit --stage 3a: n Website-Suchen)")
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="Fortschritt anzeigen")
    p_status.set_defaults(func=cmd_status)

    p_export = sub.add_parser("export", help="CSV exportieren")
    p_export.add_argument("--all", action="store_true", help="Auch nicht versandfertige Leads")
    p_export.add_argument("--mark", action="store_true", help="Exportierte Leads markieren")
    p_export.add_argument("--einzeln", action="store_true",
                          help="Eine Gesamtliste statt der vier getrennten Listen")
    p_export.add_argument("--lead-format", action="store_true",
                          help="Zusätzlich leads_<kampagne>_<zeit>.json im festen Lead-Format (nur Listen 1 und 2)")
    p_export.set_defaults(func=cmd_export)

    p_icp = sub.add_parser("set-icp", help="ICP-Prompt nachträglich setzen")
    p_icp.add_argument("file")
    p_icp.set_defaults(func=cmd_icp)

    p_neu = sub.add_parser("neue-kampagne", help="kampagnen/<name>/ aus der Vorlage anlegen")
    p_neu.add_argument("name")
    p_neu.set_defaults(func=cmd_neue_kampagne)

    p_ausw = sub.add_parser("auswahl", help="Nur N Firmen prüfen, den Rest zurückstellen")
    p_ausw.add_argument("--firmen", type=int, required=True)
    p_ausw.add_argument("--reihenfolge", choices=["groesse", "zufall"], default="groesse")
    p_ausw.set_defaults(func=cmd_auswahl)

    p_nach = sub.add_parser("nachziehen", help="N zurückgestellte Firmen wieder aufnehmen")
    p_nach.add_argument("--firmen", type=int, required=True)
    p_nach.set_defaults(func=cmd_nachziehen)

    p_sch = sub.add_parser("schaetzen", help="Kosten für eine Zielmenge schätzen")
    p_sch.add_argument("--leads", type=int, required=True)
    p_sch.set_defaults(func=cmd_schaetzen)

    p_block = sub.add_parser("blockliste-import",
                             help="Bereits kontaktierte Leads (CSV) auf die eigene Blockliste setzen")
    p_block.add_argument("file")
    p_block.set_defaults(func=cmd_blockliste_import)

    p_doctor = sub.add_parser("doctor", help="Zugänge, Prompts und Erreichbarkeit prüfen")
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


def _check_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit(
            f"Python 3.10 oder neuer nötig — gefunden: {sys.version.split()[0]}\n"
            "macOS/Linux:  brew install python@3.12   bzw.  apt install python3.12\n"
            "Danach denselben Befehl mit python3.12 statt python3 aufrufen."
        )


def main(argv: list[str] | None = None) -> int:
    _check_python()
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

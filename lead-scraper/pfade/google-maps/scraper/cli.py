"""Kommandozeile — bildet die Clay-Stufen als einzeln aufrufbare Schritte ab.

Beispiele:
    python -m scraper init --keywords "Metallbau,Schlosserei" --countries DE,AT,CH \
                           --min-population 1 --icp-prompt prompts/icp_beispiel_metallbau.txt
    python -m scraper run --stage all
    python -m scraper run --stage 2 --limit 5      # Dry-Run über 5 Städte
    python -m scraper status
    python -m scraper export
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import db, export as export_mod, pipeline
from .clients import FindymailClient, SkaelClient
from .config import CONFIG, ROOT
from .llm import LLM


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_init(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)

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

    if args.icp_prompt:
        path = Path(args.icp_prompt)
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            raise SystemExit(f"ICP-Prompt-Datei nicht gefunden: {path}")
        db.set_meta(conn, "icp_prompt", path.read_text(encoding="utf-8"))
        print(f"ICP-Prompt übernommen aus {path}")

    db.set_meta(conn, "keywords", keywords)
    db.set_meta(conn, "countries", countries)
    print(f"{len(keywords)} Keywords × {len(countries)} Länder = "
          f"{len(keywords) * len(countries)} Kombinationen angelegt.")
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
    needs_llm = stage in ("all", "3", "3a", "4", "4a", "4d", "4e", "4f")
    if needs_llm:
        CONFIG.require("openai_api_key")

    if stage in ("all", "1"):
        pipeline.stufe1_staedte(conn, skael)
    if stage in ("all", "2"):
        pipeline.stufe2_maps(conn, skael, limit=args.limit)
    if stage in ("all", "3", "3a"):
        pipeline.stufe3a_domains(conn, llm)
    if stage in ("all", "3", "3b"):
        pipeline.stufe3b_dedupe(conn)
    if stage in ("all", "3", "3c"):
        pipeline.stufe3c_icp(conn, skael, icp_prompt)
    if stage in ("all", "3", "3d"):
        pipeline.stufe3d_uebergabe(conn)
    if stage in ("all", "4", "4a"):
        pipeline.stufe4a_website_final(conn, llm)
    if stage in ("all", "4", "4b"):
        pipeline.stufe4b_impressum(conn, skael)
    if stage in ("all", "4", "4c"):
        pipeline.stufe4c_emails(conn, skael, findymail)
    if stage in ("all", "4", "4d"):
        pipeline.stufe4d_anrede(conn, llm)
    if stage in ("all", "4", "4e"):
        pipeline.stufe4e_personalisierung(conn, skael, llm)
    if stage in ("all", "4", "4f"):
        pipeline.stufe4f_videotitel(conn, llm)
    if stage in ("all", "4", "4g"):
        pipeline.stufe4g_linkedin(conn, skael)
    if stage in ("all", "4", "4h"):
        pipeline.stufe4h_ready(conn)

    cmd_status(args)


def cmd_status(args: argparse.Namespace) -> None:  # noqa: ARG001
    conn = db.connect()
    db.init(conn)
    s = db.stats(conn)
    print()
    print("  Stufe 1  Keyword × Land       ", f"{s['eingabe_done']}/{s['eingabe']} erledigt")
    print("  Stufe 2  Städte-Queries       ", f"{s['verarbeitung_done']}/{s['verarbeitung']} erledigt")
    print("  Stufe 3  Firmen gefunden      ", s["datensaetze"])
    print("           nach Dedupe          ", s["datensaetze_kept"])
    print("           ICP true / false     ", f"{s['icp_true']} / {s['icp_false']}")
    print("  Stufe 4  Leads in Anreicherung", s["anreicherung"])
    print("           mit E-Mail           ", s["mit_email"])
    print("           Ready to Send        ", s["ready_to_send"])
    print()


def cmd_export(args: argparse.Namespace) -> None:
    conn = db.connect()
    db.init(conn)
    if args.einzeln:
        path = export_mod.export_csv(conn, only_ready=not args.all)
        print(f"Export geschrieben: {path}")
    else:
        print()
        for bezeichnung, pfad, anzahl in export_mod.export_listen(conn, only_ready=not args.all):
            print(f"  {anzahl:>6} Zeilen  {bezeichnung}")
            print(f"                 {pfad}")
        print()
    if args.mark:
        count = export_mod.mark_exported(conn)
        print(f"{count} Leads als 'bereits exportiert' markiert.")


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
    placeholders = ("dein_key", "your_api_key", "...", "…", "xxx", "hier_eintragen", "changeme")

    print()
    print("  Zugangsdaten")
    for label, value in (
        ("SKAEL_API_KEY", CONFIG.skael_api_key),
        ("OPENAI_API_KEY", CONFIG.openai_api_key),
        ("FINDYMAIL_API_KEY (optional)", CONFIG.findymail_api_key),
    ):
        is_placeholder = value and any(p in value.lower() for p in placeholders)
        if is_placeholder:
            mark, hint = "✗", "noch Platzhalter aus .env.example"
        elif value:
            mark, hint = "✓", f"…{value[-6:]}"
        else:
            mark, hint = "✗", "nicht gesetzt"
        print(f"    {mark} {label:<30} {hint}")

    print()
    print("  Prompt-Dateien")
    from .config import PROMPTS_DIR

    for name in ("company_domain.txt", "anrede.txt", "anrede.schema.json",
                 "personalisierung.txt", "personalisierung.schema.json",
                 "video_title_cleanup.txt", "video_title_cleanup.schema.json"):
        exists = (PROMPTS_DIR / name).exists()
        print(f"    {'✓' if exists else '✗'} {name}")

    conn = db.connect()
    db.init(conn)
    icp = db.get_meta(conn, "icp_prompt", "") or ""
    print()
    print(f"  ICP-Prompt: {'✓ hinterlegt (' + str(len(icp)) + ' Zeichen)' if icp else '✗ fehlt — `scraper set-icp <datei>`'}")

    print()
    print("  Erreichbarkeit")
    if CONFIG.skael_api_key and not any(p in CONFIG.skael_api_key.lower() for p in placeholders):
        try:
            out = SkaelClient().find_cities("LU", 100000, limit=1)
            print(f"    ✓ Skael API erreichbar (Testabfrage lieferte {out.get('total', '?')} Städte für LU)")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Skael API: {exc}")
    else:
        print("    – Skael übersprungen (kein Key)")

    if CONFIG.findymail_api_key and not any(p in CONFIG.findymail_api_key.lower() for p in placeholders):
        try:
            guthaben = FindymailClient().credits()
            print(f"    ✓ Findymail erreichbar ({guthaben.get('credits', '?')} Finder-Credits, "
                  f"{guthaben.get('verifier_credits', '?')} Verifier-Credits übrig)")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ Findymail: {exc}")
    else:
        print("    – Findymail übersprungen (kein Key; nur Skael sucht Geschäftsführer-Adressen)")

    from . import sperrliste as sperrliste_mod
    try:
        sperre = sperrliste_mod.laden(pflicht=False)
    except SystemExit:
        sperre = None
    if sperre is None:
        print("    ✗ Community-Sperrliste nicht ladbar — SPERRLISTE_URL in .env prüfen (Export bricht sonst ab)")
    else:
        print(f"    ✓ Community-Sperrliste: {len(sperre)} gesperrte Domains, {sperre.quelle}")
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
    p_init.set_defaults(func=cmd_init)

    p_run = sub.add_parser("run", help="Pipeline ausführen")
    p_run.add_argument("--stage", default="all",
                       choices=["all", "1", "2", "3", "3a", "3b", "3c", "3d",
                                "4", "4a", "4b", "4c", "4d", "4e", "4f", "4g", "4h"])
    p_run.add_argument("--limit", type=int, help="Nur n Zeilen verarbeiten (Dry-Run)")
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="Fortschritt anzeigen")
    p_status.set_defaults(func=cmd_status)

    p_export = sub.add_parser("export", help="CSV exportieren")
    p_export.add_argument("--all", action="store_true", help="Auch nicht versandfertige Leads")
    p_export.add_argument("--mark", action="store_true", help="Exportierte Leads markieren")
    p_export.add_argument("--einzeln", action="store_true",
                          help="Eine Gesamtliste statt der vier getrennten Listen")
    p_export.set_defaults(func=cmd_export)

    p_icp = sub.add_parser("set-icp", help="ICP-Prompt nachträglich setzen")
    p_icp.add_argument("file")
    p_icp.set_defaults(func=cmd_icp)

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

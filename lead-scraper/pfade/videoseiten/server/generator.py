#!/usr/bin/env python3
"""Build one landing page per lead from the template (index.html).

The template contains exactly one block between `/* LEAD:START */` and
`/* LEAD:END */`. For every lead that block is replaced by the lead's data;
everything else (ABSENDER, SEITE, layout) stays as the customer designed it.

    python3 generator.py --vorlage vorlage/index.html --leads leads.json --ziel /srv/seiten

leads.json: a list of objects in the fixed lead format plus video_url,
video_vorschaubild, video_titel (and optionally seiten_id). Output per lead:
<ziel>/v/<seiten_id>/index.html and .meta.json, plus <ziel>/ergebnis.json
with the link for each externe_id. A page already in <ziel> for the same
externe_id keeps its seiten_id and lifetime, so re-runs never break sent links.
Standard library only.
"""
from __future__ import annotations

import argparse
import http.client
import json
import random
import re
import secrets
import shutil
import string
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

LEAD_FIELDS = [
    "externe_id", "firma", "rechtsform", "domain", "website", "strasse", "plz", "ort", "land",
    "telefon", "branche", "mitarbeiter", "handelsregister", "anrede", "vorname", "nachname",
    "position", "email", "email_typ", "email_status", "kontakt_telefon", "linkedin_url",
    "quelle", "quelle_url", "erfasst_am",
]
VIDEO_FIELDS = ["video_url", "video_vorschaubild", "video_titel"]
# Never written into a page: contact data and internal status stay in the lead store.
# The lead source (search method, URL) stays internal as proof; the page only names public sources in general.
NEVER_PUBLISHED = {"email", "email_typ", "email_status", "telefon", "kontakt_telefon", "strasse", "handelsregister", "linkedin_url",
                   "quelle", "quelle_url"}
REQUIRED = ["externe_id", "firma", "quelle", "quelle_url", "erfasst_am", "video_url"]

SEITEN_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")
LEAD_BLOCK_RE = re.compile(r"/\* LEAD:START \*/.*?/\* LEAD:END \*/", re.S)
FRAME_SRC_RE = re.compile(r"frame-src https://[^;\"\s]+")
CONFIG_BLOCK_RE = re.compile(r"const ABSENDER.*?</script>", re.S)
PLACEHOLDER_RE = re.compile(r"<[^<>\"\n/][^<>\"\n]*>")
ALPHABET = string.ascii_letters + string.digits


def new_seiten_id() -> str:
    """22 random base62 characters, about 131 bits."""
    return "".join(secrets.choice(ALPHABET) for _ in range(22))


def js_literal(data: dict) -> str:
    """JSON that is safe inside <script>: no '</', no U+2028/2029."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def check_template(html: str, probe: bool) -> None:
    if len(LEAD_BLOCK_RE.findall(html)) != 1:
        sys.exit("Vorlage: genau ein Block /* LEAD:START */ … /* LEAD:END */ erwartet.")
    config = CONFIG_BLOCK_RE.search(html)
    if not config:
        sys.exit("Vorlage: Block const ABSENDER … nicht gefunden.")
    open_values = sorted(set(PLACEHOLDER_RE.findall(config.group(0).removesuffix("</script>"))))
    if open_values and not probe:
        sys.exit("Vorlage enthält noch Platzhalter, Seiten werden nicht veröffentlicht:\n  " + "\n  ".join(open_values))


def problems(lead: dict) -> list[str]:
    errs = [f"{f} fehlt" for f in REQUIRED if not str(lead.get(f) or "").strip()]
    url = str(lead.get("video_url") or "")
    if url and (urlparse(url).scheme != "https" or "/embed/" not in url):
        errs.append("video_url ist keine https-Embed-Adresse")
    sid = lead.get("seiten_id")
    if sid and not SEITEN_ID_RE.match(sid):
        errs.append("seiten_id hat nicht 22 Zeichen A-Z a-z 0-9")
    return errs


THUMB_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

# Short retry (this file also runs on the server and must stay dependency-free, so it does not use
# werkzeuge/wiederholen.py): 3 attempts, pauses 1 s and 2 s (+ up to 25 % jitter), Retry-After up to 10 s.
# A thumbnail that still fails falls back to the default image, it never stops the run.
WIEDERHOLBAR = {408, 425, 429, 500, 502, 503, 504}
THUMB_VERSUCHE = 3
THUMB_PAUSE = 1.0
THUMB_PAUSE_MAX = 10.0


def _pause(versuch: int, retry_after: str | None = None) -> float:
    if retry_after and retry_after.strip().isdigit():
        return min(float(retry_after.strip()), THUMB_PAUSE_MAX)
    basis = min(THUMB_PAUSE * 2 ** (versuch - 1), THUMB_PAUSE_MAX)
    return basis + random.uniform(0, basis * 0.25)


def fetch_thumbnail(url: str, target: Path) -> str:
    """Copy Skael's preview image next to the page so the visitor's browser never asks Skael before the click.

    Raises OSError if the image cannot be fetched (after retries for temporary errors)."""
    if not url.startswith("https://"):
        return url
    # Cloudflare in front of Skael answers 403 to the default Python user agent
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; videoseiten-generator)"})
    for versuch in range(1, THUMB_VERSUCHE + 1):
        retry_after = None
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (https enforced above)
                # Skael serves JPEG under ".png": trust the content type, not the file name
                suffix = THUMB_TYPES.get(resp.headers.get_content_type()) or Path(urlparse(url).path).suffix or ".jpg"
                daten = resp.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in WIEDERHOLBAR or versuch >= THUMB_VERSUCHE:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
        except (OSError, http.client.HTTPException) as exc:  # network, timeout, dropped connection
            if versuch >= THUMB_VERSUCHE:
                raise OSError(f"{type(exc).__name__}: {exc}") from exc
        time.sleep(_pause(versuch, retry_after))
    target.with_suffix(suffix).write_bytes(daten)
    return "vorschau" + suffix


def build(args: argparse.Namespace) -> int:
    template = Path(args.vorlage).read_text(encoding="utf-8")
    check_template(template, args.probe)
    leads = json.loads(Path(args.leads).read_text(encoding="utf-8"))
    ziel = Path(args.ziel)
    (ziel / "v").mkdir(parents=True, exist_ok=True)

    assets = Path(args.vorlage).parent / "assets"
    if assets.is_dir():
        shutil.copytree(assets, ziel / "assets", dirs_exist_ok=True)

    # A second run (e.g. after a text fix) must keep links that may already be sent and keep their lifetime.
    bestehend = {}
    for meta_file in (ziel / "v").glob("*/.meta.json"):
        try:
            alt = json.loads(meta_file.read_text(encoding="utf-8"))
            bestehend[alt["externe_id"]] = alt
        except (ValueError, KeyError):
            continue

    now = datetime.now(timezone.utc)
    result, failed = [], []
    for lead in leads:
        errs = problems(lead)
        if errs:
            failed.append({"externe_id": lead.get("externe_id"), "fehler": errs})
            continue
        alt = bestehend.get(lead["externe_id"], {})
        sid = lead.get("seiten_id") or alt.get("seiten_id") or new_seiten_id()
        if alt.get("seiten_id") != sid:
            alt = {}
        page_dir = ziel / "v" / sid
        page_dir.mkdir(parents=True, exist_ok=True)

        data = {"seiten_id": sid}
        for f in LEAD_FIELDS + VIDEO_FIELDS:
            data[f] = "" if f in NEVER_PUBLISHED else (lead.get(f) or "")
        if data["video_vorschaubild"]:
            try:
                data["video_vorschaubild"] = fetch_thumbnail(data["video_vorschaubild"], page_dir / "vorschau")
            except OSError as exc:
                print(f"{lead['externe_id']}: Vorschaubild nicht geladen ({exc}), nehme Standardbild", file=sys.stderr)
                data["video_vorschaubild"] = ""
        if not data["video_vorschaubild"] and (ziel / "assets" / "video-vorschau.svg").is_file():
            data["video_vorschaubild"] = "/assets/video-vorschau.svg"

        video_origin = "{0.scheme}://{0.netloc}".format(urlparse(data["video_url"]))
        html = LEAD_BLOCK_RE.sub(lambda _: f"/* LEAD:START */\nconst LEAD = {js_literal(data)};\n/* LEAD:END */", template)
        html = FRAME_SRC_RE.sub(f"frame-src {video_origin}", html)
        # pages live at /v/<id>/, shared files at /assets/
        html = html.replace('"assets/', '"/assets/').replace("url(\"assets/", "url(\"/assets/")
        (page_dir / "index.html").write_text(html, encoding="utf-8")

        meta = {
            "seiten_id": sid,
            "externe_id": lead["externe_id"],
            "erstellt": alt.get("erstellt") or now.isoformat(timespec="seconds"),
            "ablauf": alt.get("ablauf") or (now + timedelta(days=args.laufzeit)).isoformat(timespec="seconds"),
        }
        (page_dir / ".meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        result.append({"externe_id": lead["externe_id"], "seiten_id": sid, "link": f"{args.basis.rstrip('/')}/v/{sid}/",
                       "vorschaubild": data["video_vorschaubild"]})

    (ziel / "ergebnis.json").write_text(json.dumps({"seiten": result, "fehler": failed}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(result)} Seiten erstellt, {len(failed)} übersprungen. Links: {ziel / 'ergebnis.json'}")
    for f in failed:
        print(f"  übersprungen {f['externe_id']}: {', '.join(f['fehler'])}")
    return 0


def cleanup(args: argparse.Namespace) -> int:
    """Delete pages whose lifetime is over. Run daily (cron)."""
    now = datetime.now(timezone.utc)
    removed = 0
    for meta_file in Path(args.ziel, "v").glob("*/.meta.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if datetime.fromisoformat(meta["ablauf"]) <= now:
            shutil.rmtree(meta_file.parent)
            removed += 1
    print(f"{removed} abgelaufene Seiten gelöscht.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Landingpages je Lead erzeugen")
    p.add_argument("--ziel", required=True, help="Ordner, den der Webserver ausliefert")
    p.add_argument("--vorlage", help="index.html mit LEAD-Block")
    p.add_argument("--leads", help="leads.json")
    p.add_argument("--basis", default="https://angebot.example", help="öffentliche Adresse, z. B. https://angebot.kunde.de")
    p.add_argument("--laufzeit", type=int, default=90, help="Tage bis zur Löschung")
    p.add_argument("--probe", action="store_true", help="Platzhalter in der Vorlage erlauben (nur zum Testen)")
    p.add_argument("--aufraeumen", action="store_true", help="nur abgelaufene Seiten löschen")
    args = p.parse_args()
    if args.aufraeumen:
        return cleanup(args)
    if not (args.vorlage and args.leads):
        p.error("--vorlage und --leads sind nötig")
    return build(args)


if __name__ == "__main__":
    raise SystemExit(main())

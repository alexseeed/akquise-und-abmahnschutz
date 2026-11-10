#!/usr/bin/env python3
"""Read a customer's branding from their own website and apply it to the video page template.

    python3 branding.py lesen --url beispiel.de [--aus pfade/videoseiten/arbeit/branding]
    python3 branding.py schriften --familie "Open Sans" --gewichte 400,600,700 --aus <vorlage>/assets/fonts
    python3 branding.py anwenden --vorlage <vorlage>/index.html --branding <aus>/branding.json \
        [--titel-schrift "Montserrat" --text-schrift "Open Sans"]

lesen      Loads the start page plus up to 10 linked stylesheets (GET only, browser user agent,
           robots.txt respected, short pauses) and writes branding.json: colours, fonts, logo
           (downloaded to <aus>/logo.<ext>), imprint/privacy links and the company name.
schriften  Downloads a Google Font as woff2 (latin + latin-ext only) and writes/extends fonts.css
           with local @font-face rules, so the page loads nothing from third parties.
anwenden   Writes colours, logo, @font-face rules and font variables into the template
           (backup: index.html.bak). Only targeted replacements, no reformatting.

Only evaluate the customer's own website - that is the purpose of this tool.
Standard library only (Python 3.9+).
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import http.client
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import namedtuple
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiederholen  # noqa: E402  (shared retry rule, werkzeuge/wiederholen.py)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIER = Path(__file__).resolve().parent
STANDARD_AUS = HIER.parent / "arbeit" / "branding"

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
TIMEOUT = 15
MAX_CSS = 10
MAX_BYTES = 5_000_000
PAUSE = 0.25  # seconds between requests to the customer's server
# The customer's website is fetched many times (robots.txt, page, CSS, logo, fonts): keep retries short,
# so a dead site fails after seconds, not minutes. MAX_RETRIES can lower it further.
MAX_VERSUCHE_WEBSITE = 3

GOOGLE_CSS2 = "https://fonts.googleapis.com/css2"
GOOGLE_SUBSETS = ("latin", "latin-ext")

BRAND_VAR = re.compile(r"primary|accent|brand|akzent|haupt|main-?colou?r|theme-?colou?r", re.I)
TEXT_VAR = re.compile(r"(^|-)(text|body|foreground|fg|font)(-?colou?r)?($|-)", re.I)
GRUND_VAR = re.compile(r"(^|-)(background|bg|body-bg|surface|base)(-?colou?r)?($|-)", re.I)
TITEL_FONT_VAR = re.compile(r"head|title|titel|display|primary-font|typography-primary", re.I)
TEXT_FONT_VAR = re.compile(r"body|text|base|copy|typography-text|paragraph", re.I)
BUTTON_SEL = re.compile(r"btn|button|knopf|cta|submit|wp-block-button|elementor-button", re.I)
LINK_SEL = re.compile(r"(^|[\s>+~,(])a([:.\[\s,]|$)")
# Third-party widgets and CMS defaults that say nothing about the brand.
LAERM_SEL = re.compile(r"wpadminbar|cookie|borlabs|cmplz|usercentrics|onetrust|cky-|^\s*\.has-|wp-block-cover|mejs", re.I)
LAERM_VAR = re.compile(r"^--(wp--preset--|wp-admin|bs-(blue|indigo|purple|pink|red|orange|yellow|green|teal|cyan|gray|info|warning|danger|success))", re.I)
# Framework defaults (Bootstrap, Elementor, WordPress palette): usually not the brand colour.
FRAMEWORK_FARBEN = {
    "#0D6EFD", "#007BFF", "#337AB7", "#6EC1E4", "#61CE70", "#54595F", "#7A7A7A",
    "#CF2E2E", "#FF6900", "#FCB900", "#7BDCB5", "#00D084", "#8ED1FC", "#0693E3",
    "#9B51E0", "#ABB8C3", "#F78DA7", "#2271B1", "#21759B", "#0073AA",
}
BENANNTE_FARBEN = {"white": "#FFFFFF", "black": "#000000"}
GENERISCHE_SCHRIFTEN = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif",
    "ui-serif", "ui-monospace", "-apple-system", "blinkmacsystemfont", "inherit", "initial",
    "unset", "revert", "emoji", "math",
}
SYSTEM_SCHRIFTEN = {
    "arial", "helvetica", "helvetica neue", "georgia", "times", "times new roman", "verdana",
    "tahoma", "segoe ui", "trebuchet ms", "courier new", "calibri", "cambria", "garamond",
    "san francisco", "sf pro", "sf pro text", "sf pro display", "menlo", "consolas", "impact",
}
SERIF_HINWEISE = re.compile(
    r"serif|times|georgia|garamond|baskerville|bodoni|didot|playfair|merriweather|lora|"
    r"cormorant|slab|caslon|minion|crimson|libre caslon|gelasio|spectral", re.I)

# Small similarity table: commercial/system fonts -> two free Google Fonts.
AEHNLICHE_SCHRIFTEN = [
    ("helvetica", ["Inter", "Arimo"]),
    ("arial", ["Arimo", "Inter"]),
    ("neue haas", ["Inter", "Inter Tight"]),
    ("akzidenz", ["Inter", "Work Sans"]),
    ("futura", ["Jost", "Outfit"]),
    ("avenir", ["Nunito Sans", "Mulish"]),
    ("gotham", ["Montserrat", "Outfit"]),
    ("proxima", ["Figtree", "Montserrat"]),
    ("gill sans", ["Lato", "Cabin"]),
    ("frutiger", ["Hind", "Open Sans"]),
    ("myriad", ["PT Sans", "Source Sans 3"]),
    ("segoe", ["Open Sans", "Noto Sans"]),
    ("san francisco", ["Inter", "Roboto"]),
    ("sf pro", ["Inter", "Roboto"]),
    ("calibri", ["Carlito", "Open Sans"]),
    ("verdana", ["PT Sans", "Noto Sans"]),
    ("tahoma", ["PT Sans", "Noto Sans"]),
    ("din", ["Barlow", "Roboto Condensed"]),
    ("univers", ["Roboto", "Archivo"]),
    ("circular", ["DM Sans", "Plus Jakarta Sans"]),
    ("graphik", ["Inter", "Manrope"]),
    ("sofia", ["Nunito", "Lexend"]),
    ("museo sans", ["Mulish", "Nunito Sans"]),
    ("brandon", ["Josefin Sans", "Raleway"]),
    ("trade gothic", ["Archivo Narrow", "Oswald"]),
    ("garamond", ["EB Garamond", "Cormorant Garamond"]),
    ("times", ["Tinos", "Libre Baskerville"]),
    ("georgia", ["Gelasio", "Merriweather"]),
    ("baskerville", ["Libre Baskerville", "Baskervville"]),
    ("didot", ["Playfair Display", "Bodoni Moda"]),
    ("bodoni", ["Bodoni Moda", "Playfair Display"]),
    ("minion", ["Crimson Pro", "Source Serif 4"]),
]


class HolFehler(Exception):
    """Raised when a resource cannot be fetched. wiederholbar: temporary (network, timeout, 429, 5xx)."""

    def __init__(self, meldung: str, code: int | None = None, wiederholbar: bool = False,
                 retry_after: int | None = None):
        super().__init__(meldung)
        self.code = code
        self.wiederholbar = wiederholbar
        self.retry_after = retry_after


Antwort = namedtuple("Antwort", "url status content_type daten")


# ---------------------------------------------------------------------------
# Network (single entry point, mocked in tests)
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: int = TIMEOUT, max_bytes: int = MAX_BYTES, accept: str | None = None) -> Antwort:
    """GET a URL with a normal browser user agent. Raises HolFehler on any failure.

    Temporary errors are retried with backoff (werkzeuge/wiederholen.py), at most
    MAX_VERSUCHE_WEBSITE attempts; 404 and other permanent errors fail at once."""
    versuche = min(wiederholen.max_versuche(), MAX_VERSUCHE_WEBSITE)
    for versuch in range(1, versuche + 1):
        try:
            return _http_get_einmal(url, timeout, max_bytes, accept)
        except HolFehler as e:
            if not e.wiederholbar or versuch >= versuche:
                raise
            time.sleep(wiederholen.wartezeit(versuch, e.code or 0, e.retry_after))
    raise HolFehler(f"nicht erreichbar: {url}")  # not reached: versuche >= 1


def _http_get_einmal(url: str, timeout: int, max_bytes: int, accept: str | None) -> Antwort:
    kopf = {
        "User-Agent": BROWSER_UA,
        "Accept": accept or "text/html,application/xhtml+xml,text/css,image/*,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.6",
    }
    req = urllib.request.Request(url, headers=kopf, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            daten = r.read(max_bytes + 1)
            if len(daten) > max_bytes:
                raise HolFehler(f"zu groß (> {max_bytes // 1_000_000} MB): {url}")
            return Antwort(r.geturl(), r.status, r.headers.get("Content-Type", ""), daten)
    except urllib.error.HTTPError as e:
        raise HolFehler(f"HTTP {e.code}: {url}", e.code, e.code in wiederholen.WIEDERHOLBAR,
                        wiederholen.retry_after_aus(e.headers)) from None
    except ValueError as e:  # invalid URL: retrying does not help
        raise HolFehler(f"nicht erreichbar ({e}): {url}") from None
    except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
        grund = str(getattr(e, "reason", None) or e)
        raise HolFehler(f"nicht erreichbar ({grund}): {url}",
                        wiederholbar=wiederholen.voruebergehend(0, grund)) from None


def text_aus(antwort: Antwort) -> str:
    m = re.search(r"charset=([\w-]+)", antwort.content_type or "", re.I)
    kodierung = m.group(1) if m else None
    if not kodierung:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", antwort.daten[:4000], re.I)
        kodierung = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    try:
        return antwort.daten.decode(kodierung, errors="replace")
    except LookupError:
        return antwort.daten.decode("utf-8", errors="replace")


class Robots:
    """robots.txt check for the customer's host (other hosts, e.g. CDNs, are not checked)."""

    def __init__(self, basis_url: str):
        teile = urllib.parse.urlsplit(basis_url)
        self.host = teile.netloc.lower()
        self.parser = None
        try:
            antwort = http_get(f"{teile.scheme}://{teile.netloc}/robots.txt", max_bytes=500_000)
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(text_aus(antwort).splitlines())
            self.parser = rp
        except HolFehler:
            pass  # no robots.txt -> everything allowed

    def erlaubt(self, url: str) -> bool:
        if self.parser is None or urllib.parse.urlsplit(url).netloc.lower() != self.host:
            return True
        return self.parser.can_fetch(BROWSER_UA, url)


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

def _kanal(wert: str, maximum: float = 255) -> float:
    wert = wert.strip()
    if wert.endswith("%"):
        return float(wert[:-1]) / 100 * maximum
    return float(wert)


def farbe_parsen(text: str):
    """Parse a single CSS colour. Returns (r, g, b, alpha) with 0-255 ints or None."""
    t = text.strip().lower()
    if t in BENANNTE_FARBEN:
        t = BENANNTE_FARBEN[t].lower()
    if t.startswith("#"):
        h = t[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
            return None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a
    m = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", t)
    if not m:
        return None
    teile = [p for p in re.split(r"[\s,/]+", m.group(2).strip()) if p]
    if len(teile) < 3:
        return None
    try:
        alpha = 1.0
        if len(teile) >= 4:
            alpha = _kanal(teile[3], 1.0)
        if m.group(1).startswith("rgb"):
            r, g, b = (max(0, min(255, round(_kanal(p)))) for p in teile[:3])
        else:
            hue = float(re.sub(r"deg$", "", teile[0])) % 360 / 360
            s, l = _kanal(teile[1], 1.0), _kanal(teile[2], 1.0)
            rf, gf, bf = colorsys.hls_to_rgb(hue, l, s)
            r, g, b = round(rf * 255), round(gf * 255), round(bf * 255)
    except ValueError:
        return None  # e.g. alpha given as var(...)
    return r, g, b, alpha


FARB_MUSTER = re.compile(r"#[0-9a-fA-F]{3,8}\b|(?:rgba?|hsla?)\([^()]*\)|\b(?:white|black)\b", re.I)


def farben_in(wert: str):
    """All parseable colours in a CSS value (url(...) parts ignored)."""
    wert = re.sub(r"url\([^)]*\)", "", wert, flags=re.I)
    for m in FARB_MUSTER.finditer(wert):
        f = farbe_parsen(m.group(0))
        if f:
            yield f


def hex_von(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def hls_von(rgb):
    return colorsys.rgb_to_hls(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)


def ist_bunt(f) -> bool:
    """Saturated, not near black/white/grey, mostly opaque."""
    if f[3] < 0.5:
        return False
    _, l, s = hls_von(f)
    return s >= 0.25 and 0.12 <= l <= 0.88 and (max(f[:3]) - min(f[:3])) >= 40


def abdunkeln(hexwert: str, anteil: float = 0.15) -> str:
    f = farbe_parsen(hexwert)
    return hex_von(tuple(round(c * (1 - anteil)) for c in f[:3]))


def luminanz(hexwert: str) -> float:
    """WCAG 2.x relative luminance."""
    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b, _ = farbe_parsen(hexwert)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def kontrast(hex_a: str, hex_b: str) -> float:
    la, lb = sorted((luminanz(hex_a), luminanz(hex_b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def lesbare_variante(hexwert: str, ziel: float = 4.5) -> str:
    """Darken step by step until white text reaches the target contrast."""
    wert = hexwert
    for _ in range(40):
        if kontrast("#FFFFFF", wert) >= ziel:
            return wert
        wert = abdunkeln(wert, 0.05)
    return wert


def abstand(a, b) -> float:
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])) ** 0.5


def aehnlicher_ton(a, b) -> bool:
    """Same colour in a lighter/darker shade (typical hover/active states)."""
    if abstand(a, b) < 20:
        return True
    ha, la, sa = hls_von(a)
    hb, lb, sb = hls_von(b)
    farbton = min(abs(ha - hb), 1 - abs(ha - hb))
    return farbton < 0.025 and abs(la - lb) < 0.12 and abs(sa - sb) < 0.2


# ---------------------------------------------------------------------------
# CSS parsing
# ---------------------------------------------------------------------------

Regel = namedtuple("Regel", "selektor deklarationen datei")  # deklarationen: list[(prop, value)]


def css_regeln(css: str, datei: str):
    """Very small CSS walker: returns (rules, font_face_blocks, imports).

    Handles comments, nested @media/@supports/@layer and skips @keyframes.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    importe = [m.group(1) or m.group(2) for m in re.finditer(
        r"@import\s+(?:url\(\s*[\"']?([^\"')]+)[\"']?\s*\)|[\"']([^\"']+)[\"'])", css, re.I)]
    regeln, font_faces = [], []
    i, n, start = 0, len(css), 0
    while i < n:
        c = css[i]
        if c == "{":
            prelude = css[start:i].strip()
            # find matching brace
            tiefe, j = 1, i + 1
            while j < n and tiefe:
                if css[j] == "{":
                    tiefe += 1
                elif css[j] == "}":
                    tiefe -= 1
                j += 1
            inhalt = css[i + 1:j - 1]
            pl = prelude.lower()
            if pl.startswith("@font-face"):
                font_faces.append(_deklarationen(inhalt))
            elif pl.startswith(("@media", "@supports", "@layer", "@container", "@document")):
                r, f, _ = css_regeln(inhalt, datei)
                regeln.extend(r)
                font_faces.extend(f)
            elif pl.startswith("@"):
                pass  # @keyframes, @page, ...
            elif "{" in inhalt:
                # CSS nesting: keep own declarations, recurse into nested rules
                eigene = re.sub(r"[^{};]*\{[^{}]*\}", "", inhalt)
                regeln.append(Regel(prelude, _deklarationen(eigene), datei))
                r, f, _ = css_regeln(inhalt, datei)
                regeln.extend(r)
            else:
                regeln.append(Regel(prelude, _deklarationen(inhalt), datei))
            i = j
            start = j
            continue
        if c in ";}":
            start = i + 1
        i += 1
    return regeln, font_faces, importe


def _deklarationen(block: str):
    paare = []
    for teil in re.split(r";(?![^(]*\))", block):
        if ":" not in teil:
            continue
        prop, _, wert = teil.partition(":")
        prop = prop.strip()
        wert = re.sub(r"\s*!important\s*$", "", wert.strip(), flags=re.I)
        if prop and wert:
            paare.append((prop if prop.startswith("--") else prop.lower(), wert))
    return paare


def variablen_sammeln(regeln):
    """Custom properties: name -> (value, rule). Prefer definitions on :root/html/body."""
    var = {}
    for regel in regeln:
        wurzel = re.search(r":root|^\s*html|^\s*body|\[data-theme", regel.selektor, re.I) is not None
        for prop, wert in regel.deklarationen:
            if not prop.startswith("--"):
                continue
            if prop not in var or (wurzel and not var[prop][2]):
                var[prop] = (wert, regel, wurzel)
    return var


def var_aufloesen(wert: str, var: dict, tiefe: int = 0) -> str:
    if "var(" not in wert or tiefe > 6:
        return wert

    def ersetze(m):
        name, _, ersatz = m.group(1).partition(",")
        name = name.strip()
        if name in var:
            return var_aufloesen(var[name][0], var, tiefe + 1)
        return var_aufloesen(ersatz.strip(), var, tiefe + 1) if ersatz else ""

    # innermost var() first
    neu = re.sub(r"var\(\s*([^()]*(?:\([^()]*\)[^()]*)*)\)", ersetze, wert)
    return var_aufloesen(neu, var, tiefe + 1) if neu != wert else neu


def selektor_hat_element(selektor: str, element: str) -> bool:
    return re.search(rf"(^|[\s>+~,(]){element}(?![\w-])", selektor, re.I) is not None


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

VOID_TAGS = {"img", "meta", "link", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr", "track"}
LOGO_HINWEIS = re.compile(r"logo|brand|marke|site-title|custom-logo", re.I)


class SeitenParser(HTMLParser):
    def __init__(self, quelltext: str):
        super().__init__(convert_charrefs=True)
        self.quelltext = quelltext
        self._zeilen = [0]
        for m in re.finditer("\n", quelltext):
            self._zeilen.append(m.end())
        self.metas, self.links, self.bilder, self.anker, self.svgs = [], [], [], [], []
        self.styles, self.inline_styles = [], []
        self.titel = ""
        self._im_titel = self._im_style = False
        self._kopf_stapel = []
        self._logo_stapel = []
        self._a = None
        self._svg_start = None
        self._svg_tiefe = 0
        self._svg_info = None

    def _offset(self):
        zeile, spalte = self.getpos()
        return self._zeilen[zeile - 1] + spalte

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        kennung = " ".join([a.get("class", ""), a.get("id", ""), a.get("aria-label", "")])
        im_logo = bool(self._logo_stapel)
        if tag not in VOID_TAGS and tag not in ("body", "html", "svg"):
            if tag in ("header", "nav") or re.search(r"(^|\s)(header|site-header|navbar|masthead)(\s|$)",
                                                     a.get("class", "") + " " + a.get("id", ""), re.I):
                self._kopf_stapel.append(tag)
            if LOGO_HINWEIS.search(kennung):
                self._logo_stapel.append(tag)
        im_kopf = bool(self._kopf_stapel)
        if tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "title":
            self._im_titel = True
        elif tag == "style":
            self._im_style = True
            self.styles.append("")
        elif tag == "a":
            self._a = {"href": a.get("href", ""), "text": "", "attrs": a, "im_kopf": im_kopf}
        elif tag == "img":
            self.bilder.append({
                "attrs": a, "im_kopf": im_kopf, "im_logo": im_logo,
                "home_link": self._a is not None and _ist_home(self._a["href"]),
            })
        elif tag == "svg":
            if self._svg_start is None:
                self._svg_start = self._offset()
                self._svg_tiefe = 1
                self._svg_info = {
                    "kennung": kennung + " " + a.get("role", ""),
                    "im_kopf": im_kopf, "im_logo": im_logo,
                    "home_link": self._a is not None and _ist_home(self._a["href"]),
                }
            else:
                self._svg_tiefe += 1
        if "style" in a and tag != "style":
            self.inline_styles.append((tag, a))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "svg" and self._svg_tiefe == 1 and self._svg_start is not None:
            self._svg_fertig()
        elif tag not in VOID_TAGS and tag != "svg":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._im_titel = False
        elif tag == "style":
            self._im_style = False
        elif tag == "a" and self._a is not None:
            self.anker.append(self._a)
            self._a = None
        elif tag == "svg" and self._svg_start is not None:
            self._svg_tiefe -= 1
            if self._svg_tiefe <= 0:
                self._svg_fertig()
        for stapel in (self._kopf_stapel, self._logo_stapel):
            if tag in stapel:
                idx = len(stapel) - 1 - stapel[::-1].index(tag)
                del stapel[idx:]

    def _svg_fertig(self):
        ende = self.quelltext.find(">", self._offset()) + 1
        self._svg_info["markup"] = self.quelltext[self._svg_start:ende]
        self.svgs.append(self._svg_info)
        self._svg_start, self._svg_info, self._svg_tiefe = None, None, 0

    def handle_data(self, data):
        if self._im_titel:
            self.titel += data
        if self._im_style and self.styles:
            self.styles[-1] += data
        if self._a is not None:
            self._a["text"] += data


def _ist_home(href: str) -> bool:
    if not href:
        return False
    teile = urllib.parse.urlsplit(href)
    return teile.path in ("", "/", "/index.html", "/de/", "/de") and not teile.query


# ---------------------------------------------------------------------------
# Analysis (pure, no network)
# ---------------------------------------------------------------------------

def analysiere(html: str, basis_url: str, css_dateien: list) -> dict:
    """Analyse the start page. css_dateien: list of (url, css_text). Returns the branding dict
    (without downloaded logo file)."""
    seite = SeitenParser(html)
    seite.feed(html)
    seite.close()

    alle_regeln, alle_ff = [], []
    google_urls = [urllib.parse.urljoin(basis_url, l.get("href", "")) for l in seite.links]
    for i, inline in enumerate(seite.styles):
        r, f, importe = css_regeln(inline, f"<style> #{i + 1} der Startseite")
        alle_regeln += r
        alle_ff += [(ff, basis_url) for ff in f]
        google_urls += importe
    for url, text in css_dateien:
        name = urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1] or url
        r, f, importe = css_regeln(text, name)
        google_urls += importe
        alle_regeln += [Regel(x.selektor, x.deklarationen, name) for x in r]
        alle_ff += [(ff, url) for ff in f]
    alle_regeln = [r for r in alle_regeln if not LAERM_SEL.search(r.selektor)]
    var = variablen_sammeln(alle_regeln)

    warnungen = []
    farben = farben_ermitteln(seite, alle_regeln, var, warnungen)
    schriften = schriften_ermitteln(seite, alle_regeln, alle_ff, var, google_familien(google_urls))
    logo_kandidaten = logo_kandidaten_ermitteln(seite, alle_regeln, basis_url, css_dateien)
    impressum, datenschutz = rechtliche_links(seite, basis_url)
    return {
        "quelle_url": basis_url,
        "abgerufen_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": name_ermitteln(seite, basis_url),
        "farben": farben,
        "schriften": schriften,
        "logo": {"datei": None, "kandidaten": logo_kandidaten},
        "impressum_url": impressum,
        "datenschutz_url": datenschutz,
        "geladene_css": [u for u, _ in css_dateien],
        "warnungen": warnungen,
    }


def farben_ermitteln(seite, regeln, var, warnungen) -> dict:
    punkte = {}  # hex -> {"punkte": float, "fundstellen": [(gewicht, text)], "rgb": tuple}

    def zaehle(f, gewicht, fundstelle):
        if not ist_bunt(f):
            return
        h = hex_von(f)
        if h in FRAMEWORK_FARBEN:
            gewicht *= 0.3
            fundstelle += " (Framework-Standardfarbe, abgewertet)"
        e = punkte.setdefault(h, {"punkte": 0.0, "fundstellen": [], "rgb": f[:3]})
        e["punkte"] += gewicht
        e["fundstellen"].append((gewicht, fundstelle))

    for name, (wert, regel, _) in var.items():
        if LAERM_VAR.search(name):
            continue
        if BRAND_VAR.search(name):
            for f in farben_in(var_aufloesen(wert, var)):
                zaehle(f, 6, f"CSS-Variable {name} ({regel.datei})")

    text_kand, grund_kand = [], []
    for regel in regeln:
        sel = regel.selektor
        ist_knopf = bool(BUTTON_SEL.search(sel))
        ist_link = bool(LINK_SEL.search(sel))
        ist_wurzel = selektor_hat_element(sel, "body") or selektor_hat_element(sel, "html")
        for prop, wert in regel.deklarationen:
            if prop.startswith("--"):
                if not LAERM_VAR.search(prop):
                    aufgeloest = var_aufloesen(wert, var)
                    for f in farben_in(aufgeloest):
                        if TEXT_VAR.search(prop[2:]) and not BRAND_VAR.search(prop):
                            text_kand.append((5, f, f"CSS-Variable {prop} ({regel.datei})"))
                        if GRUND_VAR.search(prop[2:]) and not BRAND_VAR.search(prop):
                            grund_kand.append((5, f, f"CSS-Variable {prop} ({regel.datei})"))
                continue
            if "color" not in prop and prop not in ("background", "border", "fill", "stroke", "outline", "box-shadow"):
                continue
            aufgeloest = var_aufloesen(wert, var)
            kurz = sel if len(sel) <= 60 else sel[:57] + "..."
            for f in farben_in(aufgeloest):
                gewicht = 1.0
                if ist_knopf and prop in ("background", "background-color"):
                    gewicht = 4
                elif ist_knopf:
                    gewicht = 2
                elif ist_link and prop == "color":
                    gewicht = 3
                zaehle(f, gewicht, f"{kurz} {{ {prop} }} ({regel.datei})")
                if ist_wurzel and prop == "color":
                    text_kand.append((10, f, f"{kurz} {{ color }} ({regel.datei})"))
                if ist_wurzel and prop in ("background", "background-color"):
                    grund_kand.append((10, f, f"{kurz} {{ {prop} }} ({regel.datei})"))
                if selektor_hat_element(sel, "p") and prop == "color":
                    text_kand.append((3, f, f"{kurz} {{ color }} ({regel.datei})"))

    for tag, attrs in seite.inline_styles:
        knopf = tag == "button" or BUTTON_SEL.search(attrs.get("class", ""))
        for prop, wert in _deklarationen(attrs.get("style", "")):
            if "color" in prop or prop == "background":
                for f in farben_in(var_aufloesen(wert, var)):
                    zaehle(f, 4 if knopf else 1, f"style-Attribut an <{tag}>")

    for meta in seite.metas:
        if meta.get("name", "").lower() == "theme-color":
            f = farbe_parsen(meta.get("content", ""))
            if f:
                zaehle(f, 8, "meta theme-color")

    # cluster near-identical shades (hover states etc.) into the strongest one
    gruppen = []
    for h, e in sorted(punkte.items(), key=lambda kv: -kv[1]["punkte"]):
        for g in gruppen:
            if aehnlicher_ton(g["rgb"], e["rgb"]):
                g["punkte"] += e["punkte"]
                g["fundstellen"] += e["fundstellen"]
                break
        else:
            gruppen.append({"wert": h, "rgb": e["rgb"], "punkte": e["punkte"], "fundstellen": list(e["fundstellen"])})
    gruppen.sort(key=lambda g: -g["punkte"])

    ergebnis = {}
    kandidaten = []
    for g in gruppen[:5]:
        fund = [t for _, t in sorted(g["fundstellen"], key=lambda x: -x[0])]
        kandidaten.append({"wert": g["wert"], "punkte": round(g["punkte"], 1), "fundstellen": list(dict.fromkeys(fund))[:3]})
    if kandidaten:
        bester = kandidaten[0]
        ergebnis["akzent"] = {"wert": bester["wert"], "fundstelle": bester["fundstellen"][0], "kandidaten": kandidaten}
    else:
        ergebnis["akzent"] = {"wert": None, "fundstelle": "keine bunte Farbe gefunden", "kandidaten": []}
        warnungen.append("Keine Akzentfarbe erkannt – bitte beim Nutzer erfragen.")

    def beste(liste, standard):
        liste = [x for x in liste if x[1][3] >= 0.5]
        if not liste:
            return standard
        gewicht, f, fund = max(liste, key=lambda x: x[0])
        return {"wert": hex_von(f), "fundstelle": fund}

    ergebnis["text"] = beste(text_kand, {"wert": None, "fundstelle": "nicht gefunden – Vorlagenwert bleibt"})
    ergebnis["grund"] = beste(grund_kand, {"wert": "#FFFFFF", "fundstelle": "Browser-Standard (keine Angabe gefunden)"})

    akzent = ergebnis["akzent"]["wert"]
    if akzent:
        ergebnis["akzent_dunkel"] = {"wert": abdunkeln(akzent), "fundstelle": "berechnet: Akzent 15 % dunkler"}
        k = kontrast("#FFFFFF", akzent)
        info = {"verhaeltnis": k, "ok": k >= 4.5, "warnung": None}
        if k < 4.5:
            vorschlag = lesbare_variante(akzent)
            info["warnung"] = (f"Weiße Schrift auf {akzent} hat nur {k}:1 (WCAG verlangt 4.5:1). "
                               f"Lesbare dunklere Variante: {vorschlag}.")
            info["lesbare_variante"] = vorschlag
            warnungen.append(info["warnung"])
        ergebnis["kontrast_weiss_auf_akzent"] = info
    if ergebnis["grund"]["wert"] and luminanz(ergebnis["grund"]["wert"]) < 0.2:
        warnungen.append("Dunkler Hintergrund erkannt – die Vorlage ist hell gestaltet (Karten weiß); Ergebnis prüfen.")
    return ergebnis


SYSTEM = "__system__"  # marker: pure system font stack, no own font
SYSTEM_SCHLUESSEL = {"ui-sans-serif", "ui-serif", "ui-monospace", "ui-rounded", "system-ui",
                     "-apple-system", "blinkmacsystemfont"}
# Names that typically appear in system font stacks (OS defaults and emoji fonts).
SYSTEM_STAPEL = SYSTEM_SCHLUESSEL | {
    "segoe ui", "roboto", "helvetica neue", "helvetica", "arial", "noto sans", "oxygen", "oxygen-sans",
    "ubuntu", "cantarell", "fira sans", "droid sans", "liberation sans", "sans-serif",
    "serif", "monospace", "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji",
    "android emoji", "emojisymbols", "emojione color", "twemoji mozilla", "sf pro text", "sf pro display",
}
EMOJI = re.compile(r"emoji|symbol", re.I)


def huellen_aufloesen(wert: str) -> str:
    """Unwrap function wrappers around font lists, keeping their fallback list.

    theme("fontFamily.sans", a, b) -> a, b ; var(--x, a, b) -> a, b ; env(x, a) -> a
    (var() with a known variable is resolved earlier by var_aufloesen).
    """
    for _ in range(10):
        m = re.search(r"\b(?!url\(|format\(|local\()([a-zA-Z_-]+)\(([^()]*)\)", wert)
        if not m:
            break
        args = [a.strip() for a in re.split(r",", m.group(2))]
        # first argument is a key/path (theme("fontFamily.sans"), var(--x), env(x)), not a font
        if args and (args[0][:1] in "\"'" or args[0].startswith("--") or "." in args[0]
                     or m.group(1).lower() in ("var", "env", "theme", "config", "token")):
            args = args[1:]
        wert = wert[:m.start()] + ", ".join(a for a in args if a) + wert[m.end():]
    return wert


def familien_liste(wert: str) -> list:
    namen = []
    for teil in huellen_aufloesen(wert).split(","):
        name = teil.strip().strip("\"'").strip()
        if name:
            namen.append(name)
    return namen


def _erste_familie(wert: str):
    """First real family of a font stack, SYSTEM for a pure system stack, or None."""
    namen = familien_liste(wert)
    if not namen:
        return None
    klein = [n.lower() for n in namen]
    if klein[0] in SYSTEM_SCHLUESSEL:
        return SYSTEM
    benannt = [n for n in klein if n not in GENERISCHE_SCHRIFTEN or n in SYSTEM_SCHLUESSEL]
    if len(benannt) >= 3 and all(n in SYSTEM_STAPEL or EMOJI.search(n) for n in benannt):
        return SYSTEM
    for name, k in zip(namen, klein):
        if k not in GENERISCHE_SCHRIFTEN and not EMOJI.search(k):
            return name
    return SYSTEM if any(k in SYSTEM_SCHLUESSEL for k in klein) else None


def _familie_aus_font(wert: str):
    """font shorthand: family list follows the size (e.g. '600 16px/1.5 "Inter", sans-serif')."""
    m = re.search(r"(?:^|\s)[\d.]+(?:px|rem|em|%|pt|vw|vh)(?:\s*/\s*[\d.]+[a-z%]*)?\s+(.+)$", huellen_aufloesen(wert))
    return _erste_familie(m.group(1)) if m else None


def google_familien(urls) -> dict:
    """Family -> list of weights from fonts.googleapis.com URLs (css and css2 API)."""
    familien = {}
    for url in urls:
        teile = urllib.parse.urlsplit(url)
        if "fonts.googleapis.com" not in teile.netloc:
            continue
        for roh in re.findall(r"family=([^&]+)", teile.query):
            roh = urllib.parse.unquote_plus(roh)
            for eintrag in roh.split("|"):
                name, _, rest = eintrag.partition(":")
                gewichte = sorted(set(re.findall(r"(?<![\d.])([1-9]00)(?!\d)", rest)))
                familien.setdefault(name.strip(), gewichte)
    return familien


def schriften_ermitteln(seite, regeln, font_faces, var, google: dict) -> dict:
    titel, text = [], []
    for regel in regeln:
        sel = regel.selektor
        for prop, wert in regel.deklarationen:
            if prop.startswith("--"):
                if "font" in prop.lower() or "family" in prop.lower():
                    fam = _erste_familie(var_aufloesen(wert, var))
                    if fam and not re.search(r"size|weight|height|spacing", prop, re.I):
                        if TITEL_FONT_VAR.search(prop):
                            titel.append((4, fam, f"CSS-Variable {prop} ({regel.datei})"))
                        elif TEXT_FONT_VAR.search(prop):
                            text.append((4, fam, f"CSS-Variable {prop} ({regel.datei})"))
                continue
            if prop not in ("font-family", "font"):
                continue
            aufgeloest = var_aufloesen(wert, var)
            fam = _erste_familie(aufgeloest) if prop == "font-family" else _familie_aus_font(aufgeloest)
            if not fam:
                continue
            kurz = sel if len(sel) <= 50 else sel[:47] + "..."
            if selektor_hat_element(sel, "h1") or selektor_hat_element(sel, "h2"):
                titel.append((5, fam, f"{kurz} ({regel.datei})"))
            if selektor_hat_element(sel, "body") or selektor_hat_element(sel, "html") or re.search(r":root", sel):
                text.append((5, fam, f"{kurz} ({regel.datei})"))
            elif selektor_hat_element(sel, "p"):
                text.append((2, fam, f"{kurz} ({regel.datei})"))

    def waehle(liste):
        if not liste:
            return None
        zaehler = {}
        for gewicht, fam, fund in liste:
            e = zaehler.setdefault(fam, [0, fund])
            e[0] += gewicht * (0.5 if fam == SYSTEM else 1)  # a real font beats a system stack
        fam, (_, fund) = max(zaehler.items(), key=lambda kv: kv[1][0])
        return fam, fund

    selbst = {}
    for ff, quelle in font_faces:
        d = dict(ff)
        fam = (d.get("font-family") or "").strip().strip("\"'")
        urls = re.findall(r"url\(\s*[\"']?([^\"')]+)", d.get("src", ""))
        if fam and urls:
            selbst.setdefault(fam.lower(), []).extend(urllib.parse.urljoin(quelle, u) for u in urls)

    def herkunft(fam):
        if fam is None:
            return None
        if fam == SYSTEM:
            return {"art": "Systemschrift (keine eigene Schrift)"}
        for g in google:
            if g.lower() == fam.lower():
                return {"art": "Google Fonts (Link)", "gewichte": google[g]}
        if fam.lower() in selbst:
            urls = selbst[fam.lower()]
            art = "@font-face (Google-Server)" if any("gstatic.com" in u for u in urls) else "@font-face (selbst gehostet)"
            return {"art": art, "dateien": list(dict.fromkeys(urls))[:6]}
        if any("use.typekit.net" in (l.get("href") or "") for l in seite.links):
            return {"art": "evtl. Adobe Fonts (lizenzpflichtig)"}
        if fam.lower() in SYSTEM_SCHRIFTEN:
            return {"art": "System"}
        return {"art": "unbekannt"}

    t, b = waehle(titel), waehle(text)
    if b is None and google:
        b = (next(iter(google)), "Google-Fonts-Link")
    if t is None and b is not None:
        t = (b[0], "keine eigene Überschriften-Schrift – wie Fließtext")
    ergebnis = {}
    for schluessel, wahl in (("titel", t), ("text", b)):
        if wahl is None:
            ergebnis[schluessel] = {"familie": None, "fundstelle": "nicht gefunden", "herkunft": None}
        elif wahl[0] == SYSTEM:
            ergebnis[schluessel] = {"familie": None, "systemschrift": True, "vorschlag": "Inter",
                                    "fundstelle": wahl[1], "herkunft": herkunft(SYSTEM)}
        else:
            ergebnis[schluessel] = {"familie": wahl[0], "fundstelle": wahl[1], "herkunft": herkunft(wahl[0])}
    return ergebnis


def _typ_von(url: str) -> str:
    if url.startswith("data:"):
        m = re.match(r"data:image/([\w+.-]+)", url)
        typ = m.group(1) if m else "unbekannt"
    else:
        endung = urllib.parse.urlsplit(url).path.rsplit(".", 1)
        typ = endung[1].lower() if len(endung) == 2 else "unbekannt"
    return {"svg+xml": "svg", "jpeg": "jpg", "x-icon": "ico", "vnd.microsoft.icon": "ico"}.get(typ, typ)


def _bild_src(attrs: dict) -> str:
    kandidaten = [attrs.get(k, "") for k in ("data-src", "data-lazy-src", "data-original", "src")]
    for k in kandidaten:
        if k and not k.startswith("data:"):
            return k
    srcset = attrs.get("data-srcset") or attrs.get("srcset") or ""
    if srcset:
        # largest width descriptor
        teile = [t.strip().split() for t in srcset.split(",") if t.strip()]
        teile.sort(key=lambda t: int(re.sub(r"\D", "", t[1]) or 0) if len(t) > 1 else 0)
        return teile[-1][0]
    src = attrs.get("src", "")
    return src if len(src) > 200 else ""  # tiny data: URIs are lazy-load placeholders


def logo_kandidaten_ermitteln(seite, regeln, basis_url, css_dateien) -> list:
    kand = []

    def neu(url, typ, punkte, herkunft):
        if not url:
            return
        if not url.startswith("data:") and not url.startswith("svg-inline:"):
            url = urllib.parse.urljoin(basis_url, url)
        if typ == "svg":
            punkte += 20
        elif typ == "ico":
            punkte -= 5
        kand.append({"url": url, "typ": typ, "punkte": punkte, "herkunft": herkunft})

    for b in seite.bilder:
        a = b["attrs"]
        src = _bild_src(a)
        if not src:
            continue
        merkmal = " ".join([src, a.get("alt", ""), a.get("class", ""), a.get("id", "")])
        typ = _typ_von(src)
        if LOGO_HINWEIS.search(merkmal) or b["im_logo"]:
            punkte = 100 + (10 if b["im_kopf"] else 0) + (15 if b["home_link"] else 0)
            beschreibung = a.get("class") or a.get("alt") or src.rsplit("/", 1)[-1]
            neu(src, typ, punkte, f"<img> mit Logo-Hinweis ({beschreibung[:40]})")
        elif b["im_kopf"]:
            neu(src, typ, 60 + (15 if b["home_link"] else 0), "erstes Bild im Seitenkopf")

    for i, s in enumerate(seite.svgs):
        if (LOGO_HINWEIS.search(s["kennung"]) or s["im_logo"] or (s["home_link"] and s["im_kopf"])) and len(s["markup"]) < 200_000:
            neu(f"svg-inline:{i}", "svg", 95 + (10 if s["im_kopf"] else 0), "eingebettetes <svg> im Logo-Bereich")

    for regel in regeln:
        if LOGO_HINWEIS.search(regel.selektor):
            for prop, wert in regel.deklarationen:
                if prop in ("background", "background-image"):
                    m = re.search(r"url\(\s*[\"']?([^\"')]+)", wert)
                    if m:
                        quelle = next((u for u, _ in css_dateien if u.endswith(regel.datei)), basis_url)
                        url = urllib.parse.urljoin(quelle, m.group(1))
                        neu(url, _typ_von(url), 70, f"CSS-Hintergrund von {regel.selektor[:40]}")

    for l in seite.links:
        rel = l.get("rel", "").lower()
        if "icon" not in rel or not l.get("href"):
            continue
        href = l["href"]
        typ = _typ_von(href) if not l.get("type") else _typ_von("x." + l["type"].split("/")[-1].replace("svg+xml", "svg"))
        groesse = max([int(x) for x in re.findall(r"(\d+)x\d+", l.get("sizes", ""))] or [0])
        if "mask-icon" in rel:
            punkte = 20
        elif typ == "svg" or groesse >= 180:
            punkte = 30
        elif groesse >= 96:
            punkte = 25
        else:
            punkte = 10
        neu(href, typ, punkte, f"<link rel=\"{rel}\"{' sizes=' + l['sizes'] if l.get('sizes') else ''}>")

    for m in seite.metas:
        if m.get("property", m.get("name", "")).lower() in ("og:image", "twitter:image") and m.get("content"):
            neu(m["content"], _typ_von(m["content"]), 5, m.get("property") or m.get("name"))

    eindeutig = {}
    for k in sorted(kand, key=lambda k: -k["punkte"]):
        eindeutig.setdefault(k["url"], k)
    return list(eindeutig.values())[:8]


IMPRESSUM = re.compile(r"impressum|imprint|legal[\s_-]?notice|anbieterkennzeichnung", re.I)
DATENSCHUTZ = re.compile(r"datenschutz|privacy|data[\s_-]?protection|dsgvo", re.I)


def rechtliche_links(seite, basis_url):
    host = re.sub(r"^www\.", "", urllib.parse.urlsplit(basis_url).netloc.lower())

    def suche(muster):
        beste, beste_punkte = None, 0
        for a in seite.anker:
            href = a["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            punkte = 0
            if muster.search(a["text"]):
                punkte += 3
            if muster.search(href):
                punkte += 2
            if not punkte:
                continue
            url = urllib.parse.urljoin(basis_url, href)
            ziel = re.sub(r"^www\.", "", urllib.parse.urlsplit(url).netloc.lower())
            if ziel == host or ziel.endswith("." + host):
                punkte += 2
            else:
                punkte -= 3  # e.g. Google privacy policy
            if punkte > beste_punkte:
                beste, beste_punkte = url, punkte
        return beste

    return suche(IMPRESSUM), suche(DATENSCHUTZ)


def name_ermitteln(seite, basis_url) -> str | None:
    for m in seite.metas:
        if m.get("property", "").lower() == "og:site_name" and m.get("content", "").strip():
            return m["content"].strip()
    for m in seite.metas:
        if m.get("name", "").lower() == "application-name" and m.get("content", "").strip():
            return m["content"].strip()
    titel = re.sub(r"\s+", " ", seite.titel).strip()
    if not titel:
        return None
    teile = [t.strip() for t in re.split(r"\s+[|–—·:-]\s+", titel) if t.strip()]
    teile = [t for t in teile if t.lower() not in ("startseite", "home", "willkommen", "homepage", "start")] or teile
    domain = re.sub(r"^www\.", "", urllib.parse.urlsplit(basis_url).netloc.lower()).split(".")[0]
    domain_kern = re.sub(r"[^a-z0-9]", "", domain)
    for t in teile:
        kern = re.sub(r"[^a-z0-9]", "", t.lower())
        if kern and (kern in domain_kern or domain_kern[:6] in kern):
            return t
    return teile[-1] if len(teile) > 1 else teile[0]


# ---------------------------------------------------------------------------
# Command: lesen
# ---------------------------------------------------------------------------

MAGIC = [
    (b"\x89PNG", "png"), (b"\xff\xd8", "jpg"), (b"GIF8", "gif"), (b"\x00\x00\x01\x00", "ico"),
]


def bildtyp(daten: bytes) -> str | None:
    kopf = daten[:512].lstrip()
    for magie, typ in MAGIC:
        if daten.startswith(magie):
            return typ
    if daten[:4] == b"RIFF" and daten[8:12] == b"WEBP":
        return "webp"
    if daten[4:12] in (b"ftypavif", b"ftypavis"):
        return "avif"
    if re.search(rb"<svg[\s>]", daten[:4000], re.I) or kopf.startswith(b"<?xml") and b"<svg" in daten[:20000]:
        return "svg"
    return None


def logo_laden(kandidaten: list, svgs: list, aus: Path, robots: Robots | None, ausgabe=print):
    """Try candidates in order, save the first valid image as <aus>/logo.<ext>."""
    for k in kandidaten:
        url = k["url"]
        try:
            if url.startswith("svg-inline:"):
                markup = svgs[int(url.split(":", 1)[1])]["markup"]
                if "xmlns=" not in markup[:300]:
                    markup = markup.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
                daten = markup.encode("utf-8")
            elif url.startswith("data:"):
                kopf, _, nutz = url.partition(",")
                daten = base64.b64decode(nutz) if ";base64" in kopf else urllib.parse.unquote(nutz).encode("utf-8")
            else:
                if robots and not robots.erlaubt(url):
                    ausgabe(f"  übersprungen (robots.txt): {url}")
                    continue
                daten = http_get(url, accept="image/svg+xml,image/*;q=0.9,*/*;q=0.5").daten
                time.sleep(PAUSE)
        except (HolFehler, ValueError, IndexError) as e:
            ausgabe(f"  Logo-Kandidat nicht ladbar: {e}")
            continue
        typ = bildtyp(daten)
        if not typ:
            ausgabe(f"  Logo-Kandidat ist kein Bild: {url[:80]}")
            continue
        aus.mkdir(parents=True, exist_ok=True)
        ziel = aus / f"logo.{typ}"
        ziel.write_bytes(daten)
        return ziel, k
    return None, None


def css_laden(seite: SeitenParser, basis_url: str, robots: Robots, ausgabe=print) -> list:
    """Fetch linked stylesheets (+ @import), at most MAX_CSS, own host first."""
    host = urllib.parse.urlsplit(basis_url).netloc.lower()
    urls = []
    for l in seite.links:
        rel = l.get("rel", "").lower().split()
        if "stylesheet" in rel or ("preload" in rel and l.get("as") == "style"):
            href = l.get("href")
            if href:
                urls.append(urllib.parse.urljoin(basis_url, href))
    for inline in seite.styles:
        _, _, importe = css_regeln(inline, "inline")
        urls += [urllib.parse.urljoin(basis_url, u) for u in importe]
    # Google Fonts CSS is only evaluated via its URL; never needed for colours.
    urls = [u for u in dict.fromkeys(urls) if "fonts.googleapis.com" not in u and u.startswith("http")]
    urls.sort(key=lambda u: urllib.parse.urlsplit(u).netloc.lower() != host)

    geladen, warteschlange, gesehen = [], list(urls), set()
    while warteschlange and len(geladen) < MAX_CSS:
        url = warteschlange.pop(0)
        if url in gesehen:
            continue
        gesehen.add(url)
        if not robots.erlaubt(url):
            ausgabe(f"  übersprungen (robots.txt): {url}")
            continue
        try:
            antwort = http_get(url, accept="text/css,*/*;q=0.1")
        except HolFehler as e:
            ausgabe(f"  CSS nicht geladen: {e}")
            continue
        text = text_aus(antwort)
        geladen.append((url, text))
        _, _, importe = css_regeln(text, url)
        warteschlange += [urllib.parse.urljoin(url, u) for u in importe if "fonts.googleapis.com" not in u]
        time.sleep(PAUSE)
    return geladen


def url_normalisieren(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    teile = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(teile._replace(path=teile.path or "/"))


def lesen(url: str, aus: Path, ausgabe=print) -> dict:
    url = url_normalisieren(url)
    robots = Robots(url)
    if not robots.erlaubt(url):
        raise HolFehler(f"robots.txt der Website verbietet das Abrufen von {url}")
    antwort = http_get(url)
    basis = antwort.url or url
    if urllib.parse.urlsplit(basis).netloc.lower() != robots.host:
        robots = Robots(basis)
    html = text_aus(antwort)
    seite = SeitenParser(html)
    seite.feed(html)
    seite.close()
    css = css_laden(seite, basis, robots, ausgabe)
    daten = analysiere(html, basis, css)

    datei, kandidat = logo_laden(daten["logo"]["kandidaten"], seite.svgs, aus, robots, ausgabe)
    if datei:
        daten["logo"]["datei"] = str(datei.resolve())
        daten["logo"]["typ"] = datei.suffix[1:]
        daten["logo"]["herkunft"] = kandidat["herkunft"]
        if datei.suffix == ".ico":
            daten["warnungen"].append("Als Logo nur ein Favicon (.ico) gefunden – besser eine SVG/PNG-Datei vom Nutzer erfragen.")
        elif kandidat["punkte"] < 50:
            daten["warnungen"].append(f"Logo ist nur ein Ersatz ({kandidat['herkunft']}) – bitte prüfen.")
    else:
        daten["warnungen"].append("Kein Logo gefunden – bitte beim Nutzer als SVG oder PNG erfragen.")
    for k in daten["logo"]["kandidaten"]:
        if k["url"].startswith("data:"):
            k["url"] = k["url"][:60] + "…"
    gepruft = {}
    for s in ("titel", "text"):
        e = daten["schriften"][s]
        h = e.get("herkunft") or {}
        if h.get("art") == "unbekannt" and e.get("familie"):
            # origin not visible in the loaded CSS: ask the Google Fonts API whether it is a free font
            fam = e["familie"]
            if fam not in gepruft:
                try:
                    gepruft[fam] = google_css_holen(fam, [400])[0] is not None
                except HolFehler:
                    gepruft[fam] = False
            if gepruft[fam]:
                h["art"] = "frei bei Google Fonts verfügbar (Einbindung auf der Website unklar)"
        if h.get("art", "").startswith(("evtl. Adobe", "unbekannt")):
            daten["warnungen"].append(f"Schrift „{daten['schriften'][s]['familie']}“: Herkunft unklar – evtl. lizenzpflichtig.")

    aus.mkdir(parents=True, exist_ok=True)
    (aus / "branding.json").write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return daten


def zusammenfassung(daten: dict, aus: Path) -> str:
    f, s = daten["farben"], daten["schriften"]
    host = urllib.parse.urlsplit(daten["quelle_url"]).netloc

    def farbe(schluessel):
        e = f.get(schluessel) or {}
        return f"{e.get('wert') or '–'}  ({e.get('fundstelle', '')})"

    def schrift(schluessel):
        e = s[schluessel]
        if e.get("systemschrift"):
            return f"Systemschrift (keine eigene Schrift) – Vorschlag: {e['vorschlag']} (frei, Google Fonts)"
        if not e["familie"]:
            return "– (nicht erkannt)"
        return f"{e['familie']}  ({(e.get('herkunft') or {}).get('art', '?')})"

    zeilen = [f"Branding von {host}:", f"  Name:            {daten.get('name') or '–'}",
              f"  Akzentfarbe:     {farbe('akzent')}"]
    if f.get("akzent_dunkel"):
        zeilen.append(f"  Akzent dunkel:   {f['akzent_dunkel']['wert']}")
    zeilen += [f"  Textfarbe:       {farbe('text')}", f"  Hintergrund:     {farbe('grund')}"]
    k = f.get("kontrast_weiss_auf_akzent")
    if k:
        bewertung = "gut lesbar" if k["ok"] else f"zu schwach, lesbare Variante {k.get('lesbare_variante')}"
        zeilen.append(f"  Kontrast weiß auf Akzent: {str(k['verhaeltnis']).replace('.', ',')}:1 – {bewertung}")
    weitere = [c["wert"] for c in f["akzent"].get("kandidaten", [])[1:4]]
    if weitere:
        zeilen.append(f"  Weitere Farbkandidaten: {', '.join(weitere)}")
    zeilen += [f"  Überschriften:   {schrift('titel')}", f"  Fließtext:       {schrift('text')}",
               f"  Logo:            {daten['logo'].get('datei') or '– (nicht gefunden)'}"]
    zeilen += [f"  Impressum:       {daten.get('impressum_url') or '–'}",
               f"  Datenschutz:     {daten.get('datenschutz_url') or '–'}"]
    if daten["warnungen"]:
        zeilen.append("Hinweise:")
        zeilen += [f"  ! {w}" for w in daten["warnungen"]]
    zeilen.append(f"Gespeichert: {aus / 'branding.json'}")
    zeilen.append("Bitte dem Nutzer zeigen: „Passen Farbe, Schriften und Logo so?“")
    return "\n".join(zeilen)


# ---------------------------------------------------------------------------
# Command: schriften
# ---------------------------------------------------------------------------

def aehnliche_schriften(familie: str) -> list:
    name = re.sub(r"\s+", " ", familie.lower().replace("-", " ")).strip()
    for schluessel, vorschlaege in AEHNLICHE_SCHRIFTEN:
        if schluessel in name:
            return vorschlaege
    if "mono" in name or "code" in name:
        return ["JetBrains Mono", "IBM Plex Mono"]
    if "slab" in name:
        return ["Roboto Slab", "Zilla Slab"]
    if re.search(r"script|hand|brush", name):
        return ["Caveat", "Dancing Script"]
    if SERIF_HINWEISE.search(name) and "sans" not in name:
        return ["Source Serif 4", "Lora"]
    return ["Inter", "Open Sans"]


def google_css_url(familie: str, gewichte: list | None) -> str:
    fam = urllib.parse.quote(familie.strip(), safe="").replace("%20", "+")
    if gewichte:
        fam += ":wght@" + ";".join(str(g) for g in sorted(gewichte))
    return f"{GOOGLE_CSS2}?family={fam}&display=swap"


def google_css_holen(familie: str, gewichte: list):
    """Return (css_text, available_weights) or (None, []) if the family is not on Google Fonts."""
    def versuch(fam, gw):
        try:
            return text_aus(http_get(google_css_url(fam, gw), accept="text/css,*/*;q=0.1"))
        except HolFehler as e:
            if e.code in (400, 404):
                return None
            raise

    namen = [familie]
    titel = " ".join(w[:1].upper() + w[1:] for w in familie.split())
    if titel != familie:
        namen.append(titel)
    for fam in namen:
        css = versuch(fam, gewichte)
        if css:
            return css, gewichte
        if len(gewichte) > 1:
            teile, vorhanden = [], []
            for g in gewichte:
                c = versuch(fam, [g])
                if c:
                    teile.append(c)
                    vorhanden.append(g)
            if teile:
                return "\n".join(teile), vorhanden
        css = versuch(fam, None)
        if css:
            return css, []
    return None, []


def google_css_parsen(css: str) -> list:
    """Return faces: dict(familie, stil, gewicht, subset, url, unicode_range)."""
    faces = []
    bloecke = list(re.finditer(r"(?:/\*\s*([\w\[\]-]+)\s*\*/\s*)?@font-face\s*\{([^}]*)\}", css))
    hat_subsets = any(m.group(1) for m in bloecke)
    for m in bloecke:
        subset = m.group(1) or "alle"
        if hat_subsets and subset not in GOOGLE_SUBSETS:
            continue
        d = dict(_deklarationen(m.group(2)))
        url = re.search(r"url\(\s*[\"']?([^\"')]+)", d.get("src", ""))
        if not url:
            continue
        faces.append({
            "familie": d.get("font-family", "").strip().strip("\"'"),
            "stil": d.get("font-style", "normal"),
            "gewicht": d.get("font-weight", "400"),
            "subset": subset,
            "url": url.group(1),
            "unicode_range": d.get("unicode-range"),
        })
    return faces


def font_face_zeile(familie, stil, gewicht, pfad, unicode_range=None) -> str:
    teile = [f'font-family: "{familie}"', f"font-style: {stil}", f"font-weight: {gewicht}",
             "font-display: swap", f'src: url("{pfad}") format("woff2")']
    if unicode_range:
        teile.append(f"unicode-range: {unicode_range}")
    return "@font-face { " + "; ".join(teile) + "; }"


def font_face_regeln(css: str) -> list:
    """All @font-face rules of a CSS text, each normalised to a single line."""
    return [re.sub(r"\s+", " ", m.group(0)).strip() for m in re.finditer(r"@font-face\s*\{[^}]*\}", css)]


def font_familie_von(regel: str) -> str:
    m = re.search(r"font-family:\s*[\"']?([^;\"']+)", regel)
    return m.group(1).strip() if m else ""


def schriften(familie: str, gewichte: list, aus: Path, css_pfad: str = "assets/fonts", ausgabe=print) -> int:
    css, vorhanden = google_css_holen(familie, gewichte)
    if css is None:
        vorschlag = aehnliche_schriften(familie)
        if familie.lower() in SYSTEM_SCHRIFTEN:
            ausgabe(f"„{familie}“ ist eine Systemschrift – keine Dateien nötig; sie wird nicht von Google geladen.")
            ausgabe(f"Wer überall dasselbe Schriftbild will: ähnliche freie Google-Schriften: {vorschlag[0]}, {vorschlag[1]}.")
        else:
            ausgabe(f"„{familie}“ ist keine Google-Schrift (vermutlich lizenzpflichtig oder selbst gehostet).")
            ausgabe("Möglichkeiten:")
            ausgabe("  1. Der Nutzer liefert die Schriftdateien (woff2) samt Lizenz für Web-Einbettung;")
            ausgabe(f"     dann nach {aus}/ legen und @font-face-Regeln in fonts.css ergänzen.")
            ausgabe(f"  2. Ähnliche freie Google-Schrift verwenden: {vorschlag[0]} oder {vorschlag[1]}, z. B.:")
            ausgabe(f"     python3 werkzeuge/branding.py schriften --familie \"{vorschlag[0]}\" "
                    f"--gewichte {','.join(map(str, gewichte))} --aus {aus}")
        return 2

    faces = google_css_parsen(css)
    if not faces:
        ausgabe("Google Fonts hat keine latin/latin-ext-Dateien geliefert.")
        return 1
    fam_name = faces[0]["familie"] or familie
    slug = re.sub(r"[^A-Za-z0-9]", "", fam_name)
    aus.mkdir(parents=True, exist_ok=True)

    nach_url = {}
    for f in faces:
        nach_url.setdefault(f["url"], []).append(f)
    dateiname = {}
    for url, gruppe in nach_url.items():
        if urllib.parse.urlsplit(url).netloc != "fonts.gstatic.com":
            ausgabe(f"Unerwartete Quelle übersprungen: {url}")
            continue
        gw = sorted({g["gewicht"] for g in gruppe}, key=lambda x: int(re.sub(r"\D", "", x) or 0))
        stil = "italic" if gruppe[0]["stil"] == "italic" else ""
        name = f"{slug}-{gw[0]}" + (f"-{gw[-1]}" if len(gw) > 1 else "") + stil + f"-{gruppe[0]['subset']}.woff2"
        daten = http_get(url, accept="font/woff2,*/*;q=0.1").daten
        if not daten.startswith(b"wOF2"):
            ausgabe(f"Keine woff2-Datei erhalten: {url}")
            continue
        (aus / name).write_bytes(daten)
        dateiname[url] = name
        ausgabe(f"  gespeichert: {aus / name} ({len(daten) // 1024} KB)")

    neue = [font_face_zeile(fam_name, f["stil"], f["gewicht"], f"{css_pfad.rstrip('/')}/{dateiname[f['url']]}", f["unicode_range"])
            for f in faces if f["url"] in dateiname]
    if not neue:
        return 1

    ziel = aus / "fonts.css"
    alt = font_face_regeln(ziel.read_text(encoding="utf-8")) if ziel.exists() else []
    behalten = [r for r in alt if font_familie_von(r).lower() != fam_name.lower()]
    kopf = ("/* Lokale Schriften, erzeugt von werkzeuge/branding.py aus Google Fonts "
            "(freie Lizenzen: SIL Open Font License / Apache 2.0). Nur latin + latin-ext. */")
    ziel.write_text(kopf + "\n" + "\n".join(behalten + neue) + "\n", encoding="utf-8")

    fehlend = [g for g in gewichte if g not in vorhanden]
    if vorhanden and fehlend:
        ausgabe(f"Hinweis: Gewichte {', '.join(map(str, fehlend))} gibt es bei „{fam_name}“ nicht.")
    elif not vorhanden:
        ausgabe(f"Hinweis: „{fam_name}“ hat die gewünschten Gewichte nicht – Standardschnitt geladen.")
    ausgabe(f"„{fam_name}“ lokal gespeichert, {len(neue)} @font-face-Regeln in {ziel}.")
    return 0


# ---------------------------------------------------------------------------
# Command: anwenden
# ---------------------------------------------------------------------------

def schrift_stapel(familie: str, rolle: str) -> str:
    if SERIF_HINWEISE.search(familie) and "sans" not in familie.lower():
        rest = ['Georgia', '"Times New Roman"', "serif"]
    elif rolle == "titel":
        rest = ["Helvetica", "Arial", "sans-serif"]
    else:
        rest = ["system-ui", "-apple-system", '"Segoe UI"', "sans-serif"]
    rest = [r for r in rest if r.strip('"').lower() != familie.lower()]
    return ", ".join([f'"{familie}"'] + rest)


class VorlagenFehler(Exception):
    pass


def _ersetze_einmal(text: str, muster: str, ersatz, beschreibung: str, pflicht: bool = True, flags=0):
    neu, anzahl = re.subn(muster, ersatz, text, count=1, flags=flags)
    if anzahl == 0 and pflicht:
        raise VorlagenFehler(f"Stelle nicht gefunden: {beschreibung}")
    return neu, anzahl


def _im_block(text, block_muster, feld_muster, ersatz, beschreibung, pflicht=True):
    """Replace inside the first block matched by block_muster (group 1 = block body)."""
    m = re.search(block_muster, text, re.S)
    if not m:
        if pflicht:
            raise VorlagenFehler(f"Block nicht gefunden: {beschreibung}")
        return text, 0
    inhalt, anzahl = re.subn(feld_muster, ersatz, m.group(1), count=1)
    if anzahl == 0 and pflicht:
        raise VorlagenFehler(f"Stelle nicht gefunden: {beschreibung}")
    return text[:m.start(1)] + inhalt + text[m.end(1):], anzahl


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def anwenden(vorlage: Path, branding: dict, titel_schrift: str | None = None, text_schrift: str | None = None,
             fonts_css: Path | None = None, ausgabe=print) -> list:
    """Apply branding to the template in place. Returns list of change descriptions."""
    html = vorlage.read_text(encoding="utf-8")
    original = html
    aenderungen = []
    f = branding.get("farben", {})

    # 1. SEITE.design colours
    seite_design = r"const SEITE\s*=\s*\{\s*design:\s*\{(.*?)\}"
    for feld in ("akzent", "akzent_dunkel", "text", "grund"):
        wert = (f.get(feld) or {}).get("wert")
        if not wert:
            continue
        if not HEX.match(wert):
            raise VorlagenFehler(f"Ungültige Farbe für {feld}: {wert}")
        html, _ = _im_block(html, seite_design, rf'(\b{feld}:\s*)"[^"]*"', rf'\g<1>"{wert.upper()}"', f"SEITE.design.{feld}")
        aenderungen.append(f"SEITE.design.{feld} = {wert.upper()}")
        # keep the offer block (own variables) in sync if present
        ang = {"akzent": "--ang-akzent", "akzent_dunkel": "--ang-akzent-dunkel", "text": "--ang-text"}.get(feld)
        if ang:
            html, n = _ersetze_einmal(html, rf"({ang}:\s*)#[0-9A-Fa-f]{{3,8}}(;)", rf"\g<1>{wert.upper()}\g<2>", ang, pflicht=False)
            if n:
                aenderungen.append(f"{ang} = {wert.upper()}")

    # 2. ABSENDER.logo (+ favicon pointing to the same file)
    logo = (branding.get("logo") or {}).get("datei")
    if logo:
        quelle = Path(logo)
        if not quelle.exists():
            quelle = Path(branding.get("_basis", ".")) / quelle.name
        if quelle.exists():
            assets = vorlage.parent / "assets"
            assets.mkdir(exist_ok=True)
            ziel = assets / f"logo{quelle.suffix.lower()}"
            if ziel.exists() and ziel.resolve() != quelle.resolve() and ziel.read_bytes() != quelle.read_bytes():
                shutil.copy2(ziel, ziel.with_name(ziel.name + ".bak"))
            if ziel.resolve() != quelle.resolve():
                shutil.copy2(quelle, ziel)
            neu_pfad = f"assets/{ziel.name}"
            m = re.search(r'const ABSENDER\s*=\s*\{[^}]*?\blogo:\s*"([^"]*)"', html, re.S)
            alt_pfad = m.group(1) if m else None
            html, _ = _im_block(html, r"const ABSENDER\s*=\s*\{(.*?)\};", r'(\blogo:\s*)"[^"]*"', rf'\g<1>"{neu_pfad}"', "ABSENDER.logo")
            aenderungen.append(f"ABSENDER.logo = {neu_pfad}")
            if alt_pfad and alt_pfad != neu_pfad:
                html, n = _ersetze_einmal(html, rf'(<link rel="icon" href=")({re.escape(alt_pfad)})(")', rf"\g<1>{neu_pfad}\g<3>",
                                          "favicon", pflicht=False)
                if n:
                    aenderungen.append(f'<link rel="icon"> = {neu_pfad}')
        else:
            ausgabe(f"Hinweis: Logodatei {logo} nicht gefunden – ABSENDER.logo bleibt.")

    # 3. @font-face rules from fonts.css
    fonts_css = fonts_css or (vorlage.parent / "assets" / "fonts" / "fonts.css")
    lokale_familien = set()
    if fonts_css.exists():
        regeln = font_face_regeln(fonts_css.read_text(encoding="utf-8"))
        if regeln:
            for r in regeln:
                lokale_familien.add(font_familie_von(r).lower())
                pfad = re.search(r'url\(\s*["\']?([^"\')]+)', r)
                if pfad and not (vorlage.parent / pfad.group(1)).exists():
                    ausgabe(f"Warnung: Schriftdatei fehlt neben der Vorlage: {pfad.group(1)}")
            m = re.search(r"(<style>[ \t]*\n)((?:[ \t]*@font-face\s*\{[^}]*\}[ \t]*\n)+)", html)
            if not m:
                raise VorlagenFehler("@font-face-Regeln oben im <style> nicht gefunden")
            einzug = re.match(r"[ \t]*", m.group(2)).group(0)
            block = "".join(f"{einzug}{r}\n" for r in regeln)
            html = html[:m.start(2)] + block + html[m.end(2):]
            aenderungen.append(f"@font-face: {len(regeln)} Regeln aus {fonts_css}")
    else:
        ausgabe(f"Hinweis: {fonts_css} nicht gefunden – @font-face-Regeln bleiben unverändert.")

    # 4. font variables in :root (and offer block)
    s = branding.get("schriften", {})
    def erkannt(e):
        # system stack: use the suggested free font only once it is available locally
        e = e or {}
        if e.get("familie"):
            return e["familie"]
        if e.get("systemschrift") and (e.get("vorschlag") or "").lower() in lokale_familien:
            return e["vorschlag"]
        return None

    wahl = {"titel": titel_schrift or erkannt(s.get("titel")),
            "text": text_schrift or erkannt(s.get("text"))}
    for rolle, familie in wahl.items():
        if not familie:
            continue
        familie = familie.strip().strip("\"'")
        if lokale_familien and familie.lower() not in lokale_familien and familie.lower() not in SYSTEM_SCHRIFTEN:
            ausgabe(f"Warnung: „{familie}“ ist nicht lokal eingebunden – Browser nutzt Ersatzschrift. "
                    f"Erst `schriften --familie \"{familie}\"` ausführen.")
        stapel = schrift_stapel(familie, rolle)
        html, _ = _im_block(html, r":root\s*\{(.*?)\}", rf"(--schrift-{rolle}:\s*)[^;]+(;)", lambda m: m.group(1) + stapel + m.group(2),
                            f"--schrift-{rolle} in :root")
        aenderungen.append(f"--schrift-{rolle}: {stapel}")
        ang = "--ang-titel" if rolle == "titel" else "--ang-schrift"
        html, n = _ersetze_einmal(html, rf"({ang}:\s*)[^;]+(;)", lambda m: m.group(1) + stapel + m.group(2), ang, pflicht=False)
        if n:
            aenderungen.append(f"{ang}: {stapel}")

    if html != original:
        shutil.copy2(vorlage, vorlage.with_name(vorlage.name + ".bak"))
        vorlage.write_text(html, encoding="utf-8")
    return aenderungen


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Branding einer Website auslesen und auf die Videoseiten-Vorlage anwenden.")
    sub = p.add_subparsers(dest="befehl", required=True)

    p_l = sub.add_parser("lesen", help="Farben, Schriften, Logo und Rechtslinks von der Website des Nutzers lesen")
    p_l.add_argument("--url", required=True, help="Website des Nutzers, z. B. beispiel.de")
    p_l.add_argument("--aus", type=Path, default=STANDARD_AUS, help=f"Zielordner (Standard: {STANDARD_AUS})")

    p_s = sub.add_parser("schriften", help="Google-Schrift lokal als woff2 speichern und fonts.css schreiben")
    p_s.add_argument("--familie", required=True, help='Schriftname, z. B. "Open Sans"')
    p_s.add_argument("--gewichte", default="400,600,700", help="z. B. 400,600,700")
    p_s.add_argument("--aus", type=Path, required=True, help="Zielordner, z. B. <vorlage>/assets/fonts")
    p_s.add_argument("--css-pfad", default="assets/fonts", help="Pfad der Dateien aus Sicht von index.html")

    p_a = sub.add_parser("anwenden", help="Branding in die Vorlage schreiben (mit Sicherungskopie)")
    p_a.add_argument("--vorlage", type=Path, required=True, help="index.html der Vorlage (Kopie)")
    p_a.add_argument("--branding", type=Path, required=True, help="branding.json aus „lesen“")
    p_a.add_argument("--titel-schrift", help="Überschriften-Schrift (statt der erkannten)")
    p_a.add_argument("--text-schrift", help="Fließtext-Schrift (statt der erkannten)")
    p_a.add_argument("--fonts-css", type=Path, help="fonts.css (Standard: <vorlage>/assets/fonts/fonts.css)")

    a = p.parse_args(argv)
    try:
        if a.befehl == "lesen":
            print(f"Lese {url_normalisieren(a.url)} …")
            daten = lesen(a.url, a.aus)
            print(zusammenfassung(daten, a.aus))
            return 0
        if a.befehl == "schriften":
            try:
                gewichte = sorted({int(g) for g in a.gewichte.split(",") if g.strip()})
            except ValueError:
                print("--gewichte: nur Zahlen wie 400,600,700", file=sys.stderr)
                return 1
            return schriften(a.familie, gewichte, a.aus, a.css_pfad)
        if a.befehl == "anwenden":
            branding = json.loads(a.branding.read_text(encoding="utf-8"))
            branding["_basis"] = str(a.branding.parent)
            aenderungen = anwenden(a.vorlage, branding, a.titel_schrift, a.text_schrift, a.fonts_css)
            if aenderungen:
                print(f"Vorlage angepasst ({a.vorlage}, Sicherung: {a.vorlage.name}.bak):")
                print("\n".join(f"  - {x}" for x in aenderungen))
            else:
                print("Nichts zu ändern.")
            return 0
    except HolFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1
    except VorlagenFehler as e:
        print(f"Vorlage passt nicht: {e}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())

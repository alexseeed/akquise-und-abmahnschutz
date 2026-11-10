"""Offline tests for werkzeuge/branding.py (no network: http_get is mocked).

    python3 -m unittest discover -s pfade/videoseiten/tests -p "test_branding.py" -v
"""
import difflib
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "werkzeuge"))
import branding  # noqa: E402

VORLAGE = HIER.parent / "vorlage"
BASIS = "https://www.feldmark.de/"

HTML = """<!doctype html><html lang="de"><head>
<meta charset="utf-8">
<title>Startseite | Feldmark Kreativagentur</title>
<meta property="og:site_name" content="Feldmark Kreativagentur">
<meta property="og:image" content="/media/og.jpg">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Open+Sans:wght@400;600&display=swap">
<link rel="icon" href="/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
<style>.hero { background: #F4F4F4; }</style>
</head><body>
<header class="site-header">
  <a href="/" class="custom-logo-link"><img src="/media/feldmark-logo.svg" alt="Feldmark" class="custom-logo" width="160"></a>
  <nav><a href="/leistungen/">Leistungen</a><button aria-label="Menü"><svg viewBox="0 0 10 10"><path d="M0 0h10"/></svg></button></nav>
</header>
<main>
  <a class="btn btn-primary" href="/kontakt/">Kontakt</a>
  <img src="/media/team.jpg" alt="Team">
</main>
<footer>
  <a href="/impressum/">Impressum</a>
  <a href="/datenschutzerklaerung/">Datenschutz</a>
  <a href="https://policies.google.com/privacy">Datenschutz von Google</a>
</footer>
</body></html>
"""

CSS = """/* Theme */
@charset "UTF-8";
:root { --primary-color: #E30613; --text-color: #222222; --bs-primary: #0d6efd;
        --wp--preset--color--vivid-cyan-blue: #0693e3; }
body { color: var(--text-color); background-color: #FFFFFF; font-family: "Open Sans", sans-serif; }
h1, h2 { font-family: 'Montserrat', Helvetica, sans-serif; }
a { color: var(--primary-color); }
.btn-primary { background-color: #E30613; color: #fff; }
.btn-primary:hover { background-color: #C80511; }
@media (max-width: 600px) { .teaser { border-color: #1E88E5; } }
@keyframes puls { from { color: #00AA00; } to { color: #00BB00; } }
.has-vivid-red-color { color: #cf2e2e; }
#cookie-banner .accept { background: #00FF00; }
"""

LOGO_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 40"><rect width="160" height="40" fill="#E30613"/></svg>'


def antwort(url, daten, typ="text/html; charset=utf-8"):
    return branding.Antwort(url, 200, typ, daten if isinstance(daten, bytes) else daten.encode("utf-8"))


def falsches_netz(seiten: dict):
    """Fake http_get serving a dict url -> (bytes|str, content_type); everything else is 404."""
    aufrufe = []

    def holen(url, timeout=None, max_bytes=None, accept=None):
        aufrufe.append(url)
        if url in seiten:
            daten, typ = seiten[url]
            return antwort(url, daten, typ)
        raise branding.HolFehler(f"HTTP 404: {url}", 404)

    holen.aufrufe = aufrufe
    return holen


class Farben(unittest.TestCase):
    def test_parsen(self):
        self.assertEqual(branding.farbe_parsen("#abc")[:3], (0xAA, 0xBB, 0xCC))
        self.assertEqual(branding.farbe_parsen("rgb(0 122 255 / 50%)"), (0, 122, 255, 0.5))
        self.assertEqual(branding.farbe_parsen("rgba(227, 6, 19, .9)")[:3], (227, 6, 19))
        self.assertEqual(branding.hex_von(branding.farbe_parsen("hsl(0, 100%, 50%)")), "#FF0000")
        self.assertIsNone(branding.farbe_parsen("#12345"))

    def test_kontrast_wcag(self):
        self.assertEqual(branding.kontrast("#FFFFFF", "#000000"), 21.0)
        self.assertAlmostEqual(branding.kontrast("#FFFFFF", "#767676"), 4.54, places=2)
        self.assertLess(branding.kontrast("#FFFFFF", "#007AFF"), 4.5)

    def test_abdunkeln_und_lesbare_variante(self):
        self.assertEqual(branding.abdunkeln("#E30613"), "#C10510")
        variante = branding.lesbare_variante("#FFD400")
        self.assertGreaterEqual(branding.kontrast("#FFFFFF", variante), 4.5)

    def test_extraktion(self):
        d = branding.analysiere(HTML, BASIS, [(BASIS + "css/style.css", CSS)])
        f = d["farben"]
        self.assertEqual(f["akzent"]["wert"], "#E30613")
        self.assertIn("primary", " ".join(f["akzent"]["kandidaten"][0]["fundstellen"]).lower() + f["akzent"]["fundstelle"].lower() + "btn-primary")
        self.assertEqual(f["akzent_dunkel"]["wert"], "#C10510")
        self.assertEqual(f["text"]["wert"], "#222222")
        self.assertEqual(f["grund"]["wert"], "#FFFFFF")
        werte = [k["wert"] for k in f["akzent"]["kandidaten"]]
        # hover shade merged; cookie banner, keyframes, WP preset and Bootstrap default ignored or demoted
        self.assertNotIn("#C80511", werte)
        self.assertNotIn("#00FF00", werte)
        self.assertNotIn("#00AA00", werte)
        self.assertNotIn("#0693E3", werte)
        k = f["kontrast_weiss_auf_akzent"]
        self.assertTrue(k["ok"])
        self.assertAlmostEqual(k["verhaeltnis"], branding.kontrast("#FFFFFF", "#E30613"))

    def test_theme_color_und_kontrastwarnung(self):
        html = '<html><head><meta name="theme-color" content="#FFD400"></head><body></body></html>'
        d = branding.analysiere(html, BASIS, [])
        self.assertEqual(d["farben"]["akzent"]["wert"], "#FFD400")
        self.assertEqual(d["farben"]["akzent"]["fundstelle"], "meta theme-color")
        k = d["farben"]["kontrast_weiss_auf_akzent"]
        self.assertFalse(k["ok"])
        self.assertTrue(any("4.5:1" in w for w in d["warnungen"]))
        self.assertEqual(d["farben"]["grund"]["wert"], "#FFFFFF")  # browser default

    def test_css_parser_verschachtelt(self):
        regeln, faces, importe = branding.css_regeln(
            '@import url("a.css"); @media screen { @supports (x:y) { .b { color: red; } } }'
            '@font-face { font-family: "X"; src: url(x.woff2); } .c { --v: #fff; }', "t.css")
        self.assertEqual(importe, ["a.css"])
        self.assertEqual([r.selektor for r in regeln], [".b", ".c"])
        self.assertEqual(dict(faces[0])["font-family"], '"X"')


class SchriftenErkennung(unittest.TestCase):
    def test_familien_und_herkunft(self):
        s = branding.analysiere(HTML, BASIS, [(BASIS + "css/style.css", CSS)])["schriften"]
        self.assertEqual(s["titel"]["familie"], "Montserrat")
        self.assertEqual(s["text"]["familie"], "Open Sans")
        self.assertEqual(s["titel"]["herkunft"]["art"], "Google Fonts (Link)")
        self.assertEqual(s["titel"]["herkunft"]["gewichte"], ["600", "700"])

    def test_selbst_gehostet_und_variable(self):
        css = (':root { --font-heading: "Fraunces", serif; } body { font: 400 16px/1.5 "Lato", sans-serif; }'
               '@font-face { font-family: "Lato"; src: url(../fonts/lato.woff2) format("woff2"); }')
        s = branding.analysiere("<html><body></body></html>", BASIS, [(BASIS + "css/a.css", css)])["schriften"]
        self.assertEqual(s["titel"]["familie"], "Fraunces")
        self.assertEqual(s["text"]["familie"], "Lato")
        self.assertEqual(s["text"]["herkunft"]["art"], "@font-face (selbst gehostet)")
        self.assertEqual(s["text"]["herkunft"]["dateien"], [BASIS + "fonts/lato.woff2"])

    def test_tailwind_systemstapel(self):
        # real case (strato.de): unprocessed Tailwind theme() with a pure system stack
        stapel = ('ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",'
                  'Arial,"Noto Sans",sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol","Noto Color Emoji"')
        css = (f'html {{ font-family: theme("fontFamily.sans",{stapel}); }}'
               f'h1, h2 {{ font-family: var(--font-display, {stapel}); }}')
        d = branding.analysiere("<html><body></body></html>", BASIS, [(BASIS + "app.css", css)])
        for rolle in ("titel", "text"):
            e = d["schriften"][rolle]
            self.assertIsNone(e["familie"])
            self.assertTrue(e["systemschrift"])
            self.assertEqual(e["vorschlag"], "Inter")
            self.assertEqual(e["herkunft"]["art"], "Systemschrift (keine eigene Schrift)")
        self.assertFalse(any("lizenzpflichtig" in w for w in d["warnungen"]))
        self.assertIn("Systemschrift (keine eigene Schrift) – Vorschlag: Inter", branding.zusammenfassung(d, Path("x")))

    def test_huellen_und_erste_echte_familie(self):
        self.assertEqual(branding._erste_familie('theme("fontFamily.sans", "Poppins", ui-sans-serif, sans-serif)'), "Poppins")
        self.assertEqual(branding._erste_familie('var(--unbekannt, "Lato", Arial, sans-serif)'), "Lato")
        self.assertEqual(branding._erste_familie('"Inter", system-ui, sans-serif'), "Inter")
        self.assertEqual(branding._erste_familie("Arial, sans-serif"), "Arial")
        self.assertEqual(branding._erste_familie('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto'), branding.SYSTEM)
        self.assertEqual(branding._familie_aus_font('600 16px/1.5 theme("fontFamily.sans", "Rubik", sans-serif)'), "Rubik")
        # a real font beats the Tailwind preflight system stack on html
        css = 'html { font-family: ui-sans-serif, system-ui, sans-serif; } body { font-family: "Rubik", sans-serif; }'
        s = branding.analysiere("<html></html>", BASIS, [(BASIS + "a.css", css)])["schriften"]
        self.assertEqual(s["text"]["familie"], "Rubik")

    def test_aehnlichkeit(self):
        self.assertEqual(branding.aehnliche_schriften("Gotham Rounded"), ["Montserrat", "Outfit"])
        self.assertEqual(len(branding.aehnliche_schriften("Irgendwas Serif Pro")), 2)


class LogoUndLinks(unittest.TestCase):
    def test_logo_kandidaten(self):
        d = branding.analysiere(HTML, BASIS, [])
        k = d["logo"]["kandidaten"]
        self.assertEqual(k[0]["url"], BASIS + "media/feldmark-logo.svg")
        self.assertEqual(k[0]["typ"], "svg")
        urls = [x["url"] for x in k]
        self.assertLess(urls.index(BASIS + "apple-touch-icon.png"), urls.index(BASIS + "favicon-32.png"))
        self.assertEqual(urls[-1], BASIS + "media/og.jpg")  # og:image last resort
        self.assertNotIn(BASIS + "media/team.jpg", urls)
        self.assertFalse(any(u.startswith("svg-inline:") for u in urls))  # menu icon is no logo

    def test_inline_svg_und_lazy_load(self):
        html = ('<html><body><header><a href="/" class="brand"><svg viewBox="0 0 10 10"><g><path d="M0 0h10"/></g></svg></a>'
                '<img class="logo lazyload" src="data:image/gif;base64,R0lGOD" data-src="/img/logo.png"></header></body></html>')
        d = branding.analysiere(html, BASIS, [])
        typen = {k["url"]: k["typ"] for k in d["logo"]["kandidaten"]}
        self.assertEqual(typen.get(BASIS + "img/logo.png"), "png")
        self.assertIn("svg-inline:0", typen)

    def test_impressum_datenschutz_name(self):
        d = branding.analysiere(HTML, BASIS, [])
        self.assertEqual(d["impressum_url"], BASIS + "impressum/")
        self.assertEqual(d["datenschutz_url"], BASIS + "datenschutzerklaerung/")
        self.assertEqual(d["name"], "Feldmark Kreativagentur")
        ohne_og = HTML.replace('<meta property="og:site_name" content="Feldmark Kreativagentur">', "")
        self.assertEqual(branding.analysiere(ohne_og, BASIS, [])["name"], "Feldmark Kreativagentur")
        englisch = '<html><body><a href="/legal/imprint">Imprint</a><a href="/privacy-policy">Privacy</a></body></html>'
        d = branding.analysiere(englisch, BASIS, [])
        self.assertEqual((d["impressum_url"], d["datenschutz_url"]), (BASIS + "legal/imprint", BASIS + "privacy-policy"))


class Lesen(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        patcher = mock.patch.object(branding, "PAUSE", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_lesen_ende_zu_ende(self):
        netz = falsches_netz({
            BASIS: (HTML, "text/html; charset=utf-8"),
            BASIS + "css/style.css": (CSS, "text/css"),
            BASIS + "media/feldmark-logo.svg": (LOGO_SVG, "image/svg+xml"),
        })
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            daten = branding.lesen("www.feldmark.de", self.tmp)
        self.assertTrue(all(u.startswith(BASIS) for u in netz.aufrufe), netz.aufrufe)  # Google Fonts not fetched
        self.assertEqual((self.tmp / "logo.svg").read_bytes(), LOGO_SVG)
        gespeichert = json.loads((self.tmp / "branding.json").read_text(encoding="utf-8"))
        self.assertEqual(gespeichert["farben"]["akzent"]["wert"], "#E30613")
        self.assertEqual(gespeichert["logo"]["typ"], "svg")
        text = branding.zusammenfassung(daten, self.tmp)
        for erwartet in ("#E30613", "Montserrat", "Open Sans", "logo.svg", "impressum"):
            self.assertIn(erwartet, text)

    def test_robots_und_logo_fallback(self):
        netz = falsches_netz({
            BASIS: (HTML, "text/html"),
            BASIS + "robots.txt": ("User-agent: *\nDisallow: /css/\n", "text/plain"),
            # the svg is broken (HTML error page) -> next candidate
            BASIS + "media/feldmark-logo.svg": ("<html>Fehler</html>", "text/html"),
            BASIS + "apple-touch-icon.png": (b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png"),
        })
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            daten = branding.lesen(BASIS, self.tmp)
        self.assertNotIn(BASIS + "css/style.css", netz.aufrufe)
        self.assertEqual(daten["geladene_css"], [])
        self.assertTrue((self.tmp / "logo.png").exists())
        self.assertTrue(any("Ersatz" in w for w in daten["warnungen"]))

    def test_unbekannte_herkunft_wird_bei_google_geprueft(self):
        html = '<html><head><link rel="stylesheet" href="/a.css"></head><body></body></html>'
        netz = falsches_netz({
            BASIS: (html, "text/html"),
            BASIS + "a.css": (':root { font-family: "Open Sans", sans-serif; }', "text/css"),
            branding.google_css_url("Open Sans", [400]): ("@font-face { src: url(x.woff2); }", "text/css"),
        })
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            daten = branding.lesen(BASIS, self.tmp)
        self.assertTrue(daten["schriften"]["text"]["herkunft"]["art"].startswith("frei bei Google Fonts"))
        self.assertFalse(any("lizenzpflichtig" in w for w in daten["warnungen"]))

    def test_inline_svg_wird_gespeichert(self):
        html = '<html><body><header><a href="/" class="logo"><svg viewBox="0 0 4 4"><rect width="4" height="4"/></svg></a></header></body></html>'
        netz = falsches_netz({BASIS: (html, "text/html")})
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            branding.lesen(BASIS, self.tmp)
        svg = (self.tmp / "logo.svg").read_text()
        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
        self.assertTrue(svg.endswith("</svg>"))


GOOGLE_CSS = """/* cyrillic */
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/opensans/v40/cyr.woff2) format('woff2');
  unicode-range: U+0301, U+0400-045F;
}
/* latin-ext */
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/opensans/v40/ext.woff2) format('woff2');
  unicode-range: U+0100-02BA;
}
/* latin */
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/opensans/v40/lat.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131;
}
/* latin */
@font-face {
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url(https://fonts.gstatic.com/s/opensans/v40/lat.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131;
}
"""


class SchriftenLaden(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def netz(self, google_ok=True):
        aufrufe = []

        def holen(url, timeout=None, max_bytes=None, accept=None):
            aufrufe.append(url)
            if url.startswith(branding.GOOGLE_CSS2):
                if not google_ok:
                    raise branding.HolFehler("HTTP 400", 400)
                return antwort(url, GOOGLE_CSS, "text/css")
            if url.startswith("https://fonts.gstatic.com/"):
                return antwort(url, b"wOF2" + url.encode(), "font/woff2")
            raise branding.HolFehler("HTTP 404", 404)

        holen.aufrufe = aufrufe
        return holen

    def test_google_schrift_lokal(self):
        netz = self.netz()
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            code = branding.schriften("Open Sans", [400, 600], self.tmp)
        self.assertEqual(code, 0)
        self.assertIn("family=Open+Sans:wght@400;600&display=swap", netz.aufrufe[0])
        self.assertFalse(any("cyr.woff2" in u for u in netz.aufrufe))
        self.assertEqual(sorted(p.name for p in self.tmp.glob("*.woff2")),
                         ["OpenSans-400-600-latin.woff2", "OpenSans-400-latin-ext.woff2"])
        regeln = branding.font_face_regeln((self.tmp / "fonts.css").read_text())
        self.assertEqual(len(regeln), 3)
        self.assertIn('src: url("assets/fonts/OpenSans-400-latin-ext.woff2") format("woff2")', regeln[0])
        self.assertTrue(all("font-display: swap" in r and "googleapis" not in r and "gstatic" not in r for r in regeln))
        # second run for the same family replaces instead of duplicating
        with mock.patch.object(branding, "http_get", netz), redirect_stdout(io.StringIO()):
            branding.schriften("Open Sans", [400, 600], self.tmp)
        self.assertEqual(len(branding.font_face_regeln((self.tmp / "fonts.css").read_text())), 3)

    def test_keine_google_schrift(self):
        puffer = io.StringIO()
        with mock.patch.object(branding, "http_get", self.netz(google_ok=False)), redirect_stdout(puffer):
            code = branding.schriften("Gotham", [400, 700], self.tmp)
        self.assertEqual(code, 2)
        self.assertIn("keine Google-Schrift", puffer.getvalue())
        self.assertIn("Montserrat", puffer.getvalue())
        self.assertIn("Outfit", puffer.getvalue())
        self.assertFalse((self.tmp / "fonts.css").exists())


class Anwenden(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.vorlage_dir = self.tmp / "seite"
        shutil.copytree(VORLAGE, self.vorlage_dir)
        self.index = self.vorlage_dir / "index.html"
        self.original = self.index.read_text(encoding="utf-8")
        fonts = self.vorlage_dir / "assets" / "fonts"
        for name in ("Montserrat-600-700-latin.woff2", "OpenSans-400-latin.woff2"):
            (fonts / name).write_bytes(b"wOF2")
        (fonts / "fonts.css").write_text(
            "/* Kopf */\n"
            + branding.font_face_zeile("Montserrat", "normal", "600", "assets/fonts/Montserrat-600-700-latin.woff2", "U+0000-00FF") + "\n"
            + branding.font_face_zeile("Open Sans", "normal", "400", "assets/fonts/OpenSans-400-latin.woff2", "U+0000-00FF") + "\n",
            encoding="utf-8")
        arbeit = self.tmp / "branding"
        arbeit.mkdir()
        (arbeit / "logo.svg").write_bytes(LOGO_SVG)
        self.branding = {
            "farben": {
                "akzent": {"wert": "#E30613"}, "akzent_dunkel": {"wert": "#C10510"},
                "text": {"wert": "#222222"}, "grund": {"wert": "#FFFFFF"},
            },
            "schriften": {"titel": {"familie": "Montserrat"}, "text": {"familie": "Open Sans"}},
            "logo": {"datei": str(arbeit / "logo.svg")},
        }

    def test_anwenden_auf_echte_vorlage(self):
        with redirect_stdout(io.StringIO()):
            aenderungen = branding.anwenden(self.index, self.branding)
        neu = self.index.read_text(encoding="utf-8")
        self.assertEqual((self.vorlage_dir / "index.html.bak").read_text(encoding="utf-8"), self.original)
        self.assertTrue(aenderungen)

        design = neu[neu.index("const SEITE"):neu.index("bausteine:")]
        for erwartet in ('akzent: "#E30613"', 'akzent_dunkel: "#C10510"', 'text: "#222222"', 'grund: "#FFFFFF"', 'radius: "20px"'):
            self.assertIn(erwartet, design)
        absender = neu[neu.index("const ABSENDER"):neu.index("const SEITE")]
        self.assertIn('logo: "assets/logo.svg"', absender)
        self.assertIn('<link rel="icon" href="assets/logo.svg">', neu)
        self.assertEqual((self.vorlage_dir / "assets" / "logo.svg").read_bytes(), LOGO_SVG)

        stil = neu[neu.index("<style>"):neu.index(":root")]
        self.assertEqual(stil.count("@font-face"), 2)
        self.assertIn('font-family: "Montserrat"', stil)
        self.assertNotIn("Funnel Display", stil)
        root = neu[neu.index(":root"):]
        root = root[:root.index("}")]
        self.assertIn('--schrift-titel: "Montserrat", Helvetica, Arial, sans-serif;', root)
        self.assertIn('--schrift-text: "Open Sans", system-ui, -apple-system, "Segoe UI", sans-serif;', root)

        # only targeted lines changed, nothing reformatted
        geaendert = [z for z in difflib.ndiff(self.original.splitlines(), neu.splitlines()) if z[:2] in ("- ", "+ ")]
        erlaubt = ("@font-face", "akzent", "text:", "grund:", "logo:", 'rel="icon"', "--schrift-", "--ang-")
        for zeile in geaendert:
            self.assertTrue(any(e in zeile for e in erlaubt), zeile)
        alte_regeln = len(branding.font_face_regeln(self.original[:self.original.index(":root")]))
        self.assertEqual(len(neu.splitlines()), len(self.original.splitlines()) - alte_regeln + 2)

    def test_systemschrift_nutzt_lokalen_vorschlag(self):
        fonts = self.vorlage_dir / "assets" / "fonts"
        (fonts / "Inter-400-latin.woff2").write_bytes(b"wOF2")
        (fonts / "fonts.css").write_text(
            branding.font_face_zeile("Inter", "normal", "400", "assets/fonts/Inter-400-latin.woff2") + "\n", encoding="utf-8")
        system = {"familie": None, "systemschrift": True, "vorschlag": "Inter"}
        self.branding["schriften"] = {"titel": dict(system), "text": dict(system)}
        with redirect_stdout(io.StringIO()):
            branding.anwenden(self.index, self.branding)
        neu = self.index.read_text(encoding="utf-8")
        self.assertIn('--schrift-titel: "Inter", Helvetica, Arial, sans-serif;', neu)
        self.assertIn('--schrift-text: "Inter", system-ui', neu)

    def test_schrift_ueberschreiben_und_fehlende_stelle(self):
        with redirect_stdout(io.StringIO()) as puffer:
            branding.anwenden(self.index, self.branding, titel_schrift="Georgia")
        self.assertIn('--schrift-titel: "Georgia", "Times New Roman", serif;', self.index.read_text(encoding="utf-8"))
        self.assertNotIn("nicht lokal eingebunden", puffer.getvalue())  # system font: fine
        kaputt = self.tmp / "kaputt.html"
        kaputt.write_text("<html><style>\n</style></html>", encoding="utf-8")
        with self.assertRaises(branding.VorlagenFehler):
            branding.anwenden(kaputt, {"farben": {"akzent": {"wert": "#E30613"}}})
        self.assertFalse(kaputt.with_name("kaputt.html.bak").exists())


if __name__ == "__main__":
    unittest.main()

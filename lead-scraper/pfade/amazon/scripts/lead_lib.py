"""Gemeinsame Helfer fuer die Leadlisten-Pipeline."""
import csv, json, os, re, sys

SPALTEN_NEU = [
    'Seller Storefront URL', 'Geschäftsname (Impressum)', 'Handelsregister',
    'Geschäftsadresse', 'Website', 'GF Vorname', 'GF Nachname', 'GF Alle',
    'GF Quelle', 'GF Confidence', 'Anrede', 'Anrede Confidence',
    'Ansprache', 'Ansprache Grund',
]
MARKETPLACE_DE = 'A1PA6795UKMFR9'


def lade(pfad):
    """CSV lesen. utf-8-sig, weil die Exporte ein BOM haben."""
    with open(pfad, encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        rows = list(r)
        cols = list(r.fieldnames or [])
    for c in SPALTEN_NEU:
        if c not in cols:
            cols.append(c)
    for row in rows:
        for c in cols:
            row.setdefault(c, '')
    return rows, cols


def schreibe(pfad, rows, cols):
    """QUOTE_ALL, weil Firmennamen Kommas und Anfuehrungszeichen enthalten."""
    with open(pfad, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def arbeit_dir(csv_pfad):
    d = os.path.join(os.path.dirname(os.path.abspath(csv_pfad)), 'arbeit')
    os.makedirs(os.path.join(d, 'gf'), exist_ok=True)
    return d


def umsatz(row):
    try:
        return float(row.get('Est. Monthly Revenue') or 0)
    except ValueError:
        return 0.0


def storefront_url(sid):
    return f'https://www.amazon.de/s?me={sid}&marketplaceID={MARKETPLACE_DE}'


def ist_deutsch(addr):
    return bool(re.search(r'\bDE\b|Deutschland|Germany', addr or '', re.I))


def gf_chunks(rows, arbeit, n=40):
    """Firmen fuer die Agenten-Recherche: DE-Adresse, Geschaeftsname da, GF fehlt.
    Nach Umsatz sortiert, damit die wertvollsten Leads zuerst kommen -- falls
    ein Lauf abbricht, hat man wenigstens die wichtigen."""
    kand = [r for r in rows
            if ist_deutsch(r.get('Geschäftsadresse'))
            and r.get('Geschäftsname (Impressum)', '').strip()
            and not r.get('GF Vorname', '').strip()]
    seen, uniq = set(), []
    for r in sorted(kand, key=lambda x: -umsatz(x)):
        g = r['Geschäftsname (Impressum)']
        if g in seen:
            continue
        seen.add(g)
        uniq.append({'firma': g, 'hr': r.get('Handelsregister', ''), 'ort': r.get('Geschäftsadresse', '')})
    gf_dir = os.path.join(arbeit, 'gf')
    for alt in os.listdir(gf_dir):
        if alt.startswith('chunk_'):
            os.remove(os.path.join(gf_dir, alt))
    for i in range(0, len(uniq), n):
        with open(os.path.join(gf_dir, f'chunk_{i // n:02d}.json'), 'w', encoding='utf-8') as f:
            json.dump(uniq[i:i + n], f, ensure_ascii=False, indent=0)
    return len(uniq), (len(uniq) + n - 1) // n


def personen_name(gname, addr):
    """Einzelunternehmer: Der Geschaeftsname IST die Person. Nur bei DE-Adresse
    und ohne Rechtsform-Kuerzel, sonst faengt man chinesische Firmennamen ein."""
    rechtsform = re.compile(
        r'GmbH|UG\b|e\.K|OHG|\bKG\b|GbR|\bAG\b|Ltd|LIMITED|LLC|Inc\b|B\.V|S\.R\.L|s\.r\.o|'
        r'OÜ|ApS|A/S|SIA|Co\.|Corp|Company|Store|Shop|Trading|Technolog|GROUP|SE\b|AS\b|BV\b', re.I)
    person = re.compile(r'^[A-ZÄÖÜ][a-zäöüß]+(?: [A-ZÄÖÜ][a-zäöüß]+){1,2}$')
    if not gname or not ist_deutsch(addr):
        return None
    if rechtsform.search(gname) or not person.match(gname):
        return None
    p = gname.split()
    return p[0], p[-1]

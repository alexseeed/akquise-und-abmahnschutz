#!/usr/bin/env python3
"""Agenten-Ergebnisse (Website + Geschaeftsfuehrer) in die CSV mergen.

  python3 merge_gf.py <liste.csv> <arbeit/gf/>

Liest alle result_*.json aus dem Ordner. Fehlende Chunks sind kein Fehler --
so kann man auch nach einem Teillauf schon mergen.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lead_lib import lade, schreibe


def main(pfad, gf_dir):
    res = {}
    dateien = sorted(glob.glob(os.path.join(gf_dir, 'result_*.json')))
    for f in dateien:
        try:
            with open(f, encoding='utf-8') as fh:
                for x in json.load(fh):
                    if x.get('firma'):
                        res[x['firma']] = x
        except (json.JSONDecodeError, KeyError) as e:
            print(f'  WARNUNG: {os.path.basename(f)} unlesbar ({e}) - uebersprungen')

    rows, cols = lade(pfad)
    n = 0
    for row in rows:
        if row.get('GF Vorname', '').strip():
            continue  # nicht ueberschreiben
        x = res.get(row.get('Geschäftsname (Impressum)', ''))
        if not x:
            continue
        if x.get('website'):
            row['Website'] = x['website']
        gfs = [g for g in (x.get('gf') or []) if g and g.strip()]
        if not gfs:
            continue
        teile = gfs[0].split()
        if len(teile) < 2:
            continue  # einzelnes Wort ist kein Personenname
        row['GF Vorname'] = ' '.join(teile[:-1])
        row['GF Nachname'] = teile[-1]
        row['GF Alle'] = '; '.join(gfs)
        row['GF Quelle'] = x.get('quelle', '')
        row['GF Confidence'] = x.get('confidence', '')
        # Anrede kommt aus demselben Agenten-Call (siehe referenzen/agent-prompt.md).
        # Nur uebernehmen, was der Agent auch geliefert hat -- fehlt sie, holt
        # anrede.py die Zeile spaeter in Phase 4b nach.
        if x.get('anrede') in ('Herr', 'Frau'):
            row['Anrede'] = x['anrede']
        if x.get('anrede_confidence') is not None:
            try:
                row['Anrede Confidence'] = str(int(float(x['anrede_confidence'])))
            except (TypeError, ValueError):
                pass
        n += 1

    schreibe(pfad, rows, cols)
    ges = len(rows)
    mit_gf = sum(1 for r in rows if r['GF Vorname'].strip())
    print(f'Chunks gelesen: {len(dateien)}, Firmen: {len(res)}')
    print(f'Zeilen neu befuellt: {n}\n')
    print(f'Zeilen gesamt:        {ges}')
    print(f'mit Seller ID:        {sum(1 for r in rows if r["Seller ID"].strip())}')
    print(f'mit Storefront URL:   {sum(1 for r in rows if r["Seller Storefront URL"].strip())}')
    print(f'mit Website:          {sum(1 for r in rows if r["Website"].strip())}')
    print(f'mit Geschäftsführer:  {mit_gf}  ({100*mit_gf//max(ges,1)}%)')
    print(f'  davon unsicher:     {sum(1 for r in rows if r["GF Confidence"] == "unsicher")}')
    print(f'  aus Website:        {sum(1 for r in rows if r["GF Quelle"] == "website_impressum")}')
    print(f'  aus Handelsregister:{sum(1 for r in rows if r["GF Quelle"] == "handelsregister")}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Aufruf: python3 merge_gf.py <liste.csv> <arbeit/gf/>')
    main(sys.argv[1], sys.argv[2])

#!/usr/bin/env python3
"""Seller IDs + Impressum in die CSV mergen, Storefront-URLs bauen.

  python3 merge_amazon.py <liste.csv> [seller_ids.json] [impressum.json]

Idempotent: fuellt nur leere Felder. Ein abgebrochener Lauf wird einfach
wiederholt, ohne dass vorhandene Daten kaputtgehen.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lead_lib import lade, schreibe, arbeit_dir, storefront_url, gf_chunks, personen_name


def main(pfad, seller_json=None, imp_json=None):
    rows, cols = lade(pfad)
    arbeit = arbeit_dir(pfad)

    neu_ids = 0
    if seller_json and os.path.exists(seller_json):
        with open(seller_json, encoding='utf-8') as f:
            for x in json.load(f):
                if not x.get('sellerId'):
                    continue
                r = rows[x['i']]
                if r.get('Seller ID', '').strip():
                    continue  # nie ueberschreiben
                r['Seller ID'] = x['sellerId']
                if 'Match Method' in cols:
                    r['Match Method'] = 'chrome_exact_dominant'
                neu_ids += 1

    # Storefront-URLs: immer aus der aktuellen Seller ID ableiten, damit
    # URL und ID nicht auseinanderlaufen koennen.
    urls = 0
    for r in rows:
        sid = r.get('Seller ID', '').strip()
        r['Seller Storefront URL'] = storefront_url(sid) if sid else ''
        if sid:
            urls += 1

    neu_imp = 0
    if imp_json and os.path.exists(imp_json):
        with open(imp_json, encoding='utf-8') as f:
            imp = {x['id']: x for x in json.load(f) if x.get('id')}
        for r in rows:
            i = imp.get(r.get('Seller ID', '').strip())
            if not i or not i.get('gname'):
                continue
            if r.get('Geschäftsname (Impressum)', '').strip():
                continue
            r['Geschäftsname (Impressum)'] = i.get('gname') or ''
            r['Handelsregister'] = i.get('hr') or ''
            r['Geschäftsadresse'] = i.get('addr') or ''
            neu_imp += 1

    # Einzelunternehmer: hier steht die Person schon im Geschaeftsnamen,
    # die brauchen keine Agenten-Recherche.
    gratis_gf = 0
    for r in rows:
        if r.get('GF Vorname', '').strip():
            continue
        gn = r.get('Geschäftsname (Impressum)', '')
        addr = r.get('Geschäftsadresse', '')
        # Sonderfall "Firma GmbH/Nachname Vorname"
        if '/' in gn and not any(t in gn for t in ('A/S', '/mag', 'w/')):
            teile = gn.split('/')[-1].strip().split()
            if len(teile) == 2:
                r['GF Nachname'], r['GF Vorname'] = teile[0], teile[1]
                r['GF Quelle'] = 'amazon_impressum_gname'
                r['GF Confidence'] = 'unsicher'
                gratis_gf += 1
                continue
        p = personen_name(gn, addr)
        if p:
            r['GF Vorname'], r['GF Nachname'] = p
            r['GF Quelle'] = 'amazon_impressum_einzelunternehmer'
            r['GF Confidence'] = 'sicher'
            gratis_gf += 1

    schreibe(pfad, rows, cols)
    n_gf, n_chunks = gf_chunks(rows, arbeit)

    print(f'Seller IDs neu eingetragen: {neu_ids}')
    print(f'Storefront URLs gesetzt:    {urls}')
    print(f'Impressen neu eingetragen:  {neu_imp}')
    print(f'GF direkt aus Impressum:    {gratis_gf}')
    print(f'\nPhase 4: {n_gf} Firmen in {n_chunks} Chunks unter {arbeit}/gf/')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Aufruf: python3 merge_amazon.py <liste.csv> [seller_ids.json] [impressum.json]')
    main(sys.argv[1],
         sys.argv[2] if len(sys.argv) > 2 else None,
         sys.argv[3] if len(sys.argv) > 3 else None)

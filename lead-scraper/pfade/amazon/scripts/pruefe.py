#!/usr/bin/env python3
"""Programmatische Pruefung der fertigen Liste + Stichprobe fuer die Agenten-Verifikation.

  python3 pruefe.py <liste.csv> [anzahl_stichproben]

Faengt die Fehler, die man ohne Netzwerk finden kann. Ersetzt NICHT die
inhaltliche Verifikation der Geschaeftsfuehrer -- die braucht Phase 5.
"""
import csv, json, random, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lead_lib import lade, storefront_url

URL_RE = re.compile(r'https://www\.amazon\.de/s\?me=[A-Z0-9]{10,20}&marketplaceID=A1PA6795UKMFR9$')


def main(pfad, n_stich=5):
    rows, _ = lade(pfad)
    fehler = []

    for i, r in enumerate(rows, 2):  # 2 = erste Datenzeile in der Tabelle
        sid = r.get('Seller ID', '').strip()
        url = r.get('Seller Storefront URL', '').strip()
        if sid and not url:
            fehler.append(f'Zeile {i}: Seller ID ohne Storefront URL')
        if url and not URL_RE.match(url):
            fehler.append(f'Zeile {i}: URL-Format falsch: {url[:60]}')
        if url and sid and sid not in url:
            fehler.append(f'Zeile {i}: URL enthaelt fremde Seller ID')
        if url and not sid:
            fehler.append(f'Zeile {i}: URL ohne Seller ID')
        # Ein Geschaeftsfuehrer ohne Quellenangabe ist nicht nachvollziehbar
        if r.get('GF Vorname', '').strip() and not r.get('GF Quelle', '').strip():
            fehler.append(f'Zeile {i}: GF ohne Quelle')

    print(f'Zeilen geprueft: {len(rows)}')
    if fehler:
        print(f'\nPROBLEME ({len(fehler)}):')
        for f in fehler[:20]:
            print('  ' + f)
        if len(fehler) > 20:
            print(f'  ... und {len(fehler)-20} weitere')
    else:
        print('Strukturpruefung: keine Probleme.')

    # Stichprobe fuer Phase 5: nur "sichere" Website-Treffer, denn genau deren
    # Zuverlaessigkeit ist die Frage. Unsichere sind ohnehin markiert.
    kand = [r for r in rows
            if r.get('GF Quelle') == 'website_impressum'
            and r.get('GF Confidence') == 'sicher'
            and r.get('Website', '').strip()]
    seen, uniq = set(), []
    for r in kand:
        g = r['Geschäftsname (Impressum)']
        if g in seen:
            continue
        seen.add(g)
        uniq.append(r)
    if uniq:
        random.seed(42)  # reproduzierbar, damit man Laeufe vergleichen kann
        print(f'\nStichprobe fuer Phase 5 ({min(n_stich, len(uniq))} von {len(uniq)} Firmen):')
        for r in random.sample(uniq, min(n_stich, len(uniq))):
            print(json.dumps({'firma': r['Geschäftsname (Impressum)'],
                              'gf': r['GF Alle'] or f"{r['GF Vorname']} {r['GF Nachname']}",
                              'url': r['Website']}, ensure_ascii=False))

    return 1 if fehler else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Aufruf: python3 pruefe.py <liste.csv> [anzahl]')
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5))

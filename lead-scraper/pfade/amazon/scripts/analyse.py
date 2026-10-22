#!/usr/bin/env python3
"""Bestandsaufnahme: was fehlt, wie lange dauert es, was ist zu tun.

  python3 analyse.py <liste.csv>

Legt neben der Liste einen arbeit/-Ordner an mit:
  todo_seller.json  - [[zeilenindex, brand, dominantSeller], ...] fuer Phase 1
  todo_impressum.json - ["SELLERID", ...] fuer Phase 3
  gf/chunk_NN.json  - Firmenlisten fuer die Agenten in Phase 4
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lead_lib import lade, arbeit_dir, gf_chunks, umsatz


def main(pfad):
    rows, cols = lade(pfad)
    arbeit = arbeit_dir(pfad)
    n = len(rows)

    hat_id = [r for r in rows if r.get('Seller ID', '').strip()]
    # Ohne Dominant Seller ist exaktes Matching unmoeglich -> gar nicht erst versuchen
    todo_seller = [[i, r['Brand Name'], r['Dominant Seller']]
                   for i, r in enumerate(rows)
                   if not r.get('Seller ID', '').strip() and r.get('Dominant Seller', '').strip()]
    ohne_dom = sum(1 for r in rows
                   if not r.get('Seller ID', '').strip() and not r.get('Dominant Seller', '').strip())

    with open(os.path.join(arbeit, 'todo_seller.json'), 'w', encoding='utf-8') as f:
        json.dump(todo_seller, f, ensure_ascii=False, separators=(',', ':'))

    ids_ohne_imp = sorted({r['Seller ID'].strip() for r in hat_id
                           if not r.get('Geschäftsname (Impressum)', '').strip()})
    with open(os.path.join(arbeit, 'todo_impressum.json'), 'w', encoding='utf-8') as f:
        json.dump(ids_ohne_imp, f, ensure_ascii=False, separators=(',', ':'))

    n_gf, n_chunks = gf_chunks(rows, arbeit)

    hat_gf = sum(1 for r in rows if r.get('GF Vorname', '').strip())
    print(f'Datei: {pfad}')
    print(f'Zeilen: {n}\n')
    print(f'Seller ID vorhanden:      {len(hat_id):5d}  ({100*len(hat_id)//max(n,1)}%)')
    print(f'  -> Phase 1 zu suchen:   {len(todo_seller):5d}')
    if ohne_dom:
        print(f'  -> ohne Dominant Seller:{ohne_dom:5d}  (nicht ermittelbar, uebersprungen)')
    print(f'Impressum vorhanden:      {n - len(ids_ohne_imp) - (n - len(hat_id)):5d}')
    print(f'  -> Phase 3 abzurufen:   {len(ids_ohne_imp):5d}  (unique Seller IDs)')
    print(f'Geschäftsführer vorhanden:{hat_gf:5d}')
    print(f'  -> Phase 4 zu suchen:   {n_gf:5d}  DE-Firmen in {n_chunks} Chunks\n')

    print('Geschätzte Laufzeit:')
    if todo_seller:
        print(f'  Phase 1: ~{max(1, round(len(todo_seller)/50))} min Browser, ~{max(4, round(len(todo_seller)/40))} Tool-Calls')
    if ids_ohne_imp:
        print(f'  Phase 3: ~{max(1, round(len(ids_ohne_imp)/260))} min Browser, ~{max(4, round(len(ids_ohne_imp)/70))} Tool-Calls')
    if n_chunks:
        print(f'  Phase 4: ~{max(4, round(n_chunks/7)*4)} min, {n_chunks} Agenten (je 6-9 parallel, model=sonnet)')
    print(f'\nArbeitsdateien: {arbeit}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Aufruf: python3 analyse.py <liste.csv>')
    main(sys.argv[1])

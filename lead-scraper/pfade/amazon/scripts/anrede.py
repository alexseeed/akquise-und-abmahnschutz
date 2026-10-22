#!/usr/bin/env python3
"""Anrede und Ansprache berechnen.

  python3 anrede.py <liste.csv> [arbeit/anrede_result.json]

Die Geschlechtsbestimmung machen die Agenten (Phase 4 bzw. 4b) -- dieses Skript
wendet nur die Regeln an. Das ist Absicht: Die Regel gehoert an EINE Stelle, damit
Schwellwert und Wortlaut nicht in zwanzig Agenten-Antworten auseinanderlaufen.

Regeln:
  GF-Angabe unsicher            -> "Guten Tag"       (falsche Anrede ist schlimmer als keine)
  Anrede-Confidence > 60        -> "Guten Tag Herr/Frau <Nachname>"
  Anrede-Confidence <= 60       -> "Guten Tag"
  kein Geschaeftsfuehrer        -> "Guten Tag"
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lead_lib import lade, schreibe, arbeit_dir

SCHWELLE = 60  # exklusiv: >60 nutzt den Namen, <=60 gruesst neutral
NEUTRAL = 'Guten Tag'


def ansprache(row):
    """Gibt (text, grund) zurueck. Der Grund macht nachvollziehbar, warum
    jemand neutral gegruesst wird -- sonst ist die Spalte eine Blackbox."""
    nach = (row.get('GF Nachname') or '').strip()
    anrede = (row.get('Anrede') or '').strip()
    if not nach:
        return NEUTRAL, 'kein Geschäftsführer'
    if (row.get('GF Confidence') or '').strip() == 'unsicher':
        return NEUTRAL, 'GF-Angabe unsicher'
    if anrede not in ('Herr', 'Frau'):
        return NEUTRAL, 'Anrede nicht bestimmbar'
    try:
        conf = int(float(row.get('Anrede Confidence') or 0))
    except ValueError:
        conf = 0
    if conf <= SCHWELLE:
        return NEUTRAL, f'Vorname mehrdeutig ({conf}%)'
    return f'{NEUTRAL} {anrede} {nach}', f'{conf}%'


def main(pfad, result_json=None):
    rows, cols = lade(pfad)
    arbeit = arbeit_dir(pfad)

    # Ergebnisse aus Phase 4b nachtragen
    if result_json and os.path.exists(result_json):
        with open(result_json, encoding='utf-8') as f:
            res = {(x.get('vorname', ''), x.get('nachname', '')): x for x in json.load(f)}
        for r in rows:
            k = (r.get('GF Vorname', ''), r.get('GF Nachname', ''))
            if k in res and not (r.get('Anrede') or '').strip():
                r['Anrede'] = res[k].get('anrede', '') or ''
                r['Anrede Confidence'] = str(res[k].get('anrede_confidence', 0))

    for r in rows:
        text, grund = ansprache(r)
        r['Ansprache'] = text
        r['Ansprache Grund'] = grund

    schreibe(pfad, rows, cols)

    # Wer hat einen GF, aber noch keine Anrede? -> Phase 4b
    # Zeilen mit unsicherer GF-Angabe bleiben ohnehin neutral -- fuer die eine
    # Anrede zu bestimmen waere Tokenverschwendung fuer ein Ergebnis, das nie
    # verwendet wird.
    offen = []
    for r in rows:
        if (r.get('GF Confidence') or '').strip() == 'unsicher':
            continue
        if (r.get('GF Nachname') or '').strip() and not (r.get('Anrede') or '').strip() \
           and not (r.get('Anrede Confidence') or '').strip():
            offen.append({'vorname': r.get('GF Vorname', ''), 'nachname': r.get('GF Nachname', '')})
    # deduplizieren, dieselbe Person kann mehrfach vorkommen
    uniq = list({(o['vorname'], o['nachname']): o for o in offen}.values())
    todo = os.path.join(arbeit, 'anrede_todo.json')
    if uniq:
        with open(todo, 'w', encoding='utf-8') as f:
            json.dump(uniq, f, ensure_ascii=False, indent=0)

    mit_gf = sum(1 for r in rows if (r.get('GF Nachname') or '').strip())
    named = sum(1 for r in rows if r['Ansprache'] != NEUTRAL)
    print(f'Zeilen:                    {len(rows)}')
    print(f'mit Geschäftsführer:       {mit_gf}')
    print(f'persönliche Ansprache:     {named}')
    print(f'neutrale Ansprache:        {len(rows) - named}')
    if mit_gf:
        from collections import Counter
        c = Counter(r['Ansprache Grund'] for r in rows if r['Ansprache'] == NEUTRAL and (r.get('GF Nachname') or '').strip())
        if c:
            print('\n  Warum trotz Geschäftsführer neutral:')
            for k, v in c.most_common():
                print(f'    {k:32} {v}')
    if uniq:
        print(f'\nOFFEN: {len(uniq)} Namen ohne Anrede -> {todo}')
        print('       Phase 4b laufen lassen (referenzen/agent-prompt.md), dann dieses Skript erneut.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Aufruf: python3 anrede.py <liste.csv> [arbeit/anrede_result.json]')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

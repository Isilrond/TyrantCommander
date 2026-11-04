#!/usr/bin/env python3
"""
replay_check.py - Neuberechnung auffaelliger Prognosen mit tuo.exe (nur lesend).

Zu jedem Zug eines Logs steht der komplette TUO-Befehl (tuo_cmd: Decks, Feld, Hand,
Kartenzustaende). Dieses Skript startet ihn erneut, aber mit viel mehr Spielen, und
beantwortet damit drei Fragen:

  A  Replay    : gleicher Befehl, reorder N (Standard 20000 statt 5000 live).
                 Ist die geloggte 100%-Prognose stabil, oder war es ein Ausreisser des Live-Laufs?
                 Bleibt A bei ~100 %, glaubte TUO ehrlich an den Sieg (die Abweichung liegt dann
                 zwischen Sim und echtem Spiel, nicht in der Rechnung).
  B  Ergaenzt  : wie A, aber das Gegnerdeck wird um alle Karten ergaenzt, die der Gegner im
                 ganzen Kampf wirklich gespielt hat (bei teilweise bekanntem Deck).
                 Faellt B deutlich unter A, erklaeren die unbekannten Karten die Prognose.
  C  Flex-Iter : (nur mit --flex-iter) wie A, aber mit mehr Probespielen in der Flex-Wahl innerhalb der
                 Sim (Live: 50). Zeigt, ob dieser Parameter die Prognose verschiebt.

Standard: nur die auffaelligen Zuege (Niederlage: Anzeige >= 95 %, Sieg: <= 5 %), je Log hoechstens
3 Zuege (erster, mittlerer, letzter). Mit --all-turns werden alle Zuege gerechnet.

Aufruf:
    python replay_check.py --tuo C:\\TUO-Live\\tuo.exe                       (Logs: data\\combatlog\\suspicious)
    python replay_check.py logs_ordner --tuo tuo.exe --n 20000 --workers 2 --threads 8
Ausgabe: replay_check.csv und replay_check.txt (Praefix mit --out aenderbar).
"""
import argparse
import concurrent.futures as cf
import csv
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from collections import Counter

COLS = ['log', 'mode', 'result', 'enemy', 'script', 'turn', 'shown', 'logged_reorder', 'incomplete',
        'a_replay', 'b_completed', 'c_flex', 'added_cards', 'ok']

OPT_RE = re.compile(r'Optimized Deck:.*?(?::\s*([\d.]+):\s*|\([^\)]*\)\s*[\d.]+(?:\s*\[[^\]]*\])?\s*:\s*)(.+)')


def parse_cmd(cmd):
    rest = cmd.split('tuo.exe', 1)[1] if 'tuo.exe' in cmd else cmd.split(' ', 1)[1]
    return shlex.split(rest.replace('\\"', '"'))


def parse_win(output):
    """Gleiche Formate wie das Hauptskript: pvp 'Optimized Deck: N units: 99.8: ...',
    brawl/gw '(99.8% win) ...', sonst 'win%: 99.8'."""
    m = OPT_RE.search(output)
    if m:
        if m.group(1):
            return float(m.group(1))
        p = re.search(r'\(([\d.]+)%\s*win\)', output)
        if p:
            return float(p.group(1))
    p = re.search(r'win%:\s*([\d.]+)', output)
    return float(p.group(1)) if p else None


def build_args(args, n, threads, flex_iter=None, enemy_deck=None):
    a = list(args)
    if 'reorder' not in a:
        return None
    a[a.index('reorder') + 1] = str(n)
    if '-t' in a:
        a[a.index('-t') + 1] = str(threads)
    else:
        a += ['-t', str(threads)]
    if flex_iter is not None and 'flexible-iter' in a:
        a[a.index('flexible-iter') + 1] = str(flex_iter)
    if enemy_deck is not None and len(a) > 1:
        a[1] = enemy_deck
    return a


def run_tuo(exe, cwd, args, timeout):
    env = dict(os.environ)
    env.pop('TUO_LIVE_DEBUG', None)
    try:
        p = subprocess.run([exe] + args, cwd=cwd, env=env, capture_output=True, text=True,
                           errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return parse_win(p.stdout + p.stderr)


def actual_enemy_cards(turns):
    """Karten, die der Gegner im ganzen Kampf auf dem Feld hatte (hoechste Anzahl gleichzeitig) -
    gleiche Logik wie 'actual cards played' in Menue F>6>5."""
    act = {}
    for t in turns:
        cnt = {}
        for c in (t.get('field') or {}).get('enemy', []):
            if c.get('card_id') and c.get('name'):
                cnt[c['name']] = cnt.get(c['name'], 0) + 1
        for n, k in cnt.items():
            act[n] = max(act.get(n, 0), k)
    return act


def complete_enemy_deck(deck_str, act):
    """Ergaenzt fehlende Karten (Stufe = haeufigste Stufe der vorhandenen Karten). Gibt (deck, [ergaenzt])."""
    parts = [p.strip() for p in deck_str.split(',') if p.strip()]
    if len(parts) < 3 or not act:
        return deck_str, []
    base = lambda n: re.sub(r'-\d+$', '', n.strip())
    start = 2 if parts[1].startswith('Alpha ') else 1
    have = Counter(base(p) for p in parts[start:])
    skip = {base(p) for p in parts[:start]}
    lvls = Counter(m.group(1) for p in parts[start:] for m in [re.search(r'-(\d+)$', p)] if m)
    suf = ('-' + lvls.most_common(1)[0][0]) if lvls else ''
    add = []
    for n, k in act.items():
        if n in skip:
            continue
        add += [n + suf] * max(0, k - have.get(n, 0))
    return (', '.join(parts + add) if add else deck_str), add


def pick_turns(d, all_turns, max_per_log, lo_win, hi_loss):
    res = d.get('result')
    ts = [t for t in d.get('turns', []) if t.get('tuo_cmd') and t.get('tuo_win_pct') is not None]
    if not all_turns:
        if res == 'LOSS':
            ts = [t for t in ts if t['tuo_win_pct'] >= hi_loss]
        elif res == 'WIN':
            ts = [t for t in ts if t['tuo_win_pct'] <= lo_win]
        else:
            ts = []
        if max_per_log and len(ts) > max_per_log:
            idx = sorted({0, len(ts) // 2, len(ts) - 1})
            ts = [ts[i] for i in idx][:max_per_log]
    return ts


def collect_logs(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                files += [os.path.join(root, n) for n in names if n.lower().endswith('.json')]
        else:
            files += glob.glob(p)
    return sorted(f for f in set(files) if not os.path.basename(f).startswith('_'))


def fnum(x):
    try:
        return float(x) if x not in (None, '') else None
    except Exception:
        return None


def verdict(r):
    a, b, lg = r['a_replay'], r['b_completed'], r['logged_reorder']
    if a is None:
        return 'keine Neuberechnung'
    res = r['result']
    hi = (res == 'LOSS')            # Niederlage trotz hoher Prognose
    notes = []
    if lg is not None and abs(a - lg) >= 10:
        notes.append(f'Live-Wert instabil (live {lg:.0f}, Replay {a:.0f})')
    if hi:
        if a >= 95:
            notes.append('TUO glaubt auch mit 20000 Spielen an den Sieg')
        elif a < 80:
            notes.append(f'Replay deutlich niedriger ({a:.0f})')
        if b is not None and a - b >= 15:
            notes.append(f'unbekannte Gegnerkarten erklaeren es (mit Ergaenzung {b:.0f})')
    else:
        if a <= 5:
            notes.append('TUO glaubt auch mit 20000 Spielen an die Niederlage')
        elif a > 20:
            notes.append(f'Replay deutlich hoeher ({a:.0f})')
        if b is not None and b - a >= 15:
            notes.append(f'Ergaenzung hebt auf {b:.0f}')
    return '; '.join(notes) if notes else 'unauffaellig'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('logs', nargs='*', help='JSON-Logs, Ordner oder Glob; Standard: <tuo-Ordner>\\data\\combatlog\\suspicious')
    ap.add_argument('--tuo', default='tuo.exe', help='Pfad zu tuo.exe (Standard: tuo.exe im aktuellen Ordner)')
    ap.add_argument('--n', type=int, default=20000, help='Spiele je Neuberechnung (reorder N), Standard 20000')
    ap.add_argument('--threads', type=int, default=8, help='TUO-Threads je Lauf (-t)')
    ap.add_argument('--workers', type=int, default=2, help='parallele TUO-Prozesse')
    ap.add_argument('--flex-iter', type=int, default=0, help='Variante C: flexible-iter (Live: 50), 0 = aus')
    ap.add_argument('--all-turns', action='store_true', help='alle Zuege statt nur der auffaelligen')
    ap.add_argument('--max-per-log', type=int, default=3, help='hoechstens N auffaellige Zuege je Log (0 = alle), Standard 3')
    ap.add_argument('--hi-loss', type=float, default=95.0, help='Niederlage: Anzeige >= X gilt als auffaellig')
    ap.add_argument('--lo-win', type=float, default=5.0, help='Sieg: Anzeige <= X gilt als auffaellig')
    ap.add_argument('--timeout', type=int, default=1800, help='Sekunden je Lauf')
    ap.add_argument('--limit', type=int, default=0, help='nur die ersten N Logs')
    ap.add_argument('--out', default='replay_check', help='Praefix der Ausgabedateien')
    ap.add_argument('--resume', action='store_true', help='bereits gerechnete Zuege aus <out>.csv uebernehmen')
    o = ap.parse_args()

    exe = os.path.abspath(o.tuo)
    if not os.path.isfile(exe):
        sys.exit(f'tuo.exe nicht gefunden: {exe}')
    cwd = os.path.dirname(exe)
    if not o.logs:
        o.logs = [os.path.join(cwd, 'data', 'combatlog', 'suspicious')]
    files = collect_logs(o.logs)
    if o.limit:
        files = files[:o.limit]

    csv_path, txt_path = o.out + '.csv', o.out + '.txt'
    rows, done_keys = [], set()
    if o.resume and os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as fh:
            for r in csv.DictReader(fh, delimiter=';'):
                for k in ('shown', 'logged_reorder', 'a_replay', 'b_completed', 'c_flex'):
                    r[k] = fnum(r.get(k))
                r['turn'] = int(r['turn'])
                rows.append(r)
        done_keys = {(r['log'], r['turn']) for r in rows}
        print(f'Wiederaufnahme: {len(rows)} Zuege aus {csv_path}', flush=True)
        fh_csv = open(csv_path, 'a', newline='', encoding='utf-8')
        writer = csv.DictWriter(fh_csv, fieldnames=COLS, extrasaction='ignore', delimiter=';')
    else:
        fh_csv = open(csv_path, 'w', newline='', encoding='utf-8')
        writer = csv.DictWriter(fh_csv, fieldnames=COLS, extrasaction='ignore', delimiter=';')
        writer.writeheader()
        fh_csv.flush()

    jobs = []
    for f in files:
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print('uebersprungen', f, e)
            continue
        act = actual_enemy_cards(d.get('turns', []))
        for t in pick_turns(d, o.all_turns, o.max_per_log, o.lo_win, o.hi_loss):
            if (os.path.basename(f), t['turn']) in done_keys:
                continue
            jobs.append((f, d, t, act))
    print(f'{len(files)} Logs, {len(jobs)} Zuege, reorder {o.n}, threads {o.threads}, workers {o.workers}', flush=True)

    lock = threading.Lock()
    done = [0]
    t0 = time.time()

    def work(job):
        f, d, t, act = job
        try:
            args = parse_cmd(t['tuo_cmd'])
        except Exception:
            args = None
        fc = t.get('forecast') or {}
        row = dict(log=os.path.basename(f), mode=d.get('mode'), result=d.get('result'), enemy=d.get('enemy_name'),
                   script=d.get('script_version'), turn=t['turn'], shown=t.get('tuo_win_pct'),
                   logged_reorder=fc.get('reorder'), incomplete=bool(t.get('enemy_deck_known')),
                   a_replay=None, b_completed=None, c_flex=None, added_cards='', ok=False)
        if args and len(args) > 1:
            a = build_args(args, o.n, o.threads)
            if a:
                row['a_replay'] = run_tuo(exe, cwd, a, o.timeout)
                row['ok'] = row['a_replay'] is not None
                deck2, add = complete_enemy_deck(args[1], act)
                # nur sinnvoll, wenn das zweite Argument wirklich das Gegnerdeck ist
                if add and d.get('enemy_deck') and args[1].split(',')[0].strip()[:8] == d['enemy_deck'].split(',')[0].strip()[:8]:
                    row['added_cards'] = ', '.join(add)
                    row['b_completed'] = run_tuo(exe, cwd, build_args(args, o.n, o.threads, enemy_deck=deck2), o.timeout)
                if o.flex_iter:
                    row['c_flex'] = run_tuo(exe, cwd, build_args(args, o.n, o.threads, flex_iter=o.flex_iter), o.timeout)
        with lock:
            rows.append(row)
            writer.writerow(row)
            fh_csv.flush()
            done[0] += 1
            print(f'  {done[0]}/{len(jobs)}  ({time.time() - t0:.0f}s)  {row["log"][:44]} T{row["turn"]}: '
                  f'live {row["logged_reorder"]} -> Replay {row["a_replay"]}'
                  + (f' / ergaenzt {row["b_completed"]}' if row['b_completed'] is not None else ''), flush=True)

    with cf.ThreadPoolExecutor(max_workers=max(1, o.workers)) as ex:
        list(ex.map(work, jobs))
    fh_csv.close()
    rows.sort(key=lambda r: (r['log'], int(r['turn'])))

    ok = [r for r in rows if r['a_replay'] is not None]
    L = []
    L.append(f'Zuege neu gerechnet: {len(ok)} von {len(rows)} | reorder {o.n} (Live: 5000) | {len({r["log"] for r in rows})} Logs')
    for res, lab in (('LOSS', 'Niederlagen mit hoher Anzeige'), ('WIN', 'Siege mit niedriger Anzeige')):
        s = [r for r in ok if r['result'] == res]
        if not s:
            continue
        lg = [r for r in s if r['logged_reorder'] is not None]
        L.append('')
        L.append(f'== {lab}: {len(s)} Zuege ==')
        if lg:
            dev = [abs(r['a_replay'] - r['logged_reorder']) for r in lg]
            L.append(f'  Replay gegen geloggten reorder-Wert: mittlere Abweichung {sum(dev) / len(dev):.1f} Punkte, '
                     f'>= 10 Punkte: {sum(1 for x in dev if x >= 10)} von {len(dev)}')
        if res == 'LOSS':
            L.append(f'  Replay bleibt >= 95 %: {sum(1 for r in s if r["a_replay"] >= 95)} von {len(s)}  '
                     f'(TUO glaubt auch mit mehr Spielen an den Sieg)')
        else:
            L.append(f'  Replay bleibt <= 5 %: {sum(1 for r in s if r["a_replay"] <= 5)} von {len(s)}')
        for flag, nm in ((True, 'Gegnerdeck teilweise bekannt'), (False, 'Gegnerdeck vollstaendig/unbekannt')):
            g = [r for r in s if bool(r['incomplete']) == flag]
            if not g:
                continue
            line = f'  {nm}: {len(g)} Zuege, mittlerer Replay {sum(r["a_replay"] for r in g) / len(g):.1f} %'
            gb = [r for r in g if r['b_completed'] is not None]
            if gb:
                line += (f' | mit ergaenztem Deck ({len(gb)} Zuege): {sum(r["a_replay"] for r in gb) / len(gb):.1f} % -> '
                         f'{sum(r["b_completed"] for r in gb) / len(gb):.1f} %, Rueckgang >= 15: '
                         f'{sum(1 for r in gb if r["a_replay"] - r["b_completed"] >= 15)}')
            L.append(line)
        gc = [r for r in s if r['c_flex'] is not None]
        if gc:
            L.append(f'  Variante C (flexible-iter {o.flex_iter}): mittlerer Replay {sum(r["a_replay"] for r in gc) / len(gc):.1f} % -> '
                     f'{sum(r["c_flex"] for r in gc) / len(gc):.1f} %')
    L.append('')
    L.append('Je Zug: Log | Zug | angezeigt | live reorder | Replay | ergaenzt | Bewertung')
    for r in rows:
        f1 = lambda x: '-' if x is None else f'{x:.1f}'
        L.append(f'  {r["log"][:52]:52s} T{r["turn"]:<2} {r["result"]:4s} {f1(r["shown"]):>6} {f1(r["logged_reorder"]):>6} '
                 f'{f1(r["a_replay"]):>6} {f1(r["b_completed"]):>6}  {verdict(r)}'
                 + (f'  [+ {r["added_cards"]}]' if r.get('added_cards') else ''))
    with open(txt_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print(f'\nGeschrieben: {csv_path}, {txt_path}')


if __name__ == '__main__':
    main()

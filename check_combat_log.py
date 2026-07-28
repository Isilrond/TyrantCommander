"""
check_combat_log.py  —  v2
Validates combat log JSON files: checks whether api_card_states match
the hand-state / enemy:hand-state values passed to TUO.

Requires logs produced by TyrantAPICommander v4.9+
(api_card_states = pre-sim, card_name_map stored per turn).

Usage:
    python check_combat_log.py <logfile.json> [logfile2.json ...]
    python check_combat_log.py          (auto-scans combatlog/ folder)
"""

import json, re, sys, os
from collections import defaultdict

SKIP_FLAGS = {'poisoner', 'h', 'mimic_skill', 'corroder',
              # Evolved-skill init pairs (set at deck-init time, not runtime state)
              'pierce_evolved_into_rupture', 'weaken_evolved_into_sunder',
              'absorb_evolved_into_evade', 'leech_evolved_into_refresh',
              'payback_evolved_into_revenge', 'poison_evolved_into_venom',
              'siege_evolved_into_besiege', 'siege_evolved_into_mortar',
              'swipe_evolved_into_drain'}
INT_FLAGS  = {
    'h', 'perm_max_health', 'attack_boost', 'avenge_attack',
    'protect', 'absorb', 'enfeeble', 'inhibited', 'stasis', 'poison',
    'disease', 'corrosive', 'corrosion', 'subdue', 'sabotage', 'mark',
    'jam_countdown', 'flurry_countdown', 'add_skill_counter',
    'add_skill_berserk', 'entrap', 'tribute',
    'enhance_subdue', 'enhance_scavenge', 'enhance_allegiance',
    'enhance_armor', 'enhance_armored', 'enhance_avenge', 'enhance_barrier',
    'enhance_berserk', 'enhance_besiege', 'enhance_coalition', 'enhance_corrosive',
    'enhance_counter', 'enhance_disease', 'enhance_drain', 'enhance_evade',
    'enhance_fortify', 'enhance_hunt', 'enhance_inhibit', 'enhance_leech',
    'enhance_legion', 'enhance_mark', 'enhance_poison', 'enhance_stasis',
    'enhance_swipe', 'enhance_tribute', 'enhance_venom',
}
BOOL_FLAGS = {'jammed', 'overloaded', 'sunder', 'enrage'}


def parse_hand_state_str(hs_str):
    """Parse TUO hand-state string → list of (name, {flag: val})."""
    result = []
    if not hs_str:
        return result
    for entry in hs_str.split(','):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(':')
        name = parts[0].strip()
        flags = {}
        for part in parts[1:]:
            if '=' in part:
                k, v = part.split('=', 1)
                try:
                    flags[k.strip()] = int(v.strip())
                except ValueError:
                    flags[k.strip()] = v.strip()
        result.append((name, flags))
    return result


def build_expected(acs, uid_range, name_map):
    """
    Build expected hand-state list from api_card_states + name_map.
    Returns ordered list of (card_name, {flag: val}) for alive cards with state.
    name_map: uid_str -> TUO_card_name
    """
    result = []
    for uid_i in uid_range:
        if uid_i < 0:
            continue  # skip UID -1 (commander mimic state)
        uid = str(uid_i)
        flags = acs.get(uid)
        if not isinstance(flags, dict):
            continue
        h = flags.get('h')
        if h is not None and int(h) <= 0:
            continue  # dead
        name = name_map.get(uid)
        if not name:
            continue  # not in card_name_map → can't verify

        tuo_flags = {}
        if h is not None and int(h) > 0:
            tuo_flags['h'] = int(h)
        for flag, val in flags.items():
            if flag in SKIP_FLAGS:
                continue
            try:
                ival = int(val)
            except (TypeError, ValueError):
                continue
            if ival == 0:
                continue
            if flag in BOOL_FLAGS:
                tuo_flags[flag] = 1
            elif flag in INT_FLAGS and flag != 'h':
                tuo_flags[flag] = ival

        if tuo_flags:
            result.append((name, tuo_flags))
    return result


def compare_hs(expected_list, actual_list, side, issues):
    """Compare expected vs actual hand-state lists."""
    # Group actual by base name (strip #N suffix)
    actual_by_base = defaultdict(list)
    for name, flags in actual_list:
        actual_by_base[name.split('#')[0]].append((name, flags))

    for exp_name, exp_flags in expected_list:
        base = exp_name.split('#')[0]
        if base not in actual_by_base or not actual_by_base[base]:
            issues.append(f"  {side} MISSING card '{exp_name}'  expected={exp_flags}")
            continue
        _, act_flags = actual_by_base[base].pop(0)
        for flag, exp_val in exp_flags.items():
            if flag not in act_flags:
                issues.append(f"  {side} MISSING flag '{flag}'={exp_val} on {exp_name}")
            elif act_flags[flag] != exp_val:
                issues.append(f"  {side} WRONG '{flag}': expected={exp_val} actual={act_flags[flag]} on {exp_name}")
        for flag, act_val in act_flags.items():
            if flag not in exp_flags:
                issues.append(f"  {side} EXTRA flag '{flag}'={act_val} on {exp_name} (not in api_card_states)")

    # Extra cards in actual not matched to expected
    for base, remaining in actual_by_base.items():
        for name, _ in remaining:
            issues.append(f"  {side} EXTRA card '{name}' (dead or wrong UID range)")


def detect_ranges(tuo_cmd, acs, name_map=None):
    # Correct UID schema (empirically verified from GW combat logs):
    # own dominion ALWAYS = UID 51, enemy dominion ALWAYS = UID 151
    # Forts occupy first slots in 52-range (enemy) and 152-range (own):
    #   enemy forts: 52..52+n_enemy_forts-1  own summons: 52+n_enemy_forts..100
    #   own forts:  152..152+n_own_forts-1   enemy summons: 152+n_own_forts..200
    import re as _re

    def _count_forts(fort_arg):
        """Count number of forts from yfort/efort argument string."""
        if not fort_arg:
            return 0
        return len([f for f in fort_arg.split(',') if f.strip()])

    def _own_is_101(tuo_cmd, acs, name_map):
        if name_map:
            hm = _re.search(r"(?<!enemy:)hand\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
            hand_str = next((g for g in (hm.groups() if hm else []) if g), '') or ''
            if hand_str:
                hand_names = {n.strip().rsplit('-', 1)[0].strip().lower()
                              for n in hand_str.split(',')}
                found_in_1_10 = False
                for uid, nm in name_map.items():
                    if not uid.isdigit():
                        continue
                    uid_i = int(uid)
                    if not ((1 <= uid_i <= 10) or (101 <= uid_i <= 110)):
                        continue
                    base = nm.rsplit('-', 1)[0].strip().lower() if nm else ''
                    if base in hand_names:
                        if 101 <= uid_i <= 110:
                            return True   # definitive: own card in 101-110
                        else:
                            found_in_1_10 = True  # ambiguous: same card plays both sides
                # Only found match in enemy assault range → try yfort before deciding
                if not found_in_1_10:
                    pass  # no assault match at all → fall through to yfort
            # Fallback: check yfort card UIDs
            yf = _re.search(r"yfort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
            yfort_str = next((g for g in (yf.groups() if yf else []) if g), '') or ''
            if yfort_str:
                yfort_names = {n.strip().rsplit('-', 1)[0].strip().lower()
                               for n in yfort_str.split(',')}
                for uid, nm in name_map.items():
                    base = nm.rsplit('-', 1)[0].strip().lower() if nm else ''
                    if base in yfort_names and uid.isdigit():
                        return int(uid) >= 152
        return any(100 < int(k) < 111 and isinstance(v, dict) and v.get('h', 0) > 0
                   for k, v in acs.items() if k.isdigit())

    cmd_lower = tuo_cmd.lower()
    if ' brawl ' in cmd_lower or ' gw ' in cmd_lower:
        mode = 'brawl' if ' brawl ' in cmd_lower else 'gw'
        own_101 = _own_is_101(tuo_cmd, acs, name_map)
        # Parse fort counts
        yf_m = _re.search(r"yfort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        ef_m = _re.search(r"efort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        yfort_str = next((g for g in (yf_m.groups() if yf_m else []) if g), '') or ''
        efort_str = next((g for g in (ef_m.groups() if ef_m else []) if g), '') or ''
        n_own_forts   = _count_forts(yfort_str)
        n_enemy_forts = _count_forts(efort_str)
        if own_101:
            # own=101-110: own forts=152..152+n_own-1, own summons=52+n_enemy..100
            return (list(range(101, 111)) + [51] +
                    list(range(52 + n_enemy_forts, 100)) +
                    list(range(152, 152 + n_own_forts)),
                    list(range(1, 11)) + [151] +
                    list(range(52, 52 + n_enemy_forts)) +
                    list(range(152 + n_own_forts, 200)), mode)
        else:
            return (list(range(1, 11)) + [51] +
                    list(range(152 + n_enemy_forts, 200)) +
                    list(range(52, 52 + n_own_forts)),
                    list(range(101, 111)) + [151] +
                    list(range(152, 152 + n_enemy_forts)) +
                    list(range(52 + n_own_forts, 100)), mode)
    else:
        # Arena: no forts, own=1-10, dominion=51, summons start at 52
        return (list(range(1, 11))   + [51] + list(range(52, 100)),
                list(range(101, 111)) + [151] + list(range(152, 200)), 'arena')


def check_log(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0, 0

    turns = data.get('turns', [])
    if not turns:
        return 0, 0

    has_name_map = any('card_name_map' in t for t in turns)

    print(f"\n{'='*70}")
    print(f"  {os.path.basename(path)}")
    print(f"  Mode: {data.get('mode','?')}  Enemy: {data.get('enemy_name','?')}  Result: {data.get('result','?')}")
    if not has_name_map:
        print(f"  ⚠ No card_name_map — log predates this fix, name resolution limited")
    print(f"{'='*70}")

    total_issues = 0
    turns_checked = 0

    for t in turns:
        turn_num   = t.get('turn', '?')
        tuo_cmd    = t.get('tuo_cmd', '')
        acs        = t.get('api_card_states', {})
        win_pct    = t.get('tuo_win_pct')
        name_map   = t.get('card_name_map', {})

        if not tuo_cmd:
            continue
        # Hand-state may use single OR double quotes (double quotes are used
        # when a card name contains an apostrophe, e.g. "Halcyon's APC").
        # The own hand-state regex must NOT match inside "enemy:hand-state ..."
        # (which also contains the substring "hand-state") - use a negative
        # lookbehind for "enemy:".
        # hand-state may be: quoted with ' or " (when it contains commas/spaces/
        # apostrophes), OR completely unquoted when it's a single token with no
        # special chars (e.g. "enemy:hand-state Lavawyrm:stasis=14").
        hs_m  = re.search(r"(?<!enemy:)hand-state\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        ehs_m = re.search(r"enemy:hand-state\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        if not hs_m and not ehs_m:
            continue

        turns_checked += 1
        hs_str  = next((g for g in hs_m.groups()  if g is not None), '') if hs_m  else ''
        ehs_str = next((g for g in ehs_m.groups() if g is not None), '') if ehs_m else ''
        actual_hs  = parse_hand_state_str(hs_str)
        actual_ehs = parse_hand_state_str(ehs_str)

        own_range, enemy_range, mode = detect_ranges(tuo_cmd, acs, name_map)

        exp_own   = build_expected(acs, own_range,   name_map)
        exp_enemy = build_expected(acs, enemy_range, name_map)

        turn_issues = []
        compare_hs(exp_own,   actual_hs,  'OWN',   turn_issues)
        compare_hs(exp_enemy, actual_ehs, 'ENEMY', turn_issues)

        # Unknown flags
        unknown = {f for flags in acs.values() if isinstance(flags, dict)
                   for f in flags
                   if f not in INT_FLAGS and f not in BOOL_FLAGS and f not in SKIP_FLAGS}
        if unknown:
            turn_issues.append(f"  UNKNOWN flags: {sorted(unknown)}")

        if turn_issues:
            total_issues += len(turn_issues)
            print(f"\n  Turn {turn_num} | win%={win_pct} | mode={mode}")
            for issue in turn_issues:
                print(issue)
        else:
            print(f"  Turn {turn_num} | win%={win_pct} | ✓ OK")

    summary = "✓ CLEAN" if total_issues == 0 else f"✗ {total_issues} issue(s)"
    print(f"\n  {summary} — {turns_checked} turns checked")
    return turns_checked, total_issues


def main():
    files = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                files.append(arg)
            elif os.path.isdir(arg):
                for root, _, fnames in os.walk(arg):
                    for fn in fnames:
                        if fn.endswith('.json'):
                            files.append(os.path.join(root, fn))
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for base in (script_dir, os.path.join(script_dir, 'data')):
            cdir = os.path.join(base, 'combatlog')
            if os.path.isdir(cdir):
                for root, _, fnames in os.walk(cdir):
                    for fn in sorted(fnames):
                        if fn.endswith('.json'):
                            files.append(os.path.join(root, fn))
    if not files:
        print("Usage: python check_combat_log.py <logfile.json> [...]")
        sys.exit(1)

    # ── Issues folder setup ──────────────────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    issues_dir = os.path.join(script_dir, 'Issues')
    if os.path.isdir(issues_dir):
        import shutil as _shutil
        _shutil.rmtree(issues_dir)
    os.makedirs(issues_dir, exist_ok=True)
    issues_log_path = os.path.join(issues_dir, '_issues_summary.txt')
    issues_log_lines = []

    total_t = total_i = 0
    affected_files = []

    for path in sorted(files):
        # Capture output from check_log
        import io as _io
        old_stdout = sys.stdout
        sys.stdout = _io.StringIO()
        t, i = check_log(path)
        captured = sys.stdout.getvalue()
        sys.stdout = old_stdout
        print(captured, end='')

        total_t += t
        total_i += i

        if i > 0:
            affected_files.append(path)
            issues_log_lines.append(captured)
            # Copy affected JSON to Issues folder
            import shutil as _shutil
            dst_name = os.path.basename(path)
            dst = os.path.join(issues_dir, dst_name)
            # Avoid name collision
            if os.path.exists(dst):
                base, ext = os.path.splitext(dst_name)
                idx = 1
                while os.path.exists(os.path.join(issues_dir, f"{base}_{idx}{ext}")):
                    idx += 1
                dst = os.path.join(issues_dir, f"{base}_{idx}{ext}")
            _shutil.copy2(path, dst)

    print(f"\n{'='*70}")
    print(f"  TOTAL: {len(files)} log(s)  {total_t} turns  ", end='')
    print("✓ All clean" if total_i == 0 else f"✗ {total_i} issue(s)")
    print(f"{'='*70}")

    # ── Write issues log ─────────────────────────────────────────────────
    if affected_files:
        with open(issues_log_path, 'w', encoding='utf-8') as _f:
            _f.write(f"check_combat_log — Issues Summary\n")
            _f.write(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            _f.write(f"Affected files: {len(affected_files)} / {len(files)}\n")
            _f.write(f"Total issues: {total_i}\n")
            _f.write("=" * 70 + "\n\n")
            for block in issues_log_lines:
                _f.write(block)
                _f.write("\n")
        print(f"\n  📁 Issues folder: {issues_dir}")
        print(f"     {len(affected_files)} affected log(s) copied + _issues_summary.txt written")
    else:
        # Remove empty Issues folder if no issues found
        import shutil as _shutil
        _shutil.rmtree(issues_dir)

    input("\nEnter zum Schließen...")


if __name__ == '__main__':
    main()

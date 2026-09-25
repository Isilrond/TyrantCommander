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
    'enhance_berserk', 'enhance_besiege', 'enhance_coalition', 'enhance_corrosive', 'enhance_sabotage',
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
    # Commander UIDs (50/150) store their states under internal API UIDs (-1/-2)
    commander_extra = {}
    for internal_uid, target_uid in [('-1', 50), ('-2', 150)]:
        extra = acs.get(internal_uid)
        if isinstance(extra, dict):
            commander_extra[target_uid] = extra

    for uid_i in uid_range:
        if uid_i < 0:
            continue
        uid = str(uid_i)
        flags = dict(acs.get(uid) or {})
        # Merge commander internal states (-1/-2) into commander UIDs (50/150)
        if uid_i in commander_extra:
            flags.update(commander_extra[uid_i])
        if not flags:
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
            # mimic_skill: nested dict → extract derived skill (x takes priority over n)
            # Handle BEFORE SKIP_FLAGS check since mimic_skill is in SKIP_FLAGS for UNKNOWN suppression
            if flag == 'mimic_skill' and isinstance(val, dict):
                skill_id = val.get('id', '')
                skill_val = val.get('x') or val.get('n') or '1'
                # Skip if real state flag with same name already exists (different meaning)
                # Skip skills with non-standard triggers (e.g. "attacked") - can't be represented in hand-state
                if skill_id and skill_id not in tuo_flags:
                    try:
                        tuo_flags[skill_id] = int(skill_val)
                    except (ValueError, TypeError):
                        pass
                continue
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


def detect_ranges(tuo_cmd, acs, name_map=None, cached_own_101=None):
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

    def _own_is_101(tuo_cmd, acs, name_map, cache=None):
        # If we already determined own_101 for this battle, reuse it
        if cache is not None:
            return cache

        # Priority check: enemy:hand card at uid 1-10 → own is 101-110
        # Must run before deck-name matching (same card may appear in both decks)
        if name_map:
            ehm = _re.search(r"enemy:hand\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
            ehand_str = next((g for g in (ehm.groups() if ehm else []) if g), '') or ''
            if ehand_str:
                ehand_names = {n.strip().rsplit('-', 1)[0].strip().lower()
                               for n in ehand_str.split(',')}
                for uid, nm in name_map.items():
                    if not uid.isdigit():
                        continue
                    uid_i = int(uid)
                    if not (1 <= uid_i <= 10):
                        continue
                    base = nm.rsplit('-', 1)[0].strip().lower() if nm else ''
                    if base in ehand_names:
                        return True  # definitive: enemy:hand card at uid 1-10

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
                if not found_in_1_10:
                    pass  # no assault match at all → fall through

            # Fallback A: match own AND enemy deck against name_map assault UIDs
            # Use first arg (own deck) and second arg (enemy deck) from TUO command
            deck_m = _re.match(r'''\S+\s+(?:'([^']*)'|"([^"]*)")\s+(?:'([^']*)'|"([^"]*)")''', tuo_cmd)
            if deck_m and name_map:
                own_str   = next((g for g in deck_m.groups()[:2] if g is not None), '') or ''
                enemy_str = next((g for g in deck_m.groups()[2:] if g is not None), '') or ''
                own_names   = {n.strip().rsplit('-', 1)[0].strip().lower() for n in own_str.split(',')}
                enemy_names = {n.strip().rsplit('-', 1)[0].strip().lower() for n in enemy_str.split(',')}
                score_101 = score_1 = 0
                for uid, nm in name_map.items():
                    if not uid.isdigit():
                        continue
                    uid_i = int(uid)
                    if not ((1 <= uid_i <= 10) or (101 <= uid_i <= 110)):
                        continue
                    base = nm.rsplit('-', 1)[0].strip().lower() if nm else ''
                    if 101 <= uid_i <= 110:
                        if base in own_names:   score_101 += 2  # own card in 101-110 → strong signal
                        if base in enemy_names: score_1   += 2  # enemy card in 101-110 → signals own=1-10
                    else:  # 1-10
                        if base in enemy_names: score_101 += 2  # enemy card in 1-10 → signals own=101-110
                        if base in own_names:   score_1   += 2  # own card in 1-10 → signals own=1-10
                if score_101 > score_1:
                    return True
                if score_1 > score_101:
                    return False

            # Fallback B: check yfort card UIDs (GW only)
            yf = _re.search(r"yfort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
            yfort_str = next((g for g in (yf.groups() if yf else []) if g), '') or ''
            if yfort_str:
                yfort_names = {n.strip().rsplit('-', 1)[0].strip().lower()
                               for n in yfort_str.split(',')}
                for uid, nm in name_map.items():
                    base = nm.rsplit('-', 1)[0].strip().lower() if nm else ''
                    if base in yfort_names and uid.isdigit():
                        return int(uid) >= 152

        # Fallback D: h>0 heuristic (last resort, no cache available)
        result = any(100 < int(k) < 111 and isinstance(v, dict) and v.get('h', 0) > 0
                     for k, v in acs.items() if k.isdigit())
        return result

    cmd_lower = tuo_cmd.lower()
    if ' brawl ' in cmd_lower or ' gw ' in cmd_lower:
        mode = 'brawl' if ' brawl ' in cmd_lower else 'gw'
        # Parse fort counts first
        yf_m = _re.search(r"yfort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        ef_m = _re.search(r"efort\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", tuo_cmd)
        yfort_str = next((g for g in (yf_m.groups() if yf_m else []) if g), '') or ''
        efort_str = next((g for g in (ef_m.groups() if ef_m else []) if g), '') or ''
        n_own_forts   = _count_forts(yfort_str)
        n_enemy_forts = _count_forts(efort_str)
        # Brawl never has forts. Summons use fort slots directly:
        # own_101=True: own assault=101-110, own summons=152+, enemy assault=1-10, enemy summons=52+
        # own_101=False: own assault=1-10, own summons=52+, enemy assault=101-110, enemy summons=152+
        if mode == 'brawl':
            own_101 = _own_is_101(tuo_cmd, acs, name_map, cached_own_101)
            if own_101:
                return (list(range(101, 111)) + [50] + [51] + list(range(152, 200)),
                        list(range(1, 11)) + [150] + [151] + list(range(52, 100)), mode)
            else:
                return (list(range(1, 11)) + [50] + [51] + list(range(52, 100)),
                        list(range(101, 111)) + [150] + [151] + list(range(152, 200)), mode)
        own_101 = _own_is_101(tuo_cmd, acs, name_map, cached_own_101)
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
        # Arena: no forts, own=1-10, commander=50, dominion=51, summons start at 52
        return (list(range(1, 11))   + [50] + [51] + list(range(52, 100)),
                list(range(101, 111)) + [150] + [151] + list(range(152, 200)), 'arena')


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
    cached_own_101 = None  # cached per-battle to avoid detection flip-flop

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

        own_range, enemy_range, mode = detect_ranges(tuo_cmd, acs, name_map, cached_own_101)
        # Cache first reliable detection within a battle
        if mode in ('brawl', 'gw') and cached_own_101 is None:
            cached_own_101 = (own_range[0] == 101)  # True if own assault starts at 101

        # For Brawl: summon UIDs (52-99 and 152-199) are assigned sequentially regardless
        # of which side summoned the card. Use state-matching against hand-states to assign
        # each UID to the correct side.
        if mode == 'brawl' and name_map:
            SUMMON_UIDS = sorted(set(range(52, 100)) | set(range(152, 200)))

            # Build state dict from hand-state entries for matching
            def _hs_to_flag_set(flags_dict):
                return frozenset((k, v) for k, v in flags_dict.items()
                                 if k not in ('h',) or v > 0)

            def _acs_to_flag_set(uid_flags):
                """Build flag set from api_card_states for matching — includes 'h' for summon disambiguation."""
                out = {}
                for k, v in uid_flags.items():
                    if k in SKIP_FLAGS and k != 'h':
                        # Extract mimic_skill as derived flag for matching
                        if k == 'mimic_skill' and isinstance(v, dict):
                            skill_id = v.get('id', '')
                            skill_val = v.get('x') or v.get('n') or '1'
                            if skill_id and not v.get('trigger'):
                                try:
                                    out[skill_id] = int(skill_val)
                                except (TypeError, ValueError):
                                    pass
                        continue
                    try:
                        iv = int(v)
                    except (TypeError, ValueError):
                        continue
                    if iv != 0:
                        out[k] = iv
                return frozenset(out.items())

            def _match_score(uid_flags_set, hs_flags_dict):
                """Score UID match against hand-state entry.
                +1 per matching (key,value), -2 per same-key mismatch,
                -1 per extra flag in UID not present in hand-state (prefers exact fits)."""
                hs_set = frozenset((k, int(v)) for k, v in hs_flags_dict.items()
                                   if isinstance(v, (int, float)) and int(v) != 0)
                uid_dict = dict(uid_flags_set)
                hs_dict  = dict(hs_set)
                matches  = len(uid_flags_set & hs_set)
                # Penalise same-key value mismatches heavily
                penalty  = sum(2 for k in uid_dict if k in hs_dict and uid_dict[k] != hs_dict[k])
                # Penalise extra flags in UID not in hand-state (prefer minimal/exact state)
                penalty += sum(1 for k in uid_dict if k not in hs_dict)
                return matches - penalty

            # Build lists of hand-state entries per card name per side
            own_hs_by_name   = {}
            enemy_hs_by_name = {}
            for name, flags in actual_hs:
                base = name.split('#')[0].lower()
                own_hs_by_name.setdefault(base, []).append(dict(flags))
            for name, flags in actual_ehs:
                base = name.split('#')[0].lower()
                enemy_hs_by_name.setdefault(base, []).append(dict(flags))

            # Collect all alive summon UIDs with name and flag_set
            summon_candidates = {}  # uid_i → (name_base, flag_set, uid_flags_raw)
            for uid_i in SUMMON_UIDS:
                uid = str(uid_i)
                nm = name_map.get(uid)
                if not nm:
                    continue
                base = nm.split('#')[0].lower()
                uid_flags = acs.get(uid)
                if not isinstance(uid_flags, dict):
                    continue
                h = uid_flags.get('h')
                if h is not None and int(h) <= 0:
                    continue  # dead
                summon_candidates[uid_i] = (base, _acs_to_flag_set(uid_flags))

            # Build own/enemy entries WITH their index (to preserve hand-state order)
            own_hs_entries   = [(e[0].split('#')[0].lower(), dict(e[1])) for e in actual_hs]
            enemy_hs_entries = [(e[0].split('#')[0].lower(), dict(e[1])) for e in actual_ehs]

            assigned = set()
            own_summon_range   = []
            enemy_summon_range = []

            def _best_uid(entries_for_name, flag_set):
                """Find best unassigned UID matching this hand-state entry."""
                best_uid_i = best_score = None
                for uid_i, (base, ufs) in summon_candidates.items():
                    if uid_i in assigned or base != entries_for_name:
                        continue
                    score = _match_score(ufs, {})  # placeholder
                    # compute proper score
                    hs_set = frozenset((k, v) for k, v in {}.items())
                    s = _match_score(flag_set, {})
                    # Use direct computation
                    hs_items = frozenset((k, int(v)) for k, v in {}.items()
                                        if isinstance(v, (int, float)) and int(v) != 0)
                    match_count = len(flag_set & hs_items)
                    uid_d  = dict(flag_set)
                    hs_d   = {}
                    pen    = sum(2 for k in uid_d if k in hs_d and uid_d[k] != hs_d[k])
                    s      = match_count - pen
                    if best_score is None or s > best_score:
                        best_score = s
                        best_uid_i = uid_i
                return best_uid_i

            # Process in hand-state order: match each entry to the best unassigned UID
            def _assign_entries(hs_entries, result_list, skip_counts=None):
                _skips = dict(skip_counts or {})
                for base, entry_flags in hs_entries:
                    # Skip if already covered by a non-summon UID (e.g. dominion with same name)
                    if _skips.get(base, 0) > 0:
                        _skips[base] -= 1
                        continue
                    best = None
                    best_score = None
                    for uid_i, (cbase, cflag_set) in summon_candidates.items():
                        if uid_i in assigned or cbase != base:
                            continue
                        s = _match_score(cflag_set, entry_flags)
                        if best_score is None or s > best_score:
                            best_score = s
                            best = uid_i
                    if best is not None:
                        assigned.add(best)
                        result_list.append(best)

            # Count cards already covered by non-summon UIDs (commanders, dominions, assaults)
            # Only count alive UIDs (h != 0) — dead cards should not suppress summon assignment
            from collections import Counter as _Counter
            _dom_own_counts   = _Counter()
            _dom_enemy_counts = _Counter()
            for _u in own_range:
                if _u < 52 or (100 <= _u < 152):
                    _uid_flags = acs.get(str(_u), {})
                    if isinstance(_uid_flags, dict) and _uid_flags.get('h', 1) == 0:
                        continue  # dead card — don't count as covered
                    _nm = name_map.get(str(_u), '').rsplit('-', 1)[0].strip().lower()
                    if _nm: _dom_own_counts[_nm] += 1
            for _u in enemy_range:
                if _u < 52 or (100 <= _u < 152):
                    _uid_flags = acs.get(str(_u), {})
                    if isinstance(_uid_flags, dict) and _uid_flags.get('h', 1) == 0:
                        continue  # dead card — don't count as covered
                    _nm = name_map.get(str(_u), '').rsplit('-', 1)[0].strip().lower()
                    if _nm: _dom_enemy_counts[_nm] += 1

            _assign_entries(own_hs_entries,   own_summon_range,   _dom_own_counts)
            _assign_entries(enemy_hs_entries, enemy_summon_range, _dom_enemy_counts)

            assault_dom_own   = [u for u in own_range   if u < 52 or (100 <= u < 152)]
            assault_dom_enemy = [u for u in enemy_range if u < 52 or (100 <= u < 152)]
            own_range   = assault_dom_own   + own_summon_range
            enemy_range = assault_dom_enemy + enemy_summon_range

        exp_own   = build_expected(acs, own_range,   name_map)
        exp_enemy = build_expected(acs, enemy_range, name_map)

        # For Brawl: also include stateless summons that appear in hand-state
        # (build_expected skips cards with no flags, but they can still be in actual_hs)
        if mode == 'brawl' and name_map:
            exp_own_names   = {e[0].split('#')[0].lower() for e in exp_own}
            exp_enemy_names = {e[0].split('#')[0].lower() for e in exp_enemy}
            for name, flags in actual_hs:
                base = name.split('#')[0].lower()
                if not flags and base not in exp_own_names:
                    # Check if this card is in own_summon_range
                    for uid_i in own_summon_range:
                        if name_map.get(str(uid_i), '').split('#')[0].lower() == base:
                            exp_own.append((name_map.get(str(uid_i), name), {}))
                            exp_own_names.add(base)
                            break
            for name, flags in actual_ehs:
                base = name.split('#')[0].lower()
                if not flags and base not in exp_enemy_names:
                    for uid_i in enemy_summon_range:
                        if name_map.get(str(uid_i), '').split('#')[0].lower() == base:
                            exp_enemy.append((name_map.get(str(uid_i), name), {}))
                            exp_enemy_names.add(base)
                            break

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

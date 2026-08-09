# TyrantAPICommander
**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.
> July 2026 — v5.4

---

## Requirements
| Component | Details |
|-----------|---------|
| Python | 3.8+ (no external libraries required) |
| `settings_N.json` | Account config with `user_id`, `auth_token`, `user_agent` |
| `tuo.exe` | Custom-compiled TUO with hand-state patch (see TUO Build section) |
| `arenagauntlet.txt` | Known opponent defense decks (`data/` folder) |
| `attackdecks.txt` | Known attack decks for Brawl gauntlet (`data/` folder, auto-generated) |
| `cards_section_*.xml` | Card database (`data/` folder) |
| `missions.xml` | Mission database (`data/` folder) |
| `achievements.xml` | Achievement database (`data/` folder) |
| `items.xml` | Items database (`data/` folder) |
| `events.xml` | Events database (`data/` folder) |
| `battleground_effects.xml` | BGE definitions (`data/` folder) |
| `updates.xml` | Game updates (`data/` folder) |
| `fusion_recipes_cj2.xml` | Fusion recipe database (`data/` folder) |
| `database.yml` | TUO database file (auto-managed, max ~310 MB) |

*Note: v4.7+ requires a custom-compiled tuo.exe with the hand-state patch. See TUO Build section.*

---

## settings_N.json Format
```json
{
    "request_data": {
        "user_id": "xxx",
        "password": "xxx",
        "syncode": "xxx",
        "kong_id": "xxx",
        "kong_token": "xxx",
        "kong_name": "xxx",
        "unity": "Unity5_4_2",
        "client_version": "80",
        "device_type": "Firefox+85.0",
        "os_version": "Windows 10",
        "platform": "Web"
    },
    "url": "mobile.tyrantonline.com",
    "user_agent": "Mozilla/5.0 ...",
    "play_enabled": true,
    "skip_brawl": false,
    "skip_guildwar": false
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `play_enabled` | `true` | Excludes account from all multi-account operations if `false` |
| `skip_brawl` | `false` | Skips brawl in F→16 and F→20 pipelines; single-account F→12 unaffected |
| `skip_guildwar` | `false` | Skips GW in F→17 pipeline; single-account F→13 unaffected |

---

## File Structure
```
TUO-Live/
├── tuo.exe
└── data/
    ├── TyrantAPICommander.py          ← Main script
    ├── generate_war_html.py           ← Standalone Guild War HTML generator
    ├── check_combat_log.py            ← Combat log validator
    ├── check_suspicious_losses.py     ← Suspicious loss filter
    ├── settings_1.json                ← Account configuration
    ├── settings_2.json
    ├── settings/                      ← Alternative: settings files in subfolder
    ├── arenagauntlet.txt              ← Defense deck database
    ├── attackdecks.txt                ← Attack deck database (auto-generated)
    ├── outdatedIDs.txt                ← Card IDs to salvage (shared)
    ├── bges.txt                       ← TUO BGE alias definitions
    ├── import/                        ← Drop *.txt here for deck import (D→18)
    ├── ownedcards/                    ← Inventory export target (all accounts)
    ├── export/                        ← Gauntlet output + loyal_challenge_issues.txt
    ├── combatlog/                     ← Per-account combat logs (Arena + Brawl)
    │   └── suspicious/                ← Auto-copied suspicious loss logs
    ├── guild_member_cache/            ← Name→ID cache per guild (6 h TTL)
    ├── energylog/                     ← Hourly energy snapshots
    ├── guildwar_stats/                ← Guild War JSON + HTML snapshots
    └── [xml/yml files]
```

---

## Menu Structure
| Submenu | Category | Key Features |
|---------|----------|--------------|
| **A** | Info & Events | Player info, active events, XML update, deck editor, guild members, quests, **PvP Challenge Overview** |
| **B** | Inventory & Export | Export decks, gauntlet management, sync guild defense + attack decks, Build Brawl Gauntlet, Fuse All Maxed Cards |
| **C** | Guild Management | Sync decks, leave/invite/accept, Build Brawl Gauntlet |
| **D** | Economy | Buy, salvage, build card/dominion, optimize mission, update from import, use shards (all accounts) |
| **E** | Events & Rewards | Claim rewards, play missions/quests/raid (single & all accounts) |
| **F** | Automation & Battle | Live Sim, multi-account pipelines, energy tracker, Guild War, claim daily reward |

Settings (`91`/`92`) accessible from main menu at any time.

---

## Information Menu (A)
| # | Name | Description |
|---|------|-------------|
| 1 | Player Info | Account stats and resources |
| 2 | Active Events & Activities | Current events, brawl, GW |
| 3 | Guild Members with Rating | Member list with ratings |
| 4 | Energy Overview – All Accounts | Mission/Arena/Event energy snapshot |
| 5 | Energy Tracker (hourly log) | Logs to `energylog/`; auto-detects Raid/Brawl/GW |
| 6 | Quests & Achievements | Active quests and achievements |
| 7 | PvP Challenge Overview (All Accounts) | Challenge step + sub-challenge progress; Enter=Refresh, ESC=Exit |

---

## Automation & Battle (F)
| # | Name | Description |
|---|------|-------------|
| 11 | Live Sim Battle (Arena) | TUO reorder; flexible auto; hand-state; optional combat log |
| 12 | Live Sim Battle (Brawl) | TUO `brawl` mode; hand-state; optional combat log |
| 13 | Live Sim Battle (Guild War) | TUO `gw` mode; hand-state; BGE; fort/summon UID tracking |
| 14 | Optimize Deck vs Guild Defense | TUO anneal (500 iter) vs all guild defenses |
| 15 | Multi-Account: Arena | Live Sim Arena; challenge deck auto-applied |
| 16 | Multi-Account: Brawl | Live Sim Brawl; respects `skip_brawl` |
| 17 | Multi-Account: Guild War | Live Sim GW; respects `skip_guildwar` |
| 18 | Multi-Account: Raid + Quest Mission + Arena | Daily Reward → Raid → Quest → Arena |
| 19 | Multi-Account: Quest Mission + Arena | Daily Reward → Quest → Arena |
| 20 | Multi-Account: Brawl + Quest Mission + Arena | Daily Reward → Brawl → Quest → Arena |
| 21 | Energy Tracker (hourly log) | Logs Raid/Brawl/GW/Mission/Arena energy |
| 22 | Guild War Stats Tracker | Polls every 30 min; JSON + HTML |
| 23 | Guild War Summary from JSON files | Generates summary HTML |
| 25 | Claim Daily Reward | Current account |
| 26 | Claim Daily Reward – All Accounts | All `play_enabled` accounts |

Multi-account arena pipelines (F→15, F→18, F→19, F→20) automatically detect the active PvP Challenge and apply deck adjustments per account before battles. Deck is always restored afterwards (try/finally).

---

## PvP Challenge Automation

### Detection Logic
1. **Time-limited challenge** (type-12, `end_time` in future) — highest priority
2. **Expired time-limited** — fallback
3. **Extreme PVP Challenge** (permanent, no `end_time`) — final fallback

### Forever Loyal PVP Challenge (16 steps)
| Step | Name | Commander | Required | Pool (n) |
|------|------|-----------|----------|----------|
| 1 | Loyal Persecutor | Gaia the Purifier | — | — |
| 2 | Loyal Electrosizer | Octane Optimized | Scythe Persecutor | — |
| 3 | Loyal Dominion | — | — | — |
| 4 | Loyal Axis | Gaia the Purifier | Electrosizer | — |
| 5 | Loyal Hunter | — | — | — |
| 6 | Loyal Invader | — | — | Ikadri Rex, Vengeful Spectre, Vatborn Tynosquid, Tunneler Drillmaster, Gate Pulser (5) |
| 7 | Loyal Deadline | — | — | Rebel Ranger, Mezarkos of Thule, Halcyon's Regiment, Igniting Cargo, Skydrop Pyxis (3) |
| 8 | Loyal Adept | Malort Blightfather | Collapser Deadline ★ | — |
| 9 | Loyal Berserker | — | — | Tongues of Tirlok, Razorsharp Hydroblade, Yobedyssseus, Primal Yeren (3) |
| 10 | Loyal Core | — | Devoted Adept | Primal Yeren, Arcadia Redeemed, Experiment Gasher, The Mass, Impurity Arrester, Restore Sequencer (4) |
| 11 | Loyal Eagle | Octane Optimized | Radiated Core | — |
| 12 | Loyal Eliminator | — | — | — |
| 13 | Loyal Cheetah | Daedalus Charged | Boreal Eagle | — |
| 14 | Loyal Revered | Malort Blightfather | Constantine's Cheetah ★ | — |
| 15 | Loyal Vindicator | Octane Optimized | — | Gate Pulser, Malediction, Anchorage Defender (3) |
| 16 | Loyal Dominion | — | The Revered | Enyo Ruinmaker, Yurich's Observatory, Metro Monitor, Veles Shapeshifter, Yurich's Toeslasher, Tengri Godhammer (2) |

★ `play_first` active: card is played immediately when drawn

### Extreme PVP Challenge (28 steps, permanent fallback)
Steps 1–7: no deck changes. Steps 8–28 apply commander swaps, required assault cards, and pool cards. Heal steps (18, 20, 22, 24, 27) have `play_first` active.

### Pool Card Logic
Per card in priority order:
1. Equip existing max-level copies from free inventory (as many as needed)
2. Build additional copies via `build_card` (Gold→SP auto-triggered if SP low)
3. Only move to next pool card when current card exhausted or build fails

### Issue Logging
Failures (card unavailable, insufficient pool, setDeckCards error) appended to `export/loyal_challenge_issues.txt` with timestamp and account name. Never overwritten.

### PvP Challenge Overview (A→7)
Displays all accounts with step, challenge name, active sub-challenge and progress.
- **Enter** → refresh (re-fetches all accounts)
- **ESC** → exit
- After refresh: step column shows `6 (+1)` if step advanced; progress shows `18/25 (+3)` if progress within same step

---

## Key Features

### Live Sim Battle
- **Arena** — `pvp` mode; flexible auto; hand-state; own-guild + skip-guild filter; pre-sim win% threshold 50%; deck restored after session
- **Brawl** — Slot 2 fixed; `brawl` mode; flexible auto; hand-state; live deck fetch before each battle
- **Guild War** — `gw` mode; `yeffect`/`eeffect`/`effect` BGE; dynamic fort/summon UID tracking; hand-state; partial deck accumulates turn-by-turn; gauntlet entry written after each battle

### Energy Tracker (F→21)
Auto-detects active event each run:
- Guild War active → reads `faction_war.battle_energy` (max 20, no regen/cap warning)
- Raid active → reads `raid_info.energy.battle_energy`
- Brawl active (end_time in future) → reads `player_brawl_data.energy.battle_energy`
- Otherwise → Mission/Arena only (event column hidden)

Accounts with `skip_brawl=true` show `skipped` in event column but display Mission/Arena normally.
Event column header shows full event name (e.g. `Fury Unleashed War /20`).

### GW UID Schema (v5.0+)
| Range | Belongs to |
|-------|-----------|
| 101–110 | Own assault cards |
| 51 | Own dominion |
| 52 .. 52+n_enemy | Enemy forts (efort) |
| 52+n_enemy .. ~100 | Own summons |
| 1–10 | Enemy assault cards |
| 151 | Enemy dominion |
| 152 .. 152+n_own | Own forts (yfort) |
| 152+n_own .. ~200 | Enemy summons |

---

## arenagauntlet.txt
```
//Last seen on: 2026-07-27 12:00
GUILD_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
WIN_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
LOSS_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```
| Prefix | Meaning | Priority |
|--------|---------|----------|
| `GUILD_` | Synced from guild roster or live-fetched | Always beats WIN_/LOSS_ |
| `WIN_` | Beaten the player | Overrides LOSS_ |
| `LOSS_` | Lost against the player | Lowest priority |

---

## TUO Custom Build — Hand-State Patch

### Build (Windows / MinGW-w64, static)
```powershell
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DSTATIC=ON
mingw32-make -j8
```
Disable antivirus during cmake configure step.

### Supported State Flags
`h`, `protect`, `attack_boost`, `perm_max_health`, `avenge_attack`, `enfeeble`, `inhibited`, `jammed`, `jam_countdown`, `flurry_countdown`, `poison`, `sunder`, `enrage`, `add_skill_berserk`, `overloaded`, `stasis`, `entrap`, `add_skill_counter`, `tribute`, `sabotage`, `mark`, `disease`, `corrosive`, `corrosion`

**Evolved skill pairs (8):** `absorb→evade`, `weaken→sunder`, `pierce→rupture`, `swipe→drain`, `leech→refresh`, `siege→mortar`, `poison→venom`, `payback→revenge`

**Enhanced values:** `enhance_subdue`, `enhance_scavenge`, `enhance_berserk`, `enhance_avenge`, `enhance_leech`, `enhance_coalition`, `enhance_mark`, `enhance_venom`, `enhance_allegiance`, `enhance_inhibit`, `enhance_armored`, `enhance_legion`, `enhance_tribute`, `enhance_hunt`, `enhance_drain`, `enhance_stasis`, `enhance_swipe`, `enhance_besiege`

---

## Changelog

### v5.4 — August 2026 *(current)*
- **NEW** Extreme PVP Challenge (28 steps) as permanent fallback when no time-limited challenge is active; full ruleset for all steps
- **NEW** PvP Challenge Overview (A→7) — generalized for any type-12 challenge; Enter=Refresh with step/progress deltas; ESC=Exit
- **NEW** `play_first` override — Loyal step 8 (Collapser Deadline), step 14 (Constantine's Cheetah); all Extreme Heal steps (18/20/22/24/27)
- **FIX** Pool card logic — each card now uses as many copies as available before moving to next card; was incorrectly limited to 1 copy per unique pool entry
- **FIX** Deck snapshot taken before builds (Phase 0) so restore correctly reverts to pre-challenge state
- **FIX** `setDeckCards` success detection — API returns full `init_data` on success (containing `user_decks`/`user_data`), not `result: True`
- **FIX** Arena pipelines — `try/finally` ensures deck restore even if battle session crashes
- **FIX** `player_brawl_data` list guard — no crash when API returns list instead of dict (e.g. no active brawl)
- **FIX** Energy tracker — `skip_event` accounts show Mission/Arena values normally; only event column shows `skipped`
- **CHANGE** Step 7 pool_min 2→3; Step 8 commander Jotun→Malort; Step 9 pool_min 2→3; Step 10 pool updated; Step 15 pool_min 2→3
- **CHANGE** Challenge detection prefers time-limited (end_time in future) over permanent challenges

### v5.3 — July 2026
- **NEW** Forever Loyal PvP Challenge Automation — deck auto-adjusted per step; required cards built/upgraded; pool cards equipped/built in priority order; deck restored after each account (try/finally)
- **NEW** `skip_brawl` / `skip_guildwar` per-account settings keys
- **NEW** Claim Daily Reward as Phase 0 in F→18, F→19, F→20
- **FIX** `_resolve_to_max_level_id` — uses base_id + xml_level scan instead of unreliable upgrade_id chain
- **FIX** Energy tracker — event_label default was 'Brawl'; now None when no event active; event name shown in header

### v5.2 — July 2026
- **FIX** Fuse — rarity threshold corrected (≥3 Epic, was ≥4 Legendary); tier lookup via base_id for Level-6 cards
- **FIX** GW gauntlet export — enemy_guild variable; partial deck growth cumulative; commander/dominion excluded from rev_uids
- **FIX** check_combat_log — own_101 detection; Issues folder; enhance_besiege in INT_FLAGS and scan_flags
- **FIX** Energy tracker — event label crash (None in join); GW energy after GW ends; event name in column header

### v5.1 — July 2026
- **FIX** GW/Brawl UID Schema; hand-state dict-valued flag filter
- **NEW** GW Gauntlet Export; enhance_besiege in sim.cpp
- **FIX** GW BGE pass-through; dominion position; energy tracker GW energy

### v5.0 — July 2026
- Live Deck Fetch; Commander/Dominion/Summon UID tracking; Fuse All Maxed Cards; pre-sim threshold 50%; quest mission fallback

### v4.0–v4.9 — April–May 2026
Guild War Live Sim; Build Brawl Gauntlet; Resolution Assistant; 6-category menu; multi-account pipelines; Raid event; hand-state patch.

---
*TyrantAPICommander — August 2026 — v5.4*

# TyrantAPICommander
**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.
> July 2026 — v5.1
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
    ├── export/                        ← Gauntlet output files
    ├── combatlog/                     ← Per-account combat logs (Arena + Brawl)
    │   └── suspicious/                ← Auto-copied suspicious loss logs
    ├── guild_member_cache/            ← Name→ID cache per guild (6 h TTL)
    ├── energylog/                     ← Hourly energy snapshots
    ├── guildwar_stats/                ← Guild War JSON + HTML snapshots
    ├── missions.xml
    ├── achievements.xml
    ├── items.xml
    ├── events.xml
    ├── battleground_effects.xml
    ├── updates.xml
    ├── cards_section_*.xml
    ├── fusion_recipes_cj2.xml
    └── database.yml
```
---
## Menu Structure
| Submenu | Category | Key Features |
|---------|----------|--------------|
| **A** | Info & Events | Player info, active events, XML update, deck editor, guild members, quests |
| **B** | Inventory & Export | Export decks (slots 1–6), gauntlet management, sync guild defense + attack decks, Build Brawl Gauntlet (defense + attack), Fuse All Maxed Cards |
| **C** | Guild Management | Sync decks, leave/invite/accept, Build Brawl Gauntlet |
| **D** | Economy | Buy, salvage, build card/dominion, optimize mission, update from import, use shards (all accounts) |
| **E** | Events & Rewards | Claim rewards, play missions/quests/raid (single & all accounts) |
| **F** | Automation & Battle | Live Sim, multi-account pipelines, energy tracker, Guild War, claim daily reward |
Settings (`91`/`92`) accessible from main menu at any time.
---
## Automation & Battle (F)
| # | Name | Description |
|---|------|-------------|
| 1 | Claim Rewards | Auto-detects and claims current event reward |
| 2 | Claim Rewards – All Accounts | For all `play_enabled` accounts |
| 3 | Attack Next Free Player | Arena attack without TUO; skip-guild filter |
| 4 | Play Highest Mission (loop) | 3-star grind until energy empty |
| 5 | Play Highest Mission – All Accounts | Same for account range |
| 6 | ↳ Clear Mission Blacklist | Clears skipped mission IDs for all accounts |
| 7 | Play Quest Missions (loop) | Quest-linked missions until energy depleted; fallback to Mission 142 |
| 8 | Play First Quest Mission – All Accounts | Per account: first quest mission until energy=0 |
| 9 | Play Raid (auto+skip, loop) | Raid battles until battle energy empty; auto Slot 5 |
| 10 | Play Raid – All Accounts | Same for account range |
| 11 | Live Sim Battle (Arena) | TUO reorder; flexible auto; hand-state; optional combat log |
| 12 | Live Sim Battle (Brawl) | TUO `brawl` mode; hand-state; optional combat log |
| 13 | Live Sim Battle (Guild War) | TUO `gw` mode; hand-state; `yeffect`/`eeffect`/`effect` BGE; fort/summon UID tracking |
| 14 | Optimize Deck vs Guild Defense | TUO anneal (500 iter) vs all guild defenses |
| 15 | Multi-Account: Arena | Live Sim Arena; deck restored after each account |
| 16 | Multi-Account: Brawl | Live Sim Brawl for account range |
| 17 | Multi-Account: Guild War | Live Sim Guild War for account range |
| 18 | Multi-Account: Raid + Quest Mission + Arena | Raid → Quest Mission → Arena; deck restored |
| 19 | Multi-Account: Quest Mission + Arena | Quest Mission → Arena; Arena combat log prompt |
| 20 | Multi-Account: Brawl + Quest Mission + Arena | Brawl → Quest Mission → Arena; log prompt N/b/a |
| 21 | Energy Tracker (hourly log) | Auto-detects Raid/Brawl/Guild War; logs to `energylog/` |
| 22 | Guild War Stats Tracker | Polls every 30 min; JSON + HTML snapshot |
| 23 | Guild War Summary from JSON files | Generates summary HTML per guild+event group |
| 25 | Claim Daily Reward | Claims daily bonus for current account |
| 26 | Claim Daily Reward – All Accounts | Claims for all `play_enabled` accounts |
---
## Inventory & Card Management (B)
| # | Name | Description |
|---|------|-------------|
| 21 | Fuse All Maxed Cards | Fuses Epic+ Tier 0/1 Level-6 cards with ≥2 free copies; no SP cost |
| 22 | Fuse All Maxed Cards – All Accounts | Same for all `play_enabled` accounts |
Excludes: base fusion cards (all FUSION_GROUPS), T1 products derived from base fusion cards, Neocyte Core, Vindicator Reactor.
---
## Key Features
### Live Sim Battle
- **Arena** — `pvp` mode; flexible auto; hand-state; own-guild + skip-guild filter; pre-sim win% threshold 50%; deck restored after session
- **Brawl** — Slot 2 fixed; `brawl` mode; flexible auto; hand-state; live deck fetch before each battle
- **Guild War** — `gw` mode; `yeffect`/`eeffect`/`effect` BGE; dynamic fort/summon UID tracking; hand-state; partial deck accumulates turn-by-turn; gauntlet entry written after each battle
- **BGE conversion** — hyphens (`Temporal Backlash` → `Temporal-Backlash`); bges.txt aliases passed through unchanged; exceptions: `Oath-Of-Loyalty`, `Zealots-Preservation`, `SuperHeroism`, `EnduringRage 2`

### Live Deck Fetch (Arena & Brawl)
Before each battle, the current enemy defense deck is fetched live via `getProfileData(target_user_id)`. Uses a guild→proxy-account map built at session start. Persistent name→ID cache in `guild_member_cache/{guild}.json` (6 h TTL). Live-fetched decks written as `GUILD_` entries; `WIN_`/`LOSS_` writes skipped for players from accessible guilds.

### GW UID Schema (v5.0+)
Empirically verified from combat logs. When own assault = 101–110:
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

### BGE Flags
| TUO Flag | Meaning | Used in |
|----------|---------|---------|
| `effect` | Global BGE (both sides) | Arena, Brawl, global GW BGE |
| `yeffect` | Own faction BGE | Guild War (own faction only) |
| `eeffect` | Enemy faction BGE | Guild War (enemy faction only) |

### Hand-State (v4.7+)
Real-time card state passed to TUO via `hand-state` and `enemy:hand-state` each turn. Includes commander/dominion (UIDs 50/51/150/151) and summon card IDs (read from `battle_data.turn[N].tokens`). Dict-valued flags (e.g. `mimic_skill`) and UID −1 are filtered out automatically.

### Quest Mission Fallback
When no active quest mission is found, `play_first_quest_mission_loop` falls back to `play_highest_mission_loop` (Mission 142) to avoid energy accumulation.

### Energy Tracker (F→21)
Auto-detects active event each run:
- Guild War active → reads `faction_war.battle_energy` (max 20, no regen/cap warning)
- Raid active → reads `raid_info.energy.battle_energy`
- Brawl active (end_time in future) → reads `player_brawl_data.energy.battle_energy`
- Otherwise → Mission energy only
Lines at 100% cap flagged with `!!` (except GW energy).

### Build Brawl Gauntlet (B→13 & 14)
Smart multi-phase polling engine (ranks 1–100). Option 13 reuses existing gauntlet; Option 14 always rebuilds. Attack gauntlet auto-built at end of every defense run.

### Sync All Guild Decks (B→11)
Single-pass sync per member. Dedup passes remove `WIN_`/`LOSS_` entries shadowed by `GUILD_` entries, and resolve guild-switch duplicates.

### Autosalvage Outdated (D→10 & 19)
Cards equipped in any deck slot are always skipped. When a card from `outdatedIDs.txt` is found equipped, its ID is automatically removed from the file.

### Combat Log
Per-turn JSON logs in `combatlog/`. Suspicious losses (TUO predicted win% ≥ threshold) auto-copied to `combatlog/suspicious/` by `check_suspicious_losses.py`.

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
### Patched Files
| File | Change |
|------|--------|
| `tyrant_optimize.h` | `extern` declarations for `your_hand_state` / `enemy_hand_state` |
| `tyrant_optimize.cpp` | Define maps; implement `parse_hand_state()` with `#N` duplicate-card indexing |
| `sim.cpp` | Apply overrides in `Hand::reset()`; evolved skill offsets; enhanced values |

### Build (Windows / MinGW-w64, static)
```powershell
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DSTATIC=ON
mingw32-make -j8
```
Disable antivirus during cmake configure step (blocks temp EXE deletion).

### Supported State Flags (v5.1)
`h`, `protect`, `attack_boost`, `perm_max_health`, `avenge_attack`, `enfeeble`, `inhibited`, `jammed`, `jam_countdown`, `flurry_countdown`, `poison`, `sunder`, `enrage`, `add_skill_berserk`, `overloaded`, `stasis`, `entrap`, `add_skill_counter`, `tribute`, `sabotage`, `mark`, `disease`, `corrosive`, `corrosion`

**Evolved skill pairs (8):** `absorb→evade`, `weaken→sunder`, `pierce→rupture`, `swipe→drain`, `leech→refresh`, `siege→mortar`, `poison→venom`, `payback→revenge`

**Enhanced values:** `enhance_subdue`, `enhance_scavenge`, `enhance_berserk`, `enhance_avenge`, `enhance_leech`, `enhance_coalition`, `enhance_mark`, `enhance_venom`, `enhance_allegiance`, `enhance_inhibit`, `enhance_armored`, `enhance_legion`, `enhance_tribute`, `enhance_hunt`, `enhance_drain`, `enhance_stasis`, `enhance_swipe`, `enhance_besiege` *(new in v5.1 — maps to Skill::mortar)*

**Ignored (not serializable):** `corroder`, `poisoner`, `mimic_skill` (dict value), UID −1

---
## Changelog

### v5.1 — July 2026 *(current)*
- **FIX** GW/Brawl UID Schema — complete rewrite based on empirical combat log analysis. Own forts at 152..152+n, enemy forts at 52..52+n, summons beyond. Fixes 215,000 errors across 7,227 GW logs.
- **FIX** check_combat_log.py — detect_ranges() now dynamic based on yfort/efort count; extended to UID ~100/200 for summons
- **FIX** Hand-state — dict-valued flags (mimic_skill) and UID −1 filtered in all three _states_for_range functions
- **NEW** GW Gauntlet Export — deck written to arenagauntlet.txt after every GW battle; guild suffix from faction_war data
- **FIX** GW Enemy Guild — entries now correctly suffixed (WIN_Player_Guild)
- **FIX** GW BGE — bges.txt loaded at runtime; GW BGE aliases passed through unchanged
- **FIX** Dominion position in freeze deck — stays at slot 2 regardless of reorder
- **FIX** Brawl start detection — energy > 0 fallback when end_time not yet set
- **FIX** Trim logic — guildless entries no longer share one bucket
- **NEW** enhance_besiege in sim.cpp → Skill::mortar
- **FIX** Energy Tracker — GW energy from faction_war.battle_energy (max 20, no cap warning); stale brawl hidden after end_time

### v5.0 — July 2026
- Live Deck Fetch (Arena & Brawl); Commander/Dominion/Summon UID tracking; tokens[] parsing
- arenagauntlet.txt atomic writes; GUILD_ write-skip for accessible guilds; _degrade_guild_entry()
- Fuse All Maxed Cards (B→21/22); Autosalvage ID auto-removal; Base epics keep 15→10
- Pre-sim threshold 30%→50%; flexible-iter 20→100; BGE mapping overhaul
- Quest mission fallback to Mission 142; check_suspicious_losses.py; XML downloads

### v4.9 — May 2026
- Sync dedup (WIN_/LOSS_ shadowed by GUILD_); guild-switch duplicate resolution
- Placement Brawl display; Claim Event Rewards endpoint fix; GW Summary NameError fixes

### v4.8 — May 2026
- Card state replace-per-turn semantics; combat log for Arena; 6 new evolved skill pairs

### v4.7 — May 2026
- Hand-state / enemy:hand-state; Brawl combat log; Energy Tracker; Sync All Guild Decks combined pass

### v4.0–v4.6 — April–May 2026
Guild War Live Sim; Build Brawl Gauntlet smart polling; Resolution Assistant; 6-category menu; multi-account pipelines; Raid event.

---
*TyrantAPICommander — July 2026 — v5.1*

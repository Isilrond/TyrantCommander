# TyrantAPICommander

**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.

> August 2026 — v5.5

---

## Requirements

| Component | Details |
|-----------|---------|
| Python | 3.8+ (no external libraries required) |
| `settings_N.json` | Account config with `user_id`, `auth_token`, `user_agent` |
| `tuo.exe` | Custom-compiled TUO executable with hand-state patch (see Chapter 8); in parent folder (`../tuo.exe`) |
| `arenagauntlet.txt` | Known opponent defense decks (`data/` folder) |
| `attackdecks.txt` | Known attack decks for Brawl gauntlet (`data/` folder, auto-generated) |
| `cards_section_*.xml` | Card database (`data/` folder) |
| `missions.xml` | Mission database (`data/` folder) |
| `fusion_recipes_cj2.xml` | Fusion recipe database (`data/` folder) |
| `achievements.xml` | Achievement database (`data/` folder) |
| `items.xml` | Items database (`data/` folder) |
| `battleground_effects.xml` | Global BGE definitions with active time windows (`data/` folder) |
| `updates.xml` | Game news/event announcements (`data/` folder) |
| `database.yml` | TUO database file (auto-managed, max ~310 MB) |

> **Important:** All XML files (`cards_section_*.xml`, `missions.xml`, `achievements.xml`, `items.xml`, `battleground_effects.xml`, `updates.xml`, etc.) must be kept up to date manually using **F→1 (Download Game Data)**. Run this regularly to ensure card stats, BGE schedules, and mission data reflect the current game state.

---

## File Structure

```
TUO-Live/
├── tuo.exe
└── data/
    ├── TyrantAPICommander.py        ← Main script
    ├── check_combat_log.py          ← Combat log validator (standalone)
    ├── check_suspicious_losses.py   ← Suspicious loss filter (standalone)
    ├── generate_war_html.py         ← Standalone Guild War HTML generator
    ├── settings_1.json              ← Account configuration
    ├── settings_2.json
    ├── settings/                    ← Alternative: settings files in subfolder
    ├── arenagauntlet.txt            ← Defense deck database
    ├── attackdecks.txt              ← Attack deck database (auto-generated)
    ├── outdatedIDs.txt              ← Card IDs to salvage (shared)
    ├── import/                      ← Drop *.txt files here for D→18
    ├── ownedcards/                  ← Export target (all accounts)
    ├── export/                      ← Gauntlet + challenge issue output
    │   └── loyal_challenge_issues.txt
    ├── combatlog/                   ← Combat logs per account (Arena + Brawl)
    │   └── suspicious/             ← Auto-copied suspicious loss logs
    ├── energylog/                   ← Hourly energy snapshots
    ├── guildwar_stats/              ← Guild War JSON + HTML snapshots
    ├── missions.xml
    ├── achievements.xml
    ├── items.xml
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
| **B** | Inventory & Export | Export decks (slots 1–6), gauntlet management, sync guild defense + attack decks, Build Brawl Gauntlet |
| **C** | Guild Management | Sync decks, leave/invite/accept, Build Brawl Gauntlet |
| **D** | Economy | Buy, salvage, build card/dominion, optimize mission, update from import, use shards (all accounts) |
| **E** | Events & Rewards | Claim rewards, play missions/quests/raid (single & all accounts) |
| **F** | Automation & Battle | Live Sim, multi-account pipelines, energy tracker, Guild War, Loyal Challenge PvP, claim daily reward |

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
| 7 | Play Quest Missions (loop) | Quest-linked missions until energy depleted |
| 8 | Play First Quest Mission – All Accounts | Per account: first quest mission until energy=0 |
| 9 | Play Raid (auto+skip, loop) | Raid battles until battle energy empty; auto Slot 5 |
| 10 | Play Raid – All Accounts | Same for account range |
| 11 | Live Sim Battle (Arena) | TUO reorder; flexible auto; `effect` for global BGE |
| 12 | Live Sim Battle (Brawl) | TUO `brawl` mode; `effect` for global BGE |
| 13 | Live Sim Battle (Guild War) | TUO `surge` mode; `yeffect`/`eeffect`/`effect` for BGE |
| 14 | Optimize Deck vs Guild Defense | TUO anneal (500 iter) vs all guild defenses |
| 15 | Multi-Account: Arena | Live Sim Arena; Loyal Challenge deck applied + restored per account |
| 16 | Multi-Account: Brawl | Live Sim Brawl for account range |
| 17 | Multi-Account: Guild War | Live Sim Guild War for account range |
| 18 | Multi-Account: Raid + Quest Mission + Arena | Raid → Quest → Arena; Loyal Challenge deck applied + restored |
| 19 | Multi-Account: Quest Mission + Arena | Quest → Arena; Loyal Challenge deck applied + restored |
| 20 | Multi-Account: Brawl + Quest Mission + Arena | Brawl → Quest → Arena; Loyal Challenge deck applied + restored |
| 21 | Energy Tracker (hourly log) | Auto-detects Raid/Brawl/Guild Brawl; logs to `energylog/` |
| 22 | Guild War Stats Tracker | Polls every 30 min; JSON + HTML snapshot |
| 23 | Guild War Summary from JSON files | Generates summary HTML per guild+event group |
| 24 | Forever Loyal PVP Challenge Overview | Progress table for all accounts; detects stagnation |
| 25 | Claim Daily Reward | Claims daily bonus for current account |
| 26 | Claim Daily Reward – All Accounts | Claims for all `play_enabled` accounts |

---

## Deck Slots

| Slot | Label | Unlock Cost | Auto-switch |
|------|-------|-------------|-------------|
| 1 | Arena | — | Live Sim Arena, Multi-Account Arena |
| 2 | Brawl | — | Live Sim Brawl, Multi-Account Brawl |
| 3 | Arena Defense | 100 WB | — |
| 4 | Brawl Defense | 150 WB | — |
| 5 | Raid | 200 WB | Play Raid (all variants) |
| 6 | Mission | 250 WB | Play Quest Mission (all variants), Optimize Mission Deck |

---

## Multi-Account Range & Loop Selection

All multi-account options offer 6 run modes:

| Choice | Behaviour |
|--------|-----------|
| 1 | All accounts, once |
| 2 | All accounts, loop |
| 3 | Select range, once |
| 4 | Select range, loop |
| 5 | Single account, once |
| 6 | Single account, loop |

---

## Key Features

### Forever Loyal PVP Challenge (F→15/18/19/20 + F→24)

Automatically adapts Slot 1 deck for the current Loyal Challenge step before arena battles, then restores the original deck after. Runs fully unattended across all accounts.

**Challenge priority:**
1. Forever Loyal PVP Challenge (time-limited, active window)
2. Extreme PVP Challenge (fallback when Loyal is completed or absent)
3. Master the Arena PVP Challenge (defined, deck rules TBD)
4. Cutlass Unleashed PVP Challenge (defined, deck rules TBD)

**How it works:**

1. Detects the current challenge step via `getPvpChallengeData`
2. Checks if required commander is owned; auto-builds via `build_card(id)` if not
3. Builds required cards (upgrades via `build_card` if needed; skips if insufficient SP — logs issue, deck unchanged)
4. Builds pool cards from inventory (up to `pool_min` copies)
5. Pads deck to 10 cards if original has fewer than 10
6. Replaces last N slots with challenge cards via `setDeckCards`
7. Runs arena battles (`live_sim_battle`)
8. Restores original deck via `_restore_loyal_deck` (always, via `finally` block)

**Abort conditions** (deck left unchanged):
- Required card cannot be built (SP/gold insufficient) → `return None, None` before any deck modification
- Fewer than `pool_min` pool cards available

**Extreme PVP Challenge:** parallel quest strands — sub-challenge detected by type-9 achievement name, not linear step counter. Only names from EXTREME_CHALLENGES table are accepted to avoid false matches with other challenge types.

**Issues log:** `export/loyal_challenge_issues.txt`

**Challenge Overview (F→24):** shows all accounts with step, sub-challenge name, progress, and end date. Highlights stagnating accounts (+0 between snapshots). Uses `_detect_loyal_challenge_step()` for consistency with battle selection.

### Auto GBGE Detection (B→16/17)

Mission deck optimization (B→16 single account, B→17 all accounts) automatically reads the active Global Battleground Effect from `battleground_effects.xml`. If an active GBGE is found (current time within `global_start_time`/`global_end_time`), it is applied automatically with a 5-second notice — no manual input required. If no GBGE is active, the optimizer runs without one.

**XML name → TUO flag conversion:** names with spaces are hyphenated by default. Known overrides: `Crackdown` → `Crackdown 2`, `Oath of Loyalty` → `Oath-Of-Loyalty`, etc.

### Brawl & Guild Brawl

Guild Brawls are treated identically to regular Brawls for energy tracking and sim. Score calculation differs (guild sum vs individual) but energy source (`player_brawl_data.energy.battle_energy`) is the same.

**Structure/Summon UID assignment:** Own and enemy structures (uid 52-99, 152-199) are assigned dynamically by matching card names against `own_states`/`enemy_states` from the API turn data. This correctly handles infinite summon chains (e.g., Kozel the Deathless, Industry of Eden). Ambiguous cases fall back to convention (52-99 = enemy, 152-199 = own).

### Live Sim Battle

- **Arena** — flexible mode automatic; own-guild + skip-guild filter (`Predacons` excluded by default); Loyal Challenge deck applied and restored per session
- **Brawl** — Slot 2 fixed; `brawl` mode (maximises brawl score)
- **Guild War** — `surge` mode (workaround; `gw` mode causes failures); `yeffect`/`eeffect`/`effect` for BGE; fort UID detection

### BGE Flags

| TUO Flag | Meaning | Used in |
|----------|---------|---------|
| `effect` | Global BGE (both sides) | Arena, Brawl, global GW BGE |
| `yeffect` | Own faction BGE | Guild War (own faction only) |
| `eeffect` | Enemy faction BGE | Guild War (enemy faction only) |

### Multi-Account Combined Pipelines (F→18/19/20)

Active deck saved before Phase 1 and restored after Arena completes for each account. Loyal Challenge deck applied and restored within the Arena phase. Each phase pre-checks energy and skips gracefully if zero. Quest Mission always uses Slot 6.

### Suspicious Loss Filter (`check_suspicious_losses.py`)

Standalone script — scans `combatlog/` for battles where TUO predicted ≥ threshold% win but result was LOSS.

```
python check_suspicious_losses.py                  # auto-scan combatlog/
python check_suspicious_losses.py <folder/file>    # specific path
python check_suspicious_losses.py --threshold 95   # custom threshold (default: 99.5%)
```

Matching files are auto-copied to `combatlog/suspicious/`.

### Combat Log Validator (`check_combat_log.py`)

Standalone script — validates that `api_card_states` in each JSON log matches the `hand-state` string in `tuo_cmd`. Reports mismatches with field-level diff. Handles:
- mimic_skill extraction (before SKIP_FLAGS check)
- Commander state merging (-1/-2 → uid 50/150)
- Extended UID ranges for dominions and structures
- Brawl own/enemy side detection via `enemy:hand` uid matching (priority over deck-name matching)
- Structure disambiguation via mimic_skill extraction in `_acs_to_flag_set`

### Energy Tracker (F→21)

Auto-detects active event type each run:
- Raid active → reads `raid_info.energy.battle_energy`, column: `Raid /25`
- Brawl/Guild Brawl active → reads `player_brawl_data.energy.battle_energy`, column: brawl name
- Otherwise → column: `Event /25`

Brawl detected via `active_brawl_data` name + time fields. Brawl not marked active before `start_time`. Guild Brawls detected identically to regular Brawls.

### Build Brawl Gauntlet (B→13 & 14)

**Defense gauntlet** — Smart multi-phase polling engine:
1. **Phase 1a** — Rank discovery (no leaderboard calls)
2. **Phase 1b** — Consensus poll: majority vote per rank; verified ties
3. **Phase 1c** — Coverage top-up for remaining gaps
4. **Gap-fill** — Targeted retry; force-place fallback; `_placed_uids` guard
5. **Phase 2** — Deck lookup from `arenagauntlet.txt`

Guild Brawl active → automatically falls back to `getPreviousBrawlTopLeaderboard`.

**Attack gauntlet** — Built automatically at end of every defense gauntlet run. Substitutes attack decks from `attackdecks.txt`. Output: `export/<brawl_key>_A.txt`.

---

## arenagauntlet.txt

```
//Last seen on: 2026-08-11 09:15
WIN_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
LOSS_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
GUILD_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```

| Prefix | Meaning | Priority |
|--------|---------|----------|
| `WIN_` | Beaten the player | Newer timestamp wins vs `LOSS_` |
| `LOSS_` | Lost against the player | Newer timestamp wins vs `WIN_` |
| `GUILD_` | Synced from guild roster | Always beats `WIN_`/`LOSS_` |

Post-merge cleanup: `WIN_`/`LOSS_` entries are removed after sync if a `GUILD_` entry exists for the same player.

---

## attackdecks.txt

```
//Last seen on: 2026-08-11 09:15
ATTACK_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```

Generated by **B → 11 Sync All Guild Decks** (combined defense + attack pass).

---

## settings_N.json

```json
{
  "user_id":           "12345678",
  "auth_token":        "abcdef1234567890",
  "user_agent":        "Mozilla/5.0 ...",
  "kong_token":        "kongregate_token_optional",
  "kong_name":         "AccountDisplayName",
  "play_enabled":      true,
  "mission_blacklist": [2301, 2305]
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `user_id` | — | Game user ID (required) |
| `auth_token` | — | Login token (required) |
| `user_agent` | — | Browser user agent (required) |
| `kong_token` | — | Kongregate token (optional) |
| `kong_name` | — | Display name; read from top-level or `request_data.kong_name` |
| `play_enabled` | `true` | Skip account in all multi-account operations if `false` |
| `mission_blacklist` | `[]` | Mission IDs permanently skipped by mission grind |

---

## Changelog

### v5.5 — August 2026 *(current)*

- **NEW** Auto GBGE detection for B→16/17 — reads active Global BGE from `battleground_effects.xml` (unix timestamps); passes `effect 'Crackdown 2'` to TUO automatically; 5-second notice instead of manual prompt
- **NEW** `battleground_effects.xml` and `updates.xml` added to required data files (download via F→1)
- **NEW** Crackdown → Crackdown 2 override in `_api_bge_to_tuo()`
- **FIX** Brawl structure/summon UID assignment — dynamic name-matching against `own_states`/`enemy_states`; correctly handles infinite summon chains (Kozel the Deathless, Industry of Eden)
- **FIX** Guild Brawl detected as regular Brawl for energy tracking (same energy source)
- **FIX** Brawl `start_time` check — brawl not active before `start_time` (3 detection points fixed)
- **FIX** Brawl NameError — `_brawl_card_states` → `_cl_card_states`
- **FIX** Challenge fallback — when Forever Loyal PVP Challenge is completed, Extreme PVP Challenge is correctly used as fallback (both in battle selection and F→24 overview)
- **FIX** Extreme PVP Challenge — deck selection by sub-challenge name (type-9 achievement), not linear step; parallel quest strands supported; type-9 filter accepts only names from EXTREME_CHALLENGES table
- **FIX** F→24 overview — uses `_detect_loyal_challenge_step()` for consistency with battle selection
- **FIX** `Loyal Dominion (16)` → `Loyal Dominion` to match API name
- **FIX** Commander auto-build for Loyal Challenge — checks inventory, builds via `build_card(id)` if not owned
- **FIX** `play_first` override removed — TUO decides card order
- **FIX** mimic_skill handling — real state flags not overwritten by mimic-derived values; trigger field is metadata only; Mimic fires as normal activation
- **FIX** sim.cpp — `enhance_sabotage` → `Skill::sabotage`; `enhance_besiege` → `Skill::mortar` added
- **FIX** check_combat_log — `enemy:hand` uid 1-10 detection moved before deck-name matching; mimic_skill extraction in `_acs_to_flag_set` for structure disambiguation
- **CHANGE** Combat log field snapshot — removed redundant fields (`barrier`, `attack_boost`, `corrosion`, `flurry_countdown`, `max_hp`, `hp_pct`); logs now contain only `uid`, `card_id`, `name`, `hp`
- **ADD** `MASTER_ARENA_CHALLENGES` and `CUTLASS_CHALLENGES` tables defined (deck rules TBD)

### v5.4 — August 2026

- **NEW** Forever Loyal PVP Challenge system — fully automated deck management for all Loyal Challenge steps across all multi-account arena pipelines (F→15/18/19/20)
- **NEW** Forever Loyal PVP Challenge Overview (F→24) — progress table with stagnation detection
- **NEW** Suspicious loss filter (`check_suspicious_losses.py`) — scans combat logs for TUO ≥99.5% win predictions that resulted in LOSS; auto-copies to `combatlog/suspicious/`
- **NEW** Combat log validator (`check_combat_log.py`) — validates `api_card_states` vs `hand-state` string per turn
- **FIX** Loyal Challenge — deck restore guaranteed via `try/finally` in all pipeline variants
- **FIX** Loyal Challenge — early `return None, None` before any deck modification when required card unavailable
- **FIX** Loyal Challenge — deck padded to 10 cards before challenge card replacement
- **FIX** Non-interactive mode — `build_card` prompt auto-confirms when no terminal attached
- **FIX** sim.cpp — 8 evolved skill pairs; `siege_evolved_into_mortar`/`siege_evolved_into_besiege` both handled

### v4.9 — May 2026

- **FIX** Sync All Guild Decks — WIN_/LOSS_ cleanup after sync; guild-switch duplicate removal
- **FIX** Active Events — `faction_war_event_info` list handling
- **NEW** Active Events — Placement Brawl dedicated display
- **FIX** Claim Event Rewards — Guild War endpoint corrected to `claimFactionWarRewards`
- **FIX** Guild War Summary — multiple NameErrors resolved

### v4.8 — May 2026

- **FIX** Card state replace semantics (`_update_field_state`)
- **FIX** Field-value merge before sim call
- **NEW** Combat log for Arena in F→19 and F→20
- **NEW** sim.cpp — 8 evolved skill pairs
- **NEW** XML Download — `achievements.xml` and `items.xml` added
- **FIX** `mimic_skill` added to `SKIP_FLAGS`

### v4.7 — May 2026

- **FIX** Sync All Guild Decks — combined defense+attack in single pass (API calls halved)
- **FIX** Build Brawl Gauntlet — attack auto-built at end of every defense run
- **FIX** Menu restructuring — sequential numbering; no gaps
- **NEW** Scan Combat Logs for Unknown sim.cpp Flags (F→5)
- **FIX** sim.cpp — 12 new API flag mappings

### v4.6 — April 2026

*(see full docx changelog)*

### v4.0–v4.5 — April–May 2026

Multi-account pipelines, Energy Tracker, Guild War Stats Tracker, Brawl Gauntlet overhaul, Resolution Assistant, Gold→SP workflow, 6-category menu.

### v3.0 — April 2026

Unlock Commander, Play First Quest Mission – All Accounts, Arena own-guild filter.

### v2.0–v2.9 — February–March 2026

Guild War Stats Tracker, Guild War Summary, Live Sim Guild War, Build Brawl Gauntlet smart polling engine, Resolution Assistant overhaul, 6-category menu structure (A–F).

---

*TyrantAPICommander — August 2026 — v5.5*

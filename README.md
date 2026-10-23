# TyrantAPICommander

**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.

> October 2026 — v5.8

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
| `events.xml` | Game event definitions (`data/` folder) |
| `battle_events_h52.xml` | Brawl event schedule with start/end timestamps (`data/` folder) |
| `raids_x42.xml` | Raid event schedule with start/end timestamps (`data/` folder) |
| `faction_wars_fp3.xml` | Guild War schedule with start/end timestamps (`data/` folder) |
| `event_box.xml` | Event box definitions (`data/` folder) |
| `conquest.xml` | Conquest event data (`data/` folder) |
| `mini_packs_36i.xml` | Mini pack definitions (`data/` folder) |
| `assetbundles5_4_2.xml` | Asset bundle index (`data/` folder) |
| `assetbundles4_6.xml` | Asset bundle index legacy (`data/` folder) |
| `database.yml` | TUO database file (auto-managed, max ~310 MB) |

> **Important:** All XML files must be kept up to date using **F→1 (Update XML Files)**. The event XMLs (`battle_events_h52.xml`, `raids_x42.xml`, `faction_wars_fp3.xml`) are read by D→28/29 for automatic event detection — they typically contain future events, so a single download suffices until a new event cycle begins.

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
    ├── export/                      ← Gauntlet + challenge output
    │   ├── api_errors.log             ← Network/API errors per account (retries, init, mission failures)
    │   ├── outdatedIDs_log.txt        ← Changes to outdatedIDs.txt (manual / auto)
    │   ├── pvp_challenge_issues.txt   ← Challenge build/deck failures (all types)
    │   └── challenge_analysis.txt     ← Per-battle challenge log + PROGRESS lines (for diagnosis)
    ├── combatlog/                   ← Combat logs per account (Arena + Brawl)
    │   └── suspicious/             ← Auto-copied suspicious loss logs
    ├── guild_member_cache/          ← Name→ID cache per guild (6 h TTL)
    ├── energylog/                   ← Hourly energy snapshots
    ├── guildwar_stats/              ← Guild War JSON + HTML snapshots
    ├── logo/                        ← Optional logos for GW HTML snapshots
    ├── gw_bges_<Guild>.txt          ← BGE per match for GW Auto-Pipeline (one name per line)
    ├── missions.xml
    ├── achievements.xml
    ├── items.xml
    ├── battleground_effects.xml
    ├── updates.xml
    ├── events.xml
    ├── battle_events_h52.xml
    ├── raids_x42.xml
    ├── faction_wars_fp3.xml
    ├── event_box.xml
    ├── conquest.xml
    ├── mini_packs_36i.xml
    ├── assetbundles5_4_2.xml
    ├── assetbundles4_6.xml
    ├── cards_section_*.xml
    ├── fusion_recipes_cj2.xml
    └── database.yml
```

---

## Menu Structure

Main menu: **A–F** submenus, `99` = back to account selection, `0` = exit. At account selection: `997` Check API for all accounts, `998` Settings Generator, `999` Settings Help. References in this document use the form **Submenu→Option** (e.g. D→28).

| Submenu | Category | Options |
|---------|----------|---------|
| **A** | Information | 7 |
| **B** | Inventory & Card Management | 24 |
| **C** | Sim Preparation & Export | 14 |
| **D** | Automation & Battle | 29 |
| **E** | Guild Management | 4 |
| **F** | Settings & Maintenance | 5 |

Options marked *multi* are only shown when more than one account is configured.

### A – Information

| # | Name | Description |
|---|------|-------------|
| A→1 | Player Info | Account overview |
| A→2 | Active Events & Activities 🎯 | Active events incl. Guild War section |
| A→3 | Guild Members with Rating |  |
| A→4 | Energy Overview – All Accounts |  |
| A→5 | Energy Tracker (hourly log – Brawl/Mission/Arena) | Auto-detects Raid/Brawl/Guild Brawl; logs to `energylog/` |
| A→6 | Quests & Achievements |  |
| A→7 | PvP Challenge Overview (All Accounts) | Progress table; all challenge types; detects stagnation |

### B – Inventory & Card Management

| # | Name | Description |
|---|------|-------------|
| B→1 | Update Deck (Edit slot + Set Attack/Defense) |  |
| B→2 | Buy Packages |  |
| B→3 | Salvage All Commons |  |
| B→4 | Salvage All Rares |  |
| B→5 | Salvage Base Epics (keep X) |  |
| B→6 | Workflow: Buy + Commons + Rares + Base Epics |  |
| B→7 | Buy Back Card |  |
| B→8 | Build Card (Fusion Recipe & SP-Costs) |  |
| B→9 | Build Dominion (Auto-Build) |  |
| B→10 | Salvage Outdated (Manage outdated cards) |  |
| B→11 | Unlock All Cards | Unlocks all locked cards |
| B→12 | Unlock Commander | Unlocks the commander |
| B→13 | Use Shards (Epic / Legendary / Vindicator) |  |
| B→14 | Salvage Base Epics (keep X) – All Accounts |  |
| B→15 | Change Attack/Defense Deck – All Accounts |  |
| B→16 | Optimize Mission Deck -> Slot 6 (this account) |  |
| B→17 | Optimize Mission Deck -> Slot 6 – All Accounts |  |
| B→18 | Update Deck from Import File (TUO result → all accounts) |  |
| B→19 | Salvage Outdated – All Accounts |  |
| B→20 | Use Shards – All Accounts |  |
| B→21 | Fuse All Maxed Cards (Epic+, Tier 0/1, Level 6) | Fuses all maxed Epic+ cards (Tier 0/1, Level 6) |
| B→22 | Fuse All Maxed Cards – All Accounts |  |
| B→23 | Fill SP to Cap (Buy + Salvage loop) | Buy + Salvage loop until SP cap reached |
| B→24 | Fill SP to Cap – All Accounts |  |

### C – Sim Preparation & Export

| # | Name | Description |
|---|------|-------------|
| C→1 | Export Starterdecks Arena (Slot 1, active accounts) |  |
| C→2 | Export Starterdecks Brawl (Slot 2, active accounts) |  |
| C→3 | Export Starterdecks Arena Defense (Slot 3, active accounts) - unlock costs 100 WB | Unlock costs 100 WB |
| C→4 | Export Starterdecks Brawl Defense (Slot 4, active accounts) - unlock costs 150 WB | Unlock costs 150 WB |
| C→5 | Export Starterdecks Raid (Slot 5, active accounts) |  |
| C→6 | Export Starterdecks Mission (Slot 6, active accounts) |  |
| C→7 | Export Inventory (NAME.txt / currentdecks_NAME.txt) |  |
| C→8 | Export Inventory – All Accounts -> ownedcards/ |  |
| C→9 | Export Guild Decks |  |
| C→10 | Export Specific Guild Decks (from arenagauntlet.txt) |  |
| C→11 | Sync All Guild Decks (defense + attack → arenagauntlet.txt + attackdecks.txt) |  |
| C→12 | Merge arenagauntlet.txt (from import folder) |  |
| C→13 | Build Brawl Gauntlet – last brawl  (defense + attack) |  |
| C→14 | Build Brawl Gauntlet – current brawl  (defense + attack) |  |

### D – Automation & Battle

| # | Name | Description |
|---|------|-------------|
| D→1 | Claim Rewards | Auto-detects and claims current event reward |
| D→2 | Attack Next Free Player (Arena, no TUO) | Arena attack without TUO; skip-guild filter |
| D→3 | Play Highest Mission (auto+skip, loop) | 3-star grind until energy empty |
| D→4 | Play Quest Missions (loop until energy empty) | Quest-linked missions until energy depleted |
| D→5 | Play Raid (auto+skip, loop) | Raid battles until battle energy empty; auto Slot 5 |
| D→6 | Live Sim Battle (Arena) | TUO reorder; flexible auto; `effect` for global BGE |
| D→7 | Live Sim Battle (Brawl) | TUO `brawl` mode; `effect` for global BGE |
| D→8 | Live Sim Battle (Guild War) | TUO `surge` mode; `yeffect`/`eeffect`/`effect` for BGE |
| D→9 | Optimize Deck vs Guild Defense (TUO) | TUO anneal (500 iter) vs all guild defenses |
| D→10 | Guild War Stats Tracker | Polls every 30 min; JSON + HTML snapshot |
| D→11 | Guild War Summary from JSON files | Generates summary HTML per guild+event group |
| D→12 | Guild War Auto-Pipeline 🚀 | Unattended GW run: 15-min countdown + Sync All Guild Decks; Q1 = TUO anneal vs own-guild gauntlet (one account at a time, all TUO threads); Q2+Q3 = build missing cards, set Slot 2, Live Sim GW (background, overlaps next Q1). BGEs activated at T-2:00 from `gw_bges_<Guild>.txt` |
| D→13 | Claim Daily Reward | Claims daily bonus for current account |
| D→14 | Claim Rewards – All Accounts | For all `play_enabled` accounts |
| D→15 | Play Highest Mission – All Accounts | Same for account range |
| D→16 | ↳ Clear Mission Blacklist (all accounts) | Clears skipped mission IDs for all accounts |
| D→17 | Play First Quest Mission – All Accounts | Per account: first quest mission until energy=0 |
| D→18 | Play Raid – All Accounts | Same for account range |
| D→19 | Multi-Account: Arena | Live Sim Arena; Loyal Challenge deck applied + restored per account |
| D→20 | Multi-Account: Brawl | Live Sim Brawl for account range |
| D→21 | Multi-Account: Guild War | Live Sim Guild War for account range; GW prep-phase guard |
| D→22 | Multi-Account: Raid + Quest Mission + Arena | Raid → Quest → Arena; Loyal Challenge deck applied + restored |
| D→23 | Multi-Account: Quest Mission + Arena | Quest → Arena; Loyal Challenge deck applied + restored |
| D→24 | Multi-Account: Brawl + Quest Mission + Arena | Brawl → Quest → Arena; Loyal Challenge deck applied + restored |
| D→25 | Energy Tracker (hourly log – Brawl/Mission/Arena) | Auto-detects Raid/Brawl/Guild Brawl; logs to `energylog/` |
| D→26 | Claim Daily Reward – All Accounts | Claims for all `play_enabled` accounts |
| D→27 | Refill Arena Stamina | Buys stamina refill token for current account |
| D→28 | Auto: Event + Quest Mission + Arena | Auto-detects Raid/Brawl from XML per loop pass; Brawl always logged; PvP Challenge deck for Arena; GW prep-phase guard |
| D→29 | Auto: Event + Quest Mission + Arena  (GW Pipeline) | GW phase prepended when `_gw_in_active_phase()` is True; then delegates to F→28 |

### E – Guild Management

| # | Name | Description |
|---|------|-------------|
| E→1 | Send Guild Message | Sends a message to the guild chat |
| E→2 | Leave Guild | Leaves the current guild |
| E→3 | Invite Player to Guild | Invites a player by name |
| E→4 | Accept Guild Invite | Accepts a pending guild invite |

### F – Settings & Maintenance

| # | Name | Description |
|---|------|-------------|
| F→1 | Update XML Files | Downloads all game XMLs (cards, missions, events, raids, …) and bges.txt |
| F→2 | TUO Threads |  |
| F→3 | database.yml |  |
| F→4 | Clear Old Gauntlet Entries (>7 days) | Removes arenagauntlet entries older than 7 days |
| F→5 | Scan Combat Logs for Unknown sim.cpp Flags | Scans combat logs for flags unknown to sim.cpp |

Settings (`F`) are part of the main menu; all submenus return with `0`.

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

All multi-account options offer 14 run modes (plus 0 = cancel). The account list is split into halves and quarters (rounded so every slice is non-empty); the menu prints the accounts of each slice before you choose.

| Choice | Behaviour |
|--------|-----------|
| 1 | All accounts, once |
| 2 | All accounts, loop (until ESC/Ctrl+C) |
| 3 | First half (Q1+Q2), once |
| 4 | First half (Q1+Q2), loop (until ESC/Ctrl+C) |
| 5 | Second half (Q3+Q4), once |
| 6 | Second half (Q3+Q4), loop (until ESC/Ctrl+C) |
| 7 | First quarter (Q1), once |
| 8 | First quarter (Q1), loop (until ESC/Ctrl+C) |
| 9 | Second quarter (Q2), once |
| 10 | Second quarter (Q2), loop (until ESC/Ctrl+C) |
| 11 | Third quarter (Q3), once |
| 12 | Third quarter (Q3), loop (until ESC/Ctrl+C) |
| 13 | Fourth quarter (Q4), once |
| 14 | Fourth quarter (Q4), loop (until ESC/Ctrl+C) |

---

## Key Features

### PvP Challenge System (D→19/22/23/24/28/29, A→7)

Automatically adapts Slot 1 deck for the active PvP Challenge step before arena battles, then restores the original deck. Runs fully unattended across all accounts.

**Challenge priority:**
1. Living Mirrors PVP Challenge (15 steps, Oct 27 – Nov 24, 2026 — only while `end_time` is in the future; time-limited, always first)
2. Forever Loyal PVP Challenge *(LEGACY — Aug 2026 one-time event)*
3. Extreme PVP Challenge (28 steps across 6 faction streams)
4. Enter the Arena PVP Challenge (8 steps)
5. Orbo Underground PVP Challenge (12 steps, Mythic Orbo required)
6. Dominate the Arena PVP Challenge (9 steps)
7. Progenitor Requiem PVP Challenge (13 steps)
8. Master the Arena PVP Challenge (8 steps)
9. Cutlass Unleashed PVP Challenge (4 steps)

**How it works:**

1. Detects the current challenge step via `getPvpChallengeData`
2. Checks if required commander is owned; auto-builds via `build_card(id)` if not
3. Builds required cards (upgrades via `build_card` if needed; skips if insufficient SP — logs issue, deck unchanged)
4. Builds pool cards: pass 1 takes the per-type count from the pool list (inventory first, then build); pass 2 tops up with additional copies of pool cards until `pool_min` is reached
5. Assembles the deck: copies of challenge cards already in the start deck are removed first, the challenge cards are added, and no card id is sent more often than `num_owned` (the server rejects the **whole** deck otherwise)
6. Writes the deck via `setDeckCards` and compares the returned cards with what was sent — any difference aborts the challenge deck and writes `pvp_challenge_issues.txt` (including the server `result_message`)
7. Re-activates the slot and prints a `[VERIFY]` line: commander and cards as actually stored on the server
8. Runs arena battles (`live_sim_battle`); card order is decided by the TUO flexible sim only (`play_first` keys in the tables have no effect)
9. Restores the original deck via `_restore_challenge_deck` (always, via `finally` block); the restore is verified the same way

**Abort conditions** (deck left unchanged):
- Required card cannot be built (SP/gold insufficient) → `return None, None` before any deck modification
- Server does not store the sent deck (card comparison fails) → issue logged, battles continue with the normal deck

Fewer than `pool_min` pool cards available → logged as issue, proceeds with the cards that are available.

**Extreme PVP Challenge:** parallel quest strands — sub-challenge detected by type-9 achievement name, not linear step counter. Only names from EXTREME_CHALLENGES table are accepted to avoid false matches with other challenge types.

**Living Mirrors PVP Challenge (Oct 27 – Nov 24, 2026):** 15 steps (`LIVING_MIRRORS_CHALLENGES`), checked before all other challenges while active. Win steps (Mirror 25/50/75/100) use a wins counter; skill steps use support commanders/pools: Octane Optimized (Rally/Entrap), Daedalus Charged (Enrage), Malort Blightfather (Heal), Fortify pool (Arcadia Redeemed, Experiment Gasher, The Mass, Impurity Arrester, Restore Sequencer; 4 copies), Overload pool (2 copies), Progenitor pool for Mirror Vindicated (4 copies).

**Issues log:** `export/pvp_challenge_issues.txt` — build failures, rejected decks (with server message), failed restores.

**Challenge analysis log:** `export/challenge_analysis.txt` — one result line per arena battle (complete deck, played cards, verdict, skillcheck, enemy) plus an indented `detail:` line (`copies_in_deck`, `first_in_hand_turn`, `first_played_turn`, pool usage, kills, damage, flags, action tally) and a `PROGRESS` line comparing server-side sub-challenge progress before/after (COUNTED / NOT COUNTED). `first_in_hand_turn=never` means the card was not drawn before the battle ended; in hand but `first_played_turn=never` is a TUO sim decision.

**Challenge Overview (F→24):** shows all accounts with step, sub-challenge name, progress, and end date. Highlights stagnating accounts (+0 between snapshots). Uses `_detect_loyal_challenge_step()` for consistency with battle selection.

### Diagnostic Log Files (`export/`)

| File | Content |
|------|---------|
| `pvp_challenge_issues.txt` | Challenge build/deck failures: missing cards, rejected decks (with server message), pool shortages, failed restores |
| `challenge_analysis.txt` | Per-battle challenge log with PROGRESS lines |
| `api_errors.log` | `timestamp \| account \| API call \| error type \| detail` — NetworkError, EmptyResponse, PleaseWait, InitIncomplete, InitFailed, MissionBlacklisted, MissionFallbackFailed, ArenaBattleFailed |
| `outdatedIDs_log.txt` | Every change to `outdatedIDs.txt` (manually added / manually removed / auto-removed equipped card) |

### Auto GBGE Detection (B→16/17)

Mission deck optimization (B→16 single account, B→17 all accounts) automatically reads the active Global Battleground Effect from `battleground_effects.xml`. If an active GBGE is found (current time within `global_start_time`/`global_end_time`), it is applied automatically with a 5-second notice — no manual input required. If no GBGE is active, the optimizer runs without one.

**XML name → TUO flag conversion:** names with spaces are hyphenated by default. Known overrides: `Overcharged` → `Overload all`, `Crackdown` → `Crackdown 2`, `Oath of Loyalty` → `Oath-Of-Loyalty`, `Enduring Rage` → `EnduringRage 2`, etc.

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

### v5.8 — October 2026 *(current)*

- **NEW** Living Mirrors PVP Challenge — `LIVING_MIRRORS_CHALLENGES` (15 steps, Oct 27 – Nov 24, 2026); checked first while `end_time` is in the future; support commanders/pools per skill; win steps via wins counter
- **NEW** Challenge analysis log `export/challenge_analysis.txt` — complete deck, played cards, verdict, skillcheck, detail line (`copies_in_deck`, `first_in_hand_turn`, `first_played_turn`, pool, kills, damage, flags, action tally), PROGRESS lines (server progress before/after, COUNTED / NOT COUNTED)
- **NEW** `[VERIFY]` console line after the deck update — commander and cards as stored on the server
- **NEW** API error log `export/api_errors.log` (`_write_api_error_log`) — network errors (each retry + final), empty responses, "please wait", failed init, mission blacklist/fallback failures, failed arena battle start; format: `timestamp | account | API call | error type | detail`
- **NEW** outdatedIDs change log `export/outdatedIDs_log.txt` — manual add/remove and automatic removal of equipped cards; `outdatedIDs.txt` is now written atomically (`.bak` backup, temp file + `os.replace`) via `_write_outdated_ids_safe`
- **NEW** Arena guild fallback — if only own-guild members remain as targets, their live decks are fetched (`_fetch_enemy_deck_live`) and pre-simmed; best live-deck target is used unless a known-deck target scored higher
- **NEW** Code map — section banners `[S01]`–`[S24]`, `[T01]`–`[T04]`, `[M01]`–`[M02]` and CODE MAP in the module docstring; `# FIX:` comments mark bug fixes
- **FIX** `setDeckCards` success check — commander-only comparison counted a rejected deck as success whenever the commander was unchanged (e.g. Extreme step 8); now sent vs. returned cards are compared, `result_message` logged, challenge deck aborted on mismatch
- **FIX** Challenge card already in the start deck (only 1 owned) was added twice → server answered "You do not have 2 of card X" and discarded the whole deck, so the challenge deck was never active (Rhilfen, Extreme step 8). Copies are now removed from the base deck first; no id is sent more often than `num_owned`
- **FIX** Pool build — per-type copy count capped at the pool list count (previously the first card was taken up to `pool_min` times); second pass tops up additional copies when `pool_min` is not reached; new-copy detection via counter
- **FIX** `_restore_challenge_deck` — success also requires matching cards; failed restore logged as "Deck RESTORE not applied"
- **FIX** `_verify_challenge_deck` — pool-only steps (no commander/required card, e.g. Extreme step 8) were skipped, so the pool check never ran; `pool_min` steps are now included (warning + issue log)
- **FIX** `initialize()` — a response without `user_data` (server overloaded, connection dropped) silently set energy/stamina to 0 and skipped all phases; now the account is skipped with an `InitIncomplete` entry in `api_errors.log`
- **FIX** `_fetch_enemy_deck_live` — stale guild-member cache: on a name miss the roster is re-read once, cache rebuilt, lookup repeated before reporting "left guild"
- **FIX** `play_highest_mission_loop` — fallback mission is never blacklisted; repeated failures stop the session (`MissionFallbackFailed`); blacklist output shortened to a count
- **FIX** `interactive_menu` option 95 — local `import glob as _glob` made `_glob` local for the whole function (UnboundLocalError in settings search)
- **FIX** `optimize_mission_deck` — NameError on auto-detected GBGE (check of a non-existent variable removed)
- **FIX** `get_player_info` — "Account Age" never shown (`date.today()` NameError swallowed); now `datetime.now().date()`
- **CHANGE** `PROGENITOR_REQUIEM_CHALLENGES` step 1 (Progenitor Reactor) — `pool_min` 6 → 4
- **CHANGE** ~50 lines of unreachable dead code removed in `play_first_quest_mission_loop`; 9 bare `except` around `int()` narrowed to `(ValueError, TypeError)` (`show_events`, `_gw_in_active_phase`)
- **CHANGE** `play_first` keys in challenge tables have no effect — card order is decided by the TUO flexible sim only
- **CHANGE** README/documentation updated to v5.8 (duplicate `battleground_effects.xml` row removed, file structure and challenge chapter completed)

### v5.7 — October 2026

- **FIX** Arena auto-target: if no target reaches ≥30% pre-sim win rate, the target with the **highest pre-sim win rate** is now chosen as fallback (previously: first known target from list)
- **FIX** Arena pre-sim threshold lowered from ≥50% to **≥30%** — better matches real performance when PvP Challenge deck (weaker cards) is active
- **FIX** Arena challenge deck applied **before** pre-sim — `_apply_challenge_deck` + `_verify_challenge_deck` now run before the pre-sim loop; correct commander and challenge cards are used in the simulation
- **FIX** `_ch_applied` guard prevents double-application of challenge deck when auto-select runs pre-sim (both auto-select and battle-start blocks guarded)
- **FIX** PvP Challenge Overview (F→24) — type-6 achievements now included; rank-suffix API names matched with `startswith` instead of exact match
- **FIX** `_detect_challenge_step` — same type-6 + `startswith` fix; correctly detects challenge step when API appends rank suffix to challenge name
- **FIX** Raid stale-XML detection — when local XML shows raid ended, `getRaidInfo` API is called to distinguish a still-active raid (leftover energy) from a truly finished one; `end_time` used as arbiter
- **FIX** Arena pre-sim deck built directly from `user_decks[arena_slot]` in `init_data` (after `_verify_challenge_deck` refresh); `flush=True` added to pre-sim progress prints

### v5.6 — September 2026

- **NEW** F→27 Refill Arena Stamina — buys stamina refill token; reads `max_stamina` from `init_data` with fallback 15
- **NEW** F→28 Auto: Event + Quest Mission + Arena — auto-detects Raid/Brawl from local XML per loop pass; Brawl always logged; PvP Challenge deck for Arena phase; GW prep-phase guard; raid drain after event end (leftover energy used)
- **NEW** F→29 Auto: Event + Quest Mission + Arena (GW Pipeline) — GW phase prepended when `_gw_in_active_phase()` is True
- **NEW** `_detect_active_event_from_xml()` — reads `raids_x42.xml` (`<raid>`) and `battle_events_h52.xml` (`<battle_event>`); child-element timestamps via `findtext()`; Raid checked before Brawl
- **NEW** `_gw_in_active_phase()` — reads `faction_wars_fp3.xml` (`<faction_war>`); child-element timestamps
- **NEW** XML downloads: `battle_events_h52.xml`, `raids_x42.xml`, `faction_wars_fp3.xml`, `event_box.xml`, `conquest.xml`, `mini_packs_36i.xml`, `assetbundles5_4_2.xml`, `assetbundles4_6.xml`
- **NEW** Challenge tables: `ENTER_THE_ARENA_CHALLENGES` (8), `ORBO_UNDERGROUND_CHALLENGES` (12, `MYTHIC_ORBO_ID=58573`), `DOMINATE_THE_ARENA_CHALLENGES` (9), `PROGENITOR_REQUIEM_CHALLENGES` (13)
- **NEW** `_AUTO_CONFIRM_INPUT` flag — suppresses `input_with_esc()` and `confirm_action()` prompts during pipeline deck builds; works on Windows (`msvcrt`-based input)
- **COMPLETE** `EXTREME_CHALLENGES` — all 28 steps with `desc`, `pvp`, `commander`, `pool`
- **COMPLETE** `MASTER_ARENA_CHALLENGES` — all 8 steps; `CUTLASS_CHALLENGES` — all 4 steps
- **LEGACY** `LOYAL_CHALLENGES` marked `# LEGACY (Aug 2026 one-time event)`
- **FIX** F→17 GW prep-phase guard added
- **FIX** All event XML parsing — child elements not attributes; correct tags: `<raid>`, `<battle_event>`, `<faction_war>`
- **FIX** `play_raid_loop(silent=True)` in pipeline — no start prompt
- **FIX** BGE: `Overcharged` → `Overload all` in `_api_bge_to_tuo()`
- **FIX** Issues log: `loyal_challenge_issues.txt` → `pvp_challenge_issues.txt`
- **FIX** Helper methods reconstructed after file corruption: `_collect_settings_files()`, `_load_setting()`, `_select_account_range()`
- **FIX** Duplicate menu entry "14. Refill Arena Stamina" removed
- **FIX** `claim_event_rewards` docstring: `claimGuildwarRewards` → `claimFactionWarRewards`

### v5.5 — August 2026


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

*TyrantAPICommander — October 2026 — v5.8*

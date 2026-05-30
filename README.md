# TyrantAPICommander

**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.

> May 2026 — v4.9

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
| `fusion_recipes_cj2.xml` | Fusion recipe database (`data/` folder) |
| `database.yml` | TUO database file (auto-managed, max ~310 MB) |

*Note: v4.7+ requires a custom-compiled tuo.exe with the hand-state patch. See TUO Build section.*

---

## File Structure

```
TUO-Live/
├── tuo.exe                     ← Custom-compiled TUO (hand-state patch)
├── TyrantAPICommander.py       ← Main script
├── generate_war_html.py        ← Standalone Guild War HTML generator
├── missions.xml
├── achievements.xml
├── items.xml
└── data/
    ├── settings_1.json         ← Account configuration
    ├── settings_2.json
    ├── settings/               ← Alternative: settings files in subfolder
    ├── arenagauntlet.txt       ← Defense deck database
    ├── attackdecks.txt         ← Attack deck database (auto-generated)
    ├── outdatedIDs.txt         ← Card IDs to salvage (shared)
    ├── import/                 ← Drop *.txt here for deck import (D→18)
    ├── ownedcards/             ← Inventory export target (all accounts)
    ├── export/                 ← Gauntlet output files
    ├── combatlog/              ← Per-account combat logs (Arena + Brawl)
    ├── energylog/              ← Hourly energy snapshots
    ├── guildwar_stats/         ← Guild War JSON + HTML snapshots
    ├── cards_section_*.xml
    ├── fusion_recipes_cj2.xml
    └── database.yml
```

---

## Menu Structure

| Submenu | Category | Key Features |
|---------|----------|--------------|
| **A** | Info & Events | Player info, active events, XML update, deck editor, guild members, quests |
| **B** | Inventory & Export | Export decks (slots 1–6), gauntlet management, sync guild defense + attack decks, Build Brawl Gauntlet (defense + attack) |
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
| 7 | Play Quest Missions (loop) | Quest-linked missions until energy depleted |
| 8 | Play First Quest Mission – All Accounts | Per account: first quest mission until energy=0 |
| 9 | Play Raid (auto+skip, loop) | Raid battles until battle energy empty; auto Slot 5 |
| 10 | Play Raid – All Accounts | Same for account range |
| 11 | Live Sim Battle (Arena) | TUO reorder; flexible auto; hand-state; optional combat log |
| 12 | Live Sim Battle (Brawl) | TUO `brawl` mode; hand-state; optional combat log |
| 13 | Live Sim Battle (Guild War) | TUO `gw` mode; hand-state; `yeffect`/`eeffect`/`effect` BGE |
| 14 | Optimize Deck vs Guild Defense | TUO anneal (500 iter) vs all guild defenses |
| 15 | Multi-Account: Arena | Live Sim Arena; deck restored after each account |
| 16 | Multi-Account: Brawl | Live Sim Brawl for account range |
| 17 | Multi-Account: Guild War | Live Sim Guild War for account range |
| 18 | Multi-Account: Raid + Quest Mission + Arena | Raid → Quest Mission → Arena; deck restored |
| 19 | Multi-Account: Quest Mission + Arena | Quest Mission → Arena; Arena combat log prompt (v4.8) |
| 20 | Multi-Account: Brawl + Quest Mission + Arena | Brawl → Quest Mission → Arena; log prompt N/b/a (v4.8) |
| 21 | Energy Tracker (hourly log) | Auto-detects Raid/Brawl; logs to `energylog/` |
| 22 | Guild War Stats Tracker | Polls every 30 min; JSON + HTML snapshot |
| 23 | Guild War Summary from JSON files | Generates summary HTML per guild+event group |
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

### Live Sim Battle

- **Arena** — `pvp` mode; flexible auto; hand-state; own-guild + skip-guild filter; deck restored after session
- **Brawl** — Slot 2 fixed; `brawl` mode (maximises brawl score); flexible auto; hand-state
- **Guild War** — `gw` mode (maximises GW score); `yeffect`/`eeffect`/`effect` for BGE; fort UID detection; hand-state
- **BGE conversion** — spaces removed (`Temporal Backlash` → `TemporalBacklash`); exception: `Oath of Loyalty` → `Oath-Of-Loyalty`

### BGE Flags

| TUO Flag | Meaning | Used in |
|----------|---------|---------|
| `effect` | Global BGE (both sides) | Arena, Brawl, global GW BGE |
| `yeffect` | Own faction BGE | Guild War (own faction only) |
| `eeffect` | Enemy faction BGE | Guild War (enemy faction only) |

In Guild War, all three flags can be active simultaneously.

### Hand-State (v4.7+)

At each battle turn, real-time card state is passed to TUO via `hand-state` and `enemy:hand-state`. Flags include HP, protect, attack buffs, poison, sunder, evolved skill offsets (8 pairs in v4.9), and all `enhance_*` values. Requires custom-compiled `tuo.exe` (see TUO Build section).

### Active Events Display (A→2)

- **Regular Brawl** — energy bar, current/regen, wasted count, player/guild leaderboard with ⭐ own-guild marker
- **Placement Brawl** — detected by `"placement"` in event name (e.g. *Wise Placements*); one-time 25-energy grant, no regen; single energy bar only; leaderboard always guild-based; info line shows GW relevance
- **Guild War** — ranking, match score, BGE, opponent; `faction_war_event_info` list/dict handled

### Multi-Account Combined Pipelines (F→18/19/20)

Active deck saved **before Phase 1** and restored after Arena completes for each account. Each phase pre-checks energy and skips gracefully if zero. Quest Mission always uses Slot 6.

### Combat Log (v4.6+)

Per-turn JSON logs written to `combatlog/` per account. Available for:

| Function | Prompt |
|----------|--------|
| F→11 Live Sim Arena | y/N at start |
| F→12 Live Sim Brawl | y/N at start |
| F→19 Quest + Arena | y/N before account loop (v4.8) |
| F→20 Brawl + Quest + Arena | N=none / b=Brawl only / a=Brawl+Arena (v4.8) |

Each log entry includes `own_states`, `enemy_states`, `api_card_states`, and `tuo_cmd`.

### Energy Tracker (F→21)

Auto-detects active event type each run:
- Raid active → reads `raid_info.energy.battle_energy`, cap 25
- Brawl active → reads `player_brawl_data.energy.battle_energy`, cap 25
- Otherwise → Mission energy from `user_data`

First snapshot taken immediately; subsequent snapshots every 60 minutes. Lines at 100% cap flagged with `!!`.

### Build Brawl Gauntlet (B→13 & 14)

**Defense gauntlet** — Smart multi-phase polling engine (ranks 1–100):
1. **Phase 1a** — Rank discovery (no leaderboard calls)
2. **Phase 1b** — Consensus poll: majority vote per rank; verified ties both enter rank_map
3. **Phase 1c** — Coverage top-up for remaining gaps
4. **Gap-fill** — Targeted retry; force-place fallback; `_placed_uids` guard
5. **Phase 2** — Deck lookup from `arenagauntlet.txt`

Option 13 (last brawl) reuses existing defense gauntlet from `export/` if available. Option 14 (current brawl) always rebuilds independently. Guild Brawl active → auto-fallback to `getPreviousBrawlTopLeaderboard`.

**Attack gauntlet** — auto-built at the end of every defense gauntlet run. Substitutes attack decks from `attackdecks.txt`. Output: `export/<brawl_key>_A.txt`.

### Sync All Guild Decks (B→11)

Single-pass sync: one `getProfileData` call per member reads both `defense_deck` and `attack_deck`. Each guild synced once per run across all connected accounts.

**Dedup passes after each sync:**
1. `WIN_`/`LOSS_` entries removed when a `GUILD_` entry exists for the same player (matching: `G == W` or `G.startswith(W + '_')`)
2. Guild-switch duplicates resolved — if a player appears under two different guild names, the earlier entry is removed

### Optimize Mission Deck (D→16 & 17)

Finds active quest mission → TUO climb → saves result to Slot 6.

Parameters: `pvp random -t N endgame 2 target 99 timeout 1 climb 50000 dom-owned no-db no-ml`

**Single-thread missions** (`-t 1`, `climb 10000`): Gore Typhon Enraged, Excelsitus Emerged

**Hardcoded enemy deck:** Infested Relay – Delirium (card 19333 causes TUO hang)

### Update Deck from Import (D→18)

Drop TUO result `.txt` into `import/`, pick file and slot. Matches accounts by normalised `kong_name` (top-level and `request_data` nested structure both supported). Runs Resolution Assistant automatically for missing cards. Incomplete accounts shown in summary.

Supported TUO output formats: Arena, Arena+stall, Raid, Brawl, Defense-stall.

### Salvage Outdated (D→10 & 19)

- Cards in any `user_decks` slot are **always skipped** (equipped-card guard)
- `user_cards` from the API already contains only regular inventory — no buyback subtraction needed
- Option 19 (All Accounts) runs without confirmation prompt

### Claim Event Rewards (F→1 & 2)

Auto-detects active event type. Guild War rewards use `claimFactionWarRewards` endpoint. All event types supported across all accounts.

---

## arenagauntlet.txt

```
//Last seen on: 2026-05-21 20:13
GUILD_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
WIN_PlayerName: Commander-1, Dominion-6, Card1-6, ...
LOSS_PlayerName: Commander-1, Dominion-6, Card1-6, ...
```

| Prefix | Meaning | Priority |
|--------|---------|----------|
| `GUILD_` | Synced from guild roster | Always beats WIN_/LOSS_ |
| `WIN_` | Beaten the player | Overrides LOSS_ |
| `LOSS_` | Lost against the player | Lowest priority |

`WIN_`/`LOSS_` are fallback entries for players outside any synced guild. As soon as a player joins a synced guild, their `WIN_`/`LOSS_` entry is removed and replaced by `GUILD_` on the next sync.

---

## attackdecks.txt

```
//Last seen on: 2026-05-21 20:13
ATTACK_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```

Generated and maintained by **B→11 Sync All Guild Decks**.

---

## settings_N.json

```json
{
  "user_id":           "12345678",
  "auth_token":        "abcdef1234567890",
  "user_agent":        "Mozilla/5.0 ...",
  "kong_name":         "AccountDisplayName",
  "play_enabled":      true,
  "mission_blacklist": [2301, 2305]
}
```

Also supported — nested `request_data` structure:

```json
{
  "request_data": {
    "user_id":   "12345678",
    "kong_name": "AccountDisplayName"
  },
  "user_agent":   "Mozilla/5.0 ...",
  "play_enabled": true
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `user_id` | — | Game user ID (required) |
| `auth_token` / `password` | — | Login token (required) |
| `user_agent` | — | Browser user agent (required) |
| `kong_name` | — | Display name; read from top-level or `request_data.kong_name` |
| `play_enabled` | `true` | Skip account in all multi-account operations if `false` |
| `mission_blacklist` | `[]` | Mission IDs permanently skipped by mission grind |

---

## TUO Custom Build — Hand-State Patch

Required since v4.7. Passes real-time card HP and status flags to TUO each turn.

### Build (Windows / MinGW-w64)

```bash
g++ -O2 -std=c++17 -o tuo.exe tyrant_optimize.cpp sim.cpp cards.cpp [...] \
    -lboost_program_options -lboost_regex
```

Install via MSYS2:
```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-boost
```

### Patched Files

| File | Change |
|------|--------|
| `tyrant_optimize.h` | `extern` declarations for `your_hand_state` / `enemy_hand_state` |
| `tyrant_optimize.cpp` | Define maps; implement `parse_hand_state()` with `#N` duplicate-card indexing |
| `sim.cpp` | Apply overrides in `Hand::reset()` — HP, flags, evolved skill offsets, enhanced values |

### Supported State Flags (v4.9)

`h` (HP), `protect`, `attack_boost`, `perm_max_health`, `avenge_attack`, `enfeeble`, `inhibited`, `jammed`, `jam_countdown`, `flurry_countdown`, `poison`, `sunder`, `enrage`, `add_skill_berserk`, `overloaded`, `stasis`, `entrap`, `add_skill_counter`, `tribute`, `sabotage`, `mark`, `disease`, `corrosive`, `corrosion`

**Evolved skill pairs (8):** `absorb→evade`, `weaken→sunder`, `pierce→rupture`, `swipe→drain`, `leech→refresh`, `siege→mortar`, `poison→venom`, `payback→revenge`

**Enhanced values:** `enhance_subdue`, `enhance_scavenge`, `enhance_berserk`, `enhance_avenge`, `enhance_leech`, `enhance_coalition`, `enhance_mark`, `enhance_venom`, `enhance_allegiance`, `enhance_inhibit`, `enhance_armored`, `enhance_legion`, `enhance_tribute`, `enhance_hunt`, `enhance_drain`, `enhance_stasis`, `enhance_swipe` and others

**Ignored (source-tracking only):** `corroder`, `poisoner`, `mimic_skill`

---

## Changelog

### v4.9 — May 2026 *(current)*

- **FIX** Sync All Guild Decks — WIN_/LOSS_ entries superseded by GUILD_ now removed automatically after each sync (exact-prefix matching, no false positives)
- **FIX** Sync All Guild Decks — Guild-switch duplicate GUILD_ entries resolved; earlier entry removed when player changes guild
- **FIX** Active Events — `faction_war_event_info` list vs dict handled correctly; prevented AttributeError crash
- **NEW** Active Events — Placement Brawl display: 🎯 icon, 25-energy bar (no regen/wasted), guild leaderboard, ⭐ own-guild marker with `user_data` fallback
- **FIX** Claim Event Rewards — endpoint corrected to `claimFactionWarRewards` (was `claimGuildwarRewards`)
- **FIX** Guild War Summary (F→23) — multiple NameErrors resolved (`_os`, `_glob`, `CSS`, `JS_INLINE`, `_dt`); `import glob as _glob` added as module-level alias; `JS_INLINE` promoted to class constant

### v4.8 — May 2026

- **FIX** Card state replace-per-card semantics — stale flags no longer carry over between turns
- **FIX** Field-value merge before sim call — `protect`, `attack_boost`, `flurry_countdown`, `corrosion` always current before TUO call
- **NEW** Combat log for Arena — available in F→19 (y/N prompt) and F→20 (N/b/a prompt)
- **NEW** sim.cpp — 6 new evolved skill pairs: absorb→evade, leech→refresh, siege→mortar, poison→venom, payback→revenge, swipe→drain
- **NEW** XML download — `achievements.xml` and `items.xml` added
- **FIX** `mimic_skill` added to SKIP_FLAGS (JSON object `{id, x, all}`, not int)

### v4.7 — May 2026

- **NEW** Hand-state / enemy:hand-state — full live card state passed to TUO each turn
- **NEW** Combat log (Brawl) — per-turn JSON with own/enemy states, api_card_states, tuo_cmd
- **NEW** Energy Tracker (F→21)
- **NEW** Scan combat logs for unknown sim.cpp flags (Settings)
- **FIX** Sync All Guild Decks — defense + attack combined in one pass (B→11); API calls halved
- **FIX** Build Brawl Gauntlet — attack gauntlet auto-built after every defense run; Options 13 & 14
- **FIX** sim.cpp — 12 new `enhance_*` flag mappings; `pierce_evolved_into_rupture` added

### v4.6 — April 2026

- **NEW** Initial hand-state support (HP + status flags)
- **NEW** Brawl combat logging
- **NEW** Energy Tracker prototype

### v4.4 — May 2026

- **NEW** Sync All Guild Attack Decks; Build Brawl Gauntlet Attack
- **NEW** Claim Daily Reward (F→25/26); Use Shards – All Accounts (D→20)
- **FIX** BGE flags: `yeffect`/`eeffect` for Guild War
- **FIX** TUO mode: Brawl → `brawl`, Guild War → `gw`
- **FIX** Mission name overrides (Albatross/Pandemonium → Mutant-10)
- **FIX** Infested Relay – Delirium hardcoded enemy deck

### v4.3 — May 2026

- **NEW** Deck slots 5 & 6; Optimize Mission Deck (D→16/17); Update Deck from Import (D→18); Salvage Outdated – All Accounts (D→19)

### v4.2 — May 2026

- **NEW** Change Attack/Defense Deck – All Accounts (D→15); Energy Tracker event detection
- **FIX** Multi-account deck save/restore; `setDeck` → `setDeckCards`

### v4.1 — April 2026

- **NEW** Multi-Account: Raid + Quest Mission + Arena (F→18/19)
- **FIX** Resolution Assistant: ingredients locked upfront; `_protected_card_ids`

### v4.0 — April 2026

- **NEW** Multi-Account: Brawl + Quest Mission + Arena (F→20); Energy Tracker (F→21)

### v2.0–v3.9 — February–April 2026

Guild War Stats Tracker & Summary, Live Sim Guild War, Build Brawl Gauntlet smart polling engine, Resolution Assistant, Gold→SP workflow, 6-category menu structure (A–F), multi-account loop modes, Raid event.

---

*TyrantAPICommander — May 2026 — v4.9*

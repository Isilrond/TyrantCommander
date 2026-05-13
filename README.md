# TyrantAPICommander

**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.

> May 2026 — v4.4

---

## Requirements

| Component | Details |
|-----------|---------|
| Python | 3.8–3.12 (PyInstaller does not support 3.13+) |
| `settings_N.json` | Account config with `user_id`, `auth_token`, `user_agent` |
| `tuo.exe` | TUO executable in parent folder (`../tuo.exe`) |
| `arenagauntlet.txt` | Known opponent defense decks (`data/` folder) |
| `attackdecks.txt` | Known attack decks for Brawl gauntlet (`data/` folder, auto-generated) |
| `cards_section_*.xml` | Card database (`data/` folder) |
| `missions.xml` | Mission database (`data/` folder) |
| `fusion_recipes_cj2.xml` | Fusion recipe database (`data/` folder) |
| `database.yml` | TUO database file (auto-managed, max ~310 MB) |

---

## File Structure

```
TUO-Live/
├── tuo.exe
├── TyrantAPICommander.py
├── generate_war_html.py        ← Standalone Guild War HTML generator
├── missions.xml
└── data/
    ├── settings_1.json
    ├── settings_2.json
    ├── settings/               ← Alternative: settings files in subfolder
    ├── arenagauntlet.txt
    ├── attackdecks.txt         ← Attack deck database (auto-generated)
    ├── outdatedIDs.txt
    ├── import/                 ← Drop *.txt here for Option 18
    ├── ownedcards/             ← Export target (all accounts)
    ├── export/                 ← Gauntlet output files
    ├── combatlog/
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
| 11 | Live Sim Battle (Arena) | TUO reorder; flexible auto; `effect` for global BGE |
| 12 | Live Sim Battle (Brawl) | TUO `brawl` mode; `effect` for global BGE |
| 13 | Live Sim Battle (Guild War) | TUO `gw` mode; `yeffect`/`eeffect`/`effect` for BGE |
| 14 | Optimize Deck vs Guild Defense | TUO anneal (500 iter) vs all guild defenses |
| 15 | Multi-Account: Arena | Live Sim Arena; deck restored after each account |
| 16 | Multi-Account: Brawl | Live Sim Brawl for account range |
| 17 | Multi-Account: Guild War | Live Sim Guild War for account range |
| 18 | Multi-Account: Raid + Quest Mission + Arena | Raid → Quest Mission → Arena; deck restored |
| 19 | Multi-Account: Quest Mission + Arena | Quest Mission → Arena; deck restored |
| 20 | Multi-Account: Brawl + Quest Mission + Arena | Brawl → Quest Mission → Arena; deck restored |
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

- **Arena** — flexible mode automatic; own-guild + skip-guild filter (`Predacons` excluded by default); deck restored after session
- **Brawl** — Slot 2 fixed; `brawl` mode (maximises brawl score); flexible auto-set in multi-account path
- **Guild War** — `gw` mode (maximises GW score); `yeffect`/`eeffect`/`effect` for BGE; fort UID detection
- **BGE conversion** — spaces removed by default (`Temporal Backlash` → `TemporalBacklash`); exception: `Oath of Loyalty` → `Oath-Of-Loyalty`

### BGE Flags (v4.4)

| TUO Flag | Meaning | Used in |
|----------|---------|---------|
| `effect` | Global BGE (both sides) | Arena, Brawl, global GW BGE |
| `yeffect` | Own faction BGE | Guild War (own faction only) |
| `eeffect` | Enemy faction BGE | Guild War (enemy faction only) |

In Guild War, all three flags can be active simultaneously.

### Multi-Account Combined Pipelines (F→18/19/20)

Active deck saved **before Phase 1** and restored after Arena completes for each account. Each phase pre-checks energy and skips gracefully if zero. Quest Mission always uses Slot 6.

### Energy Tracker (F→21)

Auto-detects active event type each run:
- Raid active → reads `raid_info.energy.battle_energy`, column: `Raid /25`
- Brawl active → reads `player_brawl_data.energy.battle_energy`, column: brawl name
- Otherwise → column: `Event /25`

### Build Brawl Gauntlet (B→13 & 15)

**Defense gauntlet (B→13)** — Smart multi-phase polling engine:
1. **Phase 1a** — Rank discovery (no leaderboard calls)
2. **Phase 1b** — Consensus poll: majority vote per rank; verified ties
3. **Phase 1c** — Coverage top-up for remaining gaps
4. **Gap-fill** — Targeted retry; force-place fallback; `_placed_uids` guard
5. **Phase 2** — Deck lookup from `arenagauntlet.txt`

Guild Brawl active → automatically falls back to `getPreviousBrawlTopLeaderboard`.

**Attack gauntlet (B→15)** — Uses existing defense gauntlet as rank source (Phase 1 skipped if file exists). Substitutes attack decks from `attackdecks.txt`. Output: `export/<brawl_key>_A.txt`.

### Sync All Guild Attack Decks (B→14)

Reads `attack_deck` from `getProfileData` for all guild members across all connected accounts. Each guild synced once per run. Writes `ATTACK_PlayerName_Guild: deck` to `attackdecks.txt`.

### Optimize Mission Deck (D→16 & 17)

Finds active quest mission → TUO climb with Slot 6 as seed → saves result to Slot 6.

Parameters: `pvp random -t N endgame 2 target 99 timeout 1 climb 50000 dom-owned no-db no-ml`

**Mission name overrides** (TUO uses different names than missions.xml):

| missions.xml name | TUO target |
|---|---|
| Albatross Endgame I–X | `Albatross Mutant-10` |
| Pandemonium Endgame I–X | `Pandemonium Mutant-10` |

**Single-thread missions** (use `-t 1`, `climb 10000`): Gore Typhon Enraged, Excelsitus Emerged

### Update Deck from Import (D→18)

Drop TUO result `.txt` into `import/`, pick file and slot. Matches accounts by normalised `kong_name` (supports both top-level and `request_data` nested structure). Runs Resolution Assistant automatically for missing cards. Incomplete accounts (no gold for SP) shown in summary.

Supported TUO output formats: Arena, Arena+stall, Raid, Brawl, Defense-stall.

### Salvage Outdated (D→10 & 19)

- Cards in any `user_decks` slot are **always skipped** (equipped-card guard)
- `user_cards` from the API already contains only regular inventory — no buyback subtraction needed
- Option 19 (All Accounts) runs cleanup for all accounts without confirmation prompt

### Change Attack/Defense Deck – All Accounts (D→15)

Sets any slot (1–6) as attack or defense deck for all `play_enabled` accounts. Checks `user_decks` for slot unlock status; lists unequipped accounts separately.

### Use Shards – All Accounts (D→20)

Uses all Epic/Legendary/Vindicator shard stacks for all `play_enabled` accounts. No confirmation prompt in multi-account mode.

### Update Deck (A→4)

- Accepts card names, `#count` syntax (`Daemon #3`), or raw numeric IDs
- Resolution Assistant activates when cards are missing: locks all ingredients upfront, builds fusion chain, runs Gold→SP workflow automatically
- Workflow aborts immediately if no SP progress (no gold left)

---

## arenagauntlet.txt

```
//Last seen on: 2026-05-01 14:23
WIN_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
LOSS_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
GUILD_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```

| Prefix | Meaning | Priority |
|--------|---------|----------|
| `WIN_` | Beaten the player | Newer timestamp wins vs `LOSS_` |
| `LOSS_` | Lost against the player | Newer timestamp wins vs `WIN_` |
| `GUILD_` | Synced from guild roster | Always beats `WIN_`/`LOSS_` |

---

## attackdecks.txt

```
//Last seen on: 2026-05-01 14:23
ATTACK_PlayerName_GuildName: Commander-1, Dominion-6, Card1-6, ...
```

Generated by **B → 14 Sync All Guild Attack Decks**.

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
| `auth_token` | — | Login token (required) |
| `user_agent` | — | Browser user agent (required) |
| `kong_token` | — | Kongregate token (optional) |
| `kong_name` | — | Display name; read from top-level or `request_data.kong_name` |
| `play_enabled` | `true` | Skip account in all multi-account operations if `false` |
| `mission_blacklist` | `[]` | Mission IDs permanently skipped by mission grind |

---

## Changelog

### v4.4 — May 2026 *(current)*

- **NEW** Sync All Guild Attack Decks (B→14): reads `attack_deck` from all guild members → `attackdecks.txt`
- **NEW** Build Brawl Gauntlet Attack (B→15/15b): attack gauntlet with `// Unknown decks` summary; Phase 1 skipped if defense gauntlet exists
- **NEW** Claim Daily Reward (F→25/26): single account and all accounts
- **NEW** Use Shards – All Accounts (D→20): auto-confirms for all accounts
- **FIX** BGE flags: `effect` for Arena/Brawl; `yeffect`/`eeffect`/`effect` for Guild War
- **FIX** TUO mode: Brawl → `brawl`, Guild War → `gw`
- **FIX** Mission name overrides extended to Roman numerals I–X (Albatross/Pandemonium Endgame → Mutant-10)
- **FIX** Infested Relay - Delirium: hardcoded enemy deck bypasses TUO hang
- **FIX** Workflow no-progress abort: stops immediately when no gold left
- **FIX** Import account matching: reads `kong_name` from `request_data` nested structure
- **FIX** Salvage Outdated: buyback logic fully removed; `user_cards` used directly
- **FIX** Import file parser: defense stall format `(X% stall)` correctly parsed

### v4.3 — May 2026

- **NEW** Deck Slots 5 (Raid, 200 WB) and 6 (Mission, 250 WB) integrated across all functions
- **NEW** Optimize Mission Deck → Slot 6 (D→16/17): TUO climb for active quest mission
- **NEW** Update Deck from Import File (D→18): all TUO output formats; auto Resolution Assistant
- **NEW** Salvage Outdated – All Accounts (D→19)
- **FIX** Salvage Outdated buyback handling rewritten
- **FIX** TUO card name resolution: base-name map for suffix-free TUO output
- **FIX** build_exe.bat: targets py -3.12 through py -3.9; skips unsupported 3.13+/3.14

### v4.2 — May 2026

- **NEW** Change Attack/Defense Deck – All Accounts (D→15): slots 1–6; slot unlock check
- **NEW** Energy Tracker: automatic event type detection (Raid / Brawl / Event)
- **NEW** Arena target skip-guild list (`Predacons` by default)
- **FIX** Multi-account combined (F→15/18/19/20): active deck saved before Phase 1, restored after Arena
- **FIX** Quest Mission: no longer forces Slot 1; uses currently active deck
- **FIX** Build Brawl Gauntlet: Guild Brawl fallback to `getPreviousBrawlTopLeaderboard`
- **FIX** Update Deck: `setDeck` → `setDeckCards` (deck saves now persist)
- **FIX** Salvage Outdated: equipped-card guard via `user_decks`; Energy Tracker list/dict guards

### v4.1 — April 2026

- **NEW** Multi-Account: Raid + Quest Mission + Arena (F→18)
- **NEW** Multi-Account: Quest Mission + Arena (F→19)
- **FIX** BGE name conversion applied to `yeffect` path
- **FIX** Resolution Assistant: all ingredients locked upfront; salvage functions respect `_protected_card_ids`
- **CHANGE** Build Brawl Gauntlet: consensus-based Phase 1b; `_placed_uids` guard; force-place fallback

### v4.0 — April 2026

- **NEW** Multi-Account: Brawl + Quest Mission + Arena (F→20)
- **NEW** Energy Tracker (F→21)
- **LEGACY** Pity the Fool PvP Challenge Runner (hidden, code preserved)

### v3.0 — April 2026

- **NEW** Unlock Commander (B→12)
- **NEW** Play First Quest Mission – All Accounts (F→8)
- **NEW** Update XML stat diff report; numeric ID input for deck editor
- **NEW** Arena own-guild filter

### v2.0–v2.9 — February–March 2026

Guild War Stats Tracker, Guild War Summary, Live Sim Guild War, Build Brawl Gauntlet smart polling engine, Resolution Assistant overhaul, Gold→SP workflow, 6-category menu structure (A–F), multi-account loop modes, Raid event full implementation.

---

*TyrantAPICommander — May 2026 — v4.4*

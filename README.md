# TyrantAPICommander

**Python-based automation tool for Tyrant Unleashed**  
Communicates directly via the official game API — no game client required.

> May 2026 — v4.2

---

## Requirements

| Component | Details |
|-----------|---------|
| Python | 3.8+ (no external libraries required) |
| `settings_N.json` | Account config with `user_id`, `auth_token`, `user_agent` |
| `tuo.exe` | TUO executable in parent folder (`../tuo.exe`) |
| `arenagauntlet.txt` | Known opponent decks (`data/` folder) |
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
    ├── import/                 ← Drop *.txt here for Option 10 merge
    ├── ownedcards/             ← Export target (all accounts)
    ├── export/                 ← Export target (guild decks, gauntlet)
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
| **A** | Info & Events | Player info, active events, XML update, deck editor, guild members |
| **B** | Inventory & Export | Export inventory/decks (single/all), gauntlet management, starterdeck export slots 1–4 |
| **C** | Guild Management | Sync decks, leave/invite/accept, Build Brawl Gauntlet |
| **D** | Economy | Buy packages, salvage, build card/dominion, buyback, unlock all, change attack/defense deck (all accounts) |
| **E** | Events & Rewards | Claim rewards, play missions/quests/raid (single & all accounts) |
| **F** | Automation & Battle | Live Sim (Arena/Brawl/GW), multi-account pipelines, energy tracker, guild war tracker, Pity the Fool |

Settings (`91`/`92`) accessible from main menu at any time.

---

## Automation & Battle (F) — All 24 Options

| # | Name | Description |
|---|------|-------------|
| 1 | Claim Rewards | Auto-detects and claims current event reward |
| 2 | Claim Rewards – All Accounts | Claims for all `play_enabled` accounts |
| 3 | Attack Next Free Player | Arena attack without TUO; skip-guild filter |
| 4 | Play Highest Mission (loop) | 3-star grind until energy empty |
| 5 | Play Highest Mission – All Accounts | Same as 4 for account range |
| 6 | ↳ Clear Mission Blacklist | Clears skipped mission IDs for all accounts |
| 7 | Play Quest Missions (loop) | Quest-linked missions until energy depleted |
| 8 | Play First Quest Mission – All Accounts | Per account: first quest mission until energy=0 |
| 9 | Play Raid (auto+skip, loop) | Raid battles until battle energy empty |
| 10 | Play Raid – All Accounts | Same as 9 for account range |
| 11 | Live Sim Battle (Arena) | TUO real-time simulation; flexible mode automatic |
| 12 | Live Sim Battle (Brawl) | TUO real-time Brawl simulation |
| 13 | Live Sim Battle (Guild War) | TUO surge mode |
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
| 24 | Pity the Fool — PvP Challenge Runner | Auto-runs all 10 Fool sub-challenges |

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
- **Brawl** — Slot 2 fixed; flexible mode auto-set even in multi-account path
- **Guild War** — TUO `surge` mode; BGE via `yeffect`/`eeffect`; fort UID detection
- **BGE conversion** — spaces removed by default (`Temporal Backlash` → `TemporalBacklash`); exception: `Oath of Loyalty` → `Oath-Of-Loyalty`

### Multi-Account Combined Pipelines (F→18/19/20)
Active deck saved **before Phase 1** and restored after Arena completes for each account. Quest Mission uses the currently active deck slot — no forced Slot 1 switch.

### Energy Tracker (F→21)
Auto-detects active event type each run:
- Raid active → reads `raid_info.energy.battle_energy`, column: `Raid /25`
- Brawl active → reads `player_brawl_data.energy.battle_energy`, column: brawl name
- Otherwise → column: `Event /25`

### Build Brawl Gauntlet (C→19)
Smart multi-phase polling engine:
1. **Phase 1a** — Rank discovery (no leaderboard calls)
2. **Phase 1b** — Consensus poll: majority vote per rank; verified ties
3. **Phase 1c** — Coverage top-up for remaining gaps
4. **Gap-fill** — Targeted retry; force-place fallback; `_placed_uids` guard
5. **Phase 2** — Deck lookup from `arenagauntlet.txt`

Guild Brawl active → automatically falls back to `getPreviousBrawlTopLeaderboard`.

### Salvage Outdated (D→10)
- Cards found in any `user_decks` slot (cards, commander, dominion) are **always skipped** — even if `num_used=0` (server-side corruption guard)
- Buyback IDs removed from working inventory map before processing

### Change Attack/Defense Deck – All Accounts (D→15)
Sets any slot (1–6) as attack or defense deck for all `play_enabled` accounts. Checks `user_decks` for slot unlock status; lists unequipped accounts separately.

### Update Deck (A→4)
- Accepts card names, `#count` syntax (`Daemon #3`), or raw numeric IDs
- Resolution Assistant activates when cards are missing: locks all ingredients upfront, builds fusion chain, runs Gold→SP workflow automatically

---

## arenagauntlet.txt

```
//Last seen on: 2026-04-07 14:23
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
| `kong_name` | — | Display name for export filenames |
| `play_enabled` | `true` | Skip account in all multi-account operations if `false` |
| `mission_blacklist` | `[]` | Mission IDs permanently skipped by mission grind |

---

## Changelog

### v4.2 — May 2026 *(current)*

- **NEW** Change Attack/Defense Deck – All Accounts (D→15): sets slot 1–6 as attack or defense for all accounts; slot unlock check via `user_decks`
- **NEW** Energy Tracker: automatic event type detection (Raid / Brawl / Event); reads Raid energy from `raid_info`
- **NEW** Arena target selection: configurable skip-guild list (`Predacons` by default)
- **FIX** Multi-account combined (F→15/18/19/20): active deck saved before Phase 1, restored after Arena — no longer lost through Quest Mission's Slot 1 switch
- **FIX** Quest Mission: no longer forces Slot 1; uses currently active deck
- **FIX** F→19 (Quest Mission + Arena): was returning "Invalid option" — dispatch entry added
- **FIX** Build Brawl Gauntlet: Guild Brawl active → falls back to `getPreviousBrawlTopLeaderboard`
- **FIX** Update Deck: switched from `setDeck` (not persisting) to `setDeckCards` with JSON count map
- **FIX** Salvage Outdated: equipped-card check now uses `user_decks` cross-reference (not `num_used` which can be 0 due to server corruption); buyback IDs excluded before processing
- **FIX** Energy Tracker: `list` vs `dict` guards for `user_data`, `player_brawl_data`, `raid_data`

### v4.1 — April 2026

- **NEW** Multi-Account: Raid + Quest Mission + Arena (F→18)
- **NEW** Multi-Account: Quest Mission + Arena (F→19)
- **FIX** BGE name conversion applied to `yeffect` path (live sim was using raw API names)
- **FIX** BGE default rule: spaces removed (not → hyphens); `Oath of Loyalty` exception kept
- **FIX** Resolution Assistant: all ingredients locked upfront; salvage functions respect `_protected_card_ids`
- **FIX** Automation menu option number mapping (14/15/16 were swapped)
- **CHANGE** Build Brawl Gauntlet: consensus-based Phase 1b; score-verified ties; unranked excluded from gap-fill; `_placed_uids` guard; force-place fallback

### v4.0 — April 2026

- **NEW** Pity the Fool PvP Challenge Runner (F→24)
- **NEW** Multi-Account: Brawl + Quest Mission + Arena (F→20)
- **NEW** Energy Tracker (F→21)
- **FIX** Arena Live Sim: flexible mode automatic; no inter-battle pause; own-guild fallback
- **FIX** Live Sim Brawl: flexible mode in multi-account path

### v3.0 — April 2026

- **NEW** Unlock Commander (B→12)
- **NEW** Play First Quest Mission – All Accounts (F→8)
- **NEW** Update XML stat diff report
- **NEW** Update Deck numeric ID input
- **NEW** Arena own-guild filter

### v2.9 — March 2026

- **NEW** Starterdeck export slots 3 & 4 (with unlock option)
- **FIX** Network retry on API calls
- **FIX** Buy Packages inventory pre-check

### v2.0–v2.8 — February–March 2026

Guild War Stats Tracker, Guild War Summary, Live Sim Guild War, Build Brawl Gauntlet smart polling engine, Resolution Assistant overhaul, Gold→SP workflow, 6-category menu structure (A–F), multi-account loop modes.

---

*TyrantAPICommander — May 2026 — v4.2*

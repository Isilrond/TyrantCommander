"""
Tyrant Unleashed API Commander - Standalone Version
Funktioniert OHNE tyrant-Modul (zeigt Karten-IDs statt Namen)

Haupt-Features:
  • Dominion Auto-Build - Automatischer Fusion-Pfad mit Reset-Support
  • Shop-Funktionen - 2000-Gold Pakete kaufen
  • Salvage-Funktionen - L1 Commons/Rares auf einmal salvagen
  • Buyback-Funktionen - Karten aus dem Buyback-Store zurückkaufen ⭐ NEU
  • Card-Building - Fusion-Rezepte mit SP-Kosten
"""

import json
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime
from time import sleep
import os
import sys
import hashlib
import logging
import time
import requests
import traceback

# ==================== EMBEDDED TyrantAPI ====================
# Die folgenden Klassen ersetzen das externe TyrantAPI-Modul

class TyrantAPISession(requests.Session):
    """Establish a session for Tyrant Unleashed's API."""
    
    def __init__(self, url, user_agent, *args, **kwargs):
        """Initialize the session.

        Parameters:
        ----------
        url : str
            The hostname to connect to.
        user_agent : str
            The user agent of the real client.
        """
        super().__init__(*args, **kwargs)

        self.headers = {
            'Host':             url,
            'User-Agent':       user_agent,
            'Accept':          '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type':    'application/x-www-form-urlencoded',
            'Origin':          'https://game208033.konggames.com',
            'Connection':      'keep-alive',
            'Referer':         'https://game208033.konggames.com/gamez/0020/8033/live/index.html?kongregate_game_version=1533748295&kongregate_host=www.kongregate.com',
        }


class TyrantAPI:
    """Provides a wrapper for named Tyrant Unleashed API calls."""

    def __init__(self, path, raw=False):
        """Initialize the API session.

        Parameters:
        ----------
        path : path-like
            The path to the JSON file containing the settings.
        raw : bool
            If raw=True, return the raw text of the response.
        """
        try:
            with open(path, 'r') as s:
                logging.debug(f'Settings loaded from: {s.name}')
                self.settings = json.loads(s.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Settings-Datei nicht gefunden: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültige JSON-Datei: {path}\nFehler: {e}")

        # Prüfe erforderliche Felder
        required_fields = ['request_data', 'url', 'user_agent']
        missing_fields = [field for field in required_fields if field not in self.settings]
        
        if missing_fields:
            raise ValueError(
                f"Fehlende Felder in Settings-Datei: {', '.join(missing_fields)}\n"
                f"Erforderlich: {', '.join(required_fields)}"
            )

        # Prüfe request_data Struktur
        required_request_fields = [
            'user_id', 'password', 'unity', 'client_version', 'syncode',
            'device_type', 'os_version', 'platform', 'kong_id', 'kong_token', 'kong_name'
        ]
        
        if 'request_data' in self.settings:
            missing_request_fields = [
                field for field in required_request_fields 
                if field not in self.settings['request_data']
            ]
            
            if missing_request_fields:
                raise ValueError(
                    f"Fehlende Felder in 'request_data': {', '.join(missing_request_fields)}\n"
                    f"Erforderlich: {', '.join(required_request_fields)}"
                )

        self.raw = raw
        self.req = self.settings['request_data']
        self.url = self.settings['url']

        self.session = TyrantAPISession(
            self.url,
            self.settings['user_agent']
        )

    def call(self, message, credentials=True, dummy=True, **kwargs):
        """Execute an arbitrary API call.

        Parameters:
        ---------- 
        message : str
            The API message, e.g. `updateFaction` or `playCard`.
        credentials : bool
            Whether to execute the API call as an logged-in user.
        dummy : bool
            Legacy parameter for some API calls.
        kwargs : dict
            Named parameters for the API call.
        """
        if credentials:
            url = f'https://{self.url}/api.php?message={message}&user_id={self.req["user_id"]}'
        else:
            url = f'https://{self.url}/api.php?message={message}'

        data = {
            'message':          message,
            'user_id':          self.req['user_id'],
            'password':         self.req['password'],
            'client_time':      (client_time := str(int(time.time()))),
            'client_signature': hashlib.md5(f'{client_time}{self.req["password"]}emJwaVK0HrTxVjIONHYH'.encode()).hexdigest(),
            'unity':            self.req['unity'],
            'client_version':   self.req['client_version'],
            'timestamp':        client_time,
            'hash':             hashlib.md5(f'TR&Q$K{self.req["user_id"]}{client_time}'.encode()).hexdigest(),
            'syncode':          self.req['syncode'],
            'device_type':      self.req['device_type'],
            'os_version':       self.req['os_version'],
            'platform':         self.req['platform'],
            'kong_id':          self.req['kong_id'],
            'kong_token':       self.req['kong_token'],
            'kong_name':        self.req['kong_name'],
            'data_usage':      '0',
        }

        if not credentials:
            del data['password']

        if dummy and not kwargs:
            data['dummy'] = 'data'
        else:
            data.update(kwargs)

        resp = self.session.post(url, data=data)

        logging.debug(f'Request headers: {resp.request.headers}')
        logging.debug(f'Request body: {resp.request.body}')

        if resp.status_code >= 400:
            raise RuntimeError('E{code}: request {body} received: {text}'.format(
                code=resp.status_code,
                body=resp.request.body,
                text=resp.text,
            ))

        return resp.text if self.raw else resp.json()

# ==================== END EMBEDDED TyrantAPI ====================

# Verzeichnis, in dem das Skript liegt  →  dort werden lokale XMLs gesucht
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== KONFIGURATION ====================

# Shop
PACK_ITEM_ID        = 48
PACK_ITEM_TYPE      = 3
PACK_COST           = 2000
DELAY_BETWEEN_BUYS  = 2          # Pause zwischen Käufen (Sekunden)

# Card-Daten: XML-Quellen
CARDS_BASE_URL      = "http://mobile.tyrantonline.com/assets/"
CARDS_SECTIONS      = 21         # cards_section_1.xml … cards_section_21.xml

# Upgrade-Materialien (werden bei Kartenzählung ignoriert)
UPGRADE_MATERIAL_IDS = {43451, 43452}

# Commander-Karten (werden bei Kartenzählung ignoriert)
COMMANDER_IDS = {
    1000, 1003, 1007, 1011, 1015, 1019, 1023, 1029, 1041, 1047,
    1053, 1059, 1099, 1105, 1119, 1181, 1187, 1193, 1199, 1205,
    1211, 1441, 1481, 1487, 1493, 1499, 1800, 1801, 1802, 1803,
    1804, 1805, 1806, 1807, 1808, 1809, 1810, 1811, 1812, 1813,
    1814, 1998, 25227, 25233, 25239, 25245, 25251, 25257, 25263, 25269,
    25275, 25281, 25287, 25293, 25299, 25305, 25311, 25578, 25584, 25590,
    25596, 25608, 25614, 25620, 25626, 25632, 25638, 25644, 25650, 25656,
    25662, 25668, 25674, 25680, 25686, 25692, 25698, 25704, 25710, 25716,
    25722, 25728, 25734, 25740, 25746, 25752, 26308, 26314, 26320, 26326,
    26332, 26338, 26344, 26350, 26356, 26362, 26368, 26374, 26380, 26386,
    26392, 26398, 26404, 26410, 26416, 26422, 26428, 26434, 26440, 26446,
    26494, 26500, 26506, 26512, 26518, 26524, 26530, 26536, 26542, 26548,
    26554, 26560, 26566, 26572, 26578,
}

# Dominion-Karten (werden bei Kartenzählung ignoriert)
# Bereiche: 50001-50236 und 50238-50359
DOMINION_IDS = set(range(50001, 50237)) | set(range(50238, 50360))

# Kombinierte Ausschluss-Liste
EXCLUDED_CARD_IDS = UPGRADE_MATERIAL_IDS | COMMANDER_IDS | DOMINION_IDS

# ---------- Dominion System: Vollständige Daten ----------

# Dominion Shard ID
DOMINION_SHARD_ID = 43452

# Dominion Fusion Recipes - Aus fusion_recipes_cj2.xml
# Format: source_id -> [(result_id, result_name, shard_cost), ...]
DOMINION_FUSIONS = {
    # Alpha Branch Tier 1: Alpha-2 -> Type
    50002: [
        (50003, 'Alpha Type-A', 50),
        (50081, 'Alpha Type-B', 50),
        (50159, 'Alpha Type-C', 50),
    ],
    # Alpha Branch Tier 2: Type-6 -> Named Level 1
    50008: [  # Alpha Type-A-6
        (50009, 'Alpha Bulwark', 110),
        (50015, 'Alpha Central', 110),
        (50021, 'Alpha Discovery', 110),
    ],
    50086: [  # Alpha Type-B-6
        (50087, 'Alpha Flag-bearer', 110),
        (50093, 'Alpha Blitz', 110),
        (50099, 'Alpha Fortress', 110),
    ],
    50164: [  # Alpha Type-C-6
        (50165, 'Alpha Proton', 110),
        (50171, 'Alpha Artillery', 110),
        (50177, 'Alpha Debilitate', 110),
    ],
    # Alpha Branch Tier 3: Named1-6 -> Named Level 2 (Final)
    50014: [  # Alpha Bulwark-6
        (50027, 'Alpha Defense Grid', 170),
        (50033, 'Alpha Shielding', 170),
        (50039, 'Alpha Hardened', 170),
    ],
    50020: [  # Alpha Central-6
        (50045, 'Alpha Muster', 170),
        (50051, 'Alpha Retainer', 170),
        (50057, 'Alpha Subjugator', 170),
    ],
    50026: [  # Alpha Discovery-6
        (50063, 'Alpha Replicant', 170),
        (50069, 'Alpha Breakthrough', 170),
        (50075, 'Alpha Regenerator', 170),
    ],
    50092: [  # Alpha Flag-bearer-6
        (50105, 'Alpha Ferocity', 170),
        (50111, 'Alpha Terror', 170),
        (50117, 'Alpha Advancer', 170),
    ],
    50098: [  # Alpha Blitz-6
        (50123, 'Alpha Serrated', 170),
        (50129, 'Alpha Dynamo', 170),
        (50135, 'Alpha Siphon', 170),
    ],
    50104: [  # Alpha Fortress-6
        (50141, 'Alpha Loyal', 170),
        (50147, 'Alpha Cooperator', 170),
        (50153, 'Alpha Ender', 170),
    ],
    50170: [  # Alpha Proton-6
        (50183, 'Alpha Disintegrator', 170),
        (50189, 'Alpha Seeker', 170),
        (50195, 'Alpha Terminus', 170),
    ],
    50176: [  # Alpha Artillery-6
        (50201, 'Alpha Bombard', 170),
        (50207, 'Alpha Calamity', 170),
        (50213, 'Alpha Thunder', 170),
    ],
    50182: [  # Alpha Debilitate-6
        (50219, 'Alpha Impostor', 170),
        (50225, 'Alpha Lockon', 170),
        (50231, 'Alpha Uniter', 170),
    ],
    # Nexus Branch Tier 1: Nexus-2 -> Faction
    50239: [
        (50240, 'Imperial Nexus', 50),
        (50264, 'Raider Nexus', 50),
        (50288, 'Bloodthirsty Nexus', 50),
        (50312, 'Xeno Nexus', 50),
        (50336, 'Righteous Nexus', 50),
    ],
    # Nexus Branch Tier 2: Faction-6 -> Named (Final)
    50245: [  # Imperial Nexus-6
        (50246, "Halcyon's Nexus", 110),
        (50252, "Octane's Nexus", 110),
        (50258, "Cassius' Nexus", 110),
    ],
    50269: [  # Raider Nexus-6
        (50270, "Barracus' Nexus", 110),
        (50276, "Yurich's Nexus", 110),
        (50282, "Silus' Nexus", 110),
    ],
    50293: [  # Bloodthirsty Nexus-6
        (50294, "Petrisis' Nexus", 110),
        (50300, "Dracorex's Nexus", 110),
        (50306, "Broodmother's Nexus", 110),
    ],
    50317: [  # Xeno Nexus-6
        (50318, "Kleave's Nexus", 110),
        (50324, "Kylen's Nexus", 110),
        (50330, "Krellus' Nexus", 110),
    ],
    50341: [  # Righteous Nexus-6
        (50342, "Empress' Nexus", 110),
        (50348, "Constantine's Nexus", 110),
        (50354, "Gaia's Nexus", 110),
    ],
}

# Upgrade-Kosten pro Tier (upgradeCard)
# Format: tier -> {level: shards}
DOMINION_TIER_UPGRADE_COSTS = {
    1: {  # Tier 1: Base -> L2 (via FUSION!)
        1: 50,  # L1->L2: 50 Shards via fuseCard (nicht upgradeCard!)
    },
    2: {  # Tier 2: Types/Factions L1->L6 (via upgradeCard)
        1: 60,   # L1->L2
        2: 70,   # L2->L3
        3: 80,   # L3->L4
        4: 90,   # L4->L5
        5: 100,  # L5->L6
        # L6->Next: 110 Shards via fuseCard (Tier 2->3 Fusion)
    },
    3: {  # Tier 3: Named Level 1 L1->L6 (via upgradeCard)
        1: 120,  # L1->L2
        2: 130,  # L2->L3
        3: 140,  # L3->L4
        4: 150,  # L4->L5
        5: 160,  # L5->L6
        # L6->Next (nur Alpha): 170 Shards via fuseCard (Tier 3->4 Fusion)
    },
    4: {  # Tier 4: Alpha Final Named L1->L6 (via upgradeCard, nur Alpha!)
        1: 180,  # L1->L2
        2: 190,  # L2->L3
        3: 200,  # L3->L4
        4: 210,  # L4->L5
        5: 220,  # L5->L6
        # ENDE - Nexus endet bei Tier 3, Alpha endet bei Tier 4
    }
}

# Fusion-Kosten zwischen Tiers (fuseCard, NICHT upgradeCard!)
# Format: from_tier -> to_tier: shards
DOMINION_FUSION_COSTS = {
    (1, 2): 50,   # Tier 1->2: Base-2 -> Type/Faction (50 Shards)
    (2, 3): 110,  # Tier 2->3: Type/Faction-6 -> Named1 (110 Shards)
    (3, 4): 170,  # Tier 3->4: Named1-6 -> Named2 (170 Shards, nur Alpha!)
}

# Dominion Branch Detection
# Alpha Branch: 50001-50237
# Nexus Branch: 50238-50359
ALPHA_RANGE = range(50001, 50238)
NEXUS_RANGE = range(50238, 50360)

# Basis-IDs für Branches
# WICHTIG: Nach Reset erhält man direkt Level 2 (nicht Level 1!)
# Level 1 Versionen (50001, 50238) existieren nicht im Spiel
ALPHA_BASE_IDS = {50002}  # Alpha Dominion-2 (nach Reset)
NEXUS_BASE_IDS = {50239}  # Nexus Dominion-2 (nach Reset)

# ---------- Dominion Helper-Funktionen ----------

def get_dominion_branch(card_id):
    """
    Bestimmt Branch eines Dominions
    
    Returns:
        'alpha' oder 'nexus' oder None
    """
    if card_id in ALPHA_RANGE:
        return 'alpha'
    elif card_id in NEXUS_RANGE:
        return 'nexus'
    return None

def get_dominion_tier(card_id):
    """
    Bestimmt Tier eines Dominions (1-4)
    
    Tiers:
        1: Base (Alpha/Nexus-1 und -2)
        2: Types/Factions
        3: Named Level 1
        4: Alpha Final Named (nur Alpha Branch)
    
    Returns:
        int (1-4) oder None
    """
    # Base IDs
    if card_id in ALPHA_BASE_IDS or card_id in NEXUS_BASE_IDS:
        return 1
    
    # Alpha Branch Tiers
    if card_id in ALPHA_RANGE:
        # Tier 2: Types (50003-50008, 50081-50086, 50159-50164)
        if (50003 <= card_id <= 50008) or (50081 <= card_id <= 50086) or (50159 <= card_id <= 50164):
            return 2
        # Tier 3: Named Level 1 (all 6 levels of each)
        # Bulwark, Central, Discovery, Flag-bearer, Blitz, Fortress, Proton, Artillery, Debilitate
        elif (50009 <= card_id <= 50014) or (50015 <= card_id <= 50020) or (50021 <= card_id <= 50026) or \
             (50087 <= card_id <= 50092) or (50093 <= card_id <= 50098) or (50099 <= card_id <= 50104) or \
             (50165 <= card_id <= 50170) or (50171 <= card_id <= 50176) or (50177 <= card_id <= 50182):
            return 3
        # Tier 4: Final Named Dominions (all others)
        else:
            return 4
    
    # Nexus Branch Tiers
    elif card_id in NEXUS_RANGE:
        # Tier 2: Factions (50240-50245, 50264-50269, etc.)
        if (50240 <= card_id <= 50245) or (50264 <= card_id <= 50269) or \
           (50288 <= card_id <= 50293) or (50312 <= card_id <= 50317) or \
           (50336 <= card_id <= 50341):
            return 2
        # Tier 3: Named (Final für Nexus)
        else:
            return 3
    
    return None

def get_fusion_cost_between_tiers(from_tier, to_tier):
    """
    Gibt Fusion-Kosten zwischen zwei Tiers zurück
    
    Args:
        from_tier: Aktueller Tier (1-3)
        to_tier: Ziel-Tier (2-4)
    
    Returns:
        int: Shard-Kosten oder None wenn ungültig
    """
    return DOMINION_FUSION_COSTS.get((from_tier, to_tier))

def is_fusion_available(card_id):
    """
    Prüft ob eine Karte fusioniert werden kann
    
    Args:
        card_id: Card ID
    
    Returns:
        bool: True wenn Fusion möglich
    """
    return card_id in DOMINION_FUSIONS

# ---------- Fusion-Material-Gruppen (für ownedcards.txt) ----------
# Muster: Wildcard am Ende, wird mit str.startswith() geprüft

FUSION_GROUPS = [
    ("Vindicator Reactors",      ["Vindicator Reactor"]),
    ("Bloodthirsty base fusion", ["Draconian Queen", "Smog Tank", "Blight Crusher",
                                  "Blood Pool", "Sinew Feeder", "Malgoth"]),
    ("Imperial base fusion",     ["Tiamat", "Aegis", "Windreaver",
                                  "Absorption Shield", "Blackrock", "Nimbus"]),
    ("Raider base fusion",       ["Havoc", "Bulldozer", "Iron Maiden",
                                  "Missile Silo", "Demon of Embers", "Omega"]),
    ("Righteous base fusion",    ["Vigil", "Contaminant Scour", "Equalizer",
                                  "Sanctuary", "Falcion", "Benediction"]),
    ("Xeno base fusion",         ["Dreadship", "Xeno Mothership", "Daemon",
                                  "Genetics Pit", "Lurker Beast", "Apex"]),
]

# Rarity-Namen für lesbare Ausgabe
RARITY_NAMES = {
    1: "Common",
    2: "Rare", 
    3: "Epic",
    4: "Legendary",
    5: "Vindicator",
    6: "Mythic"
}

# Buyback-Kosten basierend auf Seltenheit und Tier
# Format: (rarity, tier) -> SP-Kosten
# Commons (1) und Rares (2) gibt es NICHT im Buyback-Store
BUYBACK_COSTS = {
    # Epic (Rarity 3)
    (3, 0): 20,
    (3, 1): 80,
    (3, 2): 180,
    # Legendary (Rarity 4)
    (4, 0): 40,
    (4, 1): 150,
    (4, 2): 310,
    # Vindicator (Rarity 5)
    (5, 0): 80,
    (5, 1): 300,
    (5, 2): 500,
    # Mythic (Rarity 6)
    (6, 0): 120,
    (6, 1): 400,
    (6, 2): 1400,
}

# =====================================================================

class TyrantCommander:
    """Hauptklasse für API-Operationen - Standalone Version"""
    
    def __init__(self, settings_path):
        """
        Initialisiert die API-Verbindung
        
        Args:
            settings_path: Pfad zur Settings-JSON-Datei
        """
        self.api = TyrantAPI(settings_path)
        self.init_data = None
        self._card_data_cache  = None
        self._card_data_with_rarity_cache = None  # Cache für Buyback
    
    def initialize(self, verbose=False):
        """
        Lädt die Initialisierungsdaten
        
        Args:
            verbose: Wenn True, zeigt Verbindungsmeldungen (nur beim ersten Start)
        """
        try:
            if verbose:
                print("⏳ Verbinde mit API...")
            self.init_data = self.api.call('init')
            if verbose:
                print("✓ API-Verbindung erfolgreich initialisiert")
                print("✓ Login-Daten sind korrekt")
            return True
        except ValueError as e:
            # Settings-Datei Fehler
            print(f"✗ Fehler in Settings-Datei: {e}")
            return False
        except ConnectionError as e:
            print(f"✗ Verbindungsfehler: {e}")
            print("  → Prüfe deine Internet-Verbindung")
            return False
        except RuntimeError as e:
            # API-Fehler (z.B. 400, 403, etc.)
            error_msg = str(e)
            print(f"✗ API-Fehler: {error_msg}")
            
            if "403" in error_msg or "401" in error_msg:
                print("  → Login-Daten sind ungültig oder abgelaufen!")
                print("  → Erstelle eine neue Settings-Datei mit aktuellen Daten")
            elif "404" in error_msg:
                print("  → API-Endpunkt nicht gefunden")
                print("  → Prüfe die 'url' in der Settings-Datei")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                print("  → Server-Problem")
                print("  → Versuche es später erneut")
            
            return False
        except Exception as e:
            print(f"✗ Unerwarteter Fehler bei der Initialisierung: {e}")
            print(f"  Fehlertyp: {type(e).__name__}")
            return False
    
    # ==================== SPIELER-INFORMATIONEN ====================
    
    def get_player_info(self):
        """Zeigt eigene Spielerinformationen"""
        if not self.init_data:
            self.initialize()
        
        player = self.init_data['user_data']
        caps = player.get('caps', {})
        
        # Kartenplätze berechnen (nur user_cards, buyback_data nicht relevant)
        user_cards = self.init_data.get('user_cards', {})
        
        # Karten in Decks auch zählen
        user_decks = self.init_data.get('user_decks', {})
        deck_cards = 0
        for deck in user_decks.values():
            cards_dict = deck.get('cards', {})
            for count in cards_dict.values():
                deck_cards += int(count)
        
        # Berechnung der Kartenanzahl
        # WICHTIG: Upgradematerialien, Commanders und Dominions werden ignoriert
        # WICHTIG: Deck-Karten sind bereits in user_cards enthalten!
        import math
        
        # Karten zählen (Deck-Karten NICHT extra addieren - sind schon in user_cards!)
        total_cards = sum(int(info.get('num_owned', 0))
                         for card_id, info in user_cards.items()
                         if int(card_id) not in EXCLUDED_CARD_IDS)
        
        max_cards = int(caps.get('max_cards', 0))
        
        # League Points (nicht XP!)
        league_points = int(player.get('league_points', 0))
        next_level_lp = int(player.get('next_level_lp', 0))
        prev_level_lp = int(player.get('prev_level_lp', 0))
        
        print("\n" + "="*50)
        print("SPIELER-INFORMATIONEN")
        print("="*50)
        
        # Basis-Info
        print(f"Name:           {player.get('name', 'N/A')}")
        print(f"User ID:        {player.get('user_id', 'N/A')}")
        print(f"Level:          {player.get('level', 'N/A')} ({player.get('level_name', 'N/A')})")
        print(f"League Points:  {league_points:,} / {next_level_lp:,}")
        
        print("\n" + "─"*50)
        print("WÄHRUNGEN")
        print("─"*50)
        print(f"Gold:           {int(player.get('money', 0)):,}")
        print(f"WB:             {int(player.get('tokens', 0)):,}")
        print(f"SP:             {int(player.get('salvage', 0)):,} / {int(caps.get('max_salvage', 0)):,}")
        
        print("\n" + "─"*50)
        print("ENERGIE")
        print("─"*50)
        print(f"Arena Energy:   {int(player.get('stamina', 0))}")
        print(f"Stamina:        {int(player.get('energy', 0))}")
        
        # Zeige Event Energy statt Battle Energy
        active_brawl = self.init_data.get('active_brawl_data')
        player_brawl = self.init_data.get('player_brawl_data')
        
        if active_brawl and player_brawl:
            event_name = active_brawl.get('name', 'Event')
            brawl_energy = player_brawl.get('energy', {})
            current_energy = int(brawl_energy.get('battle_energy', 0))
            max_energy = int(brawl_energy.get('max_battle_energy', 25))
            rank = player_brawl.get('current_rank', '?')
            points = int(player_brawl.get('points', 0))
            
            print(f"\n{event_name}:")
            print(f"  Energy:       {current_energy}/{max_energy}")
            print(f"  Rank:         #{rank}")
            print(f"  Points:       {points:,}")
        else:
            # Fallback: zeige alte Battle Energy
            print(f"Battle Energy:  {int(player.get('battle_energy', 0))}")
        
        print("\n" + "─"*50)
        print("KARTEN")
        print("─"*50)
        print(f"Belegt:         {total_cards:,} / {max_cards:,}")
        print(f"Freie Slots:    {max_cards - total_cards:,}")
        
        print("\n" + "─"*50)
        print("GILDE")
        print("─"*50)
        if 'faction' in self.init_data:
            faction = self.init_data['faction']
            print(f"Name:           {faction.get('name', 'N/A')}")
            print(f"ID:             {player.get('faction_id', 'N/A')}")
        else:
            print("Keine Gilde")
        
        print("="*50 + "\n")
        
    def calculate_max_packs(self):
        """
        Berechnet maximale Anzahl an Paketen die gekauft werden können
        basierend auf freien Kartenslots
        
        Logik:
        - Freie Slots berechnen
        - Durch 20 teilen (jedes Paket hat 20 Karten)
        - Abrunden auf ganze Zahl
        
        Beispiel: 546 freie Slots / 20 = 27.3 -> 27 Pakete
        
        Returns:
            tuple: (max_packs, free_slots)
        """
        if not self.init_data:
            self.initialize()
        
        player = self.init_data['user_data']
        caps = player.get('caps', {})
        user_cards = self.init_data.get('user_cards', {})
        
        # Karten zählen (ohne Upgradematerialien, Commanders, Dominions)
        total_cards = sum(int(info.get('num_owned', 0))
                         for card_id, info in user_cards.items()
                         if int(card_id) not in EXCLUDED_CARD_IDS)
        
        max_cards = int(caps.get('max_cards', 0))
        free_slots = max_cards - total_cards
        
        # Durch 20 teilen und abrunden
        # z.B. 546 slots / 20 = 27.3 -> 27 Pakete
        max_packs = int(free_slots / 20)
        
        return max_packs, free_slots
    
    def get_profile(self, user_id):
        """
        Holt Profil eines anderen Spielers
        
        Args:
            user_id: User-ID des Spielers
        """
        try:
            profile = self.api.call('getProfileData', target_user_id=str(user_id))
            player_info = profile['player_info']
            
            print(f"\n=== PROFIL: {player_info['name']} ===")
            print(f"Level: {player_info['level']}")
            print(f"Guild: {player_info.get('faction_name', 'Keine')}")
            print(f"PvP Rating: {player_info.get('rating', 'N/A')}")
            
            return profile
        except Exception as e:
            print(f"✗ Fehler beim Laden des Profils: {e}")
            return None
    
    # ==================== GILDEN-MANAGEMENT ====================
    
    def update_xmls(self):
        """Lädt alle XML-Dateien neu herunter"""
        print("\n" + "="*60)
        print("XML-DATEIEN AKTUALISIEREN")
        print("="*60)
        
        base_url = "http://mobile.tyrantonline.com/assets/"
        
        # Liste aller Dateien
        files_to_download = [
            # Basis-XMLs
            ("fusion_recipes_cj2.xml", base_url + "fusion_recipes_cj2.xml"),
            ("skills_set.xml", base_url + "skills_set.xml"),
            ("missions.xml", base_url + "missions.xml"),
            ("levels.xml", base_url + "levels.xml"),
        ]
        
        # Card sections 1-21 (bekannt vorhanden)
        for i in range(1, 22):
            filename = f"cards_section_{i}.xml"
            files_to_download.append((filename, base_url + filename))
        
        # Card section 22 (optional - könnte kommen)
        files_to_download.append(("cards_section_22.xml", base_url + "cards_section_22.xml"))
        
        # GitHub-Dateien
        files_to_download.extend([
            ("bges.txt", "https://raw.githubusercontent.com/APN-Pucky/tyrant_optimize/master/data/bges.txt"),
            ("raids.xml", "https://raw.githubusercontent.com/APN-Pucky/tyrant_optimize/master/data/raids.xml"),
        ])
        
        print(f"\nDateien zum Download: {len(files_to_download)}")
        print(f"Zielverzeichnis: {SCRIPT_DIR}\n")
        
        # Bestätigung
        if not confirm_action("Alle XML-Dateien neu herunterladen?"):
            print("Abgebrochen")
            return
        
        print("\n" + "─"*60)
        print("DOWNLOAD STARTET")
        print("─"*60)
        
        downloaded = 0
        skipped = 0
        failed = 0
        
        for filename, url in files_to_download:
            filepath = os.path.join(SCRIPT_DIR, filename)
            
            # Alte Datei löschen falls vorhanden
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"⚠ Konnte alte Datei nicht löschen: {filename} ({e})")
            
            # Download
            print(f"⏳ {filename:<30} ", end='', flush=True)
            
            try:
                with urlopen(url, timeout=10) as response:
                    if response.status == 200:
                        content = response.read()
                        
                        # Speichern
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        size_kb = len(content) / 1024
                        print(f"✓ ({size_kb:.1f} KB)")
                        downloaded += 1
                    else:
                        print(f"✗ HTTP {response.status}")
                        failed += 1
                        
            except URLError as e:
                # 404 ist OK für cards_section_22.xml
                if "404" in str(e) and filename == "cards_section_22.xml":
                    print(f"⊘ Noch nicht vorhanden (404)")
                    skipped += 1
                else:
                    print(f"✗ Fehler: {e}")
                    failed += 1
            except Exception as e:
                print(f"✗ Fehler: {e}")
                failed += 1
            
            # Rate limiting (nicht zu schnell)
            sleep(0.2)
        
        # Zusammenfassung
        print("\n" + "─"*60)
        print("DOWNLOAD ABGESCHLOSSEN")
        print("─"*60)
        print(f"✓ Erfolgreich:  {downloaded}")
        print(f"⊘ Übersprungen: {skipped} (cards_section_22.xml)")
        print(f"✗ Fehlgeschlagen: {failed}")
        print(f"\nDateien gespeichert in: {SCRIPT_DIR}")
        print("="*60 + "\n")
    
    
    def list_guild_members_with_rating(self):
        """
        Listet alle Gildenmitglieder mit Player ID, Name und Rating auf
        Am Ende wird die Summe aller Ratings angezeigt
        """
        if not self.init_data:
            self.initialize()
        
        if 'faction' not in self.init_data:
            print("✗ Nicht in einer Gilde")
            return []
        
        faction_name = self.init_data['faction']['name']
        members = self.init_data['faction']['members']
        
        print("\n" + "="*60)
        print(f"GILDENMITGLIEDER: {faction_name}")
        print("="*60)
        print(f"Anzahl Mitglieder: {len(members)}")
        print("\n⏳ Lade Mitglieder-Daten...\n")
        
        member_list = []
        total_rating = 0
        
        for i, member_id in enumerate(members, 1):
            try:
                profile = self.api.call('getProfileData', target_user_id=str(member_id))
                player_info = profile['player_info']
                
                name = player_info['name']
                level = player_info['level']
                rating = int(player_info.get('rating', 0))
                
                member_data = {
                    'id': member_id,
                    'name': name,
                    'level': level,
                    'rating': rating
                }
                
                # Ausgabe: Nr. Name (ID) - Level - Rating
                # Mit Tabstops für schöne Ausrichtung
                print(f"{i:2}. {name} ({member_id})\t\tLvl {level:3}\t\tRating: {rating:,}")
                
                member_list.append(member_data)
                total_rating += rating
                
                # Rate limiting
                sleep(0.3)
                
            except Exception as e:
                print(f"{i:2}. ID {member_id} - ✗ Fehler: {e}")
        
        # Zusammenfassung
        print("\n" + "─"*60)
        print("ZUSAMMENFASSUNG")
        print("─"*60)
        print(f"Geladene Mitglieder:  {len(member_list)} / {len(members)}")
        print(f"Gesamt-Rating:        {total_rating:,}")
        if len(member_list) > 0:
            avg_rating = total_rating / len(member_list)
            print(f"Durchschnitts-Rating: {avg_rating:,.1f}")
        print("="*60)
        
        return member_list
    
    def send_guild_message(self, message_text):
        """
        Sendet eine Nachricht an die Gilde (sendFactionMessage)
        
        Args:
            message_text: Nachrichtentext
        """
        try:
            if not message_text or not message_text.strip():
                print("✗ Keine Nachricht eingegeben")
                return None
            
            print("\n" + "="*60)
            print("GILDENNACHRICHT SENDEN")
            print("="*60)
            print(f"\nNachricht: \"{message_text}\"")
            
            print("\n⏳ Sende Nachricht...")
            # Parameter: chat = Nachrichtentext
            # Optional: last_activity_id (falls vorhanden in init_data)
            kwargs = {'chat': message_text}
            
            # Füge last_activity_id hinzu falls vorhanden
            if self.init_data and 'last_activity_id' in self.init_data:
                kwargs['last_activity_id'] = str(self.init_data['last_activity_id'])
            
            result = self.api.call('sendFactionMessage', **kwargs)
            
            if result and result.get('result') == True:
                print("✓ Gildennachricht erfolgreich gesendet!")
            else:
                print("✗ Fehler beim Senden der Nachricht")
                if result:
                    print(f"   API Response: {result}")
            
            print("="*60)
            return result
            
        except Exception as e:
            print(f"✗ Fehler beim Senden der Nachricht: {e}")
            traceback.print_exc()
            return None
    
    # ==================== DECK-MANAGEMENT ====================
    
    def get_decks(self, user_id=None):
        """
        Zeigt eigene Decks im currentdecks.txt Format in der Shell
        Identisch zu Punkt 6 Export, aber ohne Datei zu erstellen
        """
        try:
            if not self.init_data:
                self.initialize()
            
            print("\n" + "="*60)
            print("EIGENE DECKS")
            print("="*60)
            
            # Card-Daten laden
            print("⏳ Lade Card-Daten...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Kann ohne Card-Daten nicht fortfahren.")
                return None
            
            user_decks = self.init_data.get('user_decks', {})
            # WICHTIG: Verwende 'active_deck' und 'defense_deck' (ohne _id)!
            active_deck = str(self.init_data.get('user_data', {}).get('active_deck', ''))
            defense_deck = str(self.init_data.get('user_data', {}).get('defense_deck', ''))
            
            print(f"✓ {len(card_data)} Karten geladen")
            print("\n" + "─"*60)
            
            deck_count = 0
            for deck_id, deck in user_decks.items():
                # Deck-Name (gleich wie in currentdecks.txt)
                deck_name = deck.get('name') or f"Deck{deck_id}"
                
                # Markierungen [A] für Active, [D] für Defense
                marks = []
                if str(deck_id) == active_deck:
                    marks.append("A")
                if str(deck_id) == defense_deck:
                    marks.append("D")
                mark_str = f" [{'/'.join(marks)}]" if marks else ""
                
                # Commander
                commander = self._resolve_card(deck.get('commander_id', '0'), card_data)
                
                # Dominion (optional)
                dominion_id = deck.get('dominion_id')
                dominion = self._resolve_card(dominion_id, card_data) if dominion_id else ""
                
                # Cards mit Anzahl
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    cname = self._resolve_card(cid, card_data)
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)
                
                # Zeile zusammenbauen: Name[Mark]:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)
                
                line = f"{deck_name}{mark_str}:{','.join(parts)}"
                
                # Ausgabe
                print(line)
                deck_count += 1
            
            print("─"*60)
            print(f"Gesamt: {deck_count} Decks")
            print("="*60)
            
            return user_decks
            
        except Exception as e:
            print(f"✗ Fehler beim Laden der Decks: {e}")
            traceback.print_exc()
            return None
    
    def update_deck(self):
        """
        Aktualisiert ein Deck in einem bestimmten Slot
        Akzeptiert Karten-Namen (z.B. "Barracus-6") statt IDs
        """
        try:
            if not self.init_data:
                self.initialize()
            
            print("\n" + "="*60)
            print("DECK AKTUALISIEREN")
            print("="*60)
            
            # Lade Card-Daten für Name->ID Mapping
            print("\n⏳ Lade Card-Daten...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Kann ohne Card-Daten nicht fortfahren.")
                print("   Bitte stelle sicher dass cards_section_*.xml verfügbar sind")
                print("   oder verwende Punkt 2 (XML-Dateien aktualisieren)")
                return
            
            # Erstelle Reverse-Mapping: Name -> ID
            # Inklusive Basenames ohne Level (z.B. "Daemon" -> höchstes Level "Daemon-6")
            # Case-insensitive (Groß-/Kleinschreibung egal)
            name_to_id = {}
            name_to_id_lower = {}  # Lowercase-Version für case-insensitive Suche
            base_name_to_max = {}  # Speichert für jeden Basenames das höchste Level
            
            for card_id, name in card_data.items():
                # Vollständiger Name (z.B. "Daemon-6")
                name_to_id[name] = card_id
                name_to_id_lower[name.lower()] = card_id
                
                # Extrahiere Basename und Level
                if '-' in name:
                    base_name, level_str = name.rsplit('-', 1)
                    try:
                        level = int(level_str)
                        
                        # Speichere höchstes Level für jeden Basenames
                        if base_name not in base_name_to_max or level > base_name_to_max[base_name][1]:
                            base_name_to_max[base_name] = (card_id, level)
                    except ValueError:
                        pass  # Kein numerisches Level
            
            # Füge Basenames hinzu (zeigen auf höchstes Level)
            for base_name, (card_id, level) in base_name_to_max.items():
                if base_name not in name_to_id:  # Nur wenn nicht schon existiert
                    name_to_id[base_name] = card_id
                    name_to_id_lower[base_name.lower()] = card_id
            
            print(f"✓ {len(card_data)} Karten geladen ({len(base_name_to_max)} Basenames)")
            
            # Zeige verfügbare Slots mit kompletten Decks
            user_decks = self.init_data.get('user_decks', {})
            active_deck = str(self.init_data.get('user_data', {}).get('active_deck', ''))
            defense_deck = str(self.init_data.get('user_data', {}).get('defense_deck', ''))
            
            print(f"\nVerfügbare Deck-Slots: {len(user_decks)}")
            print("─"*60)
            
            for deck_id in sorted(user_decks.keys(), key=lambda x: int(x)):
                deck = user_decks[deck_id]
                deck_name = deck.get('name') or f"Deck{deck_id}"
                
                # Markierungen [A] für Active, [D] für Defense
                marks = []
                if str(deck_id) == active_deck:
                    marks.append("A")
                if str(deck_id) == defense_deck:
                    marks.append("D")
                mark_str = f" [{'/'.join(marks)}]" if marks else ""
                
                # Commander
                commander_id = deck.get('commander_id', '0')
                commander = card_data.get(int(commander_id), str(commander_id)) if commander_id and commander_id != '0' else '?'
                # Entferne "-6" wenn vorhanden
                if commander.endswith('-6'):
                    commander = commander[:-2]
                
                # Dominion (optional)
                dominion_id = deck.get('dominion_id')
                dominion = card_data.get(int(dominion_id), str(dominion_id)) if dominion_id else ""
                # Entferne "-6" wenn vorhanden
                if dominion and dominion.endswith('-6'):
                    dominion = dominion[:-2]
                
                # Cards mit Anzahl
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    cname = card_data.get(int(cid), str(cid))
                    # Entferne "-6" wenn vorhanden
                    if cname.endswith('-6'):
                        cname = cname[:-2]
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)
                
                # Zeile zusammenbauen: Name[Mark]:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)
                
                line = f"{deck_name}{mark_str}:{', '.join(parts)}"
                print(line)
            
            print("─"*60)
            
            # Slot-Auswahl mit ESC-Support
            slot_input = input_with_esc("\nWelchen Slot bearbeiten? (1-6, ESC=Abbruch): ")
            if slot_input is None:
                return
            
            slot_input = slot_input.strip()
            if not slot_input.isdigit():
                print("✗ Ungültige Eingabe")
                return
            
            deck_id = slot_input
            
            # Validiere Slot-Nummer
            if int(deck_id) < 1 or int(deck_id) > 6:
                print("✗ Slot muss zwischen 1 und 6 liegen")
                return
            
            print(f"\n✓ Bearbeite Slot {deck_id}")
            
            # Frage was gemacht werden soll
            print("\n" + "─"*60)
            print("WAS MÖCHTEST DU TUN?")
            print("─"*60)
            print("1. Deck bearbeiten (Commander, Dominion, Karten ändern)")
            print("2. Nur als Attack Deck setzen")
            print("3. Nur als Defense Deck setzen")
            
            action = input_with_esc("\nAuswahl (1-3, ESC=Abbruch): ")
            if action is None:
                return
            
            action = action.strip()
            
            if action == '2':
                # Nur als Attack Deck setzen
                print(f"\n⏳ Setze Slot {deck_id} als Attack Deck...")
                result = self.api.call('setActiveDeck', deck_id=deck_id)
                if result and result.get('result') == True:
                    print(f"✓ Slot {deck_id} ist jetzt das Attack Deck!")
                    # Init-Daten neu laden
                    print("\n⏳ Aktualisiere Daten...")
                    self.initialize()
                    print("✓ Daten aktualisiert")
                else:
                    print(f"✗ Fehler beim Setzen als Attack Deck")
                print("="*60)
                return
            
            elif action == '3':
                # Nur als Defense Deck setzen
                print(f"\n⏳ Setze Slot {deck_id} als Defense Deck...")
                result = self.api.call('setDefenseDeck', deck_id=deck_id)
                if result and result.get('result') == True:
                    print(f"✓ Slot {deck_id} ist jetzt das Defense Deck!")
                    # Init-Daten neu laden
                    print("\n⏳ Aktualisiere Daten...")
                    self.initialize()
                    print("✓ Daten aktualisiert")
                else:
                    print(f"✗ Fehler beim Setzen als Defense Deck")
                print("="*60)
                return
            
            elif action != '1':
                print("✗ Ungültige Auswahl")
                return
            
            # Wenn action == '1', weiter mit Deck-Bearbeitung
            print("\n" + "─"*60)
            print("DECK-EINGABE FORMAT")
            print("─"*60)
            print("Commander-Name, Dominion-Name, Karte1-Name, Karte2-Name, ...")
            print("\nBeispiel: Barracus-6, Imperial Fortress-5, Windreaver-5, Aegis-5")
            print("Oder:     Barracus, Imperial Fortress, Windreaver, Aegis")
            print("Oder:     barracus, imperial fortress, windreaver, aegis")
            print("\nMehrfache Karten (beide Schreibweisen möglich):")
            print("  Daemon, Daemon, Daemon")
            print("  Daemon #3")
            print("  Kulkan Neurotox, Kulkan Neurotox")
            print("  Kulkan Neurotox #2")
            print("\n  • Genau 1 Commander (erforderlich)")
            print("  • Dominion (erforderlich, '0' für kein Dominion)")
            print("  • 1-10 Karten")
            print("\nHinweis:")
            print("  • Name ohne Level (z.B. 'Daemon') = höchstes Level (Daemon-6)")
            print("  • Name mit Level (z.B. 'Daemon-5') = exakt dieses Level")
            print("  • Groß-/Kleinschreibung wird NICHT beachtet")
            print("  • #count Syntax: 'Karte #3' = 3x diese Karte")
            print("─"*60)
            
            # Deck-Eingabe mit ESC-Support
            deck_input = input_with_esc("\nDeck eingeben (ESC=Abbruch): ")
            if deck_input is None:
                return
            
            deck_input = deck_input.strip()
            if not deck_input:
                print("✗ Keine Eingabe")
                return
            
            # Parse Eingabe
            try:
                parts = [p.strip() for p in deck_input.split(',')]
                if len(parts) < 3:
                    print("✗ Zu wenige Einträge (mindestens Commander, Dominion, 1 Karte)")
                    return
                
                commander_entry = parts[0]
                dominion_entry = parts[1]
                card_entries = parts[2:]
                
                # Expandiere #count Syntax
                # "Daemon #3" -> ["Daemon", "Daemon", "Daemon"]
                expanded_card_entries = []
                for entry in card_entries:
                    entry = entry.strip()
                    # Prüfe ob #count vorhanden
                    if ' #' in entry:
                        card_part, count_part = entry.rsplit(' #', 1)
                        try:
                            count = int(count_part)
                            # Füge Karte count-mal hinzu
                            for _ in range(count):
                                expanded_card_entries.append(card_part.strip())
                        except ValueError:
                            # Kein gültiger Count, behandle als normalen Namen
                            expanded_card_entries.append(entry)
                    else:
                        expanded_card_entries.append(entry)
                
                card_names = expanded_card_entries
                
                if len(card_names) < 1:
                    print("✗ Mindestens 1 Karte erforderlich")
                    return
                
                if len(card_names) > 10:
                    print("✗ Maximal 10 Karten erlaubt")
                    return
                
                # Konvertiere Namen zu IDs
                print("\n⏳ Übersetze Karten-Namen zu IDs...")
                
                commander_name = commander_entry
                dominion_name = dominion_entry
                
                # Commander
                if commander_name in name_to_id:
                    commander_id = str(name_to_id[commander_name])
                    print(f"✓ Commander: {commander_name} → ID {commander_id}")
                elif commander_name.lower() in name_to_id_lower:
                    commander_id = str(name_to_id_lower[commander_name.lower()])
                    print(f"✓ Commander: {commander_name} → ID {commander_id}")
                else:
                    print(f"✗ Commander nicht gefunden: '{commander_name}'")
                    print(f"   Tipp: Achte auf korrekte Schreibweise (z.B. 'Barracus' oder 'barracus')")
                    return
                
                # Dominion
                if dominion_name == '0':
                    dominion_id = '0'
                    print(f"✓ Dominion: Kein Dominion (0)")
                elif dominion_name in name_to_id:
                    dominion_id = str(name_to_id[dominion_name])
                    print(f"✓ Dominion: {dominion_name} → ID {dominion_id}")
                elif dominion_name.lower() in name_to_id_lower:
                    dominion_id = str(name_to_id_lower[dominion_name.lower()])
                    print(f"✓ Dominion: {dominion_name} → ID {dominion_id}")
                else:
                    print(f"✗ Dominion nicht gefunden: '{dominion_name}'")
                    print(f"   Tipp: Achte auf korrekte Schreibweise")
                    return
                
                # Karten
                card_ids = []
                for card_name in card_names:
                    if card_name in name_to_id:
                        card_id = str(name_to_id[card_name])
                        card_ids.append(card_id)
                        print(f"✓ Karte: {card_name} → ID {card_id}")
                    elif card_name.lower() in name_to_id_lower:
                        card_id = str(name_to_id_lower[card_name.lower()])
                        card_ids.append(card_id)
                        print(f"✓ Karte: {card_name} → ID {card_id}")
                    else:
                        print(f"✗ Karte nicht gefunden: '{card_name}'")
                        print(f"   Tipp: Achte auf korrekte Schreibweise")
                        return
                
                print(f"\n✓ Alle Karten erfolgreich übersetzt!")
                print(f"   Commander: {commander_name}")
                print(f"   Dominion: {dominion_name}")
                print(f"   Karten ({len(card_ids)}):")
                
                # Zeige Karten mit Count
                from collections import Counter
                card_name_counts = Counter(card_names)
                for card_name, count in card_name_counts.items():
                    if count > 1:
                        print(f"     • {card_name} x{count}")
                    else:
                        print(f"     • {card_name}")
                
                # VALIDIERUNG: Prüfe ob Karten im Inventar vorhanden sind
                print(f"\n⏳ Prüfe Inventar-Verfügbarkeit...")
                user_cards = self.init_data.get('user_cards', {})
                
                # Sammle alle benötigten Karten mit Count
                needed_cards = Counter(card_ids)
                # Füge Commander und Dominion hinzu
                needed_cards[commander_id] += 1
                if dominion_id != '0':
                    needed_cards[dominion_id] += 1
                
                # Prüfe jede benötigte Karte
                missing_cards = []
                for card_id, needed_count in needed_cards.items():
                    if card_id in user_cards:
                        owned_count = int(user_cards[card_id].get('num_owned', 0))
                        if owned_count < needed_count:
                            card_name = card_data.get(int(card_id), f"ID {card_id}")
                            missing_cards.append(f"{card_name}: benötigt {needed_count}, hast {owned_count}")
                    else:
                        card_name = card_data.get(int(card_id), f"ID {card_id}")
                        missing_cards.append(f"{card_name}: NICHT im Inventar")
                
                if missing_cards:
                    print(f"\n✗ FEHLER: Folgende Karten fehlen im Inventar:")
                    for msg in missing_cards:
                        print(f"   • {msg}")
                    print(f"\n⚠ Deck kann nicht gespeichert werden!")
                    return
                
                print(f"✓ Alle Karten im Inventar verfügbar!")
                
            except Exception as e:
                print(f"✗ Fehler beim Parsen: {e}")
                traceback.print_exc()
                return
            
            # API-Call: setDeckCards (ohne Bestätigung)
            print(f"\n⏳ Speichere Deck in Slot {deck_id}...")
            
            # Cards als JSON-Object: {"card_id": "count"}
            # Zähle wie oft jede Karte vorkommt
            from collections import Counter
            card_counts = Counter(card_ids)
            cards_dict = {card_id: str(count) for card_id, count in card_counts.items()}
            cards_json = json.dumps(cards_dict)
            
            print(f"   Cards JSON: {cards_json}")
            
            result = self.api.call('setDeckCards',
                                  deck_id=deck_id,
                                  commander_id=commander_id,
                                  dominion_id=dominion_id,
                                  cards=cards_json,
                                  activeYN='0')  # Nicht automatisch als Attack setzen
            
            if result and result.get('result') == True:
                print(f"✓ Deck in Slot {deck_id} gespeichert!")
                
                # Init-Daten neu laden
                print("\n⏳ Aktualisiere Daten...")
                self.initialize()
                print("✓ Daten aktualisiert")
                
            else:
                print(f"✗ Fehler beim Speichern des Decks")
                if result:
                    print(f"   API Response: {result}")
            
            print("="*60)
            
        except Exception as e:
            print(f"✗ Fehler: {e}")
            traceback.print_exc()
    
    def get_foreign_deck(self, user_id):
        """
        Zeigt Attack- und Defense-Deck eines fremden Spielers
        
        Args:
            user_id: User-ID des Spielers
        """
        try:
            print("\n" + "="*60)
            print(f"FREMDE DECKS: User ID {user_id}")
            print("="*60)
            
            # Spieler-Profil laden
            print("⏳ Lade Spieler-Profil...")
            profile = self.api.call('getProfileData', target_user_id=str(user_id))
            player_info = profile['player_info']
            player_name = player_info['name']
            
            print(f"✓ Spieler: {player_name} (Lvl {player_info['level']})")
            
            # Attack Deck
            attack_deck = player_info['deck']
            print("\n" + "─"*60)
            print("ATTACK DECK")
            print("─"*60)
            self._print_deck(attack_deck)
            
            # Defense Deck
            defense_deck = player_info['defense_deck']
            print("\n" + "─"*60)
            print("DEFENSE DECK")
            print("─"*60)
            self._print_deck(defense_deck)
            
            print("="*60)
            
            return {'attack': attack_deck, 'defense': defense_deck}
            
        except Exception as e:
            print(f"✗ Fehler beim Laden der Decks: {e}")
            return None
    
    def _print_deck(self, deck):
        """Hilfsfunktion zum Ausgeben eines Decks"""
        print(f"Commander ID: {deck.get('commander_id')}")
        
        if 'dominion_id' in deck and deck['dominion_id']:
            print(f"Dominion ID: {deck.get('dominion_id')}")
        
        cards = deck.get('cards', [])
        print(f"Cards ({len(cards)}): {cards}")
    
    def set_deck(self, deck_type, commander_id, card_ids, dominion_id=None):
        """
        Setzt ein Deck
        
        Args:
            deck_type: 'attack' oder 'defense'
            commander_id: ID des Commanders
            card_ids: Liste von Karten-IDs
            dominion_id: ID des Dominions (optional)
        """
        try:
            if deck_type == 'attack':
                result = self.api.call('setDeck', 
                                      commander_id=commander_id,
                                      cards=card_ids,
                                      dominion_id=dominion_id)
            else:
                result = self.api.call('setDefenseDeck',
                                      commander_id=commander_id,
                                      cards=card_ids,
                                      dominion_id=dominion_id)
            
            print(f"✓ {deck_type.capitalize()}-Deck erfolgreich gesetzt")
            return result
            
        except Exception as e:
            print(f"✗ Fehler beim Setzen des Decks: {e}")
            return None
    
    # ==================== MISSIONS & KAMPAGNEN ====================
    
    def fight_mission(self, mission_id, deck_hash=None):
        """
        Kämpft gegen eine Mission
        
        Args:
            mission_id: ID der Mission
            deck_hash: Optional - Hash des zu verwendenden Decks
        """
        try:
            result = self.api.call('fightMission', 
                                  mission_id=mission_id,
                                  deck_hash=deck_hash)
            
            print(f"✓ Mission {mission_id} gekämpft")
            print(f"Ergebnis: {result.get('result', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"✗ Fehler beim Kämpfen: {e}")
            return None
    
    # ==================== ARENA & PVP ====================
    
    
    def attack_player(self, target_user_id, deck_hash=None):
        """
        Greift einen Spieler in der Arena an
        
        Args:
            target_user_id: User-ID des Ziels
            deck_hash: Optional - Hash des zu verwendenden Decks
        """
        try:
            result = self.api.call('attackPlayer',
                                  target_user_id=str(target_user_id),
                                  deck_hash=deck_hash)
            
            print(f"✓ Angriff auf User {target_user_id}")
            print(f"Ergebnis: {result.get('result', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"✗ Fehler beim Angriff: {e}")
            return None
    
    # ==================== KARTEN-MANAGEMENT ====================
    
    # ---------- Card-Data von tyrantonline laden ----------

    def _load_card_data(self):
        """
        Lädt cards_section_1.xml … cards_section_N.xml von
        mobile.tyrantonline.com und baut eine Zuordnung
        card_id  ->  "Name-Level"  auf.

        Struktur pro XML:
            <root>
              <unit>
                <id>...</id>          ← Basis-card_id
                <name>CardName</name> ← Name
                <rarity>...</rarity>  ← 1 Common, 2 Rare, 3 Epic, 4 Legendary
                <upgrade>
                  <card_id>...</card_id>
                  <level>...</level>
                </upgrade>
                ...
              </unit>
            </root>

        Basis-Karte wird als Level 1 gespeichert.
        Ergebnis wird in _card_data_cache gepusht (nur einmal geladen).

        Returns:
            dict: { int(card_id): "Name-Level" }
        """
        if self._card_data_cache:
            return self._card_data_cache

        print("⏳ Lade Card-Daten", end='', flush=True)

        card_data = {}
        loaded    = 0
        errors    = 0

        # Erweitert auf 22 Sectionen (Section 22 optional)
        for section in range(1, 23):
            filename   = f"cards_section_{section}.xml"
            local_path = os.path.join(SCRIPT_DIR, filename)
            url        = f"{CARDS_BASE_URL}{filename}"

            try:
                # ── Quelle bestimmen: lokal bevorzugt, sonst HTTP ──
                if os.path.isfile(local_path):
                    print(".", end='', flush=True)
                    with open(local_path, 'rb') as fh:
                        xml_bytes = fh.read()
                else:
                    print(".", end='', flush=True)
                    response  = urlopen(url, timeout=15)
                    xml_bytes = response.read()

                root = ET.fromstring(xml_bytes)

                count = 0
                for unit in root.findall('.//unit'):  # .// = tiefe Suche in allen Ebenen
                    # Pflichtfelder prüfen – unit überspringen wenn eines fehlt
                    id_elem   = unit.find('id')
                    name_elem = unit.find('name')
                    if id_elem is None or name_elem is None:
                        continue                          # defektes <unit> …
                    if id_elem.text is None or name_elem.text is None:
                        continue                          # … oder leeres Tag

                    base_id = int(id_elem.text)
                    name    = name_elem.text

                    # Basis-Karte: Level 1
                    card_data[base_id] = {"name": f"{name}-1", "level": 1, "base_id": base_id}
                    count += 1

                    # Upgrades
                    for upgrade in unit.findall('upgrade'):
                        cid_elem = upgrade.find('card_id')
                        lvl_elem = upgrade.find('level')
                        if cid_elem is None or lvl_elem is None:
                            continue
                        if cid_elem.text is None or lvl_elem.text is None:
                            continue

                        upg_id    = int(cid_elem.text)
                        upg_level = lvl_elem.text
                        card_data[upg_id] = {"name": f"{name}-{upg_level}", "level": int(upg_level), "base_id": base_id}
                        count += 1

                pass  # Silent
                loaded += 1

            except URLError as e:
                # Section 22 ist optional - 404 ist OK
                if section == 22 and "404" in str(e):
                    pass  # Optional
                else:
                    print(f"✗  ({e})")
                    errors += 1
            except Exception as e:
                # Section 22 ist optional - 404 ist OK
                if section == 22 and "404" in str(e):
                    pass  # Optional
                else:
                    print(f"✗  ({e})")
                    errors += 1

        self._card_data_cache = card_data
        print(f"✓ Card-Daten fertig: {len(card_data)} Karten aus {loaded} Sections "
              f"({errors} Fehler)")
        return card_data

    def _get_card_info(self, card_data, card_id, default_name=None):
        """Universelle Funktion um card_info zu holen (Dict und String kompatibel)"""
        if default_name is None:
            default_name = f"ID_{card_id}"
        
        info = card_data.get(card_id, None)
        
        if isinstance(info, dict):
            return {
                'name': info.get('name', default_name),
                'level': info.get('level', 1),
                'base_id': info.get('base_id', card_id)
            }
        
        if isinstance(info, str):
            if '-' in info:
                parts = info.rsplit('-', 1)
                try:
                    level = int(parts[1])
                    return {'name': info, 'level': level, 'base_id': card_id}
                except:
                    pass
            return {'name': info, 'level': 1, 'base_id': card_id}
        
        return {'name': default_name, 'level': 1, 'base_id': card_id}

    def _resolve_card(self, card_id, card_data):
        """
        Löst eine card_id in einen lesbaren String auf.
        Level 6 wird entfernt (wie im PS1-Skript).

        Returns:
            str: z.B. "Tiamat-3" oder "Draconian Queen" (Level 6 → kein Suffix)
        """
        name = card_data.get(int(card_id), f"ID_{card_id}")
        # Level 6 entfernen (PS1: replace("-6",""))
        if name.endswith("-6"):
            name = name[:-2]
        return name

    def _classify_fusion(self, card_name):
        """
        Classifiziert eine Karte in eine Fusion-Material-Gruppe.
        Gibt den Gruppen-Index zurück, oder -1 wenn keine Gruppe passt.

        Args:
            card_name: der aufgelöste Name (z.B. "Tiamat-3" oder "Tiamat")
        """
        # Nur den Namen ohne Level und ohne Klammer-Anzahl prüfen
        base = card_name.split("-")[0].split(" (")[0].strip()
        for idx, (group_name, prefixes) in enumerate(FUSION_GROUPS):
            if base in prefixes:
                return idx
        return -1

    def salvage_base_epics_keep_x(self, keep_count=1, silent=False):
        """
        Salvaged alle Base Epics bis auf X Stück pro Karte.
        
        Base Epics sind die 25 Fusion-Material Karten:
        - 5x Bloodthirsty (ohne Malgoth)
        - 5x Imperial (ohne Nimbus)
        - 5x Raider (ohne Omega)
        - 5x Righteous (ohne Benediction)
        - 5x Xeno (ohne Apex)
        
        Args:
            keep_count: Anzahl die pro Karte behalten werden soll (Standard: 1)
            silent: Wenn True, reduzierte Ausgabe (für Workflows)
        
        Returns:
            (success: bool, sp_gewinn: int)
        """
        if not self.init_data:
            self.initialize()
        
        if not silent:
            print(f"\n{'='*60}")
            print(f"SALVAGE BASE EPICS (behalte {keep_count} pro Karte)")
            print(f"{'='*60}")
        
        # Card-Daten laden
        card_data = self._load_card_data_with_rarity()
        if not card_data:
            if not silent:
                print("✗ Kann ohne Card-Daten nicht fortfahren.")
            return False, 0
        
        # Base Epics identifizieren (aus Fusion-Gruppen, nur Epics)
        base_epic_names = []
        for group_name, card_names in FUSION_GROUPS[1:]:  # Skip Vindicator Reactors
            for card_name in card_names:
                # Prüfen ob Epic
                for card_id, info in card_data.items():
                    if info['name'] == card_name and info['level'] == 1 and info['rarity'] == 3:
                        base_epic_names.append(card_name)
                        break
        
        if not silent:
            print(f"\nBase Epics gefunden: {len(base_epic_names)}")
            print(f"Behalte: {keep_count} pro Karte")
            print(f"Salvage: Alles darüber\n")
        
        # Inventar durchgehen
        user_cards = self.init_data.get('user_cards', {})
        
        to_salvage = []
        
        for card_id, info in user_cards.items():
            card_id_int = int(card_id)
            
            # Upgradematerialien, Commanders und Dominions überspringen
            if card_id_int in EXCLUDED_CARD_IDS:
                continue
            
            num_owned = int(info.get('num_owned', 0))
            if num_owned <= 0:
                continue
            
            card_id_int = int(card_id)
            card_info = card_data.get(card_id_int)
            
            if not card_info:
                continue
            
            # Ist es ein Base Epic?
            if card_info['name'] in base_epic_names and card_info['level'] == 1:
                if num_owned > keep_count:
                    salvage_amount = num_owned - keep_count
                    to_salvage.append({
                        'card_id': card_id_int,
                        'name': card_info['name'],
                        'owned': num_owned,
                        'keep': keep_count,
                        'salvage': salvage_amount
                    })
        
        if not to_salvage:
            if not silent:
                print("✓ Nichts zu salvagen - alle Base Epics bereits auf Zielanzahl oder darunter")
            return True, 0
        
        # Zusammenfassung
        to_salvage.sort(key=lambda x: x['name'])
        
        total_salvage = 0
        total_sp = 0
        
        if not silent:
            print(f"{'Karte':<25} {'Besitz':>8} {'Behalten':>10} {'Salvage':>10}")
            print("─" * 60)
        
        for item in to_salvage:
            if not silent:
                print(f"{item['name']:<25} {item['owned']:>8} {item['keep']:>10} {item['salvage']:>10}")
            total_salvage += item['salvage']
            total_sp += item['salvage'] * 5  # Base Epics geben 5 SP
        
        if not silent:
            print("─" * 60)
            print(f"{'Gesamt:':<25} {'':<8} {'':<10} {total_salvage:>10}")
            print(f"\nErwarteter SP-Gewinn: +{total_sp:,} SP (à 20 SP pro Epic)\n")
        
        # Bestätigung (nur wenn nicht silent)
        if not silent:
            if not confirm_action(f"Wirklich {total_salvage} Base Epics salvagen?"):
                print("Abgebrochen")
                return False, 0
        
        # Salvagen
        salvage_vorher = int(self.init_data.get('user_data', {}).get('salvage', 0))
        
        if not silent:
            print(f"\n⏳ Salvage {total_salvage} Karten...")
        
        salvaged_count = 0
        sp_gained = 0
        
        for i, item in enumerate(to_salvage, 1):
            card_id = item['card_id']
            salvage_amount = item['salvage']
            
            if not silent:
                print(f"  [{i}/{len(to_salvage)}] {item['name']}: -{salvage_amount}...", end=' ', flush=True)
            
            # Jede einzelne Karte salvagen
            for _ in range(salvage_amount):
                try:
                    result = self.api.call('salvageCard', card_id=card_id)
                    if result and result.get('result') == True:
                        salvaged_count += 1
                        sp_gained += 5
                    else:
                        if not silent:
                            print("✗", end='')
                        break
                except Exception as e:
                    if not silent:
                        print(f"✗ Fehler: {e}")
                    break
            
            if not silent:
                print("✓")
            sleep(0.2)  # Rate limiting
        
        # Daten aktualisieren
        self.initialize()
        salvage_nachher = int(self.init_data.get('user_data', {}).get('salvage', 0))
        sp_actual = salvage_nachher - salvage_vorher
        
        if not silent:
            print(f"\n{'='*60}")
            print(f"ERGEBNIS")
            print(f"{'='*60}")
            print(f"Salvaged         : {salvaged_count}/{total_salvage} Karten")
            print(f"SP vorher        : {salvage_vorher:,}")
            print(f"SP nachher       : {salvage_nachher:,}")
            print(f"SP gewonnen      : +{sp_actual:,}")
            print(f"{'='*60}\n")
        
        return True, sp_actual

    def _load_card_data_with_rarity(self):
        """
        Lädt Card-Daten inkl. Rarity, Level und Tier aus den XMLs.
        Nutzt Cache wenn vorhanden.
        
        Returns:
            dict: { card_id: {'name': str, 'level': int, 'rarity': int, 'tier': int} }
        """
        # Cache verwenden wenn vorhanden
        if self._card_data_with_rarity_cache is not None:
            return self._card_data_with_rarity_cache
        
        print("⏳ Lade Card-Daten mit Rarity-Info...")
        
        card_data = {}
        loaded = 0
        errors = 0
        
        # Erweitert auf 22 Sectionen (Section 22 optional)
        for section in range(1, 23):
            filename = f"cards_section_{section}.xml"
            local_path = os.path.join(SCRIPT_DIR, filename)
            url = f"{CARDS_BASE_URL}{filename}"
            
            try:
                # Lokal oder HTTP
                if os.path.isfile(local_path):
                    with open(local_path, 'rb') as fh:
                        xml_bytes = fh.read()
                else:
                    response = urlopen(url, timeout=15)
                    xml_bytes = response.read()
                
                root = ET.fromstring(xml_bytes)
                
                for unit in root.findall('.//unit'):
                    id_elem = unit.find('id')
                    name_elem = unit.find('name')
                    rarity_elem = unit.find('rarity')
                    tier_elem = unit.find('tier')
                    
                    if id_elem is None or name_elem is None:
                        continue
                    if id_elem.text is None or name_elem.text is None:
                        continue
                    
                    base_id = int(id_elem.text)
                    name = name_elem.text
                    rarity = int(rarity_elem.text) if rarity_elem is not None and rarity_elem.text else 1
                    tier = int(tier_elem.text) if tier_elem is not None and tier_elem.text else 0
                    
                    # Fusion-Rezept: Was ist das nächste Upgrade?
                    upgrade_id = None
                    first_upgrade = unit.find('.//upgrade')
                    if first_upgrade is not None:
                        upgrade_cid = first_upgrade.find('card_id')
                        if upgrade_cid is not None and upgrade_cid.text:
                            upgrade_id = int(upgrade_cid.text)
                    
                    # Basis-Karte: Level 1
                    card_data[base_id] = {
                        'name': name,
                        'level': 1,
                        'rarity': rarity,
                        'tier': tier,
                        'upgrade_id': upgrade_id
                    }
                    
                    # Upgrades (Level 2-6)
                    for upgrade in unit.findall('upgrade'):
                        cid_elem = upgrade.find('card_id')
                        lvl_elem = upgrade.find('level')
                        
                        if cid_elem is None or lvl_elem is None:
                            continue
                        if cid_elem.text is None or lvl_elem.text is None:
                            continue
                        
                        upg_id = int(cid_elem.text)
                        upg_level = int(lvl_elem.text)
                        
                        card_data[upg_id] = {
                            'name': name,
                            'level': upg_level,
                            'rarity': rarity,
                            'tier': tier
                        }
                
                loaded += 1
                
            except Exception as e:
                # Section 22 ist optional - skip bei Fehler
                if section == 22:
                    pass  # Ignoriere Fehler für Section 22
                else:
                    errors += 1
        
        print(f"✓ {len(card_data)} Karten aus {loaded} Sections ({errors} Fehler)")
        
        # ===== FUSION-TIER BERECHNUNG MIT ECHTEN REZEPTEN =====
        
        # Lade fusion_recipes_cj2.xml
        fusion_file = os.path.join(SCRIPT_DIR, 'fusion_recipes_cj2.xml')
        fusion_recipes = {}
        
        if os.path.exists(fusion_file):
            try:
                tree = ET.parse(fusion_file)
                for recipe in tree.getroot().findall('fusion_recipe'):
                    card_id_elem = recipe.find('card_id')
                    if card_id_elem is not None and card_id_elem.text:
                        result_id = int(card_id_elem.text)
                        resources = []
                        for res in recipe.findall('resource'):
                            res_id = res.get('card_id')
                            if res_id:
                                resources.append(int(res_id))
                        if resources:
                            fusion_recipes[result_id] = resources
                print(f"✓ {len(fusion_recipes)} Fusion-Rezepte geladen")
            except Exception as e:
                print(f"⚠ Konnte Fusion-Rezepte nicht laden: {e}")
        else:
            print(f"⚠ fusion_recipes_cj2.xml nicht gefunden in {SCRIPT_DIR}")
        
        # Berechne Tier für jede Basis-Karte (Level 1)
        # WICHTIG: Muss über Namen gehen, da Rezepte andere IDs verwenden können!
        
        # Schritt 1: Baue Name->IDs Mapping (nur Level 1)
        name_to_ids = {}
        for card_id, info in card_data.items():
            if info.get('level', 1) == 1:
                name = info.get('name', '')
                if name:
                    if name not in name_to_ids:
                        name_to_ids[name] = []
                    name_to_ids[name].append(card_id)
        
        # Schritt 2: Baue Name->Rezept Mapping
        name_recipes = {}
        for result_id, base_ids in fusion_recipes.items():
            result_name = card_data.get(result_id, {}).get('name', '')
            if result_name:
                base_names = []
                for base_id in base_ids:
                    base_name = card_data.get(base_id, {}).get('name', '')
                    if base_name:
                        base_names.append(base_name)
                if base_names:
                    name_recipes[result_name] = base_names
        
        # Schritt 3: Finde welche Karten als Basis verwendet werden
        used_as_base = set()
        for base_names in name_recipes.values():
            for base_name in base_names:
                used_as_base.add(base_name)
        
        # Debug
        print("DEBUG: Luci-Karten:")
        for name in name_to_ids.keys():
            if 'luci' in name.lower():
                has_recipe = name in name_recipes
                is_base = name in used_as_base
                print(f"  {name}: has_recipe={has_recipe}, is_base={is_base}")
        
        # Schritt 4: Bestimme Tier basierend auf Position
        def get_fusion_tier_by_position(name):
            """
            Tier-Logik basierend auf Position in Fusion-Kette:
            - Tier 0: Nur Basis (kein Rezept, wird aber verwendet)
            - Tier 1: Mittelglied (hat Rezept UND wird verwendet)
            - Tier 2: Endglied (hat Rezept, wird NICHT verwendet)
            """
            has_recipe = name in name_recipes
            is_used_as_base = name in used_as_base
            
            if not has_recipe and is_used_as_base:
                return 0  # Nur Basis
            elif has_recipe and is_used_as_base:
                return 1  # Mittelglied
            elif has_recipe and not is_used_as_base:
                return 2  # Endglied
            else:
                return 0  # Fallback (keine Fusion)
        
        # Schritt 5: Setze fusion_tier für alle Level-1 Karten
        for card_id, info in card_data.items():
            if info.get('level', 1) == 1:
                name = info.get('name', '')
                if name:
                    tier = get_fusion_tier_by_position(name)
                    card_data[card_id]['fusion_tier'] = tier
                    
                    # Debug für Luci-Karten
                    if 'luci' in name.lower():
                        print(f"  {name} (ID {card_id}) → Tier {tier}")
        
        # Cache setzen
        self._card_data_with_rarity_cache = card_data
        
        return card_data

    # ---------- Inventar: ownedcards.txt & currentdecks.txt ----------

    def get_inventory(self):
        """
        Erzeugt ownedcards.txt und currentdecks.txt – analog zum PS1-Skript,
        aber komplett über die API (init-Daten).

        ownedcards.txt:
            - Sortiert nach Fusion-Gruppen (Vindicator → Bloodthirsty → Imperial
              → Raider → Righteous → Xeno → Rest)
            - Jede Gruppe mit einem //Kommentar-Header
            - Pro Karte: "Name-Level" bzw. "Name-Level (count)" wenn >1
            - Am Ende: "//cards from restore" + buyback_data Einträge

        currentdecks.txt:
            - Pro Deck eine Zeile:
              "DeckName:Commander,Dominion,Card1,Card2 #count,..."
            - Aktives Deck wird mit [A] markiert, Defense mit [D]
        """
        try:
            print("\n=== INVENTAR EXPORTIEREN - START ===")
            
            if not self.init_data:
                print("⏳ Initialisiere...")
                self.initialize()

            print("⏳ Lade Card-Daten...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Kann ohne Card-Daten nicht fortfahren.")
                return

            print(f"✓ {len(card_data)} Karten geladen")
            print("\n⏳ Verarbeite Inventar...")

            # ----------------------------------------------------------
            # A) ownedcards.txt
            # ----------------------------------------------------------
            user_cards  = self.init_data.get('user_cards', {})
            buyback     = self.init_data.get('buyback_data', {})

            print(f"   User hat {len(user_cards)} Karten-Einträge")
            
            # Gruppen-Buckets initialisieren
            buckets = {i: [] for i in range(len(FUSION_GROUPS))}
            buckets[-1] = []   # Rest

            print("   Klassifiziere Karten...")
            for card_id, info in user_cards.items():
                card_id_int = int(card_id)
                
                # KEIN Filter mehr - alle Karten werden exportiert
                # (auch Dominion Shards, Dominions und Commanders)
                
                num_owned = int(info.get('num_owned', 0))
                if num_owned <= 0:
                    continue

                name = self._resolve_card(card_id, card_data)

                # Anzahl anhängen wenn >1
                line = name if num_owned == 1 else f"{name} ({num_owned})"

                group_idx = self._classify_fusion(name)
                buckets[group_idx].append(line)

            # Datei zusammenbauen
            print("   Baue ownedcards.txt zusammen...")
            owned_lines = []
            for idx, (group_name, _) in enumerate(FUSION_GROUPS):
                owned_lines.append(f"//{group_name}")
                owned_lines.extend(buckets[idx])
                owned_lines.append("")          # Leerzeile zwischen Gruppen

            # Rest (keine Gruppe)
            owned_lines.extend(buckets[-1])

            # Buyback-Anhang ("cards from restore")
            print("   Verarbeite Buyback-Daten...")
            owned_lines.append("")
            owned_lines.append("//cards from restore")
            for card_id, bb_info in buyback.items():
                number = int(bb_info.get('number', 0))
                if number <= 0:
                    continue
                name = self._resolve_card(card_id, card_data)
                line = name if number == 1 else f"{name} ({number})"
                owned_lines.append(line)

            # Schreiben
            print("   Schreibe ownedcards.txt...")
            
            # Im Skript-Verzeichnis schreiben, nicht im aktuellen Arbeitsverzeichnis
            owned_path = os.path.join(SCRIPT_DIR, "ownedcards.txt")
            print(f"   Ziel: {owned_path}")
            
            # Alte Datei löschen falls vorhanden
            if os.path.exists(owned_path):
                try:
                    print(f"   Lösche alte Datei...")
                    os.remove(owned_path)
                    print(f"   ✓ Alte Datei gelöscht")
                except Exception as e:
                    print(f"   ⚠ Konnte alte Datei nicht löschen: {e}")
                    raise
            
            # Neue Datei erstellen
            try:
                print(f"   Erstelle neue Datei...")
                with open(owned_path, 'w', encoding='ascii', errors='replace') as f:
                    f.write("\n".join(owned_lines))
                print(f"✓ {os.path.basename(owned_path)} geschrieben ({sum(len(b) for b in buckets.values())} Karten)")
                    
            except PermissionError as e:
                raise PermissionError(
                    f"Kann '{owned_path}' nicht schreiben. "
                    f"Bitte prüfe die Ordner-Berechtigungen für '{SCRIPT_DIR}'"
                ) from e

            # ----------------------------------------------------------
            # B) currentdecks.txt
            # ----------------------------------------------------------
            print("\n⏳ Verarbeite Decks...")
            user_decks   = self.init_data.get('user_decks', {})
            active_deck  = str(self.init_data.get('user_data', {}).get('active_deck', ''))
            defense_deck = str(self.init_data.get('user_data', {}).get('defense_deck', ''))

            print(f"   User hat {len(user_decks)} Decks")
            deck_lines = []
            for deck_id, deck in user_decks.items():
                # Deck-Name
                deck_name = deck.get('name') or f"Deck{deck_id}"

                # Markierung
                marks = []
                if str(deck_id) == active_deck:  marks.append("A")
                if str(deck_id) == defense_deck: marks.append("D")
                mark_str = f" [{'/'.join(marks)}]" if marks else ""

                # Commander
                commander = self._resolve_card(deck.get('commander_id', '0'), card_data)

                # Dominion (optional)
                dominion_id = deck.get('dominion_id')
                dominion    = self._resolve_card(dominion_id, card_data) if dominion_id else ""

                # Cards mit Anzahl
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    cname = self._resolve_card(cid, card_data)
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)

                # Zeile zusammenbauen: Name:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)

                line = f"{deck_name}{mark_str}:{','.join(parts)}"
                deck_lines.append(line)

            # Schreiben
            print("   Schreibe currentdecks.txt...")
            
            # Im Skript-Verzeichnis schreiben
            decks_path = os.path.join(SCRIPT_DIR, "currentdecks.txt")
            print(f"   Ziel: {decks_path}")
            
            # Alte Datei löschen falls vorhanden
            if os.path.exists(decks_path):
                try:
                    print(f"   Lösche alte Datei...")
                    os.remove(decks_path)
                    print(f"   ✓ Alte Datei gelöscht")
                except Exception as e:
                    print(f"   ⚠ Konnte alte Datei nicht löschen: {e}")
                    raise
            
            # Neue Datei erstellen
            try:
                print(f"   Erstelle neue Datei...")
                with open(decks_path, 'w', encoding='ascii', errors='replace') as f:
                    f.write("\n".join(deck_lines))
                print(f"✓ {os.path.basename(decks_path)} geschrieben ({len(deck_lines)} Decks)")
                    
            except PermissionError as e:
                raise PermissionError(
                    f"Kann '{decks_path}' nicht schreiben. "
                    f"Bitte prüfe die Ordner-Berechtigungen für '{SCRIPT_DIR}'"
                ) from e

            # Zusammenfassung
            print(f"\n=== ZUSAMMENFASSUNG ===")
            print(f"✓ ownedcards.txt: {len(owned_lines)} Zeilen")
            print(f"✓ currentdecks.txt: {len(deck_lines)} Decks")
            print(f"\n=== INVENTAR EXPORTIEREN - FERTIG ===")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"KRITISCHER FEHLER in get_inventory():")
            print(f"{'='*60}")
            print(f"Fehlertyp: {type(e).__name__}")
            print(f"Fehlermeldung: {e}")
            print(f"\nStacktrace:")
            traceback.print_exc()
            print(f"{'='*60}")
            print("\nDrücke Enter um fortzufahren...")
            input()
    
    def salvage_card(self, card_id):
        """
        Salvaged eine Karte
        
        Args:
            card_id: ID der zu salvagenden Karte
        """
        try:
            result = self.api.call('salvageCard', card_id=card_id)
            print(f"✓ Karte {card_id} salvaged")
            return result
        except Exception as e:
            print(f"✗ Fehler beim Salvagen: {e}")
            return None
    
    # ==================== BUYBACK ====================
    
    def get_buyback_info(self):
        """
        Gibt Informationen über Buyback-Karten zurück
        
        Returns:
            dict: {card_id: {'name': str, 'number': int, 'rarity': int, 'tier': int, 'cost': int}}
        """
        if not self.init_data:
            self.initialize()
        
        buyback_data = self.init_data.get('buyback_data', {})
        if not buyback_data:
            return {}
        
        card_data = self._load_card_data_with_rarity()
        result = {}
        
        for card_id, bb_info in buyback_data.items():
            number = int(bb_info.get('number', 0))
            if number <= 0:
                continue
            
            # Karteninformationen abrufen
            card_info = card_data.get(int(card_id), {
                'name': f'ID_{card_id}',
                'level': 1,
                'rarity': 3,
                'tier': 0,
                'fusion_tier': 0
            })
            
            # DEBUG: Zeige was geladen wurde
            if card_info['name'] not in [f'ID_{card_id}']:
                pass  # Normal gefunden
            
            # Kosten basierend auf Seltenheit UND Fusion-Tier berechnen
            rarity = card_info.get('rarity', 3)
            fusion_tier = card_info.get('fusion_tier', 0)
            level = card_info.get('level', 1)
            
            # Hole Kosten aus BUYBACK_COSTS Dictionary
            cost_per_card = BUYBACK_COSTS.get((rarity, fusion_tier), 0)
            
            # Fallback falls Kombination nicht existiert
            if cost_per_card == 0:
                # Versuche mit Tier 0
                cost_per_card = BUYBACK_COSTS.get((rarity, 0), 20)
            
            result[card_id] = {
                'name': f"{card_info['name']}-1",  # Immer Level 1 im Buyback-Store
                'base_name': card_info['name'],  # Original-Name für Suche
                'number': number,
                'rarity': rarity,
                'tier': fusion_tier,  # Jetzt fusion_tier
                'rarity_name': RARITY_NAMES.get(rarity, 'Unknown'),
                'cost_per_card': cost_per_card,
                'total_cost': cost_per_card * number
            }
        
        return result
    
    def list_buyback_cards(self):
        """
        Listet alle Karten im Buyback-Store mit Details und Kosten
        """
        buyback_info = self.get_buyback_info()
        
        if not buyback_info:
            print("\n❌ Keine Karten im Buyback-Store")
            return
        
        # Aktuelle SP anzeigen
        current_sp = self.get_salvage()
        
        print("\n" + "="*70)
        print("BUYBACK-STORE")
        print("="*70)
        print(f"Verfügbare SP: {current_sp:,}")
        print(f"Karten im Store: {len(buyback_info)}")
        print()
        
        # Nach Seltenheit gruppieren
        by_rarity = {}
        for card_id, info in buyback_info.items():
            rarity = info['rarity']
            if rarity not in by_rarity:
                by_rarity[rarity] = []
            by_rarity[rarity].append((card_id, info))
        
        # Ausgabe sortiert nach Seltenheit (4 -> 1)
        total_cost = 0
        for rarity in sorted(by_rarity.keys(), reverse=True):
            cards = by_rarity[rarity]
            rarity_name = RARITY_NAMES.get(rarity, 'Unknown')
            
            print(f"{'─'*70}")
            print(f"[{rarity_name}]")
            print(f"{'─'*70}")
            
            for card_id, info in sorted(cards, key=lambda x: x[1]['name']):
                name = info['name']
                number = info['number']
                tier = info['tier']
                cost_per = info['cost_per_card']
                total = info['total_cost']
                
                total_cost += total
                
                # Kann es sich leisten?
                affordable = "✓" if current_sp >= total else "✗"
                
                print(f"{affordable} [{card_id:>6}] {name:<30} Tier{tier} x{number:>3}  "
                      f"({cost_per:>4} SP/Karte = {total:>6} SP gesamt)")
            print()
        
        print("="*70)
        print(f"Gesamtkosten für alle Karten: {total_cost:,} SP")
        if current_sp >= total_cost:
            print(f"✓ Du kannst ALLE Karten zurückkaufen")
        else:
            print(f"✗ Du benötigst noch {total_cost - current_sp:,} SP")
        print("="*70)
    
    def buyback_card(self, card_name_or_id, quantity=1):
        """
        Kauft eine Karte aus dem Buyback-Store zurück
        
        Args:
            card_name_or_id: Name oder ID der Karte (z.B. "Infernal Walker" oder 50123)
            quantity: Anzahl der Karten (default: 1, 0 = alle)
        
        Returns:
            API response oder None bei Fehler
        """
        try:
            # Prüfe ob Eingabe eine ID ist (nur Ziffern)
            if isinstance(card_name_or_id, str) and not card_name_or_id.isdigit():
                # Es ist ein Name - konvertiere zu ID
                card_id = self._find_buyback_card_id_by_name(card_name_or_id)
                if card_id is None:
                    print(f"✗ Karte '{card_name_or_id}' nicht im Buyback-Store gefunden")
                    return None
            else:
                card_id = int(card_name_or_id)
            
            # Buyback-Info abrufen
            buyback_info = self.get_buyback_info()
            
            if str(card_id) not in buyback_info:
                print(f"✗ Karte {card_id} ist nicht im Buyback-Store")
                return None
            
            info = buyback_info[str(card_id)]
            available = info['number']
            
            # Quantity validieren
            if quantity == 0:
                quantity = available
            elif quantity > available:
                print(f"✗ Nur {available}x {info['name']} verfügbar (du wolltest {quantity}x)")
                return None
            
            # Kosten berechnen
            cost = info['cost_per_card'] * quantity
            current_sp = self.get_salvage()
            
            if current_sp < cost:
                print(f"✗ Nicht genug SP: {current_sp:,} vorhanden, {cost:,} benötigt")
                return None
            
            # API-Call
            # Hinweis: Basierend auf dem Muster könnte die API entweder card_id und quantity
            # oder nur card_id erwarten. Wir probieren beides.
            try:
                # Versuche mit quantity-Parameter
                result = self.api.call('buybackCard', card_id=card_id, quantity=quantity)
            except:
                # Falls das nicht funktioniert, probiere nur card_id (für 1 Karte)
                if quantity == 1:
                    result = self.api.call('buybackCard', card_id=card_id)
                else:
                    # Für mehrere Karten, wiederhole den Call
                    print(f"⏳ Kaufe {quantity}x {info['name']} zurück (Einzelaufrufe)...")
                    for i in range(quantity):
                        result = self.api.call('buybackCard', card_id=card_id)
                        if i < quantity - 1:
                            sleep(0.5)  # Kurze Pause zwischen Calls
            
            print(f"✓ {quantity}x {info['name']} für {cost:,} SP zurückgekauft")
            print(f"  Verbleibende SP: {current_sp - cost:,}")
            
            return result
            
        except Exception as e:
            print(f"✗ Fehler beim Buyback: {e}")
            return None
    
    def _find_buyback_card_id_by_name(self, card_name):
        """
        Findet die Karten-ID im Buyback-Store anhand des Namens
        
        Args:
            card_name: Name der Karte (z.B. "Infernal Walker" oder "Lucifire-1")
        
        Returns:
            card_id als int oder None wenn nicht gefunden
        """
        buyback_info = self.get_buyback_info()
        
        # Entferne -1 Suffix falls vorhanden (Buyback ist immer Level 1)
        card_name_clean = card_name.strip()
        if card_name_clean.endswith('-1'):
            card_name_clean = card_name_clean[:-2]
        
        card_name_lower = card_name_clean.lower()
        
        # Exakte Suche gegen base_name
        for card_id, info in buyback_info.items():
            if info['base_name'].lower() == card_name_lower:
                return int(card_id)
        
        # Teilstring-Suche (falls exakt nicht gefunden)
        matches = []
        for card_id, info in buyback_info.items():
            if card_name_lower in info['base_name'].lower():
                matches.append((card_id, info['name']))  # Zeige name mit -1 Suffix
        
        if len(matches) == 1:
            card_id = matches[0][0]
            print(f"✓ Gefunden: {matches[0][1]} (ID: {card_id})")
            return int(card_id)
        elif len(matches) > 1:
            print(f"✗ Mehrere Karten gefunden für '{card_name}':")
            for card_id, name in matches[:5]:  # Zeige max 5
                print(f"   [{card_id}] {name}")
            return None
        
        return None
    
    def buyback_multiple(self, rarity_filter=None, max_sp=None):
        """
        Kauft mehrere Karten aus dem Buyback-Store zurück
        
        Args:
            rarity_filter: Nur Karten dieser Seltenheit zurückkaufen (1-4, None = alle)
            max_sp: Maximale SP, die ausgegeben werden sollen (None = alle verfügbaren)
        """
        buyback_info = self.get_buyback_info()
        
        if not buyback_info:
            print("\n❌ Keine Karten im Buyback-Store")
            return
        
        # Filter anwenden
        filtered = {}
        for card_id, info in buyback_info.items():
            if rarity_filter is None or info['rarity'] == rarity_filter:
                filtered[card_id] = info
        
        if not filtered:
            if rarity_filter:
                print(f"\n❌ Keine {RARITY_NAMES.get(rarity_filter, 'Unknown')}-Karten im Buyback-Store")
            else:
                print("\n❌ Keine passenden Karten gefunden")
            return
        
        # Nach Kosten sortieren (günstigste zuerst)
        sorted_cards = sorted(filtered.items(), key=lambda x: x[1]['cost_per_card'])
        
        current_sp = self.get_salvage()
        if max_sp is None:
            max_sp = current_sp
        
        print("\n" + "="*70)
        print("BUYBACK - MEHRERE KARTEN")
        print("="*70)
        print(f"Verfügbare SP: {current_sp:,}")
        print(f"Maximales Budget: {max_sp:,} SP")
        if rarity_filter:
            print(f"Filter: {RARITY_NAMES.get(rarity_filter)} Karten")
        print()
        
        total_bought = 0
        total_spent = 0
        
        for card_id, info in sorted_cards:
            quantity = info['number']
            cost_total = info['total_cost']
            
            # Prüfen ob noch Budget vorhanden
            if total_spent + cost_total > max_sp:
                # Teilweise kaufen wenn möglich
                remaining_budget = max_sp - total_spent
                partial_quantity = remaining_budget // info['cost_per_card']
                
                if partial_quantity > 0:
                    result = self.buyback_card(card_id, partial_quantity)
                    if result:
                        partial_cost = partial_quantity * info['cost_per_card']
                        total_spent += partial_cost
                        total_bought += partial_quantity
                break
            else:
                # Alle Karten kaufen
                result = self.buyback_card(card_id, quantity)
                if result:
                    total_spent += cost_total
                    total_bought += quantity
                    sleep(0.5)  # Pause zwischen Käufen
        
        print("\n" + "="*70)
        print(f"✓ {total_bought} Karten für {total_spent:,} SP zurückgekauft")
        print(f"  Verbleibende SP: {current_sp - total_spent:,}")
        print("="*70)
    
    def buyback_by_names(self, card_names, max_sp=None):
        """
        Kauft mehrere Karten anhand einer Namensliste zurück
        
        Args:
            card_names: Liste von Kartennamen oder komma-separierter String
            max_sp: Maximale SP (None = alle verfügbaren)
        """
        if isinstance(card_names, str):
            card_names = [name.strip() for name in card_names.split(',')]
        
        buyback_info = self.get_buyback_info()
        current_sp = self.get_salvage()
        if max_sp is None:
            max_sp = current_sp
        
        print("\n" + "="*70)
        print("BUYBACK - NACH NAMEN")
        print("="*70)
        print(f"Verfügbare SP: {current_sp:,}")
        print(f"Maximales Budget: {max_sp:,} SP")
        print()
        
        total_bought = 0
        total_spent = 0
        
        for card_name in card_names:
            if not card_name:
                continue
            
            # Finde Karten-ID
            card_id = self._find_buyback_card_id_by_name(card_name)
            if card_id is None:
                print(f"⚠ Überspringe '{card_name}' (nicht gefunden)")
                continue
            
            info = buyback_info[str(card_id)]
            quantity = info['number']
            cost_total = info['total_cost']
            
            # Budget-Prüfung
            if total_spent + cost_total > max_sp:
                remaining_budget = max_sp - total_spent
                partial_quantity = remaining_budget // info['cost_per_card']
                
                if partial_quantity > 0:
                    result = self.buyback_card(card_id, partial_quantity)
                    if result:
                        partial_cost = partial_quantity * info['cost_per_card']
                        total_spent += partial_cost
                        total_bought += partial_quantity
                print(f"⚠ Budget erreicht - verbleibende Karten übersprungen")
                break
            else:
                result = self.buyback_card(card_id, quantity)
                if result:
                    total_spent += cost_total
                    total_bought += quantity
                    sleep(0.5)
        
        print("\n" + "="*70)
        print(f"✓ {total_bought} Karten für {total_spent:,} SP zurückgekauft")
        print(f"  Verbleibende SP: {current_sp - total_spent:,}")
        print("="*70)
    
    # ==================== SHOP & KAUFEN ====================
    
    def buy_stamina(self, amount=1):
        """
        Kauft Stamina
        
        Args:
            amount: Anzahl der Käufe
        """
        try:
            result = self.api.call('buyStamina', amount=amount)
            print(f"✓ {amount}x Stamina gekauft")
            return result
        except Exception as e:
            print(f"✗ Fehler beim Kauf: {e}")
            return None
    
    def buy_energy(self, amount=1):
        """
        Kauft Arena Energy
        
        Args:
            amount: Anzahl der Käufe
        """
        try:
            result = self.api.call('buyEnergy', amount=amount)
            print(f"✓ {amount}x Arena Energy gekauft")
            return result
        except Exception as e:
            print(f"✗ Fehler beim Kauf: {e}")
            return None
    
    # ==================== SHOP – PAKETE & BATCH-SALVAGE ====================

    # ---------- Gold-Hilfsfunktion ----------

    def get_gold(self):
        """Gibt aktuelles Gold aus init_data zurück"""
        if not self.init_data:
            self.initialize()
        return int(self.init_data.get('user_data', {}).get('money', 0))
    
    def get_salvage(self):
        """Gibt aktuelle SP aus init_data zurück"""
        if not self.init_data:
            self.initialize()
        return int(self.init_data.get('user_data', {}).get('salvage', 0))

    # ---------- Pakete kaufen ----------

    def buy_pack(self):
        """Kauft einmal das 2000-Gold Paket (buyStorePromoGold)"""
        try:
            result = self.api.call(
                'buyStorePromoGold',
                expected_cost=PACK_COST,
                item_id=PACK_ITEM_ID,
                item_type=PACK_ITEM_TYPE
            )
            if result and result.get('result') == True:
                return True, result.get('new_cards', [])
            else:
                return False, []
        except Exception as e:
            print(f"✗ Kauf fehlgeschlagen: {e}")
            return False, []

    def buy_packs(self, count):
        """
        Kauft mehrere Pakete nacheinander mit Delay.

        Args:
            count: Anzahl zu kaufender Pakete

        Returns:
            (gekaufte: int, alle_neue_karten: list)
        """
        print(f"\n{'='*50}")
        print(f" KAUFE {count}x 2000-GOLD PAKET")
        print(f"{'='*50}")

        gold_vorher = self.get_gold()
        print(f" Gold vorher   : {gold_vorher:,}")
        print(f" Kosten gesamt : {count * PACK_COST:,}")

        if gold_vorher < count * PACK_COST:
            print(f"\n ✗ Nicht genug Gold!")
            print(f"   Benötigt  : {count * PACK_COST:,}")
            print(f"   Vorhanden : {gold_vorher:,}")
            return 0, []

        gekauft     = 0
        alle_karten = []

        print()  # Neue Zeile für Fortschrittsbalken
        for i in range(1, count + 1):
            # Fortschrittsbalken
            percent = int((i / count) * 100)
            bar_length = 40
            filled = int((i / count) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Zeile überschreiben mit \r
            print(f"\r [{bar}] {percent}% ({i}/{count})", end='', flush=True)
            
            success, new_cards = self.buy_pack()

            if success:
                gekauft += 1
                alle_karten.extend(new_cards)

            if i < count:
                sleep(DELAY_BETWEEN_BUYS)
        
        # Finale 100% Anzeige
        bar = '█' * bar_length
        print(f"\r [{bar}] 100% ({count}/{count})")

        # Daten aktualisieren
        self.initialize()
        gold_nachher = self.get_gold()

        print(f"\n{'─'*50}")
        print(f" Gekauft        : {gekauft}/{count}")
        print(f" Gold nachher   : {gold_nachher:,}")
        print(f" Gold ausgegeben: {gold_vorher - gold_nachher:,}")
        print(f" Neue Karten    : {len(alle_karten)}")
        print(f"{'─'*50}")

        return gekauft, alle_karten

    # ---------- Batch-Salvage ----------

    def salvage_all_commons(self):
        """
        Salvagt ALLE L1 Common Cards auf einmal (salvageL1CommonCards).
        Server berechnet alles – keine ID-Liste nötig.

        Returns:
            (success: bool, sp_gewinn: int)
        """
        print(f"\n{'='*50}")
        print(f" SALVAGE ALLE COMMON CARDS")
        print(f"{'='*50}")

        salvage_vorher = int(self.init_data.get('user_data', {}).get('salvage', 0))
        print(f" Salvage vorher: {salvage_vorher:,} SP")

        try:
            result = self.api.call('salvageL1CommonCards', dummy='data')

            if result and result.get('result') == True:
                salvage_nachher = int(result.get('user_data', {}).get('salvage', 0))
                sp_gewinn       = salvage_nachher - salvage_vorher

                print(f" ✓ Salvage erfolgreich!")
                print(f"{'─'*50}")
                print(f" Salvage nachher: {salvage_nachher:,} SP")
                print(f" SP gewonnen    : +{sp_gewinn:,} SP")
                print(f"{'─'*50}")

                self.init_data = result
                return True, sp_gewinn
            else:
                print(" ✗ Salvage fehlgeschlagen")
                return False, 0

        except Exception as e:
            print(f" ✗ Fehler: {e}")
            return False, 0

    def salvage_all_rares(self):
        """
        Salvagt ALLE L1 Rare Cards auf einmal (salvageL1RareCards).
        Analog zu salvage_all_commons.

        Returns:
            (success: bool, sp_gewinn: int)
        """
        print(f"\n{'='*50}")
        print(f" SALVAGE ALLE RARE CARDS")
        print(f"{'='*50}")

        salvage_vorher = int(self.init_data.get('user_data', {}).get('salvage', 0))
        print(f" Salvage vorher: {salvage_vorher:,} SP")

        try:
            result = self.api.call('salvageL1RareCards', dummy='data')

            if result and result.get('result') == True:
                salvage_nachher = int(result.get('user_data', {}).get('salvage', 0))
                sp_gewinn       = salvage_nachher - salvage_vorher

                print(f" ✓ Salvage erfolgreich!")
                print(f"{'─'*50}")
                print(f" Salvage nachher: {salvage_nachher:,} SP")
                print(f" SP gewonnen    : +{sp_gewinn:,} SP")
                print(f"{'─'*50}")

                self.init_data = result
                return True, sp_gewinn
            else:
                print(" ✗ Salvage fehlgeschlagen")
                return False, 0

        except Exception as e:
            print(f" ✗ Fehler: {e}")
            return False, 0

    # ---------- Workflow: Kaufen + Salvagen ----------

    def shop_salvage_workflow(self, pack_count, salvage_base_epics=False, keep_base_epics=1):
        """
        Kompletter Workflow:
          1. Pakete kaufen
          2. Alle Commons salvagen
          3. Alle Rares salvagen
          4. Optional: Base Epics salvagen (behalte X)
          5. Zusammenfassung ausgeben

        Args:
            pack_count: Anzahl zu kaufender Pakete
            salvage_base_epics: Wenn True, auch Base Epics salvagen
            keep_base_epics: Anzahl Base Epics die pro Karte behalten werden
        """
        start_time = datetime.now()

        print(f"\n{'#'*50}")
        print(f"# SHOP & SALVAGE WORKFLOW")
        print(f"# Start: {start_time.strftime('%H:%M:%S')}")
        print(f"{'#'*50}")

        # Status
        self.initialize()
        gold_start = self.get_gold()
        print(f"\n Gold Start: {gold_start:,}")

        # Kaufen
        gekauft, neue_karten = self.buy_packs(pack_count)
        if gekauft == 0:
            print("\n ✗ Keine Pakete gekauft – Workflow abgebrochen")
            return

        # Commons salvagen
        print("\n Warte 3s vor Common-Salvage...")
        sleep(3)
        success_common, sp_gewinn_common = self.salvage_all_commons()

        # Rares salvagen
        print("\n Warte 2s vor Rare-Salvage...")
        sleep(2)
        success_rare, sp_gewinn_rare = self.salvage_all_rares()

        # Base Epics salvagen (optional)
        sp_gewinn_epics = 0
        if salvage_base_epics:
            print("\n Warte 2s vor Base Epic-Salvage...")
            sleep(2)
            success_epic, sp_gewinn_epics = self.salvage_base_epics_keep_x(keep_base_epics, silent=True)

        # Zusammenfassung
        self.initialize()
        gold_ende     = self.get_gold()
        salvage_final = int(self.init_data.get('user_data', {}).get('salvage', 0))
        dauer         = (datetime.now() - start_time).seconds

        print(f"\n{'#'*50}")
        print(f"# ZUSAMMENFASSUNG")
        print(f"{'#'*50}")
        print(f" Dauer            : {dauer}s")
        print(f" Pakete gekauft   : {gekauft}")
        print(f" Neue Karten      : {len(neue_karten)}")
        print(f"")
        print(f" Gold Start       : {gold_start:,}")
        print(f" Gold Ende        : {gold_ende:,}")
        print(f" Gold Netto       : {gold_ende - gold_start:,}")
        print(f"")
        print(f" Common-Salvage   : +{sp_gewinn_common:,} SP")
        print(f" Rare-Salvage     : +{sp_gewinn_rare:,} SP")
        if salvage_base_epics:
            print(f" Epic-Salvage     : +{sp_gewinn_epics:,} SP (behalte {keep_base_epics})")
            print(f" Gesamt-Salvage   : +{sp_gewinn_common + sp_gewinn_rare + sp_gewinn_epics:,} SP")
        else:
            print(f" Gesamt-Salvage   : +{sp_gewinn_common + sp_gewinn_rare:,} SP")
        print(f"")
        print(f" Salvage-Zähler   : {salvage_final:,} SP")
        print(f"{'#'*50}\n")

    # ==================== WEITERE FUNKTIONEN ====================
    
    def auto_claim_daily_bonus(self):
        """
        Prüft und sammelt Daily Bonus automatisch beim Start.
        Zeigt Cooldown wenn nicht verfügbar.
        
        Returns:
            bool: True wenn erfolgreich abgeholt oder bereits geholt, False bei Fehler
        """
        try:
            if not self.init_data:
                self.initialize()
            
            # Prüfe daily_bonus_time in init_data
            daily_bonus_time = int(self.init_data.get('daily_bonus_time', 0))
            current_time = int(time.time())
            
            # Wenn daily_bonus_time in der Zukunft liegt, ist Cooldown aktiv
            if daily_bonus_time > current_time:
                cooldown_seconds = daily_bonus_time - current_time
                hours = cooldown_seconds // 3600
                minutes = (cooldown_seconds % 3600) // 60
                
                print(f"\n{'─'*60}")
                print(f"📅 Daily Reward")
                print(f"{'─'*60}")
                print(f"Status:   ⏳ Cooldown aktiv")
                print(f"Verfügbar in: {hours}h {minutes}min")
                print(f"{'─'*60}")
                return True
            
            # Daily Bonus ist verfügbar - hole ab
            result = self.api.call('useDailyBonus')
            
            if result and result.get('result') == True:
                print(f"\n{'─'*60}")
                print(f"📅 Daily Reward")
                print(f"{'─'*60}")
                print(f"Status:   ✓ Erfolgreich eingesammelt!")
                
                # Zeige Belohnung - versuche Kartenname zu laden
                if 'reward' in result:
                    reward = result['reward']
                    print(f"Belohnung: {reward}")
                elif 'cards' in result:
                    cards = result.get('cards', {})
                    if cards:
                        # Lade Card-Daten für Namen
                        card_data = self._load_card_data()
                        
                        # Zeige erste Karte (Daily Bonus gibt nur 1 Karte)
                        card_id = list(cards.keys())[0]
                        card_name = card_data.get(int(card_id), f"Karte #{card_id}") if card_data else f"Karte #{card_id}"
                        
                        print(f"Belohnung: {card_name}")
                
                print(f"{'─'*60}")
                
                # Daten neu laden
                self.initialize()
                return True
            else:
                # Bereits abgeholt oder Fehler
                if result and 'message' in result:
                    msg = result['message']
                    if 'already' in msg.lower() or 'bereits' in msg.lower():
                        print(f"\n{'─'*60}")
                        print(f"📅 Daily Reward")
                        print(f"{'─'*60}")
                        print(f"Status:   ✓ Bereits heute eingesammelt")
                        print(f"{'─'*60}")
                        return True
                
                return False
                
        except Exception as e:
            # Stille Fehlerbehandlung - soll den Start nicht blockieren
            return False
    
    def claim_daily_bonus(self):
        """
        Holt den täglichen Bonus ab (useDailyBonus)
        """
        try:
            print("\n" + "="*60)
            print("DAILY BONUS ABHOLEN")
            print("="*60)
            
            print("\n⏳ Hole Daily Bonus ab...")
            result = self.api.call('useDailyBonus')
            
            if result and result.get('result') == True:
                print("✓ Daily Bonus erfolgreich abgeholt!")
                
                # Zeige was erhalten wurde (falls in Response)
                if 'reward' in result:
                    reward = result['reward']
                    print(f"\nBelohnung:")
                    print(f"  {reward}")
                
                # Init-Daten neu laden
                self.initialize()
                
            else:
                print("✗ Fehler beim Abholen des Daily Bonus")
                if result:
                    # Prüfe ob bereits abgeholt
                    if 'message' in result:
                        msg = result['message']
                        if 'already' in msg.lower() or 'bereits' in msg.lower():
                            print("   Bereits heute abgeholt")
                        else:
                            print(f"   Meldung: {msg}")
                    else:
                        print(f"   API Response: {result}")
            
            print("="*60)
            
        except Exception as e:
            print(f"✗ Fehler: {e}")
            traceback.print_exc()
    
    def claim_rewards(self):
        """Holt verfügbare Belohnungen ab"""
        try:
            result = self.api.call('claimRewards')
            print("✓ Belohnungen abgeholt")
            return result
        except Exception as e:
            print(f"✗ Fehler beim Abholen: {e}")
            return None
    
    
    def export_data_to_json(self, filename=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Exportiert alle init-Daten als JSON
        Wird im SCRIPT_DIR gespeichert (data-Ordner)
        
        Args:
            filename: Dateiname (default: tyrant_data_TIMESTAMP.json)
        """
        if not self.init_data:
            self.initialize()
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tyrant_data_{timestamp}.json"
        
        # Stelle sicher dass Datei in SCRIPT_DIR gespeichert wird
        if not os.path.isabs(filename):
            filename = os.path.join(SCRIPT_DIR, filename)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.init_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Daten exportiert nach: {filename}")
            print(f"✓ Dateigröße: {os.path.getsize(filename) / 1024:.1f} KB")
            return filename
        except Exception as e:
            print(f"✗ Fehler beim Export: {e}")
            traceback.print_exc()
            return None
    
    def export_guild_decks_simple(self, output_file='guild_decks.txt'):
        """
        Exportiert Gildendecks im einfachen Format (nur IDs)
        """
        try:
            print("\n=== GUILD DECK EXPORT ===")
            
            if not self.init_data:
                print("Initialisiere API...")
                if not self.initialize():
                    print("✗ Fehler bei der Initialisierung")
                    return
            
            if 'faction' not in self.init_data:
                print("✗ Nicht in einer Gilde")
                return
            
            faction_name = self.init_data['faction']['name']
            members = self.init_data['faction']['members']
            
            print(f"\nExportiere Decks für Gilde: {faction_name}")
            print(f"Anzahl Mitglieder: {len(members)}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"// Guild: {faction_name}\n")
                f.write(f"// Export Date: {datetime.now()}\n")
                f.write(f"// Members: {len(members)}\n\n")
                
                # Gauntlet Patterns
                f.write(f"{faction_name}_D: /^{faction_name}_D_.*$/\n")
                f.write(f"{faction_name}_A: /{faction_name}_A_.*$/\n\n")
                
                # Jedes Mitglied
                for i, member_id in enumerate(members, 1):
                    try:
                        print(f"Verarbeite Mitglied {i}/{len(members)}...", end='\r')
                        
                        profile = self.api.call('getProfileData', target_user_id=str(member_id))
                        
                        if not profile or 'player_info' not in profile:
                            print(f"\n⚠ Überspringe Mitglied {member_id} - keine Daten")
                            continue
                        
                        player_info = profile['player_info']
                        
                        name = player_info.get('name', f'Unknown_{member_id}')
                        level = player_info.get('level', 0)
                        
                        # Attack Deck
                        attack_deck = player_info.get('deck', {})
                        if 'commander_id' in attack_deck:
                            deck_attack_str = f"[{attack_deck['commander_id']}]"
                            if 'dominion_id' in attack_deck and attack_deck['dominion_id']:
                                deck_attack_str += f", [{attack_deck['dominion_id']}]"
                            for card_id in attack_deck.get('cards', []):
                                deck_attack_str += f", [{card_id}]"
                        else:
                            deck_attack_str = "[0]"  # Fallback
                        
                        # Defense Deck
                        defense_deck = player_info.get('defense_deck', {})
                        if 'commander_id' in defense_deck:
                            deck_defense_str = f"[{defense_deck['commander_id']}]"
                            if 'dominion_id' in defense_deck and defense_deck['dominion_id']:
                                deck_defense_str += f", [{defense_deck['dominion_id']}]"
                            for card_id in defense_deck.get('cards', []):
                                deck_defense_str += f", [{card_id}]"
                        else:
                            deck_defense_str = "[0]"  # Fallback
                        
                        # Schreiben
                        f.write(f"// {name} (Lvl {level})\n")
                        f.write(f"{faction_name}_A_{name}: {deck_attack_str}\n")
                        f.write(f"{faction_name}_D_{name}: {deck_defense_str}\n\n")
                        
                        # Rate limiting
                        sleep(0.3)
                        
                    except KeyError as e:
                        print(f"\n✗ Fehlende Daten bei Mitglied {member_id}: {e}")
                        continue
                    except Exception as e:
                        print(f"\n✗ Fehler bei Mitglied {member_id}: {e}")
                        continue
            
            print(f"\n✓ Export abgeschlossen: {output_file}")
                
        except PermissionError as e:
            print(f"\n✗ FEHLER: Keine Schreibrechte für '{output_file}'")
            print(f"   Mögliche Lösungen:")
            print(f"   1. Schließe die Datei falls sie geöffnet ist")
            print(f"   2. Verwende einen vollständigen Pfad (z.B. C:\\Users\\...\\datei.txt)")
            print(f"   3. Führe das Skript als Administrator aus")
            print(f"   4. Wähle ein anderes Verzeichnis")
        except Exception as e:
            print(f"\n✗ KRITISCHER FEHLER beim Export: {e}")
            traceback.print_exc()
    
    # ==================== INVENTAR - KARTEN BAUEN ====================
    
    # ==================== INVENTAR - KARTEN BAUEN ====================
    
    def build_card(self, card_name_or_id=None):
        """
        Baut eine oder mehrere Karten - zeigt Rezept, Kosten, Inventar
        
        PHASE 1: Multi-Card Support
        Syntax:
        - "Luxbearer" → 1x Luxbearer-6  
        - "Luxbearer #2" → 2x Luxbearer-6
        - "Luxbearer, Daemon" → beide nacheinander
        - "Luxbearer #2, Daemon #3" → kombiniert
        
        PHASE 2: Auto-Build (noch nicht implementiert)
        PHASE 3: Smart Inventory (noch nicht implementiert)
        """
        try:
            print("\n" + "="*80)
            print("KARTE(N) BAUEN - REZEPT & KOSTEN")
            print("="*80)
            
            if not card_name_or_id:
                print("\n📋 MULTI-CARD SYNTAX:")
                print("  Einzelne Karte:     Luxbearer")
                print("  Mehrere Kopien:     Luxbearer #2")
                print("  Mehrere Karten:     Luxbearer, Daemon")
                print("  Kombiniert:         Luxbearer #2, Daemon, Aasi #3")
                
                card_name_or_id = input_with_esc("\nKartenname(n) oder ID(s) (ESC=Abbruch): ")
                if card_name_or_id is None:
                    return
                
                card_name_or_id = card_name_or_id.strip()
                if not card_name_or_id:
                    print("✗ Keine Eingabe")
                    return
            
            # ===== PHASE 1: PARSE INPUT =====
            card_requests = []
            card_counts = {}  # {card_name: total_count}
            
            for part in card_name_or_id.split(','):
                part = part.strip()
                if not part:
                    continue
                
                # Entferne führende Sonderzeichen (wie : aus Copy-Paste Fehlern)
                part = part.lstrip(':;.,-_ ')
                part = part.strip()
                
                if not part:
                    continue
                
                # Parse #count Syntax
                count = 1
                if '#' in part:
                    card_part, count_part = part.rsplit('#', 1)
                    try:
                        count = int(count_part.strip())
                        part = card_part.strip()
                    except ValueError:
                        print(f"⚠ Ungültiges Count-Format in '{part}', verwende Count=1")
                
                # Normalisiere Namen (lowercase für Vergleich)
                part_normalized = part.lower().strip()
                
                # Addiere counts wenn Karte schon in Liste
                if part_normalized in card_counts:
                    card_counts[part_normalized]['count'] += count
                else:
                    card_counts[part_normalized] = {'name': part, 'count': count}
            
            # Konvertiere zu Liste
            card_requests = [data for data in card_counts.values()]
            
            if not card_requests:
                print("✗ Keine gültigen Karten gefunden")
                return
            
            # Zeige was gebaut werden soll
            print(f"\n✓ {len(card_requests)} Karte(n) zum Bauen:")
            total_count = sum(req['count'] for req in card_requests)
            for req in card_requests:
                print(f"  • {req['count']}x {req['name']}")
            print(f"\nGesamt: {total_count} Karte(n)")
            
            # ===== BAUE JEDE KARTE =====
            for idx, req in enumerate(card_requests, 1):
                print("\n" + "="*80)
                if req['count'] > 1:
                    print(f"KARTE {idx}/{len(card_requests)}: {req['count']}x {req['name']}")
                else:
                    print(f"KARTE {idx}/{len(card_requests)}: {req['name']}")
                print("="*80)
                
                # Rufe single card build auf (mit count)
                success = self._build_single_card_info(req['name'], req['count'])
                
                if not success:
                    print(f"\n⚠ Fehler bei {req['name']}")
                    if not confirm_action("Fortfahren mit nächster Karte?"):
                        print("\n✗ Abgebrochen")
                        return
            
            print("\n" + "="*80)
            print("✅ ALLE KARTEN ANALYSIERT!")
            print("="*80)
            
        except Exception as e:
            print(f"✗ Fehler in build_card: {e}")
            traceback.print_exc()
    
    def _build_single_card_info(self, card_name_or_id, build_count=1):
        """
        Zeigt Info für eine einzelne Karte (Rezept, Kosten, Inventar)
        Phase 1: Nur Info anzeigen
        Phase 2: Wird erweitert mit Auto-Build
        
        Args:
            card_name_or_id: Name oder ID der Karte
            build_count: Anzahl wie oft diese Karte gebaut werden soll (für SP-Kosten)
        
        Returns: True wenn erfolgreich, False bei Fehler
        """
        try:
            # Lade Card-Daten mit allen Upgrade-Leveln
            print("\n⏳ Lade Card-Daten...")
            
            card_data = {}
            import glob
            import xml.etree.ElementTree as ET
            
            card_files = glob.glob(os.path.join(SCRIPT_DIR, 'cards_section_*.xml'))
            if not card_files:
                print(f"✗ Keine cards_section_*.xml Dateien in {SCRIPT_DIR}")
                return False
            
            for card_file in card_files:
                tree = ET.parse(card_file)
                for unit in tree.getroot().findall('.//unit'):
                    base_id = unit.find('id')
                    base_name = unit.find('name')
                    base_rarity = unit.find('rarity')
                    
                    if base_id is None or base_name is None:
                        continue
                    
                    # Base Card (Level 1)
                    card_data[base_id.text] = {
                        'name': base_name.text,
                        'rarity': int(base_rarity.text) if base_rarity is not None else 0,
                        'level': 1,
                        'base_id': base_id.text
                    }
                    
                    # Alle Upgrades (Level 2-6+)
                    for upgrade in unit.findall('.//upgrade'):
                        upgrade_card_id = upgrade.find('card_id')
                        upgrade_level = upgrade.find('level')
                        
                        if upgrade_card_id is not None and upgrade_level is not None:
                            card_data[upgrade_card_id.text] = {
                                'name': base_name.text,
                                'rarity': int(base_rarity.text) if base_rarity is not None else 0,
                                'level': int(upgrade_level.text),
                                'base_id': base_id.text
                            }
            
            print(f"✓ {len(card_data)} Card-IDs geladen")
            
            # Lade Fusion Recipes
            print("⏳ Lade Fusion Recipes...")
            
            fusion_file = os.path.join(SCRIPT_DIR, 'fusion_recipes_cj2.xml')
            if not os.path.exists(fusion_file):
                print(f"✗ fusion_recipes_cj2.xml nicht gefunden in {SCRIPT_DIR}")
                return False
            
            tree = ET.parse(fusion_file)
            recipes = {}
            
            for recipe in tree.getroot().findall('fusion_recipe'):
                card_id_elem = recipe.find('card_id')
                if card_id_elem is not None:
                    result_id = card_id_elem.text
                    resources = []
                    for res in recipe.findall('resource'):
                        resources.append({
                            'card_id': res.get('card_id'),
                            'number': int(res.get('number'))
                        })
                    recipes[result_id] = resources
            
            print(f"✓ {len(recipes)} Fusion Recipes geladen")
            
            # Lade SP-Kosten
            print("⏳ Lade SP-Kosten...")
            
            levels_file = os.path.join(SCRIPT_DIR, 'levels.xml')
            if not os.path.exists(levels_file):
                print(f"✗ levels.xml nicht gefunden in {SCRIPT_DIR}")
                return False
            
            tree = ET.parse(levels_file)
            sp_costs = {}
            
            for card_level in tree.getroot().findall('card_level'):
                rarity = card_level.find('rarity')
                level = card_level.find('level')
                sp_cost = card_level.find('sp_cost')
                
                if rarity is not None and level is not None and sp_cost is not None:
                    key = (int(rarity.text), int(level.text))
                    sp_costs[key] = int(sp_cost.text)
            
            # Speichere als Member für Smart Inventory
            self.sp_costs = sp_costs
            
            print(f"✓ SP-Kosten Tabelle geladen")
            
            # Finde Ziel-Karte
            print(f"\n⏳ Suche nach '{card_name_or_id}'...")
            
            target_id = None
            target_name = None
            target_level = None
            
            # Ist es eine ID?
            if card_name_or_id.isdigit():
                if card_name_or_id in card_data:
                    target_id = card_name_or_id
                    target_name = card_data[target_id]['name']
                    target_level = card_data[target_id]['level']
            else:
                # Suche nach Namen - NIMM LEVEL 6 als Standard
                search_name = card_name_or_id.lower().replace('-6', '').replace('-', '')
                
                # Zuerst suche Level 6
                for cid, info in card_data.items():
                    card_name_clean = info['name'].lower().replace('-', '')
                    if search_name in card_name_clean and info['level'] == 6:
                        target_id = cid
                        target_name = info['name']
                        target_level = 6
                        break
                
                # Falls nicht gefunden, suche Level 1
                if not target_id:
                    for cid, info in card_data.items():
                        card_name_clean = info['name'].lower().replace('-', '')
                        if search_name in card_name_clean and info['level'] == 1:
                            target_id = cid
                            target_name = info['name']
                            target_level = 1
                            break
            
            if not target_id:
                print(f"✗ Karte '{card_name_or_id}' nicht gefunden")
                return False
            
            target_info = card_data[target_id]
            print(f"✓ Gefunden: {target_name}-{target_level} (ID {target_id}, Rarity {target_info['rarity']})")
            
            # Wenn Level 6, müssen wir von Level 1 Base starten
            if target_level == 6:
                base_target_id = target_info['base_id']
                print(f"  → Baue von {target_name}-1 (ID {base_target_id}) und upgrade zu Level 6")
            else:
                base_target_id = target_id
            
            # Prüfe ob Rezept existiert
            if base_target_id not in recipes:
                print(f"\n⚠ Kein Fusion-Rezept für {target_name}-1")
                print("   → Diese Karte kann nicht gebaut werden (Base-Karte oder Drop)")
                
                # Zeige nur Upgrade-Kosten
                if target_level > 1:
                    rarity = target_info['rarity']
                    total_cost = 0
                    steps = []
                    
                    for lvl in range(1, target_level):
                        key = (rarity, lvl)
                        if key in sp_costs:
                            cost = sp_costs[key]
                            total_cost += cost
                            steps.append(str(cost))
                    
                    print(f"\nUpgrade-Kosten: {' + '.join(steps)} = {total_cost} SP")
                
                return True  # Kein Fehler, nur keine Fusion möglich
            
            # Berechne alle Base-Karten (OHNE Ausgabe)
            
            def get_all_base_cards(card_id, multiplier=1):
                """Rekursiv alle Base-Karten finden - prüft auch Base-IDs von Upgrade-Versionen"""
                # Prüfe ob diese Card ein Rezept hat
                if card_id in recipes:
                    # Hat Rezept - weiter auflösen
                    all_cards = {}
                    for res in recipes[card_id]:
                        sub_cards = get_all_base_cards(res['card_id'], res['number'] * multiplier)
                        for sub_id, count in sub_cards.items():
                            if sub_id in all_cards:
                                all_cards[sub_id] += count
                            else:
                                all_cards[sub_id] = count
                    return all_cards
                
                # Kein Rezept für diese ID - prüfe ob es eine Upgrade-Version ist
                info = card_data.get(card_id, {})
                base_id = info.get('base_id', card_id)
                
                # Falls das eine Upgrade-Version ist, prüfe ob die Base-Version ein Rezept hat
                if base_id != card_id and base_id in recipes:
                    # Die Level-1 Version hat ein Rezept!
                    all_cards = {}
                    for res in recipes[base_id]:
                        sub_cards = get_all_base_cards(res['card_id'], res['number'] * multiplier)
                        for sub_id, count in sub_cards.items():
                            if sub_id in all_cards:
                                all_cards[sub_id] += count
                            else:
                                all_cards[sub_id] = count
                    return all_cards
                
                # Echte Base-Karte (weder diese ID noch Base-ID hat Rezept)
                return {card_id: multiplier}
            
            base_cards = get_all_base_cards(base_target_id)
            
            # SP-Kosten berechnen
            print("="*80)
            print("\nAnnahme: Alle Base-Karten auf Level 1 vorhanden\n")
            
            # Sammle ALLE Karten die upgegraded werden müssen
            def collect_all_needed_upgrades(card_id, result_level=None, multiplier=1):
                """
                Sammelt alle Upgrade-Schritte die nötig sind
                Returns: dict {base_id: {'level': target_level, 'count': anzahl}}
                """
                upgrades = {}
                
                # Wenn diese Card eine Upgrade-Version ist, hole Base-ID
                info = card_data.get(card_id, {})
                base_id = info.get('base_id', card_id)
                needed_level = info.get('level', 1)
                
                # Prüfe ob Base-Version ein Rezept hat
                if base_id in recipes:
                    # Diese Fusion-Karte muss gebaut werden
                    # Und dann auf needed_level upgegraded werden
                    if needed_level > 1:
                        if base_id in upgrades:
                            upgrades[base_id]['count'] += multiplier
                            upgrades[base_id]['level'] = max(upgrades[base_id]['level'], needed_level)
                        else:
                            upgrades[base_id] = {'level': needed_level, 'count': multiplier}
                    
                    # Rekursiv: Sammle Upgrades für alle Komponenten
                    for res in recipes[base_id]:
                        sub_upgrades = collect_all_needed_upgrades(res['card_id'], multiplier=res['number'] * multiplier)
                        for sub_base_id, sub_data in sub_upgrades.items():
                            if sub_base_id in upgrades:
                                # Addiere count, nimm max level
                                upgrades[sub_base_id]['count'] += sub_data['count']
                                upgrades[sub_base_id]['level'] = max(upgrades[sub_base_id]['level'], sub_data['level'])
                            else:
                                upgrades[sub_base_id] = sub_data.copy()
                
                elif card_id not in recipes:
                    # Base-Karte (keine Fusion)
                    # Muss auf needed_level upgegraded werden
                    if needed_level > 1:
                        if base_id in upgrades:
                            upgrades[base_id]['count'] += multiplier
                            upgrades[base_id]['level'] = max(upgrades[base_id]['level'], needed_level)
                        else:
                            upgrades[base_id] = {'level': needed_level, 'count': multiplier}
                
                return upgrades
            
            # Sammle alle nötigen Upgrades
            all_upgrades = collect_all_needed_upgrades(base_target_id)
            
            # Füge finales Upgrade hinzu (Luxbearer-1 → Luxbearer-6)
            if target_level > 1:
                if base_target_id in all_upgrades:
                    all_upgrades[base_target_id]['count'] += 1
                    all_upgrades[base_target_id]['level'] = max(all_upgrades[base_target_id]['level'], target_level)
                else:
                    all_upgrades[base_target_id] = {'level': target_level, 'count': 1}
            
            total_sp = 0
            
            # Berechne SP (ohne Ausgabe der Details)
            for base_id, data in all_upgrades.items():
                info = card_data.get(base_id, {'name': f'ID {base_id}', 'rarity': 0})
                rarity = info['rarity']
                target_lv = data['level']
                count = data['count']
                
                cost_per = 0
                for lvl in range(1, target_lv):
                    key = (rarity, lvl)
                    if key in sp_costs:
                        cost_per += sp_costs[key]
                
                if cost_per > 0:
                    total_sp += cost_per * count
            
            # Multipliziere mit build_count
            if build_count > 1:
                total_sp = total_sp * build_count
            
            # Inventar-Check
            print("\n" + "="*80)
            print("INVENTAR-CHECK")
            if build_count > 1:
                print(f"({build_count}x {target_name}-{target_level})")
            print("="*80)
            
            if not self.init_data:
                self.initialize()
            
            user_cards = self.init_data.get('user_cards', {})
            user_sp = int(self.init_data['user_data'].get('salvage', 0))
            
            print(f"\nSP-Guthaben: {user_sp:,} SP")
            print(f"SP-Kosten:   {total_sp:,} SP")
            if build_count > 1:
                per_card_sp = total_sp // build_count
                print(f"             ({per_card_sp:,} SP pro Karte × {build_count})")
            
            missing = []
            total_cards_ok = 0
            
            for card_id, needed in base_cards.items():
                # Hole Base-ID (Level 1 Version)
                info = card_data.get(card_id, {})
                base_id = info.get('base_id', card_id)
                
                owned = 0
                if base_id in user_cards:
                    owned = int(user_cards[base_id].get('num_owned', 0))
                
                card_name = info.get('name', f'ID {card_id}')
                
                # Multipliziere needed mit build_count
                total_needed = needed * build_count
                
                if owned >= total_needed:
                    total_cards_ok += 1
                else:
                    missing.append(f"✗ {card_name}: {owned}/{total_needed} (fehlt {total_needed - owned})")
            
            # Zeige nur Zusammenfassung wenn alles OK
            if not missing:
                print(f"\n✓ Alle {total_cards_ok} Basiskarten verfügbar")
            else:
                print(f"\n✓ {total_cards_ok}/{len(base_cards)} Basiskarten verfügbar")
                print("\nFehlt:")
                for msg in missing:
                    print(f"  {msg}")
                print("\n⚠ Kann nicht gebaut werden - Karten fehlen")
                return True  # Info wurde angezeigt, kein Fehler
            
            if user_sp < total_sp:
                print(f"\n⚠ Kann nicht gebaut werden - SP fehlt ({user_sp:,}/{total_sp:,})")
                return True
            else:
                print("\n🎉 ALLE KARTEN VERFÜGBAR UND GENUG SP!")
                
                # ===== PHASE 2: AUTO-BUILD =====
                if not confirm_action(f"\n🔨 Jetzt {build_count}x {target_name}-{target_level} bauen?"):
                    print("✓ Abgebrochen")
                    return True
                
                # SP vorher merken
                sp_before = user_sp
                
                print("\n" + "="*80)
                print("🔨 AUTO-BUILD GESTARTET")
                print("="*80)
                
                # Baue jede Kopie
                for copy_idx in range(build_count):
                    if build_count > 1:
                        print(f"\n{'─'*80}")
                        print(f"📦 BAUE KOPIE {copy_idx + 1}/{build_count}")
                        print(f"{'─'*80}")
                    
                    # Führe Build aus
                    success = self._execute_build(
                        target_name=target_name,
                        target_level=target_level,
                        base_target_id=base_target_id,
                        card_data=card_data,
                        recipes=recipes,
                        sp_costs=sp_costs
                    )
                    
                    if not success:
                        print(f"\n✗ Build fehlgeschlagen bei Kopie {copy_idx + 1}")
                        if copy_idx < build_count - 1:
                            if not confirm_action(f"Fortfahren mit nächster Kopie?"):
                                break
                        break
                    
                    # Reload Inventar für nächste Kopie
                    if copy_idx < build_count - 1:
                        self.initialize()
                
                # SP nachher holen
                self.initialize()
                sp_after = int(self.init_data['user_data'].get('salvage', 0))
                sp_used = sp_before - sp_after
                
                # Berechne theoretische Kosten (ohne Smart Inventory)
                sp_theoretical = total_sp
                sp_saved_total = sp_theoretical - sp_used
                
                print("\n" + "="*80)
                print("✅ AUTO-BUILD ABGESCHLOSSEN")
                print("="*80)
                print(f"\nSP vorher:      {sp_before:,} SP")
                print(f"SP nachher:     {sp_after:,} SP")
                print(f"SP benutzt:     {sp_used:,} SP")
                if sp_saved_total > 0:
                    print(f"SP gespart:     {sp_saved_total:,} SP 💡 (Smart Inventory)")
                    print(f"Effizienz:      {100 - (sp_used * 100 // sp_theoretical)}% weniger SP")
            
            return True
            
        except Exception as e:
            print(f"✗ Fehler in _build_single_card_info: {e}")
            traceback.print_exc()
            return False
    
    def _find_best_card_in_inventory(self, base_id, target_level, card_data):
        """
        PHASE 3: SMART INVENTORY
        
        Findet die beste verfügbare Version einer Karte im Inventar.
        Bevorzugt höhere Levels um SP zu sparen.
        
        Args:
            base_id: Base-ID der Karte (Level 1)
            target_level: Benötigtes Level
            card_data: Card info dictionary
        
        Returns:
            (card_id, current_level, sp_saved) tuple
            - card_id: ID der besten gefundenen Karte
            - current_level: Level der gefundenen Karte
            - sp_saved: Gesparte SP im Vergleich zu Level 1
        """
        if not self.init_data:
            self.initialize()
        
        user_cards = self.init_data.get('user_cards', {})
        base_info = card_data.get(base_id, {})
        rarity = base_info.get('rarity', 0)
        
        # Sammle alle verfügbaren Levels dieser Karte
        available_levels = []
        
        # Level 1 (Base) prüfen
        if base_id in user_cards and int(user_cards[base_id].get('num_owned', 0)) > 0:
            available_levels.append((base_id, 1, 0))  # (card_id, level, sp_saved)
        
        # Alle Upgrade-Levels prüfen (2 bis target_level)
        for check_level in range(2, target_level + 1):
            for cid, info in card_data.items():
                if info.get('base_id') == base_id and info.get('level') == check_level:
                    # Prüfe ob im Inventar
                    if cid in user_cards and int(user_cards[cid].get('num_owned', 0)) > 0:
                        # Berechne gesparte SP
                        sp_saved = 0
                        for lvl in range(1, check_level):
                            key = (rarity, lvl)
                            if key in self.sp_costs:
                                sp_saved += self.sp_costs[key]
                        
                        available_levels.append((cid, check_level, sp_saved))
                    break
        
        if not available_levels:
            # Nichts verfügbar - verwende Level 1 (wird später gebaut)
            return (base_id, 1, 0)
        
        # Sortiere nach Level (höchstes zuerst) um max SP zu sparen
        available_levels.sort(key=lambda x: x[1], reverse=True)
        
        return available_levels[0]
    
    def _execute_build(self, target_name, target_level, base_target_id, card_data, recipes, sp_costs):
        """
        Führt den kompletten Build-Prozess für eine Karte aus
        
        Returns: True wenn erfolgreich, False bei Fehler
        """
        try:
            print(f"\n⏳ Baue {target_name}-{target_level}...")
            
            # Schritt 1: Baue die Level-1 Version (rekursiv)
            if base_target_id in recipes:
                print(f"  → Baue zuerst {target_name}-1 (Fusion)")
                
                built_card_id = self._build_card_recursive(
                    base_target_id,
                    card_data,
                    recipes,
                    sp_costs
                )
                
                if not built_card_id:
                    print(f"✗ Fehler beim Bauen von {target_name}-1")
                    return False
            else:
                # Keine Fusion, Karte muss im Inventar sein
                built_card_id = base_target_id
            
            # Schritt 2: Upgrade auf Ziel-Level
            if target_level > 1:
                print(f"\n  → Upgrade {target_name}-1 zu {target_name}-{target_level}")
                
                # PHASE 3: SMART INVENTORY - prüfe ob bereits höheres Level vorhanden
                base_id = base_target_id
                best_card_id, best_level, sp_saved = self._find_best_card_in_inventory(
                    base_id, target_level, card_data
                )
                
                if sp_saved > 0:
                    print(f"    💡 Smart: Nutze {target_name}-{best_level} (spart {sp_saved} SP)")
                
                current_id = best_card_id if best_level > 1 else built_card_id
                current_level = best_level
                
                while current_level < target_level:
                    # Upgrade um 1 Level (silent)
                    result = self.api.call('upgradeCard', card_id=current_id)
                    
                    if not result or result.get('result') != True:
                        print(f"    ✗ Upgrade fehlgeschlagen bei Level {current_level}!")
                        return False
                    
                    # Nächste ID finden (upgraded version)
                    base_info = card_data.get(current_id, {})
                    base_id = base_info.get('base_id', current_id)
                    
                    # Suche nach der upgrade_id für nächstes Level
                    next_level = current_level + 1
                    for cid, info in card_data.items():
                        if info.get('base_id') == base_id and info.get('level') == next_level:
                            current_id = cid
                            break
                    
                    current_level += 1
                    
                    # Kleine Pause
                    time.sleep(0.3)
                
                print(f"    ✓ Upgrade abgeschlossen")
            
            print(f"\n✅ {target_name}-{target_level} erfolgreich gebaut!")
            return True
            
        except Exception as e:
            print(f"✗ Fehler in _execute_build: {e}")
            traceback.print_exc()
            return False
    
    def _build_card_recursive(self, card_id, card_data, recipes, sp_costs):
        """
        Baut eine Karte rekursiv (inklusive aller Sub-Komponenten)
        
        Returns: card_id der gebauten Karte, oder None bei Fehler
        """
        try:
            info = card_data.get(card_id, {'name': f'ID {card_id}', 'level': 1})
            card_name = info['name']
            card_level = info['level']
            
            # Prüfe ob Rezept existiert
            if card_id not in recipes:
                # Keine Fusion - Karte muss im Inventar sein (oder ist schon gebaut)
                return card_id
            
            print(f"\n  🔧 Baue {card_name}-{card_level} (Fusion)")
            
            # Hole Rezept
            recipe_resources = recipes[card_id]
            
            # Baue/Upgrade alle Komponenten
            for res in recipe_resources:
                res_id = res['card_id']
                res_count = res['number']
                res_info = card_data.get(res_id, {'name': f'ID {res_id}', 'level': 1})
                res_name = res_info['name']
                res_level = res_info['level']
                
                print(f"    → Benötigt: {res_count}x {res_name}-{res_level}")
                
                # Wenn Komponente eine Upgrade-Version ist, müssen wir upgraden
                if res_level > 1:
                    # Hole Base-ID
                    base_id = res_info.get('base_id', res_id)
                    base_info = card_data.get(base_id, {})
                    base_name = base_info.get('name', res_name)
                    
                    # Prüfe ob Base-Version ein Rezept hat
                    if base_id in recipes:
                        # Baue Base-Version rekursiv
                        built_base = self._build_card_recursive(base_id, card_data, recipes, sp_costs)
                        if not built_base:
                            return None
                    
                    # PHASE 3: SMART INVENTORY - Finde beste verfügbare Version
                    best_card_id, best_level, sp_saved = self._find_best_card_in_inventory(
                        base_id, res_level, card_data
                    )
                    
                    if sp_saved > 0:
                        print(f"      💡 Smart: Nutze {base_name}-{best_level} (spart {sp_saved} SP)")
                    
                    # Upgrade von best_level zu res_level
                    current_id = best_card_id
                    for lvl in range(best_level, res_level):
                        result = self.api.call('upgradeCard', card_id=current_id)
                        
                        if not result or result.get('result') != True:
                            print(f"      ✗ Upgrade {base_name} fehlgeschlagen bei Level {lvl}!")
                            return None
                        
                        # Finde nächste upgrade_id
                        for cid, cinfo in card_data.items():
                            if cinfo.get('base_id') == base_id and cinfo.get('level') == lvl + 1:
                                current_id = cid
                                break
                        
                        time.sleep(0.2)
                else:
                    # Level 1 - prüfe ob Fusion nötig
                    if res_id in recipes:
                        # Rekursiv bauen
                        built = self._build_card_recursive(res_id, card_data, recipes, sp_costs)
                        if not built:
                            return None
            
            # Alle Komponenten bereit - jetzt fusionieren
            print(f"    🔗 Fusioniere → {card_name}-{card_level}")
            
            result = self.api.call('fuseCard', card_id=card_id)
            
            if not result or result.get('result') != True:
                print(f"    ✗ Fusion fehlgeschlagen!")
                return None
            
            print(f"    ✓ {card_name}-{card_level} erfolgreich fusioniert!")
            
            time.sleep(0.3)
            
            return card_id
            
        except Exception as e:
            print(f"✗ Fehler in _build_card_recursive: {e}")
            traceback.print_exc()
            return None
    
    # ==================== DOMINION FUNKTIONEN ====================
    #
    # HAUPT-FUNKTION:
    #   build_dominion_autobuild() - Auto-Build mit Reset-Support
    #
    # HELPER-FUNKTIONEN (intern verwendet):
    #   _calculate_fusion_path()   - BFS-Pfadberechnung
    #   _execute_fusion_path()     - Führt Fusion-Pfad aus
    #   _execute_simple_upgrade()  - Einfaches Upgrade (gleicher Tier)
    #   _calculate_upgrade_cost()  - Berechnet Shard-Kosten
    #
    # LEGACY-FUNKTIONEN (nicht mehr im Menü):
    #   reset_dominion()           - Manueller Reset
    #   upgrade_dominion()         - Manuelles Upgrade
    #   show_dominion_fusions()    - Zeigt verfügbare Fusionen
    #
    # ==============================================================
    
    def reset_dominion(self, dominion_card_id=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Resettet ein Dominion zurück auf die Basis-Versionen
        Wird intern von build_dominion_autobuild() verwendet
        
        WICHTIG: Reset gibt zurück:
        - Alpha Dominion-2 (ID 50002) - NICHT Level 1!
        - Nexus Dominion-2 (ID 50239) - NICHT Level 1!
        - Alle verwendeten Materialien (Shards, Fusion-Karten, etc.)
        
        Level 1 Versionen (50001, 50238) existieren nicht im Spiel!
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER neu laden um aktuelle Daten zu haben
            self.initialize()
            
            # Lade Card-Daten
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Konnte Card-Daten nicht laden")
                return False
            
            # Wenn keine ID angegeben, zeige verfügbare Dominions aus Inventar
            if dominion_card_id is None:
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde alle Dominions im Inventar
                available_dominions = []
                for card_id, info in user_cards.items():
                    card_id_int = int(card_id)
                    if card_id_int in DOMINION_IDS:
                        card_info = self._get_card_info(card_data, card_id_int)
                        card_name = card_info.get('name', f'ID {card_id}')
                        card_level = card_info.get('level', 1)
                        num_owned = int(info.get('num_owned', 0))
                        
                        if num_owned > 0:
                            available_dominions.append({
                                'id': card_id_int,
                                'name': card_name,
                                'level': card_level,
                                'count': num_owned
                            })
                
                if not available_dominions:
                    print("✗ Keine Dominions im Inventar gefunden")
                    return False
                
                # Sortiere nach Name
                available_dominions.sort(key=lambda x: x['name'])
                
                print("\n" + "="*50)
                print("VERFÜGBARE DOMINIONS")
                print("="*50)
                
                for idx, dom in enumerate(available_dominions, 1):
                    print(f"{idx}. {dom['name']}")
                
                print("="*50)
                
                # Auswahl mit Wiederholung bei ungültiger Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer oder ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Ungültige Auswahl: '{choice}'")
                            print(f"   Bitte wähle eine Nummer zwischen 1 und {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Gültige Auswahl - verlasse Loop
                        break
                    except ValueError:
                        print(f"✗ Ungültige Eingabe: '{choice}'")
                        print("   Bitte gib eine Nummer ein")
                        continue  # Wiederhole Eingabe
                
                dominion_card_id = available_dominions[idx]['id']
            
            # Hole Dominion-Info
            dominion_info = card_data.get(dominion_card_id, {})
            dominion_name = dominion_info.get('name', f'ID {dominion_card_id}')
            dominion_level = dominion_info.get('level', 1)
            
            # Prüfe ob es wirklich ein Dominion ist
            if dominion_card_id not in DOMINION_IDS:
                print(f"✗ {dominion_name} (ID {dominion_card_id}) ist kein Dominion")
                return False
            
            # Prüfe ob im Inventar
            user_cards = self.init_data.get('user_cards', {})
            card_count = int(user_cards.get(str(dominion_card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Entferne Level-Suffix aus Name falls vorhanden (Name enthält bereits "-X")
                display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
                print(f"✗ {display_name}-{dominion_level} nicht im Inventar")
                return False
            
            # Entferne Level-Suffix aus Name für Anzeige
            display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
            
            print(f"\n🔄 Resettet {display_name}-{dominion_level}")
            
            # Bestätigung
            if not confirm_action(f"Wirklich {display_name}-{dominion_level} zurück auf Level 1 setzen?"):
                print("Abgebrochen")
                return False
            
            # API Call: respecDominionCard
            print(f"⏳ Sende Reset-Anfrage...")
            result = self.api.call('respecDominionCard', card_id=dominion_card_id)
            
            if not result or result.get('result') != True:
                print(f"✗ Reset fehlgeschlagen!")
                print(f"Response: {result}")
                return False
            
            # Hole Base-ID (Level 1 Version)
            base_id = dominion_info.get('base_id', dominion_card_id)
            base_info = card_data.get(base_id, {})
            base_name = base_info.get('name', dominion_name)
            
            print(f"✅ {dominion_name} wurde erfolgreich zurückgesetzt!")
            
            # Zeige was zurückgegeben wurde (falls vorhanden)
            # Erfolg - keine Details nötig
            return True
            
        except Exception as e:
            print(f"✗ Fehler beim Reset: {e}")
            traceback.print_exc()
            return False
    
    def upgrade_dominion(self, dominion_card_id=None, target_level=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Upgraded ein Dominion auf ein bestimmtes Level
        Wird intern von build_dominion_autobuild() verwendet
        
        Args:
            dominion_card_id: Die Card-ID des Dominions (optional, wird bei None abgefragt)
            target_level: Ziel-Level (optional, wird bei None abgefragt)
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER neu laden um aktuelle Daten zu haben
            self.initialize()
            
            # Lade Card-Daten
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Konnte Card-Daten nicht laden")
                return False
            
            # Wenn keine ID angegeben, zeige verfügbare Dominions aus Inventar
            if dominion_card_id is None:
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde alle Dominions im Inventar
                available_dominions = []
                for card_id, info in user_cards.items():
                    card_id_int = int(card_id)
                    if card_id_int in DOMINION_IDS:
                        card_info = self._get_card_info(card_data, card_id_int)
                        card_name = card_info.get('name', f'ID {card_id}')
                        card_level = card_info.get('level', 1)
                        num_owned = int(info.get('num_owned', 0))
                        
                        if num_owned > 0:
                            available_dominions.append({
                                'id': card_id_int,
                                'name': card_name,
                                'level': card_level,
                                'count': num_owned
                            })
                
                if not available_dominions:
                    print("✗ Keine Dominions im Inventar gefunden")
                    return False
                
                # Sortiere nach Name
                available_dominions.sort(key=lambda x: x['name'])
                
                print("\n" + "="*50)
                print("VERFÜGBARE DOMINIONS")
                print("="*50)
                
                for idx, dom in enumerate(available_dominions, 1):
                    print(f"{idx}. {dom['name']}")
                
                print("="*50)
                
                # Auswahl mit Wiederholung bei ungültiger Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer oder ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Ungültige Auswahl: '{choice}'")
                            print(f"   Bitte wähle eine Nummer zwischen 1 und {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Gültige Auswahl - verlasse Loop
                        break
                    except ValueError:
                        print(f"✗ Ungültige Eingabe: '{choice}'")
                        print("   Bitte gib eine Nummer ein")
                        continue  # Wiederhole Eingabe
                
                dominion_card_id = available_dominions[idx]['id']
            
            # Hole Dominion-Info
            dominion_info = card_data.get(dominion_card_id, {})
            dominion_name = dominion_info.get('name', f'ID {dominion_card_id}')
            current_level = dominion_info.get('level', 1)
            base_id = dominion_info.get('base_id', dominion_card_id)
            
            # Prüfe ob es wirklich ein Dominion ist
            if dominion_card_id not in DOMINION_IDS:
                print(f"✗ {dominion_name} (ID {dominion_card_id}) ist kein Dominion")
                return False
            
            # Prüfe ob im Inventar
            user_cards = self.init_data.get('user_cards', {})
            card_count = int(user_cards.get(str(dominion_card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Entferne Level-Suffix aus Name falls vorhanden (Name enthält bereits "-X")
                display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
                print(f"✗ {display_name}-{current_level} nicht im Inventar")
                return False
            
            # Wenn kein Ziel-Level angegeben, frage
            if target_level is None:
                # Finde max Level für dieses Dominion
                max_level = current_level
                for cid, cinfo in card_data.items():
                    if cinfo.get('base_id') == base_id:
                        max_level = max(max_level, cinfo.get('level', 1))
                
                print(f"\n📊 {dominion_name} ist aktuell Level {current_level}")
                print(f"   Max Level: {max_level}")
                
                level_input = input_with_esc(f"\nZiel-Level (1-{max_level}, ESC=Abbruch): ")
                if level_input is None:
                    return False
                
                try:
                    target_level = int(level_input)
                    if target_level < 1 or target_level > max_level:
                        print(f"✗ Level muss zwischen 1 und {max_level} sein")
                        return False
                except ValueError:
                    print("✗ Ungültige Eingabe")
                    return False
            
            # Prüfe ob Upgrade nötig
            if target_level == current_level:
                print(f"ℹ {dominion_name} ist bereits Level {current_level}")
                return True
            
            if target_level < current_level:
                print(f"⚠ {dominion_name} ist bereits Level {current_level}, kann nicht auf {target_level} downgraden")
                print(f"   Nutze reset_dominion() um zurück auf Level 1 zu setzen")
                return False
            
            # Berechne Upgrade-Kosten
            upgrades_needed = target_level - current_level
            
            # WICHTIG: Dominions verwenden Dominion Shards (43452), nicht SP!
            # Die Kosten hängen vom Fusion Level ab (welche Alpha/Nexus Levels fusioniert wurden)
            
            # Bestimme Tier des Dominions für Upgrade-Kosten
            dominion_tier = get_dominion_tier(dominion_card_id)
            
            # Berechne Shard-Kosten
            total_shards = 0
            for lvl in range(current_level, target_level):
                next_lvl = lvl + 1
                if next_lvl in DOMINION_TIER_UPGRADE_COSTS[dominion_tier]:
                    total_shards += DOMINION_TIER_UPGRADE_COSTS[dominion_tier][next_lvl]
            
            # Hole aktuelle Dominion Shards im Inventar
            user_cards = self.init_data.get('user_cards', {})
            shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
            current_shards = int(shard_info.get('num_owned', 0))
            
            # Fusion Level Name für Ausgabe
            # Entferne Level-Suffix aus Name für Anzeige (Name enthält bereits "-X")
            base_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
            
            print(f"\n📊 Upgrade-Plan:")
            print(f"   Von: {base_name}-{current_level}")
            print(f"   Zu:  {base_name}-{target_level}")
            print(f"   Upgrades: {upgrades_needed}")
            print(f"   Dominion Shards: {total_shards:,} benötigt")
            print(f"   Verfügbar: {current_shards:,} Shards")
            
            if total_shards > current_shards:
                print(f"\n✗ Nicht genug Dominion Shards!")
                print(f"   Benötigt: {total_shards:,}")
                print(f"   Verfügbar: {current_shards:,}")
                print(f"   Fehlen: {total_shards - current_shards:,}")
                return False
            
            # Bestätigung
            if not confirm_action(f"\nUpgrade {dominion_name} von Level {current_level} auf {target_level} ({total_shards:,} Shards)?"):
                print("Abgebrochen")
                return False
            
            # Upgrade durchführen
            print(f"\n⏳ Upgrade startet...")
            
            current_id = dominion_card_id
            current_lvl = current_level
            
            for upgrade_step in range(upgrades_needed):
                # Upgrade um 1 Level
                result = self.api.call('upgradeCard', card_id=current_id)
                
                if not result or result.get('result') != True:
                    print(f"✗ Upgrade fehlgeschlagen bei Level {current_lvl}!")
                    print(f"Response: {result}")
                    return False
                
                # Nächste ID finden (upgraded version)
                next_lvl = current_lvl + 1
                
                for cid, cinfo in card_data.items():
                    if cinfo.get('base_id') == base_id and cinfo.get('level') == next_lvl:
                        current_id = cid
                        break
                
                current_lvl = next_lvl
                print(f"  ✓ Level {current_lvl} erreicht")
                
                # Kleine Pause
                time.sleep(0.3)
            
            print(f"\n✅ {dominion_name} wurde erfolgreich auf Level {target_level} upgraded!")
            print(f"   Verwendete Dominion Shards: {total_shards:,}")
            
            return True
            
        except Exception as e:
            print(f"✗ Fehler beim Upgrade: {e}")
            traceback.print_exc()
            return False
    
    def _calculate_fusion_path(self, current_id, target_id, card_data):
        """
        Berechnet den Fusion-Pfad von current_id zu target_id
        Verwendet Breadth-First-Search für mehrstufige Pfade
        
        Returns:
            Liste von Schritten: [{'type': 'upgrade'/'fusion', ...}, ...]
        """
        from collections import deque
        
        # Ziel base_id
        target_base = card_data.get(target_id, {}).get('base_id', target_id)
        
        # BFS Queue: (current_id, path_so_far)
        queue = deque([(current_id, [])])
        visited = set()
        
        while queue:
            curr_id, path = queue.popleft()
            
            if curr_id in visited:
                continue
            visited.add(curr_id)
            
            # Hole Info über current
            curr_info = card_data.get(curr_id, {})
            curr_level = curr_info.get('level', 1)
            curr_base = curr_info.get('base_id', curr_id)
            curr_name = curr_info.get('name', f'ID {curr_id}')
            
            # Check: Sind wir am Ziel?
            if curr_base == target_base:
                # Finaler Upgrade zum Ziel-Level
                target_level = card_data.get(target_id, {}).get('level', 6)
                if curr_level < target_level:
                    # Finde die richtige ID für das Ziel-Level
                    final_id = None
                    for cid, cinfo in card_data.items():
                        if cinfo.get('base_id') == curr_base and cinfo.get('level') == target_level:
                            final_id = cid
                            break
                    
                    if final_id:
                        cost = self._calculate_upgrade_cost(curr_id, final_id, card_data)
                        path.append({
                            'type': 'upgrade',
                            'from_id': curr_id,
                            'from_name': curr_name,
                            'from_level': curr_level,
                            'to_id': final_id,
                            'to_level': target_level,
                            'cost': cost
                        })
                
                return path if path else None
            
            # Option 1: Fusionen probieren (wenn möglich)
            if curr_id in DOMINION_FUSIONS:
                for fusion_id, fusion_name, fusion_cost in DOMINION_FUSIONS[curr_id]:
                    new_path = path + [{
                        'type': 'fusion',
                        'from_id': curr_id,
                        'from_name': curr_name,
                        'to_id': fusion_id,
                        'to_name': fusion_name,
                        'cost': fusion_cost
                    }]
                    queue.append((fusion_id, new_path))
            
            # Option 2: Upgrade auf Level 6 (falls nötig und noch nicht fusioniert)
            if curr_level < 6:
                lvl6_id = None
                for cid, cinfo in card_data.items():
                    if cinfo.get('base_id') == curr_base and cinfo.get('level') == 6:
                        lvl6_id = cid
                        break
                
                if lvl6_id:
                    cost = self._calculate_upgrade_cost(curr_id, lvl6_id, card_data)
                    new_path = path + [{
                        'type': 'upgrade',
                        'from_id': curr_id,
                        'from_name': curr_name,
                        'from_level': curr_level,
                        'to_id': lvl6_id,
                        'to_level': 6,
                        'cost': cost
                    }]
                    queue.append((lvl6_id, new_path))
        
        # Kein Pfad gefunden
        return None
    
    def _calculate_upgrade_cost(self, from_id, to_id, card_data):
        """
        Berechnet Dominion Shard-Kosten für Upgrade
        
        Args:
            from_id: Aktuelle Card-ID
            to_id: Ziel Card-ID
            card_data: Card-Daten Dictionary
            
        Returns:
            int: Gesamtkosten in Dominion Shards
        """
        from_level = card_data.get(from_id, {}).get('level', 1)
        to_level = card_data.get(to_id, {}).get('level', 6)
        tier = get_dominion_tier(from_id)
        
        total_cost = 0
        for lvl in range(from_level, to_level):
            next_lvl = lvl + 1
            if next_lvl in DOMINION_TIER_UPGRADE_COSTS[tier]:
                total_cost += DOMINION_TIER_UPGRADE_COSTS[tier][next_lvl]
        
        return total_cost
    
    def _execute_simple_upgrade(self, from_id, from_name, from_level, to_id, to_name, to_level, tier, card_data):
        """
        Führt einfaches Upgrade aus (gleiches Dominion, nur Level-Erhöhung)
        
        Args:
            from_id: Aktuelle Card-ID
            from_name: Aktueller Name
            from_level: Aktuelles Level
            to_id: Ziel Card-ID
            to_name: Ziel-Name
            to_level: Ziel-Level
            tier: Dominion Tier
            card_data: Card-Daten Dictionary
            
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        upgrades_needed = to_level - from_level
        
        if upgrades_needed <= 0:
            print(f"✓ Bereits am Ziel!")
            return True
        
        # Berechne Kosten
        total_shards = self._calculate_upgrade_cost(from_id, to_id, card_data)
        
        user_cards = self.init_data.get('user_cards', {})
        shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
        current_shards = int(shard_info.get('num_owned', 0))
        
        from_base = from_name.rsplit('-', 1)[0] if '-' in from_name else from_name
        to_base = to_name.rsplit('-', 1)[0] if '-' in to_name else to_name
        
        print(f"\n📊 Upgrade:")
        print(f"   Von: {from_base}-{from_level}")
        print(f"   Zu:  {to_base}-{to_level}")
        print(f"   Dominion Shards: {total_shards:,}")
        print(f"   Verfügbar: {current_shards:,}")
        
        if total_shards > current_shards:
            print(f"\n✗ Nicht genug Dominion Shards!")
            return False
        
        if not confirm_action(f"\nUpgrade von {from_name} auf {to_name} ({total_shards:,} Shards)?"):
            print("Abgebrochen")
            return False
        
        # Upgrade durchführen
        print(f"\n⏳ Upgrade läuft...")
        
        current_id = from_id
        current_lvl = from_level
        base_id = card_data.get(from_id, {}).get('base_id', from_id)
        
        for _ in range(upgrades_needed):
            result = self.api.call('upgradeCard', card_id=current_id)
            
            if not result or result.get('result') != True:
                print(f"✗ Upgrade fehlgeschlagen bei Level {current_lvl}!")
                return False
            
            next_lvl = current_lvl + 1
            
            for cid, cinfo in card_data.items():
                if cinfo.get('base_id') == base_id and cinfo.get('level') == next_lvl:
                    current_id = cid
                    break
            
            current_lvl = next_lvl
            print(f"  ✓ Level {current_lvl}")
            time.sleep(0.3)
        
        print(f"\n✅ Erfolgreich auf {to_name} upgraded!")
        return True
    
    def _execute_fusion_path(self, path, card_data):
        """
        Führt einen kompletten Fusion-Pfad aus (Upgrades + Fusionen)
        
        Args:
            path: Liste von Schritten [{'type': 'upgrade'/'fusion', ...}, ...]
            card_data: Card-Daten Dictionary
            
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        print(f"\n⏳ Auto-Build startet...")
        
        for i, step in enumerate(path, 1):
            print(f"\n--- Schritt {i}/{len(path)} ---")
            
            if step['type'] == 'upgrade':
                # Upgrade durchführen
                from_id = step['from_id']
                from_level = step['from_level']
                to_level = step['to_level']
                base_id = card_data.get(from_id, {}).get('base_id', from_id)
                
                current_id = from_id
                current_lvl = from_level
                
                for _ in range(to_level - from_level):
                    result = self.api.call('upgradeCard', card_id=current_id)
                    
                    if not result or result.get('result') != True:
                        print(f"✗ Upgrade fehlgeschlagen!")
                        return False
                    
                    next_lvl = current_lvl + 1
                    
                    for cid, cinfo in card_data.items():
                        if cinfo.get('base_id') == base_id and cinfo.get('level') == next_lvl:
                            current_id = cid
                            break
                    
                    current_lvl = next_lvl
                    time.sleep(0.3)
                
                print(f"✓ UPGRADE: {step['from_name']} → Level {to_level}")
            
            elif step['type'] == 'fusion':
                # Fusion durchführen
                # API: fuseCard mit card_id = Ziel-Dominion ID
                result = self.api.call('fuseCard', card_id=step['to_id'])
                
                if not result or result.get('result') != True:
                    print(f"✗ Fusion fehlgeschlagen!")
                    print(f"Response: {result}")
                    return False
                
                print(f"✓ FUSION: {step['from_name']} → {step['to_name']}")
                time.sleep(0.5)
        
        print(f"\n✅ Auto-Build erfolgreich abgeschlossen!")
        return True
    
    def build_dominion_autobuild(self, dominion_card_id=None, target_level=None):
        """
        Auto-Build: Baut automatisch ein Ziel-Dominion
        
        Features:
        - Zeigt aktuellen Status (Alpha + Nexus)
        - Zeigt alle verfügbaren Endstufen (Tier 4 Alpha, Tier 3 Nexus)
        - Berechnet automatisch Fusion-Pfad inkl. Upgrades
        - Führt Reset durch wenn kein direkter Pfad möglich
        - Kompletter Auto-Build in einem Durchlauf
        
        Args:
            dominion_card_id: Die Card-ID des Ziel-Dominions (optional, zeigt Auswahl-Dialog)
            target_level: Ziel-Level (optional, Standard: 6)
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER neu laden um aktuelle Daten zu haben (z.B. nach Reset)
            self.initialize()
            
            # Lade Card-Daten
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Konnte Card-Daten nicht laden")
                return False
            
            user_cards = self.init_data.get("user_cards", {})
            
            # Wenn keine ID angegeben, zeige verfügbare Dominions aus Inventar
            # Zeige immer Auswahl-Dialog
            if True:
                
                # Finde AKTUELLE Dominions im Inventar (pro Branch gibt es nur EINS!)
                current_dominions = []
                
                # Sammle ALLE Dominions im Inventar
                inventory_dominions = []
                for card_id, info in user_cards.items():
                    card_id_int = int(card_id)
                    if card_id_int in DOMINION_IDS:
                        num_owned = int(info.get("num_owned", 0))
                        if num_owned > 0:
                            card_info = self._get_card_info(card_data, card_id_int)
                            inventory_dominions.append({
                                "id": card_id_int,
                                "name": card_info["name"],
                                "tier": get_dominion_tier(card_id_int),
                                "branch": get_dominion_branch(card_id_int)
                            })
                
                # Pro Branch: Zeige nur das HÖCHSTE Tier (es kann nur eines geben!)
                dominions_by_branch = {}
                for dom in inventory_dominions:
                    branch = dom['branch']
                    if branch not in dominions_by_branch or dom['tier'] > dominions_by_branch[branch]['tier']:
                        dominions_by_branch[branch] = dom
                
                current_dominions = list(dominions_by_branch.values())
                
                # Zeige aktuellen Status
                if current_dominions:
                    print("\n" + "="*70)
                    print("AKTUELLER STATUS")
                    print("="*70)
                    for dom in current_dominions:
                        print(f"{dom['branch'].upper()}: {dom['name']} (Tier {dom['tier']})")
                    print("="*70)
                
                # Sammle HÖCHSTE Tier Endstufen als Ziel-Optionen
                # Alpha: Tier 4 | Nexus: Tier 3 (hat kein Tier 4)
                available_dominions = []
                
                for card_id in DOMINION_IDS:
                    tier = get_dominion_tier(card_id)
                    branch = get_dominion_branch(card_id)
                    
                    # Alpha: Tier 4, Level 6
                    if branch == 'alpha' and tier == 4:
                        card_info = self._get_card_info(card_data, card_id)
                        if card_info['level'] == 6:
                            available_dominions.append({
                                'id': card_id,
                                'name': card_info['name'],
                                'tier': tier,
                                'branch': branch
                            })
                    
                    # Nexus: Tier 3, Level 6 (Endstufe)
                    elif branch == 'nexus' and tier == 3:
                        card_info = self._get_card_info(card_data, card_id)
                        if card_info['level'] == 6:
                            available_dominions.append({
                                'id': card_id,
                                'name': card_info['name'],
                                'tier': tier,
                                'branch': branch
                            })
                
                if not available_dominions:
                    print("✗ Keine Endstufen-Dominions gefunden")
                    return False
                
                # Sortiere nach Branch (Alpha zuerst), dann nach Name
                available_dominions.sort(key=lambda x: (x['branch'], x['name']))
                
                print("\n" + "="*60)
                print("VERFÜGBARE ZIEL-DOMINIONS (Endstufen)")
                print("="*60)
                
                for idx, dom in enumerate(available_dominions, 1):
                    branch_label = dom['branch'].upper()
                    tier_label = f"Tier {dom['tier']}"
                    print(f"{idx}. [{branch_label} {tier_label}] {dom['name']}")
                
                print("="*50)
                
                # Auswahl mit Wiederholung bei ungültiger Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer oder ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Ungültige Auswahl: '{choice}'")
                            print(f"   Bitte wähle eine Nummer zwischen 1 und {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Gültige Auswahl - verlasse Loop
                        break
                    except ValueError:
                        print(f"✗ Ungültige Eingabe: '{choice}'")
                        print("   Bitte gib eine Nummer ein")
                        continue  # Wiederhole Eingabe
                
                # Das ist das ZIEL-Dominion, nicht das aktuelle!
                target_dominion = available_dominions[idx]
                target_card_id = target_dominion['id']
                target_branch = target_dominion['branch']
            
            # Hole ZIEL-Dominion Info
            target_info = card_data.get(target_card_id, {})
            target_name = target_info.get('name', f'ID {target_card_id}')
            target_level = target_info.get('level', 6)  # Sollte immer 6 sein
            
            # Prüfe ob es wirklich ein Dominion ist
            if target_card_id not in DOMINION_IDS:
                print(f"✗ {target_name} ist kein Dominion")
                return False
            
            # Finde AKTUELLES Dominion im selben Branch
            current_dominion = None
            for dom in current_dominions:
                if dom['branch'] == target_branch:
                    current_dominion = dom
                    break
            
            if not current_dominion:
                print(f"✗ Kein {target_branch.upper()} Dominion im Inventar gefunden!")
                print(f"   Du brauchst ein {target_branch.upper()} Dominion um {target_name} zu bauen.")
                return False
            
            current_card_id = current_dominion['id']
            current_info = card_data.get(current_card_id, {})
            current_name = current_info.get('name', f'ID {current_card_id}')
            current_level = current_info.get('level', 1)
            current_tier = current_dominion['tier']
            current_base_id = current_info.get('base_id', current_card_id)
            
            target_tier = target_dominion['tier']
            target_base_id = target_info.get('base_id', target_card_id)
            
            # Prüfe ob bereits am Ziel (gleiche base_id = gleiches Dominion)
            if current_base_id == target_base_id:
                # Gleiche base_id, nur Level-Unterschied möglich
                if current_level >= target_level:
                    print(f"✓ Du hast bereits {target_name}!")
                    return True
            
            # Wenn kein Ziel-Level angegeben, setze es auf 6 (Endstufe)
            if target_level is None:
                target_level = 6
            
            print("\n📋 AUTO-BUILD PLAN")
            print("="*70)
            
            print(f"\n📊 Status:")
            print(f"   Aktuell: {current_name} (Tier {current_tier})")
            print(f"   Ziel:    {target_name} (Tier {target_tier})")
            
            # Wenn gleicher Tier UND gleiches Dominion (base_id), nur upgraden
            if current_tier == target_tier and current_base_id == target_base_id:
                return self._execute_simple_upgrade(
                    current_card_id, current_name, current_level,
                    target_card_id, target_name, target_level,
                    current_tier, card_data
                )
            
            # Berechne Fusion-Pfad
            fusion_path = self._calculate_fusion_path(current_card_id, target_card_id, card_data)
            
            reset_performed = False  # Track ob Reset durchgeführt wurde
            
            if not fusion_path:
                # Kein direkter Pfad möglich
                print(f"\n⚠️  Kein direkter Pfad gefunden!")
                print(f"   Von {current_name} zu {target_name} ist nicht direkt möglich.")
                print(f"\n💡 Lösung: Reset auf Tier 1, dann zum Ziel bauen")
                
                # Bestätige Reset
                if not confirm_action(f"\n{current_name} zurücksetzen und dann {target_name} bauen?"):
                    print("Abgebrochen")
                    return False
                
                reset_performed = True
                
                # SCHRITT 1: Reset durchführen
                print(f"\n🔄 Schritt 1/2: Reset {current_name}...")
                reset_result = self.api.call('respecDominionCard', card_id=current_card_id)
                
                if not reset_result or reset_result.get('result') != True:
                    print(f"✗ Reset fehlgeschlagen!")
                    print(f"Response: {reset_result}")
                    return False
                
                print(f"✓ Reset erfolgreich!")
                time.sleep(0.5)
                
                # Reload Daten nach Reset
                self.initialize()
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde neues aktuelles Dominion (sollte Tier 1 sein)
                new_current = None
                for card_id, info in user_cards.items():
                    card_id_int = int(card_id)
                    if card_id_int in DOMINION_IDS:
                        num_owned = int(info.get("num_owned", 0))
                        if num_owned > 0:
                            branch = get_dominion_branch(card_id_int)
                            if branch == target_branch:
                                new_current = card_id_int
                                break
                
                if not new_current:
                    print(f"✗ Konnte Dominion nach Reset nicht finden!")
                    return False
                
                new_current_info = card_data.get(new_current, {})
                new_current_name = new_current_info.get('name', f'ID {new_current}')
                
                print(f"   Neuer Status: {new_current_name}")
                
                # SCHRITT 2: Berechne neuen Pfad
                print(f"\n🔨 Schritt 2/2: Baue {target_name}...")
                fusion_path = self._calculate_fusion_path(new_current, target_card_id, card_data)
                
                if not fusion_path:
                    print(f"\n❌ Auch nach Reset kein Pfad möglich!")
                    print(f"   Das sollte nicht passieren - bitte prüfen.")
                    return False
                
                # Update current für die weitere Verarbeitung
                current_card_id = new_current
                current_name = new_current_name
                current_level = new_current_info.get('level', 1)
                current_tier = get_dominion_tier(new_current)
            
            # Zeige Pfad
            print(f"\n📋 Fusion-Pfad ({len(fusion_path)} Schritte):")
            total_shards = 0
            
            for i, step in enumerate(fusion_path, 1):
                step_type = step['type']
                if step_type == 'upgrade':
                    print(f"   {i}. UPGRADE: {step['from_name']} L{step['from_level']} → L{step['to_level']}")
                    total_shards += step['cost']
                elif step_type == 'fusion':
                    print(f"   {i}. FUSION:  {step['from_name']} → {step['to_name']} ({step['cost']} Shards)")
                    total_shards += step['cost']
            
            # Hole aktuelle Dominion Shards
            user_cards = self.init_data.get('user_cards', {})
            shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
            current_shards = int(shard_info.get('num_owned', 0))
            
            print(f"\n💎 Dominion Shards:")
            print(f"   Benötigt:  {total_shards:,}")
            print(f"   Verfügbar: {current_shards:,}")
            
            if total_shards > current_shards:
                print(f"   ✗ Fehlen: {total_shards - current_shards:,}")
                return False
            else:
                print(f"   ✓ Ausreichend!")
            
            # Bestätigung - nur wenn KEIN Reset durchgeführt wurde
            if not reset_performed:
                if not confirm_action(f"\nAuto-Build von {current_name} zu {target_name} starten ({total_shards:,} Shards)?"):
                    print("Abgebrochen")
                    return False
            
            # Führe Pfad aus
            return self._execute_fusion_path(fusion_path, card_data)
            
        except Exception as e:
            print(f"✗ Fehler beim Upgrade: {e}")
            traceback.print_exc()
            return False
    
    def show_dominion_fusions(self, card_id=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Zeigt verfügbare Dominion Fusionen für eine Karte
        Wird für Debugging/Information verwendet
        
        Args:
            card_id: ID der Quell-Karte (optional)
        """
        try:
            if not self.init_data:
                self.initialize()
            
            user_cards = self.init_data.get('user_cards', {})
            
            # Wenn keine ID angegeben, zeige alle Dominions die fusioniert werden können
            if card_id is None:
                print("\n" + "="*60)
                print("VERFÜGBARE DOMINION FUSIONEN")
                print("="*60)
                
                fusion_options = []
                
                for source_id in DOMINION_FUSIONS.keys():
                    # Prüfe ob Karte im Inventar
                    card_count = int(user_cards.get(str(source_id), {}).get('num_owned', 0))
                    
                    if card_count > 0:
                        # Hole Karten-Info
                        card_data = self._load_card_data()
                        if not card_data:
                            continue
                        
                        card_info = card_data.get(source_id, {})
                        card_name = card_info.get('name', f'Card {source_id}')
                        card_level = card_info.get('level', '?')
                        
                        branch = get_dominion_branch(source_id)
                        tier = get_dominion_tier(source_id)
                        
                        fusion_options.append({
                            'id': source_id,
                            'name': card_name,
                            'level': card_level,
                            'count': card_count,
                            'branch': branch,
                            'tier': tier
                        })
                
                if not fusion_options:
                    print("✗ Keine Dominions mit Fusion-Option gefunden")
                    return
                
                # Sortiere nach Branch und Tier
                fusion_options.sort(key=lambda x: (x['branch'], x['tier'], x['id']))
                
                current_branch = None
                for opt in fusion_options:
                    if opt['branch'] != current_branch:
                        current_branch = opt['branch']
                        branch_name = 'ALPHA' if current_branch == 'alpha' else 'NEXUS'
                        print(f"\n━━━ {branch_name} BRANCH ━━━")
                    
                    # Fusion-Kosten bestimmen
                    fusion_cost = None
                    for result_id, result_name, shards in DOMINION_FUSIONS[opt['id']]:
                        fusion_cost = shards
                        break
                    
                    print(f"\n{opt['name']}-{opt['level']} (ID: {opt['id']}, {opt['count']}x)")
                    print(f"  Tier {opt['tier']} → FUSION zu Tier {opt['tier'] + 1 if opt['tier'] < 4 else opt['tier']} ({fusion_cost} Shards):")
                    
                    for result_id, result_name, shards in DOMINION_FUSIONS[opt['id']]:
                        # Prüfe ob genug Shards
                        shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                        status = "✓" if shard_count >= shards else "✗"
                        print(f"    {status} {result_name} ({shards} Shards)")
                
                # Zeige verfügbare Shards
                shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                print(f"\nVerfügbare Dominion Shards: {shard_count:,}")
                
                print("\n" + "="*60)
                print("WICHTIG:")
                print("- Tier-Übergänge verwenden FUSION (fuseCard)")
                print("- Innerhalb eines Tiers verwenden UPGRADE (upgradeCard)")
                print("="*60)
                return
            
            # Zeige Fusionen für spezifische Karte
            if card_id not in DOMINION_FUSIONS:
                print(f"✗ Keine Fusionen verfügbar für Card {card_id}")
                return
            
            # Lade Card-Daten
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Konnte Card-Daten nicht laden")
                return
            
            card_info = card_data.get(card_id, {})
            card_name = card_info.get('name', f'Card {card_id}')
            card_level = card_info.get('level', '?')
            
            # Prüfe Inventar
            card_count = int(user_cards.get(str(card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Entferne Level-Suffix aus Name falls vorhanden (Name enthält bereits "-X")
                display_name = card_name.rsplit('-', 1)[0] if '-' in card_name else card_name
                print(f"✗ {display_name}-{card_level} nicht im Inventar")
                return
            
            # Zeige verfügbare Fusionen
            print(f"\n{card_name}-{card_level} (ID: {card_id})")
            print(f"Verfügbar: {card_count}x")
            print("\nKann fusioniert werden zu:")
            
            for result_id, result_name, shards in DOMINION_FUSIONS[card_id]:
                # Prüfe ob genug Shards
                shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                
                status = "✓" if shard_count >= shards else "✗"
                print(f"  {status} {result_name} ({shards} Shards)")
            
            # Zeige verfügbare Shards
            shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
            print(f"\nVerfügbare Dominion Shards: {shard_count:,}")
            
        except Exception as e:
            print(f"✗ Fehler: {e}")
            traceback.print_exc()


# ==================== HELPER FUNKTIONEN ====================

def confirm_action(prompt):
    """
    Fragt Benutzer um Bestätigung mit Enter/ESC
    
    Args:
        prompt: Die anzuzeigende Frage
    
    Returns:
        True wenn Enter gedrückt (JA), False wenn ESC oder q (NEIN)
    """
    import sys
    
    print(f"{prompt}")
    print("  [Enter] = JA  |  [ESC/q] = NEIN")
    print("  ", end='', flush=True)
    
    # Windows-Unterstützung
    if os.name == 'nt':
        import msvcrt
        while True:
            key = msvcrt.getch()
            if key == b'\r':  # Enter
                print("✓ JA")
                return True
            elif key == b'\x1b' or key == b'q':  # ESC oder q
                print("✗ NEIN")
                return False
    else:
        # Unix/Linux/Mac
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == '\r' or ch == '\n':  # Enter
                    print("✓ JA")
                    return True
                elif ch == '\x1b' or ch == 'q':  # ESC oder q
                    print("✗ NEIN")
                    return False
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def show_settings_help():
    """
    Zeigt ausführliche Hilfe zum Settings-Dateiformat
    """
    print("\n" + "="*80)
    print("SETTINGS-DATEIFORMAT HILFE")
    print("="*80)
    
    print("\n📋 AKTUELLES FORMAT (EMPFOHLEN):")
    print("-"*80)
    print("""
{
    "request_data": {
        "user_id": "1234567",
        "password": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "syncode": "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6",
        "kong_id": "9876543",
        "kong_token": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5",
        "kong_name": "MusterSpieler",
        "unity": "Unity5_4_2",
        "client_version": "80",
        "device_type": "Firefox+85.0",
        "os_version": "Windows 10",
        "platform": "Web"
    },
    "url": "mobile.tyrantonline.com",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
}
""")
    
    print("\n📋 ALTES FORMAT (WIRD NOCH UNTERSTÜTZT):")
    print("-"*80)
    print("""
{
  "user_id": "1234567",
  "password": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "kong_id": "9876543",
  "kong_token": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5",
  "kong_name": "MusterSpieler"
}
""")
    
    print("\n📋 TEMPLATE-VORLAGE:")
    print("-"*80)
    print("""
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
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
}
""")
    
    print("\n🔧 KONVERTIERUNG VON POST-DATA:")
    print("-"*80)
    print("""
Wenn du POST-Data aus dem Browser kopierst, sieht es so aus:

password=xxx&client_time=xxx&syncode=xxx&kong_id=xxx&kong_token=xxx&kong_name=xxx...

So konvertierst du es in Settings:

1. Extrahiere diese Felder:
   - user_id
   - password
   - syncode
   - kong_id
   - kong_token
   - kong_name

2. Füge sie in die Template-Vorlage ein (oben)

3. Speichere als: settings_DEINNAME.json
""")
    
    print("\n💡 BEISPIEL-KONVERTIERUNG:")
    print("-"*80)
    print("""
POST-Data:
  password=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6&user_id=1234567&
  syncode=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6&
  kong_id=9876543&kong_token=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5&
  kong_name=MusterSpieler

Wird zu Settings:
  "user_id": "1234567",
  "password": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "syncode": "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6",
  "kong_id": "9876543",
  "kong_token": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5",
  "kong_name": "MusterSpieler"
""")
    
    print("\n📁 SPEICHERORT:")
    print("-"*80)
    print(f"""
Speichere deine Settings-Datei als:
  settings_DEINNAME.json

Im selben Verzeichnis wie dieses Script.

Beispiele:
  settings_MainAccount.json
  settings_AltAccount.json
  settings_MeinName.json
""")
    
    print("\n" + "="*80)
    input("\n[ENTER] zum Fortfahren...")


def input_with_esc(prompt, allow_empty=False):
    """
    Input-Funktion mit ESC-Support zum Abbrechen
    
    Args:
        prompt: Der anzuzeigende Prompt
        allow_empty: Wenn True, ist leere Eingabe erlaubt
    
    Returns:
        Eingabe-String oder None wenn ESC gedrückt wurde
    """
    print(f"{prompt}", end='', flush=True)
    
    # Windows-Unterstützung
    if os.name == 'nt':
        import msvcrt
        result = []
        while True:
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC
                print("\n✗ Abgebrochen")
                return None
            elif key == b'\r':  # Enter
                print()
                text = ''.join(result)
                if not text and not allow_empty:
                    print("✗ Leere Eingabe nicht erlaubt")
                    print(f"{prompt}", end='', flush=True)
                    result = []
                    continue
                return text
            elif key == b'\x08':  # Backspace
                if result:
                    result.pop()
                    print('\b \b', end='', flush=True)
            elif key >= b' ':  # Normale Zeichen
                char = key.decode('utf-8', errors='ignore')
                result.append(char)
                print(char, end='', flush=True)
    else:
        # Unix/Linux/Mac - verwende normale input() mit readline
        import readline
        try:
            result = input()
            if not result and not allow_empty:
                print("✗ Leere Eingabe nicht erlaubt")
                return input_with_esc(prompt, allow_empty)
            return result
        except KeyboardInterrupt:
            print("\n✗ Abgebrochen")
            return None


# ==================== SETTINGS GENERATOR ====================

def generate_settings_from_response():
    """
    Erstellt eine settings_name.json aus einer API-Response.
    Unterstützt sowohl JSON als auch URL-encoded Format.
    Extrahiert alle erforderlichen Felder für das neue Format.
    """
    print("="*80)
    print("SETTINGS GENERATOR")
    print("="*80)
    print("\nFüge API-Daten ein (JSON oder URL-encoded POST-Body)")
    print("z.B. aus Browser DevTools → Network → Request Payload\n")
    
    # Single-line Input
    full_text = input("Daten einfügen und Enter drücken: ").strip()
    
    if not full_text:
        print("✗ Keine Eingabe")
        return
    
    # Initialisiere alle Felder
    user_id = None
    password = None
    syncode = None
    kong_id = None
    kong_token = None
    kong_name = None
    unity = "Unity5_4_2"  # Default
    client_version = "80"  # Default
    device_type = None
    os_version = None
    platform = None
    
    # Versuche zuerst URL-encoded Format (typisch für API POST-Body)
    if '=' in full_text and '&' in full_text:
        print("\n⏳ Parse URL-encoded Format...")
        from urllib.parse import parse_qs, unquote
        
        # Entferne Zeilenumbrüche
        full_text = full_text.replace('\n', '').replace('\r', '')
        
        # Parse als Query-String
        params = parse_qs(full_text)
        
        # Extrahiere Werte (parse_qs gibt Listen zurück)
        user_id = params.get('user_id', [None])[0]
        password = params.get('password', [None])[0]
        syncode = params.get('syncode', [None])[0]
        kong_id = params.get('kong_id', [None])[0]
        kong_token = params.get('kong_token', [None])[0]
        kong_name = params.get('kong_name', [None])[0]
        unity = params.get('unity', [unity])[0]
        client_version = params.get('client_version', [client_version])[0]
        device_type = params.get('device_type', [None])[0]
        os_version = params.get('os_version', [None])[0]
        platform = params.get('platform', [None])[0]
        
        if kong_name:
            kong_name = unquote(kong_name)
        if device_type:
            device_type = unquote(device_type)
    
    # Falls URL-encoded nicht erfolgreich, versuche JSON
    if not all([user_id, password, kong_id, kong_token]):
        try:
            print("\n⏳ Parse JSON Format...")
            data = json.loads(full_text)
            
            # Extrahiere aus verschiedenen möglichen Strukturen
            if 'request' in data:
                request = data['request']
                user_id = request.get('user_id')
                password = request.get('password')
                syncode = request.get('syncode')
                kong_id = request.get('kong_id')
                kong_token = request.get('kong_token')
                kong_name = request.get('kong_name')
                unity = request.get('unity', unity)
                client_version = request.get('client_version', client_version)
                device_type = request.get('device_type')
                os_version = request.get('os_version')
                platform = request.get('platform')
            elif 'request_data' in data:
                request_data = data['request_data']
                user_id = request_data.get('user_id')
                password = request_data.get('password')
                syncode = request_data.get('syncode')
                kong_id = request_data.get('kong_id')
                kong_token = request_data.get('kong_token')
                kong_name = request_data.get('kong_name')
                unity = request_data.get('unity', unity)
                client_version = request_data.get('client_version', client_version)
                device_type = request_data.get('device_type')
                os_version = request_data.get('os_version')
                platform = request_data.get('platform')
            else:
                user_id = data.get('user_id')
                password = data.get('password')
                syncode = data.get('syncode')
                kong_id = data.get('kong_id')
                kong_token = data.get('kong_token')
                kong_name = data.get('kong_name')
                unity = data.get('unity', unity)
                client_version = data.get('client_version', client_version)
                device_type = data.get('device_type')
                os_version = data.get('os_version')
                platform = data.get('platform')
        except json.JSONDecodeError:
            pass
    
    # Validiere erforderliche Felder
    if not all([user_id, password, kong_id, kong_token]):
        print("\n✗ Fehlende erforderliche Felder!")
        print(f"   user_id:    {user_id or '❌ FEHLT'}")
        print(f"   password:   {password or '❌ FEHLT'}")
        print(f"   syncode:    {syncode or '⚠️  FEHLT (optional aber empfohlen)'}")
        print(f"   kong_id:    {kong_id or '❌ FEHLT'}")
        print(f"   kong_token: {kong_token or '❌ FEHLT'}")
        print(f"   kong_name:  {kong_name or '(optional)'}")
        print("\nTipp: Kopiere den kompletten POST-Body aus dem Browser DevTools:")
        print("      Network → Request → Payload (view source)")
        return
    
    # Frage nach Dateinamen
    default_name = kong_name.lower() if kong_name else "user"
    name_input = input(f"\nDateiname für settings_<n>.json (leer={default_name}): ").strip()
    name = name_input if name_input else default_name
    
    # Erstelle Settings-Dict im neuen Format
    settings = {
        "request_data": {
            "user_id": user_id,
            "password": password,
            "syncode": syncode or "",
            "kong_id": kong_id,
            "kong_token": kong_token,
            "kong_name": kong_name or "",
            "unity": unity,
            "client_version": client_version,
            "device_type": device_type or "Firefox+85.0",
            "os_version": os_version or "Windows 10",
            "platform": platform or "Web"
        },
        "url": "mobile.tyrantonline.com",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    
    # Speichere Datei
    filename = f"settings_{name}.json"
    filepath = os.path.join(SCRIPT_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"\n✓ Settings gespeichert: {filepath}\n")
    print(json.dumps(settings, indent=2))
    print(f"\n{'='*80}")






# ==================== INTERAKTIVES MENU ====================

def interactive_menu():
    """Interaktives Hauptmenü"""
    
    # Versuche Konsolenfenster-Größe zu setzen
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Setze Fenstergröße: Breite=120, Höhe=40
            kernel32.SetConsoleScreenBufferSize(kernel32.GetStdHandle(-11), 
                                                ctypes.wintypes._COORD(120, 9999))
            # Setze sichtbaren Bereich
            kernel32.SetConsoleWindowInfo(kernel32.GetStdHandle(-11), True,
                                         ctypes.byref(ctypes.wintypes.SMALL_RECT(0, 0, 119, 39)))
        else:  # Linux/Mac
            # Funktioniert nur in manchen Terminals
            print('\033[8;40;120t')  # 40 Zeilen, 120 Spalten
    except Exception:
        pass  # Ignoriere Fehler, wenn es nicht funktioniert
    
    print("="*50)
    print("TYRANT UNLEASHED API COMMANDER")
    print("Standalone Version (ohne tyrant-Modul)")
    print("="*50)
    
    # Prüfe ob im "data" Ordner
    current_dir = os.path.basename(SCRIPT_DIR)
    if current_dir.lower() != "data":
        print("\n" + "⚠"*50)
        print("WARNUNG: Script läuft nicht im 'data' Ordner!")
        print("⚠"*50)
        print(f"\nAktuelles Verzeichnis: {SCRIPT_DIR}")
        print(f"Ordnername: {current_dir}")
        print("\n" + "─"*50)
        print("EMPFEHLUNG: Starte das Script aus einem 'data' Ordner")
        print("─"*50)
        print("\nGründe:")
        print("  • Card-XMLs (cards_section_1.xml bis cards_section_21.xml)")
        print("    werden für folgende Funktionen benötigt:")
        print("    - Inventar exportieren (ownedcards.txt)")
        print("    - Base Epics salvagen")
        print("    - Karten-Namen anzeigen (statt nur IDs)")
        print("\n  • Falls XMLs fehlen, versucht das Script automatischen")
        print("    Download - das dauert länger und benötigt Internet!")
        print("\n  • Im 'data' Ordner werden auch Exports gespeichert:")
        print("    - ownedcards.txt")
        print("    - currentdecks.txt")
        print("    - guild_decks.txt")
        print("    - JSON exports")
        print("\n" + "─"*50)
        print("Optimale Ordnerstruktur:")
        print("─"*50)
        print("  MeinOrdner/")
        print("  └── data/")
        print("      ├── tyrant_api_commander_standalone.py  ← Das Script")
        print("      ├── settings_main.json                  ← Deine Settings")
        print("      ├── cards_section_1.xml                 ← Card-Daten")
        print("      ├── cards_section_2.xml")
        print("      ├── ... (bis cards_section_21.xml)")
        print("      └── (Outputs werden hier erstellt)")
        print("\n" + "─"*50)
        
        # Frage ob fortfahren
        if not confirm_action("\nTrotzdem fortfahren?"):
            print("\nAbbruch. Bitte starte das Script aus einem 'data' Ordner.")
            print("\nTipp: Erstelle einen 'data' Ordner und verschiebe")
            print("      das Script + settings_*.json + XMLs dorthin.")
            return
        
        print("\n" + "="*50)
        print("Fahre fort...")
        print("="*50)
    else:
        print(f"\n✓ Script läuft im 'data' Ordner: {SCRIPT_DIR}")
    
    # Konfiguration
    print(f"\nSkript-Verzeichnis: {SCRIPT_DIR}")
    
    # Suche nach settings_*.json Dateien
    import glob
    settings_files = glob.glob(os.path.join(SCRIPT_DIR, "settings_*.json"))
    
    # Filtere TEMPLATE aus
    settings_files = [f for f in settings_files if not os.path.basename(f).startswith("settings_TEMPLATE")]
    
    if not settings_files:
        print("\n✗ KEINE Settings-Dateien gefunden!")
        print(f"Bitte erstelle eine Datei wie 'settings_main.json' in: {SCRIPT_DIR}")
        print("\nTipp: Verwende settings_TEMPLATE.json als Vorlage")
        print("\nODER: Eingabe '999' = Settings Generator (aus API-Response)")
        return
    
    # Zeige verfügbare Settings als nummerierte Liste
    print("\nVerfügbare Settings-Dateien:")
    print("─"*50)
    
    settings_map = {}
    for idx, filepath in enumerate(sorted(settings_files), 1):
        basename = os.path.basename(filepath)
        name_part = basename.replace("settings_", "").replace(".json", "")
        settings_map[str(idx)] = filepath
        print(f"{idx}. {name_part} ({basename})")
    
    print("─"*50)
    print("998. Settings Generator (aus API-Response)")
    print("999. Settings-Hilfe (Dateiformat & Konvertierung)")
    print("─"*50)
    
    # Auswahl mit Wiederholung bei ungültiger Eingabe
    while True:
        choice = input(f"\nWähle Settings (1-{len(settings_files)}, 998 oder 999): ").strip()
        
        # Settings Generator
        if choice == "998":
            generate_settings_from_response()
            print("\n⏳ Starte Script neu um neue Settings zu verwenden...")
            import sys
            import time
            time.sleep(2)
            # Starte Script neu
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return
        
        # Settings-Hilfe
        if choice == "999":
            show_settings_help()
            # Nach Hilfe zurück zur Auswahl
            return interactive_menu()
        
        # Prüfe ob gültige Settings-Nummer
        if choice in settings_map:
            break  # Gültige Auswahl, verlasse Loop
        
        # Ungültige Eingabe
        print(f"✗ Ungültige Auswahl: '{choice}'")
        print(f"   Bitte wähle eine Nummer zwischen 1 und {len(settings_files)}, oder 998/999")
    
    # Wenn wir hier ankommen, ist choice gültig
    
    settings_path = settings_map[choice]
    settings_name = os.path.basename(settings_path).replace("settings_", "").replace(".json", "")
    
    print(f"✓ Lade Settings: {settings_name}")
    
    commander = TyrantCommander(settings_path)
    
    if not commander.initialize(verbose=True):  # Nur beim ersten Mal verbose
        print("Abbruch wegen Initialisierungsfehler")
        return
    
    # Auto-Check Daily Bonus (nur einmal beim Start)
    commander.auto_claim_daily_bonus()
    
    while True:
        print("\n" + "="*50)
        print("HAUPTMENÜ")
        print("="*50)
        print("1.  Spieler-Info")
        print("2.  XML-Dateien aktualisieren")
        print("3.  Deck aktualisieren (Slot bearbeiten + Attack/Defense setzen)")
        print("4.  Gildenmitglieder mit Rating")
        print("5.  Inventar exportieren (ownedcards.txt + currentdecks.txt)")
        print("6.  Gildennachricht senden")
        print("7.  Belohnungen abholen")
        print("8.  Gildendecks exportieren")
        print("="*50)
        print("── SHOP & SALVAGE ──")
        print("9.  Pakete kaufen")
        print("10. Alle Commons salvagen")
        print("11. Alle Rares salvagen")
        print("12. Base Epics salvagen (behalte X)")
        print("13. Workflow: Kaufen + Commons + Rares + Base Epics salvagen")
        print("="*50)
        print("── BUYBACK ──")
        print("16. Karte zurückkaufen")
        print("17. Mehrere Karten zurückkaufen (nach Seltenheit)")
        print("="*50)
        print("── INVENTAR ──")
        print("14. Karte bauen (Fusion-Rezept & SP-Kosten)")
        print("="*50)
        print("── DOMINION ──")
        print("15. Dominion bauen (Auto-Build) ⭐")
        print("="*50)
        print("0.  Beenden")
        print("="*50)
        
        choice = input("\nWähle eine Option: ").strip()
        
        if choice == "1":
            commander.get_player_info()
        
        elif choice == "2":
            commander.update_xmls()
        
        elif choice == "3":
            commander.update_deck()
        
        elif choice == "4":
            commander.list_guild_members_with_rating()
        
        elif choice == "5":
            commander.get_inventory()
        
        elif choice == "6":
            message = input("Nachricht eingeben: ").strip()
            commander.send_guild_message(message)
        
        elif choice == "7":
            commander.claim_rewards()
        
        elif choice == "8":
            filename = input_with_esc("Dateiname (leer='guild_decks', ESC=Abbruch): ")
            if filename is None:
                continue
            
            filename = filename.strip()
            if not filename:
                filename = 'guild_decks'
            # Stelle sicher dass .txt Endung vorhanden ist
            if not filename.endswith('.txt'):
                filename = filename + '.txt'
            # Verwende aktuelles Verzeichnis (SCRIPT_DIR)
            full_path = os.path.join(SCRIPT_DIR, filename)
            commander.export_guild_decks_simple(full_path)
        
        elif choice == "9":
            try:
                n_input = input_with_esc("Anzahl Pakete (ESC=Abbruch): ")
                if n_input is None:
                    continue
                n = int(n_input)
                commander.buy_packs(n)
            except ValueError:
                print("✗ Ungültige Zahl")

        elif choice == "10":
            commander.salvage_all_commons()

        elif choice == "11":
            commander.salvage_all_rares()

        elif choice == "12":
            # Base Epics salvagen (behalte X)
            try:
                keep_input = input_with_esc("Anzahl Base Epics die pro Karte behalten werden sollen (leer=20, ESC=Abbruch): ", allow_empty=True)
                if keep_input is None:
                    continue
                
                # Leere Eingabe = Standard 20
                if not keep_input or keep_input.strip() == "":
                    keep = 20
                    print(f"✓ Verwende Standard: {keep}")
                else:
                    keep = int(keep_input)
                
                commander.salvage_base_epics_keep_x(keep)
            except ValueError:
                print("✗ Ungültige Zahl")

        elif choice == "13":
            # Workflow: Kaufen + Commons + Rares + Base Epics salvagen
            try:
                # Berechne maximale Paketanzahl
                max_packs, free_slots = commander.calculate_max_packs()
                
                print(f"\nFreie Kartenslots: {free_slots}")
                print(f"Berechnete max. Pakete: {max_packs} ({free_slots} / 20 = {free_slots/20:.1f})")
                
                pack_input = input_with_esc(f"Anzahl Pakete (leer={max_packs}, ESC=Abbruch): ", allow_empty=True)
                if pack_input is None:
                    continue
                
                pack_input = pack_input.strip()
                
                # Leere Eingabe = automatisch berechnetes Maximum
                if not pack_input:
                    n = max_packs
                    print(f"✓ Verwende berechnetes Maximum: {n} Pakete")
                else:
                    n = int(pack_input)
                
                # Frage nach keep-Wert für Base Epics
                keep_input = input_with_esc("Anzahl Base Epics behalten pro Karte (leer=20, ESC=Abbruch): ", allow_empty=True)
                if keep_input is None:
                    continue
                
                keep_input = keep_input.strip()
                if not keep_input:
                    keep = 20
                    print(f"✓ Verwende Standard: {keep}")
                else:
                    keep = int(keep_input)
                
                if n <= 0:
                    print("✗ Anzahl muss größer als 0 sein")
                elif n > max_packs:
                    print(f"⚠ Warnung: {n} Pakete überschreitet berechnetes Maximum von {max_packs}")
                    print(f"   Das würde {n * 20} Slots benötigen, aber nur {free_slots} sind frei")
                    if confirm_action(f"Trotzdem {n} Pakete kaufen + Commons + Rares + Base Epics salvagen?"):
                        commander.shop_salvage_workflow(n, salvage_base_epics=True, keep_base_epics=keep)
                    else:
                        print("Abgebrochen")
                else:
                    if confirm_action(f"{n} Pakete kaufen + Commons + Rares + Base Epics (behalte {keep}) salvagen?"):
                        commander.shop_salvage_workflow(n, salvage_base_epics=True, keep_base_epics=keep)
                    else:
                        print("Abgebrochen")
            except ValueError:
                print("✗ Ungültige Zahl")

        elif choice == "14":
            commander.build_card()

        elif choice == "15":
            # Dominion Auto-Build
            commander.build_dominion_autobuild()

        elif choice == "16":
            # Einzelne Karte zurückkaufen
            try:
                card_input = input_with_esc("Kartenname oder ID (ESC=Abbruch): ")
                if card_input is None:
                    continue
                
                card_input = card_input.strip()
                if not card_input:
                    print("✗ Keine Eingabe")
                    continue
                
                # Prüfe ob Eingabe reine Zahl ist (ID) oder Name
                is_id = card_input.isdigit()
                
                # Hole Buyback-Info
                buyback_info = commander.get_buyback_info()
                
                if is_id:
                    # ID-Suche
                    card_id = int(card_input)
                    if str(card_id) not in buyback_info:
                        print(f"✗ Karte {card_id} ist nicht im Buyback-Store")
                        continue
                    info = buyback_info[str(card_id)]
                else:
                    # Name-Suche
                    card_id = commander._find_buyback_card_id_by_name(card_input)
                    if card_id is None:
                        continue
                    info = buyback_info[str(card_id)]
                
                # Zeige Info
                print(f"\n{info['name']} ({info['rarity_name']} Tier{info['tier']})")
                print(f"Verfügbar: {info['number']}x")
                print(f"Kosten: {info['cost_per_card']} SP/Karte")
                print(f"Gesamt: {info['total_cost']} SP für alle")
                
                qty_input = input_with_esc(f"Anzahl (leer={info['number']}, ESC=Abbruch): ", allow_empty=True)
                if qty_input is None:
                    continue
                
                qty_input = qty_input.strip()
                if not qty_input:
                    quantity = 0  # 0 = alle
                else:
                    quantity = int(qty_input)
                
                commander.buyback_card(card_id, quantity)
                    
            except ValueError:
                print("✗ Ungültige Eingabe")

        elif choice == "17":
            # Mehrere Karten zurückkaufen
            print("\nWähle Modus:")
            print("1. Nach Seltenheit filtern")
            print("2. Nach Namen (komma-separiert)")
            
            mode_choice = input_with_esc("Option (ESC=Abbruch): ")
            if mode_choice is None:
                continue
            
            if mode_choice == "1":
                # Nach Seltenheit
                print("\nWähle Seltenheit:")
                print("1. Common")
                print("2. Rare")
                print("3. Epic")
                print("4. Legendary")
                print("0. Alle Seltenheiten")
                
                rarity_choice = input_with_esc("Option (ESC=Abbruch): ")
                if rarity_choice is None:
                    continue
                
                rarity_map = {
                    "1": 1,
                    "2": 2,
                    "3": 3,
                    "4": 4,
                    "0": None
                }
                
                if rarity_choice not in rarity_map:
                    print("✗ Ungültige Option")
                    continue
                
                rarity_filter = rarity_map[rarity_choice]
                
                # Budget festlegen
                current_sp = commander.get_salvage()
                max_sp_input = input_with_esc(f"Maximales SP-Budget (leer={current_sp:,}, ESC=Abbruch): ", allow_empty=True)
                if max_sp_input is None:
                    continue
                
                max_sp_input = max_sp_input.strip()
                if not max_sp_input:
                    max_sp = None
                else:
                    try:
                        max_sp = int(max_sp_input)
                    except ValueError:
                        print("✗ Ungültige Zahl")
                        continue
                
                commander.buyback_multiple(rarity_filter=rarity_filter, max_sp=max_sp)
            
            elif mode_choice == "2":
                # Nach Namen
                names_input = input_with_esc("Kartennamen (komma-separiert, ESC=Abbruch): ")
                if names_input is None:
                    continue
                
                names_input = names_input.strip()
                if not names_input:
                    print("✗ Keine Namen eingegeben")
                    continue
                
                # Budget festlegen
                current_sp = commander.get_salvage()
                max_sp_input = input_with_esc(f"Maximales SP-Budget (leer={current_sp:,}, ESC=Abbruch): ", allow_empty=True)
                if max_sp_input is None:
                    continue
                
                max_sp_input = max_sp_input.strip()
                if not max_sp_input:
                    max_sp = None
                else:
                    try:
                        max_sp = int(max_sp_input)
                    except ValueError:
                        print("✗ Ungültige Zahl")
                        continue
                
                commander.buyback_by_names(names_input, max_sp=max_sp)
            else:
                print("✗ Ungültige Option")

        elif choice == "0":
            print("\nAuf Wiedersehen!")
            break

        else:
            print("✗ Ungültige Option")


# ==================== HAUPTPROGRAMM ====================

if __name__ == "__main__":
    interactive_menu()

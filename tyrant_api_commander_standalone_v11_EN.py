"""
Tyrant Unleashed API Commander - Standalone Version
Funktioniert OHNE tyrant-Modul (zeigt Cardn-IDs statt Namen)

Haupt-Features:
  • Dominion Auto-Build - Automatischer Fusion-Pfad mit Reset-Support
  • Shop-Funktionen - 2000-Gold Pakete buyingn
  • Salvage-Funktionen - L1 Commons/Rares auf einmal salvagen
  • Buyback-Funktionen - Cardn aus dem Buyback-Store zurückbuyingn ⭐ NEU
  • Card-Building - Fusion-Rezepte mit SP-Kosten
  
Usage:
  python tyrant_api_commander_standalone_v11_EN.py          # Normal mode
  python tyrant_api_commander_standalone_v11_EN.py --debug  # Debug mode
"""

# ==================== DEBUG MODE ====================
# Set to True to enable detailed startup debugging
# Cat so be enabled via --debug command line argaroundent
import sys
DEBUG_MODE = '--debug' in sys.argv or '-d' in sys.argv

if DEBUG_MODE:
    print("\n" + "="*70)
    print("DEBUG MODE - Script Startup Diagnostics")
    print("="*70)
    
    # 1. Python version check
    import sys
    print(f"\n1. Python Version Check:")
    print(f"   Version: {sys.version}")
    print(f"   Version Info: {sys.version_info}")
    
    if sys.version_info < (3, 6):
        print("   ⚠ WARNING: Python 3.6+ recommended")
    else:
        print("   ✓ Python version OK")
    
    # 2. Platform info
    import platform
    print(f"\n2. Platform Information:")
    print(f"   System: {platform.system()}")
    print(f"   Release: {platform.release()}")
    print(f"   Machine: {platform.machine()}")
    print(f"   Python Implementation: {platform.python_implementation()}")
    
    # 3. Test critical imports
    print(f"\n3. Testing Critical Imports:")
    
    critical_imports = [
        ('json', 'JSON handling'),
        ('xml.etree.ElementTree', 'XML parsing'),
        ('urllib.request', 'HTTP requests'),
        ('urllib.error', 'HTTP error handling'),
        ('urllib.parse', 'URL encoding'),
        ('datetime', 'Date/time handling'),
        ('time', 'Time functions'),
        ('os', 'OS operations'),
        ('hashlib', 'Hashing'),
        ('logging', 'Logging'),
        ('traceback', 'Error tracing'),
        ('gzip', 'Compression'),
        ('io', 'IO operations'),
    ]
    
    import_errors = []
    for module_name, description in critical_imports:
        try:
            __import__(module_name)
            print(f"   ✓ {module_name:<30} ({description})")
        except ImportError as e:
            print(f"   ✗ {module_name:<30} FAILED: {e}")
            import_errors.append((module_name, e))
    
    # 4. Test platform-specific imports
    print(f"\n4. Platform-Specific Imports:")
    if platform.system() != 'Windows':
        try:
            import termios
            import tty
            print(f"   ✓ termios (Unix terminal control)")
            print(f"   ✓ tty (Terminal functions)")
        except ImportError as e:
            print(f"   ⚠ termios/tty not available: {e}")
            print(f"   → This is expected on Windows")
    else:
        try:
            import msvcrt
            print(f"   ✓ msvcrt (Windows console)")
        except ImportError as e:
            print(f"   ⚠ msvcrt not available: {e}")
    
    # 5. File system check
    print(f"\n5. File System Check:")
    try:
        import os
        cwd = os.getcwd()
        print(f"   Current directory: {cwd}")
        print(f"   Directory readable: {os.access(cwd, os.R_OK)}")
        print(f"   Directory writable: {os.access(cwd, os.W_OK)}")
    except Exception as e:
        print(f"   ✗ Error checking file system: {e}")
    
    # 6. Encoding check
    print(f"\n6. Encoding Check:")
    try:
        print(f"   Default encoding: {sys.getdefaultencoding()}")
        print(f"   File system encoding: {sys.getfilesystemencoding()}")
        print(f"   stdout encoding: {sys.stdout.encoding}")
        
        # Test UTF-8 string
        test_str = "Test: äöüß ⭐ 🎯"
        print(f"   UTF-8 test: {test_str}")
        print(f"   ✓ UTF-8 support working")
    except Exception as e:
        print(f"   ⚠ Encoding issue: {e}")
    
    # 7. Saroundmary
    print(f"\n7. Summary:")
    if import_errors:
        print(f"   ✗ {len(import_errors)} import error(s) detected:")
        for module, error in import_errors:
            print(f"      - {module}: {error}")
        print(f"\n   ⚠ Script may not work correctly!")
    else:
        print(f"   ✓ All critical imports successful")
        print(f"   ✓ System appears compatible")
    
    print("="*70)
    print("DEBUG MODE - Continuing with normal startup...")
    print("="*70 + "\n")

# ==================== ACTUAL IMPORTS ====================
# Now import everything for real (after debug checks)

import json
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from datetime import datetime
from time import sleep
import os
import sys
import hashlib
import logging
import time
import traceback
import gzip
import io

# ==================== STDLIB REQUESTS REPLACEMENT ====================
# Statsincelone replacement for 'requests' using only Python stdlib

class RequestInfo:
    """Simple request info object"""
    def __init__(self, method, url, body=None, headers=None):
        self.method = method
        self.url = url
        self.body = body
        self.headers = headers or {}

class Response:
    """Response object compatible with requests.Response"""
    
    def __init__(self, status_code, content, headers, request_info=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers
        self.text = content.decode('utf-8', errors='replace')
        self.request = request_info
    
    def json(self):
        """Parse JSON response"""
        return json.loads(self.text)

class Session:
    """Session object compatible with requests.Session"""
    
    def __init__(self, *args, **kwargs):
        self.headers = {}
        self.cookies = {}
    
    def _make_request(self, method, url, data=None, headers=None, timeout=30):
        """Internal method to make HTTP request"""
        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)
        
        body_data = None
        if method == 'POST' and data:
            if isinstance(data, dict):
                body_data = urlencode(data).encode('utf-8')
            elif isinstance(data, str):
                body_data = data.encode('utf-8')
            else:
                body_data = data
        
        request_info = RequestInfo(method, url, body_data, req_headers)
        request = Request(url, data=body_data, headers=req_headers, method=method)
        
        try:
            response = urlopen(request, timeout=timeout)
            content = response.read()
            
            if response.headers.get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content)
            
            return Response(
                status_code=response.status,
                content=content,
                headers=dict(response.headers),
                request_info=request_info
            )
        
        except HTTPError as e:
            content = e.read()
            if e.headers.get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content)
            
            return Response(
                status_code=e.code,
                content=content,
                headers=dict(e.headers),
                request_info=request_info
            )
        
        except URLError as e:
            raise
    
    def get(self, url, **kwargs):
        """GET request"""
        return self._make_request('GET', url, **kwargs)
    
    def post(self, url, data=None, **kwargs):
        """POST request"""
        return self._make_request('POST', url, data=data, **kwargs)

# ==================== EMBEDDED TyrattAPI ====================
# The following classes replace the external TyrattAPI module

class TyrantAPISession(Session):
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
            error_msg = (
                f"\n{'='*70}\n"
                f"ERROR: Settings file not found!\n"
                f"{'='*70}\n"
                f"Expected location: {path}\n\n"
                f"Solution:\n"
                f"1. Copy 'settings_example.json' to 'settings.json'\n"
                f"2. Edit 'settings.json' and fill in your account details:\n"
                f"   - user_id: Your Tyrant user ID\n"
                f"   - password: Your password hash\n"
                f"   - kong_id: Your Kongregate ID\n"
                f"   - kong_token: Your Kongregate token\n"
                f"   - kong_name: Your Kongregate username\n\n"
                f"NOTE: The fixed values (unity, client_version, etc.) are already set correctly!\n"
                f"{'='*70}\n"
            )
            raise FileNotFoundError(error_msg)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {path}\nError: {e}")

        # Check required fields
        required_fields = ['request_data', 'url', 'user_agent']
        missing_fields = [field for field in required_fields if field not in self.settings]
        
        if missing_fields:
            raise ValueError(
                f"Fehlende Felder in Settings-Datei: {', '.join(missing_fields)}\n"
                f"Erforderlich: {', '.join(required_fields)}"
            )

        # Check request_data structure
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

# ==================== END EMBEDDED TyrattAPI ====================

# Directory where the script is located  →  there werden lokale XMLs gesucht
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== KONFIGURATION ====================

# Shop
PACK_ITEM_ID        = 48
PACK_ITEM_TYPE      = 3
PACK_COST           = 2000
DELAY_BETWEEN_BUYS  = 2          # Pfrome between purchases (Sekanden)

# Card-since: XML-Quellen
CARDS_BASE_URL      = "http://mobile.tyrantonline.com/assets/"
CARDS_SECTIONS      = 21         # cards_section_1.xml … cards_section_21.xml

# Upgrade materials (Neocyte Cores) - should NOT be used for building cards!
# Only use for Commander upgrades
UPGRADE_MATERIAL_IDS = {43451, 43452}
# 43451 = Neocyte Core (presumably)
# 43452 = Neocyte Fusion Core / Dominion Shard (presumably)

# Neocyte Cores - DO NOT use for building except for Commanders
NEOCYTE_CORE_IDS = UPGRADE_MATERIAL_IDS.copy()

# SP Maximum - Default fallback (actual cap is account-specific!)
# Use get_sp_cap() to get the actual limit for current account
SP_MAX_FALLBACK = 999999

# Commander cards (are ignored in card counting)
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

# Dominion cards (are ignored in card counting)
# Ratges: 50001-50236 and 50238-50359
DOMINION_IDS = set(range(50001, 50237)) | set(range(50238, 50360))

# Kombineverrte Ausschluss-list
EXCLUDED_CARD_IDS = UPGRADE_MATERIAL_IDS | COMMANDER_IDS | DOMINION_IDS

# ---------- Dominion System: Complete since ----------

# Dominion Shard ID
DOMINION_SHARD_ID = 43452

# Dominion Fusion Recipes - Aus fusion_recipes_cj2.xml
# Format: source_id -> [(result_id, result_name, shard_cost), ...]
DOMINION_FUSIONS = {
    # Alpha branch Tier 1: Alpha-2 -> Type
    50002: [
        (50003, 'Alpha Type-A', 50),
        (50081, 'Alpha Type-B', 50),
        (50159, 'Alpha Type-C', 50),
    ],
    # Alpha branch Tier 2: Type-6 -> Named Level 1
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
    # Alpha branch Tier 3: Named1-6 -> Named Level 2 (Final)
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
    # Nexus branch Tier 1: Nexus-2 -> Faction
    50239: [
        (50240, 'Imperial Nexus', 50),
        (50264, 'Raider Nexus', 50),
        (50288, 'Bloodthirsty Nexus', 50),
        (50312, 'Xeno Nexus', 50),
        (50336, 'Righteous Nexus', 50),
    ],
    # Nexus branch Tier 2: Faction-6 -> Named (Final)
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
        1: 50,  # L1->L2: 50 Shards via fuseCard (not upgradeCard!)
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
        # L6->Next (only Alpha): 170 Shards via fuseCard (Tier 3->4 Fusion)
    },
    4: {  # Tier 4: Alpha Final Named L1->L6 (via upgradeCard, only Alpha!)
        1: 180,  # L1->L2
        2: 190,  # L2->L3
        3: 200,  # L3->L4
        4: 210,  # L4->L5
        5: 220,  # L5->L6
        # ENDE - Nexus endet at Tier 3, Alpha endet at Tier 4
    }
}

# Fusion-Kosten between Tiers (fuseCard, NICHT upgradeCard!)
# Format: from_tier -> to_tier: shards
DOMINION_FUSION_COSTS = {
    (1, 2): 50,   # Tier 1->2: Base-2 -> Type/Faction (50 Shards)
    (2, 3): 110,  # Tier 2->3: Type/Faction-6 -> Named1 (110 Shards)
    (3, 4): 170,  # Tier 3->4: Named1-6 -> Named2 (170 Shards, only Alpha!)
}

# Dominion branch Detection
# Alpha branch: 50001-50237
# Nexus branch: 50238-50359
ALPHA_RANGE = range(50001, 50238)
NEXUS_RANGE = range(50238, 50360)

# Base IDs for bratches
# IMPORTANT: After reset you get direkt Level 2 (not Level 1!)
# Level 1 Versionen (50001, 50238) existieren not im Spiel
ALPHA_BASE_IDS = {50002}  # Alpha Dominion-2 (after reset)
NEXUS_BASE_IDS = {50239}  # Nexus Dominion-2 (after reset)

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
    
    # Alpha branch Tiers
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
    
    # Nexus branch Tiers
    elif card_id in NEXUS_RANGE:
        # Tier 2: Factions (50240-50245, 50264-50269, etc.)
        if (50240 <= card_id <= 50245) or (50264 <= card_id <= 50269) or \
           (50288 <= card_id <= 50293) or (50312 <= card_id <= 50317) or \
           (50336 <= card_id <= 50341):
            return 2
        # Tier 3: Named (Final for Nexus)
        else:
            return 3
    
    return None

def get_fusion_cost_between_tiers(from_tier, to_tier):
    """
    Gibt Fusion-Kosten zwischen zwei Tiers zurück
    
    Args:
        from_tier: Currenter Tier (1-3)
        to_tier: Ziel-Tier (2-4)
    
    Returns:
        int: Shard-Kosten oder None wenn ungültig
    """
    return DOMINION_FUSION_COSTS.get((from_tier, to_tier))

def is_fusion_available(card_id):
    """
    Prüft ob eine Card be fused kann
    
    Args:
        card_id: Card ID
    
    Returns:
        bool: True wenn Fusion möglich
    """
    return card_id in DOMINION_FUSIONS

# ---------- Fusion-Material-Gruppen (for ownedcards.txt) ----------
# Pattern: Wildcard at end, is checked with str.startswith() checked

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

# Rarity-Namen for reasinceble output
RARITY_NAMES = {
    1: "Common",
    2: "Rare", 
    3: "Epic",
    4: "Legendary",
    5: "Vindicator",
    6: "Mythic"
}

# Buyback-Kosten based on rarity and tier
# Format: (rarity, tier) -> SP-Kosten
# Commons (1) and Rares (2) gibt es NICHT im Buyback-Store
BUYBACK_COSTS = {
    # Epic (Rarity 3)
    (3, 0): 20,
    (3, 1): 80,
    (3, 2): 180,
    # Legensincery (Rarity 4)
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
        self._card_data_with_rarity_cache = None  # Cache for Buyback
    
    def initialize(self, verbose=False):
        """
        Lädt die Initialisierungsdaten
        
        Args:
            verbose: Wenn True, zeigt Verbindungsmeldungen (nur beim ersten Start)
        """
        try:
            if verbose:
                print("⏳ Connecting to API...")
            self.init_data = self.api.call('init')
            if verbose:
                print("✓ API connection successfully initialized")
                print("✓ Login data is correct")
            return True
        except ValueError as e:
            # Settings-file error
            print(f"✗ Error in Settings-File: {e}")
            return False
        except ConnectionError as e:
            print(f"✗ Verbindungsfehler: {e}")
            print("  → Check your internet connection")
            return False
        except RuntimeError as e:
            # API-error (e.g. 400, 403, etc.)
            error_msg = str(e)
            print(f"✗ API-Error: {error_msg}")
            
            if "403" in error_msg or "401" in error_msg:
                print("  → Login data is invalid or expired!")
                print("  → Create a new settings file with current data")
            elif "404" in error_msg:
                print("  → API-Endpunkt not found")
                print("  → Check the 'url' in the settings file")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                print("  → Server-Problem")
                print("  → Try again later")
            
            return False
        except Exception as e:
            print(f"✗ Unexpected error during initialization: {e}")
            print(f"  Error type: {type(e).__name__}")
            return False
    
    # ==================== SPIELER-INFORMATIONEN ====================
    
    def get_player_info(self):
        """Shows own Player information"""
        if not self.init_data:
            self.initialize()
        
        player = self.init_data['user_data']
        caps = player.get('caps', {})
        
        # card slots calculate (only user_cards, buyback_since not relevant)
        user_cards = self.init_data.get('user_cards', {})
        
        # so count cards in decks
        user_decks = self.init_data.get('user_decks', {})
        deck_cards = 0
        for deck in user_decks.values():
            cards_dict = deck.get('cards', {})
            for count in cards_dict.values():
                deck_cards += int(count)
        
        # Berechnung der cardsatzahl
        # IMPORTANT: Upgradematerialien, Commanders and Dominions werden ignoriert
        # IMPORTANT: Deck-cards sind already in user_cards entholden!
        import math
        
        # count cards (Deck-cards NICHT extra addieren - sind already in user_cards!)
        total_cards = sum(int(info.get('num_owned', 0))
                         for card_id, info in user_cards.items()
                         if int(card_id) not in EXCLUDED_CARD_IDS)
        
        max_cards = int(caps.get('max_cards', 0))
        
        # League Points (not XP!)
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
        print("CURRENCIES")
        print("─"*50)
        print(f"Gold:           {int(player.get('money', 0)):,}")
        print(f"WB:             {int(player.get('tokens', 0)):,}")
        print(f"SP:             {int(player.get('salvage', 0)):,} / {int(caps.get('max_salvage', 0)):,}")
        
        print("\n" + "─"*50)
        print("ENERGIE")
        print("─"*50)
        print(f"Arena Energy:   {int(player.get('stamina', 0))}")
        print(f"Stamina:        {int(player.get('energy', 0))}")
        
        # Zeige Event Energy (Brawl or Raid)
        active_brawl = self.init_data.get('active_brawl_data')
        player_brawl = self.init_data.get('player_brawl_data')
        current_raids = self.init_data.get('current_raids', {})
        raid_info = self.init_data.get('raid_info', {})
        
        event_shown = False
        
        # Zeige Brawl-informationen
        if active_brawl and player_brawl:
            event_name = active_brawl.get('name', 'Event')
            brawl_energy = player_brawl.get('energy', {})
            current_energy = int(brawl_energy.get('battle_energy', 0))
            max_energy = int(brawl_energy.get('max_battle_energy', 25))
            rank = player_brawl.get('current_rank', '?')
            points = int(player_brawl.get('points', 0))
            
            print(f"\n{event_name}:")
            print(f"  Energy:       {current_energy}/{max_energy}")
            print(f"  Rank:         #{ratk}")
            print(f"  Points:       {points:,}")
            event_shown = True
        
        # Zeige Raid-informationen
        if current_raids and raid_info:
            for raid_id, raid_data in raid_info.items():
                if raid_id in current_raids:
                    raid_name = current_raids[raid_id].get('name', 'Raid Event')
                    raid_level = raid_data.get('raid_level', '?')
                    current_health = int(raid_data.get('health', 0))
                    max_health = int(raid_data.get('max_health', 0))
                    
                    # Energy
                    energy_data = raid_data.get('energy', {})
                    current_energy = int(energy_data.get('battle_energy', 0))
                    max_energy = int(energy_data.get('max_battle_energy', 25))
                    
                    # Eigener Damage
                    user_id = str(player.get('user_id', ''))
                    members = raid_data.get('members', {})
                    own_damage = 0
                    if user_id in members:
                        own_damage = int(members[user_id].get('damage', 0))
                    
                    # Verbleibende Zeit until Level-Ende
                    import time
                    level_end_time = int(raid_data.get('raid_level_end', 0))
                    current_time = int(time.time())
                    time_remaining = max(0, level_end_time - current_time)
                    hours = time_remaining // 3600
                    minutes = (time_remaining % 3600) // 60
                    
                    # Status
                    status = raid_data.get('status', '0')
                    status_text = 'Aktiv' if status == '0' else 'Abgeschlossen'
                    
                    print(f"\n{raid_name}:")
                    print(f"  Energy:       {current_energy}/{max_energy}")
                    print(f"  Level:        {raid_level}")
                    print(f"  Boss HP:      {current_health:,}/{max_health:,}")
                    print(f"  Da Schaden: {own_damage:,}")
                    print(f"  Zeit:         {hours}h {minutes}m")
                    print(f"  Status:       {status_text}")
                    event_shown = True
        
        if not event_shown:
            # Fallback: zeige olde Battle Energy
            print(f"Battle Energy:  {int(player.get('battle_energy', 0))}")
        
        print("\n" + "─"*50)
        print("CARDS")
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
            print("None Guild")
        
        print("="*50 + "\n")
        
    def calculate_max_packs(self):
        """
        Berechnet maximale Anzahl an Paketen die purchased werden can
        basierend auf freien Cardnslots
        
        Logik:
        - Freie Slots berechnen
        - Durch 20 teilen (jedes Paket hat 20 Cardn)
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
        
        # count cards (without upgrade materials, Commanders, Dominions)
        total_cards = sum(int(info.get('num_owned', 0))
                         for card_id, info in user_cards.items()
                         if int(card_id) not in EXCLUDED_CARD_IDS)
        
        max_cards = int(caps.get('max_cards', 0))
        free_slots = max_cards - total_cards
        
        # Durch 20 teilen and abranden
        # e.g. 546 slots / 20 = 27.3 -> 27 Pakete
        max_packs = int(free_slots / 20)
        
        return max_packs, free_slots
    
    def get_profile(self, user_id):
        """
        Holt Profil eines anderen Players
        
        Args:
            user_id: User-ID des Players
        """
        try:
            profile = self.api.call('getProfileData', target_user_id=str(user_id))
            player_info = profile['player_info']
            
            print(f"\n=== PROFIL: {player_info['name']} ===")
            print(f"Level: {player_info['level']}")
            print(f"Guild: {player_info.get('faction_name', 'None')}")
            print(f"PvP Rating: {player_info.get('rating', 'N/A')}")
            
            return profile
        except Exception as e:
            print(f"✗ Error loading perfile: {e}")
            return None
    
    # ==================== GILDEN-MANAGEMENT ====================
    
    def update_xmls(self):
        """Downloads all XML files again"""
        print("\n" + "="*60)
        print("UPDATE XML FILES")
        print("="*60)
        
        base_url = "http://mobile.tyrantonline.com/assets/"
        
        # list all files
        files_to_download = [
            # Base XMLs
            ("fusion_recipes_cj2.xml", base_url + "fusion_recipes_cj2.xml"),
            ("skills_set.xml", base_url + "skills_set.xml"),
            ("missions.xml", base_url + "missions.xml"),
            ("levels.xml", base_url + "levels.xml"),
        ]
        
        # Card sections 1-21 (always present)
        for i in range(1, 22):
            filename = f"cards_section_{i}.xml"
            files_to_download.append((filename, base_url + filename))
        
        # Card section 22 (optional - might come)
        files_to_download.append(("cards_section_22.xml", base_url + "cards_section_22.xml"))
        
        # GitHub files
        files_to_download.extend([
            ("bges.txt", "https://raw.githubusercontent.com/APN-Pucky/tyrant_optimize/master/data/bges.txt"),
            ("raids.xml", "https://raw.githubusercontent.com/APN-Pucky/tyrant_optimize/master/data/raids.xml"),
        ])
        
        print(f"\nFiles to download: {len(files_to_download)}")
        print(f"Target directory: {SCRIPT_DIR}\n")
        
        # confirmation
        if not confirm_action("Download all XML files again?"):
            print("Canceled")
            return
        
        print("\n" + "─"*60)
        print("DOWNLOAD STARTING")
        print("─"*60)
        
        downloaded = 0
        skipped = 0
        failed = 0
        
        for filename, url in files_to_download:
            filepath = os.path.join(SCRIPT_DIR, filename)
            
            # Delete old file if present
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"⚠ Could not delete old file: {filename} ({e})")
            
            # Download
            print(f"⏳ {filename:<30} ", end='', flush=True)
            
            try:
                with urlopen(url, timeout=10) as response:
                    if response.status == 200:
                        content = response.read()
                        
                        # Save
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        size_kb = len(content) / 1024
                        print(f"✓ ({size_kb:.1f} KB)")
                        downloaded += 1
                    else:
                        print(f"✗ HTTP {response.status}")
                        failed += 1
                        
            except URLError as e:
                # 404 ist OK for cards_section_22.xml
                if "404" in str(e) and filename == "cards_section_22.xml":
                    print(f"⊘ Not yet available (404)")
                    skipped += 1
                else:
                    print(f"✗ Error: {e}")
                    failed += 1
            except Exception as e:
                print(f"✗ Error: {e}")
                failed += 1
            
            # Rate limiting (not too fast)
            sleep(0.2)
        
        # Summary
        print("\n" + "─"*60)
        print("DOWNLOAD COMPLETED")
        print("─"*60)
        print(f"✓ Successful:  {downloaded}")
        print(f"⊘ Skipped: {skipped} (cards_section_22.xml)")
        print(f"✗ Failed: {failed}")
        print(f"\nFiles saved in: {SCRIPT_DIR}")
        print("="*60 + "\n")
    
    
    def list_guild_members_with_rating(self):
        """
        Lists all guild members with Player ID, Name and Rating
        At the end the sum of all ratings is displayed
        """
        if not self.init_data:
            self.initialize()
        
        if 'faction' not in self.init_data:
            print("✗ Not in a guild")
            return []
        
        faction_name = self.init_data['faction']['name']
        members = self.init_data['faction']['members']
        
        print("\n" + "="*60)
        print(f"GUILD MEMBERS: {faction_name}")
        print("="*60)
        print(f"Total members: {len(members)}")
        print("\n⏳ Loading member data...\n")
        
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
                
                # Output: Nr. Name (ID) - Level - Rating
                # With tabs for nice alignment
                print(f"{i:2}. {name} ({member_id})\t\t\tLvl {level:3}\t\tRating: {rating:,}")
                
                member_list.append(member_data)
                total_rating += rating
                
                # Rate limiting
                sleep(0.3)
                
            except Exception as e:
                print(f"{i:2}. ID {member_id} - ✗ Error: {e}")
        
        # Summary
        print("\n" + "─"*60)
        print("SUMMARY")
        print("─"*60)
        print(f"Loaded members:  {len(member_list)} / {len(members)}")
        print(f"Total Rating:    {total_rating:,}")
        if len(member_list) > 0:
            avg_rating = total_rating / len(member_list)
            print(f"Average Rating:  {avg_rating:,.1f}")
        print("="*60)
        
        return member_list
    
    def send_guild_message(self, message_text):
        """
        Sends a message to the guild (sendFactionMessage)
        
        Args:
            message_text: Nachrichtentext
        """
        try:
            if not message_text or not message_text.strip():
                print("✗ None Message eingegeben")
                return None
            
            print("\n" + "="*60)
            print("GILDENNACHRICHT SENDEN")
            print("="*60)
            print(f"\nNachricht: \"{message_text}\"")
            
            print("\n⏳ Sende Message...")
            # Parameter: chat = messageentext
            # optional: last_activity_id (if present in init_since)
            kwargs = {'chat': message_text}
            
            # Add last_activity_id into if present
            if self.init_data and 'last_activity_id' in self.init_data:
                kwargs['last_activity_id'] = str(self.init_data['last_activity_id'])
            
            result = self.api.call('sendFactionMessage', **kwargs)
            
            if result and result.get('result') == True:
                print("✓ Guild message sent successfully!")
            else:
                print("✗ Error sending message")
                if result:
                    print(f"   API Response: {result}")
            
            print("="*60)
            return result
            
        except Exception as e:
            print(f"✗ Error sending message: {e}")
            traceback.print_exc()
            return None
    
    # ==================== DECK-MANAGEMENT ====================
    
    def get_decks(self, user_id=None):
        """
        Shows own Decks im currentdecks.txt Format in der Shell
        Identisch zu Punkt 6 Export, aber ohne Datei zu createn
        """
        try:
            if not self.init_data:
                self.initialize()
            
            print("\n" + "="*60)
            print("EIGENE DECKS")
            print("="*60)
            
            # Card-since load
            print("⏳ Loading card data...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Cannot continue without card data.")
                return None
            
            user_decks = self.init_data.get('user_decks', {})
            # IMPORTANT: Verwende 'active_deck' and 'defense_deck' (without _id)!
            active_deck = str(self.init_data.get('user_data', {}).get('active_deck', ''))
            defense_deck = str(self.init_data.get('user_data', {}).get('defense_deck', ''))
            
            print(f"✓ {len(card_data)} cards loaded")
            print("\n" + "─"*60)
            
            deck_count = 0
            for deck_id, deck in user_decks.items():
                # Deck-Name (gleich wie in currentdecks.txt)
                deck_name = deck.get('name') or f"Deck{deck_id}"
                
                # Markierungen [A] for Active, [D] for Defense
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
                
                # Cards with count
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    cname = self._resolve_card(cid, card_data)
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)
                
                # Zeile tosammenbauen: Name[Mark]:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)
                
                line = f"{deck_name}{mark_str}:{','.join(parts)}"
                
                # Ausgabe
                print(line)
                deck_count += 1
            
            print("─"*60)
            print(f"Total: {deck_count} Decks")
            print("="*60)
            
            return user_decks
            
        except Exception as e:
            print(f"✗ Error loading decks: {e}")
            traceback.print_exc()
            return None
    
    def update_deck(self):
        """
        Updates a deck in einem bestimmten Slot
        Accepts card names (e.g. "Barracus-6") statt IDs
        """
        try:
            if not self.init_data:
                self.initialize()
            
            print("\n" + "="*60)
            print("DECK AKTUALISIEREN")
            print("="*60)
            
            # Lade Card-since for Name->ID Mapping
            print("\n⏳ Loading card data...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Cannot continue without card data.")
                print("   Please make sure that cards_section_*.xml available are")
                print("   or use option 2 (Update XML Files)")
                return
            
            # Erstelle Reverse-Mapping: Name -> ID
            # Inklusive Basenames without Level (e.g. "Daemon" -> highest level "Daemon-6")
            # Case-insensitive (case-insensitive)
            name_to_id = {}
            name_to_id_lower = {}  # Lowercase-Version for case-insensitive Suche
            base_name_to_max = {}  # Speichert for eachn Basenames its highest Level
            
            for card_id, card_info in card_data.items():
                # Handle dict format (from XML since)
                if isinstance(card_info, dict):
                    name = card_info.get('name', f"ID_{card_id}")
                # Handle string format (legacy)
                elif isinstance(card_info, str):
                    name = card_info
                else:
                    continue  # Skip invalid entries
                
                # Complete name (e.g. "Daemon-6")
                name_to_id[name] = card_id
                name_to_id_lower[name.lower()] = card_id
                
                # Extract Basename and Level
                if '-' in name:
                    base_name, level_str = name.rsplit('-', 1)
                    try:
                        level = int(level_str)
                        
                        # Speichere highest level for eachn Basenames
                        if base_name not in base_name_to_max or level > base_name_to_max[base_name][1]:
                            base_name_to_max[base_name] = (card_id, level)
                    except ValueError:
                        pass  # No narounderisches Level
            
            # Add basenames into (show at highest level)
            for base_name, (card_id, level) in base_name_to_max.items():
                if base_name not in name_to_id:  # Nur if not already existiert
                    name_to_id[base_name] = card_id
                    name_to_id_lower[base_name.lower()] = card_id
            
            print(f"✓ {len(card_data)} cards loaded ({len(base_name_to_max)} Basenames)")
            
            # Zeige availablee Slots with kompletten Decks
            user_decks = self.init_data.get('user_decks', {})
            active_deck = str(self.init_data.get('user_data', {}).get('active_deck', ''))
            defense_deck = str(self.init_data.get('user_data', {}).get('defense_deck', ''))
            
            print(f"\nAvailable deck slots: {len(user_decks)}")
            print("─"*60)
            
            for deck_id in sorted(user_decks.keys(), key=lambda x: int(x)):
                deck = user_decks[deck_id]
                deck_name = deck.get('name') or f"Deck{deck_id}"
                
                # Markierungen [A] for Active, [D] for Defense
                marks = []
                if str(deck_id) == active_deck:
                    marks.append("A")
                if str(deck_id) == defense_deck:
                    marks.append("D")
                mark_str = f" [{'/'.join(marks)}]" if marks else ""
                
                # Commander
                commander_id = deck.get('commander_id', '0')
                commander_info = card_data.get(int(commander_id), str(commander_id)) if commander_id and commander_id != '0' else '?'
                # Handle both dict and string
                if isinstance(commander_info, dict):
                    commander = commander_info.get('name', str(commander_id))
                else:
                    commander = str(commander_info)
                # Remove "-6" if present
                if commander.endswith('-6'):
                    commander = commander[:-2]
                
                # Dominion (optional)
                dominion_id = deck.get('dominion_id')
                if dominion_id:
                    dominion_info = card_data.get(int(dominion_id), str(dominion_id))
                    # Handle both dict and string
                    if isinstance(dominion_info, dict):
                        dominion = dominion_info.get('name', str(dominion_id))
                    else:
                        dominion = str(dominion_info)
                    # Remove "-6" if present
                    if dominion.endswith('-6'):
                        dominion = dominion[:-2]
                else:
                    dominion = ""
                
                # Cards with count
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    card_info = card_data.get(int(cid), str(cid))
                    # Handle both dict and string
                    if isinstance(card_info, dict):
                        cname = card_info.get('name', str(cid))
                    else:
                        cname = str(card_info)
                    # Remove "-6" if present
                    if cname.endswith('-6'):
                        cname = cname[:-2]
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)
                
                # Zeile tosammenbauen: Name[Mark]:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)
                
                line = f"{deck_name}{mark_str}:{', '.join(parts)}"
                print(line)
            
            print("─"*60)
            
            # Slot-selection with ESC-Support
            slot_input = input_with_esc("\nWhich slot to edit? (1-6, ESC=Cancel): ")
            if slot_input is None:
                return
            
            slot_input = slot_input.strip()
            if not slot_input.isdigit():
                print("✗ Invalid input")
                return
            
            deck_id = slot_input
            
            # Validiere Slot-Naroundmer
            if int(deck_id) < 1 or int(deck_id) > 6:
                print("✗ Slot must be between 1 and 6")
                return
            
            print(f"\n✓ Editing slot {deck_id}")
            
            # Frage was gemacht werden soll
            print("\n" + "─"*60)
            print("WHAT DO YOU WANT TO DO?")
            print("─"*60)
            print("1. Edit deck (Commander, Dominion, cards change)")
            print("2. Only set as attack deck")
            print("3. Only set as defense deck")
            
            action = input_with_esc("\nSelection (1-3, ESC=Cancel): ")
            if action is None:
                return
            
            action = action.strip()
            
            if action == '2':
                # Nur als Attack Deck set
                print(f"\n⏳ Setting slot {deck_id} as attack deck...")
                result = self.api.call('setActiveDeck', deck_id=deck_id)
                if result and result.get('result') == True:
                    print(f"✓ Slot {deck_id} is now the attack deck!")
                    # Init-since new load
                    print("\n⏳ Updating Data...")
                    self.initialize()
                    print("✓ Data updated")
                else:
                    print(f"✗ Error setting as attack deck")
                print("="*60)
                return
            
            elif action == '3':
                # Nur als Defense Deck set
                print(f"\n⏳ Setting slot {deck_id} as defense deck...")
                result = self.api.call('setDefenseDeck', deck_id=deck_id)
                if result and result.get('result') == True:
                    print(f"✓ Slot {deck_id} is now the defense deck!")
                    # Init-since new load
                    print("\n⏳ Updating Data...")
                    self.initialize()
                    print("✓ Data updated")
                else:
                    print(f"✗ Error setting as defense deck")
                print("="*60)
                return
            
            elif action != '1':
                print("✗ Invalid selection")
                return
            
            # If action == '1', weiter with Deck-Bearattung
            print("\n" + "─"*60)
            print("DECK-EINGABE FORMAT")
            print("─"*60)
            print("Commander-Name, Dominion-Name, card1-Name, card2-Name, ...")
            print("\nBeispiel: Barracus-6, Imperial Fortress-5, Windreaver-5, Aegis-5")
            print("Or:     Barracus, Imperial Fortress, Windreaver, Aegis")
            print("Or:     barracus, imperial fortress, windreaver, aegis")
            print("\nMultiple cards (both spellings allowed):")
            print("  Daemon, Daemon, Daemon")
            print("  Daemon #3")
            print("  Kulkan Neurotox, Kulkan Neurotox")
            print("  Kulkan Neurotox #2")
            print("\n  • Exactly 1 Commander (required)")
            print("  • Dominion (required, '0' for no Dominion)")
            print("  • 1-10 cards")
            print("\nNote:")
            print("  • Name without level (e.g. 'Daemon') = highest level (Daemon-6)")
            print("  • Name with Level (e.g. 'Daemon-5') = exactly this level")
            print("  • Case-insensitive")
            print("  • #count Syntax: 'card #3' = 3x diese card")
            print("─"*60)
            
            # Deck-Eingabe with ESC-Support
            deck_input = input_with_esc("\nEnter deck (ESC=Cancel): ")
            if deck_input is None:
                return
            
            deck_input = deck_input.strip()
            if not deck_input:
                print("✗ Empty input")
                return
            
            # Parse Eingabe
            try:
                parts = [p.strip() for p in deck_input.split(',')]
                if len(parts) < 3:
                    print("✗ Too few entries (at least Commander, Dominion, 1 card)")
                    return
                
                commander_entry = parts[0]
                dominion_entry = parts[1]
                card_entries = parts[2:]
                
                # Expandiere #count Syntax
                # "Daemon #3" -> ["Daemon", "Daemon", "Daemon"]
                expanded_card_entries = []
                for entry in card_entries:
                    entry = entry.strip()
                    # Check if #count present
                    if ' #' in entry:
                        card_part, count_part = entry.rsplit(' #', 1)
                        try:
                            count = int(count_part)
                            # Add card count times into
                            for _ in range(count):
                                expanded_card_entries.append(card_part.strip())
                        except ValueError:
                            # No valid count, treat as normal name
                            expanded_card_entries.append(entry)
                    else:
                        expanded_card_entries.append(entry)
                
                card_names = expanded_card_entries
                
                if len(card_names) < 1:
                    print("✗ At least 1 card required")
                    return
                
                if len(card_names) > 10:
                    print("✗ Maximum 10 cards allowed")
                    return
                
                # Konvertiere Namen to IDs
                print("\n⏳ Translate card names to IDs...")
                
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
                    print(f"✗ Commander not found: '{commander_name}'")
                    print(f"   Tip: Pay attention to correct spelling (e.g. 'Barracus' or 'barracus')")
                    return
                
                # Dominion
                if dominion_name == '0':
                    dominion_id = '0'
                    print(f"✓ Dominion: No Dominion (0)")
                elif dominion_name in name_to_id:
                    dominion_id = str(name_to_id[dominion_name])
                    print(f"✓ Dominion: {dominion_name} → ID {dominion_id}")
                elif dominion_name.lower() in name_to_id_lower:
                    dominion_id = str(name_to_id_lower[dominion_name.lower()])
                    print(f"✓ Dominion: {dominion_name} → ID {dominion_id}")
                else:
                    print(f"✗ Dominion not found: '{dominion_name}'")
                    print(f"   Tip: Pay attention to correct spelling")
                    return
                
                # cards
                card_ids = []
                for card_name in card_names:
                    if card_name in name_to_id:
                        card_id = str(name_to_id[card_name])
                        card_ids.append(card_id)
                        print(f"✓ Card: {card_name} → ID {card_id}")
                    elif card_name.lower() in name_to_id_lower:
                        card_id = str(name_to_id_lower[card_name.lower()])
                        card_ids.append(card_id)
                        print(f"✓ Card: {card_name} → ID {card_id}")
                    else:
                        print(f"✗ Card not found: '{card_name}'")
                        print(f"   Tip: Pay attention to correct spelling")
                        return
                
                print(f"\n✓ All cards successfully translated!")
                print(f"   Commander: {commander_name}")
                print(f"   Dominion: {dominion_name}")
                print(f"   Cards ({len(card_ids)}):")
                
                # Zeige cards with Count
                from collections import Counter
                card_name_counts = Counter(card_names)
                for card_name, count in card_name_counts.items():
                    if count > 1:
                        print(f"     • {card_name} x{count}")
                    else:
                        print(f"     • {card_name}")
                
                # VALIDATION: Check ob cards in inventory present sind
                # First reload inventory to include freshly built cards
                print(f"\n⏳ Reloading inventory (to include freshly built cards)...")
                self.initialize()
                print(f"✓ Inventory updated")
                
                print(f"\n⏳ Check inventory availability...")
                user_cards = self.init_data.get('user_cards', {})
                
                # Collect all required cards with count
                needed_cards = Counter(card_ids)
                # Add Commander and Dominion into
                needed_cards[commander_id] += 1
                if dominion_id != '0':
                    needed_cards[dominion_id] += 1
                
                # Check each required card
                missing_cards = []
                for card_id, needed_count in needed_cards.items():
                    if str(card_id) in user_cards:  # user_cards has string keys
                        owned_count = int(user_cards[str(card_id)].get('num_owned', 0))
                        if owned_count < needed_count:
                            card_name = card_data.get(int(card_id), f"ID {card_id}")
                            missing_cards.append(f"{card_name}: needed {needed_count}, have {owned_count}")
                    else:
                        card_name = card_data.get(int(card_id), f"ID {card_id}")
                        missing_cards.append(f"{card_name}: NOT in inventory")
                
                if missing_cards:
                    print(f"\n✗ ERROR: Following cards missing in inventory:")
                    for msg in missing_cards:
                        print(f"   • {msg}")
                    print(f"\n⚠ Deck cannot be saved!")
                    return
                
                print(f"✓ All cards available in inventory!")
                
            except Exception as e:
                print(f"✗ Error parsing: {e}")
                traceback.print_exc()
                return
            
            # API call: setDeckCards (without confirmation)
            print(f"\n⏳ Saving deck in Slot {deck_id}...")
            
            # Cards als JSON-Object: {"card_id": "count"}
            # Count how often each card appears
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
                                  activeYN='0')  # Nicht automatisch als Attack set
            
            if result and result.get('result') == True:
                print(f"✓ Deck in Slot {deck_id} saved!")
                
                # Init-since new load
                print("\n⏳ Updating Data...")
                self.initialize()
                print("✓ Data updated")
                
            else:
                print(f"✗ Error saving deck")
                if result:
                    print(f"   API Response: {result}")
            
            print("="*60)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            traceback.print_exc()
    
    def get_foreign_deck(self, user_id):
        """
        Zeigt Attack- und Defense-Deck eines fremden Players
        
        Args:
            user_id: User-ID des Players
        """
        try:
            print("\n" + "="*60)
            print(f"FOREIGN DECKS: User ID {user_id}")
            print("="*60)
            
            # player-Profil load
            print("⏳ Loading player perfile...")
            profile = self.api.call('getProfileData', target_user_id=str(user_id))
            player_info = profile['player_info']
            player_name = player_info['name']
            
            print(f"✓ Player: {player_name} (Lvl {player_info['level']})")
            
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
            print(f"✗ Error loading decks: {e}")
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
        Setzt a Deck
        
        Args:
            deck_type: 'attack' oder 'defense'
            commander_id: ID des Commanders
            card_ids: Liste von Cardn-IDs
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
            
            print(f"✓ {deck_type.capitalize()}-Deck successful gesetzt")
            return result
            
        except Exception as e:
            print(f"✗ Error setting deck: {e}")
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
            
            print(f"✓ Mission {mission_id} fought")
            print(f"Ergebnis: {result.get('result', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"✗ Error while fighting: {e}")
            return None
    
    # ==================== ARENA & PVP ====================
    
    
    def attack_player(self, target_user_id, deck_hash=None):
        """
        Greift einen Player in der Arena an
        
        Args:
            target_user_id: User-ID des Ziels
            deck_hash: Optional - Hash des zu verwendenden Decks
        """
        try:
            result = self.api.call('attackPlayer',
                                  target_user_id=str(target_user_id),
                                  deck_hash=deck_hash)
            
            print(f"✓ Attack on user {target_user_id}")
            print(f"Ergebnis: {result.get('result', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"✗ Error during attack: {e}")
            return None
    
    # ==================== CARDN-MANAGEMENT ====================
    
    # ---------- Card-Data from tyrattonline load ----------

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

        Basis-Card wird als Level 1 gespeichert.
        Ergebnis wird in _card_data_cache gepusht (nur einmal geload).

        Returns:
            dict: { int(card_id): "Name-Level" }
        """
        if self._card_data_cache:
            return self._card_data_cache

        print("⏳ Loading card data", end='', flush=True)

        card_data = {}
        loaded    = 0
        errors    = 0

        # Erweitert on 22 Sectionen (Section 22 optional)
        for section in range(1, 23):
            filename   = f"cards_section_{section}.xml"
            local_path = os.path.join(SCRIPT_DIR, filename)
            url        = f"{CARDS_BASE_URL}{filename}"

            try:
                # ── Quelle bestimmen: lokal bebeforetogt, sonst HTTP ──
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
                for unit in root.findall('.//unit'):  # .// = tiefe Suche in alln Ebenen
                    # Pflichtfelder check – unit overspringen if as missing
                    id_elem   = unit.find('id')
                    name_elem = unit.find('name')
                    if id_elem is None or name_elem is None:
                        continue                          # defektes <unit> …
                    if id_elem.text is None or name_elem.text is None:
                        continue                          # … or emptyes Tag

                    base_id = int(id_elem.text)
                    name    = name_elem.text

                    # Basis-card: Level 1
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
                    pass  # optional
                else:
                    print(f"✗  ({e})")
                    errors += 1
            except Exception as e:
                # Section 22 ist optional - 404 ist OK
                if section == 22 and "404" in str(e):
                    pass  # optional
                else:
                    print(f"✗  ({e})")
                    errors += 1

        self._card_data_cache = card_data
        print(f"✓ Card data ready: {len(card_data)} cards from {loaded} Sections "
              f"({errors} Error)")
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
            str: e.g. "Tiamat-3" oder "Draconian Queen" (Level 6 → no Suffix)
        """
        card_info = card_data.get(int(card_id), f"ID_{card_id}")
        
        # Handle dict format (from XML since)
        if isinstance(card_info, dict):
            name = card_info.get('name', f"ID_{card_id}")
        # Handle string format (legacy)
        elif isinstance(card_info, str):
            name = card_info
        else:
            name = f"ID_{card_id}"
        
        # Level 6 entfernen (PS1: replace("-6",""))
        if isinstance(name, str) and name.endswith("-6"):
            name = name[:-2]
        return name

    def _classify_fusion(self, card_name):
        """
        Classifiziert eine Card in eine Fusion-Material-Gruppe.
        Gibt den Gruppen-Index zurück, oder -1 wenn noe Gruppe passt.

        Args:
            card_name: der aufgelöste Name (e.g. "Tiamat-3" oder "Tiamat")
        """
        # Nur den Namen without Level and without Klammer-count check
        base = card_name.split("-")[0].split(" (")[0].strip()
        for idx, (group_name, prefixes) in enumerate(FUSION_GROUPS):
            if base in prefixes:
                return idx
        return -1

    def salvage_base_epics_keep_x(self, keep_count=1, silent=False):
        """
        Salvaged alle Base Epics bis auf X Stück pro Card.
        
        Base Epics sind die 25 Fusion-Material Cardn:
        - 5x Bloodthirsty (ohne Malgoth)
        - 5x Imperial (ohne Nimbus)
        - 5x Raider (ohne Omega)
        - 5x Righteous (ohne Benediction)
        - 5x Xeno (ohne Apex)
        
        Args:
            keep_count: Anzahl die pro Card behalten werden soll (Standard: 1)
            silent: Wenn True, reduzierte Ausgabe (für Workflows)
        
        Returns:
            (success: bool, sp_gain: int)
        """
        if not self.init_data:
            self.initialize()
        
        if not silent:
            print(f"\n{'='*60}")
            print(f"SALVAGE BASE EPICS (keep {keep_count} per card)")
            print(f"{'='*60}")
        
        # Card-since load
        card_data = self._load_card_data_with_rarity()
        if not card_data:
            if not silent:
                print("✗ Cannot continue without card data.")
            return False, 0
        
        # Base Epics identifizieren (from Fusion-Gruppen, only Epics)
        base_epic_names = []
        for group_name, card_names in FUSION_GROUPS[1:]:  # Skip Vindicator Reactors
            for card_name in card_names:
                # Check if Epic
                for card_id, info in card_data.items():
                    # Handle both dict and string format
                    if isinstance(info, dict):
                        if info.get('name') == card_name and info.get('level', 1) == 1 and info.get('rarity') == 3:
                            base_epic_names.append(card_name)
                            break
                    elif isinstance(info, str):
                        # String format doesn't have rarity info, skip
                        continue
        
        if not silent:
            print(f"\nBase Epics found: {len(base_epic_names)}")
            print(f"Keep: {keep_count} per card")
            print(f"Salvage: Everything above\n")
        
        # Inventar throughgehen
        user_cards = self.init_data.get('user_cards', {})
        
        to_salvage = []
        
        for card_id, info in user_cards.items():
            card_id_int = int(card_id)
            
            # Upgradematerialien, Commanders and Dominions overspringen
            if card_id_int in EXCLUDED_CARD_IDS:
                continue
            
            num_owned = int(info.get('num_owned', 0))
            if num_owned <= 0:
                continue
            
            card_id_int = int(card_id)
            card_info = card_data.get(card_id_int)
            
            if not card_info:
                continue
            
            # Handle both dict and string format
            if isinstance(card_info, dict):
                card_name = card_info.get('name', '')
                card_level = card_info.get('level', 1)
            elif isinstance(card_info, str):
                # String format - parse level from name
                card_name = card_info
                card_level = 1
                if '-' in card_info:
                    parts = card_info.rsplit('-', 1)
                    try:
                        card_level = int(parts[1])
                    except ValueError:
                        pass
            else:
                continue
            
            # Ist es a Base Epic?
            if card_name in base_epic_names and card_level == 1:
                if num_owned > keep_count:
                    salvage_amount = num_owned - keep_count
                    to_salvage.append({
                        'card_id': card_id_int,
                        'name': card_name,
                        'owned': num_owned,
                        'keep': keep_count,
                        'salvage': salvage_amount
                    })
        
        if not to_salvage:
            if not silent:
                print("✓ Nothing to salvage - all base epics already at target count or below")
            return True, 0
        
        # Summary
        to_salvage.sort(key=lambda x: x['name'])
        
        total_salvage = 0
        total_sp = 0
        
        if not silent:
            print(f"{'card':<25} {'Besitz':>8} {'Behalten':>10} {'Salvage':>10}")
            print("─" * 60)
        
        for item in to_salvage:
            if not silent:
                print(f"{item['name']:<25} {item['owned']:>8} {item['keep']:>10} {item['salvage']:>10}")
            total_salvage += item['salvage']
            total_sp += item['salvage'] * 5  # Base Epics geben 5 SP
        
        if not silent:
            print("─" * 60)
            print(f"{'Total:':<25} {'':<8} {'':<10} {total_salvage:>10}")
            print(f"\nExpected SP gain: +{total_sp:,} SP (at 20 SP per epic)\n")
        
        # SP LIMIT CHECK BEFORE salvaging
        salvage_before = int(self.init_data.get('user_data', {}).get('salvage', 0))
        
        sp_cap = self.get_sp_cap()
        if salvage_before >= sp_cap:
            if not silent:
                print(f"\n⚠ WARNING: Already at SP maximum ({sp_cap:,})!")
                print(f"⚠ Salvaging now would DESTROY cards WITHOUT giving SP!")
                print(f"\n❌ Salvage aborted to prevent loss")
            return False, 0
        
        # Check if salvage would exceed limit
        estimated_sp_after = salvage_before + total_sp
        if estimated_sp_after > sp_cap:
            sp_that_will_be_lost = estimated_sp_after - sp_cap
            if not silent:
                print(f"\n⚠ WARNING: Salvage would exceed SP maximum!")
                print(f"   Current SP: {salvage_before:,}")
                print(f"   Expected gain: +{total_sp:,}")
                print(f"   Would be: {estimated_sp_after:,}")
                print(f"   Maximum: {sp_cap:,}")
                print(f"   → {sp_that_will_be_lost:,} SP would be LOST!")
                if not confirm_action("\n⚠ Continue anyway (some SP will be lost)?"):
                    print("✓ Salvage canceled to prevent SP loss")
                    return False, 0
        
        # confirmation (only if not silent)
        if not silent:
            if not confirm_action(f"Really salvage {total_salvage} Base Epics?"):
                print("Canceled")
                return False, 0
        
        if not silent:
            print(f"\n⏳ Salvage {total_salvage} cards...")
        
        salvaged_count = 0
        sp_gained = 0
        
        for i, item in enumerate(to_salvage, 1):
            card_id = item['card_id']
            salvage_amount = item['salvage']
            
            if not silent:
                print(f"  [{i}/{len(to_salvage)}] {item['name']}: -{salvage_amount}...", end=' ', flush=True)
            
            # Jede einzelne card salvagen
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
                        print(f"✗ Error: {e}")
                    break
            
            if not silent:
                print("✓")
            sleep(0.2)  # Rate limiting
        
        # since upsincete
        self.initialize()
        salvage_after = int(self.init_data.get('user_data', {}).get('salvage', 0))
        sp_actual = salvage_after - salvage_before
        
        if not silent:
            print(f"\n{'='*60}")
            print(f"ERGEBNIS")
            print(f"{'='*60}")
            print(f"Salvaged         : {salvaged_count}/{total_salvage} cards")
            print(f"SP before        : {salvage_before:,}")
            print(f"SP after       : {salvage_after:,}")
            print(f"SP gewonnen      : +{sp_actual:,}")
            print(f"{'='*60}\n")
        
        return True, sp_actual

    def _load_card_data_with_rarity(self):
        """
        Lädt Card-Daten inkl. Rarity, Level und Tier aus den XMLs.
        Nutzt Cache wenn available.
        
        Returns:
            dict: { card_id: {'name': str, 'level': int, 'rarity': int, 'tier': int} }
        """
        # Cache verwenden if present
        if self._card_data_with_rarity_cache is not None:
            return self._card_data_with_rarity_cache
        
        print("⏳ Loading card data with Rarity-Info...")
        
        card_data = {}
        loaded = 0
        errors = 0
        
        # Erweitert on 22 Sectionen (Section 22 optional)
        for section in range(1, 23):
            filename = f"cards_section_{section}.xml"
            local_path = os.path.join(SCRIPT_DIR, filename)
            url = f"{CARDS_BASE_URL}{filename}"
            
            try:
                # Lokal or HTTP
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
                    
                    # Fusion-Rezept: Was ist its next Upgrade?
                    upgrade_id = None
                    first_upgrade = unit.find('.//upgrade')
                    if first_upgrade is not None:
                        upgrade_cid = first_upgrade.find('card_id')
                        if upgrade_cid is not None and upgrade_cid.text:
                            upgrade_id = int(upgrade_cid.text)
                    
                    # Basis-card: Level 1
                    card_data[base_id] = {
                        'name': name,
                        'level': 1,
                        'rarity': rarity,
                        'tier': tier,
                        'upgrade_id': upgrade_id,
                        'base_id': base_id  # Base verweist on sich selbst
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
                            'tier': tier,
                            'base_id': base_id  # Verweist on Level-1 Version
                        }
                
                loaded += 1
                
            except Exception as e:
                # Section 22 ist optional - skip at error
                if section == 22:
                    pass  # Ignoriere error for Section 22
                else:
                    errors += 1
        
        print(f"✓ {len(card_data)} cards from {loaded} Sections ({errors} Error)")
        
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
                print(f"✓ {len(fusion_recipes)} fusion recipes loaded")
            except Exception as e:
                print(f"⚠ Could not load fusion recipes: {e}")
        else:
            print(f"⚠ fusion_recipes_cj2.xml not found in {SCRIPT_DIR}")
        
        # Berechne Tier for each Basis-card (Level 1)
        # IMPORTANT: Must go by names, since recipes can use different IDs!
        
        # Step 1: Build Name->IDs Mapping (only Level 1)
        name_to_ids = {}
        for card_id, info in card_data.items():
            # Handle both dict and string format
            if isinstance(info, dict):
                if info.get('level', 1) == 1:
                    name = info.get('name', '')
                    if name:
                        if name not in name_to_ids:
                            name_to_ids[name] = []
                        name_to_ids[name].append(card_id)
            elif isinstance(info, str):
                # String format: extract level from name (e.g., "Daemon-1")
                if '-' in info:
                    base_name, level_str = info.rsplit('-', 1)
                    try:
                        level = int(level_str)
                        if level == 1:
                            if info not in name_to_ids:
                                name_to_ids[info] = []
                            name_to_ids[info].append(card_id)
                    except ValueError:
                        pass
        
        # Step 2: Build Name->Rezept Mapping
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
        
        # Step 3: Find welche cards als Basis verwendet werden
        used_as_base = set()
        for base_names in name_recipes.values():
            for base_name in base_names:
                used_as_base.add(base_name)
        
        # Schritt 4: Bestimme Tier based on Position
        def get_fusion_tier_by_position(name):
            """
            Tier-Logik basierend auf Position in Fusion-Kette:
            - Tier 0: Nur Basis (no Rezept, wird aber verwendet)
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
                return 0  # Fallback (none Fusion)
        
        # Schritt 5: Set fusion_tier for all Level-1 cards
        for card_id, info in card_data.items():
            # Handle both dict and string format
            if isinstance(info, dict):
                if info.get('level', 1) == 1:
                    name = info.get('name', '')
                    if name:
                        tier = get_fusion_tier_by_position(name)
                        card_data[card_id]['fusion_tier'] = tier
            # String format catnot be modified, skip
            elif isinstance(info, str):
                continue
        
        # Cache set
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
            - Pro Card: "Name-Level" bzw. "Name-Level (count)" wenn >1
            - Am Ende: "//cards from restore" + buyback_data Einträge

        currentdecks.txt:
            - Pro Deck eine Zeile:
              "DeckName:Commander,Dominion,Card1,Card2 #count,..."
            - Aktives Deck wird mit [A] markiert, Defense mit [D]
        """
        try:
            print("\n=== INVENTORY EXPORTIEREN - START ===")
            
            if not self.init_data:
                print("⏳ Initialisiere...")
                self.initialize()

            print("⏳ Loading card data...")
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Cannot continue without card data.")
                return

            print(f"✓ {len(card_data)} cards loaded")
            print("\n⏳ Verarbeite inventory...")

            # ----------------------------------------------------------
            # A) ownedcards.txt
            # ----------------------------------------------------------
            user_cards  = self.init_data.get('user_cards', {})
            buyback     = self.init_data.get('buyback_data', {})

            print(f"   User has {len(user_cards)} card entries")
            
            # Gruppen-Buckets initialize
            buckets = {i: [] for i in range(len(FUSION_GROUPS))}
            buckets[-1] = []   # Rest

            print("   Classifying cards...")
            for card_id, info in user_cards.items():
                card_id_int = int(card_id)
                
                # KEIN Filter more - all cards werden exportiert
                # (so Dominion Shards, Dominions and Commanders)
                
                num_owned = int(info.get('num_owned', 0))
                if num_owned <= 0:
                    continue

                name = self._resolve_card(card_id, card_data)

                # count append if >1
                line = name if num_owned == 1 else f"{name} ({num_owned})"

                group_idx = self._classify_fusion(name)
                buckets[group_idx].append(line)

            # file tosammenbauen
            print("   Building ownedcards.txt...")
            owned_lines = []
            for idx, (group_name, _) in enumerate(FUSION_GROUPS):
                owned_lines.append(f"//{group_name}")
                owned_lines.extend(buckets[idx])
                owned_lines.append("")          # Leerzeile between Gruppen

            # Rest (none Gruppe)
            owned_lines.extend(buckets[-1])

            # Buyback-Anhatg ("cards from restore")
            print("   Verarbeite Buyback-Data...")
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
            
            # Im Skript-directory schreiben, not im currenten Arattsverzeichnis
            owned_path = os.path.join(SCRIPT_DIR, "ownedcards.txt")
            print(f"   Ziel: {owned_path}")
            
            # Delete old file if present
            if os.path.exists(owned_path):
                try:
                    print(f"   Deleting old file...")
                    os.remove(owned_path)
                    print(f"   ✓ Old file deleted")
                except Exception as e:
                    print(f"   ⚠ Could not delete old file: {e}")
                    raise
            
            # Neue file create
            try:
                print(f"   Creating new file...")
                with open(owned_path, 'w', encoding='ascii', errors='replace') as f:
                    f.write("\n".join(owned_lines))
                print(f"✓ {os.path.basename(owned_path)} written ({sum(len(b) for b in buckets.values())} cards)")
                    
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

            print(f"   User has {len(user_decks)} Decks")
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

                # Cards with count
                card_parts = []
                for cid, count in deck.get('cards', {}).items():
                    cname = self._resolve_card(cid, card_data)
                    count = int(count)
                    card_parts.append(f"{cname} #{count}" if count > 1 else cname)

                # Zeile tosammenbauen: Name:Commander,Dominion,Cards...
                parts = [commander]
                if dominion:
                    parts.append(dominion)
                parts.extend(card_parts)

                line = f"{deck_name}{mark_str}:{','.join(parts)}"
                deck_lines.append(line)

            # Schreiben
            print("   Schreibe currentdecks.txt...")
            
            # Im Skript-directory schreiben
            decks_path = os.path.join(SCRIPT_DIR, "currentdecks.txt")
            print(f"   Ziel: {decks_path}")
            
            # Delete old file if present
            if os.path.exists(decks_path):
                try:
                    print(f"   Deleting old file...")
                    os.remove(decks_path)
                    print(f"   ✓ Old file deleted")
                except Exception as e:
                    print(f"   ⚠ Could not delete old file: {e}")
                    raise
            
            # Neue file create
            try:
                print(f"   Creating new file...")
                with open(decks_path, 'w', encoding='ascii', errors='replace') as f:
                    f.write("\n".join(deck_lines))
                print(f"✓ {os.path.basename(decks_path)} written ({len(deck_lines)} Decks)")
                    
            except PermissionError as e:
                raise PermissionError(
                    f"Kann '{decks_path}' nicht schreiben. "
                    f"Bitte prüfe die Ordner-Berechtigungen für '{SCRIPT_DIR}'"
                ) from e

            # Summary
            print(f"\n=== SUMMARY ===")
            print(f"✓ ownedcards.txt: {len(owned_lines)} Zeilen")
            print(f"✓ currentdecks.txt: {len(deck_lines)} Decks")
            print(f"\n=== INVENTORY EXPORT - COMPLETE ===")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"KRITISCHER FEHLER in get_inventory():")
            print(f"{'='*60}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            print(f"\nStacktrace:")
            traceback.print_exc()
            print(f"{'='*60}")
            print("\nPress Enter to continue...")
            input()
    
    def salvage_card(self, card_id):
        """
        Salvages a single card
        
        Args:
            card_id: ID of the card to salvage
            
        Note: This function does NOT check SP limit!
        Use salvage_all_commons/rares/base_epics instead for safe batch salvaging.
        """
        try:
            result = self.api.call('salvageCard', card_id=card_id)
            print(f"✓ card {card_id} salvaged")
            return result
        except Exception as e:
            print(f"✗ Error while salvaging: {e}")
            return None
    
    # ==================== BUYBACK ====================
    
    def get_buyback_info(self):
        """
        Gibt Informationen über Buyback-Cardn zurück
        
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
            
            # cardsinformationen abrufen
            card_info = card_data.get(int(card_id), {
                'name': f'ID_{card_id}',
                'level': 1,
                'rarity': 3,
                'tier': 0,
                'fusion_tier': 0
            })
            
            # Kosten based on Seltenheit UND Fusion-Tier calculate
            rarity = card_info.get('rarity', 3)
            fusion_tier = card_info.get('fusion_tier', 0)
            level = card_info.get('level', 1)
            
            # Get costs from BUYBACK_COSTS Dictionary
            cost_per_card = BUYBACK_COSTS.get((rarity, fusion_tier), 0)
            
            # Fallback if Kombination not existiert
            if cost_per_card == 0:
                # Try with Tier 0
                cost_per_card = BUYBACK_COSTS.get((rarity, 0), 20)
            
            result[card_id] = {
                'name': f"{card_info['name']}-1",  # Immer Level 1 im Buyback-Store
                'base_name': card_info['name'],  # Original-Name for Suche
                'number': number,
                'rarity': rarity,
                'tier': fusion_tier,  # Now fusion_tier
                'rarity_name': RARITY_NAMES.get(rarity, 'Unknown'),
                'cost_per_card': cost_per_card,
                'total_cost': cost_per_card * number
            }
        
        return result
    
    def list_buyback_cards(self):
        """
        Listet alle Cardn im Buyback-Store mit Details und Kosten
        """
        buyback_info = self.get_buyback_info()
        
        if not buyback_info:
            print("\n❌ None cards im Buyback-Store")
            return
        
        # Currente SP display
        current_sp = self.get_salvage()
        
        print("\n" + "="*70)
        print("BUYBACK-STORE")
        print("="*70)
        print(f"Available SP: {current_sp:,}")
        print(f"cards im Store: {len(buyback_info)}")
        print()
        
        # Nach Seltenheit gruppieren
        by_rarity = {}
        for card_id, info in buyback_info.items():
            rarity = info['rarity']
            if rarity not in by_rarity:
                by_rarity[rarity] = []
            by_rarity[rarity].append((card_id, info))
        
        # Ausgabe sortiert after Seltenheit (4 -> 1)
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
                
                # Cat es sich leisten?
                affordable = "✓" if current_sp >= total else "✗"
                
                print(f"{affordable} [{card_id:>6}] {name:<30} Tier{tier} x{number:>3}  "
                      f"({cost_per:>4} SP/Card = {total:>6} SP total)")
            print()
        
        print("="*70)
        print(f"Gesamtkosten for all cards: {total_cost:,} SP")
        if current_sp >= total_cost:
            print(f"✓ You can buy back ALL cards")
        else:
            print(f"✗ You need {total_cost - current_sp:,} SP")
        print("="*70)
    
    def buyback_card(self, card_name_or_id, quantity=1):
        """
        Kauft eine Card aus dem Buyback-Store zurück
        
        Args:
            card_name_or_id: Name oder ID der Card (e.g. "Infernal Walker" oder 50123)
            quantity: Anzahl der Cardn (default: 1, 0 = alle)
        
        Returns:
            API response oder None bei Error
        """
        try:
            # Check ob Eingabe a ID ist (only Ziffern)
            if isinstance(card_name_or_id, str) and not card_name_or_id.isdigit():
                # Es ist a Name - konvertiere to ID
                card_id = self._find_buyback_card_id_by_name(card_name_or_id)
                if card_id is None:
                    print(f"✗ card '{card_name_or_id}' not found in Buyback store")
                    return None
            else:
                card_id = int(card_name_or_id)
            
            # Buyback-Info abrufen
            buyback_info = self.get_buyback_info()
            
            if str(card_id) not in buyback_info:
                print(f"✗ card {card_id} is not in Buyback store")
                return None
            
            info = buyback_info[str(card_id)]
            available = info['number']
            
            # Quattity validieren
            if quantity == 0:
                quantity = available
            elif quantity > available:
                print(f"✗ Nur {available}x {info['name']} available (du wolltest {quantity}x)")
                return None
            
            # Kosten calculate
            cost = info['cost_per_card'] * quantity
            current_sp = self.get_salvage()
            
            if current_sp < cost:
                print(f"✗ Not enough SP: {current_sp:,} available, {cost:,} required")
                return None
            
            # API-Call
            # Note: Basierend on dem Muster could die API entweder card_id and quattity
            # or only card_id erwarten. Wir probieren andes.
            try:
                # Try with quattity-Parameter
                result = self.api.call('buybackCard', card_id=card_id, quantity=quantity)
            except:
                # If its not funktioneverrt, probiere only card_id (for 1 card)
                if quantity == 1:
                    result = self.api.call('buybackCard', card_id=card_id)
                else:
                    # For multiple cards, repeat the call
                    print(f"⏳ Buying {quantity}x {info['name']} back (individual calls)...")
                    for i in range(quantity):
                        result = self.api.call('buybackCard', card_id=card_id)
                        if i < quantity - 1:
                            sleep(0.5)  # Kurze Pfrome between Calls
            
            print(f"✓ {quantity}x {info['name']} for {cost:,} SP bought back")
            print(f"  Verbleibende SP: {current_sp - cost:,}")
            
            return result
            
        except Exception as e:
            print(f"✗ Error while Buyback: {e}")
            return None
    
    def _find_buyback_card_id_by_name(self, card_name):
        """
        Finds the card ID im Buyback-Store anhand des Namens
        
        Args:
            card_name: Name der Card (e.g. "Infernal Walker" oder "Lucifire-1")
        
        Returns:
            card_id als int oder None wenn nicht gefunden
        """
        buyback_info = self.get_buyback_info()
        
        # Remove -1 Suffix if present (Buyback ist always Level 1)
        card_name_clean = card_name.strip()
        if card_name_clean.endswith('-1'):
            card_name_clean = card_name_clean[:-2]
        
        card_name_lower = card_name_clean.lower()
        
        # Exakte Suche against base_name
        for card_id, info in buyback_info.items():
            if info['base_name'].lower() == card_name_lower:
                return int(card_id)
        
        # Teilstring-Suche (if exakt not gefanden)
        matches = []
        for card_id, info in buyback_info.items():
            if card_name_lower in info['base_name'].lower():
                matches.append((card_id, info['name']))  # Zeige name with -1 Suffix
        
        if len(matches) == 1:
            card_id = matches[0][0]
            print(f"✓ Found: {matches[0][1]} (ID: {card_id})")
            return int(card_id)
        elif len(matches) > 1:
            print(f"✗ Multiple cards found for '{card_name}':")
            for card_id, name in matches[:5]:  # Zeige max 5
                print(f"   [{card_id}] {name}")
            return None
        
        return None
    
    def buyback_multiple(self, rarity_filter=None, max_sp=None):
        """
        Kauft mehrere Cardn aus dem Buyback-Store zurück
        
        Args:
            rarity_filter: Nur Cardn dieser Seltenheit zurückbuyingn (1-4, None = alle)
            max_sp: Maximale SP, die spent werden sollen (None = alle availableen)
        """
        buyback_info = self.get_buyback_info()
        
        if not buyback_info:
            print("\n❌ None cards im Buyback-Store")
            return
        
        # Filter atwenden
        filtered = {}
        for card_id, info in buyback_info.items():
            if rarity_filter is None or info['rarity'] == rarity_filter:
                filtered[card_id] = info
        
        if not filtered:
            if rarity_filter:
                print(f"\n❌ None {RARITY_NAMES.get(rarity_filter, 'Unknown')}-cards im Buyback-Store")
            else:
                print("\n❌ None passenden cards found")
            return
        
        # Sort by cost (cheapest first)
        sorted_cards = sorted(filtered.items(), key=lambda x: x[1]['cost_per_card'])
        
        current_sp = self.get_salvage()
        if max_sp is None:
            max_sp = current_sp
        
        print("\n" + "="*70)
        print("BUYBACK - MEHRERE CARDS")
        print("="*70)
        print(f"Available SP: {current_sp:,}")
        print(f"Maximales Budget: {max_sp:,} SP")
        if rarity_filter:
            print(f"Filter: {RARITY_NAMES.get(rarity_filter)} cards")
        print()
        
        total_bought = 0
        total_spent = 0
        
        for card_id, info in sorted_cards:
            quantity = info['number']
            cost_total = info['total_cost']
            
            # Checkn ob still Budget present
            if total_spent + cost_total > max_sp:
                # Teilweise konen if possible
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
                # All cards konen
                result = self.buyback_card(card_id, quantity)
                if result:
                    total_spent += cost_total
                    total_bought += quantity
                    sleep(0.5)  # Pfrome between purchases
        
        print("\n" + "="*70)
        print(f"✓ {total_bought} cards for {total_spent:,} SP bought back")
        print(f"  Verbleibende SP: {current_sp - total_spent:,}")
        print("="*70)
    
    def buyback_by_names(self, card_names, max_sp=None):
        """
        Kauft mehrere Cardn anhand einer Namensliste zurück
        
        Args:
            card_names: Liste von Cardnnamen oder komma-separierter String
            max_sp: Maximale SP (None = alle availableen)
        """
        if isinstance(card_names, str):
            card_names = [name.strip() for name in card_names.split(',')]
        
        buyback_info = self.get_buyback_info()
        current_sp = self.get_salvage()
        if max_sp is None:
            max_sp = current_sp
        
        print("\n" + "="*70)
        print("BUYBACK - BY NAME")
        print("="*70)
        print(f"Available SP: {current_sp:,}")
        print(f"Maximales Budget: {max_sp:,} SP")
        print()
        
        total_bought = 0
        total_spent = 0
        
        for card_name in card_names:
            if not card_name:
                continue
            
            # Find card ID
            card_id = self._find_buyback_card_id_by_name(card_name)
            if card_id is None:
                print(f"⚠ Skipping '{card_name}' (not found)")
                continue
            
            info = buyback_info[str(card_id)]
            quantity = info['number']
            cost_total = info['total_cost']
            
            # Budget check
            if total_spent + cost_total > max_sp:
                remaining_budget = max_sp - total_spent
                partial_quantity = remaining_budget // info['cost_per_card']
                
                if partial_quantity > 0:
                    result = self.buyback_card(card_id, partial_quantity)
                    if result:
                        partial_cost = partial_quantity * info['cost_per_card']
                        total_spent += partial_cost
                        total_bought += partial_quantity
                print(f"⚠ Budget reached - remaining cards skipped")
                break
            else:
                result = self.buyback_card(card_id, quantity)
                if result:
                    total_spent += cost_total
                    total_bought += quantity
                    sleep(0.5)
        
        print("\n" + "="*70)
        print(f"✓ {total_bought} cards for {total_spent:,} SP bought back")
        print(f"  Verbleibende SP: {current_sp - total_spent:,}")
        print("="*70)
    
    # ==================== SHOP & BUYINGN ====================
    
    def buy_stamina(self, amount=1):
        """
        Kauft Stamina
        
        Args:
            amount: Anzahl der Käufe
        """
        try:
            result = self.api.call('buyStamina', amount=amount)
            print(f"✓ {amount}x Stamina purchased")
            return result
        except Exception as e:
            print(f"✗ Error while Kauf: {e}")
            return None
    
    def buy_energy(self, amount=1):
        """
        Kauft Arena Energy
        
        Args:
            amount: Anzahl der Käufe
        """
        try:
            result = self.api.call('buyEnergy', amount=amount)
            print(f"✓ {amount}x Arena Energy purchased")
            return result
        except Exception as e:
            print(f"✗ Error while Kauf: {e}")
            return None
    
    # ==================== SHOP – PAKETE & BATCH-SALVAGE ====================

    # ---------- Gold-Hilfsfunktion ----------

    def get_gold(self):
        """Gibt currentes Gold aus init_data zurück"""
        if not self.init_data:
            self.initialize()
        return int(self.init_data.get('user_data', {}).get('money', 0))
    
    def get_salvage(self):
        """Returns current SP from init_data"""
        if not self.init_data:
            self.initialize()
        return int(self.init_data.get('user_data', {}).get('salvage', 0))
    
    def get_sp_cap(self):
        """
        Returns the SP cap (maximum salvage) for this account.
        
        The SP cap is account-specific and can vary between players.
        Tries multiple possible field names, falls back to default.
        
        Returns:
            int: Maximum SP this account can hold
        """
        if not self.init_data:
            self.initialize()
        
        user_data = self.init_data.get('user_data', {})
        
        # Try different possible field names for SP cap
        possible_fields = [
            'salvage_max',      # Most likely
            'max_salvage',      
            'salvage_cap',
            'salvage_limit',
            'sp_max',
            'sp_cap',
            'max_sp'
        ]
        
        for field in possible_fields:
            if field in user_data:
                try:
                    cap = int(user_data[field])
                    if cap > 0:  # Sanity check
                        return cap
                except (ValueError, TypeError):
                    continue
        
        # Fallback: Use default value
        return SP_MAX_FALLBACK

    # ---------- Packages ----------

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
            print(f"✗ Kauf failed: {e}")
            return False, []

    def buy_packs(self, count):
        """
        Kauft mehrere Pakete nacheinander mit Delay.

        Args:
            count: Anzahl zu buyingnder Pakete

        Returns:
            (purchasede: int, alle_neue_karten: list)
        """
        print(f"\n{'='*50}")
        print(f" BUYING {count}x 2000-GOLD PAKET")
        print(f"{'='*50}")

        gold_before = self.get_gold()
        print(f" Gold before   : {gold_before:,}")
        print(f" Costs total : {count * PACK_COST:,}")

        if gold_before < count * PACK_COST:
            print(f"\n ✗ Not enough Gold!")
            print(f"   Required  : {count * PACK_COST:,}")
            print(f"   Available : {gold_before:,}")
            return 0, []

        purchased     = 0
        alle_karten = []

        print()  # Neue Zeile for Fortschrittsbalken
        for i in range(1, count + 1):
            # Fortschrittsbalken
            percent = int((i / count) * 100)
            bar_length = 40
            filled = int((i / count) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Zeile overschreiben with \r
            print(f"\r [{bar}] {percent}% ({i}/{count})", end='', flush=True)
            
            success, new_cards = self.buy_pack()

            if success:
                purchased += 1
                alle_karten.extend(new_cards)

            if i < count:
                sleep(DELAY_BETWEEN_BUYS)
        
        # Finale 100% Anzeige
        bar = '█' * bar_length
        print(f"\r [{bar}] 100% ({count}/{count})")

        # since upsincete
        self.initialize()
        gold_after = self.get_gold()

        print(f"\n{'─'*50}")
        print(f" Purchased        : {purchased}/{count}")
        print(f" Gold after   : {gold_after:,}")
        print(f" Gold spent: {gold_before - gold_after:,}")
        print(f" Neue cards    : {len(alle_karten)}")
        print(f"{'─'*50}")

        return purchased, alle_karten

    # ---------- Batch-Salvage ----------

    def salvage_all_commons(self):
        """
        Salvages ALL L1 Common Cards at once (salvageL1CommonCards).
        Server calculates everything - no ID list needed.

        Returns:
            (success: bool, sp_gain: int)
        """
        print(f"\n{'='*50}")
        print(f" SALVAGE ALL COMMON CARDS")
        print(f"{'='*50}")

        salvage_before = int(self.init_data.get('user_data', {}).get('salvage', 0))
        print(f" Salvage before: {salvage_before:,} SP")
        
        # SP LIMIT CHECK
        sp_cap = self.get_sp_cap()
        
        if salvage_before >= sp_cap:
            print(f"\n ⚠ WARNING: Already at SP maximum ({sp_cap:,})!")
            print(f" ⚠ Salvaging now would DESTROY cards WITHOUT giving SP!")
            print(f"\n ❌ Salvage aborted to prevent loss")
            return False, 0
        
        # Warning if close to limit
        if salvage_before > sp_cap - 1000:
            remaining_space = sp_cap - salvage_before
            print(f"\n ⚠ WARNING: Close to SP maximum!")
            print(f" ⚠ Only {remaining_space:,} SP space remaining")
            print(f" ⚠ Excess SP from salvage will be LOST!")
            if not confirm_action("\n Continue salvage anyway?"):
                print(" ✓ Salvage canceled")
                return False, 0

        try:
            result = self.api.call('salvageL1CommonCards', dummy='data')

            if result and result.get('result') == True:
                salvage_after = int(result.get('user_data', {}).get('salvage', 0))
                sp_gain       = salvage_after - salvage_before
                
                # Check if SP was lost
                if salvage_after >= sp_cap and sp_gain == 0:
                    print(f" ⚠ WARNING: At SP maximum - no SP gained!")
                    print(f" ⚠ Cards were salvaged but SP was lost")

                print(f" ✓ Salvage successful!")
                print(f"{'─'*50}")
                print(f" Salvage after: {salvage_after:,} SP")
                print(f" SP gained    : +{sp_gain:,} SP")
                print(f"{'─'*50}")

                self.init_data = result
                return True, sp_gain
            else:
                print(" ✗ Salvage failed")
                return False, 0

        except Exception as e:
            print(f" ✗ Error: {e}")
            return False, 0

    def salvage_all_rares(self):
        """
        Salvages ALL L1 Rare Cards at once (salvageL1RareCards).
        Analogous to salvage_all_commons.

        Returns:
            (success: bool, sp_gain: int)
        """
        print(f"\n{'='*50}")
        print(f" SALVAGE ALL RARE CARDS")
        print(f"{'='*50}")

        salvage_before = int(self.init_data.get('user_data', {}).get('salvage', 0))
        print(f" Salvage before: {salvage_before:,} SP")
        
        # SP LIMIT CHECK
        sp_cap = self.get_sp_cap()
        
        if salvage_before >= sp_cap:
            print(f"\n ⚠ WARNING: Already at SP maximum ({sp_cap:,})!")
            print(f" ⚠ Salvaging now would DESTROY cards WITHOUT giving SP!")
            print(f"\n ❌ Salvage aborted to prevent loss")
            return False, 0
        
        # Warning if close to limit
        if salvage_before > sp_cap - 5000:  # Higher threshold for rares (give more SP)
            remaining_space = sp_cap - salvage_before
            print(f"\n ⚠ WARNING: Close to SP maximum!")
            print(f" ⚠ Only {remaining_space:,} SP space remaining")
            print(f" ⚠ Excess SP from salvage will be LOST!")
            if not confirm_action("\n Continue salvage anyway?"):
                print(" ✓ Salvage canceled")
                return False, 0

        try:
            result = self.api.call('salvageL1RareCards', dummy='data')

            if result and result.get('result') == True:
                salvage_after = int(result.get('user_data', {}).get('salvage', 0))
                sp_gain       = salvage_after - salvage_before
                
                # Check if SP was lost
                if salvage_after >= sp_cap and sp_gain == 0:
                    print(f" ⚠ WARNING: At SP maximum - no SP gained!")
                    print(f" ⚠ Cards were salvaged but SP was lost")

                print(f" ✓ Salvage successful!")
                print(f"{'─'*50}")
                print(f" Salvage after: {salvage_after:,} SP")
                print(f" SP gained    : +{sp_gain:,} SP")
                print(f"{'─'*50}")

                self.init_data = result
                return True, sp_gain
            else:
                print(" ✗ Salvage failed")
                return False, 0

        except Exception as e:
            print(f" ✗ Error: {e}")
            return False, 0

    # ---------- Workflow: Konen + Salvagen ----------

    def shop_salvage_workflow(self, pack_count, salvage_base_epics=False, keep_base_epics=1):
        """
        Kompletter Workflow:
          1. Pakete buyingn
          2. Alle Commons salvagen
          3. Alle Rares salvagen
          4. Optional: Base Epics salvagen (behalte X)
          5. Summary ausgeben

        Args:
            pack_count: Anzahl zu buyingnder Pakete
            salvage_base_epics: Wenn True, auch Base Epics salvagen
            keep_base_epics: Number of Base Epics die pro Card behalten werden
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

        # Konen
        purchased, neue_karten = self.buy_packs(pack_count)
        if purchased == 0:
            print("\n ✗ None Packages purchased – Workflow canceled")
            return

        # Commons salvagen
        print("\n Wait 3s before Common salvage...")
        sleep(3)
        success_common, sp_gain_common = self.salvage_all_commons()

        # Rares salvagen
        print("\n Wait 2s before Rare salvage...")
        sleep(2)
        success_rare, sp_gain_rare = self.salvage_all_rares()

        # Base Epics salvagen (optional)
        sp_gain_epics = 0
        if salvage_base_epics:
            print("\n Wait 2s before Base Epic salvage...")
            sleep(2)
            success_epic, sp_gain_epics = self.salvage_base_epics_keep_x(keep_base_epics, silent=True)

        # Summary
        self.initialize()
        gold_ende     = self.get_gold()
        salvage_final = int(self.init_data.get('user_data', {}).get('salvage', 0))
        dauer         = (datetime.now() - start_time).seconds

        print(f"\n{'#'*50}")
        print(f"# SUMMARY")
        print(f"{'#'*50}")
        print(f" Dauer            : {dauer}s")
        print(f" Packages purchased   : {purchased}")
        print(f" Neue cards      : {len(neue_karten)}")
        print(f"")
        print(f" Gold Start       : {gold_start:,}")
        print(f" Gold Ende        : {gold_ende:,}")
        print(f" Gold Netto       : {gold_ende - gold_start:,}")
        print(f"")
        print(f" Common-Salvage   : +{sp_gain_common:,} SP")
        print(f" Rare-Salvage     : +{sp_gain_rare:,} SP")
        if salvage_base_epics:
            print(f" Epic-Salvage     : +{sp_gain_epics:,} SP (behalte {keep_base_epics})")
            print(f" Total-Salvage   : +{sp_gain_common + sp_gain_rare + sp_gain_epics:,} SP")
        else:
            print(f" Total-Salvage   : +{sp_gain_common + sp_gain_rare:,} SP")
        print(f"")
        print(f" Salvage counter   : {salvage_final:,} SP")
        print(f"{'#'*50}\n")

    # ==================== WEITERE FUNKTIONEN ====================
    
    def auto_claim_daily_bonus(self):
        """
        Prüft und sammelt Daily Bonus automatisch beim Start.
        Zeigt Cooldown wenn nicht available.
        
        Returns:
            bool: True wenn erfolgreich claimed oder already geholt, False bei Error
        """
        try:
            if not self.init_data:
                self.initialize()
            
            # Check sinceily_bonus_time in init_since
            daily_bonus_time = int(self.init_data.get('daily_bonus_time', 0))
            current_time = int(time.time())
            
            # If sinceily_bonus_time in der Zukunft liegt, ist Cooldown aktiv
            if daily_bonus_time > current_time:
                cooldown_seconds = daily_bonus_time - current_time
                hours = cooldown_seconds // 3600
                minutes = (cooldown_seconds % 3600) // 60
                
                print(f"\n{'─'*60}")
                print(f"📅 Daily Reward")
                print(f"{'─'*60}")
                print(f"Status:   ⏳ Cooldown active")
                print(f"Available in: {hours}h {minutes}min")
                print(f"{'─'*60}")
                return True
            
            # Daily Bonus ist available - hole ab
            result = self.api.call('useDailyBonus')
            
            if result and result.get('result') == True:
                print(f"\n{'─'*60}")
                print(f"📅 Daily Reward")
                print(f"{'─'*60}")
                print(f"Status:   ✓ Successful eingesammelt!")
                
                # Zeige Reward - versuche card name to load
                if 'reward' in result:
                    reward = result['reward']
                    print(f"Reward: {reward}")
                elif 'cards' in result:
                    cards = result.get('cards', {})
                    if cards:
                        # Lade Card-since for Namen
                        card_data = self._load_card_data()
                        
                        # Show first card (Daily Bonus gives only 1 card)
                        card_id = list(cards.keys())[0]
                        card_info = card_data.get(int(card_id), f"card #{card_id}") if card_data else f"card #{card_id}"
                        # Handle both dict and string
                        if isinstance(card_info, dict):
                            card_name = card_info.get('name', f"card #{card_id}")
                        else:
                            card_name = str(card_info)
                        
                        print(f"Reward: {card_name}")
                
                print(f"{'─'*60}")
                
                # since new load
                self.initialize()
                return True
            else:
                # Already claimed or error
                if result and 'message' in result:
                    msg = result['message']
                    if 'already' in msg.lower() or 'already' in msg.lower():
                        print(f"\n{'─'*60}")
                        print(f"📅 Daily Reward")
                        print(f"{'─'*60}")
                        print(f"Status:   ✓ Already heute eingesammelt")
                        print(f"{'─'*60}")
                        return True
                
                return False
                
        except Exception as e:
            # Stille errorbehandlung - soll den Start not blockieren
            return False
    
    def claim_daily_bonus(self):
        """
        Holt den täglichen Bonus ab (useDailyBonus)
        """
        try:
            print("\n" + "="*60)
            print("DAILY BONUS ABHOLEN")
            print("="*60)
            
            print("\n⏳ Claim Daily Bonus...")
            result = self.api.call('useDailyBonus')
            
            if result and result.get('result') == True:
                print("✓ Daily Bonus successful claimed!")
                
                # Zeige was erholden was (if in Response)
                if 'reward' in result:
                    reward = result['reward']
                    print(f"\nReward:")
                    print(f"  {reward}")
                
                # Init-since new load
                self.initialize()
                
            else:
                print("✗ Error while Abholen des Daily Bonus")
                if result:
                    # Check ob already claimed
                    if 'message' in result:
                        msg = result['message']
                        if 'already' in msg.lower() or 'already' in msg.lower():
                            print("   Already heute claimed")
                        else:
                            print(f"   Meldung: {msg}")
                    else:
                        print(f"   API Response: {result}")
            
            print("="*60)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            traceback.print_exc()
    
    def claim_rewards(self):
        """Holt availablee Rewarden ab"""
        try:
            result = self.api.call('claimRewards')
            print("✓ Rewarden claimed")
            return result
        except Exception as e:
            print(f"✗ Error while Abholen: {e}")
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
        
        # Stelle sicher that file in SCRIPT_DIR gespeichert wird
        if not os.path.isabs(filename):
            filename = os.path.join(SCRIPT_DIR, filename)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.init_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Data exported to: {filename}")
            print(f"✓ File size: {os.path.getsize(filename) / 1024:.1f} KB")
            return filename
        except Exception as e:
            print(f"✗ Error while Export: {e}")
            traceback.print_exc()
            return None
    
    def export_guild_decks_simple(self, output_file='guild_decks.txt'):
        """
        Exports guild decks in simple format (nur IDs)
        """
        try:
            print("\n=== GUILD DECK EXPORT ===")
            
            if not self.init_data:
                print("Initialisiere API...")
                if not self.initialize():
                    print("✗ Error during initialization")
                    return
            
            if 'faction' not in self.init_data:
                print("✗ Not in a guild")
                return
            
            faction_name = self.init_data['faction']['name']
            members = self.init_data['faction']['members']
            
            print(f"\nExporting decks for guild: {faction_name}")
            print(f"Count members: {len(members)}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"// Guild: {faction_name}\n")
                f.write(f"// Export Date: {datetime.now()}\n")
                f.write(f"// members: {len(members)}\n\n")
                
                # Gauntlet Patterns
                f.write(f"{faction_name}_D: /^{faction_name}_D_.*$/\n")
                f.write(f"{faction_name}_A: /{faction_name}_A_.*$/\n\n")
                
                # Jedes Mitglied
                for i, member_id in enumerate(members, 1):
                    try:
                        print(f"Verarbeite member {i}/{len(members)}...", end='\r')
                        
                        profile = self.api.call('getProfileData', target_user_id=str(member_id))
                        
                        if not profile or 'player_info' not in profile:
                            print(f"\n⚠ Skipping member {member_id} - none Data")
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
                        print(f"\n✗ Fehlende Data at member {member_id}: {e}")
                        continue
                    except Exception as e:
                        print(f"\n✗ Error at member {member_id}: {e}")
                        continue
            
            print(f"\n✓ Export abgeschlossen: {output_file}")
                
        except PermissionError as e:
            print(f"\n✗ ERROR: None Schreibrechte for '{output_file}'")
            print(f"   Possible solutions:")
            print(f"   1. Close the file if it is open")
            print(f"   2. Use a full path (e.g. C:\\Users\\...\\datei.txt)")
            print(f"   3. Run the script as administrator")
            print(f"   4. Choose a different directory")
        except Exception as e:
            print(f"\n✗ KRITISCHER FEHLER while Export: {e}")
            traceback.print_exc()
    
    # ==================== INVENTAR - CARDN BAUEN ====================
    
    # ==================== INVENTAR - CARDN BAUEN ====================
    
    def build_card(self, card_name_or_id=None):
        """
        Baut eine oder mehrere Cardn - zeigt Rezept, Kosten, Inventar
        
        PHASE 1: Multi-Card Support
        Syntax:
        - "Luxbearer" → 1x Luxbearer-6  
        - "Luxbearer #2" → 2x Luxbearer-6
        - "Luxbearer, Daemon" → beide nacheinander
        - "Luxbearer #2, Daemon #3" → kombineverrt
        
        PHASE 2: Auto-Build (still nicht implementiert)
        PHASE 3: Smart Inventory (still nicht implementiert)
        """
        try:
            print("\n" + "="*80)
            print("BUILD CARD(S) - RECIPE & COSTS")
            print("="*80)
            
            if not card_name_or_id:
                print("\n📋 MULTI-CARD SYNTAX:")
                print("  Individual Card:     Luxbearer")
                print("  Multiple copies:     Luxbearer #2")
                print("  Multiple cards:     Luxbearer, Daemon")
                print("  Combined:         Luxbearer #2, Daemon, Aasi #3")
                
                card_name_or_id = input_with_esc("\nCard name(n) or ID(s) (ESC=Cancel): ")
                if card_name_or_id is None:
                    return
                
                card_name_or_id = card_name_or_id.strip()
                if not card_name_or_id:
                    print("✗ Empty input")
                    return
            
            # ===== PHASE 1: PARSE INPUT =====
            card_requests = []
            card_counts = {}  # {card_name: total_count}
            
            for part in card_name_or_id.split(','):
                part = part.strip()
                if not part:
                    continue
                
                # Remove leading special characters (wie : from copy-paste errors)
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
                        print(f"⚠ Invalid count format in '{part}', using count=1")
                
                # Normalisiere Namen (lowercase for Vergleich)
                part_normalized = part.lower().strip()
                
                # Addiere counts if card already in list
                if part_normalized in card_counts:
                    card_counts[part_normalized]['count'] += count
                else:
                    card_counts[part_normalized] = {'name': part, 'count': count}
            
            # Konvertiere to list
            card_requests = [data for data in card_counts.values()]
            
            if not card_requests:
                print("✗ No valid cards found")
                return
            
            # Zeige was be built soll
            print(f"\n✓ {len(card_requests)} card(s) to build:")
            total_count = sum(req['count'] for req in card_requests)
            for req in card_requests:
                print(f"  • {req['count']}x {req['name']}")
            print(f"\nTotal: {total_count} card(s)")
            
            # ===== BAUE JEDE CARD =====
            for idx, req in enumerate(card_requests, 1):
                print("\n" + "="*80)
                if req['count'] > 1:
                    print(f"CARD {idx}/{len(card_requests)}: {req['count']}x {req['name']}")
                else:
                    print(f"CARD {idx}/{len(card_requests)}: {req['name']}")
                print("="*80)
                
                # Rufe single card build on (with count)
                success = self._build_single_card_info(req['name'], req['count'])
                
                if not success:
                    print(f"\n⚠ Error at {req['name']}")
                    if not confirm_action("Continue with next Card?"):
                        print("\n✗ Canceled")
                        return
            
            print("\n" + "="*80)
            print("✅ ALL CARDS ANALYZED!")
            print("="*80)
            
        except Exception as e:
            print(f"✗ Error in build_card: {e}")
            traceback.print_exc()
    
    def _build_single_card_info(self, card_name_or_id, build_count=1):
        """
        Shows info for a single card (Rezept, Kosten, Inventar)
        Phase 1: Only show info
        Phase 2: Extended with auto-build
        
        Args:
            card_name_or_id: Name oder ID der Card
            build_count: Number of times this card should be built (für SP-Kosten)
        
        Returns: True wenn erfolgreich, False bei Error
        """
        try:
            # Cache clearen to ensure we have current data with base_id
            self._card_data_with_rarity_cache = None
            
            # Load card data with all upgrade levels UND fusion_tier Info
            print("\n⏳ Loading card data...")
            
            # Use _load_card_data_with_rarity for fusion_tier info
            card_data = self._load_card_data_with_rarity()
            if not card_data:
                print("✗ Cannot continue without card data.")
                return False
            
            # Lade Fusion Recipes
            print("⏳ Loading Fusion Recipes...")
            
            fusion_file = os.path.join(SCRIPT_DIR, 'fusion_recipes_cj2.xml')
            if not os.path.exists(fusion_file):
                print(f"✗ fusion_recipes_cj2.xml not found in {SCRIPT_DIR}")
                return False
            
            tree = ET.parse(fusion_file)
            recipes = {}
            
            for recipe in tree.getroot().findall('fusion_recipe'):
                card_id_elem = recipe.find('card_id')
                if card_id_elem is not None:
                    result_id = int(card_id_elem.text)  # Konvertiere to Integer!
                    resources = []
                    for res in recipe.findall('resource'):
                        resources.append({
                            'card_id': int(res.get('card_id')),  # Also here Integer!
                            'number': int(res.get('number'))
                        })
                    recipes[result_id] = resources
            
            print(f"✓ {len(recipes)} Fusion Recipes loaded")
            
            # Lade SP-Kosten
            print("⏳ Loading SP-Costs...")
            
            levels_file = os.path.join(SCRIPT_DIR, 'levels.xml')
            if not os.path.exists(levels_file):
                print(f"✗ levels.xml not found in {SCRIPT_DIR}")
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
            
            # Store as member for Smart Inventory
            self.sp_costs = sp_costs
            
            print(f"✓ SP-Costs table loaded")
            
            # Find target card
            print(f"\n⏳ Searching for '{card_name_or_id}'...")
            
            target_id = None
            target_name = None
            target_level = None
            
            # Is it an ID?
            if card_name_or_id.isdigit():
                if card_name_or_id in card_data:
                    target_id = card_name_or_id
                    card_info = card_data[target_id]
                    if isinstance(card_info, dict):
                        target_name = card_info.get('name', f"ID_{target_id}")
                        target_level = card_info.get('level', 1)
                    else:
                        target_name = card_info if isinstance(card_info, str) else f"ID_{target_id}"
                        target_level = 1
            else:
                # Suche after Namen - NIMM LEVEL 6 als Statsincerd
                search_name = card_name_or_id.lower().replace('-6', '').replace('-', '')
                
                # Zuerst suche Level 6
                for cid, info in card_data.items():
                    if isinstance(info, dict):
                        card_name_clean = info.get('name', '').lower().replace('-', '')
                        if search_name in card_name_clean and info.get('level', 1) == 6:
                            target_id = cid
                            target_name = info.get('name', f"ID_{cid}")
                            target_level = 6
                            break
                    elif isinstance(info, str):
                        card_name_clean = info.lower().replace('-', '')
                        if search_name in card_name_clean and '-6' in info:
                            target_id = cid
                            target_name = info
                            target_level = 6
                            break
                
                # If not gefanden, suche Level 1
                if not target_id:
                    for cid, info in card_data.items():
                        if isinstance(info, dict):
                            card_name_clean = info.get('name', '').lower().replace('-', '')
                            if search_name in card_name_clean and info.get('level', 1) == 1:
                                target_id = cid
                                target_name = info.get('name', f"ID_{cid}")
                                target_level = 1
                                break
                        elif isinstance(info, str):
                            card_name_clean = info.lower().replace('-', '')
                            if search_name in card_name_clean and '-1' in info:
                                target_id = cid
                                target_name = info
                                target_level = 1
                                break
            
            if not target_id:
                print(f"✗ card '{card_name_or_id}' not found")
                return False
            
            target_info = card_data.get(target_id, {})
            if isinstance(target_info, dict):
                target_rarity = target_info.get('rarity', 1)
                target_base_id = target_info.get('base_id', target_id)
            else:
                # String format - defaults
                target_rarity = 1
                target_base_id = target_id
            
            print(f"✓ Found: {target_name}-{target_level} (ID {target_id}, Rarity {target_rarity})")
            
            # If Level 6, we must start from Level 1 base
            if target_level == 6:
                base_target_id = target_base_id
                print(f"  → Building from {target_name}-1 (ID {base_target_id}) and upgrade to Level 6")
            else:
                base_target_id = target_id
            
            # Check ob Rezept existiert
            if base_target_id not in recipes:
                print(f"\n⚠ No Fusion Recipe for {target_name}-1")
                print("   → This card cannot be built (Base-card or Drop)")
                
                # Zeige only Upgrade-Kosten
                if target_level > 1:
                    rarity = target_rarity
                    total_cost = 0
                    steps = []
                    
                    for lvl in range(1, target_level):
                        key = (rarity, lvl)
                        if key in sp_costs:
                            cost = sp_costs[key]
                            total_cost += cost
                            steps.append(str(cost))
                    
                    print(f"\nUpgrade-Costs: {' + '.join(steps)} = {total_cost} SP")
                
                return True  # No error, only none Fusion possible
            
            # Berechne all Base-cards MIT INVENTAR-OPTIMIERUNG
            
            # Get inventory
            user_cards = self.init_data.get('user_cards', {})
            
            # Tracking: Welche cards werden from Inventar verwendet?
            used_from_inventory = {}
            
            def get_optimal_materials(card_id, multiplier=1, depth=0):
                """
                Recursively find all MISSING materials - WITH INVENTORY OPTIMIZATION
                If a card is already available, it will be used instead of being resolved further.
                
                Args:
                    depth: 0 = target card itself, >0 = sub-components
                
                Returns: dict {card_id: count} - only cards that are MISSING
                """
                # Get card info
                info = card_data.get(card_id, {})
                if isinstance(info, dict):
                    base_id = info.get('base_id', card_id)
                    card_name = info.get('name', f'ID_{card_id}')
                    card_level = info.get('level', 1)
                else:
                    base_id = card_id
                    card_name = info if isinstance(info, str) else f'ID_{card_id}'
                    card_level = 1
                
                # Check if this card is in inventory
                owned = 0
                if str(base_id) in user_cards:  # user_cards has string keys!
                    owned = int(user_cards[str(base_id)].get('num_owned', 0))
                
                # CRITICAL PROTECTION: Don't use Neocyte Cores unless building a Commander!
                # Neocyte Cores (43451, 43452) should ONLY be used for Commander upgrades
                if depth > 0 and base_id in NEOCYTE_CORE_IDS:
                    # Check if target card is a Commander
                    target_is_commander = base_target_id in COMMANDER_IDS
                    if not target_is_commander:
                        # NOT a Commander - don't use Neocyte Cores!
                        # Treat as if we don't have any
                        owned = 0
                
                # CRITICAL: For target card at depth=0, check if we have ANY level of it
                # If yes, we can upgrade instead of building from scratch
                if depth == 0 and owned > 0:
                    # We have this card (at some level) - no materials needed for fusion!
                    # Mark as used from inventory
                    if str(base_id) in used_from_inventory:
                        used_from_inventory[str(base_id)] += multiplier
                    else:
                        used_from_inventory[str(base_id)] = multiplier
                    return {}  # No materials needed - will upgrade existing card
                
                # For sub-components (depth > 0): standard inventory check
                if depth > 0 and owned >= multiplier:
                    # Enough present, use from inventory
                    if str(base_id) in used_from_inventory:
                        used_from_inventory[str(base_id)] += multiplier
                    else:
                        used_from_inventory[str(base_id)] = multiplier
                    return {}  # All present, nothing missing
                
                # Calculate how many really missing
                if depth > 0:
                    available_to_use = min(owned, multiplier)
                    remaining_needed = multiplier - available_to_use
                    
                    # Tracking: If partially present
                    if available_to_use > 0:
                        if str(base_id) in used_from_inventory:
                            used_from_inventory[str(base_id)] += available_to_use
                        else:
                            used_from_inventory[str(base_id)] = available_to_use
                else:
                    # Target card itself - need to build from scratch
                    remaining_needed = multiplier
                
                # Nur the missing rest further resolve
                result = {}
                
                # Check ob diese Card a Rezept hat
                if card_id in recipes:
                    # Has recipe - resolve for missing count
                    for res in recipes[card_id]:
                        sub_materials = get_optimal_materials(res['card_id'], res['number'] * remaining_needed, depth + 1)
                        for sub_id, count in sub_materials.items():
                            if sub_id in result:
                                result[sub_id] += count
                            else:
                                result[sub_id] = count
                else:
                    # No recipe for this ID - check if it is an upgrade version
                    if base_id != card_id and base_id in recipes:
                        # Die Level-1 Version hat a Rezept!
                        for res in recipes[base_id]:
                            sub_materials = get_optimal_materials(res['card_id'], res['number'] * remaining_needed, depth + 1)
                            for sub_id, count in sub_materials.items():
                                if sub_id in result:
                                    result[sub_id] += count
                                else:
                                    result[sub_id] = count
                    else:
                        # Echte Base-card (weder diese ID still Base-ID hat Rezept)
                        # These are missing and must be obtained
                        result[card_id] = remaining_needed
                
                return result
            
            base_cards = get_optimal_materials(base_target_id)
            
            # Check ob Zielkarte already in inventory present ist (Tier-2 Check)
            # Get fusion_tier info der Zielkarte
            target_card_info = card_data.get(base_target_id, {})
            if isinstance(target_card_info, dict):
                target_fusion_tier = target_card_info.get('fusion_tier', 0)
            else:
                target_fusion_tier = 0
            
            # Check count der FERTIGEN Zielkarte in inventory
            # IMPORTANT: Check the ID der card die WIRKLICH gebaut wird (with target_level)!
            owned_target_count = 0
            
            # Find the card ID with the target level
            actual_target_id = base_target_id  # Default: Level-1
            if target_level > 1:
                # Suche after der Upgrade-Version with target_level
                for cid, cinfo in card_data.items():
                    if isinstance(cinfo, dict):
                        if cinfo.get('base_id') == base_target_id and cinfo.get('level') == target_level:
                            actual_target_id = cid
                            break
            
            # Count wie maty from dieser EXAKTEN card present sind
            if str(actual_target_id) in user_cards:
                owned_target_count = int(user_cards[str(actual_target_id)].get('num_owned', 0))
            
            # For Tier-2 cards: Check limit of 10
            if target_fusion_tier == 2:
                count_after_build = owned_target_count + build_count
                
                # Check if already at limit
                if owned_target_count >= 10:
                    print(f"\n✓ {target_name}-{target_level}: Limit reached ({owned_target_count}/10)")
                    return True
                
                # Check if build would exceed limit
                if count_after_build > 10:
                    print(f"\n⚠ {target_name}-{target_level}: Would exceed limit!")
                    print(f"   Currently: {owned_target_count}x, Requested: {build_count}x → Would be: {count_after_build}x")
                    print(f"   Maximum you can build: {10 - owned_target_count}x")
                    return True
                
                # Show status if building additional copies
                if owned_target_count > 0:
                    print(f"\n📦 Building additional copies ({owned_target_count}/10 → {count_after_build}/10)")
            
            # For non-Tier-2 cards: Show status if building additional copies
            elif owned_target_count > 0:
                print(f"\n📦 Building additional copy (currently owned: {owned_target_count}x)")
            
            # Show if materials are missing
            if base_cards:
                print(f"\n✗ Materials missing - cannot build")
                return True
            
            # Set total_sp to 0 (actual cost will be shown after build)
            total_sp = 0
            
            # Quick SP check
            
            # Collect ALL cards that must be upgraded
            def collect_all_needed_upgrades(card_id, result_level=None, multiplier=1):
                """
                Collects all upgrade steps that are needed
                Returns: dict {base_id: {'level': target_level, 'count': count}}
                """
                upgrades = {}
                
                # If diese Card a Upgrade-Version ist, hole Base-ID
                info = card_data.get(card_id, {})
                base_id = info.get('base_id', card_id)
                needed_level = info.get('level', 1)
                
                # Check ob Base-Version a Rezept hat
                if base_id in recipes:
                    # Diese Fusion-card muss be built
                    # Und sincetn on needed_level upgegraded werden
                    if needed_level > 1:
                        if base_id in upgrades:
                            upgrades[base_id]['count'] += multiplier
                            upgrades[base_id]['level'] = max(upgrades[base_id]['level'], needed_level)
                        else:
                            upgrades[base_id] = {'level': needed_level, 'count': multiplier}
                    
                    # Recursive: Collect upgrades for all components
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
                    # Base-card (none Fusion)
                    # Must on needed_level upgegraded werden
                    if needed_level > 1:
                        if base_id in upgrades:
                            upgrades[base_id]['count'] += multiplier
                            upgrades[base_id]['level'] = max(upgrades[base_id]['level'], needed_level)
                        else:
                            upgrades[base_id] = {'level': needed_level, 'count': multiplier}
                
                return upgrades
            
            # SP-Kosten calculate - INVENTAR-OPTIMIERT
            # Consider only the upgrades that REALLY must be done
            total_sp = 0
            
            # Recursive function to collect required upgrades WITH inventory check
            def calculate_actual_upgrade_costs(card_id, multiplier=1, depth=0):
                """Calculates SP costs considering inventory"""
                nonlocal total_sp
                
                info = card_data.get(card_id, {})
                if isinstance(info, dict):
                    base_id = info.get('base_id', card_id)
                    needed_level = info.get('level', 1)
                    rarity = info.get('rarity', 1)
                else:
                    return
                
                # Check ob in inventory
                owned = 0
                best_level = 1
                if str(base_id) in user_cards:
                    owned = int(user_cards[str(base_id)].get('num_owned', 0))
                    
                    # Find highest available level
                    for check_level in range(needed_level, 0, -1):
                        for cid, cinfo in card_data.items():
                            if isinstance(cinfo, dict):
                                if cinfo.get('base_id') == base_id and cinfo.get('level') == check_level:
                                    if str(cid) in user_cards and int(user_cards[str(cid)].get('num_owned', 0)) >= multiplier:
                                        best_level = check_level
                                        break
                        if best_level > 1:
                            break
                
                # Berechne Upgrade-Kosten from best_level to needed_level
                for lvl in range(best_level, needed_level):
                    key = (rarity, lvl)
                    if key in sp_costs:
                        total_sp += sp_costs[key] * multiplier
                
                # If fusion needed, recursive for components
                if base_id in recipes and owned < multiplier:
                    for res in recipes[base_id]:
                        calculate_actual_upgrade_costs(res['card_id'], res['number'] * multiplier, depth + 1)
            
            # Berechne SP for Zielkarte
            calculate_actual_upgrade_costs(base_target_id, 1)
            
            # Upgrade on Ziellevel
            if target_level > 1:
                target_info = card_data.get(base_target_id, {})
                if isinstance(target_info, dict):
                    rarity = target_info.get('rarity', 1)
                    for lvl in range(1, target_level):
                        key = (rarity, lvl)
                        if key in sp_costs:
                            total_sp += sp_costs[key]
            
            # Multipliziere with build_count
            if build_count > 1:
                total_sp = total_sp * build_count
            
            
            # Quick SP check
            if not self.init_data:
                self.initialize()
            
            user_sp = int(self.init_data['user_data'].get('salvage', 0))
            
            # Only show if SP might be issue
            if total_sp > 0 and user_sp < total_sp:
                print(f"\n⚠ Not enough SP: have {user_sp:,}, need {total_sp:,}")
                return True
            
            # ===== PHASE 2: AUTO-BUILD =====
            sp_before = user_sp
            
            print(f"\n🔨 Building {build_count}x {target_name}-{target_level}...")
            
            # Build each copy
            for copy_idx in range(build_count):
                if build_count > 1:
                    print(f"\n📦 Copy {copy_idx + 1}/{build_count}")
                
                # Execute build
                success = self._execute_build(
                    target_name=target_name,
                    target_level=target_level,
                    base_target_id=base_target_id,
                    card_data=card_data,
                    recipes=recipes,
                    sp_costs=sp_costs
                )
                
                if not success:
                    print(f"\n✗ Build failed at copy {copy_idx + 1}")
                    break
                
                # Reload inventory for next copy
                if copy_idx < build_count - 1:
                    self.initialize()
            
            # Get SP afterward
            self.initialize()
            sp_after = int(self.init_data['user_data'].get('salvage', 0))
            sp_used = sp_before - sp_after
            
            # Show simple summary
            if sp_used > 0:
                print(f"\n✅ Build complete - {sp_used:,} SP used")
            else:
                print(f"\n✅ Build complete")
            
            return True
            
        except Exception as e:
            print(f"✗ Error in _build_single_card_info: {e}")
            traceback.print_exc()
            return False
    
    def _find_best_card_in_inventory(self, base_id, target_level, card_data, used_cards=None):
        """
        PHASE 3: SMART INVENTORY
        
        Finds the best available version einer Card in inventory.
        Prefers higher levels to save SP.
        
        Args:
            base_id: Base-ID der Card (Level 1)
            target_level: Beneededtes Level
            card_data: Card info dictionary
            used_cards: Dict tracking wie viele Cardn already verwendet wasn {card_id: count}
        
        Returns:
            (card_id, current_level, sp_saved) tuple
            - card_id: ID der besten gefundenen Card
            - current_level: Level der gefundenen Card
            - sp_saved: Saved SP compared to level 1
        """
        if not self.init_data:
            self.initialize()
        
        if used_cards is None:
            used_cards = {}
        
        user_cards = self.init_data.get('user_cards', {})
        base_info = card_data.get(base_id, {})
        rarity = base_info.get('rarity', 0)
        
        # Collect all availableen Levels dieser card
        available_levels = []
        
        # Level 1 (Base) check
        if str(base_id) in user_cards:  # user_cards has string keys!
            owned = int(user_cards[str(base_id)].get('num_owned', 0))
            already_used = used_cards.get(base_id, 0)
            if owned > already_used:  # Still not all used
                available_levels.append((base_id, 1, 0))  # (card_id, level, sp_saved)
        
        # All Upgrade-Levels check (2 until target_level)
        for check_level in range(2, target_level + 1):
            for cid, info in card_data.items():
                if info.get('base_id') == base_id and info.get('level') == check_level:
                    # Check if in inventory AND still not used
                    if str(cid) in user_cards:  # user_cards has string keys!
                        owned = int(user_cards[str(cid)].get('num_owned', 0))
                        already_used = used_cards.get(cid, 0)
                        if owned > already_used:  # Still available
                            # Berechne gesavese SP
                            sp_saved = 0
                            for lvl in range(1, check_level):
                                key = (rarity, lvl)
                                if key in self.sp_costs:
                                    sp_saved += self.sp_costs[key]
                            
                            available_levels.append((cid, check_level, sp_saved))
                    break
        
        if not available_levels:
            # Nothing available - use Level 1 (will be built later)
            return (base_id, 1, 0)
        
        # Sortiere after Level (highests toerst) around max SP to sparen
        available_levels.sort(key=lambda x: x[1], reverse=True)
        
        return available_levels[0]
    
    def _execute_build(self, target_name, target_level, base_target_id, card_data, recipes, sp_costs):
        """
        Executes the complete build process for a card
        
        Returns: True wenn erfolgreich, False bei Error
        """
        try:
            print(f"\n⏳ Building {target_name}-{target_level}...")
            
            # Tracking for used cards
            used_cards = {}
            
            # PHASE 1: SMART INVENTORY - Check FIRST what we already have
            print(f"  → Checking inventory for existing versions...")
            base_id = base_target_id
            best_card_id, best_level, sp_saved = self._find_best_card_in_inventory(
                base_id, target_level, card_data, used_cards
            )
            
            # Determine starting point
            if best_level >= target_level:
                # We already have target level - can't upgrade further!
                # Look for LOWER level to build from (e.g., Level-1 instead of Level-6)
                print(f"  ℹ Found {target_name}-{best_level} in inventory (building additional copy)")
                
                lower_level_found = False
                for check_level in range(1, target_level):
                    for cid, info in card_data.items():
                        if info.get('base_id') == base_id and info.get('level') == check_level:
                            if str(cid) in self.init_data.get('user_cards', {}):
                                owned = int(self.init_data['user_cards'][str(cid)].get('num_owned', 0))
                                already_used = used_cards.get(cid, 0)
                                if owned > already_used:
                                    # Found lower level!
                                    print(f"  💡 Using {target_name}-{check_level} from inventory")
                                    best_card_id = cid
                                    best_level = check_level
                                    lower_level_found = True
                                    break
                    if lower_level_found:
                        break
                
                if not lower_level_found:
                    # No lower level - build from scratch
                    best_level = 0
            
            # Now proceed with the level we found (or 0 for from-scratch)
            if best_level > 0 and best_level < target_level:
                # Have a version to upgrade from
                current_id = best_card_id
                current_level = best_level
                # Mark as used
                if best_card_id not in used_cards:
                    used_cards[best_card_id] = 0
                used_cards[best_card_id] += 1
            
            else:
                # best_level == 0, need to build from scratch
                # PHASE 2: Build Level-1 Version (recursively if needed)
                if base_target_id in recipes:
                    print(f"  → Building {target_name}-1 (Fusion)")
                    
                    built_card_id = self._build_card_recursive(
                        base_target_id,
                        card_data,
                        recipes,
                        sp_costs,
                        used_cards
                    )
                    
                    if not built_card_id:
                        print(f"✗ Error while building {target_name}-1")
                        return False
                    
                    current_id = built_card_id
                    current_level = 1
                else:
                    # No Fusion recipe - card must already be in inventory
                    # (This should have been found by _find_best_card_in_inventory)
                    current_id = base_target_id
                    current_level = 1
            
            # PHASE 3: Upgrade to target level (if needed)
            if current_level < target_level:
                print(f"\n  → Upgrading {target_name}-{current_level} to {target_name}-{target_level}")
                
                while current_level < target_level:
                    # Upgrade by 1 level (silent)
                    result = self.api.call('upgradeCard', card_id=current_id)
                    
                    if not result or result.get('result') != True:
                        print(f"    ✗ Upgrade failed at level {current_level}!")
                        return False
                    
                    # Find next ID (upgraded version)
                    base_info = card_data.get(current_id, {})
                    base_id = base_info.get('base_id', current_id)
                    
                    # Search for upgrade_id for next level
                    next_level = current_level + 1
                    for cid, info in card_data.items():
                        if info.get('base_id') == base_id and info.get('level') == next_level:
                            current_id = cid
                            break
                    
                    current_level += 1
                    
                    # Rate limiting
                    time.sleep(0.3)
                
                print(f"    ✓ Upgrade complete")
            
            print(f"\n✅ {target_name}-{target_level} successfully built!")
            return True
            
        except Exception as e:
            print(f"✗ Error in _execute_build: {e}")
            traceback.print_exc()
            return False
    
    def _build_card_recursive(self, card_id, card_data, recipes, sp_costs, used_cards=None):
        """
        Builds a card recursively (inklusive aller Sub-Komponenten)
        
        Args:
            used_cards: Dict tracking verwendete Cardn {card_id: count}
        
        Returns: card_id der gebauten Card, oder None bei Error
        """
        try:
            if used_cards is None:
                used_cards = {}
            
            info = card_data.get(card_id, {'name': f'ID {card_id}', 'level': 1})
            card_name = info['name']
            card_level = info['level']
            
            # KRITISCH: Check ZUERST ob card already in inventory present ist
            if not self.init_data:
                self.initialize()
            
            user_cards = self.init_data.get('user_cards', {})
            
            # Check if this exact card is present AND still not used
            if str(card_id) in user_cards:  # user_cards has string keys
                owned = int(user_cards[str(card_id)].get('num_owned', 0))
                already_used = used_cards.get(card_id, 0)
                
                if owned > already_used:
                    # card is available - use it!
                    print(f"  💡 Using available {card_name}-{card_level} from inventory")
                    
                    # Markiere als verwendet
                    if card_id not in used_cards:
                        used_cards[card_id] = 0
                    used_cards[card_id] += 1
                    
                    return card_id
            
            # Check ob Rezept existiert
            if card_id not in recipes:
                # No Fusion - card must be in inventory (or is already built)
                return card_id
            
            # CRITICAL PROTECTION: Warn if trying to BUILD Neocyte Cores
            # (Using from inventory is OK, but building new ones should be avoided)
            base_id = info.get('base_id', card_id)
            if base_id in NEOCYTE_CORE_IDS:
                print(f"\n  ⚠ WARNING: Recipe requires Neocyte Core!")
                print(f"  ⚠ Building {card_name} would use Neocyte Cores")
                print(f"  ⚠ Consider using existing Vindicator Reactors from inventory instead")
            
            print(f"\n  🔧 Building {card_name}-{card_level} (Fusion)")
            
            # Get recipe
            recipe_resources = recipes[card_id]
            
            # Build/Upgrade all components
            for res in recipe_resources:
                res_id = res['card_id']
                res_count = res['number']
                res_info = card_data.get(res_id, {'name': f'ID {res_id}', 'level': 1})
                res_name = res_info['name']
                res_level = res_info['level']
                
                print(f"    → Required: {res_count}x {res_name}-{res_level}")
                
                # IMPORTANT: For each required card individually
                for copy_num in range(res_count):
                    # If component is an upgrade version, we must upgrade
                    if res_level > 1:
                        # Get Base-ID
                        base_id = res_info.get('base_id', res_id)
                        base_info = card_data.get(base_id, {})
                        base_name = base_info.get('name', res_name)
                        
                        # PHASE 1: SMART INVENTORY - Check FIRST what we have
                        best_card_id, best_level, sp_saved = self._find_best_card_in_inventory(
                            base_id, res_level, card_data, used_cards
                        )
                        
                        if sp_saved > 0 and copy_num == 0:  # Only display at first time
                            print(f"      💡 Using {base_name}-{best_level} from inventory (saves {sp_saved} SP per card)")
                        
                        # If we don't have even level 1, need to build it
                        if best_level == 1 and best_card_id == base_id:
                            # Check if base version has a recipe
                            if base_id in recipes:
                                # Build base version recursively
                                built_base = self._build_card_recursive(base_id, card_data, recipes, sp_costs, used_cards)
                                if not built_base:
                                    return None
                                # Re-check inventory after build
                                best_card_id, best_level, sp_saved = self._find_best_card_in_inventory(
                                    base_id, res_level, card_data, used_cards
                                )
                        
                        # Mark as used
                        if best_card_id not in used_cards:
                            used_cards[best_card_id] = 0
                        used_cards[best_card_id] += 1
                        
                        # Upgrade from best_level to res_level (if needed)
                        if best_level < res_level:
                            current_id = best_card_id
                            for lvl in range(best_level, res_level):
                                result = self.api.call('upgradeCard', card_id=current_id)
                                
                                if not result or result.get('result') != True:
                                    print(f"      ✗ Upgrade {base_name} failed at level {lvl}!")
                                    return None
                                
                                # Find next upgrade_id
                                for cid, cinfo in card_data.items():
                                    if cinfo.get('base_id') == base_id and cinfo.get('level') == lvl + 1:
                                        current_id = cid
                                        break
                                
                                time.sleep(0.2)
                    else:
                        # Level 1 - check if fusion needed
                        if res_id in recipes:
                            # Build recursively
                            built = self._build_card_recursive(res_id, card_data, recipes, sp_costs, used_cards)
                            if not built:
                                return None
            
            # All components ready - now fuse
            print(f"    🔗 Fusioniere → {card_name}-{card_level}")
            
            result = self.api.call('fuseCard', card_id=card_id)
            
            if not result or result.get('result') != True:
                print(f"    ✗ Fusion failed!")
                return None
            
            print(f"    ✓ {card_name}-{card_level} successful fusioniert!")
            
            time.sleep(0.3)
            
            return card_id
            
        except Exception as e:
            print(f"✗ Error in _build_card_recursive: {e}")
            traceback.print_exc()
            return None
    
    # ==================== DOMINION FUNKTIONEN ====================
    #
    # HAUPT-FUNKTION:
    #   build_dominion_autobuild() - Auto-Build with Reset-Support
    #
    # HELPER-FUNKTIONEN (intern verwendet):
    #   _calculate_fusion_path()   - BFS-pathberechnung
    #   _execute_fusion_path()     - Executes fusion path from
    #   _execute_simple_upgrade()  - Einfaches Upgrade (gleicher Tier)
    #   _calculate_upgrade_cost()  - Berechnet Shard-Kosten
    #
    # LEGACY-FUNKTIONEN (no longer in menu):
    #   reset_dominion()           - Matueller Reset
    #   upgrade_dominion()         - Matuelles Upgrade
    #   show_dominion_fusions()    - Zeigt availablee Fusionen
    #
    # ==============================================================
    
    def reset_dominion(self, dominion_card_id=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Resettet a Dominion zurück auf die Basis-Versionen
        Wird intern von build_dominion_autobuild() verwendet
        
        WICHTIG: Reset gibt zurück:
        - Alpha Dominion-2 (ID 50002) - NICHT Level 1!
        - Nexus Dominion-2 (ID 50239) - NICHT Level 1!
        - Alle verwendeten Materialien (Shards, Fusion-Cardn, etc.)
        
        Level 1 Versionen (50001, 50238) existieren nicht im Spiel!
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER new load around currente since to haben
            self.initialize()
            
            # Lade Card-since
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Could not load card data")
                return False
            
            # If no ID given, zeige availablee Dominions from Inventar
            if dominion_card_id is None:
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde all Dominions in inventory
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
                    print("✗ None Dominions in inventory found")
                    return False
                
                # Sortiere after Name
                available_dominions.sort(key=lambda x: x['name'])
                
                print("\n" + "="*50)
                print("AVAILABLE DOMINIONS")
                print("="*50)
                
                for idx, dom in enumerate(available_dominions, 1):
                    print(f"{idx}. {dom['name']}")
                
                print("="*50)
                
                # selection with Wiederholung at invalider Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer or ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Invalid selection: '{choice}'")
                            print(f"   Please select a number between 1 and {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Valid selection - exit loop
                        break
                    except ValueError:
                        print(f"✗ Invalid input: '{choice}'")
                        print("   Please enter a number")
                        continue  # Wiederhole Eingabe
                
                dominion_card_id = available_dominions[idx]['id']
            
            # Hole Dominion-Info
            dominion_info = card_data.get(dominion_card_id, {})
            dominion_name = dominion_info.get('name', f'ID {dominion_card_id}')
            dominion_level = dominion_info.get('level', 1)
            
            # Check ob es wirklich a Dominion ist
            if dominion_card_id not in DOMINION_IDS:
                print(f"✗ {dominion_name} (ID {dominion_card_id}) is no Dominion")
                return False
            
            # Check ob in inventory
            user_cards = self.init_data.get('user_cards', {})
            card_count = int(user_cards.get(str(dominion_card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Remove level suffix from name if present (name already contains "-X")
                display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
                print(f"✗ {display_name}-{dominion_level} not in inventory")
                return False
            
            # Remove Level-Suffix from Name for display
            display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
            
            print(f"\n🔄 Resettet {display_name}-{dominion_level}")
            
            # confirmation
            if not confirm_action(f"Wirklich {display_name}-{dominion_level} zurück auf Level 1 setzen?"):
                print("Canceled")
                return False
            
            # API Call: respecDominionCard
            print(f"⏳ Sende Reset-Anfrage...")
            result = self.api.call('respecDominionCard', card_id=dominion_card_id)
            
            if not result or result.get('result') != True:
                print(f"✗ Reset failed!")
                print(f"Response: {result}")
                return False
            
            # Get Base ID (Level 1 Version)
            base_id = dominion_info.get('base_id', dominion_card_id)
            base_info = card_data.get(base_id, {})
            base_name = base_info.get('name', dominion_name)
            
            print(f"✅ {dominion_name} was successfully reset!")
            
            # Show what was returned (if present)
            # Success - no details needed
            return True
            
        except Exception as e:
            print(f"✗ Error while Reset: {e}")
            traceback.print_exc()
            return False
    
    def upgrade_dominion(self, dominion_card_id=None, target_level=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Upgraded a Dominion auf a bestimmtes Level
        Wird intern von build_dominion_autobuild() verwendet
        
        Args:
            dominion_card_id: Die Card-ID des Dominions (optional, wird bei None abgefragt)
            target_level: Ziel-Level (optional, wird bei None abgefragt)
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER new load around currente since to haben
            self.initialize()
            
            # Lade Card-since
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Could not load card data")
                return False
            
            # If no ID given, zeige availablee Dominions from Inventar
            if dominion_card_id is None:
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde all Dominions in inventory
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
                    print("✗ None Dominions in inventory found")
                    return False
                
                # Sortiere after Name
                available_dominions.sort(key=lambda x: x['name'])
                
                print("\n" + "="*50)
                print("AVAILABLE DOMINIONS")
                print("="*50)
                
                for idx, dom in enumerate(available_dominions, 1):
                    print(f"{idx}. {dom['name']}")
                
                print("="*50)
                
                # selection with Wiederholung at invalider Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer or ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Invalid selection: '{choice}'")
                            print(f"   Please select a number between 1 and {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Valid selection - exit loop
                        break
                    except ValueError:
                        print(f"✗ Invalid input: '{choice}'")
                        print("   Please enter a number")
                        continue  # Wiederhole Eingabe
                
                dominion_card_id = available_dominions[idx]['id']
            
            # Hole Dominion-Info
            dominion_info = card_data.get(dominion_card_id, {})
            dominion_name = dominion_info.get('name', f'ID {dominion_card_id}')
            current_level = dominion_info.get('level', 1)
            base_id = dominion_info.get('base_id', dominion_card_id)
            
            # Check ob es wirklich a Dominion ist
            if dominion_card_id not in DOMINION_IDS:
                print(f"✗ {dominion_name} (ID {dominion_card_id}) is no Dominion")
                return False
            
            # Check ob in inventory
            user_cards = self.init_data.get('user_cards', {})
            card_count = int(user_cards.get(str(dominion_card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Remove level suffix from name if present (name already contains "-X")
                display_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
                print(f"✗ {display_name}-{current_level} not in inventory")
                return False
            
            # If no Ziel-Level given, frage
            if target_level is None:
                # Finde max Level for dieses Dominion
                max_level = current_level
                for cid, cinfo in card_data.items():
                    if cinfo.get('base_id') == base_id:
                        max_level = max(max_level, cinfo.get('level', 1))
                
                print(f"\n📊 {dominion_name} is current Level {current_level}")
                print(f"   Max Level: {max_level}")
                
                level_input = input_with_esc(f"\nZiel-Level (1-{max_level}, ESC=Cancel): ")
                if level_input is None:
                    return False
                
                try:
                    target_level = int(level_input)
                    if target_level < 1 or target_level > max_level:
                        print(f"✗ Level must be between 1 and {max_level} ")
                        return False
                except ValueError:
                    print("✗ Invalid input")
                    return False
            
            # Check if upgrade needed
            if target_level == current_level:
                print(f"ℹ {dominion_name} is already Level {current_level}")
                return True
            
            if target_level < current_level:
                print(f"⚠ {dominion_name} is already Level {current_level}, cannot be downgraded to {target_level} ")
                print(f"   Use reset_dominion() to reset back to level 1")
                return False
            
            # Berechne Upgrade-Kosten
            upgrades_needed = target_level - current_level
            
            # IMPORTANT: Dominions verwenden Dominion Shards (43452), not SP!
            # The cost depends on fusion level (which Alpha/Nexus levels were fused)
            
            # Bestimme Tier des Dominions for Upgrade-Kosten
            dominion_tier = get_dominion_tier(dominion_card_id)
            
            # Berechne Shard-Kosten
            total_shards = 0
            for lvl in range(current_level, target_level):
                next_lvl = lvl + 1
                if next_lvl in DOMINION_TIER_UPGRADE_COSTS[dominion_tier]:
                    total_shards += DOMINION_TIER_UPGRADE_COSTS[dominion_tier][next_lvl]
            
            # Hole currente Dominion Shards in inventory
            user_cards = self.init_data.get('user_cards', {})
            shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
            current_shards = int(shard_info.get('num_owned', 0))
            
            # Fusion Level Name for Ausgabe
            # Remove Level-Suffix from Name for display (name already contains "-X")
            base_name = dominion_name.rsplit('-', 1)[0] if '-' in dominion_name else dominion_name
            
            print(f"\n📊 Upgrade-Plan:")
            print(f"   From: {base_name}-{current_level}")
            print(f"   To:  {base_name}-{target_level}")
            print(f"   Upgrades: {upgrades_needed}")
            print(f"   Dominion Shards: {total_shards:,} required")
            print(f"   Available: {current_shards:,} Shards")
            
            if total_shards > current_shards:
                print(f"\n✗ Not enough Dominion Shards!")
                print(f"   Required: {total_shards:,}")
                print(f"   Available: {current_shards:,}")
                print(f"   Fehlen: {total_shards - current_shards:,}")
                return False
            
            # confirmation
            if not confirm_action(f"\nUpgrade {dominion_name} von Level {current_level} auf {target_level} ({total_shards:,} Shards)?"):
                print("Canceled")
                return False
            
            # Perform upgrade
            print(f"\n⏳ Upgrade startet...")
            
            current_id = dominion_card_id
            current_lvl = current_level
            
            for upgrade_step in range(upgrades_needed):
                # Upgrade around 1 Level
                result = self.api.call('upgradeCard', card_id=current_id)
                
                if not result or result.get('result') != True:
                    print(f"✗ Upgrade failed at Level {current_lvl}!")
                    print(f"Response: {result}")
                    return False
                
                # Find next ID (upgraded version)
                next_lvl = current_lvl + 1
                
                for cid, cinfo in card_data.items():
                    if cinfo.get('base_id') == base_id and cinfo.get('level') == next_lvl:
                        current_id = cid
                        break
                
                current_lvl = next_lvl
                print(f"  ✓ Level {current_lvl} erreicht")
                
                # Rate limiting
                time.sleep(0.3)
            
            print(f"\n✅ {dominion_name} what successful on Level {target_level} upgraded!")
            print(f"   Verwendete Dominion Shards: {total_shards:,}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error while Upgrade: {e}")
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
            
            # Hole Info over current
            curr_info = card_data.get(curr_id, {})
            curr_level = curr_info.get('level', 1)
            curr_base = curr_info.get('base_id', curr_id)
            curr_name = curr_info.get('name', f'ID {curr_id}')
            
            # Check: Sind wir am Ziel?
            if curr_base == target_base:
                # Finaler Upgrade tom Ziel-Level
                target_level = card_data.get(target_id, {}).get('level', 6)
                if curr_level < target_level:
                    # Finde die richtige ID for its Ziel-Level
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
            
            # option 1: Fusionen probieren (if possible)
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
            
            # option 2: Upgrade to Level 6 (if needed and still not fused)
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
        
        # No path gefanden
        return None
    
    def _calculate_upgrade_cost(self, from_id, to_id, card_data):
        """
        Berechnet Dominion Shard-Kosten für Upgrade
        
        Args:
            from_id: Currente Card-ID
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
            from_id: Currente Card-ID
            from_name: Currenter Name
            from_level: Currentes Level
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
            print(f"✓ Already am Ziel!")
            return True
        
        # Berechne Kosten
        total_shards = self._calculate_upgrade_cost(from_id, to_id, card_data)
        
        user_cards = self.init_data.get('user_cards', {})
        shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
        current_shards = int(shard_info.get('num_owned', 0))
        
        from_base = from_name.rsplit('-', 1)[0] if '-' in from_name else from_name
        to_base = to_name.rsplit('-', 1)[0] if '-' in to_name else to_name
        
        print(f"\n📊 Upgrade:")
        print(f"   From: {from_base}-{from_level}")
        print(f"   To:  {to_base}-{to_level}")
        print(f"   Dominion Shards: {total_shards:,}")
        print(f"   Available: {current_shards:,}")
        
        if total_shards > current_shards:
            print(f"\n✗ Not enough Dominion Shards!")
            return False
        
        if not confirm_action(f"\nUpgrade von {from_name} auf {to_name} ({total_shards:,} Shards)?"):
            print("Canceled")
            return False
        
        # Perform upgrade
        print(f"\n⏳ Upgrade in pergress...")
        
        current_id = from_id
        current_lvl = from_level
        base_id = card_data.get(from_id, {}).get('base_id', from_id)
        
        for _ in range(upgrades_needed):
            result = self.api.call('upgradeCard', card_id=current_id)
            
            if not result or result.get('result') != True:
                print(f"✗ Upgrade failed at Level {current_lvl}!")
                return False
            
            next_lvl = current_lvl + 1
            
            for cid, cinfo in card_data.items():
                if cinfo.get('base_id') == base_id and cinfo.get('level') == next_lvl:
                    current_id = cid
                    break
            
            current_lvl = next_lvl
            print(f"  ✓ Level {current_lvl}")
            time.sleep(0.3)
        
        print(f"\n✅ Successful on {to_name} upgraded!")
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
                # Perform upgrade
                from_id = step['from_id']
                from_level = step['from_level']
                to_level = step['to_level']
                base_id = card_data.get(from_id, {}).get('base_id', from_id)
                
                current_id = from_id
                current_lvl = from_level
                
                for _ in range(to_level - from_level):
                    result = self.api.call('upgradeCard', card_id=current_id)
                    
                    if not result or result.get('result') != True:
                        print(f"✗ Upgrade failed!")
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
                # Perform fusion
                # API: fuseCard with card_id = Ziel-Dominion ID
                result = self.api.call('fuseCard', card_id=step['to_id'])
                
                if not result or result.get('result') != True:
                    print(f"✗ Fusion failed!")
                    print(f"Response: {result}")
                    return False
                
                print(f"✓ FUSION: {step['from_name']} → {step['to_name']}")
                time.sleep(0.5)
        
        print(f"\n✅ Auto-Build successful abgeschlossen!")
        return True
    
    def build_dominion_autobuild(self, dominion_card_id=None, target_level=None):
        """
        Auto-Build: Baut automatisch a Ziel-Dominion
        
        Features:
        - Zeigt currenten Status (Alpha + Nexus)
        - Zeigt alle availableen Endstufen (Tier 4 Alpha, Tier 3 Nexus)
        - Berechnet automatisch Fusion-Pfad inkl. Upgrades
        - Führt Reset durch wenn no direkter Pfad möglich
        - Kompletter Auto-Build in einem Durchlauf
        
        Args:
            dominion_card_id: Die Card-ID des Ziel-Dominions (optional, zeigt Selection-Dialog)
            target_level: Ziel-Level (optional, Standard: 6)
        
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            # IMMER new load around currente since to haben (e.g. after reset)
            self.initialize()
            
            # Lade Card-since
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Could not load card data")
                return False
            
            user_cards = self.init_data.get("user_cards", {})
            
            # If no ID given, zeige availablee Dominions from Inventar
            # Zeige always selection-Dialog
            if True:
                
                # Finde AKTUELLE Dominions in inventory (pro branch gibt es only EINS!)
                current_dominions = []
                
                # Collect ALLE Dominions in inventory
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
                
                # Per branch: Show only its HIGHEST tier (there can only be one!)
                dominions_by_branch = {}
                for dom in inventory_dominions:
                    branch = dom['branch']
                    if branch not in dominions_by_branch or dom['tier'] > dominions_by_branch[branch]['tier']:
                        dominions_by_branch[branch] = dom
                
                current_dominions = list(dominions_by_branch.values())
                
                # Zeige currenten Status
                if current_dominions:
                    print("\n" + "="*70)
                    print("AKTUELLER STATUS")
                    print("="*70)
                    for dom in current_dominions:
                        print(f"{dom['branch'].upper()}: {dom['name']} (Tier {dom['tier']})")
                    print("="*70)
                
                # Collect HIGHEST tier final stages as target options
                # Alpha: Tier 4 | Nexus: Tier 3 (hat no Tier 4)
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
                    print("✗ None Endstufen-Dominions found")
                    return False
                
                # Sortiere after branch (Alpha toerst), sincetn after Name
                available_dominions.sort(key=lambda x: (x['branch'], x['name']))
                
                print("\n" + "="*60)
                print("AVAILABLE TARGET DOMINIONS (Endstufen)")
                print("="*60)
                
                for idx, dom in enumerate(available_dominions, 1):
                    branch_label = dom['branch'].upper()
                    tier_label = f"Tier {dom['tier']}"
                    print(f"{idx}. [{branch_label} {tier_label}] {dom['name']}")
                
                print("="*50)
                
                # selection with Wiederholung at invalider Eingabe
                while True:
                    choice = input_with_esc("\nWähle Dominion (Nummer or ESC): ")
                    if choice is None:
                        return False
                    
                    try:
                        idx = int(choice) - 1
                        if idx < 0 or idx >= len(available_dominions):
                            print(f"✗ Invalid selection: '{choice}'")
                            print(f"   Please select a number between 1 and {len(available_dominions)}")
                            continue  # Wiederhole Eingabe
                        
                        # Valid selection - exit loop
                        break
                    except ValueError:
                        print(f"✗ Invalid input: '{choice}'")
                        print("   Please enter a number")
                        continue  # Wiederhole Eingabe
                
                # Das ist its ZIEL-Dominion, not its currente!
                target_dominion = available_dominions[idx]
                target_card_id = target_dominion['id']
                target_branch = target_dominion['branch']
            
            # Hole ZIEL-Dominion Info
            target_info = card_data.get(target_card_id, {})
            target_name = target_info.get('name', f'ID {target_card_id}')
            target_level = target_info.get('level', 6)  # Should always 6 sein
            
            # Check ob es wirklich a Dominion ist
            if target_card_id not in DOMINION_IDS:
                print(f"✗ {target_name} is no Dominion")
                return False
            
            # Finde AKTUELLES Dominion im selben branch
            current_dominion = None
            for dom in current_dominions:
                if dom['branch'] == target_branch:
                    current_dominion = dom
                    break
            
            if not current_dominion:
                print(f"✗ No {target_branch.upper()} Dominion in inventory found!")
                print(f"   Du brauchst a {target_branch.upper()} Dominion to {target_name} to build.")
                return False
            
            current_card_id = current_dominion['id']
            current_info = card_data.get(current_card_id, {})
            current_name = current_info.get('name', f'ID {current_card_id}')
            current_level = current_info.get('level', 1)
            current_tier = current_dominion['tier']
            current_base_id = current_info.get('base_id', current_card_id)
            
            target_tier = target_dominion['tier']
            target_base_id = target_info.get('base_id', target_card_id)
            
            # Check ob already am Ziel (gleiche base_id = gleiches Dominion)
            if current_base_id == target_base_id:
                # Gleiche base_id, only Level-Unterschied possible
                if current_level >= target_level:
                    print(f"✓ Du have already {target_name}!")
                    return True
            
            # If no Ziel-Level given, setze es on 6 (Endstufe)
            if target_level is None:
                target_level = 6
            
            print("\n📋 AUTO-BUILD PLAN")
            print("="*70)
            
            print(f"\n📊 Status:")
            print(f"   Current: {current_name} (Tier {current_tier})")
            print(f"   Ziel:    {target_name} (Tier {target_tier})")
            
            # If gleicher Tier UND gleiches Dominion (base_id), only upgraden
            if current_tier == target_tier and current_base_id == target_base_id:
                return self._execute_simple_upgrade(
                    current_card_id, current_name, current_level,
                    target_card_id, target_name, target_level,
                    current_tier, card_data
                )
            
            # Berechne Fusion-path
            fusion_path = self._calculate_fusion_path(current_card_id, target_card_id, card_data)
            
            reset_performed = False  # Track if reset was performed
            
            if not fusion_path:
                # No direkter path possible
                print(f"\n⚠️  No direct path found!")
                print(f"   From {current_name} to {target_name} is not directly possible.")
                print(f"\n💡 Solution: Reset to Tier 1, then build to target")
                
                # Confirm reset
                if not confirm_action(f"\n{current_name} zurücksetzen und dann {target_name} ?"):
                    print("Canceled")
                    return False
                
                reset_performed = True
                
                # STEP 1: Perform reset
                print(f"\n🔄 Schritt 1/2: Reset {current_name}...")
                reset_result = self.api.call('respecDominionCard', card_id=current_card_id)
                
                if not reset_result or reset_result.get('result') != True:
                    print(f"✗ Reset failed!")
                    print(f"Response: {reset_result}")
                    return False
                
                print(f"✓ Reset successful!")
                time.sleep(0.5)
                
                # Reload since after reset
                self.initialize()
                user_cards = self.init_data.get('user_cards', {})
                
                # Finde newes currentes Dominion (sollte Tier 1 sein)
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
                    print(f"✗ Could not find Dominion after reset!")
                    return False
                
                new_current_info = card_data.get(new_current, {})
                new_current_name = new_current_info.get('name', f'ID {new_current}')
                
                print(f"   Neuer Status: {new_current_name}")
                
                # SCHRITT 2: Berechne newen path
                print(f"\n🔨 Schritt 2/2: Building {target_name}...")
                fusion_path = self._calculate_fusion_path(new_current, target_card_id, card_data)
                
                if not fusion_path:
                    print(f"\n❌ Even after reset no path possible!")
                    print(f"   This should not happen - please check.")
                    return False
                
                # Upsincete current for die weitere Verarattung
                current_card_id = new_current
                current_name = new_current_name
                current_level = new_current_info.get('level', 1)
                current_tier = get_dominion_tier(new_current)
            
            # Zeige path
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
            
            # Hole currente Dominion Shards
            user_cards = self.init_data.get('user_cards', {})
            shard_info = user_cards.get(str(DOMINION_SHARD_ID), {})
            current_shards = int(shard_info.get('num_owned', 0))
            
            print(f"\n💎 Dominion Shards:")
            print(f"   Required:  {total_shards:,}")
            print(f"   Available: {current_shards:,}")
            
            if total_shards > current_shards:
                print(f"   ✗ Fehlen: {total_shards - current_shards:,}")
                return False
            else:
                print(f"   ✓ Ausreichend!")
            
            # confirmation - only if NO reset was performed
            if not reset_performed:
                if not confirm_action(f"\nAuto-Build von {current_name} zu {target_name} starten ({total_shards:,} Shards)?"):
                    print("Canceled")
                    return False
            
            # Execute path from
            return self._execute_fusion_path(fusion_path, card_data)
            
        except Exception as e:
            print(f"✗ Error while Upgrade: {e}")
            traceback.print_exc()
            return False
    
    def show_dominion_fusions(self, card_id=None):
        """
        [LEGACY FUNCTION - Nicht mehr im Menü]
        Zeigt availablee Dominion Fusionen für eine Card
        Wird für Debugging/Information verwendet
        
        Args:
            card_id: ID der Quell-Card (optional)
        """
        try:
            if not self.init_data:
                self.initialize()
            
            user_cards = self.init_data.get('user_cards', {})
            
            # If no ID given, show all dominions that can be fused
            if card_id is None:
                print("\n" + "="*60)
                print("AVAILABLE DOMINION FUSIONS")
                print("="*60)
                
                fusion_options = []
                
                for source_id in DOMINION_FUSIONS.keys():
                    # Check ob card in inventory
                    card_count = int(user_cards.get(str(source_id), {}).get('num_owned', 0))
                    
                    if card_count > 0:
                        # Hole cards-Info
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
                    print("✗ None Dominions with Fusion-Option found")
                    return
                
                # Sortiere after branch and Tier
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
                    print(f"  Tier {opt['tier']} → FUSION to Tier {opt['tier'] + 1 if opt['tier'] < 4 else opt['tier']} ({fusion_cost} Shards):")
                    
                    for result_id, result_name, shards in DOMINION_FUSIONS[opt['id']]:
                        # Check ob genug Shards
                        shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                        status = "✓" if shard_count >= shards else "✗"
                        print(f"    {status} {result_name} ({shards} Shards)")
                
                # Zeige availablee Shards
                shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                print(f"\nAvailable dominion shards: {shard_count:,}")
                
                print("\n" + "="*60)
                print("WICHTIG:")
                print("- Tier transitions use FUSION (fuseCard)")
                print("- Innerhalb eines Tiers verwenden UPGRADE (upgradeCard)")
                print("="*60)
                return
            
            # Zeige Fusionen for spezifische card
            if card_id not in DOMINION_FUSIONS:
                print(f"✗ None Fusionen available for Card {card_id}")
                return
            
            # Lade Card-since
            card_data = self._load_card_data()
            if not card_data:
                print("✗ Could not load card data")
                return
            
            card_info = card_data.get(card_id, {})
            card_name = card_info.get('name', f'Card {card_id}')
            card_level = card_info.get('level', '?')
            
            # Check Inventar
            card_count = int(user_cards.get(str(card_id), {}).get('num_owned', 0))
            
            if card_count == 0:
                # Remove level suffix from name if present (name already contains "-X")
                display_name = card_name.rsplit('-', 1)[0] if '-' in card_name else card_name
                print(f"✗ {display_name}-{card_level} not in inventory")
                return
            
            # Zeige availablee Fusionen
            print(f"\n{card_name}-{card_level} (ID: {card_id})")
            print(f"Available: {card_count}x")
            print("\nKann fusioniert will be to:")
            
            for result_id, result_name, shards in DOMINION_FUSIONS[card_id]:
                # Check ob genug Shards
                shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
                
                status = "✓" if shard_count >= shards else "✗"
                print(f"  {status} {result_name} ({shards} Shards)")
            
            # Zeige availablee Shards
            shard_count = int(user_cards.get(str(DOMINION_SHARD_ID), {}).get('num_owned', 0))
            print(f"\nAvailable dominion shards: {shard_count:,}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            traceback.print_exc()


# ==================== HELPER FUNKTIONEN ====================

def confirm_action(prompt):
    """
    Fragt Benutzer um Bestätigung mit Enter/ESC
    
    Args:
        prompt: Die anzuzeigende Frage
    
    Returns:
        True if Enter pressed (YES), False if ESC or q (NO)
    """
    import sys
    
    print(f"{prompt}")
    print("  [Enter] = YES  |  [ESC/q] = NO")
    print("  ", end='', flush=True)
    
    # Windows support
    if os.name == 'nt':
        import msvcrt
        while True:
            key = msvcrt.getch()
            if key == b'\r':  # Enter
                print("✓ YES")
                return True
            elif key == b'\x1b' or key == b'q':  # ESC or q
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
                    print("✓ YES")
                    return True
                elif ch == '\x1b' or ch == 'q':  # ESC or q
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
        "kong_name": "MusterPlayer",
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
    
    print("\n📋 OLD FORMAT (STILL SUPPORTED):")
    print("-"*80)
    print("""
{
  "user_id": "1234567",
  "password": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "kong_id": "9876543",
  "kong_token": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5",
  "kong_name": "MusterPlayer"
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
    
    print("\n🔧 CONVERSION FROM POST-DATA:")
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

2. Füge sie in die Template-Vorlage a (oben)

3. Speichere als: settings_DEINNAME.json
""")
    
    print("\n💡 BEISPIEL-KONVERTIERUNG:")
    print("-"*80)
    print("""
POST-Data:
  password=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6&user_id=1234567&
  syncode=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6&
  kong_id=9876543&kong_token=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5&
  kong_name=MusterPlayer

Wird zu Settings:
  "user_id": "1234567",
  "password": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "syncode": "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6",
  "kong_id": "9876543",
  "kong_token": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4z3y2x1w0v9u8t7s6r5",
  "kong_name": "MusterPlayer"
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
    input("\n[ENTER] zum Continue...")


def input_with_esc(prompt, allow_empty=False):
    """
    Input-Funktion mit ESC-Support zum Abbrechen
    
    Args:
        prompt: Der anzuzeigende Prompt
        allow_empty: Wenn True, ist leere Eingabe erlaubt
    
    Returns:
        Eingabe-String oder None wenn ESC gedrückt was
    """
    print(f"{prompt}", end='', flush=True)
    
    # Windows support
    if os.name == 'nt':
        import msvcrt
        result = []
        while True:
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC
                print("\n✗ Canceled")
                return None
            elif key == b'\r':  # Enter
                print()
                text = ''.join(result)
                if not text and not allow_empty:
                    print("✗ Empty input not allowed")
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
        # Unix/Linux/Mac - verwende normale input() with readline
        import readline
        try:
            result = input()
            if not result and not allow_empty:
                print("✗ Empty input not allowed")
                return input_with_esc(prompt, allow_empty)
            return result
        except KeyboardInterrupt:
            print("\n✗ Canceled")
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
    print("\nInsert API data (JSON or URL-encoded POST-Body)")
    print("e.g. from Browser DevTools → Network → Request Payload\n")
    
    # Single-line Input
    full_text = input("Insert data and press Enter: ").strip()
    
    if not full_text:
        print("✗ Empty input")
        return
    
    # Initialisiere all Felder
    user_id = None
    password = None
    syncode = None
    kong_id = None
    kong_token = None
    kong_name = None
    
    # FIXED VALUES - These are ALWAYS set to these values
    # DO NOT change these values even if different values come from input!
    unity = "Unity5_4_2"
    client_version = "80"
    device_type = "Firefox 147.0"
    os_version = "Windows 10"
    platform = "Web"
    
    # Try toerst URL-encoded Format (typisch for API POST-Body)
    if '=' in full_text and '&' in full_text:
        print("\n⏳ Parse URL-encoded Format...")
        from urllib.parse import parse_qs, unquote
        
        # Remove line breaks
        full_text = full_text.replace('\n', '').replace('\r', '')
        
        # Parse als Query-String
        params = parse_qs(full_text)
        
        # Extract values (parse_qs returns lists)
        user_id = params.get('user_id', [None])[0]
        password = params.get('password', [None])[0]
        syncode = params.get('syncode', [None])[0]
        kong_id = params.get('kong_id', [None])[0]
        kong_token = params.get('kong_token', [None])[0]
        kong_name = params.get('kong_name', [None])[0]
        # NOTE: unity, client_version, device_type, os_version, platform are FIXED
        # and will NOT be extracted from input!
        
        if kong_name:
            kong_name = unquote(kong_name)
        if device_type:
            device_type = unquote(device_type)
    
    # If URL-encoded not erfolgreich, versuche JSON
    if not all([user_id, password, kong_id, kong_token]):
        try:
            print("\n⏳ Parse JSON Format...")
            data = json.loads(full_text)
            
            # Extract from verschiedenen possibleen Strukturen
            if 'request' in data:
                request = data['request']
                user_id = request.get('user_id')
                password = request.get('password')
                syncode = request.get('syncode')
                kong_id = request.get('kong_id')
                kong_token = request.get('kong_token')
                kong_name = request.get('kong_name')
                # NOTE: unity, client_version, device_type, os_version, platform are FIXED
            elif 'request_data' in data:
                request_data = data['request_data']
                user_id = request_data.get('user_id')
                password = request_data.get('password')
                syncode = request_data.get('syncode')
                kong_id = request_data.get('kong_id')
                kong_token = request_data.get('kong_token')
                kong_name = request_data.get('kong_name')
                # NOTE: unity, client_version, device_type, os_version, platform are FIXED
            else:
                user_id = data.get('user_id')
                password = data.get('password')
                syncode = data.get('syncode')
                kong_id = data.get('kong_id')
                kong_token = data.get('kong_token')
                kong_name = data.get('kong_name')
                # NOTE: unity, client_version, device_type, os_version, platform are FIXED
        except json.JSONDecodeError:
            pass
    
    # Validiere requirede Felder
    if not all([user_id, password, kong_id, kong_token]):
        print("\n✗ Fehlende requirede Felder!")
        print(f"   user_id:    {user_id or '❌ FEHLT'}")
        print(f"   password:   {password or '❌ FEHLT'}")
        print(f"   syncode:    {syncode or '⚠️  MISSING (optional but recommended)'}")
        print(f"   kong_id:    {kong_id or '❌ FEHLT'}")
        print(f"   kong_token: {kong_token or '❌ FEHLT'}")
        print(f"   kong_name:  {kong_name or '(optional)'}")
        print("\nTip: copyre den kompletten POST-Body from dem Browser DevTools:")
        print("      Network → Request → Payload (view source)")
        return
    
    # Frage after filenamen
    default_name = kong_name.lower() if kong_name else "user"
    name_input = input(f"\nDateiname for settings_<n>.json (leer={default_name}): ").strip()
    name = name_input if name_input else default_name
    
    # Erstelle Settings-Dict im newen Format
    # NOTE: unity, client_version, device_type, os_version, platform are FIXED!
    settings = {
        "request_data": {
            "user_id": user_id,
            "password": password,
            "syncode": syncode or "0",
            "kong_id": kong_id,
            "kong_token": kong_token,
            "kong_name": kong_name or "",
            "_comment": "=== FIXED VALUES - DO NOT CHANGE ===",
            "unity": unity,
            "client_version": client_version,
            "device_type": device_type,
            "os_version": os_version,
            "platform": platform
        },
        "url": "mobile.tyrantonline.com",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    
    # Speichere file
    filename = f"settings_{name}.json"
    filepath = os.path.join(SCRIPT_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"\n✓ Settings saved: {filepath}\n")
    print(json.dumps(settings, indent=2))
    print(f"\n{'='*80}")
    print("ℹ️  NOTE: Fixed values were automatically set:")
    print(f"   unity: {unity}")
    print(f"   client_version: {client_version}")
    print(f"   device_type: {device_type}")
    print(f"   os_version: {os_version}")
    print(f"   platform: {platform}")
    print(f"\n   These values should NOT be changed!")
    print(f"{'='*80}")







# ==================== INTERAKTIVES MENU ====================

def interactive_menu():
    """Interaktives Hauptmenü"""
    
    # Try to set console window size
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Set window size: width=120, height=40
            kernel32.SetConsoleScreenBufferSize(kernel32.GetStdHandle(-11), 
                                                ctypes.wintypes._COORD(120, 9999))
            # Set sichtbaren Bereich
            kernel32.SetConsoleWindowInfo(kernel32.GetStdHandle(-11), True,
                                         ctypes.byref(ctypes.wintypes.SMALL_RECT(0, 0, 119, 39)))
        else:  # Linux/Mac
            # Funktioneverrt only in matchen Terminals
            print('\033[8;40;120t')  # 40 Zeilen, 120 Spolden
    except Exception:
        pass  # Ignoriere error, if es not funktioneverrt
    
    print("="*50)
    print("TYRANT UNLEASHED API COMMANDER")
    print("Standalone Version (without tyrant-Modul)")
    print("="*50)
    
    # Check ob im "since" folder
    current_dir = os.path.basename(SCRIPT_DIR)
    if current_dir.lower() != "data":
        print("\n" + "⚠"*50)
        print("WARNING: Script not running im 'data' folder!")
        print("⚠"*50)
        print(f"\nCurrent directory: {SCRIPT_DIR}")
        print(f"folder name: {current_dir}")
        print("\n" + "─"*50)
        print("RECOMMENDATION: Start the script from a 'data' folder")
        print("─"*50)
        print("\nReasons:")
        print("  • Card-XMLs (cards_section_1.xml until cards_section_21.xml)")
        print("    will be for following functions required:")
        print("    - Export Inventory (ownedcards.txt)")
        print("    - Salvage Base Epics")
        print("    - display card names (instead of only IDs)")
        print("\n  • If XMLs are missing, the script attempts automatic")
        print("    download - this takes longer and requires Internet!")
        print("\n  • In 'data' folder exports are aso saved:")
        print("    - ownedcards.txt")
        print("    - currentdecks.txt")
        print("    - guild_decks.txt")
        print("    - JSON exports")
        print("\n" + "─"*50)
        print("Optimal folder structure:")
        print("─"*50)
        print("  MyFolder/")
        print("  └── data/")
        print("      ├── tyrant_api_commander_standalone.py  ← The script")
        print("      ├── settings_main.json                  ← Your settings")
        print("      ├── cards_section_1.xml                 ← Card-Data")
        print("      ├── cards_section_2.xml")
        print("      ├── ... (until cards_section_21.xml)")
        print("      └── (Outputs will be hier created)")
        print("\n" + "─"*50)
        
        # Frage ob fortfahren
        if not confirm_action("\nContinue anyway?"):
            print("\nCanceled. Please start the script from a 'data' folder.")
            print("\nTip: Create a 'data' folder and move")
            print("      the script + settings_*.json + XMLs there.")
            return
        
        print("\n" + "="*50)
        print("Fahre fort...")
        print("="*50)
    else:
        print(f"\n✓ Script running in 'data' folder: {SCRIPT_DIR}")
    
    # configuration
    print(f"\nSkript-directory: {SCRIPT_DIR}")
    
    # Suche after settings_*.json fileen
    import glob
    settings_files = glob.glob(os.path.join(SCRIPT_DIR, "settings_*.json"))
    
    # Filtere TEMPLATE from
    settings_files = [f for f in settings_files if not os.path.basename(f).startswith("settings_TEMPLATE")]
    
    if not settings_files:
        print("\n" + "="*50)
        print("⚠ NO SETTINGS FILES FOUND!")
        print("="*50)
        print(f"\nSearched in: {SCRIPT_DIR}")
        print("\nYou have two options:")
        print("  1. Create settings manually (see option 999 below)")
        print("  2. Generate settings from API response (option 998)")
        print("\n" + "="*50)
    
    # Zeige availablee Settings als naroundmerierte list
    if settings_files:
        print("\nAvailable settings files:")
        print("─"*50)
        
        settings_map = {}
        for idx, filepath in enumerate(sorted(settings_files), 1):
            basename = os.path.basename(filepath)
            name_part = basename.replace("settings_", "").replace(".json", "")
            settings_map[str(idx)] = filepath
            print(f"{idx}. {name_part} ({basename})")
        
        print("─"*50)
    else:
        # Ka Settings present - zeige only Generator-optionen
        settings_map = {}
        print("\nNo settings files available yet.")
        print("─"*50)
    
    print("998. Settings Generator (from API-Response)")
    print("999. Settings-Help (File format & conversion)")
    print("─"*50)
    
    # selection with Wiederholung at invalider Eingabe
    while True:
        if settings_files:
            choice = input(f"\nSelect settings (1-{len(settings_files)}, 998 or 999): ").strip()
        else:
            choice = input(f"\nSelect option (998 or 999): ").strip()
        
        # Settings Generator
        if choice == "998":
            generate_settings_from_response()
            print("\n⏳ Starte script again to use new settings...")
            import sys
            import time
            time.sleep(2)
            # Starte Script new
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return
        
        # Settings-Hilfe
        if choice == "999":
            show_settings_help()
            # After help back to selection
            return interactive_menu()
        
        # Check ob valide Settings-Naroundmer
        if choice in settings_map:
            break  # Valid selection, exit loop
        
        # Unvalide Eingabe
        print(f"✗ Invalid selection: '{choice}'")
        if settings_files:
            print(f"   Please select a number between 1 and {len(settings_files)}, or 998/999")
        else:
            print(f"   Please select 998 (Settings Generator) or 999 (Help)")
    
    # If we arrive here, choice is valid and a settings file was selected
    # (998 and 999 return earlier, so we arrive here only with valider Settings-Naroundmer at)
    
    if not settings_map:
        # Should never passieren, but Sicherheitscheck
        print("\n✗ ERROR: No settings file selected!")
        return
    
    settings_path = settings_map[choice]
    settings_name = os.path.basename(settings_path).replace("settings_", "").replace(".json", "")
    
    print(f"✓ Loading Settings: {settings_name}")
    
    commander = TyrantCommander(settings_path)
    
    if not commander.initialize(verbose=True):  # Nur atm firstn Mal verbose
        print("Abbruch wegen Initialisierungsfehler")
        return
    
    # Auto-Check Daily Bonus (only once atm Start)
    commander.auto_claim_daily_bonus()
    
    while True:
        print("\n" + "="*50)
        print("MAIN MENU")
        print("="*50)
        print("1.  Player Info")
        print("2.  Update XML Files")
        print("3.  Update Deck (Edit slot + Set Attack/Defense)")
        print("4.  Guild members with Rating")
        print("5.  Export Inventory (ownedcards.txt + currentdecks.txt)")
        print("6.  Send Guild Message")
        print("7.  Claim Rewards")
        print("8.  Export Guild Decks")
        print("="*50)
        print("── SHOP & SALVAGE ──")
        print("9.  Buy Packages")
        print("10. Salvage All Commons")
        print("11. Salvage All Rares")
        print("12. Salvage Base Epics (keep X)")
        print("13. Workflow: Buy + Commons + Rares + Salvage Base Epics")
        print("="*50)
        print("── BUYBACK ──")
        print("14. Buy Back Card (WIP)")
        print("="*50)
        print("── INVENTORY ──")
        print("15. Build Card (Fusion Recipe & SP-Costs)")
        print("="*50)
        print("── DOMINION ──")
        print("16. Build Dominion (Auto-Build) ⭐")
        print("="*50)
        print("0.  Exit")
        print("─"*50)
        print("998. Settings Generator (Create settings.json)")
        print("="*50)
        
        choice = input("\nSelect an option: ").strip()
        
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
            message = input("Message enter: ").strip()
            commander.send_guild_message(message)
        
        elif choice == "7":
            commander.claim_rewards()
        
        elif choice == "8":
            filename = input_with_esc("Dateiname (leer='guild_decks', ESC=Cancel): ")
            if filename is None:
                continue
            
            filename = filename.strip()
            if not filename:
                filename = 'guild_decks'
            # Stelle sicher that .txt Endung present ist
            if not filename.endswith('.txt'):
                filename = filename + '.txt'
            # Verwende currentes directory (SCRIPT_DIR)
            full_path = os.path.join(SCRIPT_DIR, filename)
            commander.export_guild_decks_simple(full_path)
        
        elif choice == "9":
            try:
                n_input = input_with_esc("Number of packages (ESC=Cancel): ")
                if n_input is None:
                    continue
                n = int(n_input)
                commander.buy_packs(n)
            except ValueError:
                print("✗ Invalid number")

        elif choice == "10":
            commander.salvage_all_commons()

        elif choice == "11":
            commander.salvage_all_rares()

        elif choice == "12":
            # Base Epics salvagen (beholde X)
            try:
                keep_input = input_with_esc("Number of Base Epics to keep per card (leer=20, ESC=Cancel): ", allow_empty=True)
                if keep_input is None:
                    continue
                
                # Leere Eingabe = Statsincerd 20
                if not keep_input or keep_input.strip() == "":
                    keep = 20
                    print(f"✓ Verwende Standard: {keep}")
                else:
                    keep = int(keep_input)
                
                commander.salvage_base_epics_keep_x(keep)
            except ValueError:
                print("✗ Invalid number")

        elif choice == "13":
            # Workflow: Konen + Commons + Rares + Base Epics salvagen
            try:
                # Berechne maximale Paketatzahl
                max_packs, free_slots = commander.calculate_max_packs()
                
                print(f"\nFreie cardsslots: {free_slots}")
                print(f"Berechnete max. Packages: {max_packs} ({free_slots} / 20 = {free_slots/20:.1f})")
                
                pack_input = input_with_esc(f"Number of packages (leer={max_packs}, ESC=Cancel): ", allow_empty=True)
                if pack_input is None:
                    continue
                
                pack_input = pack_input.strip()
                
                # Leere Eingabe = automatisch berechnetes Maximaround
                if not pack_input:
                    n = max_packs
                    print(f"✓ Verwende berechnetes Maximum: {n} Packages")
                else:
                    n = int(pack_input)
                
                # Frage after keep-value for Base Epics
                keep_input = input_with_esc("Number of Base Epics keep per card (leer=20, ESC=Cancel): ", allow_empty=True)
                if keep_input is None:
                    continue
                
                keep_input = keep_input.strip()
                if not keep_input:
                    keep = 20
                    print(f"✓ Verwende Standard: {keep}")
                else:
                    keep = int(keep_input)
                
                if n <= 0:
                    print("✗ Count must be greater than 0")
                elif n > max_packs:
                    print(f"⚠ Warning: {n} Packages exceeds calculated maximum of {max_packs}")
                    print(f"   This would require {n * 20} slots, but only {free_slots} are free")
                    if confirm_action(f"Trotzdem {n} Pakete buyingn + Commons + Rares + Base Epics salvagen?"):
                        commander.shop_salvage_workflow(n, salvage_base_epics=True, keep_base_epics=keep)
                    else:
                        print("Canceled")
                else:
                    if confirm_action(f"{n} Pakete buyingn + Commons + Rares + Base Epics (behalte {keep}) salvagen?"):
                        commander.shop_salvage_workflow(n, salvage_base_epics=True, keep_base_epics=keep)
                    else:
                        print("Canceled")
            except ValueError:
                print("✗ Invalid number")

        elif choice == "15":
            commander.build_card()

        elif choice == "16":
            # Dominion Auto-Build
            commander.build_dominion_autobuild()

        elif choice == "14":
            # Buy back individual card
            try:
                card_input = input_with_esc("Card name or ID (ESC=Cancel): ")
                if card_input is None:
                    continue
                
                card_input = card_input.strip()
                if not card_input:
                    print("✗ Empty input")
                    continue
                
                # Check ob Eingabe ra Zahl ist (ID) or Name
                is_id = card_input.isdigit()
                
                # Hole Buyback-Info
                buyback_info = commander.get_buyback_info()
                
                if is_id:
                    # ID-Suche
                    card_id = int(card_input)
                    if str(card_id) not in buyback_info:
                        print(f"✗ card {card_id} is not in Buyback store")
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
                print(f"Available: {info['number']}x")
                print(f"Costs: {info['cost_per_card']} SP/card")
                print(f"Total: {info['total_cost']} SP for all")
                
                qty_input = input_with_esc(f"Anzahl (leer={info['number']}, ESC=Cancel): ", allow_empty=True)
                if qty_input is None:
                    continue
                
                qty_input = qty_input.strip()
                if not qty_input:
                    quantity = 0  # 0 = all
                else:
                    quantity = int(qty_input)
                
                commander.buyback_card(card_id, quantity)
                    
            except ValueError:
                print("✗ Invalid input")

        elif choice == "0":
            print("\nGoodbye!")
            break

        else:
            print("✗ Invalid option")


# ==================== HAUPTPROGRAMM ====================

if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
        print("Exiting...")
        sys.exit(0)
    except Exception as e:
        print("\n" + "="*70)
        print("FATAL ERROR - Script crashed unexpectedly")
        print("="*70)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print(f"\nFull Traceback:")
        print("-"*70)
        traceback.print_exc()
        print("-"*70)
        
        print("\nDEBUG INFORMATION:")
        print(f"  Python Version: {sys.version}")
        print(f"  Platform: {sys.platform}")
        print(f"  Current Directory: {os.getcwd()}")
        print(f"  Script Location: {os.path.abspath(__file__)}")
        
        print("\nPlease report this error with the above information.")
        print("="*70)
        
        # On Windows, keep window open
        if sys.platform == 'win32':
            input("\nPress Enter to exit...")
        
        sys.exit(1)

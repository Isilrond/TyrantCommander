"""
find_missing_assets.py
----------------------
Scans cards_section_*.xml and checks which assets are missing:
  1. Bundle sprites not extracted to --sprites folder
  2. Direct image references (e.g. crate.jpg) with no bundle

Usage:
    py find_missing_assets.py --xml-dir . --sprites sprites --probe

    --xml-dir   Folder with cards_section_*.xml (default: current dir)
    --sprites   Folder with extracted PNGs (default: sprites)
    --probe     Try to find direct image URLs on CDN/server
    --download  Download found direct images into --sprites folder
"""

import sys
import urllib.request
import urllib.error
import time
from pathlib import Path
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Candidate base URLs for direct image probing
IMAGE_BASE_URLS = [
    "https://raw.githubusercontent.com/purei/tyrant-card-builder/b8977fc8934c438cd66ba9c18142cea4c86ae470/images/TU/",
]

def scan_xmls(xml_dir):
    """
    Returns:
        bundle_sprites: {picture_name: {bundle_id, card_ids, card_names}}
        direct_images:  {picture_name: {card_ids, card_names}}  (no asset_bundle)
    """
    bundle_sprites = {}
    direct_images  = {}

    files = sorted(Path(xml_dir).glob("cards_section_*.xml"))
    if not files:
        print(f"ERROR: No cards_section_*.xml found in '{xml_dir}'")
        sys.exit(1)

    print(f"Scanning {len(files)} XML files...")
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except Exception as e:
            print(f"  [WARN] {f.name}: {e}")
            continue

        for unit in root.findall(".//unit"):
            card_id   = unit.findtext("id", "?")
            card_name = unit.findtext("name") or unit.findtext("n", "?")
            ab        = unit.findtext("asset_bundle", "").strip()

            # Collect ALL picture tags: base level + every upgrade level
            all_pictures = []
            base_pic = unit.findtext("picture", "").strip()
            if base_pic:
                all_pictures.append(base_pic)
            for upg in unit.findall("upgrade"):
                upg_pic = upg.findtext("picture", "").strip()
                if upg_pic:
                    all_pictures.append(upg_pic)

            for picture in all_pictures:
                if ab and ab.isdigit():
                    # Sprite lives inside a bundle
                    if picture not in bundle_sprites:
                        bundle_sprites[picture] = {"bundle_id": int(ab), "cards": []}
                    bundle_sprites[picture]["cards"].append((card_id, card_name))
                else:
                    # Direct image reference (no bundle)
                    if picture not in direct_images:
                        direct_images[picture] = {"cards": []}
                    direct_images[picture]["cards"].append((card_id, card_name))

    return bundle_sprites, direct_images


def check_extracted(sprites_dir, bundle_sprites):
    """Find which bundle sprite names are missing from the extracted sprites folder."""
    sprites_dir = Path(sprites_dir)
    existing_stems = (
        {f.stem.lower() for f in sprites_dir.iterdir() if f.is_file()}
        if sprites_dir.exists() else set()
    )

    missing = {}
    for name, info in bundle_sprites.items():
        stem = Path(name).stem.lower().replace("/", "_").replace("\\", "_")
        if stem not in existing_stems:
            missing[name] = info
    return missing


def probe_url(url):
    """Check if URL exists (HEAD request). Returns True/False."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


FANDOM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Referer": "https://tyrantunleashed.fandom.com/",
}

def find_fandom_image_url(name):
    """Find image on Tyrant Unleashed Fandom wiki via MediaWiki API."""
    import json
    stem = Path(name).stem

    candidates = [stem[0].upper() + stem[1:] if stem else stem, stem]
    seen = set()
    candidates = [x for x in candidates if not (x in seen or seen.add(x))]

    for try_stem in candidates:
        for ext in ['.jpg', '.png']:
            api_url = (
                f"https://tyrantunleashed.fandom.com/api.php"
                f"?action=query&titles=File:{try_stem}{ext}"
                f"&prop=imageinfo&iiprop=url&format=json"
            )
            try:
                req = urllib.request.Request(api_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read())
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    if page.get("pageid", -1) == -1:
                        continue
                    imageinfo = page.get("imageinfo", [])
                    if imageinfo:
                        img_url = imageinfo[0].get("url", "")
                        if img_url:
                            return img_url, try_stem + ext
            except Exception as e:
                print(f"[err:{e}]", end=" ", flush=True)
            time.sleep(0.15)
    return None, name


def find_direct_image_url(name):
    """Try known base URLs, then Fandom wiki as fallback."""
    names_to_try = [name]
    if not any(name.lower().endswith(ext) for ext in ('.jpg', '.png', '.jpeg')):
        names_to_try.append(name + ".jpg")
        names_to_try.append(name + ".png")

    for try_name in names_to_try:
        for base in IMAGE_BASE_URLS:
            url = base + try_name
            if probe_url(url):
                return url, try_name
            time.sleep(0.05)

    print(f"[wiki]", end=" ", flush=True)
    return find_fandom_image_url(name)


def download_file(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def main():
    parser = ArgumentParser(description="Find missing Tyrant Unleashed assets")
    parser.add_argument("--xml-dir",  default=str(Path(__file__).parent),
                        help="Folder with cards_section_*.xml")
    parser.add_argument("--sprites",  default=str(Path(__file__).parent / "pictures"),
                        help="Folder with extracted PNGs")
    parser.add_argument("--probe",    action="store_true",
                        help="Probe CDN for direct images")
    parser.add_argument("--download", action="store_true",
                        help="Download found direct images")
    args = parser.parse_args()

    bundle_sprites, direct_images = scan_xmls(args.xml_dir)

    print(f"\n  {len(bundle_sprites)} unique picture names in bundles")
    print(f"  {len(direct_images)} unique direct image references (no bundle)")

    # ── 1. Check which bundle sprites are missing ──────────────────────────
    print(f"\n{'='*60}")
    print(f"Checking extracted sprites in '{args.sprites}'...")
    sprites_path = Path(args.sprites)
    if not sprites_path.exists():
        print(f"  [WARN] Folder '{args.sprites}' does not exist — skipping check")
        missing_sprites = bundle_sprites
    else:
        missing_sprites = check_extracted(args.sprites, bundle_sprites)

    if missing_sprites:
        print(f"\n  {len(missing_sprites)} bundle sprites NOT found in '{args.sprites}':")
        for name, info in sorted(missing_sprites.items()):
            cards_str = ", ".join(f"{cid}:{cname}" for cid, cname in info["cards"][:3])
            more = f" (+{len(info['cards'])-3} more)" if len(info["cards"]) > 3 else ""
            print(f"  [MISS] '{name}'  bundle={info['bundle_id']}  cards: {cards_str}{more}")
    else:
        print("  All bundle sprites are present ✓")

    # ── 2. Direct images ───────────────────────────────────────────────────
    print(f"\n{'='*60}")

    existing_stems = set()
    if sprites_path.exists():
        existing_stems = {f.stem.lower() for f in sprites_path.iterdir() if f.is_file()}

    missing_direct = {
        name: info for name, info in direct_images.items()
        if Path(name).stem.lower() not in existing_stems
    }

    print(f"Direct image references (no asset bundle):")
    print(f"  Total: {len(direct_images)}  |  "
          f"Already in folder: {len(direct_images)-len(missing_direct)}  |  "
          f"Missing: {len(missing_direct)}")

    if not missing_direct:
        print("  All direct images already downloaded ✓")
    else:
        for name, info in sorted(missing_direct.items()):
            cards_str = ", ".join(f"{cid}:{cname}" for cid, cname in info["cards"][:2])
            more = f" (+{len(info['cards'])-2} more)" if len(info["cards"]) > 2 else ""
            print(f"  '{name}'  ({len(info['cards'])} cards: {cards_str}{more})")

    # ── 3. Probe CDN for direct images ────────────────────────────────────
    if args.probe and missing_direct:
        print(f"\n{'='*60}")
        print(f"Probing CDN + Fandom Wiki for {len(missing_direct)} missing direct images...")
        found_urls = {}
        for name in sorted(missing_direct.keys()):
            if Path(name).stem.lower() in existing_stems:
                continue
            print(f"  Checking '{name}'...", end=" ", flush=True)
            url, actual_name = find_direct_image_url(name)
            if url:
                found_urls[name] = (url, actual_name)
                print(f"[FOUND] → {url}")
            else:
                print(f"[MISS]")

        # ── 4. Download ────────────────────────────────────────────────────
        if args.download and found_urls:
            print(f"\nDownloading {len(found_urls)} direct images to '{args.sprites}'...")
            sprites_path.mkdir(parents=True, exist_ok=True)
            for name, (url, actual_name) in found_urls.items():
                dest = sprites_path / actual_name
                try:
                    download_file(url, dest)
                    size_kb = dest.stat().st_size // 1024
                    print(f"  [OK] '{actual_name}' ({size_kb} KB)")
                except Exception as e:
                    print(f"  [ERR] '{actual_name}': {e}")
        elif found_urls and not args.download:
            print(f"\nRun with --download to save these files to '{args.sprites}'")

    print(f"\n{'='*60}")
    print("Done.")


if __name__ == "__main__":
    import traceback
    try:
        main()
    except SystemExit:
        pass
    except Exception:
        traceback.print_exc()
    input("\nPress Enter to close...")

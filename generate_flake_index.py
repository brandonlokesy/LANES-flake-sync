"""
generate_flake_index.py
-----------------------
Scans a TMDC material folder for optical microscope images and generates
(or updates) a CSV index of all identified flakes.

Usage:
    python generate_flake_index.py <path/to/YYYYMMDD_TMDC/2D-material>

Example:
    python generate_flake_index.py 02_Areas/materials-exfoliation/20260304_WSe2/WSe2

The script looks for images in:
    <material_folder>/all-flakes/

Filename convention expected:
    SX_Y_color NNNN.jpg   →  slide X, flake Y, color extracted automatically
    SX_Y NNNN.jpg         →  slide X, flake Y, color left blank
    SXR_Y NNNN.jpg        →  right chip of slide X, flake Y
    SXL_Y NNNN.jpg        →  left chip of slide X, flake Y
    SX NNNN.jpg           →  calibration image, skipped

Output CSV:
    <material_folder>/<material_folder_name>_flake_index.csv

Columns:
    flake_id, slide_number, flake_number, color, used, used_in, notes

Idempotent: if the CSV already exists, only NEW flakes are appended.
Existing rows are never modified (preserving your manual annotations).
"""

import os
import re
import csv
import sys
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# Matches SX_Y, SXR_Y, SXL_Y, with optional _color suffix.
# Slide identifier is a string to support R/L suffixes (e.g. 3R, 3L, 10R).
# Examples: "S1_2 0001.jpg", "S3R_1 0001.jpg", "S3L_2_darkblue 0005.jpg"
FLAKE_PATTERN = re.compile(
    r"^(S(\d+[LRlr]?)_(\d+))(?:_([a-zA-Z&]+(?:[a-zA-Z&]*)))?",
    re.IGNORECASE,
)

# CSV_COLUMNS = ["flake_id", "slide_number", "flake_number", "color", "thickness (nm)", "quality", "est_area (um2)", "used", "used_in", "notes"]
CSV_COLUMNS = ["flake_id", "slide_number", "flake_number", "color", "thickness (nm)", "layer", "position", "quality", "est_area (um2)", "used", "used_in", "notes"]
# CSV_COLUMNS_TMDC = ["flake_id", "slide_number", "flake_number", "layer", "position", "quality", "est_area (um2)", "used", "used_in", "notes"]

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_flake_from_filename(filename: str):
    """
    Extract flake info from a filename. Returns a dict with:
        flake_id, slide_number, flake_number, color, notes

    Three cases:
      - SX_Y_color ... → normal flake, color extracted
      - SX_Y ...       → normal flake, color left blank
      - SX ...         → calibration image, skipped (returns None)
    """
    stem = Path(filename).stem  # strip extension

    # Case 1 & 2: proper flake with flake number
    match = FLAKE_PATTERN.match(stem)
    if match:
        flake_id   = match.group(1).upper()   # normalise to uppercase e.g. S3R not S3r
        slide_num  = match.group(2).upper()    # string: "3", "3R", "3L", "10R"
        flake_num  = int(match.group(3))
        color = ""
        position = ""
        if "hBN" in stem:
            color      = (match.group(4) or "").lower()
        else:
            position = (match.group(4) or "").lower()
        return {
            "flake_id":     flake_id,
            "slide_number": slide_num,
            "flake_number": flake_num,
            "color":        color,
            "position":     position,
            "notes":        "",
        }

    return None


def collect_flakes(all_flakes_dir: Path) -> dict:
    """
    Walk all-flakes/ and return a dict keyed by flake_id.
    Each value is a dict with slide_number, flake_number, color, notes.

    - For normal flakes (SX_Y), color is extracted from the filename if present.
      If the same flake appears with different colors across images, the first
      non-empty color found is used (files processed in sorted order).
    - For slide overview shots (SX only), a single row is added per slide with
      flake_number=0 and notes="unlabelled flake".
    """
    flakes = {}

    if not all_flakes_dir.is_dir():
        raise FileNotFoundError(f"Could not find folder: {all_flakes_dir}")

    files = sorted(all_flakes_dir.rglob("*"))  # recursive, sorted for determinism

    for f in files:
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        result = parse_flake_from_filename(f.name)
        if result is None:
            continue  # unrecognised filename pattern – skip

        flake_id = result["flake_id"]

        if flake_id not in flakes:
            flakes[flake_id] = result
        else:
            # Backfill color if we didn't have it yet (normal flakes only)
            if not flakes[flake_id]["color"] and result["color"]:
                flakes[flake_id]["color"] = result["color"]
            if not flakes[flake_id]["position"] and result["position"]:
                flakes[flake_id]["position"] = result["position"]

    return flakes


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_existing_csv(csv_path: Path) -> set:
    """
    Return the set of flake_ids already present in the CSV.
    """
    existing = set()
    if not csv_path.exists():
        return existing

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fid = row.get("flake_id", "").strip()
            if fid:
                existing.add(fid)

    return existing


def sort_key(flake: dict):
    # Sort by numeric part of slide_number first, then L/R suffix, then flake_number
    slide = flake["slide_number"]  # e.g. "3", "3L", "3R", "10R"
    num_part = int(re.search(r"\d+", slide).group())
    lr_part  = re.search(r"[LR]", slide, re.IGNORECASE)
    lr_char  = lr_part.group().upper() if lr_part else ""
    return (num_part, lr_char, flake["flake_number"])


def write_csv(csv_path: Path, new_flakes: list, is_new_file: bool):
    """
    Append new_flakes to csv_path.
    If is_new_file is True, write the header first.
    """
    mode = "w" if is_new_file else "a"
    with open(csv_path, mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        if is_new_file:
            writer.writeheader()
        for flake in new_flakes: # CSV_COLUMNS = ["flake_id", "slide_number", "flake_number", "color", "thickness (nm)", "layer", "position","quality", "est_area (um2)", "used", "used_in", "notes"]
            writer.writerow({
                "flake_id":     flake["flake_id"],
                "slide_number": flake["slide_number"],
                "flake_number": flake["flake_number"],
                "color":        flake["color"],
                "thickness (nm)":    "",
                "layer":             "",
                "position":     flake["position"],
                "quality":           "",
                "est_area (um2)":    "",
                "used":              "",
                "used_in":           "",
                "notes":        flake.get("notes", ""),
            })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate or update a flake index CSV for a TMDC material folder."
    )
    parser.add_argument(
        "material_folder",
        help="Relative or absolute path to the YYYYMMDD_TMDC/2D-material folder.",
    )
    args = parser.parse_args()

    material_dir = Path(args.material_folder).resolve()

    if not material_dir.is_dir():
        print(f"[ERROR] Folder not found: {material_dir}")
        sys.exit(1)

    all_flakes_dir = material_dir / "all-flakes"
    csv_name       = f"{material_dir.name}_flake_index.csv"
    csv_path       = material_dir / csv_name

    print(f"Material folder : {material_dir}")
    print(f"Scanning        : {all_flakes_dir}")
    print(f"CSV output      : {csv_path}")
    print()

    # 1. Collect all flakes found in the images
    try:
        found_flakes = collect_flakes(all_flakes_dir)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if not found_flakes:
        print("[WARNING] No flake images found matching the SX_Y pattern.")
        sys.exit(0)

    # 2. Check which flakes are already in the CSV
    existing_ids  = load_existing_csv(csv_path)
    is_new_file   = not csv_path.exists()

    new_flakes = [
        f for fid, f in found_flakes.items()
        if fid not in existing_ids
    ]
    new_flakes.sort(key=sort_key)

    # 3. Report
    print(f"Flakes found in images : {len(found_flakes)}")
    print(f"Already in CSV         : {len(existing_ids)}")
    print(f"New entries to add     : {len(new_flakes)}")

    if not new_flakes:
        print("\nNothing to do – CSV is already up to date.")
        sys.exit(0)

    # 4. Write
    write_csv(csv_path, new_flakes, is_new_file)

    print(f"\n{'Created' if is_new_file else 'Updated'}: {csv_path}")
    print("New flakes added:")
    for f in new_flakes:
        color_str = f"  color={f['color']}" if f["color"] else ""
        print(f"  {f['flake_id']}{color_str}")


if __name__ == "__main__":
    main()
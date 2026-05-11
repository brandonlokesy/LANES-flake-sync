"""
sync_selected.py
----------------
Reads the flake index CSV and copies all images belonging to flakes marked
as used (used=1) into the selected/ folder.

Usage:
    python sync_selected.py <path/to/YYYYMMDD_TMDC/2D-material>

Example:
    python sync_selected.py 02_Areas/materials-exfoliation/20260304_WSe2/WSe2

Behaviour:
  - Reads <material_folder>/<material_name>_flake_index.csv
  - For every row where used == 1, finds ALL matching images in all-flakes/
    (including subfolders) and copies them to selected/
  - If an image already exists in selected/, it is skipped (never overwritten)
  - selected/ is created automatically if it does not exist
"""

import csv
import re
import shutil
import sys
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# Matches the SX_Y prefix at the start of a filename
FLAKE_ID_PATTERN = re.compile(r"^(S\d+_\d+)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_used_flakes(csv_path: Path) -> set:
    """
    Return the set of flake_ids where used == 1.
    """
    used = set()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if "used" not in reader.fieldnames or "flake_id" not in reader.fieldnames:
            raise ValueError("CSV is missing 'flake_id' or 'used' columns.")
        for row in reader:
            if row.get("used", "").strip() == "1":
                used.add(row["flake_id"].strip())

    return used


def find_images_for_flake(all_flakes_dir: Path, flake_id: str) -> list:
    """
    Return all image files in all_flakes_dir (recursively) whose filename
    starts with the given flake_id (e.g. S22_8).
    """
    matches = []
    for f in sorted(all_flakes_dir.rglob("*")):
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        m = FLAKE_ID_PATTERN.match(f.stem)
        if m and m.group(1).upper() == flake_id.upper():
            matches.append(f)
    return matches


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Copy used flake images from all-flakes/ to selected/."
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
    selected_dir   = material_dir / "selected"
    csv_name       = f"{material_dir.name}_flake_index.csv"
    csv_path       = material_dir / csv_name

    print(f"Material folder : {material_dir}")
    print(f"CSV             : {csv_path}")
    print(f"Source          : {all_flakes_dir}")
    print(f"Destination     : {selected_dir}")
    print()

    if not all_flakes_dir.is_dir():
        print(f"[ERROR] all-flakes/ folder not found: {all_flakes_dir}")
        sys.exit(1)

    # 1. Load used flakes from CSV
    try:
        used_flakes = load_used_flakes(csv_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if not used_flakes:
        print("No flakes marked as used (used=1) found in CSV. Nothing to do.")
        sys.exit(0)

    print(f"Flakes marked as used : {len(used_flakes)}")
    print()

    # 2. Create selected/ if it doesn't exist
    selected_dir.mkdir(exist_ok=True)

    # 3. Copy images
    total_copied  = 0
    total_skipped = 0

    for flake_id in sorted(used_flakes):
        images = find_images_for_flake(all_flakes_dir, flake_id)

        if not images:
            print(f"  [WARNING] {flake_id} — no images found in all-flakes/")
            continue

        for src in images:
            dest = selected_dir / src.name
            if dest.exists():
                print(f"  [SKIP]    {src.name} (already exists)")
                total_skipped += 1
            else:
                shutil.copy2(src, dest)  # copy2 preserves file metadata
                print(f"  [COPIED]  {src.name}")
                total_copied += 1

    # 4. Summary
    print()
    print(f"Done. Copied: {total_copied}  |  Skipped (already existed): {total_skipped}")


if __name__ == "__main__":
    main()
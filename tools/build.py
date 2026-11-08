#!/usr/bin/env python3
"""Generate the textured tent shape from Tent.json and package the mod.

Tent.json is the editable source and is left untouched. Run from anywhere:
    python3 tools/build.py
"""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Tent.json"
SHAPE = ROOT / "assets/simpletent/shapes/block/tent.json"
MODINFO = ROOT / "modinfo.json"
DIST = ROOT / "dist"

# A texture spans 16 UV units and cannot repeat across one face, so panels are
# split into tiles of about one block each to match the game's texture scale.
ROW_HEIGHTS = [16, 16, 8]
COLUMN_COUNT = 3


def linen_face(uv):
    return {"texture": "#linen", "uv": uv}


def tile(name, y0, y1, z0, z1, is_bottom, is_top, is_first, is_last):
    """Build one panel tile, positioned relative to its parent panel."""
    height = y1 - y0
    faces = {
        "east": linen_face([0, 0, 16, height]),
        "west": linen_face([0, 0, 16, height]),
    }
    # Thin edges are only visible on the panel's outer perimeter.
    if is_first:
        faces["north"] = linen_face([0, 0, 1, height])
    if is_last:
        faces["south"] = linen_face([0, 0, 1, height])
    if is_bottom:
        faces["down"] = linen_face([0, 0, 1, 16])
    if is_top:
        faces["up"] = linen_face([0, 0, 1, 16])
    return {
        "name": name,
        "from": [0, y0, round(z0, 4)],
        "to": [1, y1, round(z1, 4)],
        "faces": faces,
    }


def tile_panel(element):
    """Give a panel a grid of linen child tiles; the panel itself stays faceless."""
    depth = element["to"][2] - element["from"][2]
    column_size = depth / COLUMN_COUNT
    children = []
    y0 = 0
    for row, height in enumerate(ROW_HEIGHTS):
        y1 = y0 + height
        for column in range(COLUMN_COUNT):
            children.append(tile(
                f"{element['name']}_r{row}c{column}",
                y0,
                y1,
                column * column_size,
                (column + 1) * column_size,
                row == 0,
                row == len(ROW_HEIGHTS) - 1,
                column == 0,
                column == COLUMN_COUNT - 1,
            ))
        y0 = y1
    expected = element["to"][1] - element["from"][1]
    if y0 != expected:
        raise ValueError(f"{element['name']}: rows cover {y0}, panel height is {expected}")
    element["faces"] = {}
    element["children"] = children


def texture_pole(element):
    # Plank grain runs along U; rotating 90 degrees runs it up the pole. Rotated
    # faces store UVs with width and height swapped.
    side = {"texture": "#wood", "uv": [0, 0, 16, 2], "rotation": 90}
    cap = {"texture": "#wood", "uv": [0, 0, 2, 2]}
    element["faces"] = {
        "north": dict(side),
        "east": dict(side),
        "south": dict(side),
        "west": dict(side),
        "up": dict(cap),
        "down": dict(cap),
    }


def generate_shape():
    shape = json.loads(SOURCE.read_text())
    for element in shape["elements"]:
        if element["name"].startswith("side_"):
            tile_panel(element)
        elif element["name"].startswith("pole_"):
            texture_pole(element)
        else:
            raise ValueError(f"Unexpected element {element['name']!r} in {SOURCE.name}")
    SHAPE.parent.mkdir(parents=True, exist_ok=True)
    SHAPE.write_text(json.dumps(shape, indent="\t") + "\n")


def package():
    version = json.loads(MODINFO.read_text())["version"]
    DIST.mkdir(exist_ok=True)
    archive = DIST / f"SimpleTent_{version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(MODINFO, MODINFO.name)
        for path in sorted((ROOT / "assets").rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT).as_posix())
    return archive


if __name__ == "__main__":
    generate_shape()
    print(f"Built {package()}")

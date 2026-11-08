#!/usr/bin/env python3
"""Generate the textured tent shape from Tent.json, compile the code and package the mod.

Tent.json is the editable source and is left untouched. Run from anywhere:
    python3 tools/build.py
"""
import json
import math
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Tent.json"
SHAPE = ROOT / "assets/simpletent/shapes/block/tent.json"
BLOCKTYPE = ROOT / "assets/simpletent/blocktypes/tent.json"
MODINFO = ROOT / "modinfo.json"
PROJECT = ROOT / "SimpleTent.csproj"
ASSEMBLY = ROOT / "bin/Release/SimpleTent.dll"
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


def tile_hay_bed(element):
    """Rebuild the bed from the two halves of the vanilla hay bed (shapes/block/hay/bed-*.json).

    The vanilla halves run along X, with their head end at -X. Each is turned so X runs along
    this bed's Z axis, keeping the vanilla faces and UVs (cropped to this bed's height). The
    head half sits at the north end, matching the sleeper's yaw from bed_pose().
    """
    width = element["to"][0] - element["from"][0]
    height = element["to"][1] - element["from"][1]
    half = (element["to"][2] - element["from"][2]) / 2

    def face(texture, u0, v0, u1, **extra):
        return {"texture": f"#{texture}", "uv": [u0, v0, u1, v0 + height], **extra}

    def top_face(texture, u0, u1):
        return {"texture": f"#{texture}", "uv": [u0, 1, u1, 15], "rotation": 180}

    def bottom_face(u0, u1):
        return {"texture": "#haybottom", "uv": [u0, 1, u1, 15]}

    parts = (
        ("head", {
            "north": face("hayside1", 1, 8, 16),
            "south": face("hayside1", 0, 4, 15),
            "west": face("hayside2", 1, 12, 15),
            "up": top_face("haytop2", 1, 16),
            "down": bottom_face(0, 15),
        }),
        ("foot", {
            "north": face("hayside1", 0, 12, 15),
            "south": face("hayside1", 1, 0, 16),
            "east": face("hayside2", 1.6, 4, 15.6),
            "up": top_face("haytop1", 0, 15),
            "down": bottom_face(1, 16),
        }),
    )

    children = []
    for index, (part, faces) in enumerate(parts):
        centre_x = width / 2
        centre_z = (index + 0.5) * half
        children.append({
            "name": f"{element['name']}_{part}",
            "from": [centre_x - half / 2, 0, centre_z - width / 2],
            "to": [centre_x + half / 2, height, centre_z + width / 2],
            "rotationOrigin": [centre_x, 0, centre_z],
            "rotationY": 270,
            "faces": faces,
        })
    element["faces"] = {}
    element["children"] = children


def bed_pose(element):
    """Where a sleeper lies on the bed, in blocks, using the game's Y rotation."""
    origin_x, _, origin_z = element.get("rotationOrigin", [0, 0, 0])
    yaw_deg = element.get("rotationY", 0)
    angle = math.radians(yaw_deg)
    dx = (element["from"][0] + element["to"][0]) / 2 - origin_x
    dz = (element["from"][2] + element["to"][2]) / 2 - origin_z
    x = origin_x + dx * math.cos(angle) + dz * math.sin(angle)
    z = origin_z - dx * math.sin(angle) + dz * math.cos(angle)
    return round(x / 16, 4), element["to"][1] / 16, round(z / 16, 4), yaw_deg


def write_bed_pose(pose):
    x, y, z, yaw_deg = pose
    text, count = re.subn(
        r"bedPose: \{[^}]*\}",
        f"bedPose: {{ x: {x}, y: {y}, z: {z}, yawDeg: {yaw_deg} }}",
        BLOCKTYPE.read_text(),
    )
    if count != 1:
        raise ValueError(f"Expected one bedPose line in {BLOCKTYPE.name}, found {count}")
    BLOCKTYPE.write_text(text)


def generate_shape():
    shape = json.loads(SOURCE.read_text())
    pose = None
    for element in shape["elements"]:
        if element["name"].startswith("side_"):
            tile_panel(element)
        elif element["name"].startswith("pole_"):
            texture_pole(element)
        elif element["name"] == "hay_bed":
            pose = bed_pose(element)
            tile_hay_bed(element)
        else:
            raise ValueError(f"Unexpected element {element['name']!r} in {SOURCE.name}")
    if pose is None:
        raise ValueError(f"No hay_bed element in {SOURCE.name}")
    SHAPE.parent.mkdir(parents=True, exist_ok=True)
    SHAPE.write_text(json.dumps(shape, indent="\t") + "\n")
    write_bed_pose(pose)


def compile_code():
    subprocess.run(["dotnet", "build", str(PROJECT), "-c", "Release", "--nologo", "-v", "q"], check=True)


def package():
    version = json.loads(MODINFO.read_text())["version"]
    DIST.mkdir(exist_ok=True)
    archive = DIST / f"SimpleTent_{version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(MODINFO, MODINFO.name)
        zf.write(ASSEMBLY, ASSEMBLY.name)
        for path in sorted((ROOT / "assets").rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT).as_posix())
    return archive


if __name__ == "__main__":
    generate_shape()
    compile_code()
    print(f"Built {package()}")

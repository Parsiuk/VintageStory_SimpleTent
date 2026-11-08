# Simple Tent

A craftable tent for Vintage Story that you can sleep in, made in the colour of your cloth and the wood of your support beams.

> **This mod gives you no advantage over a vanilla hay bed.** It was made mostly for aesthetics and role play: a camp on the road, a hunter's shelter, a settlement of canvas instead of bare beds in a field.

- You sleep exactly as well as in a hay bed. Sleep efficiency is identical, and the same tiredness and temporal storm rules apply.
- It costs more than a hay bed, needing cloth and support beams on top of the same three hay bales.
- The canvas has no collision, so it won't keep creatures out.

## Crafting

|          |              |          |
| -------- | ------------ | -------- |
|          | Support beam |          |
| Cloth    | Support beam | Cloth    |
| Hay bale | Hay bale     | Hay bale |

Any cloth colour and any wooden support beam will do, as long as both cloths match and both beams match. The cloth colours the canvas and the wood is used for the poles.

## Using the tent

- The tent takes up 3×3 blocks and is 2 blocks tall, centred on where you place it. It needs that space free.
- **Right-click** any part of it to sleep. Press **sneak** to wake up.
- **Ctrl + right-click** to pick it back up, keeping its colour and wood. This doesn't work while someone is sleeping in it.
- You can walk through the canvas, but you can't place blocks inside the tent.

## Compatibility

Made for Vintage Story 1.22.7. It has been tested in single player.

## Installing

Download `SimpleTent_<version>.zip` from the releases page and put it, still zipped, in your `VintagestoryData/Mods` folder.

## Building

Run `python3 tools/build.py` to create `dist/SimpleTent_<version>.zip`. It requires the .NET 10 SDK and an installed copy of the game. The game is expected in `~/Apps/VintageStory`; set `VINTAGE_STORY` if yours is elsewhere. The `dist/` folder is ignored by git.

`Tent.json` is the editable model. The build generates the textured shape from it and works out where the sleeper lies from the `hay_bed` element, so rebuild after changing it.

## Releasing

1. Bump `version` in `modinfo.json` and merge to `master`.
2. Run `tools/release.sh` to tag the latest `master` (requires `jq`).
3. Push the tag with the command it prints. GitHub then builds the mod and publishes the release.

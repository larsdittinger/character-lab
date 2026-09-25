# Adding a character

Every new character gets a separate workspace. The reference must still be individually measured; the scaffold does not relabel an existing knight as a new reconstruction.

For local models, ChatGPT or Gemini, start with [AGENT_START.md](AGENT_START.md). It distinguishes the coding agent from the image provider and explains how to import references when using a tool other than the built-in OpenAI helper.

```sh
.venv/bin/python tools/new_character.py mage --title "Mage"
```

Existing folders and reserved IDs knight/ranger/elf are rejected. The command creates:

```text
characters/mage/
  character.json            display name and optional face camera target
  config/prompt.txt         description of the NEW character
  config/                   measured profiles, masks, face and joints
  references/               original PNG and generation metadata
  tools/                    model.py, build.py, rig.py, optional render.py
  assets/                   model.json, static/rigged/animated.glb and .blend
  textures/projection.png
  animations/catalog.json
  animations/retargeted/     clips for this exact target hierarchy
  accessories/              each accessory in a separate folder
  review/                   baselines, renders, validation and build timings
```

Empty folders are not finished models. No calibration or fictitious validation report is copied into them.

## Base reference without accessories

Edit this character's `config/prompt.txt`. The base character must have **no cloak, trailing cloth, weapons, backpack, quiver, dangling straps or protruding ornaments**. Fitted clothing should expose the body's true silhouette in all three views. Natural ears remain. A cloak or equipment later gets its own reference, mesh, material and rig attachment under `accessories/<id>/`; keep it out of the base sheet.

```sh
.venv/bin/python tools/generate_reference.py --character mage --dry-run
.venv/bin/python tools/generate_reference.py --character mage
```

The default is GPT Image 2.5 Sunburst at high quality. See [PRICING.md](PRICING.md). Each attempt needs a new `--name`; raw PNG and metadata are never overwritten. Mandatory rules in `config/base-character-rules.txt` also apply to custom `--prompt-file` input. No rebuild calls the paid API.

## Calibration and build contract

Follow [WORKFLOW.md](WORKFLOW.md): silhouette/volume, landmarks, source ownership, then blending. Compare head proportions with the accepted knight using the same whole-body camera. New scripts receive `CHARACTER_LAB_DIR` (character workspace), `CHARACTER_LAB_ROOT` (project root) and `CHARACTER_LAB_CHARACTER` (ID).

| Stage | Execution | Required output |
|---|---|---|
| geometry | character `tools/model.py`, then Blender `tools/build.py` | `assets/model.json`, `assets/static.glb/.blend`, `textures/projection.png`, `review/input-validation.json`, `review/projection.json`, `review/topology.json` |
| rig | Blender `tools/rig.py`, anatomical L/R guard, standard 27-joint hierarchy | `assets/rigged.glb/.blend` |
| motion | shared `retarget.mjs`, `export_clips.mjs`, `save_animated.py` | `assets/animated.glb/.blend`, catalog, 214 motion-only files, retarget and Blender action reports |
| validate | shared real skin/curve validator, input and projection reports | `review/validation.json` |
| render | optional character Blender `tools/render.py` | matching camera views of baseline and current output |

```sh
.venv/bin/python tools/pipeline.py geometry --character mage
.venv/bin/python tools/pipeline.py build --character mage
.venv/bin/python tools/pipeline.py render --character mage
```

Missing modeling scripts produce an explicit error. There is no universal PNG-to-body algorithm here: an agent must read and calibrate the new reference. Shared retargeting expects the established joint names/hierarchy and actual downloaded source curves. Target-specific outputs must stay separate.

## Automatic viewer discovery

`npm run serve` exposes `/api/characters`. The list refreshes every five seconds or through the button beside the character selector. A completed `assets/animated.glb` takes precedence over `assets/static.glb`. A new export of the selected model reloads it. Incomplete exports and reference-only folders are not listed.

A minimal `character.json` is `{"title":"Mage"}`. Optional fields are `face: [x,y,z]`, `reference`, `path`, `blend`, `catalog` and `comparisons: {"before": {"path":"review/before.glb","title":"Before correction"}}`. Paths are relative to the character folder and cannot escape it. Without `face`, the camera target is derived from model bounds. Missing reference/Blender/catalog links are hidden. Animation controls use actual GLB clips; an animated GLB without a catalog uses its embedded names and is not labeled as a downloaded CC0 library.

The three supplied characters retain their original paths, declared in `config/characters.json`. Their existing pipeline commands remain compatible wrappers around the shared implementation.

The server listens on localhost and does not serve `.env`, hidden paths, directory listings or symlinks outside the project. Credentials are never exposed to the viewer; generation runs through the local CLI.

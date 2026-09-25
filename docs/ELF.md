# Night Elf: independent third calibration

The night elf has purple skin, silver hair, light leather armor and a separate dark cloak, without a bow, quiver or held prop. Reference, sections, rig, atlas, clips and reports are separate from the knight/ranger. This historical character predates the new rule requiring cloaks and equipment to be authored separately from the base reference.

## Provenance and reproduction

One built-in ImageGen call produced **one 1536×1024 sheet** with front, true side and back. The original [image](../references/elf/turnaround.png), [metadata and SHA-256](../references/elf/turnaround.json) and [prompt](../config/elf-prompt.txt) remain saved. Builds are offline and make no Gemini or other image-generation calls.

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/elf_pipeline.py build
.venv/bin/python tools/elf_pipeline.py render
npm run serve
```

Select **Night Elf** at http://localhost:8770/. Focused stages: geometry, rig, motion, validate, render. Geometry/projection changes require dependent stages; `--force` disables verified caching. Blender is found on PATH, in the standard macOS application, or through `BLENDER`. All Blender phases use `--python-exit-code 1`.

## Independent measurements

[elf-profiles.json](../config/elf-profiles.json) stores 17 profile types and 106 ordered sections. Front center X=281, side origin X=756, rear center X=1253, top Y=18, ground Y=944, authored height 2.5 m. Ears are separate pointed volumes. The cloak is a wide piece behind the torso with its own rear projection. [elf-rig.json](../config/elf-rig.json) fits the joints to this character. Anatomical L is +X, R is −X; paired-part centroids are checked before weighting.

Front and side ears differ in image height; side ear sampling shifts 10 px. Head projection replaces the painted ear with surrounding skin/hair so the separate geometry does not produce a duplicate. Rear silver hair uses observed hair pixels from the back view; missing silhouette pixels extend valid hair within that row. Hidden surface color is an authored approximation.

Whole-body comparison with the accepted knight exposed a narrow-looking head. `headWidthScale: 1.45` widens the face from **0.189 m to 0.274 m**. UV sampling stays on the same measured pixels, ears move with the widened face, and the neck receives half the correction. The ranger uses its separate 1.10 correction. [Matching camera views](../review/head-width.html) show both corrections and the knight. These are authored style decisions, not universal constants inferred automatically from an image.

## Outputs and verification

The final [GLB](../assets/elf-animated.glb) has **61,188 triangles, 31,242 vertices, 27 joints and 214 named clips**. The [animated Blender file](../assets/elf-animated.blend) retains 214 actions and active idle; `elf-rigged.blend` retains 30 editable mesh pieces. The 214 target-specific motion files are in `animations/elf/retargeted/`, with a separate catalog.

[Input validation](../review/elf/input-validation.json), [nine source-ownership guards](../review/elf/projection.json) and [final validation](../review/elf/validation.json) pass. Every actual motion file is opened and compared with the final hierarchy and exact matching curves. There are 32 idle clips, 8 runs and 1,284 evaluated skinned poses.

Static review covers body front/three-quarter/profile/back and three face angles. Browser review includes idle, KayKit running, Quaternius jog/sprint, KayKit short jump/waving, skeleton, face detail and switching to both other characters. Numeric checks establish topology, skin weights, finite values and curve consistency; they do not certify every animation's visual quality.

## Remaining limits

Close profiles show painted transitions around silver hair and ears. The cloak uses simple derived weights without cloth simulation or collision and can intersect legs during running/jumping. Hands lack individual finger bones. Source clips named for bow use remain available even though this model has no bow. These limits survive numeric PASS.

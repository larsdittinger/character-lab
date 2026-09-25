# Technical workflow

## Proven iteration cycle for the next agent

This cycle records fixes verified on the knight, ranger and night elf on September 25, 2026. Coordinates belong to their specific references. Reuse the review method, not arbitrary pixel values. Read [AGENTS.md](../AGENTS.md), [FACE.md](FACE.md), [VALIDATION.md](VALIDATION.md) and the relevant character document first.

1. **Reproduce the accepted state.** Use local dependencies and saved references. Build the selected character and open its actual animated GLB in the viewer. Fix a failing stage before continuing. Do not generate another reference to repair projection or weighting.
2. **Save a comparable baseline.** Preserve GLB, configuration, affected scripts, atlas and review renders in a new `review/baseline-<date>-<attempt>/`. Never overwrite historical comparisons. Record the character, defect and revealing view. Keep camera, lighting, pose and animation time identical when comparing.
3. **Find the cause in this order:** untextured silhouette/volume → landmark correspondence → source ownership → color blending. Inspect front, three-quarter, profile and rear. For a new character, compare head width and height against the accepted knight in the same whole-body view, then inspect face, ear roots and neck. Numeric skin PASS cannot detect an aesthetically narrow head.
4. **Change one cause at a time.** Keep calibrations separate. Add naming, weighting and side guards for new parts. Review the static export first. If improving one view damages another, revise or revert the attempt.
5. **Rebuild dependent outputs.** Geometry and embedded texture require geometry → rig → motion → validation. The shared pipeline reuses only content-verified identical stages; `--force` reproduces every step. Run knight face renders, ranger renders or elf renders after projection changes. Do not trust a stale PASS report.
6. **Inspect actual motion and images.** Switch all three supplied characters. On the changed model, inspect Quaternius `Idle Loop`, KayKit `Running A`, Quaternius `Jog Fwd Loop` and `Sprint Loop`, KayKit `Jump Full Short` and `Waving`. Show the skeleton, pause and scrub extreme poses. Check limbs, shoulders, armor and cloth. Inspect the rest pose from front/three-quarter/profile/back and in Clay mode. Use both knight comparisons and the [head comparison](../review/head-width.html). Reload after changed assets and inspect browser errors.
7. **Keep only a demonstrated improvement.** Require numeric PASS and visible improvement without regressions in required views/motions. Otherwise restore that attempt's code/configuration and rebuild its outputs together. Document the cause, exact changes, commands, measured counts, inspected views/clips and remaining limits. Leave the viewer open.

### Previously solved symptoms

| Symptom | Cause and correction | Verification |
|---|---|---|
| Second eye/eyebrow on temple | Align landmarks and face volume in `config/face.json` before blending | Front, three-quarter, profile; one feature per visible side |
| Ear on pauldron, armor on jaw, sleeve on bracer | Depth profile includes an occluding foreign part; define valid source regions | Semantic guards and the whole neighboring region in renders |
| White silhouette fringes | Studio background sampled into atlas; pad from the same part and image row | Padding report, side/rear, missing-source cases |
| Pale bald patch on ranger's rear head | Rear hair width differs from front; remeasure `rearHeadRegistration` | Rear/profile, no skin or background inside hair |
| Extra ear or brown rectangle below separate ear | Ear remains painted on head; mask its actual outline in contributing views | Front/three-quarter/profile against baseline; [RANGER.md](RANGER.md) |
| Stretched horizontal collar band | Constant source column; restore two-dimensional sampling inside valid side profile | Diagonal collar trim continues around the side |
| Rest pose works, idle twists/crosses limbs | Anatomical L/R names copied from the opposite reference half | L centroid +X, R −X; real idle and both run sources |
| Narrow head in whole-body view | Image coordinates do not guarantee convincing stylized proportions | Widen head geometry, move ears and blend neck; compare matching cameras, then rebuild rig/motion |
| Underground spawn flagged as exploded skin | Whole root trajectory mistaken for individual posed-body size | Preserve source travel and report scene requirements separately |

## What the agent decides

The image model supplies a raster reference. The agent reads the reference, measures proportions, chooses sections, joint positions and facial correspondences, writes configuration and reviews the results. “Manual calibration” means individual visual measurement and modeling decisions by the agent, not vertex-by-vertex mouse editing.

Python and Blender build meshes, UVs, skeletons and weights from saved measurements. Downloaded Quaternius/KayKit curves provide motion; retargeting and IK adapt them to the target. A weaker model can reproduce the supplied examples offline. That does not establish that it can calibrate an arbitrary new image equally well.

## 1. Reference images

The original knight uses a saved Gemini front/profile sheet plus a supplementary rear image. The first raw output included a duplicate profile; it remains preserved. `prepare.py` makes calibrated crops. Historical generation metadata is in `references/generation.json`.

For a new character, use front + true 90° side + back in one sheet, the same A-pose and height, neutral light and no perspective foreshortening. Shared sheets help consistency but do not guarantee matching landmarks. A separate high-resolution head turnaround is an additional paid image.

New base references must omit cloaks, trailing cloth, backpacks, quivers, weapons and protruding equipment. Keep fitted clothing and compact armor. Natural ears remain. Model accessories separately in `characters/<id>/accessories/` and attach them to the accepted rig. Historical supplied references, including the elf's cloak, remain unchanged.

```sh
.venv/bin/python tools/new_character.py mage --title "Mage"
# Edit characters/mage/config/prompt.txt first.
.venv/bin/python tools/generate_reference.py --character mage --dry-run
.venv/bin/python tools/generate_reference.py --character mage
# A separately named identity-preserving edit:
.venv/bin/python tools/generate_reference.py --character mage --name new-views --reference characters/mage/references/turnaround.png
```

The optional helper uses OpenAI GPT Image 2.5 Sunburst, `quality=high`, one 1536×1024 PNG. It reads only `OPENAI_API_KEY` from the environment or local `.env`. It preserves original bytes, full prompt, SHA-256, model, quality and API usage. It never overwrites PNG/metadata or automatically retries a paid request. Failure leaves a `.pending` record to prevent accidental duplicate charges. See [pricing](PRICING.md) and the [folder contract](CHARACTERS.md).

The ranger and elf each came from one built-in ImageGen call producing one 1536×1024 three-view image. Their originals, prompts and metadata remain in their own reference/config files. Neither used a new Gemini call, and no measured invoice is claimed. Offline builds reuse these images.

## 2. Calibration

The knight's working image is 1907×1280. Front center X=494, side depth origin X=1230, top Y=72, ground Y=1215; authored character height 2.5 m. Scale is `2.5 / (1215 - 72)`. GLB coordinates are Y-up, forward +Z.

`config/profiles.json` contains 17 profile types and 120 measured sections. Rows are `[imageY, frontLeftX, frontRightX, sideFrontX, sideBackX]`. Paired parts are mirrored. Crest and buckle have separate relief in `model.py`, yielding 29 closed pieces.

`validate_inputs.py` checks calibration size, finite coordinates, positive widths/depths, increasing Y, face correspondences and nonzero bones. Its report fingerprints raw sources and configuration. `model.py` verifies front and rear raw hashes against `config/projection.json`; changed sources with old masks fail.

For another image:

1. Preserve raw output and identify crops, scale and shared vertical landmarks.
2. Set that character's crop preparation, front center, depth origin, ground, height and relief geometry.
3. Remeasure each part's strictly increasing section rows.
4. Remeasure rear center, scale and vertical correspondences.
5. Align facial landmarks and depth warp separately.
6. Define actual source visibility in all views, add allowed/forbidden regression points and bind hashes only after calibration.
7. Inspect static geometry and head proportions before fitting joints and weights.

Use the new character folder rather than editing the knight's files. Unseen surfaces require authored choices; this is guided reconstruction, not automatic photogrammetry.

## 3. Geometry and texture

`model.py` interpolates measured sections with shape-preserving cubic Hermite interpolation. Each section has 64 radial segments, capped ends and a welded seam. Face relief and a cross-section exponent control volume; flattening a face too far pulls side landmarks forward.

Colors are projected from front, side and rear. A part's depth silhouette does not tell whether it is visible in the source: an ear may occlude a pauldron. Projection rules use rows `[imageY, validLeftX, validRightX]` and optional excluded polygons.

- `front-fallback` rejects invalid side pixels and uses the same part's front projection. Used for pauldrons and bracers.
- `clamp-valid-source` extends neighboring visible material into occluded regions. Used for jaw, hair, nape and portions of the shoulder boundary.

Rules use a 2 px inset and a 3 px feather on the valid side. Nine semantic guards and repaired sample counts are recorded in `review/projection.json`. Face vertical/depth warping happens before side masking. Sharp landmarks use narrow transitions; broad color uses wider transitions. See [FACE.md](FACE.md).

`frontBackgroundGuard` finds neutral studio background connected to the image boundary and expands it by 2 px. Invalid samples move to valid material in the same image row and measured interval of the same part. When no source exists in a row, an authored base color is used and counted separately. `frontBackgroundPadding` reports repaired samples, missing source and remaining background independently.

The knight atlas is 2640×4704 with UV island gutters. Blender imports, welds, recalculates normals, simplifies and exports a GLB with embedded texture. The editable `.blend` retains separate parts; GLB uses one mesh primitive/material. Source illumination remains painted into the texture, so rendering uses restrained material specularity.

## 4. Skeleton and weights

`rig_character.py` converts to Blender Z-up, creates 23 humanoid bones from `config/rig.json` and adds four tabard bones. Rest axes come from `config/source-rig.json`; `inspect_source_rig.py` can reproduce that source description.

Weights depend on named parts and position. Head follows head, pauldrons follow clavicles, forearm plates follow forearms and gloves follow hands. Soft joints transition smoothly; cloth blends pelvis and side cloth bones. Weights are normalized. Unknown parts deliberately fail instead of receiving arbitrary automatic weights.

L/R are anatomical: with Y-up and +Z forward, L is +X and R is −X. Rig scripts assert paired-part centroid signs before weighting. Knight and ranger trace opposite halves of their front images; blindly copying suffixes previously weighted limbs to opposite bones. Normalized weights and finite coordinates did not reveal the error. Rebuild rig/motion and inspect real idle/running after naming changes.

## 5. Downloaded animation

Official free sources:

- [Quaternius Universal Animation Library](https://quaternius.itch.io/universal-animation-library), Standard.
- [Quaternius Universal Animation Library 2](https://quaternius.itch.io/universal-animation-library-2), Standard.
- [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations), free pack 1.1.

Original ZIPs, extracted files and licenses are in `animations/source/`. `animations/sources.json` records source links, authors, sizes and archive SHA-256. These are complete free downloads, not the paid Pro/Source libraries. Credit Quaternius, Gonzalo Furnier and Kay Lousberg / KayKit. Their CC0 animation licenses do not automatically apply to generated reference images.

`python3 tools/download_animations.py` reuses existing archives. It follows the official itch.io free-download flow; website changes must be investigated rather than guessed around with paid uploads.

Retargeting uses UAL1/UAL2 without `_RM` and KayKit Rig_Medium. Other rigs and supplied root-motion variants remain in raw source. T-poses and the experimental transform are excluded from normal clips. The resulting 214 named clips include short pose clips, not 214 locomotion cycles. See the target's catalog.

## 6. Motion transfer

For each clip, `retarget.mjs`:

1. Reads glTF hierarchy, rest transforms and source curves; samples at 30 Hz including the endpoint.
2. Computes source world-rotation changes from rest and maps KayKit names to the target hierarchy.
3. Aligns target A-pose arms to source T-pose using joint-position vectors, avoiding exporter-canonicalized local axes.
4. Transfers rotations and root/pelvis translations, scaled by leg length, then derives target local rotation from parent world rotation.
5. Solves two-bone leg IK using hip-relative ankle trajectories and the source knee direction. A root-relative constant offset overextends KayKit legs. This is not terrain contact simulation.
6. Derives limited cloth-bone rotation from thigh motion; no cloth simulation.
7. Writes standard glTF curves, normalized quaternions and consistent quaternion signs between samples.

Source animated bone scaling is ignored because spawn/disassembly scaling-to-zero is not ordinary transferable humanoid joint motion. These clips retain poses rather than the complete spawn effect. Gloves have no individual finger rig. Pose clips receive at least 1/30 s to keep time samples valid.

`export_clips.mjs` writes one motion-only GLB per clip with the same target hierarchy and no duplicated mesh/atlas. `save_animated.py` imports the final GLB into Blender, preserves all 214 actions with fake users, mutes NLA tracks and selects idle. Choose other actions in Blender's Action Editor.

All targets use shared retarget/export/validation code through `character_paths.mjs`. `CHARACTER_LAB_CHARACTER` selects knight, ranger, elf or a new registered folder. Thin legacy wrappers remain compatible; they do not rewrite source code. The binary writer accumulates chunks and assembles once, preserving exact output bytes. [PERFORMANCE.md](PERFORMANCE.md) describes caching and measurements.

## 7. Viewer and review

Three.js GLTFLoader reads embedded material, skin and clips. The English viewer automatically discovers character manifests through the local server. Counts come from actual geometry; catalogs supply provenance/category labels. Camera framing uses model bounds and optional measured face targets. AnimationMixer crossfades over 0.18 s. Static models disable animation controls.

Use playback, scrubber, speed, Skeleton and Clay controls. The knight's **Projection comparison** switches among the current model and both historical GLBs while keeping the camera and rest pose. Choosing a motion returns to the current model. Download/reference links follow the selected character. Dependencies come from local `node_modules`, not a CDN.

Numeric validation checks GLB values, time order, quaternion/weight normalization and topology. It opens every actual motion-only file and compares hierarchy, channels, interpolation and exact curve values to the matching final clip. Blender action count must match. It evaluates 1,284 skinned poses, measuring each posed body's extent separately from root travel. It cannot replace visual checks of head proportions, collisions or contacts. See [VALIDATION.md](VALIDATION.md).

## Commands

| Command | Result |
|---|---|
| `pipeline.py geometry` | Prepared images, input/source checks, masks, geometry JSON, atlas, static GLB/Blend |
| `pipeline.py rig` | Fitted rigged GLB and separate editable Blender pieces |
| `pipeline.py motion` | Animated GLB, individual clips and animated Blend |
| `pipeline.py validate` | Fresh validation report |
| `pipeline.py build` | All four stages in order; verified cache supported |
| `pipeline.py render` | Knight's nine face comparison renders |

```sh
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/ranger_pipeline.py render
.venv/bin/python tools/elf_pipeline.py build
.venv/bin/python tools/elf_pipeline.py render
```

Both wrappers support focused stages and respect `BLENDER`. All Blender launches use `--python-exit-code 1`; Python exceptions stop the pipeline. Ranger/elf each have independent profile/rig config, references, atlas, clips and review reports. See [RANGER.md](RANGER.md), [ELF.md](ELF.md), and [CHARACTERS.md](CHARACTERS.md) for new folders.

Builds reproduce saved measurements and images. Export order/simplification can vary across Blender versions; image generation is not deterministic. Verified environment: Blender 5.2.1, Three.js 0.180.0, Python 3.14, NumPy 2.5.3, Pillow 12.3.0.

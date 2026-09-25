# Character Lab — instructions for the next agent

This directory is a standalone, working example of image-reference modeling, UV projection, rigging and transfer of downloaded animation. Read `README.md`, `docs/WORKFLOW.md`, `docs/FACE.md`, and `docs/VALIDATION.md` before changing it. The user wants a convincing visible result and a reproducible workflow, including with a weaker coding model.

## Preserve the proven quality

Follow the **Ověřený pracovní cyklus pro dalšího agenta** at the start of [docs/WORKFLOW.md](docs/WORKFLOW.md). It records the successful iteration order and a symptom-to-fix table for all three characters. Before experimenting, preserve the current exported model, relevant code/configuration, atlas and camera-matched renders under a new baseline directory. Keep a change only after numeric checks pass and the visible improvement survives the other required views and representative motions. If it does not improve the result, restore that attempt's code/configuration and rebuild its outputs together. Do not overwrite historical comparison assets or present a new camera/lighting setup as evidence of a projection fix.

Before accepting a newly calibrated character, compare its **head width and height in the whole-body view** with the accepted original knight using the same camera, pose and lighting; also inspect front, three-quarter and profile face, ear roots and neck. Numeric topology/skin PASS cannot detect a head that feels too narrow. The ranger and night elf needed separate width corrections after this was missed; see [review/head-width.html](review/head-width.html), [docs/RANGER.md](docs/RANGER.md) and [docs/ELF.md](docs/ELF.md). Preserve the before views, rebuild geometry → rig → motion → validation, and review motion before keeping a correction.

Document the cause, exact files/settings changed, reproduction commands, measured results, inspected views/clips and remaining limitations. Numeric PASS, a successful HTTP request and a good front screenshot are three different observations; none substitutes for the full visual check. Do not start another generation or redesign merely to reproduce the existing accepted result.

## Start here

1. Work inside this directory. Do not depend on any parent project, shared `.venv`, secret file in another repository, or global Three.js install.
2. For the supplied characters, reuse `references/`. A rebuild is offline and does not require Gemini or another image generation call. The default pipeline builds the original knight; the ranger and elf have separate workflows in `docs/RANGER.md` and `docs/ELF.md`. Read the relevant document before modifying either one.
3. Run `npm ci`. For geometry, create `.venv` with `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`. Blender is a separate installed application; set `BLENDER` if it is not on PATH or in the standard macOS location.
4. Run `.venv/bin/python tools/pipeline.py build`. Stop on any failing stage and fix the actual failure; do not replace an output with a placeholder.
5. Run `npm run serve`, then inspect `http://localhost:8770/`. If that port is already serving this project, reuse it. An HTTP success alone is not visual verification.

## Deliverables and acceptance

- `assets/knight-animated.glb`: actual mesh, embedded texture, 27 skin joints, 214 named clips.
- `assets/knight-animated.blend`: editable armature and all actions; idle is active. `knight-rigged.blend` preserves 29 separate mesh pieces for weight editing.
- `animations/source/`: complete downloaded free archives and extracted files, including original licenses and root-motion variants where supplied.
- `animations/retargeted/`: 214 small motion-only GLBs for this exact target hierarchy. They do not contain a character mesh.
- `review/validation.json`: numeric validation. Must pass. At least 5 real idle clips and 5 distinct downloaded run clips must remain available.
- `review/input-validation.json` and `review/projection.json`: input validity/source fingerprints and 9 semantic projection guards. These must pass alongside final validation. The original knight currently has 17 profile types and 120 measured sections.
- Motion-only validation must open the 214 actual files and compare their target hierarchy and exact curves with the matching final GLB clips. A file count alone is insufficient. The Blender export report must contain the same action count.
- Browser inspection: idle, KayKit run, Quaternius jog/sprint, jump, a gesture, skeleton, front/profile/three-quarter face, and before/after comparison. Check console errors.
- After face or projection changes, render `tools/render_faces.py` in Blender and compare all nine `review/face-*.png` images: historical `before`, this iteration's `baseline`, and current `after`, each front/profile/three-quarter. A front-only screenshot is insufficient. Preserve `assets/knight-before-face.glb` and `assets/knight-before-projection.glb` as separate comparison assets.
- The viewer defaults to the knight and offers a second character selector. Counts, reference/download links and camera framing must match the selected asset. Static experiments must not display a fictional animation library. Recheck model switching as well as individual motion controls.
- `assets/ranger-animated.glb/.blend`: independent second character, currently 57,584 triangles, 29,477 GLB vertices, 27 bones and 214 clips/actions. Its 214 motion-only files and catalog are in `animations/ranger/`; `review/ranger/validation.json` must pass. Keep the knight's and ranger's target-specific clips separate.
- `assets/elf-animated.glb/.blend`: independently measured night elf with light armor and a cloak, no bow. Current export has 61,188 triangles, 31,242 GLB vertices, 27 bones and 214 clips/actions. Its separate clips and catalog are in `animations/elf/`; `review/elf/input-validation.json`, `review/elf/projection.json` and `review/elf/validation.json` must pass. Keep all three target-specific motion outputs separate.
- Update documentation and actual measured counts after changes. Distinguish numeric checks, visual checks and remaining limitations.

## How to edit safely and effectively

The existing profiles are measurements for THIS image, not a universal auto-modeler. For a new character, read the images, update calibration/crops and remeasure each silhouette in `config/profiles.json`. Each row is `[imageY, frontLeftX, frontRightX, sideFrontX, sideBackX]`; rows must have strictly increasing Y, finite coordinates and positive width/depth inside the calibrated image. `tools/model.py` still contains the front center, depth origin, height, relief features and rear-view registration: these must also match a new image. Do not pretend that replacing the PNG alone reconstructs a new character. Keep the supplied ranger's independently calibrated files separate from the knight.

For a face seam, first align landmarks and geometry. Edit `config/face.json`: vertical correspondences, depth warp, section exponent and blend mask. Preserve one eye and one eyebrow per visible side. Broad blur is not a cure for double eyes. Keep old output for a camera-matched comparison. See the successful recipe and its limits in `docs/FACE.md`.

For an ear on a pauldron, armor on the jaw or a sleeve on a bracer, edit **source visibility**, not merely the blending width. `config/projection.json` describes which source pixels actually belong to each part, independently of its depth profile. Rows are `[imageY, validLeftX, validRightX]`; optional excluded polygons remove openings exposing another part. `front-fallback` rejects invalid side pixels and uses the same part's front projection. `clamp-valid-source` extends nearby valid material into an occluded region. Keep facial landmark warping before the side-face mask. Inspect front, side and rear sources: fixing one view can reveal contamination from another.

The projection configuration binds the original and rear raw images by SHA-256 and checks calibration dimensions. A mismatch requires remeasurement; never just update the hash to bypass the guard. Save both raw output and metadata for new references. Add explicit allowed/forbidden source points for observed regressions, and distinguish a passing mask check from visual image quality. Hidden material extension is an authored approximation, not recovered anatomy.

White silhouette outlines need source padding as well. `frontBackgroundGuard` detects neutral studio background connected to the image boundary and includes its 2 px fringe. `sample_front` moves samples only to visible material in the same image row and the same part's measured interval. It does not blur the entire reference. Inspect `frontBackgroundPadding` in `review/projection.json`: report repaired samples, remaining background and rows with no valid source separately. A base-color fallback for absent material is an approximation, not recovered texture.

For anatomy, edit `config/rig.json` in Y-up meters, then rebuild rig and motion. Names and hierarchy match the retarget mappings. If you add a part, add its weight recipe in `tools/rig_character.py`; the script deliberately fails on unknown parts. Keep rigid armor mostly rigid and normalize all weights.

L/R labels are anatomical: in our Y-up, forward +Z frame, paired L parts have centroids at +X and R parts at −X. Both rig scripts enforce this before weighting. The knight and ranger trace opposite sides of their front images; copying the same suffix convention without checking geometry previously produced a badly deformed ranger idle despite numeric skin tests passing. Preserve the centroid guard and verify actual idle and running after any naming or weighting change.

Animation keyframes must come from the downloaded Quaternius/KayKit files. Do not replace them with sinusoidal homemade gait or rename duplicates to meet the requested count. Rest-pose correction, retarget IK and derived tabard motion are permitted adaptations, not new source animation. Download only the official free archives through the included tool. Do not describe the free packs as all paid animations ever made by those authors.

Use the shared retarget/export/validation scripts through `tools/character_paths.mjs`; `CHARACTER_LAB_CHARACTER` chooses `knight` (default), `ranger` or `elf`. Each non-default wrapper sets this value and imports the common implementation, without rewriting source code. Validate each posed mesh's extent separately from whole-clip root travel. The downloaded ground-spawn motion begins underground; preserve the source motion and document its scene requirements instead of deleting it or treating root travel alone as an exploded skin.

Do not use local target bone quaternions as anatomical directions: the GLB exporter can canonicalize axes. The arm correction uses joint positions to align A-pose with T-pose. The leg IK works relative to each hip; a root-relative constant offset overextends KayKit legs because its hip placement differs. Keep these corrections unless a measured improvement replaces them.

## Commands for a focused iteration

```sh
.venv/bin/python tools/pipeline.py geometry  # reference -> input validation -> masked atlas -> static GLB/.blend
.venv/bin/python tools/pipeline.py rig       # static .blend -> fitted skeleton and skin
.venv/bin/python tools/pipeline.py motion    # downloaded clips -> GLB, clip files, animated .blend
npm run validate
```

Geometry changes require all four steps, in order. A texture change also requires re-export because the GLB embeds the image. `npm run build` runs all four. Invoke the required face/projection QA renders after such changes with `blender -b -t 4 --python tools/render_faces.py` (or the configured Blender executable). These commands target the knight; use the separate commands in `docs/RANGER.md` for the ranger.

Both pipeline entry points pass `--python-exit-code 1` to Blender so Python exceptions stop the build. Preserve this behavior when adding a stage; a zero exit code after a failed Blender script must not advance the pipeline.

To reproduce the second character: `.venv/bin/python tools/ranger_pipeline.py build`, followed by `.venv/bin/python tools/ranger_pipeline.py render`. Available focused stages are `geometry`, `rig`, `motion`, `validate`, and `render`. Its existing `references/ranger/turnaround.png` is one generated ImageGen image with three views; reuse it offline and retain its metadata. Do not claim that its generation used Gemini or that a billed price was measured.

To reproduce the third character: `.venv/bin/python tools/elf_pipeline.py build`, followed by `.venv/bin/python tools/elf_pipeline.py render`. Reuse its single saved ImageGen three-view reference and metadata; see `docs/ELF.md`. The elf's `headWidthScale` and the ranger's separate `headWidthScale` are authored proportion corrections, not reusable constants for an arbitrary future image.

## Gemini and reporting

The image-generation helper is separate and optional. Use only `GEMINI_API_KEY` or this directory's `.env`; never print a key or commit it. The supplied assets already exist. If a new reference is requested, the explicit command is in `docs/WORKFLOW.md`; the prompt is in `config/turnaround-prompt.txt`. Keep raw output and metadata. One three-view sheet is one output image, not three API images. Verify current prices before quoting new prices. Never claim a measured bill from a price estimate.

Do not claim perfect production rigging or photogrammetric reconstruction. This is a stylized, manually calibrated reconstruction with projection texture, rigid glove shapes and simple cloth bones. Props, individual fingers, facial expressions, cloth collision and scene-specific foot contacts need additional work for production use.

## Suggested prompt for a weaker model

> Read AGENTS.md and the linked docs, especially the proven iteration cycle at the start of docs/WORKFLOW.md. First reproduce the selected supplied character offline and open the animated viewer. Save a separate baseline before editing. Fix one identified cause at a time: geometry, landmark correspondence, source ownership, then blending. Before rigging a new character, compare head width and height against the accepted knight in camera-matched whole-body and face views. Verify idle, KayKit run, Quaternius jog/sprint, jump, gesture, skeleton and the face from front/three-quarter/profile; check anatomical L/R in motion. Inspect ear/shoulder, jaw/collar, hair/rear head and sleeve/bracer boundaries. Compare saved baselines with the same camera, pose and lighting. Rebuild every dependent stage and report actual validation separately from visual checks. Keep only a demonstrated improvement; otherwise restore the attempt and rebuild. Update documentation with commands, measured counts and limitations, and leave the viewer open. For the ranger use docs/RANGER.md and its own calibration. Do not invent source motions or regenerate the reference unnecessarily.

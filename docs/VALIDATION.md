# Validation and known limits

The knight's final report is `review/validation.json`; input, projection, construction, skin and Blender-action reports are beside it. `npm run validate` checks the final knight assets. The complete pipeline verifies inputs/outputs, rebuilds changed stages and always runs final validation. `--force` disables stage caching. Ranger and elf have their own reports and commands.

## Numeric results

| Character | Triangles | GLB vertices | Joints | Clips / motion files / Blender actions | Poses evaluated |
|---|---:|---:|---:|---:|---:|
| Knight | 54,288 | 27,704 | 27 | 214 / 214 / 214 | 1,284 |
| Ranger | 57,584 | 29,477 | 27 | 214 / 214 / 214 | 1,284 |
| Elf | 61,188 | 31,242 | 27 | 214 / 214 / 214 | 1,284 |

Each target retains **32 real idle clips and 8 distinct runs**, exceeding the 5+5 minimum without renamed duplicate motions. Short pose clips are included; the total does not mean 214 locomotion cycles.

### Knight

- Input PASS: 17 profile types, 120 measured sections, 1907×1280 calibration. Checks include finite coordinates, increasing section Y, positive width/depth, image bounds, face correspondences and nonzero bone lengths.
- Raw front/rear sources and configs have SHA-256 fingerprints. `model.py` rejects mismatched reference hashes before applying old projection masks.
- Projection PASS: all nine allowed/forbidden source-coordinate guards pass. Forbidden side weight is zero for pauldrons/bracers; jaw/hair use constrained valid regions.
- Front background padding covers 27 lofts: 641,518 repaired samples, 27,648 samples without visible same-row material filled with base color, and zero remaining background samples outside that fallback. These are atlas patch samples, not unique reference pixels. Missing material remains an approximation.
- All 29 original pieces have zero boundary/non-manifold edges.
- Maximum weight-sum error is approximately `8.94e-8`; ankle IK target error is below `1e-5 m`. This is not the accuracy of contact with a scene floor.
- Largest sampled individual posed-body span is approximately 3.127 m.

### Ranger

`review/ranger/validation.json` passes. All 214 files in `animations/ranger/retargeted/` match the ranger target. Maximum weight-sum error is about `2.98e-8`, ankle IK error below `1e-5 m`, and maximum posed-body span about 2.937 m.

The head was widened 10%, from 0.311 m to 0.342 m, after whole-body review against the knight. Matching before/after views are on the [head comparison page](../review/head-width.html). Rig, clips and validation were rebuilt afterward. The legacy ranger does not have the knight/elf-style standalone input/projection reports; do not claim it does. See [RANGER.md](RANGER.md).

### Elf

Input PASS: 17 profile types, 106 measured sections, 1536×1024 image and matching source SHA-256. Projection PASS: nine explicit source points around ear, face, hair, armor, cloak and background. These points do not verify every atlas transition.

Final validation passes, including all 214 actual files in `animations/elf/retargeted/`. Maximum weight-sum error is about `6.71e-8`, ankle IK error below `1e-5 m`, largest posed-body span about 3.130 m. The accepted head width is 0.274 m, compared with 0.189 m before correction. See [ELF.md](ELF.md).

## What is actually checked

The validator opens every motion-only GLB. Each must contain one correctly named clip, no mesh or texture, and the exact target node hierarchy, channels, interpolation, time samples and curve values of the corresponding final animated GLB clip. This proves consistency with the retargeted result, not identity with unadapted source data. Catalog, GLB clip and Blender action counts must agree.

All accessor values must be finite, times strictly increase, quaternions and weights are normalized, and topology reports must show closed manifold pieces. Three.js evaluates six poses for each of 214 clips with actual skinning, checking sampled vertices for finite coordinates and unreasonable posed-body extent. Root trajectory is reported separately: large travel alone is not skin explosion.

## Visual comparisons

`tools/render_faces.py` produces nine actual GLB renders with matching cameras and lights: historical `face-before-*`, projection `face-baseline-*` and current `face-after-*`, each front/three-quarter/profile. See [the comparison page](../review/faces.html) and [FACE.md](FACE.md).

Mask tests prove adherence to authored source regions, not perfect mask boundaries or recovered hidden anatomy. Likewise, evaluating 1,284 poses proves numeric consistency, not that every frame was visually judged.

### Recorded reviews — September 25, 2026

The original acceptance review inspected idle, KayKit `Running A`, Quaternius `Jog Fwd Loop`/`Sprint Loop`, KayKit `Jump Full Short`/`Waving`, skeletons and extreme scrubbed poses. Ranger motion was reviewed after correcting swapped anatomical sides. Front/three-quarter/profile faces, the knight's two historical comparisons, ranger ear/collar boundaries and both widened heads were inspected. Offline review included nine knight face comparisons, six knight body directions and seven ranger views. The elf review added body front/three-quarter/profile/back and three face angles. Browser consoles had no errors or warnings.

The workflow/viewer update repeated representative motion, skeleton and face-camera checks on all three characters, model switching and historical comparison loading. A temporary folder containing a known knight fixture was discovered automatically, displayed correctly as a static model, then switched to its own 214-clip animated export. It was removed from the project after testing. The fixture was an integration test, not a newly generated character.

All three final GLBs and atlases stayed byte-for-byte identical to the preserved pre-optimization baseline. The viewer's interface, neutral background and labels changed; those presentation changes are not evidence of a projection improvement. The reference/modeling algorithms were not altered. Performance and test evidence are recorded in [PERFORMANCE.md](PERFORMANCE.md).

## Remaining limits

- Every frame of every clip has not been manually reviewed. Extreme poses, sitting, climbing and combat require a scene and suitable props.
- IK adapts limb lengths without terrain contact or automatic foot locking. Sliding and floor penetration can remain.
- Broad armor volumes may intersect each other or the body in extreme bends; there is no armor collision system.
- Four derived cloth bones are not cloth simulation and do not provide leg collision. The historical elf cloak can intersect moving legs.
- Gloves are solid palm/thumb shapes without individual finger rigging. Tool/weapon animations play without those props.
- KayKit scale-to-zero spawn/disassembly effects are not fully reproduced; the transfer preserves primarily humanoid poses. Original files remain available.
- `KAY_Skeletons_Spawn_Ground` starts underground in the source. Its root can travel more than 12 m without an exploded posed mesh, and it may leave the standard viewer frame. Preserve the motion and configure its scene/camera.
- Target catalogs use the chosen in-place sources. All supplied raw root-motion variants remain stored but are not duplicated in the viewer library.
- Source lighting and details remain painted. Face fixes reduce doubled landmarks and seams; this is not a scan, facial performance rig or film close-up asset.
- A default whole-body camera can crop the top of a high jump; zoom out to inspect the full trajectory.

## Recheck after a change

Run the relevant pipeline, then play the named representative clips several times. Inspect hands in running, knees in jumping, shoulders in waving and armor during bends. Toggle Skeleton, pause and scrub. In Rest pose compare front/three-quarter/profile, rear, ear/shoulder, jaw/collar, hair and sleeve/bracer boundaries; use Clay to expose geometry. Keep comparison cameras identical and check console errors.

Record numerical validation, actual browser inspection and remaining limitations separately. An HTTP 200, numeric PASS and an attractive front screenshot are distinct observations.

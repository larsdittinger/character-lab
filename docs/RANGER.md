# Woodland Ranger: independent second calibration

The ranger has her own reference, measured silhouettes, proportions, atlas, fitted skeleton and the same 214 downloaded source motions. She is not the knight's geometry with a replacement texture.

## Reference provenance

One built-in ImageGen call produced **one 1536×1024 image with three views**. No new Gemini request was used, and no measured invoice or billed price is claimed. The immutable original is [turnaround.png](../references/ranger/turnaround.png); prompt, provenance and SHA-256 are in [metadata](../references/ranger/turnaround.json) and [the saved prompt](../config/ranger-prompt.txt).

## Offline reproduction

Use this project's `.venv`, requirements, `node_modules` and Blender installation. No new image generation or download is needed.

```sh
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/ranger_pipeline.py render
npm run serve
```

Select **Woodland Ranger** at http://localhost:8770/. Focused stages: geometry, rig, motion, validate, render. Geometry/texture changes require dependent stages because the atlas is embedded. Add `--force` for a full uncached reproduction. Blender script failures propagate through `--python-exit-code 1`.

| Output | Contents |
|---|---|
| `assets/ranger-static.glb/.blend` | Static model; 29 separate closed Blender pieces |
| `assets/ranger-rigged.glb/.blend` | Fitted skeleton and skin weights; editable separate pieces |
| `assets/ranger-animated.glb/.blend` | 214 clips/actions; idle active on open |
| `animations/ranger/retargeted/` | 214 motion-only GLBs for this exact hierarchy |
| `animations/ranger/catalog.json` | Source name, pack, duration and clip parameters |
| `review/ranger/validation.json` | Actual numeric validation |

Shared retarget/export/validation uses `CHARACTER_LAB_CHARACTER=ranger`. It preserves the common A/T rest correction, hip-relative IK and downloaded curves while fitting independent target joints and limb lengths.

## Measured calibration

[ranger-profiles.json](../config/ranger-profiles.json): front center X=317, side origin X=773, rear center X=1220, top Y=17, ground Y=959, authored height 2.5 m, scale `2.5 / 942`. Y is up and +Z forward. [ranger-rig.json](../config/ranger-rig.json) contains measured joints in meters.

Paired sections are traced from the right side of the front image: **anatomical L, +X**. The knight's measurements start on the opposite image half. Copying suffixes once assigned weights to opposite limbs: numeric skin validation passed, but idle visibly deformed. The final rig asserts L centroids on +X and R on −X before weighting. Real motion review is essential.

The three reference silhouettes are not perfectly consistent. `rearHeadRegistration` stores rear hair width by height; simply mirroring front pixel X into the rear painted studio background onto the crown. The side face has separate eye/nose/mouth/chin correspondences and a small depth correction.

An early separate hair volume overlapped the forehead. The accepted version uses one continuous head including the swept hair. Historical `face-first-3q.png` and `face-first-side.png` remain in `review/ranger/`; current front/three-quarter/profile renders use matching cameras and lighting.

## Projection ownership

- Ears are separate closed volumes attached to the head. Their front/side surfaces sample the corresponding reference regions. Head texture underneath does not retain another sharp ear.
- Shoulder pieces exclude side projection through occluding head/neck regions. Front/rear detail and authored side color fill unobserved surfaces.
- Hair masks select actual copper hair. Missing edge samples extend nearby valid hair pixels rather than studio gray or skin. This is projection padding, not another generated image.
- Upper trousers are hidden by the tunic in the source. Authored dark cloth extends above the belt, and a separate leather side part covers the hip, avoiding an exposed flat top edge.
- The atlas is 2000×3168 with padded UV islands.

### Targeted ear and collar correction

`assets/ranger-before-detail.glb` preserves the starting state. Matching face views, code and profiles are in `review/ranger/baseline-resume/`. The [six-view comparison](../review/ranger/detail-comparison.html) uses the same geometry and cameras before/after.

The old rectangular mask removed the ear center but missed its bright upper arc; its hard edge also produced a brown strip below the separate ear. The accepted changes in `tools/ranger_model.py` are:

1. **Front head texture:** soft elliptical ear masks centered at `(365,108)` and `(269,108)` px with radii `(13,23)`. Transition `smooth((radius-.85)/.28)`. Fill from nearby valid material at X=351 or 283 at the same height. Separate ear meshes still receive actual ear color.
2. **Side head texture:** ellipse centered `(779,105)`, radii `(17,23)`, mask `1-smooth((radius-.84)/.30)` includes the upper arc. Fill blends neighboring skin near X=755 with valid hair near X=806. Hair influence varies over X=774–787 and Y=89–101. This removes a foreign feature beneath the real ear without blurring the eye or whole face.
3. **Collar:** constant X=790 stretched one image column around the neck. Restore two-dimensional `(profileX,imageY)` sampling inside rows `[145,745,804]`, `[153,749,808]`, `[161,751,813]`, `[175,743,820]`, `[190,731,826]`, `[205,719,829]`, inset 3 px. Cream trim is valid material and must not be classified as gray background.

The bright extra ear arc and hard brown rectangle disappeared in three-quarter/profile views; cream trim follows the reference's diagonal shape. Front eyes/mouth, proportions, rig and weights stayed unchanged. The correction was accepted after all three views, not a front-only inspection. The geometry/UV equivalence record is `review/ranger/detail-review.json`.

For another reference, remeasure these masks. Preserve baseline views first, rebuild and render, then reload the actual animated GLB to see its updated embedded atlas. Numeric curve validation does not judge the visual ear transition.

## Head-width correction

A whole-body comparison with the accepted knight revealed a narrow-looking ranger head. GLB, profiles, script, atlas and prior renders were saved in `review/ranger/baseline-2026-09-25-head-width/`. `headWidthScale: 1.10` widens face geometry, moves the separate ears by the corresponding distance and applies half the correction to the neck. Source landmark coordinates and texture sampling remain unchanged.

Maximum face width changed from **0.311 m to 0.342 m**. The [matching-camera comparison](../review/head-width.html) includes front/three-quarter/profile and whole-body views beside the knight. Geometry, rig, all clips and validation were rebuilt, followed by idle, KayKit running, Quaternius jogging/sprinting, jumping and waving in the viewer. No browser console errors were found. A future character needs this comparison before transferring 214 clips; one numeric ratio cannot replace judgment about style.

## Measured validation

Final GLB: **57,584 triangles, 29,477 vertices, 27 joints, 214 clips**. Blender retains 29 pieces in static/rigged files and 214 actions in the animated file. All 29 pieces have zero boundary and non-manifold edges. There are 32 real idle clips and 8 runs.

The validator evaluates 1,284 skinned poses and compares all 214 real motion files against the final hierarchy and exact curves. Maximum weight-sum error is about `2.98e-8`, quaternion error `4.70e-8`, ankle IK error `9.87e-6 m`, and individual posed-body span about 2.94 m.

This character exposed an earlier validator bug: a source underground spawn's total root travel, over 12 m with ranger proportions, was mistaken for exploded geometry. The shared validator now measures each posed body separately and reports travel independently. The source motion was preserved.

## Visual review and limits

Static review includes body front/three-quarter/side/back and three face views from the actual exported GLB. Remaining painted shading/stretching near hair and ear roots is visible at close range. Ears are simple closed lofts, not anatomical retopology. Source lighting is painted into the atlas, and a whole-body sheet limits facial pixel detail.

Gloves have no individual fingers, and there is no facial rig. Skirt bones provide no cloth collision; leather panels and arms can intersect in extreme poses. Numeric PASS does not certify every frame of all clips. Combat, sitting, work and foot contact need scene-specific inspection with props. This is an independent calibration, not proof of universal automatic image reconstruction.

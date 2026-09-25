# Face alignment and projection ownership

The original texture showed a second eye and eyebrow on the temple. Landmark alignment and face volume reduced that error. A later review found a different problem: **an ear on the pauldron and gold armor along the jaw**. Blur cannot correct source pixels belonging to another body part.

## Face alignment

1. **Volume:** cross-section exponent 1.65, 100 vertical samples before simplification, and small nose, eye-region and lip relief.
2. **Vertical correspondence:** front eye Y=165 maps to side Y=162; nose 194→190, mouth 216→213, lower chin 258→255.
3. **Depth correspondence:** the side sample shifts by height: +7 px at the eyes, +8 px at the nose, falling to zero at the chin.
4. **Detail and color:** Laplacian bands with radii 0, 1.5, 5 and 16 px use a narrower transition for sharp features and a wider one for color.

These settings are in `config/face.json`. The subsequent source-ownership correction preserves geometry, the rig and the measured `config/profiles.json`.

## Correcting contamination between parts

`config/projection.json` describes visible source regions independently of geometric depth profiles. Rows are `[imageY, validLeftX, validRightX]`; excluded polygons can remove openings.

At Y=182, the first pauldron depth section spans X=1188–1240, but the side image contains an ear there. Visible gold armor starts around X=1242. At Y=231, visible beard ends around X=1156; farther back is shoulder armor, not jaw.

- **Pauldrons and forearm plates:** reject side pixels belonging to ears, beard, sleeves or gloves. Use the same part's front projection, with a narrow transition on the valid side.
- **Jaw:** clamp side coordinates to visible face/beard material and extend nearby valid color into the occluded region.
- **Rear hair and nape:** sample hair, excluding the side pauldron and rear collar.
- **Boundary:** inset 2 px with a 3 px transition. This is not whole-image blur.

Hidden anatomy is not recovered. Extended beard/hair color is an authored approximation. The knight's ears remain largely painted; ranger and elf have separate ear geometry.

`review/projection.json` records nine semantic guards, repaired/rejected sample counts and remaining forbidden side weight. These prove that authored masks are respected, not that every measured boundary is visually correct. Source SHA-256 checks prevent silently applying old masks to a replacement image.

## Comparison

In the viewer, choose **Rest pose**, a face camera and **Projection comparison**. Switch between the current model, the projection baseline and the historical face without changing the camera.

| View | Before source-ownership correction | Current |
|---|---|---|
| Front | ![Before, front](../review/face-baseline-front.png) | ![After, front](../review/face-after-front.png) |
| Three-quarter | ![Before, three-quarter](../review/face-baseline-3q.png) | ![After, three-quarter](../review/face-after-3q.png) |
| Profile | ![Before, profile](../review/face-baseline-side.png) | ![After, profile](../review/face-after-side.png) |

The [comparison page](../review/faces.html) also includes the historical doubled landmarks. Preserve `assets/knight-before-projection.glb` and `assets/knight-before-face.glb` separately. `tools/render_faces.py` produces nine images: historical, iteration baseline and current, each from front/three-quarter/profile.

## Repeat the method

Align eyes, nose, mouth and chin first. Check the untextured silhouette from three views. Mark the actually visible source material for each part; geometric depth does not encode visibility. Only then tune transitions and blend valid colors. Each visible side should have one eye, eyebrow and ear. Inspect neighboring parts: jaw/collar, ear/shoulder and sleeve/bracer.

A new image requires new geometry measurements, correspondences and masks. Replacing a PNG is not new modeling. Film close-ups would require facial retopology, separate eyes and controlled albedo without painted lighting.

## Technical background

Separating valid view selection from seam treatment follows the general principle in [Waechter, Moehrle and Goesele: Let There Be Color!](https://download.hrz.tu-darmstadt.de/pub/FB20/GCC/paper/Waechter-2014-LTB.pdf). This project uses authored masks, not that paper's automatic photogrammetric algorithm. UV padding limits filtering/mipmap seams, as described in the [Blender baking margin documentation](https://docs.blender.org/manual/en/latest/render/cycles/baking.html); padding cannot correct the wrong source content.

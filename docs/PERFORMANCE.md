# Build performance without reducing output quality

The September 25, 2026 update changes orchestration and binary-buffer assembly. It does not reduce geometry density, atlas resolution, 30 Hz motion sampling or validation coverage.

## Changes

`tools/glb.mjs` previously copied the entire growing binary buffer for every appended accessor. That repeatedly copied the embedded atlas and all earlier animation channels. It now accumulates aligned chunks and assembles them once at write/read time, producing identical bytes.

`tools/build_cache.py` caches geometry, rig, retargeting, motion-file export and Blender-action export separately. Cache reuse requires matching SHA-256 of all declared inputs **and existing outputs**, plus the recorded runtime context. Deleted or corrupted outputs trigger the corresponding stage. Missing inputs cannot hit the cache. Failed stages never receive a success stamp. A per-character lock prevents overlapping builds from mixing outputs.

Runtime context includes Python, Node, NumPy/Pillow and the Blender executable identity. Each stage's source scripts and dependency lockfile are inputs. Reference hashes, config, previous-stage artifacts and downloaded sources are included where relevant. `review/<character>/.build-cache/` and locks are ignored by Git.

The final validator always runs and still opens all 214 motion-only files and evaluates 1,284 poses. `--force` bypasses the cache. Timing is recorded in the character's `review/build-timing.json`.

## Measurements and output equivalence

[review/performance.json](../review/performance.json) records measured runs and before/after SHA-256 values. The original full knight build took **14.75 s**. Repeated verified-cache builds took approximately **1–2 s** including fresh final validation. Full-build observations varied with machine load; the first optimized run was about 19.2 s and a later uncached run about 11.2 s. These are local observations, not a promised speedup for every full reconstruction.

The knight, ranger and elf **animated GLBs and projection atlases are byte-for-byte identical** to the preserved baseline. Numerical results remain 54,288 / 57,584 / 61,188 triangles, 27 joints and 214 clips/actions per character. Blender files were re-exported with the same actions; their binary container metadata need not be byte-identical.

The baseline is `review/baseline-2026-09-25-151241-workflow/`, containing original scripts/config, GLBs, atlases, existing camera-matched renders and measured baseline time. Historical comparison assets were not replaced.

## Reproduce

```sh
# Full recomputation, then a cache-hit build:
.venv/bin/python tools/pipeline.py build --force
.venv/bin/python tools/pipeline.py build
# The other target-specific pipelines use the same cache and exporter:
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/elf_pipeline.py build
npm test
```

Offline tests cover cache hits, changed inputs, missing/corrupt outputs, failed-stage invalidation, character discovery, incomplete GLBs, invalid manifests, path confinement, generation/edit request structure, exact raw image preservation, usage metadata and duplicate-paid-request prevention. A binary test covers aligned chunks, a read before the final write, 500 appended channels and exact round-trip bytes.

A temporary `workflow-check` folder was tested with an existing knight fixture through shared motion export and validation: 214 actual target-specific files and 214 Blender actions passed. The browser automatically discovered its static and animated exports with correct links and controls. It was not a new generated character and was removed afterward.

## Limits

Caching speeds up repeated builds from unchanged measurements. It does not automate the visual calibration of a new image, make image generation free, or prove that an uninspected new reference will achieve the same quality. Editing reference geometry or masks still invalidates dependent stages and requires visual review. For projection changes, preserve baselines and render the prescribed camera-matched face views.

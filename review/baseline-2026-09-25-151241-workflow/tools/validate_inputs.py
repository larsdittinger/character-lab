"""Fail before modeling if measured reference coordinates are malformed.

These checks establish valid calibration data, not visual or anatomical correctness.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]


def validate_profiles(profiles, size):
    width, height = size
    for name, rows in profiles.items():
        p = np.asarray(rows, dtype=float)
        if p.ndim != 2 or p.shape[1] != 5 or len(p) < 2:
            raise ValueError(f'{name}: expected at least two [y,left,right,front,back] rows')
        if not np.isfinite(p).all():
            raise ValueError(f'{name}: coordinates must be finite')
        if not (np.diff(p[:, 0]) > 0).all():
            raise ValueError(f'{name}: image Y must be strictly increasing')
        if not ((p[:, 1] < p[:, 2]) & (p[:, 3] < p[:, 4])).all():
            raise ValueError(f'{name}: silhouette width/depth must be positive')
        if not ((p[:, 0] >= 0) & (p[:, 0] < height)).all():
            raise ValueError(f'{name}: image Y outside reference')
        if not ((p[:, 1:] >= 0) & (p[:, 1:] < width)).all():
            raise ValueError(f'{name}: image X outside reference')


def validate_face(face):
    for xkey, ykey in [('frontY', 'sideY'), ('depthWarpY', 'sidePixelOffset')]:
        x, y = np.asarray(face[xkey], float), np.asarray(face[ykey], float)
        if x.ndim != 1 or y.ndim != 1 or len(x) != len(y) or len(x) < 2:
            raise ValueError(f'{xkey}/{ykey}: mismatched landmarks')
        if not np.isfinite(x).all() or not np.isfinite(y).all() or not (np.diff(x) > 0).all():
            raise ValueError(f'{xkey}: landmarks must be finite and ordered')
        if ykey == 'sideY' and not (np.diff(y) > 0).all():
            raise ValueError('sideY: facial correspondence must preserve vertical order')
    if not 0 <= face['blendStart'] < face['blendEnd'] <= 1:
        raise ValueError('Face blend must satisfy 0 <= start < end <= 1')
    if not 0 < face['crossSectionExponent'] < 5:
        raise ValueError('Invalid face cross-section exponent')
    radii = np.asarray(face['pyramidRadii'], float)
    if len(radii) < 2 or radii[0] != 0 or not np.isfinite(radii).all() or not (np.diff(radii) > 0).all():
        raise ValueError('Pyramid radii must start at zero and strictly increase')


def main():
    report = {'passed': False, 'scope': 'Input validity and source identity; visual correctness requires renders.'}
    try:
        profiles = json.loads((R / 'config/profiles.json').read_text())
        face = json.loads((R / 'config/face.json').read_text())
        calibration = json.loads((R / 'references/calibration.json').read_text())
        size = Image.open(R / 'references/calibration.png').size
        if list(size) != calibration['workingSize']:
            raise ValueError('Working reference size differs from saved calibration')
        validate_profiles(profiles, size)
        validate_face(face)
        bones = json.loads((R / 'config/rig.json').read_text())['bones']
        for name, bone in bones.items():
            head, tail = np.asarray(bone['head'], float), np.asarray(bone['tail'], float)
            if head.shape != (3,) or tail.shape != (3,) or not np.isfinite([head, tail]).all() or np.linalg.norm(tail - head) < 1e-6:
                raise ValueError(f'{name}: invalid or zero-length bone')
        inputs = ['references/gemini-original.png', 'references/knight-back.png', 'config/profiles.json', 'config/face.json', 'config/rig.json']
        if (R / 'config/projection.json').exists():
            inputs.append('config/projection.json')
        report.update(passed=True, profileTypes=len(profiles), measuredSections=sum(map(len, profiles.values())),
                      referenceSize=size, sha256={f: hashlib.sha256((R / f).read_bytes()).hexdigest() for f in inputs})
    except (ValueError, KeyError, OSError, TypeError) as error:
        report['error'] = str(error)
    (R / 'review/input-validation.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

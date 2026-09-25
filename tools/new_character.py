"""Create an isolated character workspace; never copy another character's calibration."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def create_character(name, title, root=ROOT):
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', name) or name in {'knight', 'ranger', 'elf'}:
        raise ValueError('Use a new lowercase character ID: letters, numbers, - or _')
    folder = root / 'characters' / name
    folder.mkdir(parents=True, exist_ok=False)
    for part in ['references', 'config', 'tools', 'assets', 'textures', 'animations/retargeted', 'review', 'accessories']:
        (folder / part).mkdir(parents=True)
        (folder / part / '.gitkeep').touch()
    (folder / 'character.json').write_text(json.dumps({'title': title, 'comparisons': {}}, ensure_ascii=False, indent=2) + '\n')
    (folder / 'config/prompt.txt').write_text((root / 'config/turnaround-prompt.txt').read_text())
    (folder / 'README.md').write_text(f'''# {title}

Reference and measured calibration for `{name}` belong only in this folder.

1. Edit `config/prompt.txt` to describe the new base character, without a cloak or protruding equipment.
2. Generate ONE sheet: `.venv/bin/python tools/generate_reference.py --character {name}` from the project root (`--dry-run` previews the request), or import an original local-model/Gemini/ChatGPT image with metadata following ../../docs/AGENT_START.md. Only the OpenAI image API helper is built in. Use your chosen coding-agent host; a fresh clone contains no API keys.
3. Independently measure silhouettes, face, projection masks and joints into `config/`. Compare head proportions with the accepted knight before rigging.
4. Implement `tools/model.py` (measurement validation, geometry JSON, atlas, input-validation.json, projection.json), `tools/build.py` (Blender static export + topology.json) and `tools/rig.py` (Blender rig + weights). These scripts receive CHARACTER_LAB_DIR pointing here. The shared project is CHARACTER_LAB_ROOT. Do not reuse another image's pixel calibration.
5. Geometry outputs: `assets/static.glb`, `assets/static.blend`, `textures/projection.png`; rig outputs: `assets/rigged.glb`, `assets/rigged.blend`. Shared motion tools create `assets/animated.glb`, `assets/animated.blend`, `animations/catalog.json` and `animations/retargeted/` for the standard 27-joint hierarchy.
6. Build: `.venv/bin/python tools/pipeline.py build --character {name}`. Inspect static views before the full build with `geometry`. Optional `tools/render.py` runs in Blender via `render`.
7. `npm run serve` discovers `assets/animated.glb` or `assets/static.glb` automatically. A reference-only folder is not listed. Optional `face: [x,y,z]` in `character.json` sets a measured face target; otherwise it is fitted from bounds. Optional `reference`, `blend`, `catalog`, `path` and comparison paths are relative to this folder.

Keep baseline GLB/config/atlas and camera-matched views in `review/` before every correction. Keep accessories under `accessories/<id>/`, model separately and attach after the base body is accepted. See ../../docs/CHARACTERS.md and ../../AGENTS.md for acceptance requirements.
''')
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--title', required=True)
    args = parser.parse_args()
    print(create_character(args.name, args.title))

"""Offline character build with verified stage caching and per-character outputs."""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from build_cache import BuildCache

R = Path(__file__).resolve().parents[1]


def main(default_character='knight'):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=['build', 'geometry', 'rig', 'motion', 'validate', 'download', 'serve', 'render'])
    parser.add_argument('--character', default=default_character)
    parser.add_argument('--port', type=int, default=8770)
    parser.add_argument('--force', action='store_true', help='Recompute stages even when their verified cache matches')
    args = parser.parse_args()
    name = args.character
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', name):
        parser.error('Invalid character ID')
    legacy = name in ('knight', 'ranger', 'elf')
    base = R if legacy else R / 'characters' / name
    if not legacy and not (base / 'character.json').is_file():
        parser.error('Unknown character; create it with tools/new_character.py')
    env = dict(os.environ, CHARACTER_LAB_CHARACTER=name, CHARACTER_LAB_ROOT=str(R), CHARACTER_LAB_DIR=str(base))

    def run(*command):
        print('RUN', ' '.join(map(str, command)), flush=True)
        subprocess.run(list(map(str, command)), cwd=R, env=env, check=True)

    if args.task == 'serve':
        run(sys.executable, R / 'tools/serve.py', '--port', args.port)
        return
    if args.task == 'download':
        run(sys.executable, R / 'tools/download_animations.py')
        return
    exe = os.environ.get('BLENDER') or shutil.which('blender')
    if not exe and Path('/Applications/Blender.app/Contents/MacOS/Blender').exists():
        exe = '/Applications/Blender.app/Contents/MacOS/Blender'

    def blender(script, *extra):
        if not exe:
            raise RuntimeError('Install Blender or set BLENDER to its executable path')
        run(exe, '-b', '-t', '4', '--python-exit-code', '1', '--python', script, *extra)

    if args.task == 'render':
        if name == 'knight':
            blender(R / 'tools/render_faces.py')
        elif legacy:
            blender(R / f'tools/{name}_blender.py', '--', 'render')
        else:
            blender(base / 'tools/render.py')
        return
    prefix = f'{name}-' if legacy else ''
    static = ('knight' if name == 'knight' else f'{prefix}static')
    assets = base / 'assets'
    review = R / ('review' if name == 'knight' else f'review/{name}') if legacy else base / 'review'
    motion = R / ('animations/retargeted' if name == 'knight' else f'animations/{name}/retargeted') if legacy else base / 'animations/retargeted'
    catalog = motion.parent / 'catalog.json'
    review.mkdir(parents=True, exist_ok=True)
    # An exclusive per-character lock prevents mixed outputs from overlapping builds.
    lock = review / '.build.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(f'Another build owns {lock}. Remove a stale lock only after checking its PID.')
    with os.fdopen(fd, 'w') as handle:
        handle.write(str(os.getpid()))
    started = time.perf_counter()
    cache = BuildCache(review / '.build-cache', args.force)
    success = False
    try:
        # Runtime versions are part of cache identity, never secret environment values.
        context = {'python': sys.version, 'node': subprocess.check_output(['node', '--version'], text=True).strip(),
                   'blender': [exe, Path(exe).stat().st_mtime_ns] if exe else None,
                   'numpyPillow': subprocess.check_output([sys.executable, '-c', 'import numpy,PIL; print(numpy.__version__,PIL.__version__)'], text=True).strip()}
        shared = [R / 'tools/build_cache.py', R / 'tools/pipeline.py', R / 'package-lock.json']
        if legacy:
            geometry_code = [R / f'tools/{f}.py' for f in (['prepare', 'validate_inputs', 'model', 'build_blender'] if name == 'knight' else [f'{name}_model', f'{name}_blender'] + (['validate_elf_inputs'] if name == 'elf' else []))]
            config = [R / f'config/{file}.json' for file in ['face', 'projection', 'profiles', 'rig']] if name == 'knight' else sorted((R / 'config').glob(name + '-*.json'))
            refs = [R / 'references/gemini-original.png', R / 'references/knight-back.png'] if name == 'knight' else [R / 'references' / name / ('turnaround' + ext) for ext in ['.png', '.json']]
        else:
            geometry_code = [base / 'tools', R / 'tools/model.py', R / 'tools/validate_inputs.py']
            config, refs = [base / 'config', base / 'character.json'], [base / 'references']
        static_outputs = [assets / (static + ext) for ext in ['.glb', '.blend']] + [base / f'textures/{name + "-" if legacy else ""}projection.png', review / 'topology.json']
        if name != 'ranger':
            static_outputs += [review / 'input-validation.json', review / 'projection.json']
        if name == 'knight':
            static_outputs += [assets / 'model.json', R / 'references/calibration.png', R / 'references/calibration.json', R / 'references/knight-turnaround.png', R / 'references/front-calibrated.png', R / 'references/side-calibrated.png', review / 'build.json', review / 'construction.json']
        else:
            static_outputs += [assets / (f'{name}-model.json' if legacy else 'model.json')]
            if legacy:
                static_outputs += [review / 'build.json', review / 'construction.json']

        def geometry():
            if name == 'knight':
                for script in ['prepare', 'validate_inputs', 'model']:
                    run(sys.executable, R / f'tools/{script}.py')
                blender(R / 'tools/build_blender.py')
            elif legacy:
                if name == 'elf':
                    run(sys.executable, R / 'tools/validate_elf_inputs.py')
                run(sys.executable, R / f'tools/{name}_model.py')
                blender(R / f'tools/{name}_blender.py', '--', 'build')
            else:
                for script in ['model.py', 'build.py']:
                    if not (base / 'tools' / script).is_file():
                        raise RuntimeError(f'Measure and implement {base / "tools" / script} for this reference; see docs/CHARACTERS.md')
                run(sys.executable, base / 'tools/model.py')
                blender(base / 'tools/build.py')

        def rig():
            if name == 'knight':
                blender(R / 'tools/rig_character.py')
            elif legacy:
                blender(R / f'tools/{name}_blender.py', '--', 'rig')
            else:
                if not (base / 'tools/rig.py').is_file():
                    raise RuntimeError(f'Implement {base / "tools/rig.py"} after inspecting the static character')
                blender(base / 'tools/rig.py')

        if args.task in ['build', 'geometry']:
            cache.stage('geometry', shared + geometry_code + config + refs, static_outputs, context, geometry)
        if args.task in ['build', 'rig']:
            rig_code = [R / 'tools/rig_character.py', R / f'tools/{name}_blender.py'] if legacy and name != 'knight' else [R / 'tools/rig_character.py'] if legacy else [base / 'tools']
            cache.stage('rig', shared + rig_code + config + [R / 'config/source-rig.json', assets / (static + '.blend')],
                        [assets / (prefix + 'rigged' + ext) for ext in ['.glb', '.blend']], context, rig)
        if args.task in ['build', 'motion']:
            cache.stage('retarget', shared + [R / 'tools/retarget.mjs', R / 'tools/glb.mjs', R / 'tools/character_paths.mjs', R / 'animations/source', assets / (prefix + 'rigged.glb')],
                        [assets / (prefix + 'animated.glb'), catalog, review / 'retarget.json'], context,
                        lambda: run('node', R / 'tools/retarget.mjs'))
            cache.stage('clips', shared + [R / 'tools/export_clips.mjs', R / 'tools/glb.mjs', R / 'tools/character_paths.mjs', assets / (prefix + 'animated.glb')],
                        [motion], context, lambda: run('node', R / 'tools/export_clips.mjs'))
            cache.stage('actions', shared + [R / 'tools/save_animated.py', assets / (prefix + 'animated.glb')],
                        [assets / (prefix + 'animated.blend'), review / 'blender-actions.json'], context,
                        lambda: blender(R / 'tools/save_animated.py'))
        if args.task in ['build', 'validate']:
            start = time.perf_counter()
            for report in ['input-validation.json', 'projection.json']:
                file = review / report
                if name == 'ranger':
                    continue
                if not json.loads(file.read_text()).get('passed'):
                    raise RuntimeError(f'{file}: input/projection validation failed')
            run('node', R / 'tools/validate.mjs')
            cache.timings.append({'stage': 'validate', 'cached': False, 'seconds': round(time.perf_counter() - start, 4)})
        success = True
    finally:
        report = {'character': name, 'task': args.task, 'success': success, 'forced': args.force,
                  'seconds': round(time.perf_counter() - started, 4), 'stages': cache.timings}
        (review / 'build-timing.json').write_text(json.dumps(report, indent=2))
        lock.unlink()
        print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()

"""Rebuild the supplied character offline; run from any working directory."""
from pathlib import Path
import argparse, os, shutil, subprocess, sys
R = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('task', choices=['build','geometry','rig','motion','validate','download','serve'])
p.add_argument('--port', type=int, default=8770)
a = p.parse_args()
def run(*args):
    print('RUN', ' '.join(map(str,args)), flush=True)
    subprocess.run(list(map(str,args)), cwd=R, check=True)
def blender(script):
    exe = os.environ.get('BLENDER') or shutil.which('blender')
    if not exe and Path('/Applications/Blender.app/Contents/MacOS/Blender').exists():
        exe = '/Applications/Blender.app/Contents/MacOS/Blender'
    if not exe: raise SystemExit('Install Blender or set BLENDER to its executable path.')
    run(exe, '-b', '-t', '4', '--python-exit-code', '1', '--python', R/'tools'/script)
if a.task == 'serve': run(sys.executable,'-m','http.server',a.port,'--bind','127.0.0.1')
if a.task == 'download': run(sys.executable,R/'tools/download_animations.py')
if a.task in ['build','geometry']:
    run(sys.executable,R/'tools/prepare.py')
    run(sys.executable,R/'tools/validate_inputs.py')
    run(sys.executable,R/'tools/model.py')
    blender('build_blender.py')
if a.task in ['build','rig']: blender('rig_character.py')
if a.task in ['build','motion']:
    run('node',R/'tools/retarget.mjs')
    run('node',R/'tools/export_clips.mjs')
    blender('save_animated.py')
if a.task in ['build','validate']: run('node',R/'tools/validate.mjs')

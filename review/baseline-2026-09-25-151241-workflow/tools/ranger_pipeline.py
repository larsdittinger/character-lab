"""Offline copper ranger rebuild from its independently measured reference."""
from pathlib import Path
import argparse,os,shutil,subprocess,sys
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=['build','geometry','rig','motion','validate','render']);a=p.parse_args()
def run(*args):
 print('RUN',' '.join(map(str,args)),flush=True);subprocess.run(list(map(str,args)),cwd=R,check=True)
def blender(stage):
 exe=os.environ.get('BLENDER') or shutil.which('blender')
 if not exe and Path('/Applications/Blender.app/Contents/MacOS/Blender').exists():exe='/Applications/Blender.app/Contents/MacOS/Blender'
 if not exe:raise SystemExit('Install Blender or set BLENDER')
 run(exe,'-b','-t','4','--python-exit-code','1','--python',R/'tools/ranger_blender.py','--',stage)
if a.task in ['build','geometry']:run(sys.executable,R/'tools/ranger_model.py');blender('build')
if a.task in ['build','rig']:blender('rig')
if a.task in ['build','motion']:
 run('node',R/'tools/ranger_motion.mjs','retarget');run('node',R/'tools/ranger_motion.mjs','clips');blender('actions')
if a.task in ['build','validate']:run('node',R/'tools/ranger_motion.mjs','validate')
if a.task=='render':blender('render')

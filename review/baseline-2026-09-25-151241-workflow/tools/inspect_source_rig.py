import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
path=next((R/'animations/source/quaternius-ual1').rglob('UAL1_Standard.glb'))
bpy.ops.import_scene.gltf(filepath=str(path))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
out={'objectMatrix':[list(r) for r in rig.matrix_world],'bones':{b.name:{'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local),'matrix':[list(r) for r in (rig.matrix_world@b.matrix_local)],'parent':b.parent.name if b.parent else None} for b in rig.data.bones}}
(R/'config/source-rig.json').write_text(json.dumps(out,indent=2))
print('RIG',rig.name,'BONES',len(out['bones']))
for n,b in out['bones'].items():
 if not any(t in n for t in ['index','middle','pinky','ring','thumb','leaf']):print(n,[round(x,3) for x in b['head']],[round(x,3) for x in b['tail']])

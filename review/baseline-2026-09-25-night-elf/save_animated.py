"""Create editable Blender actions from the exact final animated GLB."""
import bpy, json, os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
character=os.environ.get('CHARACTER_LAB_CHARACTER','knight')
if character not in ('knight','ranger'):raise ValueError('Unknown character: '+character)
review=R/'review' if character=='knight' else R/'review/ranger'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(R/'assets'/f'{character}-animated.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rig.animation_data_create()
for tr in rig.animation_data.nla_tracks: tr.mute=True
actions=list(bpy.data.actions)
for a in actions: a.use_fake_user=True
idle=next(a for a in actions if 'UAL1_Idle_Loop' in a.name)
rig.animation_data.action=idle
if idle.slots: rig.animation_data.action_slot=idle.slots[0]
rig.show_in_front=True
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=76;bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets'/f'{character}-animated.blend'))
(review/'blender-actions.json').write_text(json.dumps({'actions':len(actions),'names':[a.name for a in actions]},indent=2))
print('ANIMATED BLENDER',len(actions),'actions')

"""Build a fitted humanoid armature and material-aware weights. No invented animation curves."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/knight.blend'))
for c in list(bpy.data.collections):
 if c.name.startswith('REFERENCES'):
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
source=json.loads((R/'config/source-rig.json').read_text());cfg=json.loads((R/'config/rig.json').read_text());spec=cfg['bones']
for n,p in list(spec.items()):
 if n.endswith('_l'):spec[n[:-2]+'_r']={k:[-v[0],v[1],v[2]] for k,v in p.items()}
rot=Matrix.Rotation(math.pi/2,4,'X')
def point(v):return rot@Vector(v)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:
 for v in o.data.vertices:v.co=point(v.co)
arm=bpy.data.armatures.new('Reference-fitted humanoid');rig=bpy.data.objects.new('KnightRig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,p in spec.items():
 eb=arm.edit_bones.new(n);head,tail=point(p['head']),point(p['tail']);canon=source['bones'][n];mat=Matrix(canon['matrix']);direction=(Vector(canon['tail'])-Vector(canon['head'])).normalized();fit=direction.rotation_difference((tail-head).normalized()).to_matrix().to_4x4()@mat;fit.translation=head;eb.matrix=fit;eb.length=(tail-head).length
for n in spec:
 par=source['bones'][n]['parent']
 if par in spec:arm.edit_bones[n].parent=arm.edit_bones[par]
for side,x in [('l',.10),('r',-.10)]:
 for view,z in [('front',.29),('back',-.24)]:
  b=arm.edit_bones.new('cloth_'+view+'_'+side);b.head=point((x,1.24,z));b.tail=point((x,.74,z));b.parent=arm.edit_bones['pelvis']
bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);rig.show_in_front=True
def smooth(y,a,b):
 t=max(0,min(1,(y-a)/(b-a)));return t*t*(3-2*t)
def blend(a,b,t):return {a:1-t,b:t}
def weights(name,p):
 x,y,z=p;s='l' if name.endswith(' L') else 'r'
 if name.startswith(('Face','Sculpted hair','Hair at')):return {'Head':1}
 if name.startswith('Neck'):return {'neck_01':1}
 if name.startswith('Torso'):
  if y<1.55:return blend('pelvis','spine_01',smooth(y,1.32,1.55))
  if y<1.78:return blend('spine_01','spine_02',smooth(y,1.55,1.78))
  return blend('spine_02','spine_03',smooth(y,1.78,1.99))
 if name.startswith('Raised golden'):return {'spine_02':.6,'spine_03':.4}
 if name.startswith('Raised belt'):return {'pelvis':1}
 if name.startswith('Pauldron'):return {'clavicle_'+s:1}
 if name.startswith('Upper arm'):return blend('lowerarm_'+s,'upperarm_'+s,smooth(y,1.56,1.70))
 if name.startswith('Bracer'):return {'lowerarm_'+s:1}
 if name.startswith(('Gauntlet','Thumb')):return {'hand_'+s:1}
 if name.startswith('Hanging hip'):return {'thigh_'+s:1}
 if name.startswith('Thigh'):return blend('calf_'+s,'thigh_'+s,smooth(y,.70,.85))
 if name.startswith('Knee'):return {'calf_'+s:1}
 if name.startswith('Greave'):return blend('foot_'+s,'calf_'+s,smooth(y,.18,.32))
 if name.startswith('Armored boot'):return {'foot_'+s:1}
 if 'tabard' in name.lower():
  view='back' if name.startswith('Rear') else 'front';f=1-smooth(y,.91,1.32);l=smooth(x,-.065,.065)
  return {'pelvis':1-f,'cloth_'+view+'_l':f*l,'cloth_'+view+'_r':f*(1-l)}
 raise ValueError('Missing weight recipe: '+name)
stats=[]
for o in objects:
 # Labels are anatomical: +X is left in our Y-up/front+Z frame. A new
 # reference traced on the opposite image side must not swap skin recipes.
 if o.name.endswith((' L',' R')):
  center_x=sum(v.co.x for v in o.data.vertices)/len(o.data.vertices)
  expected=1 if o.name.endswith(' L') else -1
  if center_x*expected<=0:raise ValueError('Anatomical side label disagrees with mesh: '+o.name)
 groups={b.name:o.vertex_groups.new(name=b.name) for b in arm.bones};sums=[]
 for v in o.data.vertices:
  p=rot.inverted()@v.co;w=weights(o.name,p);total=sum(w.values());sums.append(total)
  for n,weight in w.items():
   if weight>1e-7:groups[n].add([v.index],weight/total,'REPLACE')
 mod=o.modifiers.new('Humanoid skin','ARMATURE');mod.object=rig;o.parent=rig;stats.append({'part':o.name,'vertices':len(o.data.vertices),'minWeightSum':min(sums),'maxWeightSum':max(sums)})
rig['source_motion']='Quaternius Universal Animation Libraries and KayKit; see animations/sources.json'
rig['rig_method']='Fitted landmarks with source-compatible anatomical bone roll; part-aware normalized weights'
bpy.context.scene.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets/knight-rigged.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();model=bpy.context.object;model.name='AmberwatchKnight';rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'assets/knight-rigged.glb'),export_format='GLB',export_yup=True,export_animations=False,use_selection=True,export_materials='EXPORT',export_skins=True)
(R/'review/skin.json').write_text(json.dumps({'bones':len(arm.bones),'parts':stats},indent=2));print('RIGGED',len(arm.bones),'bones')

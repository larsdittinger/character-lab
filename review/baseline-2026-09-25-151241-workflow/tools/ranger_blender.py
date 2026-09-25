"""Independent ranger build, fitted rig, and camera-matched visual inspection.
Usage: blender -b -t 4 --python tools/ranger_blender.py -- build|rig|render|actions
"""
import bpy,bmesh,json,math,sys,os,runpy
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def export(objects,file,yup=False):
 armatures=[o for o in objects if o.type=='ARMATURE']
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=next(o for o in objects if o.type=='MESH')
 if len([o for o in objects if o.type=='MESH'])>1:
  for o in objects:
   if o.type!='MESH':o.select_set(False)
  bpy.ops.object.join()
  for o in armatures:o.select_set(True)
 bpy.context.object.name='CopperRanger'
 bpy.ops.export_scene.gltf(filepath=str(R/'assets'/file),export_format='GLB',export_yup=yup,export_animations=False,export_materials='EXPORT',use_selection=True,export_skins=yup)
if mode=='build':
 clear();spec=json.loads((R/'assets/ranger-model.json').read_text());mat=bpy.data.materials.new('Copper ranger / measured image projection');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.86;bs.inputs['Specular IOR Level'].default_value=.17
 im=nt.nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(R/'textures/ranger-projection.png'));im.image.pack();nt.links.new(im.outputs['Color'],bs.inputs['Base Color']);objects=[];topology=[]
 for part in spec['parts']:
  me=bpy.data.meshes.new(part['name']);me.from_pydata(part['vertices'],[],part['faces']);me.update();ob=bpy.data.objects.new(part['name'],me);bpy.context.collection.objects.link(ob);me.materials.append(mat);uv=me.uv_layers.new(name='Semantic projection UV')
  for loop in me.loops:uv.data[loop.index].uv=part['uv'][loop.vertex_index]
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.000001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
  dec=ob.modifiers.new('Silhouette-aware reduction','DECIMATE');dec.ratio=.32;bpy.ops.object.modifier_apply(modifier=dec.name)
  for poly in me.polygons:poly.use_smooth=True
  bm=bmesh.new();bm.from_mesh(ob.data);topology.append(dict(part=part['name'],boundaryEdges=sum(e.is_boundary for e in bm.edges),nonManifoldEdges=sum(not e.is_manifold for e in bm.edges)));bm.free();ob['projection_zone']=part['zone'];ob.select_set(False);objects.append(ob)
 assert all(p['boundaryEdges']==0 and p['nonManifoldEdges']==0 for p in topology)
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets/ranger-static.blend'));export(objects,'ranger-static.glb')
 model=bpy.context.object;report=dict(triangles=sum(len(p.vertices)-2 for p in model.data.polygons),vertices=len(model.data.vertices),parts=len(objects),source='references/ranger/turnaround.png')
 (R/'review/ranger/build.json').write_text(json.dumps(report,indent=2));(R/'review/ranger/topology.json').write_text(json.dumps(topology,indent=2));print('RANGER BUILD',report)
elif mode=='rig':
 bpy.ops.wm.open_mainfile(filepath=str(R/'assets/ranger-static.blend'));cfg=json.loads((R/'config/ranger-rig.json').read_text());spec=cfg['bones'];source=json.loads((R/'config/source-rig.json').read_text())
 for n,p in list(spec.items()):
  if n.endswith('_l'):spec[n[:-2]+'_r']={k:[-v[0],v[1],v[2]] for k,v in p.items()}
 rot=Matrix.Rotation(math.pi/2,4,'X');point=lambda v:rot@Vector(v);objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for o in objects:
  for v in o.data.vertices:v.co=point(v.co)
 arm=bpy.data.armatures.new('Ranger measured humanoid');rig=bpy.data.objects.new('RangerRig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for n,p in spec.items():
  eb=arm.edit_bones.new(n);head,tail=point(p['head']),point(p['tail']);canon=source['bones'][n];mat=Matrix(canon['matrix']);direction=(Vector(canon['tail'])-Vector(canon['head'])).normalized();fit=direction.rotation_difference((tail-head).normalized()).to_matrix().to_4x4()@mat;fit.translation=head;eb.matrix=fit;eb.length=(tail-head).length
 for n in spec:
  par=source['bones'][n]['parent']
  if par in spec:arm.edit_bones[n].parent=arm.edit_bones[par]
 for side,x in [('l',.10),('r',-.10)]:
  for view,z in [('front',.20),('back',-.14)]:
   b=arm.edit_bones.new('cloth_'+view+'_'+side);b.head=point((x,1.53,z));b.tail=point((x,1.17,z));b.parent=arm.edit_bones['pelvis']
 bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);rig.show_in_front=True
 def smooth(y,a,b):
  t=max(0,min(1,(y-a)/(b-a)));return t*t*(3-2*t)
 def blend(a,b,t):return {a:1-t,b:t}
 def weights(name,p):
  x,y,z=p;s='l' if name.endswith(' L') else 'r'
  if name.startswith(('Face','Sculpted','Hair','Ear')):return {'Head':1}
  if name.startswith('Neck'):return {'neck_01':1}
  if name.startswith('Torso'):
   if y<1.63:return blend('pelvis','spine_01',smooth(y,1.42,1.63))
   if y<1.82:return blend('spine_01','spine_02',smooth(y,1.63,1.82))
   return blend('spine_02','spine_03',smooth(y,1.82,2.05))
  if name.startswith('Pauldron'):return {'clavicle_'+s:1}
  if name.startswith('Hanging hip'):return {'pelvis':.35,'thigh_'+s:.65}
  if name.startswith('Upper'):return blend('lowerarm_'+s,'upperarm_'+s,smooth(y,1.62,1.72))
  if name.startswith('Bracer'):return {'lowerarm_'+s:1}
  if name.startswith(('Gauntlet','Thumb')):return {'hand_'+s:1}
  if name.startswith('Thigh'):return blend('calf_'+s,'thigh_'+s,smooth(y,.79,.91))
  if name.startswith('Knee'):return {'calf_'+s:1}
  if name.startswith('Greave'):return blend('foot_'+s,'calf_'+s,smooth(y,.17,.29))
  if name.startswith('Armored'):return {'foot_'+s:1}
  if 'tabard' in name:
   view='back' if name.startswith('Rear') else 'front';f=1-smooth(y,1.18,1.53);return {'pelvis':1-f,'cloth_'+view+'_'+s:f}
  raise ValueError('Missing explicit skin recipe: '+name)
 stats=[]
 for o in objects:
  if o.name.endswith((' L',' R')):
   rest_x=sum((rot.inverted()@v.co).x for v in o.data.vertices)/len(o.data.vertices)
   expected=1 if o.name.endswith(' L') else -1
   assert rest_x*expected>0, 'Anatomical side disagrees with rig: '+o.name
  groups={b.name:o.vertex_groups.new(name=b.name) for b in arm.bones};sums=[]
  for v in o.data.vertices:
   w=weights(o.name,rot.inverted()@v.co);total=sum(w.values());sums.append(total)
   for n,value in w.items():
    if value>1e-7:groups[n].add([v.index],value/total,'REPLACE')
  mod=o.modifiers.new('Fitted ranger skin','ARMATURE');mod.object=rig;o.parent=rig;stats.append(dict(part=o.name,vertices=len(o.data.vertices),minWeightSum=min(sums),maxWeightSum=max(sums)))
 bpy.context.scene.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets/ranger-rigged.blend'));export(objects+[rig],'ranger-rigged.glb',True)
 (R/'review/ranger/skin.json').write_text(json.dumps(dict(bones=len(arm.bones),parts=stats),indent=2));print('RANGER RIG',len(arm.bones))
elif mode=='actions':
 os.environ['CHARACTER_LAB_CHARACTER']='ranger'
 runpy.run_path(str(R/'tools/save_animated.py'),run_name='__main__')
elif mode=='render':
 clear();bpy.ops.import_scene.gltf(filepath=str(R/'assets/ranger-static.glb'))
 for o in list(bpy.context.selected_objects):
  if o.parent is None:o.matrix_world=Matrix.Rotation(-math.pi/2,4,'X')@o.matrix_world
 def aim(o,target):
  forward=(Vector(target)-o.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward);o.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler()
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
 w=bpy.data.worlds.new('Ranger QA');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.065,.085,.09,1);w.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=w
 for name,pos,power,color in [('Key',(-3,5,4),350,(1,.9,.8)),('Fill',(3,3,2),220,(.8,.95,1)),('Rim',(2,4,-4),300,(.8,.9,1))]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=4;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;aim(o,(0,1.5,0))
 d=bpy.data.cameras.new('Camera');d.type='ORTHO';cam=bpy.data.objects.new('Camera',d);scene.collection.objects.link(cam);scene.camera=cam
 for name,direction in [('front',(0,0,1)),('3q',(.8,.08,1)),('side',(1,0,0)),('back',(0,0,-1))]:
  target=Vector((0,1.25,0));d.ortho_scale=2.78;cam.location=target+Vector(direction).normalized()*5;aim(cam,target);scene.render.filepath=str(R/'review/ranger'/f'body-{name}.png');bpy.ops.render.render(write_still=True)
  if name!='back':
   target=Vector((0,2.29,.035));d.ortho_scale=.61;cam.location=target+Vector(direction).normalized()*5;aim(cam,target);scene.render.filepath=str(R/'review/ranger'/f'face-{name}.png');bpy.ops.render.render(write_still=True)
else:raise SystemExit('Unknown ranger task: '+mode)

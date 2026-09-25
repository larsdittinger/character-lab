"""Blender backend: import the traced surfaces, weld, simplify, package GLB and editable .blend."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
spec=json.loads((R/'assets/model.json').read_text())
mat=bpy.data.materials.new('Paint projected from Gemini reference');mat.use_nodes=True
nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.82;bs.inputs['Specular IOR Level'].default_value=.20
im=nt.nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(R/'textures/knight-projection.png'));im.image.pack();nt.links.new(im.outputs['Color'],bs.inputs['Base Color'])
objects=[];topology=[]
for part in spec['parts']:
 me=bpy.data.meshes.new(part['name']);me.from_pydata(part['vertices'],[],part['faces']);me.update();ob=bpy.data.objects.new(part['name'],me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 uv=me.uv_layers.new(name='Baked projection UV')
 for loop in me.loops:uv.data[loop.index].uv=part['uv'][loop.vertex_index]
 for p in me.polygons:p.use_smooth=True
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.000001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 dec=ob.modifiers.new('Retain silhouette / simplify surface','DECIMATE');dec.ratio=1 if len(ob.data.vertices)<100 else .25;bpy.ops.object.modifier_apply(modifier=dec.name)
 for poly in ob.data.polygons:poly.use_smooth=True
 bm=bmesh.new();bm.from_mesh(ob.data);topology.append({'part':part['name'],'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)});bm.free()
 ob['source']='Gemini front/profile reference, manually traced silhouette and depth profiles';ob['hidden_surfaces']='Authored reconstruction, not observed in source';ob.select_set(False);objects.append(ob)
# Keep the editable source in named pieces; export GLB as one render mesh/material.
bpy.context.scene['workflow']='reference-workflow: image -> traced profiles -> lofted geometry -> projection bake'
refcol=bpy.data.collections.new('REFERENCES · front and profile');bpy.context.scene.collection.children.link(refcol)
for name,file,center,width,rotation in [
 ('Front / calibrated reference','front-calibrated.png',(0,1.25,-.6),810*spec['scale'],(0,0,0)),
 ('Side / calibrated reference','side-calibrated.png',(-.9,1.25,0),360*spec['scale'],(0,math.pi/2,0))]:
 ref=bpy.data.objects.new(name,None);ref.empty_display_type='IMAGE';ref.data=bpy.data.images.load(str(R/'references'/file));ref.data.pack();ref.location=center;ref.rotation_euler=rotation;ref.empty_display_size=width;ref.color[3]=.38;ref.empty_image_depth='BACK';ref.hide_render=True;refcol.objects.link(ref)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=4.4;area.spaces.active.region_3d.view_location=(0,1.25,0);area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets/knight.blend'))
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();model=bpy.context.object;model.name='Amberwatch / reference modeled knight'
bpy.ops.export_scene.gltf(filepath=str(R/'assets/knight.glb'),export_format='GLB',export_yup=False,export_animations=False,export_materials='EXPORT',use_selection=True)
report={'triangles':sum(len(p.vertices)-2 for p in model.data.polygons),'vertices':len(model.data.vertices),'materials':len(model.data.materials),'namedPartsInBlend':len(objects),'animations':0,'glbBytes':(R/'assets/knight.glb').stat().st_size}
(R/'review/build.json').write_text(json.dumps(report,indent=2));print('REFERENCE_BUILD',report)
(R/'review/topology.json').write_text(json.dumps(topology,indent=2))

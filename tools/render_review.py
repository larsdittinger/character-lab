"""Round-trip GLB render, independent from source .blend and browser viewer."""
import bpy,math,json
from mathutils import Vector,Matrix
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(R/'assets/knight.glb'))
# glTF imports are converted to Blender's Z-up convention. Our review camera uses the viewer's Y-up frame.
for ob in list(bpy.context.selected_objects):
 if ob.parent is None:ob.matrix_world=Matrix.Rotation(-math.pi/2,4,'X')@ob.matrix_world
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('Neutral studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.13,.14,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7
def aim(obj,target):
 forward=(Vector(target)-obj.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward);rot=Matrix((right,up,-forward)).transposed();obj.rotation_euler=rot.to_euler()
def light(name,position,power,color,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=position;aim(o,(0,1.25,0))
light('Key',(-3,5,4),400,(1,.88,.72),4);light('Fill',(3,3,2),230,(.75,.9,1),3);light('Rim',(2,4,-4),450,(.7,.9,1),3);light('Rear',(-2,2,-3),200,(1,.9,.76),3)
camdata=bpy.data.cameras.new('Review camera');camdata.type='ORTHO';camdata.ortho_scale=2.9;cam=bpy.data.objects.new('Review camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
for name,direction in [('3q',(.8,.24,1)),('front',(0,0,1)),('side',(1,0,0)),('back',(0,0,-1)),('top',(.001,1,.001)),('bottom',(.001,-1,.001))]:
 cam.location=Vector((0,1.25,0))+Vector(direction).normalized()*7;aim(cam,(0,1.25,0));scene.render.filepath=str(R/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('ROUNDTRIP_RENDERED 6 views from exported GLB')

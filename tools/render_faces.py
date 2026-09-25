"""Matching offline before/after renders of the exported GLBs (no generated edits)."""
import bpy,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
def aim(o,target):
    forward=(Vector(target)-o.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward)
    o.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler()
for version,file in [('before','knight-before-face.glb'),('baseline','knight-before-projection.glb'),('after','knight.glb')]:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(R/'assets'/file))
    for o in list(bpy.context.selected_objects):
        if o.parent is None:o.matrix_world=Matrix.Rotation(-math.pi/2,4,'X')@o.matrix_world
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
    s.view_settings.view_transform='Standard';s.view_settings.look='None'
    w=bpy.data.worlds.new('Face review');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.07,.12,.13,1);w.node_tree.nodes['Background'].inputs[1].default_value=.8;s.world=w
    for name,pos,power,color in [('Key',(-3,5,4),350,(1,.9,.8)),('Fill',(3,3,2),220,(.8,.95,1)),('Rim',(2,4,-4),300,(.8,.9,1))]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=4;d.color=color;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,2.3,0))
    d=bpy.data.cameras.new('Camera');d.type='ORTHO';d.ortho_scale=.63;cam=bpy.data.objects.new('Camera',d);s.collection.objects.link(cam);s.camera=cam
    for angle,direction in [('front',(0,0,1)),('3q',(.8,.12,1)),('side',(1,0,0))]:
        target=Vector((0,2.27,.09));cam.location=target+Vector(direction).normalized()*5;aim(cam,target)
        s.render.filepath=str(R/'review'/f'face-{version}-{angle}.png');bpy.ops.render.render(write_still=True)

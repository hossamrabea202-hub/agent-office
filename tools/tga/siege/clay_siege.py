# Clay check of the siege set: blender -b siege.blend -P clay_siege.py
import bpy, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); sc = bpy.context.scene
clay = bpy.data.materials.new('Clay'); clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.30, 0.28, 1)
LAY = {'SM_Siege_Ram': (0, 0, 0), 'SM_Siege_RamWreck': (8, 0, 0), 'SM_Siege_Tower': (17, 0, 0),
       'SM_Siege_TowerBridge': (17, -1.5, 10.68), 'SM_Siege_TowerWreck': (25, 0, 0)}
for o in list(sc.objects):
    if o.name not in LAY: bpy.data.objects.remove(o); continue
    o.location = LAY[o.name]; o.data.materials.clear(); o.data.materials.append(clay)
bpy.ops.mesh.primitive_plane_add(size=80); sc.objects[-1].name = 'Ground'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-30))); bpy.context.active_object.data.energy = 3
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (2.0, -26.0, 9.0); cd.lens = 30; tgt = Vector((13.0, 0, 3.5))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 800
sc.render.filepath = os.path.join(D, 'out', 'clay_siege.png')
bpy.ops.render.render(write_still=True); print('CLAY OK', flush=True)

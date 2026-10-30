# Clay check of the wasp shape: blender -b wasp_rig.blend -P clay_wasp.py    env VIEW = 34 | side | top, CLAY_NAME
import bpy, math, os
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__)); VIEW = os.environ.get('VIEW', '34')
sc = bpy.context.scene
clay = bpy.data.materials.new('Clay'); clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.32, 0.30, 0.28, 1)
for o in sc.objects:
    if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(clay)
bpy.ops.mesh.primitive_plane_add(size=30); sc.objects[-1].name = 'Ground'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-30))); bpy.context.active_object.data.energy = 3
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0.0, 1.0))
if VIEW == 'side': cam.location = (3.6, 0.0, 1.1); cd.lens = 45
elif VIEW == 'top': cam.location = (0, 0.1, 6.0); cd.lens = 45; tgt = Vector((0, 0.1, 1.2))
elif VIEW == 'face': cam.location = (-0.35, -1.0, 1.72); cd.lens = 60; tgt = Vector((0, -0.06, 1.66))
else: cam.location = (-1.6, -3.4, 1.5); cd.lens = 42
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.render.filepath = os.path.join(D, 'out', os.environ.get('CLAY_NAME', 'clay_' + VIEW) + '.png')
bpy.ops.render.render(write_still=True); print('CLAY OK', sc.render.filepath, flush=True)

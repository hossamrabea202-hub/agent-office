# Clay check of a wall damage build:  blender -b WallDmgWall_high.blend -P clay_wall.py   env VIEW = wide | close, CLAY_NAME
import bpy, math, os
from mathutils import Vector
D = os.path.dirname(os.path.abspath(bpy.data.filepath)); VIEW = os.environ.get('VIEW', 'wide'); sc = bpy.context.scene
clay = bpy.data.materials.new('Clay'); clay.use_nodes = True; clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.36, 0.34, 0.31, 1)
core = bpy.data.materials.new('CoreClay'); core.use_nodes = True; core.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.16, 0.15, 0.14, 1)
for o in sc.objects:
    if o.type == 'MESH':
        m = core if o.name.startswith('Core') else clay
        o.data.materials.clear(); o.data.materials.append(m)
        for p in o.data.polygons: p.use_smooth = True
bpy.ops.mesh.primitive_plane_add(size=40)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(55), 0, math.radians(-35))); bpy.context.active_object.data.energy = 3.2
bpy.context.active_object.data.angle = math.radians(2)
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tx, tz = float(os.environ.get('TX', '0')), float(os.environ.get('TZ', '2.0'))
if VIEW == 'close': cam.location = (tx - 0.9, -2.4, tz + 0.5); cd.lens = 50; tgt = Vector((tx, 0, tz))
else: cam.location = (-4.5, -8.5, 3.6); cd.lens = 40; tgt = Vector((0, 0, 2.2))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '32')); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.filepath = os.path.join(D, os.environ.get('CLAY_NAME', 'clay_' + VIEW) + '.png'); bpy.ops.render.render(write_still=True); print('CLAY OK', sc.render.filepath)

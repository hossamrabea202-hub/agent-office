# #135 look-dev preview: renders the palisade HIGH mesh with the procedural material (before the bake).
#   blender -b Palisade_bake.blend -P preview135.py      env MATV = v1 | v2, SHOT = wide | close, PREV_SAMPLES
import sys, os, math
import bpy
from mathutils import Vector
D = os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))
V = os.environ.get('MATV', 'v2'); SHOT = os.environ.get('SHOT', 'wide')
sys.path.insert(0, D)
if V == 'v1': sys.path.insert(0, os.path.join(D, 'v1'))
sc = bpy.context.scene
if V == 'baked':   # Palisade_final.blend: the game mesh with the baked 4K textures, as UE will show it
    pass
else:
    import woodmat
    from matlib import set_output
    woodmat.build_all()
    for m in bpy.data.materials:
        if m.node_tree and 'OUT' in m.node_tree.nodes and 'BSDF' in m.node_tree.nodes: set_output(m, 'BSDF')
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'HP': o.hide_render = True
# ground: dark trodden earth
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
g = bpy.context.active_object; gm = bpy.data.materials.new('Ground'); gm.use_nodes = True
b = gm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.045, 0.036, 0.027, 1); b.inputs['Roughness'].default_value = 0.9
g.data.materials.append(gm)
# light: overcast sky + low warm sun from the front-left (the game's foggy dusk)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.42, 0.46, 0.52, 1); bg.inputs['Strength'].default_value = 0.55
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(58), 0, math.radians(-38)))
sun = bpy.context.active_object.data; sun.energy = 3.2; sun.angle = math.radians(6); sun.color = (1.0, 0.86, 0.70)
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
if SHOT == 'close':
    cam.location = (0.9, -1.55, 0.75); target = Vector((0.55, 0.0, 0.55)); cam_d.lens = 45
else:
    cam.location = (-3.6, -6.6, 2.1); target = Vector((0.25, 0.0, 1.45)); cam_d.lens = 38
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('PREV_SAMPLES', '48'))
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (1600, 1100); sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'
sc.render.image_settings.file_format = 'PNG'
out = os.path.join(D, 'preview', f'{SHOT}_{V}.png'); os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('PREVIEW OK', out, flush=True)

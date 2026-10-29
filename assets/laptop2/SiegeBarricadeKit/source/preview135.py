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
elif SHOT == 'tower':    # watchtower, 8.8 m
    cam.location = (-8.5, -13.0, 4.8); target = Vector((0.0, 0.0, 4.0)); cam_d.lens = 35
elif SHOT == 'low':      # cheval de frise, 1.4 m
    cam.location = (-3.2, -5.2, 1.7); target = Vector((0.0, 0.0, 0.6)); cam_d.lens = 40
else:
    cam.location = (-3.6, -6.6, 2.1); target = Vector((0.25, 0.0, 1.45)); cam_d.lens = 38
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('PREV_SAMPLES', '48'))
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (1600, 1100); sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'
sc.render.image_settings.file_format = 'PNG'
out = os.path.join(D, 'preview', os.environ.get('PREV_NAME', f'{SHOT}_{V}') + '.png'); os.makedirs(os.path.dirname(out), exist_ok=True)
if os.environ.get('LOOKDEV'):
    # calibrated lookdev (handoffs/knowledge): physical sky with the sun at 35 deg, a 0.18 grey ball and a chrome ball beside
    # the asset, exposure locked so the grey ball reads mid-grey (~118 sRGB) before anything is judged
    import bpy_extras, numpy as np
    for o in [o for o in sc.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o)
    sky = w.node_tree.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA' if 'NISHITA' in [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items] else sky.sky_type
    sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(220)
    w.node_tree.links.new(sky.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
    balls = []
    for k, (col, met, rgh) in enumerate([((0.18, 0.18, 0.18, 1), 0.0, 0.5), ((0.95, 0.95, 0.95, 1), 1.0, 0.02)]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, segments=48, ring_count=24, location=(target.x - 1.2 + k * 0.55, target.y - 1.6, 0.22))
        bpy.ops.object.shade_smooth(); m = bpy.data.materials.new('Ball%d' % k); m.use_nodes = True
        p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = met; p.inputs['Roughness'].default_value = rgh
        bpy.context.active_object.data.materials.append(m); balls.append(bpy.context.active_object)
    grey = balls[0]; uv = bpy_extras.object_utils.world_to_camera_view(sc, cam, grey.location)
    tmp = os.path.join(D, 'preview', '_meter.png'); sc.render.filepath = tmp; samples = sc.cycles.samples; sc.cycles.samples = 16
    sc.view_settings.exposure = 0.0; sc.view_settings.view_transform = 'Standard'   # meter in linear sRGB, then lock
    for it in range(4):     # Standard is linear, so this converges in 1-2 steps
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'; W, H = im.size
        px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im); px = px.reshape(H, W, 4)
        cx, cy = int(uv.x * W), int(uv.y * H); v = float(px[cy - 3:cy + 4, cx - 3:cx + 4, :3].mean()) * 255
        print('METER grey ball %.0f sRGB at exposure %.2f' % (v, sc.view_settings.exposure), flush=True)
        if abs(v - 118) < 4: break
        sc.view_settings.exposure += math.log2(((118 / 255 + 0.055) / 1.055) ** 2.4 / max(((v / 255 + 0.055) / 1.055) ** 2.4, 1e-4))
    sc.cycles.samples = samples; sc.view_settings.view_transform = 'AgX'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('PREVIEW OK', out, flush=True)

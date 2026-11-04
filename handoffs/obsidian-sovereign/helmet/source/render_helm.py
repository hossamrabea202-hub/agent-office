# Preview renders. blender -b <file.blend> -P render_helm.py -- <out_prefix> [samples] [res] [clay|keep] [views: front,side,front34,back34]
import sys, os, math, bpy, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
prefix = argv[0]; samples = int(argv[1]) if len(argv) > 1 else 48; res = int(argv[2]) if len(argv) > 2 else 900
mode = argv[3] if len(argv) > 3 else 'clay'; views_sel = argv[4].split(',') if len(argv) > 4 else None
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(os.environ.get('RENDER_THREADS', '8'))
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '-1.6'))
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.21, 0.23, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
if mode == 'clay':
    col = {'Steel': (0.30, 0.31, 0.34, 0.35, 1.0), 'Gold': (0.95, 0.70, 0.30, 0.25, 1.0), 'Leather': (0.12, 0.06, 0.03, 0.6, 0.0),
           'Buckle': (0.6, 0.6, 0.62, 0.3, 1.0), 'Etch': (0.05, 0.05, 0.06, 0.6, 0.6), 'Liner': (0.02, 0.02, 0.02, 0.9, 0.0), 'Rim': (0.4, 0.41, 0.44, 0.3, 1.0)}
    for m in bpy.data.materials:
        k = m.name.split('.')[0]
        if k in col and m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
            b = m.node_tree.nodes['Principled BSDF']; c = col[k]
            b.inputs['Base Color'].default_value = (*c[:3], 1); b.inputs['Roughness'].default_value = c[3]; b.inputs['Metallic'].default_value = c[4]
lp = bpy.data.objects.get('SM_ObsidianSovereign_Helmet')
if lp and 'HP' in bpy.data.objects: lp.hide_render = True          # bake_ready.blend: look at the high poly
TGT = mathutils.Vector((0.0, 0.03, 1.655))
def light(name, loc, energy, size, c=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = c
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = TGT + mathutils.Vector(loc)
    o.rotation_euler = (TGT - o.location).to_track_quat('-Z', 'Y').to_euler()
light('Key', (-0.9, -1.2, 0.9), 75, 1.1, (1.0, 0.95, 0.88)); light('Fill', (1.2, -0.7, 0.3), 22, 1.3, (0.8, 0.88, 1.0))
light('Rim', (0.6, 1.3, 0.9), 70, 0.9, (0.85, 0.9, 1.0)); light('Top', (0, 0, 1.3), 18, 1.0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 85
views = {'front': (0, 3, 1.05), 'front34': (-35, 8, 1.05), 'side': (-90, 3, 1.05), 'back34': (145, 12, 1.05)}
for name, (az, el, d) in views.items():
    if views_sel and name not in views_sel: continue
    a, e = math.radians(az - 90), math.radians(el)
    cam.location = (TGT.x + d * math.cos(e) * math.cos(a), TGT.y + d * math.cos(e) * math.sin(a), TGT.z + d * math.sin(e))
    cam.rotation_euler = (TGT - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'; bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath)

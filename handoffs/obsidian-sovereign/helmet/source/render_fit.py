# Fit preview: the helm over a head-size proxy lofted from the measured bands of SM_HeroHead + the gorget (probes/fit_envelope.json).
#   blender -b helm_final.blend -P render_fit.py -- <fit_envelope.json> <out_prefix> [samples] [res]
# The proxy is two lofted ellipsoid-like shapes built from numbers only: the licensed head mesh is not in the repo or the render.
# Two images: <prefix>_cutaway (helm with the +X half removed, seen from +X), <prefix>_ghost (see-through helm, 3/4 from the front).
import sys, os, json, math, bpy, bmesh, mathutils
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
E = json.load(open(a[0])); prefix = a[1]; samples = int(a[2]) if len(a) > 2 else 64; res = int(a[3]) if len(a) > 3 else 1000
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.threads_mode = 'FIXED'; sc.render.threads = int(os.environ.get('RENDER_THREADS', '8'))
sc.render.resolution_x = sc.render.resolution_y = res; sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.6
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.25, 0.26, 0.28, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0

def mat(name, col, rough=0.5, metal=0.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if alpha is not None: b.inputs['Alpha'].default_value = alpha
    return m
def loft(name, rows, m, seg=48):
    """rows: [z_cm, xmin, xmax, y_ue_back, y_ue_front]; blender y = -y_ue. Superellipse sections, closed with caps."""
    V, F = [], []; n = len(rows)
    for z, x0, x1, yb, yf in rows:
        cx, ax = (x0 + x1) / 2, max((x1 - x0) / 2, 0.05); cy, ay = -(yb + yf) / 2, max((yf - yb) / 2, 0.05)
        for i in range(seg):
            t = 2 * math.pi * i / seg; V.append(((cx + ax * math.cos(t)) * 0.01, (cy + ay * math.sin(t)) * 0.01, z * 0.01))
    for j in range(n - 1):
        for i in range(seg):
            i2 = (i + 1) % seg; F.append((j * seg + i, j * seg + i2, (j + 1) * seg + i2, (j + 1) * seg + i))
    F.append(tuple(range(seg))[::-1]); F.append(tuple((n - 1) * seg + i for i in range(seg)))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.validate(); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(m); return ob
def rows_of(key):
    return [[(r[0] + r[1]) / 2, r[2], r[3], r[4], r[5]] for r in E[key]]
head = loft('Proxy_Head', rows_of('head'), mat('ProxyHead', (0.70, 0.36, 0.26), 0.55))
gor = loft('Proxy_Gorget', rows_of('gorget_neck'), mat('ProxyGorget', (0.15, 0.45, 0.75), 0.5))

helm = bpy.data.objects['SM_ObsidianSovereign_Helmet']
TGT = mathutils.Vector((0, 0.03, 1.655))
l = bpy.data.lights.new('Sun', 'AREA'); l.energy = 60; l.size = 1.2
o = bpy.data.objects.new('Key', l); sc.collection.objects.link(o); o.location = TGT + mathutils.Vector((0.9, -0.9, 0.8)); o.rotation_euler = (TGT - o.location).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.46
def shot(name, loc):
    cam.location = TGT + mathutils.Vector(loc); cam.rotation_euler = (TGT - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = prefix + name + '.png'; bpy.ops.render.render(write_still=True); print('RENDERED', sc.render.filepath)
# ghost: textured material swapped for a thin see-through steel
ghost = mat('Ghost', (0.5, 0.52, 0.55), 0.4, 0.0, 0.22)
saved = [s.material for s in helm.material_slots]
for s in helm.material_slots: s.material = ghost
shot('_ghost', (0.55, -1.1, 0.25))
for s, m_ in zip(helm.material_slots, saved): s.material = m_
# cutaway: drop every face on the +X side
bm = bmesh.new(); bm.from_mesh(helm.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > 0.0], context='FACES')
bm.to_mesh(helm.data); bm.free()
shot('_cutaway', (1.3, 0, 0))

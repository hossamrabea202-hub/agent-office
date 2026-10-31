# Vesna's Trade (#361): turntable atlases + list icons for the Obsidian pieces that have art (checkking's meshes/textures).
#   blender -b --factory-startup -P turntable.py -- <out dir> [piece ...]
# Per piece: T_VT_Turn_<Folder>.png = 24 frames (4 x 6 cells of 512 x 340, 15 deg apart, frame 0 = 3/4 view) on alpha.
# All pieces: T_VT_Icons.png = 1024 x 256, 8 cells of 128 (order = ICON_ORDER), the frame-0 view cropped square.
# Look follows the owner's target: dark studio, warm key, cool back glow, gold rim.
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(os.path.dirname(__file__), 'out')
SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'assets', 'checkking', 'Obsidian-Sovereign'))
ICON_ORDER = ['Chest', 'Shoulders', 'Gauntlets', 'Shins', 'Boots']
PIECES = argv[1:] or ICON_ORDER
FW, FH, COLS, ROWS, N = 512, 340, 4, 6, 24
os.makedirs(OUT, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
    try: sc.cycles.device = 'GPU'
    except Exception: pass
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = FW, FH
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 1.1
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.014, 0.02, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    return sc

def tex(nt, path, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(path); n.image.colorspace_settings.name = cs; return n

def material(folder):
    t = os.path.join(SRC, folder, 'textures', 'T_ObsidianSovereign_%s_' % folder)
    m = bpy.data.materials.new('M_' + folder); m.use_nodes = True; nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bc = tex(nt, t + 'BaseColor.png', 'sRGB'); orm = tex(nt, t + 'ORM.png', 'Non-Color'); nm = tex(nt, t + 'Normal_DirectX.png', 'Non-Color')
    nt.links.new(bc.outputs[0], bsdf.inputs['Base Color'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(orm.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs['Roughness']); nt.links.new(sep.outputs[2], bsdf.inputs['Metallic'])
    s2 = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(nm.outputs[0], s2.inputs[0])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(s2.outputs[1], inv.inputs[1])
    cmb = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(s2.outputs[0], cmb.inputs[0]); nt.links.new(inv.outputs[0], cmb.inputs[1]); nt.links.new(s2.outputs[2], cmb.inputs[2])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(cmb.outputs[0], nmap.inputs['Color']); nt.links.new(nmap.outputs[0], bsdf.inputs['Normal'])
    return m

def area(name, loc, energy, color, size, target):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def load(folder):
    files = sorted(f for f in os.listdir(os.path.join(SRC, folder)) if f.lower().endswith('.fbx'))
    before = set(bpy.data.objects)
    for f in files: bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, folder, f))
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in bpy.data.objects:
        if o not in before and o.type != 'MESH': bpy.data.objects.remove(o)
    m = material(folder)
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(m)
    # normalise: centre on the bbox, biggest side = 2 units, pivot = an empty at the origin that turns
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr, k = (lo + hi) / 2, 2.0 / max(hi - lo)
    piv = bpy.data.objects.new('Pivot', None); bpy.context.scene.collection.objects.link(piv)
    piv.location = ctr; bpy.context.view_layer.update()
    for o in objs:
        o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.location = (0, 0, 0); piv.scale = (k, k, k)
    bpy.context.view_layer.update()
    return piv, objs, (hi - lo) * k

def setup_camera(size):
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = 60; bpy.context.scene.camera = cam
    # fit the turning piece: its horizontal extent can reach the bbox diagonal on X/Y
    reach = max(math.hypot(size.x, size.y), size.z * FW / FH) * 0.5 * 1.04
    dist = reach / math.tan(cam.data.angle_x / 2) + max(size) * 0.18
    el = math.radians(12)
    cam.location = (0, -dist * math.cos(el), dist * math.sin(el)); cam.rotation_euler = (math.pi / 2 - el, 0, 0)
    area('Key', (-3.2, -3.6, 3.4), 1300, (1.0, 0.86, 0.68), 2.6, (0, 0, 0))
    area('Fill', (3.6, -2.4, 0.6), 120, (0.75, 0.82, 1.0), 3.0, (0, 0, 0))
    area('RimGold', (2.6, 3.4, 2.8), 700, (1.0, 0.78, 0.42), 1.6, (0, 0, 0.2))
    area('BackCool', (-2.4, 4.2, -0.4), 380, (0.55, 0.68, 1.0), 3.5, (0, 0, 0))
    return cam

def render_frames(piv, tag):
    frames = []
    for i in range(N):
        piv.rotation_euler = (0, 0, math.radians(-35 + i * 360.0 / N))
        p = os.path.join(OUT, '_%s_%02d.png' % (tag, i)); bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True); frames.append(p)
    return frames

def px(path):
    im = bpy.data.images.load(path); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a

def save(arr, path):
    h, w = arr.shape[:2]; im = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    im.pixels[:] = arr.ravel(); im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

icons = {}
for folder in PIECES:
    reset(); piv, objs, size = load(folder); setup_camera(size)
    frames = render_frames(piv, folder)
    atlas = np.zeros((ROWS * FH, COLS * FW, 4), np.float32)
    for i, p in enumerate(frames):
        a = px(p); r, c = divmod(i, COLS)
        y0 = (ROWS - 1 - r) * FH          # Blender pixels are bottom-up
        atlas[y0:y0 + FH, c * FW:(c + 1) * FW] = a
        if i == 0: icons[folder] = a
        os.remove(p)
    save(atlas, os.path.join(OUT, 'T_VT_Turn_%s.png' % folder)); print('TURN', folder, atlas.shape)

# icons: square crop round the alpha bbox of frame 0, downsampled to 128 (box filter)
ic = np.zeros((256, 1024, 4), np.float32)
for k, folder in enumerate(ICON_ORDER):
    if folder not in icons: continue
    a = icons[folder]; ys, xs = np.where(a[..., 3] > 0.02)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2; half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.08
    sq = np.zeros((int(2 * half) + 2, int(2 * half) + 2, 4), np.float32)
    y0, x0 = int(cy - half), int(cx - half)
    for yy in range(sq.shape[0]):
        sy = y0 + yy
        if 0 <= sy < a.shape[0]:
            xa, xb = max(0, x0), min(a.shape[1], x0 + sq.shape[1]); sq[yy, xa - x0:xb - x0] = a[sy, xa:xb]
    n = sq.shape[0]; idx = (np.arange(128) * n / 128).astype(int); step = max(1, n // 128)
    small = np.zeros((128, 128, 4), np.float32)
    for dy in range(step):
        for dx in range(step): small += sq[np.minimum(idx + dy, n - 1)][:, np.minimum(idx + dx, n - 1)]
    small /= step * step
    r, c = divmod(k, 8)
    ic[(1 - r) * 128:(2 - r) * 128, c * 128:(c + 1) * 128] = small   # row 0 at the top
save(ic, os.path.join(OUT, 'T_VT_Icons.png')); print('ICONS', ICON_ORDER)

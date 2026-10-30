# Pickup reveal motion graphics (#139 bag, #140 book), checkking 2026-10-30. Blender 4.5, procedural, no external assets.
#   blender -b --factory-startup -P build_reveal.py -- <book|bag> <out_dir> [frames=64] [res=512] [samples=48]
# Renders a transparent 64-frame sequence (24 fps, 2.67 s) of the item spinning in, settling toward the camera and opening
# with gold light pouring out, then packs it into an 8x8 flipbook atlas <out_dir>/T_Reveal_<Book|Bag>_Atlas.png
# (4096 px at res 512) for the HUD material M_UI_RevealFlipbook. Also writes a 1600 px preview strip.
# Realism KB: calibrated albedo (leather sRGB ~70/35/25, page ~225/210/180, gold metal F0 ~ 1.0/0.78/0.34 linear),
# roughness never flat (noise-driven), wear at edges only (pointiness), one warm key + cool rim + weak fill (secrets §2.5).
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['book', os.getcwd()]
WHICH, OUT = argv[0], os.path.abspath(argv[1])
FR = int(argv[2]) if len(argv) > 2 else 64
RES = int(argv[3]) if len(argv) > 3 else 512
SPP = int(argv[4]) if len(argv) > 4 else 48
os.makedirs(os.path.join(OUT, 'frames_' + WHICH), exist_ok=True)

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
col = sc.collection

# ---------------------------------------------------------------- helpers
def srgb(c): return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 for x in c)

def mat_pbr(name, base, rough=(0.45, 0.7), metal=0.0, bump=0.3, scale=60.0, wear=None, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rr = N.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value, rr.inputs['To Max'].default_value = rough
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs['Result'], bsdf.inputs['Roughness'])
    bm = N.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bump; bm.inputs['Distance'].default_value = 0.0005
    L.new(nz.outputs['Fac'], bm.inputs['Height']); L.new(bm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = metal
    if wear:   # edges: lighter, smoother (rubbed), only where the geometry is convex
        geo = N.new('ShaderNodeNewGeometry')
        ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.52; ramp.color_ramp.elements[1].position = 0.6
        L.new(geo.outputs['Pointiness'], ramp.inputs['Fac'])
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        mix.inputs[6].default_value = (*base, 1); mix.inputs[7].default_value = (*wear, 1)
        L.new(ramp.outputs['Color'], mix.inputs[0]); L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = (*base, 1)
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1); bsdf.inputs['Emission Strength'].default_value = 0.0
    return m

LEATHER = mat_pbr('Leather', srgb((56, 27, 19)), (0.48, 0.72), 0, 0.35, 90, wear=srgb((96, 54, 37)))
LEATHER2 = mat_pbr('LeatherBag', srgb((66, 42, 27)), (0.5, 0.75), 0, 0.4, 70, wear=srgb((112, 78, 52)))
GOLD = mat_pbr('Gold', (1.0, 0.78, 0.34), (0.22, 0.38), 1.0, 0.08, 120)
PAGE = mat_pbr('Page', srgb((225, 210, 180)), (0.75, 0.88), 0, 0.15, 400)
GLOW = bpy.data.materials.new('Glow'); GLOW.use_nodes = True
gn = GLOW.node_tree.nodes; gn.remove(gn['Principled BSDF'])
em = gn.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.72, 0.32, 1); em.inputs['Strength'].default_value = 0.0
GLOW.node_tree.links.new(em.outputs[0], gn['Material Output'].inputs['Surface'])

def box(name, size, loc, mat, bevel=0.002, segs=3, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent: keep_parent(o, parent)
    return o

def keep_parent(o, p):
    mw = o.matrix_world.copy(); o.parent = p; o.matrix_world = mw

def cyl(name, r, depth, loc, rot, mat, verts=48, parent=None, bevel=0.0008):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 2
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    if parent: keep_parent(o, parent)
    return o

def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None); col.objects.link(o); o.location = loc
    if parent: o.parent = parent
    return o

root = empty('Root', (0, 0, 0))

# ---------------------------------------------------------------- the book (spine on -X, front cover toward the camera at -Y)
def build_book():
    W, H, T, C = 0.18, 0.25, 0.05, 0.008          # width, height, thickness, cover board
    box('Back', (W, C, H), (0, T / 2 - C / 2, 0), LEATHER, 0.0025, parent=root)
    box('Spine', (0.014, T, H), (-W / 2, 0, 0), LEATHER, 0.006, 4, parent=root)
    for i, z in enumerate((-0.08, 0.0, 0.08)):    # raised bands on the spine
        box('Band%d' % i, (0.018, T * 0.9, 0.008), (-W / 2 - 0.002, 0, z), LEATHER, 0.003, 3, parent=root)
    box('Pages', (W - 0.012, T - 2 * C - 0.002, H - 0.012), (0.004, 0, 0), PAGE, 0.0015, parent=root)
    hinge = empty('Hinge', (-W / 2, -T / 2 + C / 2, 0), root)
    box('Front', (W, C, H), (0, -T / 2 + C / 2, 0), LEATHER, 0.0025, parent=hinge)
    # gold corner caps + sigil on the front cover
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = box('Cap', (0.022, C + 0.003, 0.022), (sx * (W / 2 - 0.009), -T / 2 + C / 2, sz * (H / 2 - 0.009)), GOLD, 0.0015, parent=hinge)
    cyl('SigilRing', 0.034, 0.003, (0.004, -T / 2 - 0.0005, 0.01), (math.pi / 2, 0, 0), GOLD, parent=hinge)
    cyl('SigilCore', 0.024, 0.0045, (0.004, -T / 2 - 0.001, 0.01), (math.pi / 2, 0, 0), LEATHER, parent=hinge)
    for k in range(4):                            # four-point star
        s = box('Star%d' % k, (0.006, 0.004, 0.05), (0.004, -T / 2 - 0.0025, 0.01), GOLD, 0.001, parent=hinge)
        s.rotation_euler = (0, k * math.pi / 4, 0)
    # clasp: strap over the page edge
    box('Strap', (0.03, T + 0.004, 0.018), (W / 2 - 0.004, 0, 0), LEATHER, 0.002, parent=root)
    box('Clasp', (0.012, 0.012, 0.024), (W / 2 + 0.006, -T / 2 + 0.004, 0), GOLD, 0.0015, parent=hinge)
    # loose pages that fan out, and the light between them
    pages = []
    for k in range(4):
        ph = empty('PageHinge%d' % k, (-W / 2 + 0.008, -T / 2 + C + 0.002 + k * 0.0012, 0), root)
        box('Leaf%d' % k, (W - 0.02, 0.0008, H - 0.016), (0.002, -T / 2 + C + 0.002 + k * 0.0012, 0), PAGE, 0, parent=ph)
        pages.append(ph)
    box('GlowCard', (W - 0.03, 0.001, H - 0.04), (0.006, -T / 2 + C + 0.0068, 0), GLOW, 0, parent=root)
    return hinge, pages, (-math.radians(158), 'Z')

# ---------------------------------------------------------------- the satchel (flap hinged at the back top edge)
def build_bag():
    W, D, H = 0.30, 0.12, 0.22
    body = box('Body', (W, D, H), (0, 0, 0), LEATHER2, 0.03, 6, parent=root)
    sub = body.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    box('Opening', (W * 0.9, D * 0.8, 0.004), (0, 0, H / 2 + 0.001), GLOW, 0, parent=root)
    hinge = empty('FlapHinge', (0, D / 2 - 0.004, H / 2 - 0.004), root)
    flap = box('Flap', (W + 0.01, D + 0.012, 0.012), (0, 0, H / 2 + 0.004), LEATHER2, 0.012, 4, parent=hinge)
    front = box('FlapFront', (W + 0.01, 0.012, H * 0.55), (0, -D / 2 - 0.004, H / 2 - H * 0.275 + 0.006), LEATHER2, 0.012, 4, parent=hinge)
    box('Buckle', (0.05, 0.008, 0.04), (0, -D / 2 - 0.012, H / 2 - H * 0.5), GOLD, 0.002, parent=hinge)
    box('BuckleBar', (0.008, 0.01, 0.036), (0, -D / 2 - 0.016, H / 2 - H * 0.5), GOLD, 0.0015, parent=hinge)
    box('Tongue', (0.03, 0.006, 0.07), (0, -D / 2 - 0.007, -H * 0.06), LEATHER2, 0.003, parent=root)
    for sx in (-1, 1):   # strap rings + strap stubs going up
        cyl('Ring', 0.016, 0.006, (sx * (W / 2 + 0.004), 0, H / 2 - 0.03), (0, math.pi / 2, 0), GOLD, parent=root)
        box('StrapStub', (0.006, 0.03, 0.09), (sx * (W / 2 + 0.008), 0, H / 2 + 0.03), LEATHER2, 0.002, parent=root)
    # strap: one clean arc from ring to ring (3-point Bezier), a thick leather band
    cu = bpy.data.curves.new('StrapCurve', 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    for p_, co in zip(sp.bezier_points, ((-(W / 2 + 0.008), 0, H / 2 - 0.02), (0, 0, H / 2 + 0.13), (W / 2 + 0.008, 0, H / 2 - 0.02))):
        p_.co = co; p_.handle_left_type = p_.handle_right_type = 'AUTO'
    cu.bevel_depth = 0.010; cu.bevel_resolution = 2
    arc = bpy.data.objects.new('Strap', cu); col.objects.link(arc); arc.scale = (1, 1, 1); arc.data.materials.append(LEATHER2)
    keep_parent(arc, root)
    return hinge, [], (-math.radians(118), 'X')

hinge, pages, (OPEN, AXIS) = build_book() if WHICH == 'book' else build_bag()

# ---------------------------------------------------------------- lights + camera (warm key, cool rim, weak fill)
def area(name, loc, energy, color, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
area('Key', (-0.7, -0.9, 0.8), 40, (1.0, 0.86, 0.70), 0.6)
area('Rim', (0.8, 0.9, 0.5), 80, (0.70, 0.80, 1.0), 0.3)
area('Fill', (0.9, -0.8, -0.2), 6, (1.0, 0.95, 0.9), 1.0)
gl = bpy.data.lights.new('Inner', 'POINT'); gl.color = (1.0, 0.7, 0.3); gl.energy = 0; gl.shadow_soft_size = 0.05
glo = bpy.data.objects.new('Inner', gl); col.objects.link(glo)
glo.location = (0.0, -0.05, 0.0) if WHICH == 'book' else (0, 0, 0.16)
cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = 100
cam = bpy.data.objects.new('Cam', cam_d); col.objects.link(cam); sc.camera = cam
cam.location = (0, -1.15, 0.15); cam.rotation_euler = (math.radians(83), 0, 0)

# ---------------------------------------------------------------- animation (frames 1..FR)
sc.frame_start, sc.frame_end = 1, FR
sc.render.fps = 24
f_spin, f_open, f_glow = 1, int(FR * 0.56), int(FR * 0.66)
def key(o, path, f, v, idx=None):
    if idx is None: setattr(o, path, v); o.keyframe_insert(path, frame=f)
    else: getattr(o, path)[idx] = v; o.keyframe_insert(path, index=idx, frame=f)
# spin in: 1.5 turns, ease out, rising and growing; settle a little turned toward the light
key(root, 'rotation_euler', f_spin, math.radians(-560), 2); key(root, 'rotation_euler', f_open - 2, math.radians(-14), 2)
key(root, 'rotation_euler', FR, math.radians(-8), 2)
key(root, 'scale', f_spin, (0.25, 0.25, 0.25)); key(root, 'scale', f_open - 6, (1.04, 1.04, 1.04)); key(root, 'scale', f_open, (1.0, 1.0, 1.0))
key(root, 'location', f_spin, (0, 0, -0.12)); key(root, 'location', f_open - 4, (0, 0, 0.012)); key(root, 'location', FR, (0, 0, 0.0))
key(root, 'rotation_euler', f_spin, math.radians(18), 0); key(root, 'rotation_euler', f_open, math.radians(0), 0)
if WHICH == 'bag': key(root, 'rotation_euler', FR, math.radians(-12), 0)   # tip the bag forward so the open mouth shows
ax = {'X': 0, 'Z': 2}[AXIS]
key(hinge, 'rotation_euler', f_open, 0.0, ax); key(hinge, 'rotation_euler', min(FR, f_open + 14), OPEN, ax)
for k, ph in enumerate(pages):
    key(ph, 'rotation_euler', f_open + 4 + k, 0.0, 2); key(ph, 'rotation_euler', min(FR, f_open + 16 + 2 * k), -math.radians(12 + 14 * k), 2)
key(em.inputs['Strength'], 'default_value', f_glow - 6, 0.0); key(em.inputs['Strength'], 'default_value', FR, 9.0 if WHICH == 'book' else 16.0)
key(gl, 'energy', f_glow - 6, 0.0); key(gl, 'energy', FR, 6.0)
for o in bpy.data.objects:          # ease-out on everything (Bezier with auto-clamped handles)
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'EASE_OUT'

# ---------------------------------------------------------------- render: Cycles, transparent, AgX, locked exposure
sc.render.engine = 'CYCLES'
cp = bpy.context.preferences.addons['cycles'].preferences
try:
    cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
    for d in cp.devices: d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
except Exception: pass
sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.08
sc.render.filepath = os.path.join(OUT, 'frames_' + WHICH, 'f_')
bpy.ops.render.render(animation=True)

# ---------------------------------------------------------------- pack the 8x8 atlas + preview strip
cols = int(math.ceil(math.sqrt(FR)))
atlas = np.zeros((cols * RES, cols * RES, 4), np.float32)
frames = []
for i in range(FR):
    im = bpy.data.images.load(os.path.join(OUT, 'frames_' + WHICH, 'f_%04d.png' % (i + 1)))
    px = np.empty(RES * RES * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(RES, RES, 4)
    frames.append(px); bpy.data.images.remove(im)
    r, c = divmod(i, cols)
    atlas[(cols - 1 - r) * RES:(cols - r) * RES, c * RES:(c + 1) * RES] = px   # Blender images are bottom-up: row 0 at the top
def save(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels.foreach_set(arr.ravel()); img.filepath_raw = path; img.file_format = 'PNG'; img.save()
name = 'T_Reveal_%s_Atlas.png' % ('Book' if WHICH == 'book' else 'Bag')
save(atlas, os.path.join(OUT, name))
picks = [int(round(k * (FR - 1) / 7)) for k in range(8)]
strip = np.zeros((RES, RES * 8, 4), np.float32); strip[..., :3] = 0.035; strip[..., 3] = 1
for k, i in enumerate(picks):
    a = frames[i][..., 3:4]
    strip[:, k * RES:(k + 1) * RES, :3] = frames[i][..., :3] * a + strip[:, k * RES:(k + 1) * RES, :3] * (1 - a)
save(strip, os.path.join(OUT, 'preview_%s_strip.png' % WHICH))
print('REVEAL DONE', WHICH, name, 'frames', FR, 'atlas', atlas.shape)

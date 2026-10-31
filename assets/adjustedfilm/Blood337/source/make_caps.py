# #337 wound caps for severed limbs, "not too gory" (adjustedfilm, 2026-10-31; RESEARCH.md Â§4 / Â§5.3).

#   blender -b --factory-startup -P make_caps.py -- <out folder>

# 4 caps: SM_WoundCap_Forearm_337 (r 4.5 cm, radius + ulna), _UpperArm (6 cm, humerus), _Calf (6.5 cm, tibia + fibula),

# _Neck (7 cm, vertebra). Each is a shallow, slightly sunken disc with a ragged skin lip, facing +X (the bone axis of a

# UE mannequin-style skeleton), pivot in the centre of the cut, so it attaches to the cut bone with no rotation.

# Look (dried, dark, nothing hanging): flesh 60,30,25 sRGB, rough 0.6 with 2-3 wet spots at 0.15; off-white bone ring

# 170,155,125 with a darker marrow; a thin rim of the zombie's skin tone. 512 px BC / ORM / N per cap.

import bpy, bmesh, sys, os, math

import numpy as np

from mathutils import Vector



OUT = sys.argv[sys.argv.index('--') + 1]

os.makedirs(OUT, exist_ok=True)

CAPS = {'Forearm': (0.045, [(-0.012, 0.004, 0.0075), (0.014, -0.003, 0.006)]),

        'UpperArm': (0.060, [(0.004, 0.0, 0.011)]),

        'Calf': (0.065, [(-0.008, 0.006, 0.013), (0.024, -0.010, 0.006)]),

        'Neck': (0.070, [(0.0, -0.022, 0.012)])}

T = 512

rng = np.random.default_rng(337)





def vnoise(freq, seed, n=T):

    r = np.random.default_rng(seed).random((freq + 1, freq + 1)).astype(np.float32)

    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)

    gx, gy = xx / n * freq, yy / n * freq

    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int); fx, fy = gx - x0, gy - y0

    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    return (r[y0, x0] * (1 - fx) + r[y0, x0 + 1] * fx) * (1 - fy) + (r[y0 + 1, x0] * (1 - fx) + r[y0 + 1, x0 + 1] * fx) * fy





def s2l(c): c = np.asarray(c, np.float32) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)





def save(name, arr, cs):

    """plain PNG writer (Blender's generated-image save wrote black), then load it for the lookdev material"""

    import zlib, struct

    a8 = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8); h, w, c = a8.shape

    raw = b''.join(b'\x00' + a8[y].tobytes() for y in range(h))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    path = os.path.join(OUT, name + '.png')
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))
    img = bpy.data.images.load(path); img.colorspace_settings.name = cs; return img





def textures(key, R, bones, seed):

    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)

    u, v = (xx / T - 0.5) * 2 * R * 1.15, (0.5 - yy / T) * 2 * R * 1.15     # metres in the cap plane

    r = np.sqrt(u * u + v * v)

    edge = R * (1 + 0.06 * (vnoise(9, seed) - 0.5) + 0.03 * (vnoise(23, seed + 1) - 0.5))

    lip = np.clip((r - edge * 0.93) / (edge * 0.04), 0, 1)                   # thin skin lip (2-3 mm)
    # muscle bundles: cells (fascicles) with thin pale fascia between them, each cell its own tint
    pts = np.random.default_rng(seed + 9).uniform(-R, R, (70, 2)).astype(np.float32)
    wu = u + (vnoise(7, seed + 11) - 0.5) * R * 0.25; wv = v + (vnoise(7, seed + 12) - 0.5) * R * 0.25   # curved, organic cells
    dd = np.sqrt((wu[..., None] - pts[:, 0]) ** 2 + (wv[..., None] - pts[:, 1]) ** 2)
    srt = np.sort(dd, axis=2); d1, d2 = srt[..., 0], srt[..., 1]
    cell = np.argmin(dd, axis=2); tint = np.random.default_rng(seed + 10).uniform(0.88, 1.15, 70)[cell]
    fascia = np.clip(1 - (d2 - d1) / (R * 0.02), 0, 1) ** 2 * (0.4 + 0.6 * vnoise(25, seed + 13))
    fib = vnoise(40, seed + 2) * 0.6 + vnoise(90, seed + 3) * 0.4
    flesh = s2l((58, 26, 22)) * (tint * (0.85 + 0.3 * fib))[..., None]
    flesh = flesh * (1 - 0.2 * fascia[..., None]) + s2l((95, 62, 52)) * 0.2 * fascia[..., None]
    fat = np.clip(1 - np.abs(r - edge * 0.9) / (edge * 0.025), 0, 1)[..., None]
    flesh = flesh * (1 - fat * 0.55) + s2l((105, 88, 58)) * fat * 0.55        # thin continuous yellowed fat layer
    skin = s2l((78, 80, 66)) * (0.9 + 0.2 * vnoise(30, seed + 5))[..., None]   # zombie skin, grey-green
    col = flesh * (1 - lip[..., None]) + skin * lip[..., None]
    rough = 0.6 + 0.1 * (fib - 0.5) - 0.1 * fascia; hgt = 0.25 * fib - 0.12 * fascia
    for (bx, by, br) in bones:
        d = np.sqrt((u - bx) ** 2 + (v - by) ** 2)
        bone = np.clip((br - d) / (br * 0.08), 0, 1)                          # solid bone section
        marrow = np.clip((br * 0.5 - d) / (br * 0.1), 0, 1)                   # dark marrow inside the cortical wall
        col = col * (1 - bone[..., None]) + s2l((160, 145, 118)) * (0.85 + 0.15 * fib[..., None]) * bone[..., None]
        col = col * (1 - marrow[..., None]) + s2l((72, 34, 26)) * (0.9 + 0.2 * fib[..., None]) * marrow[..., None]
        rough = rough * (1 - bone) + (0.5 * bone - 0.1 * marrow) * bone; hgt = hgt + bone * 0.6 - marrow * 0.3
    for i in range(3):                                                       # a few wet spots, nothing more

        cx, cy = rng.uniform(-0.5, 0.5) * R, rng.uniform(-0.5, 0.5) * R

        w = np.exp(-((u - cx) ** 2 + (v - cy) ** 2) / (2 * (R * 0.12) ** 2))

        rough = rough * (1 - w) + 0.15 * w

    hgt = hgt + lip * 0.9

    gy_, gx_ = np.gradient(hgt * 4)

    n = np.dstack([-gx_, gy_, np.ones_like(hgt)]); n /= np.linalg.norm(n, axis=2, keepdims=True)

    bc = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)

    orm = np.dstack([np.ones_like(rough) * (0.75 + 0.25 * fib), np.clip(rough, 0.05, 1), np.zeros_like(rough)])

    return (save('T_WoundCap_%s_337_BC' % key, bc, 'sRGB'), save('T_WoundCap_%s_337_ORM' % key, orm, 'Non-Color'),

            save('T_WoundCap_%s_337_N' % key, n * 0.5 + 0.5, 'Non-Color'), edge)





bpy.ops.wm.read_factory_settings(use_empty=True)

for k, (key, (R, bones)) in enumerate(CAPS.items()):

    bc, orm, nmap, _ = textures(key, R, bones, 40 + 10 * k)

    me = bpy.data.meshes.new('SM_WoundCap_%s_337' % key); bm = bmesh.new()

    rings, segs = 14, 48

    centre = bm.verts.new((0, 0, 0)); grid = []

    for i in range(1, rings + 1):

        t = i / rings; row = []

        for j in range(segs):

            a = 2 * math.pi * j / segs

            rr = R * t * (1 + (0.06 * math.sin(3 * a + k) + 0.03 * math.sin(7 * a + 2 * k)) * t)

            z = -0.006 * (1 - t * t) + (0.004 if i == rings else 0.0)       # sunken centre, raised skin lip

            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))

        grid.append(row)

    for j in range(segs): bm.faces.new((centre, grid[0][j], grid[0][(j + 1) % segs]))

    for i in range(rings - 1):

        for j in range(segs): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][(j + 1) % segs], grid[i][(j + 1) % segs]))

    # lip rolls back down the limb a little (hides the mesh seam)

    last = grid[-1]; ring2 = [bm.verts.new((v.co.x * 1.03, v.co.y * 1.03, -0.012)) for v in last]

    for j in range(segs): bm.faces.new((last[j], ring2[j], ring2[(j + 1) % segs], last[(j + 1) % segs]))

    uv = bm.loops.layers.uv.new('UVMap')

    for f in bm.faces:

        for l in f.loops: l[uv].uv = (l.vert.co.x / (2 * R * 1.15) + 0.5, l.vert.co.y / (2 * R * 1.15) + 0.5)

    bm.to_mesh(me); bm.free()

    for p in me.polygons: p.use_smooth = True

    ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)

    ob.rotation_euler = (0, math.radians(90), 0)          # cap normal +Z -> +X (bone axis)

    m = bpy.data.materials.new('M_WoundCap_337'); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; b = N['Principled BSDF']

    t1, t2, t3 = N.new('ShaderNodeTexImage'), N.new('ShaderNodeTexImage'), N.new('ShaderNodeTexImage'); t1.image, t2.image, t3.image = bc, orm, nmap

    L.new(t1.outputs[0], b.inputs['Base Color']); sp = N.new('ShaderNodeSeparateColor'); L.new(t2.outputs[0], sp.inputs[0]); L.new(sp.outputs[1], b.inputs['Roughness'])

    nm = N.new('ShaderNodeNormalMap'); L.new(t3.outputs[0], nm.inputs['Color']); L.new(nm.outputs[0], b.inputs['Normal'])

    me.materials.append(m)

    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob

    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, me.name + '.fbx'), use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',

                             axis_forward='-Y', axis_up='Z', bake_space_transform=False, mesh_smooth_type='FACE', path_mode='STRIP')

    ob.location = (0, 0.18 * k - 0.27, 0.1)

    print('cap', me.name, 'R', R, 'bones', len(bones))

# lookdev: caps side by side, grey ball, torch key + moon rim, locked exposure

import math as _m

sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 64

sc.render.resolution_x, sc.render.resolution_y = 1400, 800; sc.view_settings.view_transform = 'AgX'

w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.03, 0.035, 0.045, 1)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0.45, 0.1)); bpy.ops.object.shade_smooth()

gm = bpy.data.materials.new('grey'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.18, 0.18, 1)

bpy.context.active_object.data.materials.append(gm)

bpy.ops.object.light_add(type='POINT', location=(0.6, -0.3, 0.5)); l1 = bpy.context.active_object; l1.data.energy = 25; l1.data.color = (1.0, 0.52, 0.22)

bpy.ops.object.light_add(type='SUN', rotation=(_m.radians(40), 0, _m.radians(-120))); bpy.context.active_object.data.energy = 0.3; bpy.context.active_object.data.color = (0.6, 0.72, 1.0)

bpy.ops.object.camera_add(location=(0.55, 0.05, 0.12), rotation=(_m.radians(90), 0, _m.radians(90))); sc.camera = bpy.context.active_object; sc.camera.data.lens = 26

os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)

sc.render.filepath = os.path.join(OUT, 'renders', 'woundcaps_lookdev.jpg'); sc.render.image_settings.file_format = 'JPEG'; bpy.ops.render.render(write_still=True)


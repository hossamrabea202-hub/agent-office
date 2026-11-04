# Castle Defender - box masonry generator (i9, 11-03).
# Turns a plain box (size in cm) into coursed ashlar: closed rounded stone blocks (watertight Minkowski rounding,
# chipped arrises, tooled faces), quoins alternating per course, optional coping slabs, mortar core.
# Each stone face gets a clean stone patch of T_vdbhdju_B (texrects.json), like the tunnel vault.
# Run: blender -b -P gen_boxmason.py -- specs.json   (Blender m = UE m; mesh centred on the box pivot; Y mirrored for FBX)
import bpy, bmesh, json, math, random, os, sys, functools, builtins
from mathutils import Vector, noise
print = functools.partial(builtins.print, flush=True)
import numpy as np

SPEC = json.load(open(sys.argv[sys.argv.index('--') + 1])) if '--' in sys.argv and __name__ == '__main__' else None
OUT = SPEC['out'] if SPEC else None
if OUT: os.makedirs(OUT, exist_ok=True)
RECTS = json.load(open('C:/Users/hossa/sync58/tunnel/texrects.json'))
JOINT = 0.012
SHARP = os.environ.get('MASON_SOFT') is None

def pick_rect(w, h):
    best = sorted(RECTS, key=lambda r: abs((r[2] - r[0]) * 3.2 - w) + abs((r[3] - r[1]) * 3.2 - h) + random.random() * 0.12)[:4]
    return random.choice(best)

def edge_lines(L, rb, inner):
    n = max(1, int((L - 2 * rb) / inner))
    fr = (0.0, 0.06, 0.16, 0.30, 0.48, 0.72, 1.0) if os.environ.get('MASON_SOFT') is None else (0.0, 0.35, 0.75, 1.0)   # SHARP: 6 segments round worn arrises
    a = [rb * f for f in fr]
    return a + [rb + (L - 2 * rb) * k / n for k in range(1, n)] + [L - x for x in a[::-1]]

class Buf:
    def __init__(s): s.v, s.f, s.uv, s.col, s.mat = [], [], [], [], []

def rbox(B, c, h, rb=None, rock=None, tone=None, damp=0.0, inner=0.09, skip=()):
    """Closed rounded stone block centred at c with half sizes h (Vectors, metres)."""
    # 11-04 SHARP (research: dressed ashlar arrises 3-8 mm, flat faces, 'sharp rocks beat rounded scans'); MASON_SOFT=1 = old pillow look
    if SHARP:
        rb = max(0.003, rb * 0.4) if rb is not None else (random.uniform(0.010, 0.018) if random.random() < 0.15 else random.uniform(0.003, 0.008))
    else:
        rb = rb if rb is not None else (random.uniform(0.022, 0.04) if random.random() < 0.2 else random.uniform(0.008, 0.02))
    rb = min(rb, h.x * 0.45, h.y * 0.45, h.z * 0.45)
    rock = rock if rock is not None else (2.2 if random.random() < 0.3 else 1.0)
    tone = random.random() if tone is None else tone
    seed = Vector((random.uniform(0, 500), random.uniform(0, 500), random.uniform(0, 500)))
    bul = random.uniform(0.0, 0.002) if SHARP else random.uniform(0.003, 0.01)
    # chips: points on random edges of the block
    chips = []
    for _ in range(random.randint(2, 6) + (2 if rock > 1 else 0) if SHARP else random.randint(1, 4) + (2 if rock > 1 else 0)):
        ax = random.randrange(3); p = Vector((random.choice((-1, 1)) * h.x, random.choice((-1, 1)) * h.y, random.choice((-1, 1)) * h.z))
        p[ax] = random.uniform(-h[ax], h[ax]); chips.append((p, random.uniform(0.03, 0.09)))
    if random.random() < 0.15: chips.append((Vector((random.choice((-1, 1)) * h.x, random.choice((-1, 1)) * h.y, random.choice((-1, 1)) * h.z)), random.uniform(0.08, 0.14)))
    core = Vector((h.x - rb, h.y - rb, h.z - rb))
    for ax in range(3):
        for sg in (-1, 1):
            if (ax, sg) in skip: continue
            i, j = [k for k in range(3) if k != ax]
            eb = max(rb, 0.05) if SHARP else rb               # SHARP: tessellate 5 cm in from each arris for the worn corners
            xs, ys = edge_lines(2 * h[i], min(eb, h[i] * 0.45), inner), edge_lines(2 * h[j], min(eb, h[j] * 0.45), inner)
            nx, ny = len(xs), len(ys)
            r = pick_rect(2 * h[i], 2 * h[j]); flip = random.random() < 0.5
            ix, iy = (r[2] - r[0]) * 0.08, (r[3] - r[1]) * 0.10
            ru0, rv0, ru1, rv1 = r[0] + ix, r[1] + iy, r[2] - ix, r[3] - iy
            st = len(B.v)
            for y in ys:
                for x in xs:
                    p = Vector((0, 0, 0)); p[ax] = sg * h[ax]; p[i] = x - h[i]; p[j] = y - h[j]
                    # SHARP chips (11-04): a chip is a locally LARGER corner radius (a knocked, worn arris), not a dent
                    # pushed along the edge normal - every vertex stays on a valid rounded box, so faces cannot fold
                    rl = rb
                    if SHARP:
                        # hand-dressed arris: the radius wanders along the edge (+-60 %, ~12 cm and ~4 cm waves)
                        for cp, rc in chips:
                            dd = (p - cp).length
                            if dd < rc:
                                t = 1 - dd / rc; rl = max(rl, rb + 0.4 * rc * t * t * (3 - 2 * t))   # smoothstep: slope <= 0.6, cannot fold
                        rl = min(rl, h.x * 0.45, h.y * 0.45, h.z * 0.45)
                    cl = Vector((h.x - rl, h.y - rl, h.z - rl))
                    q = Vector((max(-cl.x, min(cl.x, p.x)), max(-cl.y, min(cl.y, p.y)), max(-cl.z, min(cl.z, p.z))))
                    d = p - q
                    dn = d.normalized() if d.length > 1e-9 else Vector((0, 0, 0))
                    if d.length <= 1e-9: dn[ax] = sg
                    pr = q + dn * rl
                    w = pr + c
                    fx, fy = x / (2 * h[i]), y / (2 * h[j])
                    qn = w * 3.1 + seed
                    lf = (0.35 * (1.0 + 0.5 * (rock - 1.0))) if SHARP else rock          # SHARP: dressed face, waviness ~ +-3 mm
                    off = lf * (0.008 * noise.noise(qn * 0.7) + 0.004 * noise.noise(qn * 2.3)) + 0.0016 * noise.noise(qn * 6.5) + 0.0007 * noise.noise(qn * 17.0)
                    off += bul * max(0.0, 1 - (2 * fx - 1) ** 2) * max(0.0, 1 - (2 * fy - 1) ** 2)
                    cav = min(1.0, (d.length / rl) if rl > 0 else 0)
                    for cp, rc in chips:
                        dd = (pr - cp).length
                        if dd < rc:
                            k = (rc - dd) / rc; cav = max(cav, k)
                            if not SHARP: off -= rc * 0.45 * k            # old soft-mode dent
                    # (arris waver tried 11-04: folded 4-8 % of faces in the lookdev check -> removed)
                    B.v.append(w + dn * off)
                    uu = ru0 + (ru1 - ru0) * (1 - fx if flip else fx); vv = rv0 + (rv1 - rv0) * (1 - fy if flip else fy)
                    B.uv.append((uu, 1 - vv)); B.col.append((tone, damp, cav, 1.0))
            # winding: outward normal = sg * e_ax ; (e_i x e_j) has the sign of the axis permutation
            par = 1 if (i, j) in ((1, 2), (2, 0), (0, 1)) else -1
            outward = sg * par > 0
            for yy in range(ny - 1):
                for xx in range(nx - 1):
                    a0 = st + yy * nx + xx
                    quad = (a0, a0 + 1, a0 + nx + 1, a0 + nx)
                    B.f.append(quad if outward else quad[::-1]); B.mat.append(0)

def runs(a0, a1, lo, hi, minlast=0.3):
    out, a = [], a0
    while a1 - a > hi:
        L = random.uniform(lo, hi)
        if a1 - (a + L) < minlast: L = (a1 - a) / 2
        out.append((a, a + L)); a += L
    out.append((a, a1)); return out

def core_box(B, h, bottom=False):
    """Mortar core behind the joints (bottom optional)."""
    c = [Vector((sx * h.x, sy * h.y, sz * h.z)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    st = len(B.v)
    for p in c: B.v.append(p); B.uv.append((p.x * 0.5 + p.y * 0.5, p.z * 0.5)); B.col.append((0.5, 0.0, 1.0, 1.0))
    for q in ((4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)) + (((0, 2, 3, 1),) if bottom else ()):
        B.f.append(tuple(st + k for k in q)); B.mat.append(1)

def masonry(spec):
    random.seed(spec.get('seed', 1103))
    S = Vector(spec['size']) / 100.0; H = S / 2
    B = Buf()
    if spec.get('single'):
        rbox(B, Vector((0, 0, 0)), H - Vector((0.004, 0.004, 0.004)), rb=spec.get('rb', 0.05), rock=spec.get('rock', 2.0), tone=0.7, inner=0.12)
        return B
    t = spec.get('depth', 0.38); lo, hi = spec.get('len', (0.5, 1.0)); chmin, chmax = spec.get('course', (0.45, 0.58))
    z0, z1 = -H.z, H.z
    cop = spec.get('coping', 0.0)
    if cop: z1 -= cop
    n = max(1, round((z1 - z0) / ((chmin + chmax) / 2)))
    hs = [random.uniform(chmin, chmax) for _ in range(n)]; sc = (z1 - z0) / sum(hs); hs = [x * sc for x in hs]
    J2 = JOINT / 2; z = z0
    for k, ch in enumerate(hs):
        za, zb = z + J2, z + ch - J2; zc, zh = (za + zb) / 2, (zb - za) / 2
        damp = max(0.0, 1.0 - (z - z0) / 1.5) * spec.get('damp', 0.6)
        xfull = (k % 2 == 0)
        # faces normal to +-Y run along X; faces normal to +-X run along Y
        for sgy in (-1, 1):
            xa, xb = (-H.x, H.x) if xfull else (-H.x + t, H.x - t)
            for a, b in runs(xa, xb, lo, hi):
                inset = random.uniform(-0.006, 0.01)
                rbox(B, Vector(((a + b) / 2, sgy * (H.y - t / 2 - inset), zc)), Vector(((b - a) / 2 - J2, t / 2, zh)), damp=damp)
        for sgx in (-1, 1):
            ya, yb = (-H.y + t, H.y - t) if xfull else (-H.y, H.y)
            if yb - ya < 0.12: continue
            for a, b in runs(ya, yb, lo, hi):
                inset = random.uniform(-0.006, 0.01)
                rbox(B, Vector((sgx * (H.x - t / 2 - inset), (a + b) / 2, zc)), Vector((t / 2, (b - a) / 2 - J2, zh)), damp=damp)
        z += ch
    if spec.get('top', True) and not cop:     # cap the top inside the wall faces
        for a, b in runs(-H.x + t, H.x - t, lo, hi):
            rbox(B, Vector(((a + b) / 2, 0, H.z - 0.1)), Vector(((b - a) / 2 - J2, H.y - t - J2, 0.1 - J2)))
    if spec.get('bottom'):                    # soffit stones under a lintel
        for a, b in runs(-H.x + t, H.x - t, lo, hi):
            rbox(B, Vector(((a + b) / 2, 0, -H.z + 0.1)), Vector(((b - a) / 2 - J2, H.y - t - J2, 0.1 - J2)))
    if cop:                                   # coping slabs over the whole top, chamfered by a big rounding
        across = runs(-H.y, H.y, 0.9, 1.6) if S.y > 1.8 else [(-H.y, H.y)]
        for a, b in runs(-H.x, H.x, 0.8, 1.4):
            for c0, c1 in across:
                rbox(B, Vector(((a + b) / 2, (c0 + c1) / 2, H.z - cop / 2)), Vector(((b - a) / 2 - J2, (c1 - c0) / 2 - J2, cop / 2 - J2)), rb=random.uniform(0.03, 0.05))
    core_box(B, H - Vector((0.03, 0.03, 0.03 if spec.get('bottom') else 0.0)), bottom=spec.get('bottom', False))
    return B

if __name__ == '__main__':
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    mats = [bpy.data.materials.new('M_Tun_Ashlar'), bpy.data.materials.new('M_Tun_Mortar')]
    info = []
    for spec in SPEC['boxes']:
        B = masonry(spec)
        me = bpy.data.meshes.new(spec['name'])
        me.from_pydata([(p.x, -p.y, p.z) for p in B.v], [], B.f)
        for m in mats: me.materials.append(m)
        me.polygons.foreach_set('material_index', B.mat)
        lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
        me.uv_layers.new(name='UV0').data.foreach_set('uv', np.asarray(B.uv, dtype=np.float32)[lv].ravel())
        me.attributes.new('Col', 'FLOAT_COLOR', 'CORNER').data.foreach_set('color', np.clip(np.asarray(B.col, dtype=np.float32), 0, 1)[lv].ravel())
        me.flip_normals()                          # Y mirror flipped the winding
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
        me.shade_smooth()
        ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)
        # outward check: share of faces whose normal points away from the box centre
        pc = np.empty(len(me.polygons) * 3, dtype=np.float32); me.polygons.foreach_get('center', pc); pc = pc.reshape(-1, 3)
        pn = np.empty(len(me.polygons) * 3, dtype=np.float32); me.polygons.foreach_get('normal', pn); pn = pn.reshape(-1, 3)
        outw = float(np.mean(np.sum(pc * pn, axis=1) > 0))
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath='%s/%s.fbx' % (OUT, me.name), use_selection=True, mesh_smooth_type='FACE', add_leaf_bones=False,
                                 bake_anim=False, axis_forward='-Z', axis_up='Y', apply_scale_options='FBX_SCALE_NONE', colors_type='LINEAR')
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        info.append({'name': me.name, 'tris': tris, 'outward': outw})
        print('BOX', me.name, 'tris', tris, 'outward %.2f' % outw)
    json.dump(info, open('%s/boxes_built.json' % OUT, 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath='%s/boxmason.blend' % OUT)
    print('BOX DONE')

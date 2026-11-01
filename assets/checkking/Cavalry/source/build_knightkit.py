# #403 Cavalry knight kit on the destrier skeleton. checkking (Claude), 2026-11-01. Original, procedural.
#   blender -b <work>/destrier_anim.blend -P build_knightkit.py -- <work>    -> knightkit.blend, out/SK_Destrier_Lance.fbx,
#                                                                            out/SK_Destrier_RiderLegs.fbx, out/tex/T_Lance_*, T_RiderLegs_*
# Why skinned to the horse skeleton (not attached props): the lance rides the 'lance' bone, so it is upright in idle /
# walk / trot and couched in the gallop exactly as animated, with no socket-axis guesswork in UE. The rider's legs ride
# the saddle (spine_01): mail chausses, plate knee cops and sabatons in the stirrups, plus a surcoat skirt in the arms
# (Or an eagle sable) that hides the join with the knight's own upper body (its legs hidden at the thighs in the BP).
#   SK_Destrier_Lance: 3.4 m ash lance, swelling grip, steel vamplate, leaf head, swallowtail pennon. Couched in the rest
#     pose: pivot at the rider's right armpit, 2.65 m forward, 0.75 m behind.
#   SK_Destrier_RiderLegs: long-stirrup war seat (legs nearly straight, a little forward).
import bpy, bmesh, numpy as np, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cavlib import lin, to_srgb, ss, mix
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
D = argv[0] if argv else os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(D, 'out'); TEX = os.path.join(OUT, 'tex'); os.makedirs(TEX, exist_ok=True)
sc = bpy.context.scene
arm = bpy.data.objects['SK_Destrier_Rig']; arm.animation_data.action = None
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
body = bpy.data.objects['SK_Destrier']; tack = bpy.data.objects['SK_Destrier_Tack']
dg = bpy.context.evaluated_depsgraph_get(); bvh_t = BVHTree.FromObject(tack, dg)

def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    ref = np.array([0, 0, 1.0]) if abs(T[0] @ [0, 0, 1]) < 0.9 else np.array([1.0, 0, 0])
    N = np.zeros_like(P); n = ref - (ref @ T[0]) * T[0]; n /= np.linalg.norm(n)
    for i in range(len(P)):
        n = n - (n @ T[i]) * T[i]; n /= np.linalg.norm(n) + 1e-9; N[i] = n
    return T, N, np.cross(T, N)
def loft(P, rx, ry, seg=16, caps=True):
    P = np.asarray(P, float); T, N, B = frames(P); V, F = [], []
    for i in range(len(P)):
        for k in range(seg):
            a = 2 * math.pi * k / seg; V.append(P[i] + rx[i] * math.cos(a) * N[i] + ry[i] * math.sin(a) * B[i])
    for i in range(len(P) - 1):
        for k in range(seg): F.append([i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k])
    if caps: F.append(list(range(seg))[::-1]); F.append([(len(P) - 1) * seg + k for k in range(seg)])
    return V, F
def path(pts, n):
    pts = np.asarray(pts, float); out = []
    for k in range(n):
        s = k / (n - 1) * (len(pts) - 1); i = min(int(s), len(pts) - 2); t = s - i
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)
class Acc:
    def __init__(s): s.V, s.F, s.P = [], [], []
    def add(s, V, F, part):
        o = len(s.V); s.V += [tuple(v) for v in V]; s.F += [[i + o for i in f] for f in F]; s.P += [part] * len(V)
def make(name, acc, bone_weights):
    me = bpy.data.meshes.new(name); me.from_pydata(acc.V, [], acc.F); me.update(); me.validate()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ca = me.color_attributes.new('Part', 'FLOAT_COLOR', 'POINT'); pc = np.zeros((len(me.vertices), 4), np.float32)
    pc[:, 0] = np.array(acc.P[:len(me.vertices)]) / 10.0; pc[:, 3] = 1; ca.data.foreach_set('color', pc.ravel())
    for p in me.polygons: p.use_smooth = True
    for o in sc.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    try: bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
    except Exception: pass
    for bn, w in bone_weights:
        vg = ob.vertex_groups.new(name=bn); vg.add(list(range(len(me.vertices))), w, 'REPLACE')
    mo = ob.modifiers.new('Armature', 'ARMATURE'); mo.object = arm; ob.parent = arm
    m = bpy.data.materials.get('M_' + name.replace('SK_Destrier_', '')) or bpy.data.materials.new('M_' + name.replace('SK_Destrier_', ''))
    me.materials.append(m)
    print(name, 'tris', sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
    return ob

# ================================================================ lance (along -Y in the rest pose, pivot at the armpit)
PIV = np.array([-0.26, -0.18, 2.12]); FWD = np.array([0, -1.0, 0])
L = Acc()
s = np.array([-0.75, -0.25, -0.12, -0.05, 0.0, 0.10, 0.20, 0.6, 1.4, 2.2, 2.62])          # metres along the lance (+ = forward)
r = np.array([0.028, 0.032, 0.046, 0.046, 0.040, 0.034, 0.036, 0.034, 0.030, 0.025, 0.022])
ss_ = np.linspace(s[0], s[-1], 70); rr_ = np.interp(ss_, s, r)
L.add(*loft(PIV[None] + ss_[:, None] * FWD[None], rr_, rr_, 14), 1)                       # ash shaft (1)
L.add(*loft(PIV[None] + np.array([0.15, 0.16, 0.22, 0.30])[:, None] * FWD[None], np.array([0.04, 0.10, 0.095, 0.038]), np.array([0.04, 0.10, 0.095, 0.038]), 24), 2)  # vamplate (2 steel)
hs = np.linspace(2.62, 2.86, 14); hr = np.interp(hs, [2.62, 2.66, 2.72, 2.86], [0.024, 0.02, 0.03, 0.0])
L.add(*loft(PIV[None] + hs[:, None] * FWD[None], hr, hr * 0.35, 8), 2)                     # leaf head, flattened
L.add(*loft(PIV[None] + np.array([2.58, 2.66])[:, None] * FWD[None], np.array([0.027, 0.027]), np.array([0.027, 0.027]), 12), 2)   # socket
# pennon: swallowtail, hangs from the shaft below the head, a few waves
pv, pf = [], []; NU, NV = 12, 6
for i in range(NU + 1):
    for j in range(NV + 1):
        u = i / NU; v = j / NV
        tail_cut = 0.35 * u * (1 - abs(2 * v - 1)) if u > 0.6 else 0.0
        along = 2.50 - 0.50 * u + tail_cut * 0.0
        depth = -0.03 - 0.20 * v * (1 - 0.25 * u)
        wave = 0.02 * math.sin(u * 7 + v * 2) * u
        pv.append(PIV + np.array([wave, -along, depth]))
for i in range(NU):
    for j in range(NV):
        u0 = (i + 0.5) / NU; v0 = (j + 0.5) / NV
        if u0 > 0.72 and abs(v0 - 0.5) < (u0 - 0.72) * 1.4: continue          # the swallowtail notch
        a = i * (NV + 1) + j; pf.append([a, a + NV + 1, a + NV + 2, a + 1])
n0 = len(pv); pv2 = pv + [p + np.array([0.003, 0, 0]) for p in pv]; pf2 = pf + [[k + n0 for k in f[::-1]] for f in pf]
L.add(pv2, pf2, 3)                                                                          # wool pennon (3)
lance = make('SK_Destrier_Lance', L, [('lance', 1.0)])

# ================================================================ rider legs + surcoat skirt (rigid on the saddle)
G = Acc()
def outside(p, minoff=0.025):
    """push a point out of the tack/caparison if it ended up inside."""
    loc, nrm, _, d = bvh_t.find_nearest(Vector(p))
    if loc is None: return np.asarray(p)
    v = Vector(p) - loc
    if v.dot(nrm) < minoff: return np.array(loc + nrm * minoff)
    return np.asarray(p)
for sg in (1, -1):
    hip = np.array([0.15 * sg, -0.20, 1.70]); knee = np.array([0.50 * sg, -0.40, 1.20]); ankle = np.array([0.45 * sg, -0.30, 0.80])
    P = path([hip, hip + (knee - hip) * 0.5 + np.array([0.06 * sg, 0, 0.02]), knee, ankle], 30)
    P = np.array([outside(p, 0.08) if i > 4 else p for i, p in enumerate(P)])
    t = np.linspace(0, 1, 30)
    rad = np.interp(t, [0, 0.3, 0.55, 0.62, 0.8, 1.0], [0.095, 0.085, 0.062, 0.065, 0.062, 0.046])
    G.add(*loft(P, rad, rad * 0.9, 16), 1)                                                   # mail chausses (1)
    kc = knee + np.array([0.0, -0.035, 0.0])                                                 # poleyn (knee cop) + wing
    G.add(*loft(path([kc + np.array([0, 0, 0.09]), kc, kc - np.array([0, 0, 0.09])], 10), np.array([0.02, 0.06, 0.075, 0.078, 0.076, 0.07, 0.06, 0.05, 0.03, 0.0]) + 0.005, np.array([0.02, 0.06, 0.075, 0.078, 0.076, 0.07, 0.06, 0.05, 0.03, 0.0]), 16), 2)
    toe = ankle + np.array([0, -0.24, -0.06]); heel = ankle + np.array([0, 0.05, -0.05])     # sabaton in the stirrup
    G.add(*loft(path([heel, ankle + np.array([0, -0.04, -0.03]), toe], 12), np.array([0.04, 0.05, 0.055, 0.055, 0.052, 0.05, 0.046, 0.042, 0.036, 0.028, 0.018, 0.0]), np.array([0.05, 0.055, 0.055, 0.052, 0.05, 0.046, 0.042, 0.038, 0.032, 0.024, 0.014, 0.0]), 16), 2)
    for k in range(4):                                                                       # sabaton lames
        c = ankle + np.array([0, -0.06 - 0.045 * k, -0.035 - 0.006 * k])
        G.add(*loft(np.array([c + np.array([0, 0.012, 0]), c - np.array([0, 0.012, 0])]), np.array([0.058 - 0.006 * k] * 2), np.array([0.05 - 0.006 * k] * 2), 16), 2)
    G.add(*loft(path([knee + np.array([0, 0.02, 0.10]), knee + np.array([0, 0.03, 0.14])], 4), np.full(4, 0.082), np.full(4, 0.076), 16), 4)   # garter strap (leather)
# surcoat skirt: from the waist, over the thighs, split front and back by the saddle bows
SKN, SKR = 40, 10
sv, sf = [], []
for i in range(SKR + 1):
    t = i / SKR; z = 1.92 - 0.50 * t
    for k in range(SKN):
        a = 2 * math.pi * k / SKN
        rx = 0.17 + 0.32 * t ** 1.2; ry = 0.14 + 0.08 * t
        p = np.array([rx * math.cos(a), -0.22 + ry * math.sin(a), z - 0.06 * t * abs(math.cos(a))])
        sv.append(outside(p, 0.03) if t > 0.3 else p)
for i in range(SKR):
    for k in range(SKN):
        a0 = 2 * math.pi * (k + 0.5) / SKN
        if i > 3 and abs(math.sin(a0)) > 0.93: continue                                       # front + back slits for the saddle
        sf.append([i * SKN + k, i * SKN + (k + 1) % SKN, (i + 1) * SKN + (k + 1) % SKN, (i + 1) * SKN + k])
n0 = len(sv); sv2 = sv + [np.asarray(p) * np.array([0.985, 1, 1]) + np.array([0, -0.22 * 0.015, 0]) for p in sv]
sf2 = [f[::-1] for f in sf] + [[k + n0 for k in f] for f in sf]
G.add(sv2, sf2, 3)                                                                           # wool surcoat (3)
legs = make('SK_Destrier_RiderLegs', G, [('spine_01', 1.0)])

# ================================================================ textures (data bakes + numpy, like the tack)
def bake_set(ob, prefix, res, paint):
    mat = bpy.data.materials.new('M_Bake_' + prefix); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], outn.inputs[0])
    img = bpy.data.images.new('bake', res, res, float_buffer=True, alpha=False); img.colorspace_settings.name = 'Non-Color'
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; nt.nodes.active = tx
    keep = list(ob.data.materials); ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in sc.objects: o.select_set(False); o.hide_render = (o != ob)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    geo = nt.nodes.new('ShaderNodeNewGeometry'); one = nt.nodes.new('ShaderNodeRGB'); one.outputs[0].default_value = (1, 1, 1, 1)
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'Part'
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    def bk(kind, samples=1):
        sc.cycles.samples = samples; sc.render.bake.margin = 6; sc.render.bake.margin_type = 'EXTEND'; sc.render.bake.target = 'IMAGE_TEXTURES'
        bpy.ops.object.bake(type=kind); px = np.empty(res * res * 4, np.float32); img.pixels.foreach_get(px); return px.reshape(res, res, 4)[..., :3].copy()
    nt.links.new(one.outputs[0], em.inputs['Color']); used = bk('EMIT')[..., 0] > 0.5
    nt.links.new(geo.outputs['Position'], em.inputs['Color']); P = bk('EMIT')[used]
    nt.links.new(geo.outputs['Normal'], em.inputs['Color']); N = bk('EMIT')[used]
    nt.links.new(at.outputs['Color'], em.inputs['Color']); PID = np.round(bk('EMIT')[used][:, 0] * 10).astype(np.int32)
    m2 = bpy.data.materials.new('M_AO'); m2.use_nodes = True; t2 = m2.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = img; m2.node_tree.nodes.active = t2
    ob.data.materials.clear(); ob.data.materials.append(m2)
    if sc.world is None: sc.world = bpy.data.worlds.new('W')
    sc.world.light_settings.distance = 0.3
    AO = bk('AO', 48)[..., 0][used]
    ob.data.materials.clear()
    for m in keep: ob.data.materials.append(m)
    for o in sc.objects: o.hide_render = False
    col, rg, mt, h = paint(P, N, PID, AO)
    def save(name, rgb):
        im = bpy.data.images.new(name, res, res, alpha=False); im.colorspace_settings.name = 'Non-Color'
        a = np.ones((res, res, 4), np.float32); a[..., :3] = rgb; im.pixels.foreach_set(np.clip(a, 0, 1).ravel())
        im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im); print('SAVED', name, flush=True)
    bc = np.zeros((res, res, 3), np.float32); bc[used] = to_srgb(col); save(prefix + '_BC', bc)
    orm = np.zeros((res, res, 3), np.float32); orm[used, 0] = AO; orm[used, 1] = rg; orm[used, 2] = mt; save(prefix + '_ORM', orm)
    H = np.zeros((res, res), np.float32); H[used] = h; gy, gx = np.gradient(H); tpm = res * 1.2
    nrm = np.stack([-gx * tpm, -gy * tpm, np.ones_like(gx)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True); nrm[~used] = (0, 0, 1)
    g = nrm * 0.5 + 0.5; save(prefix + '_N_GL', g); g[..., 1] = 1 - g[..., 1]; save(prefix + '_N', g)
def vn(p, f, seed=0):
    q = p * f; i = np.floor(q).astype(np.int64); t = q - i; t = t * t * (3 - 2 * t)
    def hh(dx, dy, dz):
        n = ((i[:, 0] + dx) * 73856093) ^ ((i[:, 1] + dy) * 19349663) ^ ((i[:, 2] + dz) * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16); return (n & 0xFFFF).astype(np.float32) / 65535.0
    x0 = hh(0, 0, 0) + (hh(1, 0, 0) - hh(0, 0, 0)) * t[:, 0]; x1 = hh(0, 1, 0) + (hh(1, 1, 0) - hh(0, 1, 0)) * t[:, 0]
    x2 = hh(0, 0, 1) + (hh(1, 0, 1) - hh(0, 0, 1)) * t[:, 0]; x3 = hh(0, 1, 1) + (hh(1, 1, 1) - hh(0, 1, 1)) * t[:, 0]
    y0 = x0 + (x1 - x0) * t[:, 1]; y1 = x2 + (x3 - x2) * t[:, 1]; return y0 + (y1 - y0) * t[:, 2]
YELLOW = lin(180, 146, 64); BLACK = lin(46, 42, 40)
def paint_lance(P, N, PID, AO):
    M = len(P); col = np.zeros((M, 3), np.float32); rg = np.zeros(M, np.float32); mt = np.zeros(M, np.float32); h = np.zeros(M, np.float32)
    along = -(P[:, 1] - PIV[1])                                                                # metres forward of the pivot
    ang = np.arctan2(P[:, 2] - PIV[2], P[:, 0] - PIV[0])
    grain = vn(np.stack([P[:, 0] * 40, P[:, 1] * 2, P[:, 2] * 40], 1), 1.0, 1)
    ash = PID == 1
    spiral = (np.sin(ang * 1 + along * 2 * math.pi / 0.5) > 0.0) & (along > 0.35) & (along < 2.5)   # painted spiral bands in the arms
    col[ash] = lin(170, 140, 100) * (0.85 + 0.25 * grain[ash])[:, None]
    col[ash & spiral] = YELLOW * 0.95; col[ash & ~spiral & (along > 0.35) & (along < 2.5)] = BLACK
    grip = (along > -0.12) & (along < 0.10); col[ash & grip] = lin(70, 48, 34); rg[ash] = 0.6; rg[ash & grip] = 0.5
    rg[ash] = rg[ash] + 0.15 * (grain[ash] - 0.5); h[ash] = 0.0002 * grain[ash]
    st = PID == 2; col[st] = lin(196, 194, 190); mt[st] = 1; rg[st] = 0.32 + 0.12 * (vn(P[st], 80, 3) - 0.5)
    wo = PID == 3
    pen = vn(P, 30, 4)
    col[wo] = YELLOW * (0.9 + 0.15 * pen[wo])[:, None]
    tailz = (P[:, 2] < PIV[2] - 0.12); col[wo & tailz] = BLACK                                 # lower half black: per pale, Or and sable
    rg[wo] = 0.9
    col = mix(col, col * 0.8, 0.3 * (1 - ss(0.5, 0.95, AO)))
    return col, np.clip(rg, 0.05, 0.97), mt, h
def paint_legs(P, N, PID, AO):
    M = len(P); col = np.zeros((M, 3), np.float32); rg = np.zeros(M, np.float32); mt = np.zeros(M, np.float32); h = np.zeros(M, np.float32)
    mail = PID == 1
    # 4-in-1 mail: rows of rings; bright ring crowns, dark holes (the holes hide the tiling, INDUSTRY_SECRETS 3.3)
    q = P * 160.0; ring = np.abs(np.sin(q[:, 0] * 1.0 + q[:, 1]) * np.sin(q[:, 2] * 1.2 + 0.5 * np.sin(q[:, 0])))
    crown = ss(0.35, 0.8, ring)
    col[mail] = mix(np.tile(lin(60, 56, 52), (int(mail.sum()), 1)), np.tile(lin(190, 188, 184), (int(mail.sum()), 1)), crown[mail])
    mt[mail] = (crown[mail] > 0.5).astype(np.float32); rg[mail] = np.where(mt[mail] > 0.5, 0.35, 0.75)
    col[mail] = np.where(mt[mail][:, None] > 0.5, lin(190, 188, 184), col[mail])
    h[mail] = 0.0012 * crown[mail]
    st = PID == 2; col[st] = lin(198, 196, 192); mt[st] = 1; rg[st] = 0.28 + 0.12 * (vn(P[st], 60, 5) - 0.5)
    le = PID == 4; col[le] = lin(72, 50, 36); rg[le] = 0.6
    wo = PID == 3; col[wo] = YELLOW * (0.9 + 0.15 * vn(P[wo], 20, 6))[:, None]; rg[wo] = 0.9
    hem = (PID == 3) & (P[:, 2] < 1.47); col[hem] = BLACK
    mud = ss(1.0, 0.75, P[:, 2]) * ss(0.6, 0.8, vn(P, 12, 7)); col = mix(col, lin(88, 72, 56), mud * 0.6 * (~st)); mt = np.where(mud > 0.5, 0, mt)
    col = mix(col, col * 0.8, 0.3 * (1 - ss(0.5, 0.95, AO)))
    return col, np.clip(rg, 0.05, 0.97), mt, h
bake_set(lance, 'T_Lance', 1024, paint_lance)
bake_set(legs, 'T_RiderLegs', 1024, paint_legs)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'knightkit.blend'))
arm.name = 'Armature'
for name, ob in (('SK_Destrier_Lance', lance), ('SK_Destrier_RiderLegs', legs)):
    for o in sc.objects: o.select_set(o in (arm, ob))
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + '.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE', use_tspace=True, apply_scale_options='FBX_SCALE_ALL',
                             primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL')
    print('FBX OK', name, flush=True)
arm.name = 'SK_Destrier_Rig'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'knightkit.blend'))
print('KIT OK', flush=True)

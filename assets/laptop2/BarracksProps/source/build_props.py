# Barracks props (#14, laptop2 2026-10-30): WeaponRack, Crate, Barrel, Sack. Knowledge-base standard: real scale,
# bevels >= 3 mm, warp and sag, physical wear in the materials (propmat/gatemat).
#   blender -b --factory-startup -P build_props.py      (env RES = low | high, VARIANT = WeaponRack | Crate | Barrel | Sack)
# Units: metres, Z up, the prop stands on z 0 with its pivot at the base centre.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import kitlog
from kitlog import log
from propkit import plank, strap, nails, group
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, dome, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Crate')
rng = np.random.default_rng({'WeaponRack': 141, 'Crate': 142, 'Barrel': 143, 'Sack': 144}[VAR])
j = lambda a=0.004: rng.uniform(-a, a)

if VAR == 'Crate':      # 0.7 x 0.5 x 0.45 m shipping crate: plank sides on a frame, iron corner straps, a lid nailed shut
    W, Dp, H, T = 0.70, 0.50, 0.45, 0.022
    for k, (y, nrm) in enumerate(((-Dp / 2, (0, -1.0, 0)), (Dp / 2, (0, 1.0, 0)))):        # front/back: 4 boards each
        for b in range(4):
            z = T + (H - 2 * T) * (b + 0.5) / 4
            plank('Side', (-W / 2 + 0.01, y + j(0.002), z + j(0.003)), (W / 2 - 0.01, y + j(0.002), z + j(0.003)), (H - 2 * T) / 4 - 0.004, T, 300 + k * 10 + b, nrm, rot=0.25 if b == 0 else 0.05)
    for k, (x, nrm) in enumerate(((-W / 2, (-1.0, 0, 0)), (W / 2, (1.0, 0, 0)))):          # ends: 4 boards each
        for b in range(4):
            z = T + (H - 2 * T) * (b + 0.5) / 4
            plank('End', (x + j(0.002), -Dp / 2 + 0.03, z + j(0.003)), (x + j(0.002), Dp / 2 - 0.03, z + j(0.003)), (H - 2 * T) / 4 - 0.004, T, 320 + k * 10 + b, nrm, rot=0.25 if b == 0 else 0.05)
    for b in range(5):     # lid boards (one slightly lifted), bottom boards
        y = -Dp / 2 + 0.02 + (Dp - 0.04) * (b + 0.5) / 5
        plank('Lid', (-W / 2 - 0.015, y, H - T / 2 + (0.012 if b == 4 else 0) + j(0.002)), (W / 2 + 0.015, y + j(0.003), H - T / 2 + (0.02 if b == 4 else 0)), (Dp - 0.04) / 5 - 0.004, T, 340 + b, (0, 0, 1.0), rot=0.0)
        plank('Bottom', (-W / 2, y, T / 2), (W / 2, y, T / 2), (Dp - 0.04) / 5 - 0.003, T, 350 + b, (0, 0, -1.0), rot=0.6)
    for sx in (-1, 1):     # corner straps, vertical, each side; nails
        for sy in (-1, 1):
            x, y = sx * (W / 2 + 0.004), sy * (Dp / 2 + 0.004)
            strap('Strap', (x, y + sy * 0.0, 0.02), (x, y, H - 0.02), 0.035, 0.004, None, tip=False)
            nails('Nails', [(x, y + sy * 0.0035, z) for z in np.linspace(0.05, H - 0.05, 4)], (0, sy, 0), None, r=0.006)
    meta = {'size': [W, Dp, H]}
elif VAR == 'Barrel':   # 0.6 x 0.9 m oak barrel: 20 bulging staves, 4 iron hoops, a bung, a lid
    R0, Rm, H, ns = 0.27, 0.31, 0.90, 20
    for k in range(ns):
        a0 = 2 * PI * k / ns; a1 = 2 * PI * (k + 1) / ns; am = (a0 + a1) / 2
        n = 60 if HIGH else 9; zz = np.linspace(0.0, H, n); bul = R0 + (Rm - R0) * np.sin(zz / H * PI) ** 0.9
        wid = 2 * bul * math.sin(PI / ns) - 0.003
        path = np.stack([bul * math.cos(am), bul * math.sin(am), zz], -1) + np.array([math.cos(am), math.sin(am), 0]) * j(0.003)
        prof_up = np.tile([math.cos(am), math.sin(am), 0.0], (n, 1))
        from propkit import board_prof
        V, Q, Tr, uv = sweep(path, prof_up, board_prof(1.0, 0.024, HIGH))
        M1 = len(board_prof(1.0, 0.024, HIGH)) + 1; G = V[:n * M1].reshape(n, M1, 3); ctr = path[:, None, :]
        wv = wid[:, None, None] * np.ones((1, M1, 1))
        off = G - ctr; side = np.array([-math.sin(am), math.cos(am), 0]); upv = np.array([math.cos(am), math.sin(am), 0])
        G = ctr + (off * side).sum(-1, keepdims=True) * wv * side + (off * upv).sum(-1, keepdims=True) * upv
        if HIGH:
            G = G + upv * (0.0007 * (fbm(zz[:, None] * 40 + k * 3, np.linspace(0, 1, M1)[None, :] * 6, 61 + k, 4) - 0.5))[..., None]
            G[..., 2] = np.where(zz[:, None] > H - 0.02, G[..., 2] - 0.004 * (fbm(np.full((n, M1), k * 1.0), np.linspace(0, 1, M1)[None, :] * 8, 62 + k, 3)), G[..., 2])   # chewed top ends
        V[:n * M1] = G.reshape(-1, 3); K = M1 - 1; V[n * M1:n * M1 + K] = G[0, :K]; V[n * M1 + K:n * M1 + 2 * K] = G[-1, :K]
        mesh('Stave_%02d' % k, V, [Q, Tr], 'Plank', uv=uv)
    for zh, ww in ((0.08, 0.05), (0.30, 0.045), (H - 0.30, 0.045), (H - 0.08, 0.05)):   # hoops
        rr = R0 + (Rm - R0) * math.sin(zh / H * PI) ** 0.9 + 0.013
        a = np.linspace(0, 2 * PI, 192 if HIGH else 28, endpoint=False)
        ring = np.stack([rr * np.cos(a), rr * np.sin(a), np.full_like(a, zh)], -1)
        V, Q, Tr, uv = sweep(ring, np.tile([0, 0, 1.0], (len(a), 1)), rrect(0.005, ww, 12 if HIGH else 4, 5.0), closed=True, caps=False)
        mesh('Hoop', V, [Q], 'Iron', uv=uv)
        if HIGH: nails('HoopRivet', [(rr * math.cos(q) + 0.002 * math.cos(q), rr * math.sin(q) + 0.002 * math.sin(q), zh) for q in np.linspace(0, 2 * PI, 10, endpoint=False)], (1, 0, 0), None, r=0.005)
    for z, nrm in ((0.03, (0, 0, -1.0)), (H - 0.03, (0, 0, 1.0))):     # heads (lids): 5 boards in a circle
        for b in range(5):
            y = -R0 + 0.02 + (2 * R0 - 0.04) * (b + 0.5) / 5; hw = math.sqrt(max(R0 ** 2 - y ** 2, 0.0004)) - 0.012
            plank('Head', (-hw, y, z), (hw, y, z), (2 * R0 - 0.04) / 5 - 0.003, 0.02, 370 + b, nrm, rot=0.3 if z < 0.1 else 0.0)
    Vs, Qs, Ts = superellipsoid(20 if HIGH else 6, 8 if HIGH else 3, 0.4)
    mesh('Bung', np.array([Rm + 0.004, 0, H * 0.55]) + Vs * np.array([0.012, 0.022, 0.022]), [Qs, Ts], 'Plank', uv=np.stack([Vs[:, 1], Vs[:, 2]], -1) * 0.02)
    meta = {'size': [2 * Rm, 2 * Rm, H]}
elif VAR == 'Sack':     # 0.55 m grain sack, slumped, tied at the neck with twine; a second small sack leaning on it
    def sack(name, c, h, r, seed, lean=0.0, open_=False):
        nu, nv = (96, 72) if HIGH else (28, 20)      # the low must follow the 5 cm slump within the bake cage
        th = np.linspace(0, 2 * PI, nu + 1); zz = np.linspace(0, 1, nv + 1)
        T_, Z_ = np.meshgrid(th, zz, indexing='ij')
        prof = np.sin(np.clip(Z_, 0, 1) * PI) ** 0.55
        prof = prof * (1 - 0.35 * sstep(0.82, 0.98, Z_))                                    # necked near the top
        prof = prof * (1 + 0.18 * (fbm(np.cos(T_) * 2 + seed, Z_ * 3, seed, 3) - 0.5) * 2)     # slump
        if HIGH: prof = prof * (1 + 0.010 * (fbm(T_ * 4, Z_ * 14, seed + 1, 4) - 0.5) * 2 + 0.005 * np.sin(T_ * 36) * sstep(0.1, 0.6, Z_) * (1 - Z_))  # cloth folds, within the 6 mm bake cage (deeper folds baked as black holes)
        squash = 1.0 - 0.25 * (1 - Z_)                                                        # fatter at the bottom
        X = c[0] + r * prof * np.cos(T_) * (1 + 0.3 * squash * 0) + Z_ * lean
        Y = c[1] + r * prof * np.sin(T_) * 1.15
        Zc = c[2] + h * Z_ * (1 - 0.08 * np.cos(T_) * Z_)
        V = np.stack([X, Y, Zc], -1).reshape(-1, 3); Q = grid_quads(nu + 1, nv + 1, False)
        f = Q[len(Q) // 2]; nrm = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]); cc = V[f].mean(0)
        if np.dot(nrm, [cc[0] - c[0], cc[1] - c[1], 0]) < 0: Q = Q[:, ::-1]
        mesh(name, V, [Q], 'Burlap', uv=np.stack([T_ * r, Z_ * h], -1).reshape(-1, 2))
        # the gathered neck + twine
        nk = np.array([c[0] + lean * 0.97, c[1], c[2] + h * 0.97]); a = np.linspace(0, 2 * PI * 2.5, 120 if HIGH else 20)
        tw = np.stack([nk[0] + r * 0.33 * np.cos(a), nk[1] + r * 0.33 * np.sin(a) * 1.15, nk[2] - 0.004 * a / (2 * PI)], -1)
        V, Q, Tr, uv = sweep(tw, np.tile([0, 0, 1.0], (len(a), 1)), circ(0.004, 8 if HIGH else 4)); mesh(name + '_Twine', V, [Q, Tr], 'Twine', uv=uv)
        if open_:   # spilled grain: a low mound
            Vs, Qs, Ts = superellipsoid(32 if HIGH else 10, 10 if HIGH else 4, 1.0)
            mesh(name + '_Grain', np.array([c[0] + r * 1.1, c[1] - r * 0.3, 0.0]) + Vs * np.array([r * 0.6, r * 0.45, 0.025]), [Qs, Ts], 'Grain', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.1)
    sack('Sack_A', np.array([0, 0, 0]), 0.58, 0.26, 401)
    sack('Sack_B', np.array([0.33, 0.12, 0]), 0.36, 0.19, 402, lean=0.08, open_=True)
    meta = {'size': [0.9, 0.6, 0.6]}
elif VAR == 'WeaponRack':   # 1.6 m wide, 1.7 m tall A-frame rack: two log uprights, a bark rail, pegs; weapons are placed separately
    W, H = 1.6, 1.7
    for k, x in enumerate((-W / 2, W / 2)):
        log('Upright_%d' % k, (x, 0.0, -0.1), (x + j(0.02), 0.02 + j(0.01), H), 0.055, 500 + k, bend=0.01)
        log('Foot_%d' % k, (x, -0.28, 0.05), (x, 0.28, 0.05), 0.045, 510 + k, bend=0.0)
    RY = -0.092     # the rails lie against the front of the uprights
    log('RailTop', (-W / 2 - 0.1, RY, H - 0.1), (W / 2 + 0.1, RY + 0.01, H - 0.11), 0.045, 520, bend=0.015)
    log('RailMid', (-W / 2 - 0.1, RY, H * 0.55), (W / 2 + 0.1, RY, H * 0.55 - 0.02), 0.04, 521, bend=0.015)
    plank('Shelf', (-W / 2 + 0.06, -0.09, 0.22), (W / 2 - 0.06, -0.09, 0.215), 0.18, 0.03, 530, (0, 0, 1.0), rot=0.5)
    for k in range(7):     # pegs on the top rail to hang weapons
        x = -W / 2 + 0.16 + k * (W - 0.32) / 6
        n = 10 if HIGH else 3; p = np.array([[x, RY - 0.03 - 0.12 * t, H - 0.1 + 0.03 * t] for t in np.linspace(0, 1, n)])
        V, Q, Tr, uv = sweep(p, np.tile([0, 0, 1.0], (n, 1)), circ(0.012, 12 if HIGH else 5)); mesh('Peg_%d' % k, V, [Q, Tr], 'WoodCut', uv=uv)
    for k, x in enumerate((-W / 2, W / 2)):   # lashings where the rails meet the uprights
        for zr, rr in ((H - 0.1, 0.045), (H * 0.55, 0.04)):
            kitlog.lash('Lash_%d_%d' % (k, int(zr * 10)), (x, 0.0, zr), 0.055, (x, RY, zr), rr, (0, 0, 1), (1, 0, 0), 540 + k + int(zr))
    meta = {'size': [W + 0.2, 0.56, H]}

json.dump({'grip': [0, 0, 0], **meta}, open(os.path.join(D, 'props%s_meta.json' % VAR.lower()), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Props%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')

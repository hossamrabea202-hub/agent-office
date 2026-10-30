# Camp kit (laptop2 2026-10-30): TorchPost, Campfire, HayBale, Well, HandCart. Knowledge-base standard: real scale,
# bevels >= 3 mm, nothing perfectly straight, wear in the materials (campmat).
#   blender -b --factory-startup -P build_camp.py      (env RES = low | high, VARIANT = TorchPost | Campfire | HayBale | Well | HandCart | MarketStall | Anvil)
# Units: metres, Z up, the prop stands on z 0 with its pivot at the base centre.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import kitlog
from kitlog import log
from propkit import plank, strap, nails, board_prof
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'HayBale')
rng = np.random.default_rng({'TorchPost': 151, 'Campfire': 152, 'HayBale': 153, 'Well': 154, 'HandCart': 155, 'MarketStall': 156, 'Anvil': 157}[VAR])
j = lambda a=0.004: rng.uniform(-a, a)

def rotm(yaw, pitch, roll=0.0):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]]); Rx = np.array([[1.0, 0, 0], [0, cp, -sp], [0, sp, cp]]); Ry = np.array([[cr, 0, sr], [0, 1.0, 0], [-sr, 0, cr]])
    return Rz @ Rx @ Ry

def rock(name, c, sz, seed, mname='Stone', soot=None, yaw=None, boxy=False):
    """a fieldstone: lumpy superellipsoid, sz = (x, y, z) half sizes; soot = per-vertex 0..1 or None; boxy = dressed-ish wall stone."""
    r = np.random.default_rng(seed)
    Vs, Qs, Ts = superellipsoid(32 if HIGH else 12, 16 if HIGH else 6, r.uniform(0.12, 0.22) if boxy else r.uniform(0.3, 0.5))
    V = Vs * (1 + (0.10 if boxy else 0.16) * (fbm(Vs[:, 0] * 1.5 + seed, Vs[:, 1] * 1.5 + Vs[:, 2] * 1.2, seed, 3) - 0.5) * 2 + (0.05 if boxy else 0.0) * (fbm(Vs[:, 0] * 4 + seed, Vs[:, 2] * 4, seed + 7, 3) - 0.5) * 2)[:, None]
    if HIGH: V = V * (1 + 0.025 * (fbm(Vs[:, 0] * 9 + Vs[:, 2] * 3, Vs[:, 1] * 9, seed + 1, 4) - 0.5) * 2 + 0.006 * (fbm(Vs[:, 0] * 40, Vs[:, 1] * 40 + Vs[:, 2] * 20, seed + 2, 3) - 0.5) * 2)[:, None]
    R = rotm(r.uniform(0, 2 * PI) if yaw is None else yaw, r.uniform(-0.25, 0.25), r.uniform(-0.2, 0.2))
    P = (V * np.asarray(sz)) @ R.T + np.asarray(c)
    uv = np.stack([np.arctan2(Vs[:, 1], Vs[:, 0]) / (2 * PI) * 2 * PI * max(sz[:2]), Vs[:, 2] * sz[2]], -1)
    attrs = {'soot': np.asarray(soot, float) if soot is not None else np.zeros(len(P))}
    return mesh(name, P, [Qs, Ts], mname, uv=uv, attrs=attrs), P

def tube(name, path, up, r, mname, n=None, caps=True, closed=False, attrs=None, rad=None):
    """round tube along path (per-ring radius via rad), returns the object."""
    n = n or (24 if HIGH else 8); path = np.asarray(path, float)
    V, Q, Tr, uv = sweep(path, np.tile(np.asarray(up, float), (len(path), 1)), circ(r, n), closed=closed, caps=caps)
    if rad is not None:
        M1 = n + 1; N = len(path) + (1 if closed else 0); G = V[:N * M1].reshape(N, M1, 3); ctr = np.vstack([path, path[:1]])[:N, None, :] if closed else path[:, None, :]
        rr = np.asarray(rad, float); rr = np.concatenate([rr, rr[:1]]) if closed else rr
        G = ctr + (G - ctr) * (rr[:, None, None] / r); V[:N * M1] = G.reshape(-1, 3)
        if caps and not closed:
            K = M1 - 1; V[N * M1:N * M1 + K] = G[0, :K]; V[N * M1 + K:N * M1 + 2 * K] = G[-1, :K]
    return mesh(name, V, [Q, Tr], mname, uv=uv, attrs=attrs)

def ring(name, c, r, prof, mname, axis=(0, 0, 1.0), n=None, tilt=0.0):
    """closed ring (hoop / tyre / bracket) of radius r around c, profile: rrect(along the axis, radial thickness)."""
    n = n or (160 if HIGH else 28); a = np.linspace(0, 2 * PI, n, endpoint=False)
    ax, u, v = kitlog.frame(np.zeros(3), np.asarray(axis, float))[2], None, None
    u = unit(np.cross(ax, [0, 0, 1.0] if abs(ax[2]) < 0.9 else [1.0, 0, 0])); v = np.cross(ax, u)
    P = np.asarray(c) + r * (np.cos(a)[:, None] * u + np.sin(a)[:, None] * v) + tilt * np.sin(a * 2)[:, None] * ax
    up = np.cos(a)[:, None] * u + np.sin(a)[:, None] * v
    V, Q, Tr, uv = sweep(P, up, prof, closed=True, caps=False)
    return mesh(name, V, [Q], mname, uv=uv)

def char_log(ob, p1, depth, strength):
    """set the log's 'tip' (char) weight from the distance to the p1 end: burnt black near the fire."""
    me = ob.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    d = np.linalg.norm(co - np.asarray(p1), axis=1)
    me.attributes['tip'].data.foreach_set('value', (np.clip(1 - d / depth, 0, 1) ** 1.3 * strength).astype(np.float32))

if VAR == 'TorchPost':   # 1.9 m log post, an iron ring bracket, a pitch-wrapped torch (the flame is a Niagara in UE)
    log('Post', (0, 0, -0.10), (0.012, -0.006, 1.75), 0.045, 601, bend=0.012, tip1=0.08)
    RC = np.array([0.15, 0.0, 1.50])
    ring('Bracket', RC, 0.055, rrect(0.034, 0.007, 10 if HIGH else 4, 5.0), 'Iron', n=96 if HIGH else 20)
    arm = np.array([[0.042, 0.0, 1.485], [0.07, 0.0, 1.492], [0.098, 0.0, 1.498]])
    V, Q, Tr, uv = sweep(arm, np.tile([0, 0, 1.0], (3, 1)), rrect(0.03, 0.009, 10 if HIGH else 4, 5.0)); mesh('BracketArm', V, [Q, Tr], 'Iron', uv=uv)
    plate = np.array([[0.042, 0.0, 1.42], [0.045, 0.0, 1.49], [0.042, 0.0, 1.56]])
    V, Q, Tr, uv = sweep(plate, np.tile([1.0, 0, 0], (3, 1)), rrect(0.04, 0.006, 10 if HIGH else 4, 5.0)); mesh('BracketPlate', V, [Q, Tr], 'Iron', uv=uv)
    nails('Nails', [(0.046, 0.0, 1.435), (0.046, 0.0, 1.545)], (1.0, 0, 0), None, r=0.006)
    # the torch: an ash shaft leaning in the ring, hemp tow wrap soaked in pitch on the top 0.25 m, glowing char on top
    d = unit([0.17, 0.03, 1.0]); B = RC - d * 0.28; n = 40 if HIGH else 10
    s = np.linspace(0, 1, n); L = 0.64; path = B + d * (s * L)[:, None]
    wrap = sstep(0.56, 0.63, s); rad = 0.021 * (1 + 0.9 * wrap * (1 + (0.25 * (fbm(s * 40, np.zeros_like(s), 603, 3) - 0.5) if HIGH else 0)))
    M1 = (24 if HIGH else 8) + 1; K = M1 - 1
    wa = np.concatenate([np.repeat(wrap, M1), np.full(K, wrap[0]), np.full(K, wrap[-1]), [wrap[0], wrap[-1]]])
    tube('Torch', path, [1.0, 0, 0], 0.021, 'Shaft', rad=rad, attrs={'wrap': wa})
    top = path[-1]
    for k in range(6 if HIGH else 4):
        a = 2 * PI * k / 5; r_ = 0.02 if k else 0.0; c = top + d * (0.012 + 0.008 * (k == 0)) + np.array([math.cos(a), math.sin(a), 0]) * r_
        Vs, Qs, Ts = superellipsoid(16 if HIGH else 8, 8 if HIGH else 4, 0.55); sz = 0.024 if k == 0 else 0.017
        mesh('Ember_%d' % k, c + Vs * np.array([sz, sz * 0.9, sz * 0.7]), [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 2]], -1) * sz, attrs={'glow': np.full(len(Vs), 0.9 if k == 0 else 0.6)})
    meta = {'size': [0.45, 0.3, 2.0], 'flame': [float(v) for v in top + d * 0.04]}

elif VAR == 'Campfire':   # 1.2 m stone ring, ash bed, glowing coals, five part-burnt logs (two spare beside it)
    ns = 14
    for k in range(ns):
        a = 2 * PI * k / ns + rng.uniform(-0.1, 0.1); r_ = 0.46 + j(0.03)
        sz = (rng.uniform(0.09, 0.13), rng.uniform(0.07, 0.10), rng.uniform(0.06, 0.09))
        ob, P = rock('Stone_%02d' % k, (r_ * math.cos(a), r_ * math.sin(a), sz[2] * 0.6), sz, 620 + k, yaw=a + rng.uniform(-0.3, 0.3))
        rad = np.linalg.norm(P[:, :2], axis=1); ob.data.attributes['soot'].data.foreach_set('value', (0.85 * sstep(0.50, 0.36, rad) * np.clip(P[:, 2] / 0.04, 0, 1)).astype(np.float32))
    Vs, Qs, Ts = superellipsoid(48 if HIGH else 14, 10 if HIGH else 4, 0.6)
    ash = Vs * np.array([0.38, 0.34, 0.035]); ash[:, 2] += 0.02 * (fbm(Vs[:, 0] * 3, Vs[:, 1] * 3, 630, 3) - 0.5) * 2 - 0.01
    mesh('Ash', ash, [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.35, attrs={'glow': np.zeros(len(Vs))})
    for k in range(22 if HIGH else 14):   # coals, hottest in the middle
        a = rng.uniform(0, 2 * PI); r_ = rng.uniform(0, 1) ** 0.6 * 0.19; c = [r_ * math.cos(a), r_ * math.sin(a), 0.035 + 0.03 * (1 - r_ / 0.2)]
        Vs, Qs, Ts = superellipsoid(16 if HIGH else 8, 8 if HIGH else 4, 0.55); sz = rng.uniform(0.022, 0.045)
        if HIGH: Vs = Vs * (1 + 0.12 * (fbm(Vs[:, 0] * 4 + k, Vs[:, 1] * 4, 640, 3) - 0.5))[:, None]
        mesh('Coal_%d' % k, c + Vs * np.array([sz, sz * 0.8, sz * 0.55]), [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 2]], -1) * sz, attrs={'glow': np.full(len(Vs), max(0.0, 1 - r_ / 0.22) * rng.uniform(0.6, 1.0))})
    for k in range(5):   # logs lying into the fire, outer ends up on the stones, inner ends charred
        a = 2 * PI * k / 5 + rng.uniform(-0.25, 0.25); r0 = 0.055 if k % 2 else 0.045; L = rng.uniform(0.55, 0.68)
        p1 = np.array([0.08 * math.cos(a + 2.5), 0.08 * math.sin(a + 2.5), 0.06 + 0.035 * k]); p0 = p1 + np.array([math.cos(a), math.sin(a), 0]) * L + [0, 0, 0.09 + 0.02 * (k % 2)]
        ob = log('Log_%d' % k, tuple(p0), tuple(p1), r0, 650 + k, bend=0.01, brk=0.04 if k % 2 else 0.0)
        char_log(ob, p1, rng.uniform(0.14, 0.22), 0.8)      # only the inner end is burnt; the rest stays bark
    for k in range(2):   # spare firewood beside the ring
        p0 = np.array([0.62 + 0.02 * k, -0.42 + 0.11 * k, 0.05]); p1 = p0 + [0.55, 0.12, 0.0]
        log('Spare_%d' % k, tuple(p0), tuple(p1), 0.05, 660 + k, bend=0.008)
    meta = {'size': [1.3, 1.2, 0.35], 'flame': [0, 0, 0.08]}

elif VAR == 'HayBale':   # 0.9 x 0.47 x 0.42 m rectangular bale of straw, two twine bands, slumped and sun-greyed on top
    SX, SY, SZ = 0.45, 0.235, 0.205
    nlon, nlat = (96, 48) if HIGH else (28, 14)
    Vs, Qs, Ts = superellipsoid(nlon, nlat, 0.32)
    lump = 0.05 * (fbm(Vs[:, 0] * 3 + Vs[:, 2], Vs[:, 1] * 3, 670, 3) - 0.5) * 2
    if HIGH: lump = lump + 0.012 * (fbm(Vs[:, 0] * 14, Vs[:, 1] * 14 + Vs[:, 2] * 7, 671, 4) - 0.5) * 2 + 0.004 * (fbm(Vs[:, 0] * 60, Vs[:, 1] * 60, 672, 2) - 0.5) * 2
    V = Vs * (1 + lump)[:, None] * np.array([SX, SY, SZ])
    V[:, 2] = V[:, 2] * (1 - 0.12 * np.clip(V[:, 2] / SZ, 0, 1) * (np.abs(V[:, 0]) / SX) ** 2) + SZ * 0.98      # sags at the ends, sits on z 0
    V[:, 2] = np.maximum(V[:, 2], 0.0)
    th = np.arctan2(Vs[:, 1], Vs[:, 0])
    uv = np.stack([Vs[:, 0] * SX * 2 + th * 0.0, V[:, 2] + Vs[:, 1] * SY], -1)
    mesh('Bale', V, [Qs, Ts], 'Hay', uv=uv)
    for x in (-0.16, 0.16):   # twine bands around the bale
        n = 120 if HIGH else 28; a = np.linspace(0, 2 * PI, n, endpoint=False)
        sg = lambda v, m: np.sign(v) * np.abs(v) ** m
        P = np.stack([np.full(n, x) + 0.004 * np.sin(a * 3), sg(np.cos(a), 0.32) * SY * 1.015, sg(np.sin(a), 0.32) * SZ * 1.015 + SZ * 0.98], -1)
        up = unit(np.stack([np.zeros(n), P[:, 1], P[:, 2] - SZ * 0.98], -1))
        V, Q, Tr, uv = sweep(P, up, rrect(0.013, 0.004, 8 if HIGH else 4, 4.0), closed=True, caps=False); mesh('Twine', V, [Q], 'Twine', uv=uv)
    meta = {'size': [0.92, 0.48, 0.42]}

elif VAR == 'Well':   # 1.3 m stone well head with mortar core, two log posts, a windlass with a crank, rope and bucket, a planked roof
    RI, H = 0.62, 0.86
    ring('Core', (0, 0, H / 2), 0.56, rrect(H, 0.12, 12 if HIGH else 4, 8.0), 'Mortar', n=96 if HIGH else 24)
    for course in range(4):
        n = 13; z = 0.11 + course * 0.215
        for k in range(n):
            a = 2 * PI * (k + 0.5 * (course % 2)) / n + rng.uniform(-0.04, 0.04)
            sz = (rng.uniform(0.10, 0.13), rng.uniform(0.12, 0.15), rng.uniform(0.085, 0.105))
            rr = RI + rng.uniform(-0.02, 0.025)
            rock('Stone_%d_%02d' % (course, k), (rr * math.cos(a), rr * math.sin(a), z + j(0.012)), sz, 700 + course * 20 + k, yaw=a, boxy=True)
    for k, x in enumerate((-0.74, 0.74)):
        log('Post_%d' % k, (x, 0.0, -0.1), (x + j(0.01), j(0.01), 2.02), 0.06, 720 + k, bend=0.01)
    AZ = 1.58
    tube('Windlass', np.array([[-0.78, 0, AZ], [0, 0, AZ + 0.004], [0.78, 0, AZ]]), [0, 0, 1.0], 0.075, 'WoodCut', n=48 if HIGH else 12)
    for x in (-0.76, 0.76): ring('AxleBand_%d' % int(x > 0), (x, 0, AZ), 0.078, rrect(0.03, 0.004, 8 if HIGH else 4, 5.0), 'Iron', axis=(1.0, 0, 0), n=64 if HIGH else 16)
    crank = np.array([[0.80, 0, AZ], [0.92, 0, AZ], [0.93, 0, AZ + 0.02], [0.93, 0, AZ + 0.22], [0.95, 0, AZ + 0.24], [1.10, 0, AZ + 0.24]])
    tube('Crank', crank, [0, 1.0, 0], 0.013, 'Iron', n=16 if HIGH else 6)
    tube('CrankGrip', crank[-2:] + [[0.02, 0, 0], [-0.01, 0, 0]], [0, 1.0, 0], 0.022, 'WoodCut', n=20 if HIGH else 8)
    # rope: wound round the windlass, then down to the bucket
    tt = np.linspace(0, 6 * 2 * PI, 240 if HIGH else 60)
    helix = np.stack([-0.02 + 0.014 * tt / (2 * PI), 0.083 * np.cos(tt), AZ + 0.083 * np.sin(tt)], -1)
    hang = np.array([[helix[-1, 0], 0.083, AZ - 0.02], [helix[-1, 0] + 0.01, 0.06, 1.3], [helix[-1, 0] + 0.02, 0.0, 1.10]])
    kitlog.rope('Rope', np.vstack([helix, hang]), 0.007, 730)
    # bucket hanging from the rope, 12 staves, two hoops, an iron bail
    BC = np.array([hang[-1, 0], 0.0, 0.80]); nst = 12
    for k in range(nst):
        a = 2 * PI * (k + 0.5) / nst; r0, r1 = 0.105, 0.125
        plank('Stave_%02d' % k, (BC[0] + r0 * math.cos(a), r0 * math.sin(a), BC[2]), (BC[0] + r1 * math.cos(a), r1 * math.sin(a), BC[2] + 0.27), 2 * r1 * math.sin(PI / nst) - 0.004, 0.012, 740 + k, (math.cos(a), math.sin(a), 0), rot=0.2)
    for z, r in ((BC[2] + 0.05, 0.111), (BC[2] + 0.22, 0.123)): ring('BucketHoop', (BC[0], 0, z), r + 0.006, rrect(0.022, 0.004, 8 if HIGH else 4, 5.0), 'Iron', n=96 if HIGH else 20)
    for b in range(4):
        y = -0.09 + 0.045 * b + 0.022
        plank('BucketBottom', (BC[0] - 0.09, y, BC[2] + 0.015), (BC[0] + 0.09, y, BC[2] + 0.015), 0.042, 0.015, 750 + b, (0, 0, 1.0), rot=0.5)
    a = np.linspace(0, PI, 40 if HIGH else 10); bail = np.stack([BC[0] + 0.0 * a, 0.13 * np.cos(a), BC[2] + 0.26 + 0.14 * np.sin(a)], -1)
    tube('Bail', bail, [1.0, 0, 0], 0.006, 'Iron', n=12 if HIGH else 6)
    # roof: ridge log, three rafters a side, planks
    log('Ridge', (-0.98, 0.0, 2.33), (0.98, 0.0, 2.34), 0.04, 760, bend=0.005)
    for sy in (-1, 1):
        for k, x in enumerate((-0.74, 0.0, 0.74)):
            log('Rafter_%d_%d' % (int(sy > 0), k), (x, 0.0, 2.30), (x + j(0.01), sy * 0.80, 1.93), 0.032, 770 + k + (10 if sy > 0 else 0), bend=0.004)
        for b in range(7):
            t = (b + 0.5) / 7; y = sy * (0.03 + 0.76 * t); z = 2.36 - 0.37 * t
            plank('Roof_%d_%d' % (int(sy > 0), b), (-1.0 + j(0.02), y, z), (1.0 + j(0.02), y + j(0.004), z + j(0.004)), 0.115, 0.022, 780 + b + (10 if sy > 0 else 0), (0, sy * 0.43, 0.9), rot=0.45 if b == 6 else 0.1)
    meta = {'size': [2.1, 1.7, 2.4], 'water_z': 0.25}

elif VAR == 'HandCart':   # two-wheel hand cart, 1.8 m bed, spoked wheels with iron tyres, shafts forward (+X), resting on its front legs
    BZ, AX, WY, WR = 0.60, -0.25, 0.56, 0.50
    for b in range(7):   # bed boards
        y = -0.42 + 0.84 * (b + 0.5) / 7
        plank('Bed_%d' % b, (-0.92 + j(0.01), y + j(0.002), BZ), (0.92 + j(0.01), y + j(0.003), BZ + j(0.003)), 0.115, 0.025, 800 + b, (0, 0, 1.0), rot=0.1)
    for k, x in enumerate((-0.85, 0.0, 0.85)):   # cross bearers under the bed
        plank('Bearer_%d' % k, (x, -0.47, BZ - 0.04), (x, 0.47, BZ - 0.04), 0.07, 0.05, 810 + k, (0, 0, -1.0), rot=0.3)
    for sy in (-1, 1):   # side rails on uprights, a front board
        for k, x in enumerate((-0.86, 0.0, 0.86)):
            V, Q, Tr, uv = sweep(np.array([[x, sy * 0.45, BZ - 0.06], [x + j(0.01), sy * 0.452, BZ + 0.44]]), np.tile([0, sy * 1.0, 0], (2, 1)), rrect(0.05, 0.035, 10 if HIGH else 4, 6.0))
            mesh('Upright_%d_%d' % (int(sy > 0), k), V, [Q, Tr], 'WoodCut', uv=uv)
            strap('UprightStrap_%d_%d' % (int(sy > 0), k), (x, sy * 0.472, BZ - 0.05), (x, sy * 0.472, BZ + 0.10), 0.035, 0.004, None, tip=False)
        for r in range(2):
            z = BZ + 0.20 + 0.20 * r
            plank('Rail_%d_%d' % (int(sy > 0), r), (-0.95 + j(0.01), sy * 0.475, z), (0.95 + j(0.01), sy * 0.475 + j(0.003), z + j(0.004)), 0.11, 0.022, 820 + r + (10 if sy > 0 else 0), (0, sy * 1.0, 0), rot=0.15)
    for r in range(2):
        z = BZ + 0.20 + 0.20 * r
        plank('Front_%d' % r, (0.94, -0.44, z), (0.94, 0.44, z), 0.11, 0.022, 830 + r, (1.0, 0, 0), rot=0.15)
    # axle, bolsters, wheels
    tube('Axle', np.array([[AX, -WY - 0.12, WR], [AX, 0, WR + 0.003], [AX, WY + 0.12, WR]]), [0, 0, 1.0], 0.035, 'WoodCut', n=24 if HIGH else 8)
    for sy in (-1, 1):
        plank('Bolster_%d' % int(sy > 0), (AX - 0.07, sy * 0.3, WR + 0.04), (AX + 0.07, sy * 0.3, WR + 0.04), 0.14, 0.05, 840 + int(sy > 0), (0, 0, 1.0), rot=0.2)
        wc = np.array([AX, sy * WY, WR])
        ring('Rim_%d' % int(sy > 0), wc, WR - 0.025, rrect(0.055, 0.045, 12 if HIGH else 4, 6.0), 'WoodCut', axis=(0, 1.0, 0), n=144 if HIGH else 36, tilt=0.002)
        ring('Tyre_%d' % int(sy > 0), wc, WR + 0.004, rrect(0.05, 0.012, 10 if HIGH else 4, 5.0), 'Iron', axis=(0, 1.0, 0), n=144 if HIGH else 36)
        tube('Hub_%d' % int(sy > 0), np.array([wc + [0, -sy * 0.09, 0], wc + [0, sy * 0.10, 0]]), [0, 0, 1.0], 0.07, 'WoodCut', n=32 if HIGH else 10)
        for z_ in (-0.075, 0.08): ring('HubBand_%d_%d' % (int(sy > 0), int(z_ > 0)), wc + [0, sy * z_, 0], 0.072, rrect(0.02, 0.004, 8 if HIGH else 4, 5.0), 'Iron', axis=(0, 1.0, 0), n=64 if HIGH else 16)
        for k in range(12):
            a = 2 * PI * k / 12 + rng.uniform(-0.02, 0.02); dvec = np.array([math.cos(a), 0, math.sin(a)])
            tube('Spoke_%d_%02d' % (int(sy > 0), k), np.array([wc + dvec * 0.06, wc + dvec * (WR - 0.04)]), [0, 1.0, 0], 0.014, 'WoodCut', n=12 if HIGH else 6, rad=[0.017, 0.012])
    # shafts forward and the two front legs
    for sy in (-1, 1):
        log('Shaft_%d' % int(sy > 0), (0.3, sy * 0.40, BZ - 0.07), (2.15, sy * 0.33, BZ - 0.02), 0.032, 850 + int(sy > 0), bend=0.01)
        V, Q, Tr, uv = sweep(np.array([[0.90, sy * 0.40, BZ - 0.06], [0.92, sy * 0.41, 0.0]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.045, 0.035, 10 if HIGH else 4, 6.0))
        mesh('Leg_%d' % int(sy > 0), V, [Q, Tr], 'WoodCut', uv=uv)
    meta = {'size': [3.1, 1.3, 1.05]}

elif VAR == 'MarketStall':   # 2.4 x 1.6 m market stall (Vesna's shop): log posts, plank counter + shelf, sagging striped canvas awning, a hook bar
    W, Dp = 2.4, 1.6
    for k, (x, y, h) in enumerate(((-W / 2, Dp / 2, 2.35), (W / 2, Dp / 2, 2.35), (-W / 2, -Dp / 2, 2.05), (W / 2, -Dp / 2, 2.05))):
        log('Post_%d' % k, (x, y, -0.1), (x + j(0.015), y + j(0.015), h), 0.05, 900 + k, bend=0.008)
    for k, y in enumerate((Dp / 2 - 0.12, -Dp / 2 + 0.3)):   # counter bearers, counter planks (front half), low shelf
        plank('Bearer_%d' % k, (-W / 2 + 0.03, y, 0.86), (W / 2 - 0.03, y, 0.86), 0.09, 0.05, 910 + k, (0, 0, 1.0), rot=0.2)
    for b in range(7):
        y = Dp / 2 - 0.02 - (Dp / 2 + 0.1) * (b + 0.5) / 7
        plank('Counter_%d' % b, (-W / 2 - 0.06 + j(0.01), y, 0.93 + j(0.003)), (W / 2 + 0.06 + j(0.01), y + j(0.003), 0.93 + j(0.003)), (Dp / 2 + 0.1) / 7 - 0.006, 0.03, 920 + b, (0, 0, 1.0), rot=0.1)
    for b in range(4):
        y = -Dp / 2 + 0.1 + 0.14 * b
        plank('Shelf_%d' % b, (-W / 2 + 0.08, y, 0.35), (W / 2 - 0.08, y, 0.35), 0.13, 0.025, 930 + b, (0, 0, 1.0), rot=0.4)
    for sx in (-1, 1):   # side rails
        for z in (0.33, 0.88): plank('SideRail_%d_%d' % (int(sx > 0), int(z > 0.5)), (sx * W / 2, Dp / 2 - 0.06, z), (sx * W / 2, -Dp / 2 + 0.06, z), 0.08, 0.03, 940 + int(sx > 0), (sx * 1.0, 0, 0), rot=0.2)
    log('AwningFront', (-W / 2 - 0.15, Dp / 2 + 0.12, 2.33), (W / 2 + 0.15, Dp / 2 + 0.12, 2.34), 0.035, 950, bend=0.01)
    log('AwningBack', (-W / 2 - 0.15, -Dp / 2 - 0.05, 2.08), (W / 2 + 0.15, -Dp / 2 - 0.05, 2.09), 0.035, 951, bend=0.01)
    log('AwningMid', (0.0, Dp / 2 + 0.12, 2.33), (0.0, -Dp / 2 - 0.05, 2.08), 0.03, 952, bend=0.0)
    for k, x in enumerate((-W / 2 - 0.15, W / 2 + 0.15)):   # awning side rails and the lashings at the posts
        log('AwningSide_%d' % k, (x, Dp / 2 + 0.12, 2.33), (x, -Dp / 2 - 0.05, 2.08), 0.03, 953 + k, bend=0.0)
        kitlog.lash('AwLashF_%d' % k, (x * (W / 2) / (W / 2 + 0.15), Dp / 2, 2.33), 0.05, (x, Dp / 2 + 0.12, 2.33), 0.035, (0, 0, 1), (1, 0, 0), 960 + k)
    # the canvas: a sagging sheet over the rails (front edge hangs as a valance), stripes in UV u
    nu, nv = (120, 72) if HIGH else (24, 14)
    U, V_ = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing='ij')
    X = -W / 2 - 0.25 + (W + 0.5) * U; Y = Dp / 2 + 0.22 - (Dp + 0.3) * V_
    Z = 2.36 - 0.26 * V_ - 0.06 * np.sin(U * PI) * np.sin(V_ * PI) - 0.02 * np.sin(U * 2 * PI) ** 2 * np.sin(V_ * PI)
    if HIGH: Z = Z + 0.004 * (fbm(U * 12, V_ * 8, 970, 4) - 0.5) * 2 + 0.0012 * (fbm(U * 60, V_ * 40, 971, 3) - 0.5) * 2
    Z = Z + 0.012 * np.abs(np.sin(U * 9 * PI)) ** 2 * (1 - V_) * 0.5     # creases from the front rail
    Vc = np.stack([X, Y, Z], -1).reshape(-1, 3); Qc = grid_quads(nu, nv, False)
    mesh('Canvas', Vc, [Qc], 'Canvas', uv=np.stack([X, Y], -1).reshape(-1, 2))
    nv2 = 8 if HIGH else 3; U2, V2 = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv2), indexing='ij')   # valance hanging from the front edge
    Xv = -W / 2 - 0.25 + (W + 0.5) * U2; Yv = Dp / 2 + 0.22 + 0.02 * V2; Zv = 2.36 - 0.22 * V2 * (1 - 0.35 * np.abs(np.sin(U2 * 11 * PI)) ** 1.5)
    if HIGH: Zv = Zv + 0.003 * (fbm(U2 * 50, V2 * 10, 972, 3) - 0.5)
    Vv = np.stack([Xv, Yv, Zv], -1).reshape(-1, 3); Qv = grid_quads(nu, nv2, False)
    mesh('Valance', Vv, [Qv], 'Canvas', uv=np.stack([Xv, Zv - 2.0], -1).reshape(-1, 2))
    # hook bar under the front of the awning with 4 iron hooks (hang the shields / wares)
    tube('HookBar', np.array([[-W / 2 + 0.1, Dp / 2 - 0.05, 2.05], [0, Dp / 2 - 0.05, 2.045], [W / 2 - 0.1, Dp / 2 - 0.05, 2.05]]), [0, 0, 1.0], 0.016, 'Iron', n=16 if HIGH else 6)
    for k in range(4):
        x = -W / 2 + 0.4 + k * (W - 0.8) / 3; a = np.linspace(0, PI, 16 if HIGH else 5)
        hook = np.vstack([[[x, Dp / 2 - 0.05, 2.06]], [[x, Dp / 2 - 0.05, 1.97]], np.stack([np.full_like(a, x), Dp / 2 - 0.05 + 0.035 * np.sin(a), 1.97 - 0.035 * (1 - np.cos(a))], -1)[1:]])
        tube('Hook_%d' % k, hook, [1.0, 0, 0], 0.006, 'Iron', n=10 if HIGH else 5)
    meta = {'size': [W + 0.5, Dp + 0.5, 2.4], 'counter_z': 0.945, 'hooks': [[-W / 2 + 0.4 + k * (W - 0.8) / 3, Dp / 2 - 0.05, 1.94] for k in range(4)]}

elif VAR == 'Anvil':   # 0.62 m iron anvil on an oak stump: base, waist, face block, horn, heel; a hammer on the face
    ns_ = 40 if HIGH else 10; zs = np.linspace(-0.03, 0.45, ns_)
    stump = np.stack([0.01 * zs / 0.45, -0.005 * zs / 0.45, zs], -1)
    srad = 0.19 * (1 + 0.03 * np.sin(zs * 40) * 0 + (0.02 * (fbm(zs * 8, np.zeros_like(zs), 982, 3) - 0.5) if HIGH else 0))
    tube('Stump', stump, [1.0, 0, 0], 0.19, 'WoodCut', n=48 if HIGH else 14, rad=srad)
    def block(name, c, sz, e=0.2, seed=0, mname='Iron'):
        Vs, Qs, Ts = superellipsoid(32 if HIGH else 8, 16 if HIGH else 4, e)
        P = Vs * np.asarray(sz) + np.asarray(c)
        if HIGH: P = P + 0.0006 * (fbm(Vs[:, 0] * 30 + seed, Vs[:, 1] * 30 + Vs[:, 2] * 15, 981 + seed, 3) - 0.5)[:, None]
        mesh(name, P, [Qs, Ts], mname, uv=np.stack([Vs[:, 0] * sz[0] + Vs[:, 1] * sz[1] * 0.3, Vs[:, 2] * sz[2]], -1))
    Z0 = 0.45
    block('Base', (0.0, 0, Z0 + 0.03), (0.15, 0.11, 0.03), 0.2, 1)
    block('Waist', (0.0, 0, Z0 + 0.10), (0.085, 0.06, 0.05), 0.3, 2)
    block('Body', (0.0, 0, Z0 + 0.195), (0.14, 0.075, 0.05), 0.15, 3)
    block('Face', (0.02, 0, Z0 + 0.255), (0.13, 0.06, 0.012), 0.12, 4)
    block('Heel', (-0.17, 0, Z0 + 0.24), (0.045, 0.055, 0.025), 0.25, 5)
    n = 24 if HIGH else 7; s = np.linspace(0, 1, n)
    horn = np.stack([0.14 + 0.22 * s, np.zeros(n), Z0 + 0.235 + 0.02 * s ** 2], -1)
    tube('Horn', horn, [0, 0, 1.0], 0.05, 'Iron', n=24 if HIGH else 8, rad=0.05 * (1 - 0.86 * s) ** 0.8 + 0.004)
    tube('HammerHandle', np.array([[0.06, 0.08, Z0 + 0.29], [0.1, 0.03, Z0 + 0.31], [0.14, -0.14, Z0 + 0.335]]), [0, 0, 1.0], 0.013, 'WoodCut', n=16 if HIGH else 6, rad=[0.016, 0.013, 0.015])
    block('HammerHead', (0.065, 0.085, Z0 + 0.3), (0.045, 0.02, 0.022), 0.15, 6)
    meta = {'size': [0.62, 0.38, 0.8], 'work_point': [0.0, 0.0, Z0 + 0.27]}

json.dump({'grip': [0, 0, 0], **meta}, open(os.path.join(D, 'camp%s_meta.json' % VAR.lower()), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Camp%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')

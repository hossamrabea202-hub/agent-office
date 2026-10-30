# Camp kit (laptop2 2026-10-30): TorchPost, Campfire, HayBale, Well, HandCart. Knowledge-base standard: real scale,
# bevels >= 3 mm, nothing perfectly straight, wear in the materials (campmat).
#   blender -b --factory-startup -P build_camp.py      (env RES = low | high, VARIANT = TorchPost | Campfire | HayBale | Well | HandCart | MarketStall | Anvil | Tent | SiegeLadder)
# Units: metres, Z up, the prop stands on z 0 with its pivot at the base centre.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import kitlog
from kitlog import log
from propkit import plank, strap, nails, board_prof, group
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, orient, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'HayBale')
rng = np.random.default_rng({'TorchPost': 151, 'Campfire': 152, 'HayBale': 153, 'Well': 154, 'HandCart': 155, 'MarketStall': 156, 'Anvil': 157, 'Tent': 158, 'SiegeLadder': 159, 'CannonCart': 160, 'Workbench': 161, 'Grindstone': 162, 'Forge': 163, 'Banner': 164, 'GoldPile': 165, 'Firewood': 166, 'Lantern': 167, 'Signpost': 168, 'TargetDummy': 169, 'Burrow': 170}[VAR])
j = lambda a=0.004: rng.uniform(-a, a)

def rotm(yaw, pitch, roll=0.0):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]]); Rx = np.array([[1.0, 0, 0], [0, cp, -sp], [0, sp, cp]]); Ry = np.array([[cr, 0, sr], [0, 1.0, 0], [-sr, 0, cr]])
    return Rz @ Rx @ Ry

def rock(name, c, sz, seed, mname='Stone', soot=None, yaw=None, boxy=False, dressed=False):
    """a fieldstone: lumpy superellipsoid, sz = (x, y, z) half sizes; soot = per-vertex 0..1 or None; boxy = dressed-ish wall stone."""
    r = np.random.default_rng(seed)
    e = r.uniform(0.06, 0.1) if dressed else (r.uniform(0.12, 0.22) if boxy else r.uniform(0.3, 0.5))
    Vs, Qs, Ts = superellipsoid(32 if HIGH else 12, 16 if HIGH else 6, e)
    lump = 0.03 if dressed else (0.10 if boxy else 0.16)
    V = Vs * (1 + lump * (fbm(Vs[:, 0] * 1.5 + seed, Vs[:, 1] * 1.5 + Vs[:, 2] * 1.2, seed, 3) - 0.5) * 2 + (0.05 if boxy and not dressed else 0.0) * (fbm(Vs[:, 0] * 4 + seed, Vs[:, 2] * 4, seed + 7, 3) - 0.5) * 2)[:, None]
    if HIGH: V = V * (1 + 0.025 * (fbm(Vs[:, 0] * 9 + Vs[:, 2] * 3, Vs[:, 1] * 9, seed + 1, 4) - 0.5) * 2 + 0.006 * (fbm(Vs[:, 0] * 40, Vs[:, 1] * 40 + Vs[:, 2] * 20, seed + 2, 3) - 0.5) * 2)[:, None]
    R = rotm(r.uniform(0, 2 * PI) if yaw is None else yaw, 0.0 if dressed else r.uniform(-0.25, 0.25), 0.0 if dressed else r.uniform(-0.2, 0.2))
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
    for k in range(4):   # logs criss-crossed over the coals, each resting on the one below (13 cm steps > log diameter, lowest clears the coals), inner ends charred
        a = 2 * PI * k / 4 + 0.6 + rng.uniform(-0.15, 0.15); r0 = 0.05 if k % 2 else 0.042; L = rng.uniform(0.55, 0.68)
        # inner ends clear the ash and coals by > 12 mm (the bake ray distance), or the logs bake the coals' black
        # each log lies one diameter above the previous so they stack and never intersect (intersecting logs baked black: rays hit the neighbour's inside)
        p1 = np.array([0.10 * math.cos(a + 2.5), 0.10 * math.sin(a + 2.5), 0.19 + 0.13 * k]); p0 = p1 + np.array([math.cos(a), math.sin(a), 0]) * L + [0, 0, -0.04 - 0.02 * k]
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

elif VAR == 'Tent':   # 2.4 x 1.8 m soldiers' ridge tent: ridge pole on two end poles, canvas draped over, front flap tied open, guy ropes to pegs
    L, Wd, Ht = 2.4, 1.8, 1.55
    log('PoleF', (L / 2 - 0.1, 0.0, -0.05), (L / 2 - 0.1 + j(0.01), j(0.01), Ht), 0.03, 1000, bend=0.004)
    log('PoleB', (-L / 2 + 0.1, 0.0, -0.05), (-L / 2 + 0.1 + j(0.01), j(0.01), Ht), 0.03, 1001, bend=0.004)
    log('Ridge', (-L / 2 - 0.15, 0.0, Ht + 0.02), (L / 2 + 0.15, 0.0, Ht + 0.025), 0.028, 1002, bend=0.006)
    nu, nv = (160, 48) if HIGH else (26, 10)
    for sy in (-1, 1):   # two canvas slopes from the ridge to the ground, sagging between the poles, hem lifting at the pegs
        U, V_ = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing='ij')
        X = -L / 2 - 0.1 + (L + 0.2) * U; Y = sy * (0.015 + (Wd / 2) * V_); Z = Ht + 0.02 - (Ht + 0.02) * V_ ** 1.05
        sag = 0.05 * np.sin(np.clip((U - 0.08) / 0.84, 0, 1) * PI) * np.sin(V_ * PI) ** 0.8
        Z = Z - sag; Y = Y + sy * 0.03 * np.sin(V_ * PI) * np.sin(np.clip((U - 0.08) / 0.84, 0, 1) * PI)
        Z = Z + 0.012 * np.abs(np.sin(U * 5 * PI)) ** 2 * V_ * (1 - V_) * 2        # creases from the guy ropes
        if HIGH: Z = Z + 0.004 * (fbm(U * 14, V_ * 8 + sy, 1010, 4) - 0.5) * 2 + 0.001 * (fbm(U * 70, V_ * 40, 1011, 3) - 0.5) * 2
        Z = np.maximum(Z, 0.003)
        Vc = np.stack([X, Y, Z], -1).reshape(-1, 3); Qc = grid_quads(nu, nv, False)
        mesh('Canvas_%d' % int(sy > 0), Vc, [orient(Vc, Qc, np.array([0, sy * 1.0, 0.5]))], 'CanvasPlain', uv=np.stack([X, V_ * Wd * 0.9], -1).reshape(-1, 2))
    # back wall: a triangle of canvas; front: two flaps, one tied back to the pole
    nb = 24 if HIGH else 6
    Ub, Vb = np.meshgrid(np.linspace(-1, 1, nb), np.linspace(0, 1, nb), indexing='ij')
    Xb = -L / 2 - 0.06 + 0.0 * Ub + 0.01 * (1 - Vb); Yb = Ub * (Wd / 2 - 0.03) * (1 - Vb); Zb = (Ht - 0.03) * Vb + 0.003   # 4 cm inside the roof edge, 3 cm off the roof sheets: no shared edges with the slopes
    if HIGH: Xb = Xb + 0.004 * (fbm(Ub * 6, Vb * 6, 1012, 3) - 0.5) * 2
    Vb_ = np.stack([Xb, Yb, Zb], -1).reshape(-1, 3); mesh('BackWall', Vb_, [orient(Vb_, grid_quads(nb, nb, False), np.array([-1.0, 0, 0]))], 'CanvasEnd', uv=np.stack([Yb, Zb], -1).reshape(-1, 2))
    Uf, Vf = np.meshgrid(np.linspace(0, 1, nb), np.linspace(0, 1, nb), indexing='ij')
    Xf = L / 2 + 0.06 - 0.02 * Vf; Yf = -(Wd / 2 - 0.03) * (1 - Vf) * Uf; Zf = (Ht - 0.03) * Vf + 0.003        # closed left flap
    if HIGH: Xf = Xf + 0.004 * (fbm(Uf * 6, Vf * 6, 1013, 3) - 0.5) * 2
    Vf_ = np.stack([Xf, Yf, Zf], -1).reshape(-1, 3); mesh('FlapL', Vf_, [orient(Vf_, grid_quads(nb, nb, False), np.array([1.0, 0, 0]))], 'CanvasEnd', uv=np.stack([Yf, Zf], -1).reshape(-1, 2))
    Xr = L / 2 + 0.06 + 0.25 * Uf * (1 - Vf); Yr = (Wd / 2 - 0.03) * (1 - Vf) * (0.35 + 0.65 * Uf) * (1 - 0.5 * Uf * (1 - Vf)); Zr = (Ht - 0.03) * Vf + 0.1 * Uf * (1 - Vf) + 0.003   # right flap rolled open toward the pole
    Vr_ = np.stack([Xr, Yr, Zr], -1).reshape(-1, 3); mesh('FlapR', Vr_, [orient(Vr_, grid_quads(nb, nb, False), np.array([1.0, 0.5, 0]))], 'CanvasEnd', uv=np.stack([Yr + Xr, Zr], -1).reshape(-1, 2))
    for sy in (-1, 1):   # guy ropes from the hem to wooden pegs, and the ridge ropes to the end pegs
        for k in range(3):
            x = -L / 2 + 0.3 + k * (L - 0.6) / 2
            peg = np.array([x + j(0.03), sy * (Wd / 2 + 0.35), 0.0])
            kitlog.rope('Guy_%d_%d' % (int(sy > 0), k), [[x, sy * (Wd / 2 - 0.02), 0.12], peg + [0, 0, 0.06]], 0.005, 1020 + k)
            V, Q, Tr, uv = sweep(np.array([peg + [0, 0, -0.08], peg + [0, 0, 0.12]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.025, 0.02, 8 if HIGH else 4, 5.0)); mesh('Peg_%d_%d' % (int(sy > 0), k), V, [Q, Tr], 'WoodCut', uv=uv)
    for sx in (-1, 1):
        peg = np.array([sx * (L / 2 + 0.75), 0.0, 0.0])
        kitlog.rope('RidgeGuy_%d' % int(sx > 0), [[sx * (L / 2 + 0.15), 0.0, Ht + 0.02], peg + [0, 0, 0.07]], 0.006, 1030 + int(sx > 0))
        V, Q, Tr, uv = sweep(np.array([peg + [0, 0, -0.08], peg + [0, 0, 0.14]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.03, 0.022, 8 if HIGH else 4, 5.0)); mesh('RidgePeg_%d' % int(sx > 0), V, [Q, Tr], 'WoodCut', uv=uv)
    meta = {'size': [L + 1.7, Wd + 0.8, Ht + 0.05], 'door': [L / 2 + 0.1, 0.0, 0.0]}

elif VAR == 'SiegeLadder':   # 5 m assault ladder: two bark rails, 14 rungs, lashed at every third rung, iron hooks at the top
    LL, Wr = 5.0, 0.42
    for k, y in enumerate((-Wr / 2, Wr / 2)):
        log('Rail_%d' % k, (0.0, y, 0.0), (LL + j(0.03), y + j(0.02), 0.0 + j(0.01)), 0.038, 1100 + k, bend=0.015)
    for r in range(14):
        x = 0.25 + r * (LL - 0.5) / 13
        xr = x + j(0.006)   # rungs lie across the top of the rails
        tube('Rung_%02d' % r, np.array([[xr, -Wr / 2 - 0.05, 0.046], [xr, 0.0, 0.05], [xr, Wr / 2 + 0.05, 0.046]]), [0, 0, 1.0], 0.02, 'WoodCut', n=16 if HIGH else 7, rad=[0.019, 0.022, 0.019])
        if r % 3 == 0:
            for sy in (-1, 1): kitlog.lash('Lash_%02d_%d' % (r, int(sy > 0)), (xr, sy * Wr / 2, 0.0), 0.038, (xr, sy * Wr / 2, 0.046), 0.02, (1, 0, 0), (0, 1, 0), 1120 + r + int(sy > 0))
    for sy in (-1, 1):   # top hooks: an iron strap along the rail, bent over into a hook
        a = np.linspace(0, PI * 0.9, 16 if HIGH else 5)
        hook = np.vstack([[[LL - 0.5, sy * Wr / 2, 0.04]], [[LL, sy * Wr / 2, 0.04]], np.stack([LL + 0.06 * np.sin(a), np.full_like(a, sy * Wr / 2), 0.04 - 0.06 * (1 - np.cos(a))], -1)[1:]])
        V, Q, Tr, uv = sweep(hook, np.tile([0, 1.0, 0], (len(hook), 1)), rrect(0.03, 0.007, 8 if HIGH else 4, 5.0)); mesh('Hook_%d' % int(sy > 0), V, [Q, Tr], 'Iron', uv=uv)
        nails('HookNails_%d' % int(sy > 0), [(LL - 0.4, sy * Wr / 2, 0.044), (LL - 0.15, sy * Wr / 2, 0.044)], (0, 0, 1.0), None, r=0.006)
    meta = {'size': [LL + 0.1, Wr + 0.12, 0.09], 'note': 'lies flat along +X with the foot at the origin; lean it 65-70 deg against the wall, hooks over the crenel'}

elif VAR == 'CannonCart':   # #50: two-wheel cannon carriage/limber: the cannon sits in a cradle on the bed; wheels are separate pieces
    # pieces (vertex groups): Body (bed, cradle, axle, shafts), WheelL, WheelR (pivot on the axle: rotate about Y by distance / radius)
    BZ, AX, WY, WR = 0.55, 0.0, 0.62, 0.55
    for b in range(5):
        y = -0.36 + 0.72 * (b + 0.5) / 5
        plank('Bed_%d' % b, (-1.0 + j(0.01), y, BZ), (1.1 + j(0.01), y + j(0.003), BZ + j(0.003)), 0.135, 0.03, 1200 + b, (0, 0, 1.0), rot=0.1, gname='Body')
    for k, x in enumerate((-0.9, 0.0, 0.95)):
        plank('Bearer_%d' % k, (x, -0.42, BZ - 0.045), (x, 0.42, BZ - 0.045), 0.08, 0.06, 1210 + k, (0, 0, -1.0), rot=0.2, gname='Body')
    for k, x in enumerate((-0.45, 0.45)):   # the cradle: two V blocks that hold the barrel
        for sy in (-1, 1):
            V, Q, Tr, uv = sweep(np.array([[x, sy * 0.12, BZ + 0.015], [x + j(0.005), sy * 0.26, BZ + 0.24]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.12, 0.07, 10 if HIGH else 4, 6.0))
            group(mesh('Cradle_%d_%d' % (k, int(sy > 0)), V, [Q, Tr], 'WoodCut', uv=uv), 'Body')
            strap('CradleStrap_%d_%d' % (k, int(sy > 0)), (x, sy * 0.13, BZ + 0.03), (x, sy * 0.25, BZ + 0.23), 0.04, 0.004, 'Body', tip=False)
    group(tube('Axle', np.array([[AX, -WY - 0.14, WR], [AX, 0, WR + 0.003], [AX, WY + 0.14, WR]]), [0, 0, 1.0], 0.04, 'WoodCut', n=24 if HIGH else 8), 'Body')
    for sy in (-1, 1):
        plank('Bolster_%d' % int(sy > 0), (AX - 0.08, sy * 0.32, WR + 0.045), (AX + 0.08, sy * 0.32, WR + 0.045), 0.14, 0.05, 1220 + int(sy > 0), (0, 0, 1.0), rot=0.2, gname='Body')
        group(ring('AxleCap_%d' % int(sy > 0), (AX, sy * (WY + 0.13), WR), 0.045, rrect(0.02, 0.006, 8 if HIGH else 4, 5.0), 'Iron', axis=(0, 1.0, 0), n=48 if HIGH else 12), 'Body')
    for sy in (-1, 1):   # wheels: 12 spokes, felloe rim, iron tyre, hub with bands; pivot = (AX, sy*WY, WR)
        g = 'WheelL' if sy < 0 else 'WheelR'; wc = np.array([AX, sy * WY, WR])
        group(ring('Rim_%s' % g, wc, WR - 0.03, rrect(0.06, 0.05, 12 if HIGH else 4, 6.0), 'WoodCut', axis=(0, 1.0, 0), n=144 if HIGH else 36, tilt=0.002), g)
        group(ring('Tyre_%s' % g, wc, WR + 0.004, rrect(0.055, 0.012, 10 if HIGH else 4, 5.0), 'Iron', axis=(0, 1.0, 0), n=144 if HIGH else 36), g)
        group(tube('Hub_%s' % g, np.array([wc + [0, -sy * 0.1, 0], wc + [0, sy * 0.11, 0]]), [0, 0, 1.0], 0.075, 'WoodCut', n=32 if HIGH else 10), g)
        for z_ in (-0.085, 0.09): group(ring('HubBand_%s_%d' % (g, int(z_ > 0)), wc + [0, sy * z_, 0], 0.077, rrect(0.022, 0.004, 8 if HIGH else 4, 5.0), 'Iron', axis=(0, 1.0, 0), n=64 if HIGH else 16), g)
        for k in range(12):
            a = 2 * PI * k / 12 + rng.uniform(-0.02, 0.02); dvec = np.array([math.cos(a), 0, math.sin(a)])
            group(tube('Spoke_%s_%02d' % (g, k), np.array([wc + dvec * 0.065, wc + dvec * (WR - 0.045)]), [0, 1.0, 0], 0.015, 'WoodCut', n=12 if HIGH else 6, rad=[0.018, 0.013]), g)
    for sy in (-1, 1):   # shafts forward (+X) with a pull bar for the pulling mechanic; a push bar at the back
        group(log('Shaft_%d' % int(sy > 0), (0.6, sy * 0.38, BZ - 0.06), (2.3, sy * 0.33, BZ + 0.02), 0.034, 1230 + int(sy > 0), bend=0.01), 'Body')
    group(tube('PullBar', np.array([[2.2, -0.36, BZ + 0.02], [2.2, 0.36, BZ + 0.02]]), [0, 0, 1.0], 0.022, 'WoodCut', n=16 if HIGH else 6), 'Body')
    group(tube('PushBar', np.array([[-1.05, -0.45, BZ + 0.35], [-1.05, 0.45, BZ + 0.35]]), [0, 0, 1.0], 0.022, 'WoodCut', n=16 if HIGH else 6), 'Body')
    for sy in (-1, 1):
        V, Q, Tr, uv = sweep(np.array([[-1.0, sy * 0.4, BZ], [-1.05, sy * 0.44, BZ + 0.36]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.045, 0.035, 10 if HIGH else 4, 6.0)); group(mesh('PushPost_%d' % int(sy > 0), V, [Q, Tr], 'WoodCut', uv=uv), 'Body')
    meta = {'size': [3.4, 1.5, 1.1], 'pieces': {'Body': [0, 0, 0], 'WheelL': [AX, -WY, WR], 'WheelR': [AX, WY, WR]}, 'wheel_radius_m': WR + 0.004,
            'cradle_socket': [0.0, 0.0, BZ + 0.2], 'pull_handle': [2.2, 0.0, BZ + 0.02], 'push_handle': [-1.05, 0.0, BZ + 0.35],
            'note': 'rotate WheelL/WheelR about their local Y by travelled_distance / wheel_radius_m (radians); the cannon barrel mesh sits at cradle_socket'}

elif VAR == 'Workbench':   # #50 workshop: heavy oak bench with a leg vice, tools on top (hammer, tongs, file), a toolbox underneath
    W, Dp, H = 1.8, 0.75, 0.9
    for b in range(4):
        y = -Dp / 2 + Dp * (b + 0.5) / 4
        plank('Top_%d' % b, (-W / 2 + j(0.01), y, H - 0.04), (W / 2 + j(0.01), y + j(0.003), H - 0.04 + j(0.002)), Dp / 4 - 0.006, 0.08, 1300 + b, (0, 0, 1.0), rot=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            V, Q, Tr, uv = sweep(np.array([[sx * (W / 2 - 0.12), sy * (Dp / 2 - 0.1), 0.0], [sx * (W / 2 - 0.12) + j(0.01), sy * (Dp / 2 - 0.1), H - 0.08]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.1, 0.1, 10 if HIGH else 4, 6.0))
            mesh('Leg_%d_%d' % (int(sx > 0), int(sy > 0)), V, [Q, Tr], 'WoodCut', uv=uv)
        plank('Stretcher_%d' % int(sx > 0), (sx * (W / 2 - 0.12), -Dp / 2 + 0.1, 0.25), (sx * (W / 2 - 0.12), Dp / 2 - 0.1, 0.25), 0.09, 0.05, 1310 + int(sx > 0), (0, 0, 1.0), rot=0.3)
    plank('Shelf', (-W / 2 + 0.2, 0.0, 0.27), (W / 2 - 0.2, 0.0, 0.27), 0.5, 0.03, 1320, (0, 0, 1.0), rot=0.4)
    # leg vice on the front left: wooden jaw, iron screw with a tommy bar
    V, Q, Tr, uv = sweep(np.array([[-W / 2 + 0.15, -Dp / 2 - 0.08, 0.05], [-W / 2 + 0.15, -Dp / 2 - 0.08, H + 0.02]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.11, 0.06, 10 if HIGH else 4, 6.0)); mesh('ViceJaw', V, [Q, Tr], 'WoodCut', uv=uv)
    tube('ViceScrew', np.array([[-W / 2 + 0.15, -Dp / 2 - 0.3, H - 0.15], [-W / 2 + 0.15, -Dp / 2 + 0.05, H - 0.15]]), [0, 0, 1.0], 0.018, 'Iron', n=16 if HIGH else 6)
    tube('ViceBar', np.array([[-W / 2 + 0.15, -Dp / 2 - 0.27, H - 0.32], [-W / 2 + 0.15, -Dp / 2 - 0.27, H + 0.02]]), [1.0, 0, 0], 0.009, 'Iron', n=10 if HIGH else 5)
    # tools on top: hammer, tongs, a file
    tube('HammerHandle', np.array([[0.2, -0.1, H + 0.015], [0.5, -0.02, H + 0.015]]), [0, 0, 1.0], 0.013, 'WoodCut', n=12 if HIGH else 6)
    Vs, Qs, Ts = superellipsoid(16 if HIGH else 6, 8 if HIGH else 4, 0.15); mesh('HammerHead', np.array([0.52, -0.015, H + 0.025]) + Vs * np.array([0.03, 0.055, 0.025]), [Qs, Ts], 'Iron', uv=np.stack([Vs[:, 1], Vs[:, 2]], -1) * 0.05)
    for k, (a, L) in enumerate(((0.0, 0.42), (0.12, 0.42))):
        tube('Tong_%d' % k, np.array([[-0.5, 0.15, H + 0.008], [-0.5 + L * math.cos(a), 0.15 + L * math.sin(a), H + 0.008]]), [0, 0, 1.0], 0.007, 'Iron', n=8 if HIGH else 5)
    V, Q, Tr, uv = sweep(np.array([[0.1, 0.25, H + 0.006], [0.45, 0.28, H + 0.006]]), np.tile([0, 0, 1.0], (2, 1)), rrect(0.025, 0.006, 8 if HIGH else 4, 5.0)); mesh('File', V, [Q, Tr], 'Iron', uv=uv)
    # toolbox on the shelf: an open plank box with an iron bail
    bx, by, bz = -0.2, 0.0, 0.285
    plank('BoxBottom', (bx - 0.3, by, bz + 0.01), (bx + 0.3, by, bz + 0.01), 0.26, 0.015, 1330, (0, 0, 1.0), rot=0.1)
    for sy in (-1, 1): plank('BoxSide_%d' % int(sy > 0), (bx - 0.3, by + sy * 0.13, bz + 0.09), (bx + 0.3, by + sy * 0.13, bz + 0.09), 0.16, 0.015, 1331 + int(sy > 0), (0, sy * 1.0, 0), rot=0.1)
    for sx in (-1, 1): plank('BoxEnd_%d' % int(sx > 0), (bx + sx * 0.3, by - 0.12, bz + 0.09), (bx + sx * 0.3, by + 0.12, bz + 0.09), 0.16, 0.015, 1333 + int(sx > 0), (sx * 1.0, 0, 0), rot=0.1)
    tube('BoxHandle', np.array([[bx - 0.28, by, bz + 0.17], [bx - 0.28, by, bz + 0.27], [bx + 0.28, by, bz + 0.27], [bx + 0.28, by, bz + 0.17]]), [0, 1.0, 0], 0.008, 'Iron', n=8 if HIGH else 5)
    meta = {'size': [W + 0.4, Dp + 0.3, H + 0.1], 'work_point': [0.0, 0.0, H + 0.1]}

elif VAR == 'Grindstone':   # #50 workshop: 0.6 m sandstone wheel in an oak frame over a water trough, with a crank
    tube('Trough', np.array([[-0.26, 0.0, 0.15], [0.26, 0.0, 0.15]]), [0, 0, 1.0], 0.12, 'WoodCut', n=24 if HIGH else 8)   # top at 0.27 < the wheel's bottom 0.28: nothing intersects (intersections bake black)
    for sx in (-1, 1):
        for sy in (-1, 1):
            V, Q, Tr, uv = sweep(np.array([[sx * 0.3, sy * 0.22, 0.0], [sx * 0.3 + j(0.005), sy * 0.2, 0.55]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.07, 0.07, 8 if HIGH else 4, 6.0)); mesh('Post_%d_%d' % (int(sx > 0), int(sy > 0)), V, [Q, Tr], 'WoodCut', uv=uv)
    plank('Rail_0', (-0.36, 0.2, 0.52), (0.36, 0.2, 0.52), 0.08, 0.05, 1400, (0, 0, 1.0), rot=0.2); plank('Rail_1', (-0.36, -0.2, 0.52), (0.36, -0.2, 0.52), 0.08, 0.05, 1401, (0, 0, 1.0), rot=0.2)
    # the stone: a 0.6 m disc 9 cm thick (a tube along Y), slightly worn out of round on the high
    ob = tube('Stone', np.array([[0.0, -0.045, 0.58], [0.0, 0.045, 0.58]]), [0, 0, 1.0], 0.3, 'Stone', n=96 if HIGH else 28, rad=[0.3, 0.3])
    ob.data.attributes.new('soot', 'FLOAT', 'POINT').data.foreach_set('value', np.zeros(len(ob.data.vertices), np.float32))
    tube('Axle', np.array([[0.0, -0.3, 0.58], [0.0, 0.3, 0.58]]), [0, 0, 1.0], 0.022, 'Iron', n=16 if HIGH else 6)
    crank = np.array([[0.0, 0.3, 0.58], [0.0, 0.36, 0.58], [0.14, 0.37, 0.58], [0.14, 0.52, 0.58]])
    tube('Crank', crank, [0, 0, 1.0], 0.012, 'Iron', n=12 if HIGH else 6); tube('CrankGrip', crank[-2:] + [[0, 0.02, 0], [0, -0.01, 0]], [0, 0, 1.0], 0.02, 'WoodCut', n=16 if HIGH else 6)
    meta = {'size': [0.8, 0.7, 0.9], 'work_point': [-0.3, 0.0, 0.62]}

elif VAR == 'Forge':   # #186: blacksmith forge: fieldstone hearth with a chimney, coal bed with embers, leather bellows, quench barrel, tool rack
    # hearth: a 1.6 x 1.2 m stone block 0.95 m high, open on the front (+X), chimney hood of stone rising to 2.6 m at the back
    def wallstones(x0, x1, y0, y1, z0, z1, seed, soot=0.0):
        r = np.random.default_rng(seed); nz = max(int((z1 - z0) / 0.18), 1)
        for c in range(nz):
            z = z0 + (c + 0.5) * (z1 - z0) / nz; L = math.hypot(x1 - x0, y1 - y0); n = max(int(L / 0.26), 1)
            for k in range(n):
                tt = (k + 0.5 * (c % 2) + 0.5) / n
                if tt > 1: continue
                x, y = x0 + (x1 - x0) * tt, y0 + (y1 - y0) * tt
                sz = (r.uniform(0.12, 0.145), r.uniform(0.1, 0.12), r.uniform(0.082, 0.09))
                ob, P = rock('HStone_%d_%d_%d' % (seed, c, k), (x + r.uniform(-0.006, 0.006), y + r.uniform(-0.006, 0.006), z), sz, seed * 100 + c * 20 + k, yaw=math.atan2(y1 - y0, x1 - x0), boxy=True, dressed=True)
                ob.data.attributes['soot'].data.foreach_set('value', np.full(len(P), soot, np.float32))
    HX, HY, HZ = 0.8, 0.6, 0.95
    wallstones(-HX, -HX, -HY, HY, 0.0, HZ, 1)                       # back wall (-X)
    wallstones(-HX, HX, -HY, -HY, 0.0, HZ, 2); wallstones(-HX, HX, HY, HY, 0.0, HZ, 3)   # sides
    wallstones(HX, HX, -HY, HY, 0.0, HZ * 0.45, 4)                  # low front lip
    ring('HearthSlab', (0, 0, HZ + 0.03), 0.01, rrect(0.0, 0.0, 4, 4.0), 'Mortar', n=4) if False else None
    Vs, Qs, Ts = superellipsoid(24 if HIGH else 8, 8 if HIGH else 4, 0.12)
    mesh('HearthTop', np.array([0, 0, HZ + 0.03]) + Vs * np.array([HX + 0.04, HY + 0.04, 0.035]), [Qs, Ts], 'Mortar', uv=np.stack([Vs[:, 0] * HX, Vs[:, 1] * HY], -1))
    # chimney hood: a tapering stone box from the back half of the hearth up to 2.6 m, sooted inside
    for c in range(9):
        z0 = HZ + 0.07 + c * 0.18; f = 1 - 0.35 * c / 9
        wallstones(-HX, -HX, -HY * f, HY * f, z0, z0 + 0.18, 10 + c, soot=0.5)
        wallstones(-HX, -HX + 0.55 * f, -HY * f, -HY * f, z0, z0 + 0.18, 20 + c, soot=0.5); wallstones(-HX, -HX + 0.55 * f, HY * f, HY * f, z0, z0 + 0.18, 30 + c, soot=0.5)
        if c >= 3: wallstones(-HX + 0.55 * f, -HX + 0.55 * f, -HY * f, HY * f, z0, z0 + 0.18, 40 + c, soot=0.7)   # the hood's front closes above head height
    # coal bed and embers on the hearth top (glow attribute), a tuyere pipe from the bellows
    for k in range(30 if HIGH else 18):
        a = rng.uniform(0, 2 * PI); r_ = rng.uniform(0, 1) ** 0.6 * 0.3; c = [-0.15 + r_ * math.cos(a), r_ * math.sin(a) * 0.8, HZ + 0.07 + 0.03 * (1 - r_ / 0.3)]
        Vs, Qs, Ts = superellipsoid(16 if HIGH else 8, 8 if HIGH else 4, 0.55); sz = rng.uniform(0.02, 0.04)
        if HIGH: Vs = Vs * (1 + 0.12 * (fbm(Vs[:, 0] * 4 + k, Vs[:, 1] * 4, 1640, 3) - 0.5))[:, None]
        mesh('Coal_%d' % k, c + Vs * np.array([sz, sz * 0.8, sz * 0.55]), [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 2]], -1) * sz, attrs={'glow': np.full(len(Vs), max(0.0, 1 - r_ / 0.32) * rng.uniform(0.6, 1.0))})
    tube('Tuyere', np.array([[-0.15, HY + 0.3, HZ + 0.08], [-0.15, 0.05, HZ + 0.08]]), [0, 0, 1.0], 0.025, 'Iron', n=12 if HIGH else 6)
    # bellows beside the hearth (+Y): two oak boards hinged at the nozzle, leather pleats between, a lever handle
    BY = HY + 0.55; BZ = 0.75
    plank('BellowsTop', (-0.45, BY, BZ + 0.12), (0.25, BY, BZ + 0.22), 0.42, 0.03, 1650, (0, 0, 1.0), rot=0.0)
    plank('BellowsBot', (-0.45, BY, BZ - 0.02), (0.25, BY, BZ - 0.02), 0.42, 0.03, 1651, (0, 0, 1.0), rot=0.0)
    nu, nv = (48, 16) if HIGH else (14, 6)
    U_, V_ = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing='ij')
    for sy in (-1, 1):
        X = -0.45 + 0.7 * U_; Zc = BZ - 0.005 + (0.12 + 0.1 * U_) * V_; Yc = BY + sy * (0.21 - 0.035 * np.abs(np.sin(V_ * 4 * PI)) ** 0.7 * (1 - U_ * 0.3))
        if HIGH: Yc = Yc + sy * 0.003 * (fbm(U_ * 20, V_ * 10, 1652, 3) - 0.5)
        mesh('Pleat_%d' % int(sy > 0), np.stack([X, Yc, Zc], -1).reshape(-1, 3), [grid_quads(nu, nv, False)], 'Leather', uv=np.stack([X, Zc], -1).reshape(-1, 2))
    tube('BellowsNozzle', np.array([[-0.45, BY, BZ + 0.05], [-0.15, BY, BZ + 0.06], [-0.15, HY + 0.3, HZ + 0.08]]), [0, 0, 1.0], 0.025, 'Iron', n=12 if HIGH else 6)
    tube('BellowsHandle', np.array([[0.2, BY, BZ + 0.2], [0.65, BY, BZ + 0.62]]), [0, 0, 1.0], 0.016, 'WoodCut', n=10 if HIGH else 6)
    for k, (x, y) in enumerate(((-0.4, BY - 0.15), (-0.4, BY + 0.15), (0.2, BY - 0.15), (0.2, BY + 0.15))):
        V, Q, Tr, uv = sweep(np.array([[x, y, 0.0], [x, y, BZ - 0.03]]), np.tile([1.0, 0, 0], (2, 1)), rrect(0.06, 0.06, 8 if HIGH else 4, 6.0)); mesh('BellowsLeg_%d' % k, V, [Q, Tr], 'WoodCut', uv=uv)
    # quench barrel (-Y side): staves + 3 hoops + water disc; tool rack on the back wall: a plank with 5 pegs
    QY = -HY - 0.5
    for k in range(16):
        a = 2 * PI * k / 16; r0, r1 = 0.21, 0.24
        plank('QStave_%02d' % k, (0.2 + r0 * math.cos(a), QY + r0 * math.sin(a), 0.0), (0.2 + r1 * math.cos(a), QY + r1 * math.sin(a), 0.62), 2 * r1 * math.sin(PI / 16) - 0.004, 0.018, 1660 + k, (math.cos(a), math.sin(a), 0), rot=0.3)
    for z, r in ((0.08, 0.215), (0.33, 0.228), (0.56, 0.238)): ring('QHoop', (0.2, QY, z), r + 0.006, rrect(0.03, 0.004, 8 if HIGH else 4, 5.0), 'Iron', n=96 if HIGH else 20)
    Vs, Qs, Ts = superellipsoid(32 if HIGH else 12, 6 if HIGH else 3, 0.9)
    mesh('QWater', np.array([0.2, QY, 0.55]) + Vs * np.array([0.22, 0.22, 0.004]), [Qs, Ts], 'Iron', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.2)
    plank('ToolRack', (-HX - 0.02, -0.5, 1.75), (-HX - 0.02, 0.5, 1.75), 0.14, 0.03, 1670, (-1.0, 0, 0), rot=0.1)
    for k in range(5):
        y = -0.4 + 0.2 * k
        tube('RackPeg_%d' % k, np.array([[-HX - 0.03, y, 1.75], [-HX - 0.18, y, 1.78]]), [0, 0, 1.0], 0.012, 'WoodCut', n=10 if HIGH else 5)
    for k, (y, L) in enumerate(((-0.4, 0.38), (0.0, 0.3), (0.4, 0.42))):   # hanging tongs / hammer / poker
        tube('Tool_%d' % k, np.array([[-HX - 0.17, y, 1.76], [-HX - 0.17, y + 0.02, 1.76 - L]]), [1.0, 0, 0], 0.008, 'Iron', n=8 if HIGH else 5)
    meta = {'size': [2.4, 3.0, 2.7], 'fire': [-0.15, 0.0, HZ + 0.12], 'smoke': [-HX + 0.25, 0.0, 2.65], 'work_point': [0.5, 0.0, HZ + 0.1],
            'note': 'fire + ember Niagara at fire, chimney smoke at smoke; pair with an orange point light 1800 K 900 cd at fire'}

elif VAR == 'Banner':   # #169 watchtower banner: 3 m pole with a finial, a crossbar, a hanging wool banner (swallow tail) bearing the castle crest
    log('Pole', (0, 0, -0.05), (0.005, 0.0, 3.0), 0.03, 1700, bend=0.004, tip1=0.12)
    tube('Crossbar', np.array([[-0.42, 0.0, 2.75], [0.42, 0.0, 2.76]]), [0, 0, 1.0], 0.016, 'WoodCut', n=12 if HIGH else 6)
    a_ = np.linspace(0, 2 * PI * 4, 48 if HIGH else 16)   # a few diagonal rope turns round the bar/pole crossing (lash() needs offset centres)
    kitlog.rope('BarLash', np.stack([0.036 * np.cos(a_), 0.036 * np.sin(a_), 2.72 + 0.06 * a_ / (2 * PI * 4)], -1), 0.005, 1701)
    # the cloth: hangs from the crossbar (-Y side, 2 cm off), 0.7 m wide, 1.6 m long, sways and sags; swallow-tail cut 0.35 m deep
    nu, nv = (36, 90) if HIGH else (10, 24)
    U_, V_ = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing='ij')
    W_, Lc = 0.7, 1.6
    X = (U_ - 0.5) * W_; Z = 2.75 - 0.02 - V_ * Lc
    Y = -0.035 - 0.06 * np.sin(V_ * PI * 1.3) * (0.6 + 0.4 * np.cos(U_ * PI * 2)) - 0.03 * V_ ** 2 * np.sin(U_ * PI)      # gentle wind belly
    if HIGH: Y = Y + 0.004 * (fbm(U_ * 10, V_ * 25, 1702, 4) - 0.5) * 2 + 0.0012 * (fbm(U_ * 50, V_ * 90, 1703, 2) - 0.5) * 2   # wool folds
    Y = Y + 0.012 * np.sin(U_ * 7 * PI) ** 2 * V_                                                                  # vertical ripples growing downward
    tail = np.clip((np.abs(U_ - 0.5) * 2 - 0.0) * 0.35, 0, 0.35)                                                  # swallow tail: centre notch 0.35 m
    keep = V_ * Lc <= Lc - (0.35 - tail)
    Vc = np.stack([X, Y, Z], -1).reshape(-1, 3); Q = grid_quads(nu, nv, False)
    kf = keep.reshape(-1); Q = Q[np.all(kf[Q], axis=1)]
    uv = np.stack([U_ * W_, (1 - V_) * Lc], -1).reshape(-1, 2)        # u 0..0.7 across, v 0 at the tail .. 1.6 at the bar (the crest reads upright)
    mesh('Cloth', Vc, [Q], 'Banner', uv=uv)
    for x in (-0.3, -0.1, 0.1, 0.3):   # ties to the bar
        kitlog.rope('Tie_%d' % int((x + 0.3) * 10), [[x, -0.035, 2.73], [x, 0.0, 2.76], [x, 0.035, 2.73]], 0.004, 1710 + int((x + 0.3) * 10))
    meta = {'size': [0.9, 0.2, 3.1], 'cloth_uv': [W_, Lc], 'note': 'use SimpleGrassWind (WindIntensity 0.25) on the cloth material in UE for sway'}

elif VAR == 'GoldPile':   # #187 gold drop: a spilled leather purse with a mound of coins around it, a few coins scattered; 0.35 m
    Vs, Qs, Ts = superellipsoid(48 if HIGH else 14, 12 if HIGH else 5, 0.7)
    mound = Vs * (1 + 0.1 * (fbm(Vs[:, 0] * 3, Vs[:, 1] * 3 + 1, 1800, 3) - 0.5) * 2)[:, None] * np.array([0.16, 0.13, 0.045]); mound[:, 2] = np.maximum(mound[:, 2], 0) + 0.002
    mesh('Mound', mound, [Qs, Ts], 'Gold', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.15, attrs={'coin': np.ones(len(Vs))})
    n = 0
    for k in range(90 if HIGH else 40):   # coins: flat discs tilted at random, denser on the mound
        a = rng.uniform(0, 2 * PI); r_ = rng.uniform(0, 1) ** 0.5 * 0.17; c = np.array([r_ * math.cos(a), r_ * math.sin(a) * 0.85, 0.0])
        h = 0.045 * max(0.0, 1 - (r_ / 0.15) ** 2) * (1 + 0.1 * (fbm(c[0] * 3, c[1] * 3 + 1, 1800, 3) - 0.5) * 2)
        c[2] = h + 0.004 + rng.uniform(0, 0.006); R = rotm(rng.uniform(0, 2 * PI), rng.uniform(-0.6, 0.6) * (0.3 + h / 0.045), rng.uniform(-0.4, 0.4))
        Vc, Qc, Tc = superellipsoid(20 if HIGH else 10, 4 if HIGH else 2, 0.25)
        P = (Vc * np.array([0.014, 0.014, 0.0012])) @ R.T + c
        mesh('Coin_%02d' % k, P, [Qc, Tc], 'Gold', uv=np.stack([Vc[:, 0], Vc[:, 1]], -1) * 0.014, attrs={'coin': np.ones(len(P))})
    # the purse: a soft leather bag on its side, mouth open toward +X, drawstring
    nu, nv = (48, 24) if HIGH else (14, 8)
    T_, Z_ = np.meshgrid(np.linspace(0, 2 * PI, nu + 1), np.linspace(0, 1, nv + 1), indexing='ij')
    prof = np.sin(Z_ * PI) ** 0.5 * (1 - 0.3 * sstep(0.85, 1.0, Z_)); prof = prof * (1 + 0.06 * (fbm(np.cos(T_) * 2, Z_ * 3, 1801, 3) - 0.5) * 2)
    if HIGH: prof = prof * (1 + 0.012 * np.sin(T_ * 14) * sstep(0.7, 1.0, Z_))
    PX_ = -0.09 - 0.14 * Z_ * -1 - 0.04; PY = 0.05 + 0.07 * prof * np.cos(T_); PZ = 0.0 + 0.055 * prof * (0.5 + 0.5 * np.sin(T_)) + 0.001
    Vp = np.stack([-0.17 + 0.16 * Z_, PY, PZ], -1).reshape(-1, 3)
    mesh('Purse', Vp, [grid_quads(nu + 1, nv + 1, False)], 'Leather', uv=np.stack([T_ * 0.06, Z_ * 0.16], -1).reshape(-1, 2))
    kitlog.rope('Drawstring', [[-0.03, 0.05 + 0.07 * math.cos(a_), 0.001 + 0.055 * (0.5 + 0.5 * math.sin(a_)) * 0.7] for a_ in np.linspace(0, 2 * PI, 24)], 0.003, 1802, closed=True)
    meta = {'size': [0.4, 0.3, 0.07], 'pickup_radius_m': 0.9, 'note': 'gold drop (#187): sparkle Niagara at origin, bob + slow yaw in BP, despawn 60 s'}

elif VAR == 'Firewood':   # owner list #8: a 1.4 m stack of split logs between two stakes, a few loose on top
    for k, x in enumerate((-0.72, 0.72)):
        for y in (-0.2, 0.2): log('Stake_%d_%d' % (k, int(y > 0)), (x, y, -0.05), (x + j(0.01), y, 1.0), 0.03, 1900 + k, bend=0.004, tip1=0.06)
    rows = 6
    for r_ in range(rows):
        z = 0.08 + r_ * 0.15; n = 7 - (r_ // 3)
        for i_ in range(n):
            x = -0.62 + 1.24 * (i_ + 0.5 + 0.5 * (r_ % 2)) / n
            if x > 0.66: continue
            split = rng.random() < 0.7
            ob = log('Log_%d_%02d' % (r_, i_), (x + j(0.01), -0.26 + j(0.01), z), (x + j(0.01), 0.26 + j(0.01), z + j(0.005)), 0.065 + j(0.012), 1910 + r_ * 10 + i_, bend=0.003, split=split)
    for i_ in range(3):   # loose ones on top
        x = rng.uniform(-0.4, 0.4); a = rng.uniform(-0.4, 0.4)
        log('Loose_%d' % i_, (x - 0.25 * math.sin(a), -0.25 * math.cos(a), 0.08 + rows * 0.15 + 0.02), (x + 0.25 * math.sin(a), 0.25 * math.cos(a), 0.08 + rows * 0.15 + 0.03), 0.06, 1950 + i_, bend=0.003, split=True)
    meta = {'size': [1.5, 0.6, 1.1]}

elif VAR == 'Lantern':   # #10: hanging iron lantern: ring handle, 4 posts, horn panes (glass slot kept unbaked), a candle, a hook bracket
    base = 0.0
    group_ = None
    ring('BaseRing', (0, 0, base + 0.01), 0.075, rrect(0.02, 0.006, 8 if HIGH else 4, 5.0), 'Iron', n=64 if HIGH else 16)
    Vs, Qs, Ts = superellipsoid(24 if HIGH else 8, 6 if HIGH else 3, 0.2); mesh('BasePlate', np.array([0, 0, base + 0.006]) + Vs * np.array([0.07, 0.07, 0.006]), [Qs, Ts], 'Iron', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.07)
    for k in range(4):
        a = 2 * PI * k / 4 + PI / 4; x, y = 0.06 * math.cos(a), 0.06 * math.sin(a)
        tube('Post_%d' % k, np.array([[x, y, base + 0.01], [x * 0.9, y * 0.9, base + 0.2]]), [0, 0, 1.0], 0.005, 'Iron', n=8 if HIGH else 4)
    ring('TopRing', (0, 0, base + 0.2), 0.065, rrect(0.016, 0.005, 8 if HIGH else 4, 5.0), 'Iron', n=64 if HIGH else 16)
    # conical roof with a vent cap, a wire bail
    n = 24 if HIGH else 8; th = np.linspace(0, 2 * PI, n + 1); roof = np.stack([0.078 * np.cos(th), 0.078 * np.sin(th), np.full_like(th, base + 0.2)], -1)
    roof2 = np.stack([0.02 * np.cos(th), 0.02 * np.sin(th), np.full_like(th, base + 0.26)], -1)
    Vr = np.vstack([roof, roof2]); Qr = grid_quads(2, n + 1, False); mesh('Roof', Vr, [orient(Vr, Qr, np.array([0, 0, 1.0]))], 'Iron', uv=np.stack([np.tile(th, 2) * 0.078, np.repeat([0, 0.06], n + 1)], -1))
    tube('Cap', np.array([[0, 0, base + 0.25], [0, 0, base + 0.29]]), [1.0, 0, 0], 0.02, 'Iron', n=12 if HIGH else 6, rad=[0.022, 0.012])
    a_ = np.linspace(0, PI, 20 if HIGH else 7); bail = np.stack([0.06 * np.cos(a_), np.zeros_like(a_), base + 0.27 + 0.07 * np.sin(a_)], -1)
    tube('Bail', bail, [0, 1.0, 0], 0.004, 'Iron', n=8 if HIGH else 4)
    tube('Hook', np.array([[0, 0, base + 0.34], [0, 0, base + 0.42], [0.03, 0, base + 0.45], [0.05, 0, base + 0.43]]), [0, 1.0, 0], 0.005, 'Iron', n=8 if HIGH else 4)
    # candle stub (wax) in the middle; the horn panes: 4 thin quads named Glass (unbaked, UE translucent material)
    tube('Candle', np.array([[0, 0, base + 0.012], [0, 0, base + 0.09]]), [1.0, 0, 0], 0.012, 'WaxRed', n=12 if HIGH else 6)
    Vs, Qs, Ts = superellipsoid(10 if HIGH else 6, 5 if HIGH else 3, 0.8); mesh('Flame', np.array([0, 0, base + 0.105]) + Vs * np.array([0.006, 0.006, 0.014]), [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 2]], -1) * 0.01, attrs={'glow': np.ones(len(Vs))})
    Vg, Qg = [], []   # the four horn panes as ONE object named exactly 'Glass' (the bake skips it; UE gets a translucent slot)
    for k in range(4):
        a = 2 * PI * k / 4; c_, s_ = math.cos(a), math.sin(a)
        P = np.array([[0.062 * c_ - 0.045 * s_, 0.062 * s_ + 0.045 * c_, base + 0.015], [0.062 * c_ + 0.045 * s_, 0.062 * s_ - 0.045 * c_, base + 0.015], [0.056 * c_ + 0.04 * s_, 0.056 * s_ - 0.04 * c_, base + 0.195], [0.056 * c_ - 0.04 * s_, 0.056 * s_ + 0.04 * c_, base + 0.195]])
        Qg.append(np.array([[0, 1, 2, 3]]) + 4 * k); Vg.append(P)
    mesh('Glass', np.vstack(Vg), [np.vstack(Qg)], 'Glass', uv=np.tile(np.array([[0, 0], [0.09, 0], [0.09, 0.18], [0, 0.18]]), (4, 1)))
    meta = {'size': [0.16, 0.16, 0.46], 'light': [0, 0, base + 0.1], 'note': 'pivot at the base; hang by the hook (top at z 0.45); point light 1800 K 150 cd at light, flicker; Glass slot = translucent horn'}

elif VAR == 'Signpost':   # #11: a post with 3 carved arrow boards at different heights/angles
    log('Post', (0, 0, -0.1), (0.01, 0.0, 2.3), 0.055, 2000, bend=0.008, tip1=0.1)
    for k, (z, yaw, L, flip) in enumerate(((2.05, 0.3, 0.9, 1), (1.78, -0.9, 0.75, -1), (1.5, 2.2, 0.8, 1))):
        c_, s_ = math.cos(yaw), math.sin(yaw); d = np.array([c_, s_, 0]) * flip
        p0 = np.array([0, 0, z]) - d * 0.12; p1 = np.array([0, 0, z]) + d * L
        plank('Board_%d' % k, tuple(p0), tuple(p1), 0.16, 0.03, 2010 + k, (-s_, c_, 0), rot=0.1)
        # the arrow point: a wedge plank at the far end
        tip = p1 + d * 0.12
        V, Q, Tr, uv = sweep(np.array([p1 - [0, 0, 0.0], tip]), np.tile([-s_, c_, 0.0], (2, 1)), rrect(0.16, 0.03, 8 if HIGH else 4, 6.0))
        M1 = (8 if HIGH else 4) + 1; G = V[:2 * M1].reshape(2, M1, 3); ctr = np.array([p1, tip])[:, None, :]; G[1] = ctr[1] + (G[1] - ctr[1]) * 0.05; V[:2 * M1] = G.reshape(-1, 3)
        K = M1 - 1; V[2 * M1 + K:2 * M1 + 2 * K] = G[-1, :K]; mesh('Tip_%d' % k, V, [Q, Tr], 'WoodCut', uv=uv)
        nails('BoardNails_%d' % k, [tuple(np.array([0, 0, z]) + d * 0.0 + np.array([-s_, c_, 0]) * 0.02 + [0, 0, dz]) for dz in (-0.04, 0.04)], (-s_, c_, 0), None, r=0.007)
    meta = {'size': [2.0, 2.0, 2.3], 'note': 'carve the names as a decal per board (DecalKit next), or leave blank and let the HUD label it'}

elif VAR == 'TargetDummy':   # #13: straw training dummy on a post: burlap body stuffed with straw, a straw head, a cross-arm, a battered shield disc, bolt holes decal goes on it
    log('Post', (0, 0, -0.1), (0.01, 0.0, 1.95), 0.05, 2100, bend=0.006)
    tube('Arm', np.array([[-0.55, 0.0, 1.35], [0.55, 0.0, 1.36]]), [0, 0, 1.0], 0.025, 'WoodCut', n=12 if HIGH else 6)
    kitlog.lash('ArmLash', (0, 0, 1.35), 0.05, (0, 0, 1.35), 0.025, (0, 0, 1), (1, 0, 0), 2101) if False else None
    a_ = np.linspace(0, 2 * PI * 3, 40 if HIGH else 14); kitlog.rope('ArmLash', np.stack([0.055 * np.cos(a_), 0.055 * np.sin(a_), 1.3 + 0.1 * a_ / (6 * PI)], -1), 0.005, 2101)
    # body: a sack shape (reuse the sack profile idea) around the post, straw bulging at the neck and waist
    nu, nv = (64, 40) if HIGH else (18, 10)
    T_, Z_ = np.meshgrid(np.linspace(0, 2 * PI, nu + 1), np.linspace(0, 1, nv + 1), indexing='ij')
    prof = (0.16 + 0.06 * np.sin(Z_ * PI) ** 0.7) * (1 - 0.25 * sstep(0.9, 1.0, Z_)) * (1 + 0.05 * (fbm(np.cos(T_) * 2, Z_ * 3, 2102, 3) - 0.5) * 2)
    if HIGH: prof = prof * (1 + 0.012 * (fbm(T_ * 4, Z_ * 12, 2103, 4) - 0.5) * 2)
    Vb = np.stack([prof * np.cos(T_) * 1.1, prof * np.sin(T_) * 0.8, 0.75 + 0.75 * Z_], -1).reshape(-1, 3)
    mesh('Body', Vb, [orient(Vb, grid_quads(nu + 1, nv + 1, False), np.array([1.0, 0, 0]))], 'Burlap', uv=np.stack([T_ * 0.18, Z_ * 0.75], -1).reshape(-1, 2))
    for z in (0.78, 1.47):   # straw bulging out top and bottom
        Vs, Qs, Ts = superellipsoid(32 if HIGH else 10, 8 if HIGH else 4, 0.7); mesh('Straw_%d' % int(z * 10), np.array([0, 0, z]) + Vs * np.array([0.17, 0.13, 0.03]), [Qs, Ts], 'Hay', uv=np.stack([Vs[:, 0], Vs[:, 1]], -1) * 0.15)
    Vs, Qs, Ts = superellipsoid(24 if HIGH else 10, 12 if HIGH else 5, 0.9); mesh('Head', np.array([0, 0, 1.68]) + Vs * (1 + 0.06 * (fbm(Vs[:, 0] * 4, Vs[:, 1] * 4, 2104, 3) - 0.5) * 2)[:, None] * np.array([0.12, 0.11, 0.14]), [Qs, Ts], 'Burlap', uv=np.stack([np.arctan2(Vs[:, 1], Vs[:, 0]) * 0.12, Vs[:, 2] * 0.14], -1))
    for sy in (-1, 1):   # twine at the neck and waist, a battered round plank disc on the left arm
        a_ = np.linspace(0, 2 * PI * 2, 30 if HIGH else 10); kitlog.rope('Twine_%d' % int(sy > 0), np.stack([0.15 * np.cos(a_) * 1.1, 0.15 * np.sin(a_) * 0.8, (1.49 if sy > 0 else 0.8) + 0.01 * a_ / (4 * PI)], -1), 0.004, 2105 + int(sy > 0))
    ring('ShieldRim', (-0.45, -0.05, 1.3), 0.22, rrect(0.04, 0.02, 8 if HIGH else 4, 5.0), 'WoodCut', axis=(0, 1.0, 0), n=48 if HIGH else 14)
    for b in range(5):
        x = -0.45 - 0.2 + 0.4 * (b + 0.5) / 5; hw = math.sqrt(max(0.21 ** 2 - (x + 0.45) ** 2, 0.001))
        plank('ShieldBoard_%d' % b, (x, -0.06, 1.3 - hw), (x, -0.06, 1.3 + hw), 0.4 / 5 - 0.004, 0.02, 2110 + b, (0, -1.0, 0), rot=0.3)
    meta = {'size': [1.2, 0.5, 2.0], 'note': 'put DecalKit BoltHoles on the body/shield; the shield arm takes hits (BP: damage numbers, no HP)'}

elif VAR == 'Burrow':   # #20: tentacle burrow: a 3 m ring of heaved earth and torn roots round a dark hole, flesh lip inside; the tentacle mesh rises from the hole
    n_a, n_r = (160, 24) if HIGH else (40, 8)
    th = np.linspace(0, 2 * PI, n_a + 1); rr = np.linspace(0, 1, n_r + 1)
    T, R = np.meshgrid(th, rr, indexing='ij')
    R0, R1 = 0.55, 1.5
    rad = R0 + (R1 - R0) * R; rad = rad * (1 + 0.08 * (fbm(np.cos(T) * 2 + 3, np.sin(T) * 2, 2200, 3) - 0.5) * 2 * R)
    Z = 0.32 * np.exp(-((R - 0.22) / 0.2) ** 2) * (1 + 0.3 * (fbm(T * 2, R * 3, 2201, 3) - 0.5) * 2)      # the heaved ring
    Z = Z - 0.5 * sstep(0.18, 0.0, R)                                                                     # down into the hole
    Z = Z * sstep(1.0, 0.8, R)                                                                            # flat at the rim
    if HIGH: Z = Z + 0.01 * (fbm(T * 6, R * 14, 2202, 4) - 0.5) * 2
    V = np.stack([rad * np.cos(T), rad * np.sin(T), Z], -1).reshape(-1, 3)
    glow = (sstep(0.35, 0.05, R)).reshape(-1)
    Q = grid_quads(n_a + 1, n_r + 1, False); mesh('Earth', V, [orient(V, Q, np.array([0, 0, 1.0]))], 'Corrupt' if False else 'Mortar', uv=np.stack([rad * np.cos(T), rad * np.sin(T)], -1).reshape(-1, 2) * 0.5)
    # inner flesh lip
    th2 = np.linspace(0, 2 * PI, (96 if HIGH else 24) + 1); rr2 = np.linspace(0, 1, (10 if HIGH else 4) + 1)
    T2, R2 = np.meshgrid(th2, rr2, indexing='ij'); rad2 = 0.18 + 0.42 * R2; Z2 = -0.5 + 0.2 * R2 ** 0.6 * 1.0 - 0.1 * (1 - R2) + 0.03 * np.sin(T2 * 9) * (1 - R2)
    V2 = np.stack([rad2 * np.cos(T2), rad2 * np.sin(T2), Z2], -1).reshape(-1, 3)
    mesh('Lip', V2, [orient(V2, grid_quads(len(th2), len(rr2), False), np.array([0, 0, 1.0]))], 'Leather', uv=np.stack([T2 * 0.4, R2 * 0.5], -1).reshape(-1, 2))
    for k in range(10):   # torn roots sticking out of the heaved ring
        a = rng.uniform(0, 2 * PI); r0 = rng.uniform(0.6, 1.1); L = rng.uniform(0.25, 0.6)
        # roots arch over the heaved ring (ring top 0.32 m): they never pass through it (intersections bake black)
        ctrl = np.array([[r0 * math.cos(a), r0 * math.sin(a), 0.38], [(r0 + L * 0.5) * math.cos(a + 0.2), (r0 + L * 0.5) * math.sin(a + 0.2), 0.42 + 0.15 * rng.random()], [(r0 + L) * math.cos(a + 0.35), (r0 + L) * math.sin(a + 0.35), 0.2]])
        s_ = np.linspace(0, 1, 14 if HIGH else 7)[:, None]; p = (1 - s_) ** 2 * ctrl[0] + 2 * (1 - s_) * s_ * ctrl[1] + s_ ** 2 * ctrl[2]   # smooth quadratic curve
        if HIGH: p = p + 0.01 * (fbm(s_[:, 0] * 6 + k, np.zeros(len(s_)), 2210 + k, 3) - 0.5)[:, None] * 2
        tube('Root_%d' % k, p, [0, 0, 1.0], 0.02, 'WoodCut', n=10 if HIGH else 5, rad=list(0.022 * (1 - s_[:, 0]) ** 0.8 + 0.004))
    meta = {'size': [3.2, 3.2, 0.4], 'hole_radius_m': 0.55, 'note': 'the tentacle actor sits at the origin and rises from z -0.5; add DecalKit GroundCrack x3 around it, realm fog low'}

json.dump({'grip': [0, 0, 0], **meta}, open(os.path.join(D, 'camp%s_meta.json' % VAR.lower()), 'w'))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Camp%s_%s.blend' % (VAR, 'high' if HIGH else 'low')))
print('BUILD OK')

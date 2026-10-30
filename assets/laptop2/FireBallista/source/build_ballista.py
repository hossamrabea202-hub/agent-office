# Fire-spear launcher (#10, laptop2 2026-10-30): a medieval torsion ballista on a swivel stand with a brazier that lights
# the spears. Pieces (vertex groups -> separate FBX): Base (stand + brazier), Frame (the launcher, pivots on the stand),
# Slider (the firing bar that recoils), Spear (one pitch-wrapped fire spear, pivot at the socket end).
#   blender -b --factory-startup -P build_ballista.py      (env RES = low | high)
# Units: metres, Z up. The launcher points +X (muzzle). The stand's pivot is at the base centre on z 0.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
import kitlog
from kitlog import log
from propkit import plank, strap, nails, group
from shieldkit import fbm, sstep, mesh, grid_quads, unit, sweep, rrect, circ, superellipsoid, dome, HIGH, PI
D = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(10)
def G(ob, g): return group(ob, g)

# ---- stand: three splayed legs lashed to a hub, a swivel post ----
HUB = np.array([0, 0, 1.05])
for k in range(3):
    a = 2 * PI * k / 3 + PI / 6
    G(log('Leg_%d' % k, (0.9 * math.cos(a), 0.9 * math.sin(a), -0.08), (0.12 * math.cos(a), 0.12 * math.sin(a), 1.12), 0.06, 600 + k, bend=0.012), 'Base')
G(log('Hub', (0, 0, 0.98), (0, 0, 1.18), 0.11, 610), 'Base')
for k in range(3):
    a = 2 * PI * k / 3 + PI / 6
    G(kitlog.lash('HubLash_%d' % k, (0.12 * math.cos(a), 0.12 * math.sin(a), 1.08), 0.06, (0, 0, 1.08), 0.11, (math.cos(a) * -0.3, math.sin(a) * -0.3, 1), (0, 0, 1), 620 + k), 'Base')
n = 12 if HIGH else 4
V, Q, Tr, uv = sweep(np.array([[0, 0, 1.15], [0, 0, 1.42]]), np.tile([1.0, 0, 0], (2, 1)), circ(0.03, 24 if HIGH else 8)); G(mesh('Pivot', V, [Q, Tr], 'Iron', uv=uv), 'Base')
# brazier: an iron bowl on a short tripod beside the stand, coals glowing
BR = np.array([-0.55, 0.75, 0.0])
for k in range(3):
    a = 2 * PI * k / 3; p = np.array([[BR[0] + 0.2 * math.cos(a), BR[1] + 0.2 * math.sin(a), 0.0], [BR[0] + 0.05 * math.cos(a), BR[1] + 0.05 * math.sin(a), 0.62]])
    V, Q, Tr, uv = sweep(p, np.tile([0, 0, 1.0], (2, 1)), rrect(0.02, 0.012, 8 if HIGH else 4, 5.0)); G(mesh('BrazierLeg_%d' % k, V, [Q, Tr], 'Iron', uv=uv), 'Base')
nu, nv = (96, 24) if HIGH else (20, 5)
th = np.linspace(0, 2 * PI, nu + 1); ph = np.linspace(0.08, 0.5, nv) * PI
T_, P_ = np.meshgrid(th, ph, indexing='ij'); rb = 0.26
bowl = BR + np.stack([rb * np.sin(P_) * np.cos(T_), rb * np.sin(P_) * np.sin(T_), 0.62 + rb * 0.75 - rb * 0.75 * np.cos(P_)], -1)
if HIGH: bowl = bowl + 0.0015 * (fbm(T_ * 4, P_ * 4, 71, 4) - 0.5)[..., None]
Vb = bowl.reshape(-1, 3); Qb = grid_quads(nu + 1, nv, False)
G(mesh('Bowl', Vb, [Qb], 'Iron', uv=np.stack([T_ * rb, P_ * rb], -1).reshape(-1, 2)), 'Base')
rim = BR + np.stack([(rb + 0.012) * np.cos(th), (rb + 0.012) * np.sin(th), np.full_like(th, 0.62 + rb * 0.75)], -1)
V, Q, Tr, uv = sweep(rim[:-1], np.tile([0, 0, 1.0], (nu, 1)), rrect(0.03, 0.015, 10 if HIGH else 4, 5.0), closed=True, caps=False); G(mesh('BowlRim', V, [Q], 'Iron', uv=uv), 'Base')
# coals: a mound of lumps, emissive 'glow' attribute (hotter in the middle)
for k in range(26 if HIGH else 14):
    a = rng.uniform(0, 2 * PI); r_ = rng.uniform(0, 0.17) ** 0.7 * 0.19; c = BR + [r_ * math.cos(a), r_ * math.sin(a), 0.62 + rb * 0.75 - 0.08 + 0.05 * (1 - r_ / 0.2)]
    Vs, Qs, Ts = superellipsoid(16 if HIGH else 8, 8 if HIGH else 4, 0.55); sz = rng.uniform(0.025, 0.05)
    if HIGH: Vs = Vs * (1 + 0.12 * (fbm(Vs[:, 0] * 4 + k, Vs[:, 1] * 4, 72, 3) - 0.5))[:, None]
    ob = mesh('Coal_%d' % k, c + Vs * np.array([sz, sz * 0.8, sz * 0.6]), [Qs, Ts], 'Coal', uv=np.stack([Vs[:, 0], Vs[:, 2]], -1) * sz, attrs={'glow': np.full(len(Vs), max(0.0, 1 - r_ / 0.2) * rng.uniform(0.5, 1.0))})
    G(ob, 'Base')

# ---- frame: the launcher on the swivel: a stock (beam), two torsion bundles in a head frame, two arms, the string ----
FZ = 1.45; STK = 1.9
G(log('Stock', (-0.55, 0.0, FZ), (STK - 0.55, 0.0, FZ + 0.01), 0.055, 630, bend=0.0), 'Frame')
plank('Rail', (-0.5, 0.0, FZ + 0.06), (STK - 0.6, 0.0, FZ + 0.065), 0.09, 0.03, 631, (0, 0, 1.0), rot=0.1, gname='Frame')
HX = STK - 0.95
for sy in (-1, 1):   # head frame: two uprights and a crossbar each side, holding the torsion bundle
    for dx in (-0.1, 0.1):
        plank('Head', (HX + dx, sy * 0.28, FZ - 0.18), (HX + dx, sy * 0.28, FZ + 0.32), 0.07, 0.05, 640, (0, sy, 0), rot=0.0, gname='Frame')
    plank('HeadBar', (HX - 0.16, sy * 0.28, FZ + 0.33), (HX + 0.16, sy * 0.28, FZ + 0.33), 0.08, 0.05, 641, (0, 0, 1.0), rot=0.0, gname='Frame')
    plank('HeadBar', (HX - 0.16, sy * 0.28, FZ - 0.19), (HX + 0.16, sy * 0.28, FZ - 0.19), 0.08, 0.05, 642, (0, 0, -1.0), rot=0.1, gname='Frame')
    # torsion bundle: a vertical skein of twisted cord between the bars
    n = 40 if HIGH else 6; zz = np.linspace(FZ - 0.16, FZ + 0.30, n)
    path = np.stack([np.full(n, HX), np.full(n, sy * 0.28), zz], -1)
    V, Q, Tr, uv = sweep(path, np.tile([1.0, 0, 0], (n, 1)), circ(1.0, 20 if HIGH else 8), caps=False)
    M1 = (20 if HIGH else 8) + 1; Gm = V[:n * M1].reshape(n, M1, 3); ctr = path[:, None, :]
    ang = np.linspace(0, 2 * PI, M1)[None, :]; tw = 0.034 * (1 + (0.12 * np.cos(ang * 6 - zz[:, None] * 70) if HIGH else np.zeros((n, M1))))
    V[:n * M1] = (ctr + (Gm - ctr) * tw[..., None]).reshape(-1, 3); uv[:n * M1, 0] *= 0.03
    G(mesh('Skein_%d' % (sy > 0), V, [Q], 'Rope', uv=uv), 'Frame')
    # the arm: a tapered beam through the skein, swept back
    a0 = np.array([HX, sy * 0.28, FZ + 0.07]); a1 = a0 + np.array([-0.42, sy * 0.58, 0.0])
    n = 30 if HIGH else 5; p = np.array([a0 + (a1 - a0) * t + [0, 0, 0.03 * math.sin(t * PI)] for t in np.linspace(0, 1, n)])
    V, Q, Tr, uv = sweep(p, np.tile([0, 0, 1.0], (n, 1)), rrect(1.0, 1.0, 12 if HIGH else 4, 5.0))
    M1 = (12 if HIGH else 4) + 1; Gm = V[:n * M1].reshape(n, M1, 3); ctr = p[:, None, :]
    tp = np.linspace(0, 1, n); sz = np.stack([0.05 - 0.025 * tp, 0.045 - 0.02 * tp], -1)
    off = Gm - ctr; Gs = ctr + off * sz[:, 0][:, None, None]; V[:n * M1] = Gs.reshape(-1, 3)
    K = M1 - 1; V[n * M1:n * M1 + K] = Gs[0, :K]; V[n * M1 + K:n * M1 + 2 * K] = Gs[-1, :K]
    G(mesh('Arm_%d' % (sy > 0), V, [Q, Tr], 'WoodCut', uv=uv * 0.05), 'Frame')
    kitlog.RR = 0.006
    G(kitlog.rope('ArmWrap_%d' % (sy > 0), [a0 + (a1 - a0) * t + [0, 0.0, 0.03 * math.sin(t * PI) + 0.052 * math.cos(q)] for t, q in zip(np.linspace(0.05, 0.3, 30), np.linspace(0, 5 * 2 * PI, 30))], 0.006, 650 + (sy > 0)), 'Frame')
# the string: a thick cord from arm tip to arm tip, pulled back to the slider's claw
tipL = np.array([HX - 0.42, -0.86, FZ + 0.07]); tipR = np.array([HX - 0.42, 0.86, FZ + 0.07]); claw = np.array([HX - 0.95, 0.0, FZ + 0.10])
sp = np.vstack([tipL + (claw - tipL) * t for t in np.linspace(0, 1, 20)] + [claw + (tipR - claw) * t for t in np.linspace(0, 1, 20)[1:]])
V, Q, Tr, uv = sweep(sp, np.tile([0, 0, 1.0], (len(sp), 1)), circ(0.012, 10 if HIGH else 5)); G(mesh('String', V, [Q, Tr], 'Rope', uv=uv), 'Frame')
# windlass at the back of the stock: a drum with spoke handles, a ratchet
WX = -0.45
V, Q, Tr, uv = sweep(np.array([[WX, -0.2, FZ + 0.12], [WX, 0.2, FZ + 0.12]]), np.tile([0, 0, 1.0], (2, 1)), circ(0.045, 24 if HIGH else 8)); G(mesh('Drum', V, [Q, Tr], 'WoodCut', uv=uv), 'Frame')
for sy in (-1, 1):
    for q in (0, PI / 2):
        p = np.array([[WX, sy * 0.22, FZ + 0.12], [WX + 0.22 * math.cos(q), sy * 0.22, FZ + 0.12 + 0.22 * math.sin(q)]])
        V, Q, Tr, uv = sweep(p, np.tile([0, 1.0, 0], (2, 1)), circ(0.014, 10 if HIGH else 5)); G(mesh('Spoke', V, [Q, Tr], 'WoodCut', uv=uv), 'Frame')
for sy in (-1, 1):
    plank('DrumPost', (WX, sy * 0.21, FZ - 0.02), (WX, sy * 0.21, FZ + 0.16), 0.06, 0.04, 660, (0, sy, 0), gname='Frame')
strap('Band', (WX - 0.25, 0.0, FZ + 0.085), (WX + 0.25, 0.0, FZ + 0.085), 0.05, 0.004, 'Frame', tip=False)

# ---- slider: a bar on the rail with the claw/trigger, drawn back ----
SL0 = HX - 1.05
plank('Slider', (SL0 - 0.35, 0.0, FZ + 0.10), (SL0 + 0.45, 0.0, FZ + 0.10), 0.075, 0.04, 670, (0, 0, 1.0), rot=0.0, gname='Slider')
for sy in (-1, 1):
    plank('Claw', (SL0 + 0.1, sy * 0.045, FZ + 0.12), (SL0 + 0.1, sy * 0.045, FZ + 0.20), 0.03, 0.012, 671, (0, sy, 0), gname='Slider')
V, Q, Tr, uv = sweep(np.array([[SL0 - 0.05, 0.0, FZ + 0.12], [SL0 - 0.05, 0.0, FZ + 0.21], [SL0 - 0.18, 0.0, FZ + 0.30]]), np.tile([0, 1.0, 0], (3, 1)), circ(0.012, 10 if HIGH else 5)); G(mesh('Trigger', V, [Q, Tr], 'Iron', uv=uv), 'Slider')

# ---- spear: 1.6 m ash shaft, iron head, the fore-end wrapped in pitch-soaked tow (burns), lying in the groove ----
SX0 = SL0 + 0.15; L = 1.6
n = 80 if HIGH else 6; p = np.array([[SX0 + L * t, 0.0, FZ + 0.145] for t in np.linspace(0, 1, n)])
V, Q, Tr, uv = sweep(p, np.tile([0, 0, 1.0], (n, 1)), circ(1.0, 16 if HIGH else 7))
M1 = (16 if HIGH else 7) + 1; Gm = V[:n * M1].reshape(n, M1, 3); ctr = p[:, None, :]; t_ = np.linspace(0, 1, n)[:, None, None]
rad = 0.016 - 0.004 * t_
wrap = ((t_ > 0.68) & (t_ < 0.9)).astype(float); rad = rad + wrap * (0.012 + (0.004 * np.abs(np.sin(t_ * 260)) if HIGH else 0))
V[:n * M1] = (ctr + (Gm - ctr) * rad).reshape(-1, 3); K = M1 - 1; V[n * M1:n * M1 + K] = V[:n * M1].reshape(n, M1, 3)[0, :K]; V[n * M1 + K:n * M1 + 2 * K] = V[:n * M1].reshape(n, M1, 3)[-1, :K]
uv[:, 0] *= 0.015
G(mesh('Shaft', V, [Q, Tr], 'Shaft', uv=uv, attrs={'wrap': np.r_[np.repeat(wrap[:, 0, 0], M1), np.repeat(wrap[0, 0, 0], K), np.repeat(wrap[-1, 0, 0], K), wrap[0, 0, 0], wrap[-1, 0, 0]]}), 'Spear')
hn = 24 if HIGH else 3; hp = np.array([[SX0 + L + 0.02 + 0.22 * t, 0.0, FZ + 0.145] for t in np.linspace(0, 1, hn)])
V, Q, Tr, uv = sweep(hp, np.tile([0, 0, 1.0], (hn, 1)), rrect(1.0, 1.0, 16 if HIGH else 4, 2.2))
M1 = (16 if HIGH else 4) + 1; Gm = V[:hn * M1].reshape(hn, M1, 3); ctr = hp[:, None, :]; th_ = np.linspace(0, 1, hn)[:, None, None]
sz = np.where(th_ < 0.25, 0.014 + 0.02 * th_ / 0.25, 0.034 * (1 - (th_ - 0.25) / 0.75) ** 1.1 + 0.001)
V[:hn * M1] = (ctr + (Gm - ctr) * sz * np.array([1, 1, 0.35])).reshape(-1, 3); K = M1 - 1; V[hn * M1:hn * M1 + K] = V[:hn * M1].reshape(hn, M1, 3)[0, :K]; V[hn * M1 + K:hn * M1 + 2 * K] = V[:hn * M1].reshape(hn, M1, 3)[-1, :K]
G(mesh('Head', V, [Q, Tr], 'Iron', uv=uv * 0.03), 'Spear')

meta = {'grip': [0, 0, 0], 'pieces': {'Base': [0, 0, 0], 'Frame': [0, 0, 1.42], 'Slider': [SL0, 0, FZ + 0.10], 'Spear': [SX0, 0, FZ + 0.145]},
        'muzzle': [STK - 0.55, 0, FZ + 0.145], 'spear_length': L + 0.24}
json.dump(meta, open(os.path.join(D, 'ballista_meta.json'), 'w'), indent=1)
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print('TRIS', tris, 'VERTS', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D, 'Ballista_%s.blend' % ('high' if HIGH else 'low')))
print('BUILD OK')

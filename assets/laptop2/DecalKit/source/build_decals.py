# Decal kit (laptop2 2026-10-30): blood splats, mud splashes, moss patches, scorch marks, a ground crack. Pure numpy: each
# decal is a 1K sheet of BaseColor + alpha (opacity), a normal map derived from its own height, and ORM. No bake needed.
#   blender -b --factory-startup -P build_decals.py      (writes tex/T_Decal_<Name>_*.png)
# Knowledge-base standard: blood is dark red that dries to brown with a glossy wet centre, never black; mud is 60-90 sRGB
# with matte dry rims; moss sits in the hollows; scorch fades from soot to tan.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(D, 'tex'); os.makedirs(TEX, exist_ok=True)
N = 1024
i = np.arange(N); U, V = np.meshgrid((i + 0.5) / N, (i + 0.5) / N, indexing='xy')
X, Y = U * 2 - 1, V * 2 - 1
R = np.hypot(X, Y); A = np.arctan2(Y, X)

def _hash(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0
def vnoise(u, v, s):
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64); fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = _hash(iu, iv, s), _hash(iu + 1, iv, s), _hash(iu, iv + 1, s), _hash(iu + 1, iv + 1, s)
    return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv
def fbm(u, v, s, oct=5, gain=0.5):
    t, amp, f, tot = 0, 1.0, 1.0, 0
    for o in range(oct):
        t = t + amp * vnoise(u * f, v * f, s + o * 17); tot += amp; amp *= gain; f *= 2.03
    return t / tot
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def srgb(l): return np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.power(np.maximum(l, 0), 1 / 2.4) - 0.055)
def normal_from_height(h, strength):
    gy, gx = np.gradient(h * strength)
    n = np.stack([-gx, gy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5          # DirectX: +Y down = our row direction after the flip below
def save(name, rgb, alpha=None, depth='8', srgb_encode=True):
    arr = srgb(np.clip(rgb, 0, 1)) if srgb_encode else np.clip(rgb, 0, 1)
    a = np.ones((N, N)) if alpha is None else np.clip(alpha, 0, 1)
    px = np.concatenate([arr, a[..., None]], -1)[::-1]          # Blender images start at the bottom row
    im = bpy.data.images.new(name, N, N, alpha=True, float_buffer=(depth == '16')); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(px.astype(np.float32).ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

def splat(seed, arms, spread, drips):
    """splash mask: a lobed blob with arms, satellite droplets and (optionally) drips running +Y (down)."""
    rng = np.random.default_rng(seed)
    lobes = 1 + 0.35 * (fbm(np.cos(A) * 2 + seed, np.sin(A) * 2, seed, 3) - 0.5) * 2
    core = sstep(0.55 * spread * lobes, 0.3 * spread * lobes, R)
    m = core.copy()
    for k in range(arms):
        a = rng.uniform(0, 2 * math.pi); L = rng.uniform(0.5, 0.95) * spread; w = rng.uniform(0.02, 0.06)
        t = (X * math.cos(a) + Y * math.sin(a)); s = (-X * math.sin(a) + Y * math.cos(a))
        arm = sstep(w * (1 - t / L) + 0.002, 0.0, np.abs(s) + 0.0 * t) * (t > 0.1 * spread) * (t < L)
        m = np.maximum(m, arm * sstep(L, L * 0.8, t))
        cx, cy = L * 1.08 * math.cos(a), L * 1.08 * math.sin(a); m = np.maximum(m, sstep(w * 1.6, w * 0.6, np.hypot(X - cx, Y - cy)))
    for k in range(int(14 * spread)):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.45, 0.98) * spread; rr = rng.uniform(0.006, 0.025)
        m = np.maximum(m, sstep(rr * 1.4, rr * 0.5, np.hypot(X - r * math.cos(a), Y - r * math.sin(a))))
    if drips:
        for k in range(drips):
            x0 = rng.uniform(-0.35, 0.35) * spread; y0 = rng.uniform(-0.1, 0.3); L = rng.uniform(0.25, 0.6); w = rng.uniform(0.012, 0.03)
            d = sstep(w * (1 - 0.6 * (Y - y0) / L), 0.0, np.abs(X - x0)) * (Y > y0) * (Y < y0 + L)
            d = np.maximum(d, sstep(w * 1.7, w * 0.8, np.hypot(X - x0, Y - (y0 + L))))
            m = np.maximum(m, d)
    edge = m * (1 + 0.25 * (fbm(U * 60, V * 60, seed + 5, 3) - 0.5) * 2)          # ragged edge
    return np.clip(edge, 0, 1)

def blood(name, seed, arms, spread, drips, age):
    m = splat(seed, arms, spread, drips)
    thick = sstep(0.2, 1.0, m) * sstep(0.6 * spread, 0.1, R)                     # pooled centre
    dry = np.clip(age + 0.4 * (fbm(U * 8, V * 8, seed + 9, 4) - 0.5) * 2 + 0.5 * (1 - thick), 0, 1)   # rims dry first
    wet_col = np.array([0.15, 0.010, 0.008]); dry_col = np.array([0.085, 0.028, 0.014]); dark = np.array([0.055, 0.006, 0.004])
    col = wet_col[None, None] * (1 - dry[..., None]) + dry_col[None, None] * dry[..., None]
    col = col * (1 - 0.55 * thick[..., None]) + dark[None, None] * 0.55 * thick[..., None]
    col = col * (0.85 + 0.3 * fbm(U * 40, V * 40, seed + 3, 3))[..., None]
    rg = 0.25 + 0.55 * dry + 0.15 * (fbm(U * 90, V * 90, seed + 4, 3) - 0.5)
    h = thick * 0.6 + m * 0.2
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([np.ones_like(m), np.clip(rg, 0, 1), np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 2.5), None, srgb_encode=False)

def mud(name, seed, arms, spread):
    m = splat(seed, arms, spread, 0)
    thick = sstep(0.25, 1.0, m) * sstep(0.55 * spread, 0.1, R)
    wet = np.clip(thick * 1.2 - 0.1 + 0.3 * (fbm(U * 6, V * 6, seed + 9, 3) - 0.5), 0, 1)
    tone = fbm(U * 10, V * 10, seed + 2, 4)
    col = np.array([0.16, 0.12, 0.08])[None, None] * (0.7 + 0.6 * tone)[..., None]
    col = col * (1 - 0.55 * wet[..., None]) + np.array([0.05, 0.035, 0.022])[None, None] * 0.55 * wet[..., None]
    col = col * (1 + 0.25 * (fbm(U * 120, V * 120, seed + 3, 2) - 0.5))[..., None]        # grit
    rg = 0.92 - 0.6 * wet + 0.1 * (fbm(U * 70, V * 70, seed + 4, 3) - 0.5)
    h = thick * 0.8 + m * 0.3 + 0.1 * fbm(U * 50, V * 50, seed + 6, 3) * m
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([1 - 0.3 * thick, np.clip(rg, 0, 1), np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 5.0), None, srgb_encode=False)

def moss(name, seed, spread):
    n = fbm(U * 5 + seed, V * 5, seed, 5, 0.6)
    m = sstep(0.36, 0.58, n * (1 - 0.3 * R / spread)) * sstep(spread, spread * 0.5, R)
    m = np.clip(m * (1 + 0.3 * (fbm(U * 50, V * 50, seed + 5, 3) - 0.5) * 2), 0, 1)
    clump = fbm(U * 60, V * 60, seed + 1, 3)
    col = np.array([0.045, 0.085, 0.022])[None, None] * (0.6 + 0.9 * clump)[..., None]
    col = col + np.array([0.08, 0.10, 0.02])[None, None] * sstep(0.6, 0.85, fbm(U * 200, V * 200, seed + 2, 2))[..., None] * 0.6   # lit tips
    col = col * (1 - 0.35 * sstep(0.8, 0.3, m))[..., None]                                     # thinner at the edge: darker, damp
    rg = 0.82 + 0.1 * (fbm(U * 120, V * 120, seed + 4, 2) - 0.5)
    h = m * (0.4 + 0.6 * clump)
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([1 - 0.4 * m, np.clip(rg, 0, 1), np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 6.0), None, srgb_encode=False)

def scorch(name, seed, spread, flare):
    rays = 1 + 0.5 * (fbm(np.cos(A) * 3 + seed, np.sin(A) * 3, seed, 3) - 0.5) * 2
    m = sstep(spread * rays, spread * 0.25 * rays, R)
    m = np.clip(m * (1 + 0.5 * (fbm(U * 20, V * 20, seed + 5, 4) - 0.5) * 2), 0, 1)
    soot = sstep(0.45, 1.0, m)                                            # black centre
    tan = sstep(0.6, 0.0, m) * m                                          # heat-tan ring
    col = np.array([0.03, 0.028, 0.026])[None, None] * soot[..., None] + np.array([0.20, 0.13, 0.07])[None, None] * tan[..., None] * 1.3
    col = col + np.array([0.12, 0.11, 0.10])[None, None] * sstep(0.5, 0.8, fbm(U * 90, V * 90, seed + 2, 3))[..., None] * soot[..., None] * 0.5   # ash flecks
    if flare:   # a few blown-out streaks (the fire spear's splash)
        for k in range(6):
            a = 2 * math.pi * k / 6 + seed; t = X * math.cos(a) + Y * math.sin(a); s = -X * math.sin(a) + Y * math.cos(a)
            st = sstep(0.05, 0.0, np.abs(s)) * (t > 0) * sstep(spread * 1.6, spread * 0.4, t)
            m = np.maximum(m, st * 0.7); col = col * (1 - st[..., None] * 0.5)
    rg = 0.95 - 0.1 * soot
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([np.ones_like(m), np.clip(rg, 0, 1), np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(-soot * 0.3, 1.5), None, srgb_encode=False)

def crack(name, seed):
    # a branching ground crack: a main line with children, dark inside, a lip of displaced earth
    m = np.zeros_like(U); rng = np.random.default_rng(seed)
    def line(p, a, L, w, depth):
        nonlocal m
        t = (X - p[0]) * math.cos(a) + (Y - p[1]) * math.sin(a); s = -(X - p[0]) * math.sin(a) + (Y - p[1]) * math.cos(a)
        wob = 0.03 * (fbm(t * 6 + seed + depth, np.full_like(t, depth), seed, 3) - 0.5) * 2
        seg = sstep(w, 0.0, np.abs(s - wob)) * (t > 0) * (t < L) * sstep(L, L * 0.6, t)
        m = np.maximum(m, seg)
        if depth < 3:
            for k in range(2):
                tt = rng.uniform(0.3, 0.8) * L; q = (p[0] + tt * math.cos(a), p[1] + tt * math.sin(a))
                line(q, a + rng.uniform(0.5, 1.2) * rng.choice([-1, 1]), L * rng.uniform(0.35, 0.6), w * 0.6, depth + 1)
    line((-0.9, rng.uniform(-0.3, 0.3)), rng.uniform(-0.2, 0.2), 1.8, 0.03, 0)
    inner = sstep(0.5, 1.0, m)
    col = np.array([0.045, 0.035, 0.025])[None, None] * (1 - 0.7 * inner)[..., None] + np.array([0.09, 0.07, 0.05])[None, None] * (1 - inner)[..., None]
    rim = sstep(0.0, 0.5, m) * (1 - inner)
    alpha = np.clip(m * 1.3, 0, 1)
    h = -inner * 1.0 + rim * 0.25
    save('T_Decal_%s_BaseColor' % name, col, alpha)
    save('T_Decal_%s_ORM' % name, np.stack([1 - 0.6 * inner, 0.9 - 0.1 * rim, np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 8.0), None, srgb_encode=False)


def footprints(name, seed):
    """a walking trail of boot prints in mud: left/right alternating, 0.75 m stride along +Y (down the sheet); hobnail sole."""
    rng = np.random.default_rng(seed); m = np.zeros_like(U); h = np.zeros_like(U)
    for k in range(6):
        cx = 0.0 + (0.11 if k % 2 else -0.11) + rng.uniform(-0.02, 0.02); cy = -0.85 + k * 0.34; a = rng.uniform(-0.12, 0.12)
        dx, dy = U * 2 - 1 - cx, V * 2 - 1 - cy
        x_, y_ = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        sole = np.clip(1 - ((x_ / 0.055) ** 2 + (y_ / 0.13) ** 2), 0, 1)                           # whole sole
        heel = np.clip(1 - ((x_ / 0.045) ** 2 + ((y_ - 0.085) / 0.05) ** 2), 0, 1)
        waist = np.exp(-((y_ - 0.03) / 0.03) ** 2) * 0.6                                            # the arch is lighter
        p = np.maximum(sole * (1 - waist), heel) ** 0.5
        nails = 0
        for nx in (-0.03, 0.0, 0.03):
            for ny in np.linspace(-0.1, 0.06, 5):
                nails = np.maximum(nails, sstep(0.009, 0.004, np.hypot(x_ - nx, y_ - ny)))
        depth = (0.6 + 0.4 * rng.random()) * (1 - 0.12 * k)                                         # fading as the mud dries along the trail
        m = np.maximum(m, p * depth); h = np.minimum(h, -(p * 0.8 + nails * 0.5) * depth)
    m = np.clip(m * (1 + 0.3 * (fbm(U * 90, V * 90, seed + 3, 3) - 0.5) * 2), 0, 1)
    col = np.array([0.075, 0.055, 0.035])[None, None] * (0.8 + 0.4 * fbm(U * 30, V * 30, seed + 2, 3))[..., None]
    rg = 0.55 + 0.25 * m
    save('T_Decal_%s_BaseColor' % name, col, m * 0.85)
    save('T_Decal_%s_ORM' % name, np.stack([1 - 0.5 * m, np.clip(rg, 0, 1), np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 6.0), None, srgb_encode=False)

def boltholes(name, seed):
    """crossbow bolts stuck in wood: 5 impact holes with split grain around them and a dark bruise; the bolt shafts
    themselves are meshes, this is the wood damage under them."""
    rng = np.random.default_rng(seed); m = np.zeros_like(U); h = np.zeros_like(U)
    for k in range(5):
        cx, cy = rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6); dx, dy = X - cx, Y - cy; d = np.hypot(dx, dy)
        hole = sstep(0.03, 0.012, d); bruise = sstep(0.14, 0.02, d) * 0.5
        splits = 0
        for s in range(3):
            a = rng.uniform(0, math.pi); t = dx * math.cos(a) + dy * math.sin(a); n = -dx * math.sin(a) + dy * math.cos(a)
            L = rng.uniform(0.08, 0.2); splits = np.maximum(splits, sstep(0.006 * (1 + 2 * np.abs(t) / L), 0.0, np.abs(n)) * (np.abs(t) < L) * (1 - np.abs(t) / L))
        m = np.maximum(m, np.clip(hole + bruise + splits * 0.8, 0, 1)); h = np.minimum(h, -(hole * 1.0 + splits * 0.5))
    col = np.array([0.06, 0.04, 0.025])[None, None] * (0.7 + 0.6 * fbm(U * 40, V * 40, seed + 2, 3))[..., None]
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([1 - 0.6 * m, 0.7 + 0.2 * m, np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(h, 7.0), None, srgb_encode=False)

def muzzlescorch(name, seed):
    """cannon muzzle blast on the ground: a fan of soot in front of the muzzle (+Y), burnt grass ring, powder flecks."""
    ang = np.arctan2(Y + 0.8, X); fan = np.exp(-((ang - math.pi / 2) / 0.45) ** 2)
    dist = np.hypot(X, Y + 0.8); m = fan * sstep(1.6, 0.3, dist) * sstep(0.1, 0.3, dist)
    m = np.clip(m * (0.7 + 0.6 * fbm(U * 12, V * 12, seed, 4)), 0, 1)
    streaks = sstep(0.75, 0.95, fbm(np.arctan2(Y + 0.8, X) * 40, dist * 3, seed + 1, 3)) * m
    m = np.clip(m + streaks * 0.5, 0, 1)
    soot = sstep(0.3, 0.9, m); col = np.array([0.03, 0.028, 0.025])[None, None] * soot[..., None] + np.array([0.18, 0.12, 0.06])[None, None] * (m * (1 - soot))[..., None] * 1.2
    col = col + np.array([0.14, 0.13, 0.12])[None, None] * sstep(0.6, 0.85, fbm(U * 120, V * 120, seed + 2, 2))[..., None] * m[..., None] * 0.4
    save('T_Decal_%s_BaseColor' % name, col, m)
    save('T_Decal_%s_ORM' % name, np.stack([np.ones_like(m), 0.92 - 0.1 * soot, np.zeros_like(m)], -1), None, srgb_encode=False)
    save('T_Decal_%s_Normal_DirectX' % name, normal_from_height(-soot * 0.15, 1.0), None, srgb_encode=False)

blood('BloodSplatA', 1, 7, 0.8, 0, 0.2); blood('BloodSplatB', 2, 4, 0.6, 0, 0.6); blood('BloodDrips', 3, 3, 0.45, 5, 0.3)
mud('MudSplashA', 11, 6, 0.85); mud('MudSplashB', 12, 9, 0.7)
moss('MossPatchA', 21, 0.9); moss('MossPatchB', 22, 0.7)
scorch('ScorchA', 31, 0.75, False); scorch('ScorchFlare', 32, 0.55, True)
crack('GroundCrack', 41)
footprints('Footprints', 51); boltholes('BoltHoles', 61); muzzlescorch('MuzzleScorch', 71)
print('DECALS OK')

# #337 blood splat decals (adjustedfilm, 2026-10-31). Procedural, by the rules in handoffs/gore-337/RESEARCH.md §2 / §5.2.
#   "<blender python>" -I make_splats.py <out folder>
# Writes a 4 x 2 atlas (2048 x 1024, 512 px per splat, 8 variants, one splat = 40 cm at 1:1):
#   T_BloodSplat_337_BC.png   sRGB colour: thin film edges 110,20,14 -> thick core 60,18,12 (zombie blood; the KB floor of
#                             30 sRGB luminance keeps the core at 60 instead of the measured 50), dried rim slightly darker
#   T_BloodSplat_337_N.png    tangent normal from the blood thickness (meniscus edge, domed pools, beaded satellites)
#   T_BloodSplat_337_M.png    linear masks: R thickness 0..1, G opacity, B dry rim (coffee-ring edge where blood dries first)
# Physics behind the shapes: a pool from a falling drop / spray (round body, crown spines that end in satellite droplets),
# angled impacts stretch into ellipses with a tail on the far side (spine length grows with the angle), and fine spray
# misting around (1-4 mm droplets, forensic slash spatter, render size 2-12 px here).
import os, sys, zlib, struct
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)
T, NX, NY = 512, 4, 2
rng = np.random.default_rng(337)
yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
U, V = (xx - T / 2) / (T / 2), (yy - T / 2) / (T / 2)          # -1..1, 1 = 20 cm


def noise(freq, seed):
    """smooth value noise on the tile (bilinear upsample of random grid)"""
    r = np.random.default_rng(seed).random((freq + 1, freq + 1)).astype(np.float32)
    gx, gy = xx / T * freq, yy / T * freq
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b_, c, d = r[y0, x0], r[y0, x0 + 1], r[y0 + 1, x0], r[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b_ * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


PX = 2.0 / T                                                   # one pixel in U/V units (1 U = 20 cm)


def smin(a, b_, k):
    """smooth union of two signed distances (blood merges by surface tension)"""
    m = np.minimum(a, b_)
    return m - k * np.log1p(np.exp(-np.abs(a - b_) / k)) if k > 0 else m


class Field:
    """signed distance (negative inside) built from primitives in warped tile space"""
    def __init__(s, seed, warp=0.035, fine=0.008):
        wx = (noise(5, seed) - 0.5) * 2 * warp + (noise(19, seed + 1) - 0.5) * 2 * fine
        wy = (noise(5, seed + 2) - 0.5) * 2 * warp + (noise(19, seed + 3) - 0.5) * 2 * fine
        s.u, s.v, s.d = U + wx, V + wy, np.full(U.shape, 9.0, np.float32)
    def add(s, d, k=0.02): s.d = smin(s.d, d, k)
    def ellipse(s, cx, cy, r, sx=1.0, rot=0.0, k=0.02):
        du, dv = s.u - cx, s.v - cy
        a_, b_ = (du * np.cos(rot) + dv * np.sin(rot)) / sx, -du * np.sin(rot) + dv * np.cos(rot)
        s.add((np.sqrt(a_ * a_ + b_ * b_) - r) * min(1.0, sx), k)
    def taper(s, x0, y0, r0, x1, y1, r1, k=0.015):
        bx, by = x1 - x0, y1 - y0; L2 = bx * bx + by * by + 1e-9
        h = np.clip(((s.u - x0) * bx + (s.v - y0) * by) / L2, 0, 1)
        dx, dy = s.u - (x0 + h * bx), s.v - (y0 + h * by)
        s.add(np.sqrt(dx * dx + dy * dy) - (r0 + (r1 - r0) * h), k)
    def tadpole(s, x, y, r, ang, tail, sx=1.0):
        """an angled-impact droplet: elliptical stain, tail on the leading side (direction of travel)"""
        s.ellipse(x, y, r, sx, ang, k=0.0)
        s.taper(x + np.cos(ang) * r * sx * 0.7, y + np.sin(ang) * r * sx * 0.7, r * 0.45,
                x + np.cos(ang) * (r * sx + tail), y + np.sin(ang) * (r * sx + tail), PX * 0.4, k=0.004)
    def mist(s, rng, n, cx, cy, spread, ang=None, cone=np.pi):
        for i in range(n):
            th = (ang if ang is not None else 0) + rng.uniform(-cone, cone)
            rr = spread * (0.4 + rng.exponential(0.6))
            r = float(np.clip(rng.lognormal(np.log(PX * 1.6), 0.5), PX * 0.7, PX * 6))
            sx = 1.0 + rng.uniform(0, 1.2) * (ang is not None)
            s.ellipse(cx + np.cos(th) * rr, cy + np.sin(th) * rr, r, sx, th, k=0.0)


def splat(k):
    s = np.random.default_rng(1000 + k)
    F = Field(500 + 7 * k)
    if k in (0, 1, 2, 3):                                     # drop pools: vertical (0, 1) and angled 30 / 50 deg (2, 3)
        sx = [1.0, 1.0, 1.15, 1.55][k]; rot = s.uniform(0, 2 * np.pi)
        r = [0.20, 0.13, 0.17, 0.15][k]
        F.ellipse(0, 0, r, sx, rot)
        n = [26, 9, 18, 14][k]
        for i in range(n):                                    # crown scallops / spines, longer on the leading side
            th = rot + s.normal(0, 1.2 if k >= 2 else 3.0)
            lead = max(0.0, np.cos(th - rot)) if k >= 2 else 0.5
            base = r * (1.0 + (sx - 1) * max(0.0, np.cos(th - rot)))
            L = s.uniform(0.02, 0.07) + lead * s.uniform(0.0, 0.12) * (k >= 2)
            w = s.uniform(0.008, 0.022)
            x0, y0 = np.cos(th) * base * 0.9, np.sin(th) * base * 0.9
            x1, y1 = np.cos(th) * (base + L), np.sin(th) * (base + L)
            F.taper(x0, y0, w, x1, y1, w * 0.35)
            if s.random() < 0.55:                             # satellite flung off the spine tip
                d = base + L + s.uniform(0.02, 0.09)
                F.tadpole(np.cos(th) * d, np.sin(th) * d, s.uniform(0.006, 0.02), th, s.uniform(0.0, 0.03), 1 + 0.5 * lead)
        if k >= 2:                                            # the exclamation tail on the leading edge
            F.taper(np.cos(rot) * r * sx * 0.8, np.sin(rot) * r * sx * 0.8, r * 0.35, np.cos(rot) * (r * sx + 0.18), np.sin(rot) * (r * sx + 0.18), PX, k=0.03)
        F.mist(s, 70, 0, 0, r * 1.6, rot if k >= 2 else None, 0.7 if k >= 2 else np.pi)
    elif k == 4:                                              # cast-off from a swung blade: a curved line of tadpoles
        a0 = s.uniform(0, np.pi); bend = s.uniform(-0.6, 0.6)
        for i, t in enumerate(np.linspace(-0.8, 0.8, 16)):
            ang = a0 + bend * t
            x, y = np.cos(a0) * t * 0.95 + -np.sin(a0) * bend * t * t * 0.3, np.sin(a0) * t * 0.95 + np.cos(a0) * bend * t * t * 0.3
            r = 0.012 + 0.02 * np.exp(-((t + 0.2) / 0.5) ** 2) * s.uniform(0.6, 1.2)
            F.tadpole(x + s.normal(0, 0.015), y + s.normal(0, 0.015), r, ang, s.uniform(0.02, 0.06), s.uniform(1.6, 2.6))
        F.mist(s, 60, 0, 0, 0.35, a0, 0.25)
    elif k == 5:                                              # drip trail from a walking wound: round drops, small crowns
        x, y, a = -0.75, s.uniform(-0.3, 0.3), s.uniform(-0.3, 0.3)
        while x < 0.75:
            r = s.uniform(0.018, 0.04)
            F.ellipse(x, y, r, 1.05, a)
            for j in range(s.integers(3, 8)):
                th = s.uniform(0, 2 * np.pi); F.taper(x + np.cos(th) * r, y + np.sin(th) * r, r * 0.25, x + np.cos(th) * (r + 0.015), y + np.sin(th) * (r + 0.015), PX * 0.5, k=0.006)
            a += s.normal(0, 0.25); step = s.uniform(0.1, 0.22)
            x += np.cos(a) * step; y = np.clip(y + np.sin(a) * step, -0.6, 0.6)
        F.mist(s, 25, 0, 0, 0.5)
    elif k == 6:                                              # a pool from several drops merged (zombie standing / falling)
        for j in range(9):
            F.ellipse(s.normal(0, 0.2), s.normal(0, 0.14), s.uniform(0.05, 0.13), s.uniform(1.0, 1.6), s.uniform(0, np.pi), k=0.04)
        for j in range(12):
            th = s.uniform(0, 2 * np.pi); d = s.uniform(0.3, 0.6)
            F.tadpole(np.cos(th) * d, np.sin(th) * d, s.uniform(0.008, 0.025), th, s.uniform(0, 0.03))
        F.mist(s, 40, 0, 0, 0.45)
    else:                                                     # slash spray: a fan of fast droplets from one point, no pool
        a0 = s.uniform(0, 2 * np.pi)
        for j in range(60):
            th = a0 + s.normal(0, 0.28); d = 0.1 + s.exponential(0.3)
            if d > 1.2: continue
            ox, oy = -np.cos(a0) * 0.55, -np.sin(a0) * 0.55      # fan starts off-centre so it fills the tile
            F.tadpole(ox + np.cos(th) * d, oy + np.sin(th) * d, float(np.clip(s.lognormal(np.log(0.012), 0.5), 0.004, 0.035)), th, s.uniform(0.01, 0.05), s.uniform(1.5, 3.0))
        F.mist(s, 90, 0, 0, 0.3, a0, 0.35)
    d = F.d + (1 - np.clip((1 - np.maximum(abs(U), abs(V))) * 10, 0, 1)) * 0.2      # nothing reaches the tile border
    op = np.clip(0.5 - d / PX, 0, 1)                                                  # 1 px anti-aliased meniscus edge
    depth = np.clip(-d / 0.05, 0, 1)                                                  # 1 cm in from the edge = full thickness
    thick = (depth ** 0.5) * (0.88 + 0.12 * noise(30, 90 + k)) * op
    rim = np.clip(1 - np.abs(d + PX * 2.5) / (PX * 2.5), 0, 1) * op                  # dried ring just inside the edge
    return op, thick, rim


def srgb_to_lin(c): c = np.asarray(c, np.float32) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin_to_srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


EDGE, CORE = srgb_to_lin((110, 20, 14)), srgb_to_lin((60, 18, 12))
W, H = T * NX, T * NY
BC = np.zeros((H, W, 4), np.float32); NM = np.zeros((H, W, 3), np.float32); MK = np.zeros((H, W, 3), np.float32)
for k in range(NX * NY):
    op, th, rim = splat(k)
    tx, ty = (k % NX) * T, (k // NX) * T
    t = np.clip(th, 0, 1)[..., None]
    col = EDGE * (1 - t) + CORE * t
    col = col * (1 - 0.18 * rim[..., None])                   # dried rim a bit darker
    # background colour = the core colour (premultiplied-safe for mips; opacity hides it)
    col = col * op[..., None] + CORE * (1 - op[..., None])
    BC[ty:ty + T, tx:tx + T, :3] = lin_to_srgb(col); BC[ty:ty + T, tx:tx + T, 3] = op
    h = th * 6.0                                              # height in px units -> normal
    gy_, gx_ = np.gradient(h)
    n = np.dstack([-gx_, gy_, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    NM[ty:ty + T, tx:tx + T] = n * 0.5 + 0.5
    MK[ty:ty + T, tx:tx + T] = np.dstack([th, op, rim])


def png(path, a, srgb=True):
    a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    h, w, c = a.shape
    raw = b''.join(b'\x00' + a[y].tobytes() for y in range(h))
    ct = {3: 2, 4: 6}[c]
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ct, 0, 0, 0)) +
                           chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    print('wrote', path, a.shape)


png(os.path.join(OUT, 'T_BloodSplat_337_BC.png'), BC)
png(os.path.join(OUT, 'T_BloodSplat_337_N.png'), NM)
png(os.path.join(OUT, 'T_BloodSplat_337_M.png'), MK)
# a flat ORM-style sheet only for pbr_check (wet 0.08 .. tacky 0.3 by thickness): R ao 1, G roughness, B metal 0
ormc = np.dstack([np.ones((H, W)), 0.08 + 0.22 * (1 - MK[..., 0]), np.zeros((H, W))])
# png(os.path.join(OUT, "pbrcheck_ORM.png"), ormc)   # only for a pbr_check run

"""WinterKeep #390: terrain generator (heightmap, snow depth, weight maps, splines).

Run with Blender's Python (numpy only, no Blender needed):
  "C:\\Program Files\\Blender Foundation\\Blender 4.5\\4.5\\python\\bin\\python.exe" -I gen_terrain.py [--seed 390] [--fast]

Writes into ./out:
  WinterKeep_Height_2017.png   16-bit grey, 2017 x 2017, 1 m per pixel (UE recommended size: 16x16 comps, 63 quads, 2x2)
  WinterKeep_Height_2017.r16   same data, raw little-endian (fallback for the Landscape import dialog)
  WL_<layer>.png               8-bit weight maps (sum to 255 per pixel)
  M_<mask>.png                 dressing masks (forest, birch, drift, wind exposure, rocks)
  layout.json                  feature points, road / river / mine-road splines in UE world cm, import numbers
  preview_*.png                quick looks (hillshade, layers)

World: X east, Y south (UE +X, +Y), origin = map centre. Height in the PNG maps to metres exactly:
  UE Location Z = 20200 cm, Scale = (100, 100, 78.125). 1 grey step = 0.61 cm.
Geology first: an old glacial valley (U-shape) between a high NW ridge and lower SE hills. Prevailing winter wind from the
north-west (315 deg), so NW faces are scoured to rock and SE (lee) sides collect drifts (Winstral Sx shelter index).
"""
import json, math, os, struct, sys, time, zlib
import numpy as np

N = 2017                     # vertices per side, 1 m spacing -> 2016 m
HALF = (N - 1) / 2.0
Z_SCALE = 78.125             # UE landscape Z scale: +-256*Z/100 m around Location Z = +-200 m
Z_CENTRE_M = 202.0           # Location Z = 20200 cm, so grey values map back to true metres (range 2..402 m)
WIND = np.array([1.0, 1.0]) / math.sqrt(2)   # wind blows TOWARD +x,+y (from the NW)
ARGS = sys.argv[1:]
SEED = int(ARGS[ARGS.index('--seed') + 1]) if '--seed' in ARGS else 390
FAST = '--fast' in ARGS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)
T0 = time.time()
def log(*a): print('[%5.1fs]' % (time.time() - T0), *a, flush=True)

# ---------------------------------------------------------------- layout (metres, image space: x east, y south, 0..2016)
CASTLE = (1010.0, 930.0)          # castle centre; castle box 46 x 34.5 m, plateau 96 x 84 m
CASTLE_TOP = 62.0                 # plateau height (m); valley floor ~ 15-25 m
LAKE = (560.0, 1560.0, 300.0, 175.0, math.radians(-18))   # centre, semi-axes, rotation
LAKE_ICE = 4.0                    # ice surface height (m); lake bed below
# river: from the north gorge (frozen waterfall) down the east side of the rise, bending SW into the lake
RIVER = [(1290, -20), (1270, 120), (1250, 240), (1235, 330), (1210, 470), (1185, 600), (1160, 720), (1150, 850),
         (1140, 980), (1105, 1090), (1030, 1160), (930, 1215), (830, 1280), (735, 1360), (660, 1430)]
FALLS = (1252, 236)               # frozen waterfall: river drops over a rock step here
BRIDGE = (1100, 1095)             # gate road crosses the river here (narrowest, rock both banks)
GATE = (1036, 968)                # gate faces SSE, down to the bridge
# gate road: from the SE valley exit (map edge) up to the gate, packed and rutted
ROAD = [(2040, 1840), (1900, 1720), (1760, 1600), (1620, 1500), (1480, 1400), (1360, 1300), (1250, 1210), (1170, 1140),
        BRIDGE, (1072, 1050), (1050, 1005), GATE]
MINE = (395.0, 720.0)             # mine portal in the iced cliff of the west ridge, facing east
MINE_ROAD = [(985, 960), (900, 945), (800, 920), (700, 880), (600, 820), (510, 760), (440, 728), MINE]
AVALANCHE = [(1690, 160), (1660, 300), (1620, 430), (1585, 560), (1560, 650)]   # gully top -> runout fan
FARMS = {'Farm_East': (1480, 860), 'Farm_Road': (1500, 1450), 'Farm_North': (1000, 560)}
REALM = (1640.0, 1060.0, 115.0)   # tentacle realm: melt ring radius (m), wet black ground + steam
FIRST_VIEW = {'from': (1044, 978, CASTLE_TOP + 12), 'look_at': (1180, 1150, 44)}   # wall-walk over the gate -> bridge and road

yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)

def poly_dist(pts, warp=0.0, wseed=50):
    """Distance (m) from every pixel to a polyline, plus the parameter along it (0..1). warp = meander amplitude (m)."""
    X, Y = (xx, yy) if not warp else (xx + warp * vnoise(140, 3, 0.45, wseed), yy + warp * vnoise(140, 3, 0.45, wseed + 1))
    pts = np.array(pts, np.float32)
    best = np.full((N, N), 1e9, np.float32); tpar = np.zeros((N, N), np.float32)
    seg = np.linalg.norm(pts[1:] - pts[:-1], axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); total = cum[-1]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a; L2 = float(ab @ ab) + 1e-6
        t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / L2, 0, 1)
        d = np.hypot(X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1]))
        m = d < best; best[m] = d[m]; tpar[m] = ((cum[i] + t * seg[i]) / total)[m]
    return best, tpar

def smooth(a, r):
    """Box blur, radius r px, 3 passes (~Gaussian)."""
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r)] if ax == 0 and a.ndim == 1 else ([(r + 1, r), (0, 0)] if ax == 0 else [(0, 0), (r + 1, r)]), mode='edge'), axis=ax)
            a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a.astype(np.float32)

def vnoise(scale, octaves=5, persist=0.5, seed=0, ridged=False):
    return vnoise_at(xx, yy, scale, octaves, persist, seed, ridged)

def vnoise_at(X, Y, scale, octaves=5, persist=0.5, seed=0, ridged=False):
    """fBm value noise (smoothstep-interpolated lattice) at coords X, Y; roughly -1..1."""
    r = np.random.default_rng(SEED * 31 + seed); total = np.zeros((N, N), np.float32); amp = 1.0; norm = 0.0; f = 1.0 / scale
    X = X + 400.0; Y = Y + 400.0          # offset, never clamp (clamping made flat boxes)
    for _ in range(octaves):
        g = int((N + 800) * f) + 3; lat = r.uniform(-1, 1, (g, g)).astype(np.float32)
        u = X * f; v = Y * f; i = u.astype(int); j = v.astype(int); fu = u - i; fv = v - j
        fu = fu * fu * (3 - 2 * fu); fv = fv * fv * (3 - 2 * fv)
        n = (lat[j, i] * (1 - fu) + lat[j, i + 1] * fu) * (1 - fv) + (lat[j + 1, i] * (1 - fu) + lat[j + 1, i + 1] * fu) * fv
        if ridged: n = 1 - 2 * np.abs(n)
        total += amp * n; norm += amp; amp *= persist; f *= 2.0
    return total / norm

def grad(h):
    gy, gx = np.gradient(h); return gx, gy

# ---------------------------------------------------------------- 1. base landform
log('base landform')
# glacial valley axis runs NNE -> SSW, through the castle; U-shaped cross profile
ax_pts = [(1330, -50), (1200, 500), (1050, 950), (820, 1400), (600, 1800), (450, 2100)]
d_axis, t_axis = poly_dist(ax_pts, warp=150.0, wseed=60)
d_axis = d_axis * (1 + 0.25 * vnoise(300, 3, 0.5, 61))           # tributary spurs and bays break the wall
side = np.tanh(((xx - CASTLE[0]) * 0.9 - (yy - CASTLE[1]) * 0.35) / 260.0)     # >0 east side, <0 west side (soft)
valley_w = 380.0
u_profile = 1.6 * (1 - np.exp(-(np.clip(d_axis / valley_w, 0, None) ** 2.4)))  # U-shape: flat floor, walls ease into shoulders
west = (1 - side) / 2                                                         # 1 = west of the axis, 0 = east
north = np.clip((520 - yy) / 520, 0, 1) ** 1.3                               # the valley head: mountains close the north
east_terr = 1 - np.exp(-(np.clip(d_axis, 0, None) / 650.0) ** 2)               # east: low rolling outwash terraces
h = (18.0 + 22.0 * (1 - t_axis) + west * 215.0 * np.clip(u_profile, 0, 1.6) / 1.6
     + (1 - west) * (72.0 * east_terr + north * 150.0 * np.clip(u_profile, 0, 1.6) / 1.6))
# mountains: ridged noise on the west ridge and the north head only
WX = xx + 90 * vnoise(500, 3, 0.5, 40); WY = yy + 90 * vnoise(500, 3, 0.5, 41)   # domain warp: no grid-aligned ridges
ridge = vnoise_at(WX, WY, 380, 4, 0.45, 1, ridged=True)
mt_mask = np.clip(u_profile - 0.25, 0, 1.5) * np.clip(west + north, 0, 1)
h += mt_mask * (35 + 55 * ridge) + 25 * north * mt_mask
h += 9.0 * vnoise(160, 5, 0.5, 2) + 3.0 * vnoise(40, 4, 0.5, 3) + (1 - west) * (1 - north) * 12.0 * vnoise(240, 3, 0.5, 5)   # moraine humps; rolling east
# castle rise: a rocky glacial knob (roche moutonnee) - smooth stoss slope to the NW, plucked steep lee to the SE
dx, dy = xx - CASTLE[0], yy - CASTLE[1]
along = (dx * WIND[0] + dy * WIND[1]); across = (-dx * WIND[1] + dy * WIND[0])
knob_r = np.where(along < 0, np.hypot(along / 230.0, across / 150.0), np.hypot(along / 175.0, across / 140.0))
h = np.maximum(h, CASTLE_TOP - 6 - (CASTLE_TOP - 38) * np.clip(knob_r, 0, 1) ** 1.6 - 30 * np.clip(knob_r - 1, 0, 1) + 4 * vnoise(25, 3, 0.5, 4) * np.clip(knob_r, 0.2, 1))
# west cliff for the mine: a steep rock step on the west ridge, facing east
mine_d = np.hypot((xx - MINE[0]) / 60.0, (yy - MINE[1]) / 220.0)
cliff = np.clip((MINE[0] + 25 + 14 * vnoise(30, 3, 0.5, 70) - xx) / 30.0, 0, 1) * np.clip(1.3 - mine_d, 0, 1)
h = h + cliff * 55.0 - np.clip(1 - mine_d, 0, 1) * np.clip((xx - MINE[0]) / 80, 0, 1) * 6
# avalanche gully: a cut into the NE slope, with a runout fan at the bottom
gd, gt = poly_dist(AVALANCHE)
h -= 14.0 * np.exp(-(gd / 28.0) ** 2) * np.clip(1.2 - gt, 0, 1)
fan = np.exp(-((xx - AVALANCHE[-1][0]) ** 2 + (yy - AVALANCHE[-1][1]) ** 2) / (2 * 70.0 ** 2))
h += 5.0 * fan
h = h.astype(np.float32)

# ---------------------------------------------------------------- 2. erosion (droplet hydraulic + thermal)
def hydraulic(h, drops, steps, batch):
    """Vectorised droplet erosion (Mei/Beyer style), many droplets in parallel."""
    inertia, cap_k, dep_k, ero_k, evap, g, min_slope = 0.1, 3.0, 0.3, 0.2, 0.025, 9.0, 0.01
    for b0 in range(0, drops, batch):
        n = min(batch, drops - b0)
        px = rng.uniform(2, N - 3, n).astype(np.float32); py = rng.uniform(2, N - 3, n).astype(np.float32)
        dxv = np.zeros(n, np.float32); dyv = np.zeros(n, np.float32)
        vel = np.ones(n, np.float32); water = np.ones(n, np.float32); sed = np.zeros(n, np.float32)
        alive = np.ones(n, bool)
        for _ in range(steps):
            ix = px.astype(int); iy = py.astype(int); fx = px - ix; fy = py - iy
            h00 = h[iy, ix]; h10 = h[iy, ix + 1]; h01 = h[iy + 1, ix]; h11 = h[iy + 1, ix + 1]
            gx = (h10 - h00) * (1 - fy) + (h11 - h01) * fy; gy = (h01 - h00) * (1 - fx) + (h11 - h10) * fx
            hc = h00 * (1 - fx) * (1 - fy) + h10 * fx * (1 - fy) + h01 * (1 - fx) * fy + h11 * fx * fy
            dxv = dxv * inertia - gx * (1 - inertia); dyv = dyv * inertia - gy * (1 - inertia)
            ln = np.hypot(dxv, dyv) + 1e-9; dxv /= ln; dyv /= ln
            nx = px + dxv; ny = py + dyv
            alive &= (nx > 1) & (nx < N - 2) & (ny > 1) & (ny < N - 2)
            nx = np.clip(nx, 1, N - 2.01); ny = np.clip(ny, 1, N - 2.01)
            jx = nx.astype(int); jy = ny.astype(int); gx2 = nx - jx; gy2 = ny - jy
            hn = (h[jy, jx] * (1 - gx2) * (1 - gy2) + h[jy, jx + 1] * gx2 * (1 - gy2) + h[jy + 1, jx] * (1 - gx2) * gy2 + h[jy + 1, jx + 1] * gx2 * gy2)
            dh = hn - hc
            cap = np.maximum(-dh, min_slope) * vel * water * cap_k
            dep = np.where((sed > cap) | (dh > 0), np.where(dh > 0, np.minimum(dh, sed), (sed - cap) * dep_k), 0)
            ero = np.where((sed <= cap) & (dh <= 0), np.minimum((cap - sed) * ero_k, -dh), 0)
            change = np.clip(dep - ero, -0.25, 0.25) * alive
            sed = sed - change
            # spread the change bilinearly onto the 4 corners
            for (oy, ox, w) in ((0, 0, (1 - fx) * (1 - fy)), (0, 1, fx * (1 - fy)), (1, 0, (1 - fx) * fy), (1, 1, fx * fy)):
                np.add.at(h, (iy + oy, ix + ox), change * w)
            vel = np.clip(np.sqrt(np.maximum(vel * vel - dh * g, 0.01)), 0, 8); water *= (1 - evap)
            px, py = nx, ny
            if not alive.any(): break
    return h

def shift(a, dy, dx, fill0=False):
    """Shift without wrap-around (np.roll wrapped the west ridge onto the east edge)."""
    p = max(abs(dy), abs(dx)); b = np.pad(a, p, mode='constant' if fill0 else 'edge')
    return b[p - dy:p - dy + a.shape[0], p - dx:p - dx + a.shape[1]]

def thermal(h, talus_deg, iters, k=0.25):
    """Material slumps where slope exceeds the talus angle (scree, moraine)."""
    t = math.tan(math.radians(talus_deg))
    for _ in range(iters):
        for sy, sx in ((0, 1), (1, 0), (1, 1), (1, -1)):
            dist = math.hypot(sy, sx)
            nb = shift(h, -sy, -sx)
            diff = h - nb; ex = np.clip(np.abs(diff) - t * dist, 0, None) * np.sign(diff) * k * 0.5
            h = h - ex; h = h + shift(ex, sy, sx, fill0=True)
    return h

drops = 120_000 if FAST else 450_000
log('hydraulic erosion', drops, 'droplets')
h = hydraulic(h, drops, 60, 20_000)
log('thermal erosion')
h = thermal(h, 38, 25 if FAST else 60)
h = (0.75 * h + 0.25 * smooth(h, 1)).astype(np.float32)      # kill single-pixel spikes

# ---------------------------------------------------------------- 3. carve the authored features into the eroded land
log('rivers, lake, plateau, roads')
rd, rt = poly_dist(RIVER, warp=26.0)
river_bed = 26.0 - 20.0 * rt                                            # river falls from the gorge to the lake
river_bed = np.where((rt * 1.0) < 0.17, river_bed + 34.0 * np.clip((0.17 - rt) / 0.17, 0, 1), river_bed)   # above the falls
river_bed = np.maximum(river_bed, smooth(h, 25) - 18.0)               # gorge at most ~18 m deep
river_w = 7.0 + 9.0 * rt                                                # 7 m in the gorge, 16 m near the lake
bank = np.clip((rd - river_w) / 22.0, 0, 1) ** 1.5
h = np.where(rd < river_w + 22, np.minimum(h, river_bed + bank * (h - river_bed)), h)
# the falls: a 14 m rock step just below FALLS
fd = np.hypot(xx - FALLS[0], yy - FALLS[1])
step = np.clip((yy - FALLS[1]) / 6.0, 0, 1) * np.exp(-(fd / 60.0) ** 2)
h -= 14.0 * step * (rd < 60)
# lake: flat ice with a shallow shelf at the edge
lx, ly, la, lb, lr = LAKE
c, s = math.cos(lr), math.sin(lr)
ux = ((xx - lx) * c + (yy - ly) * s) / la; uy = (-(xx - lx) * s + (yy - ly) * c) / lb
lake_r = np.sqrt(ux ** 2 + uy ** 2) + 0.06 * vnoise(60, 3, 0.5, 7)
lake_mask = np.clip((1.0 - lake_r) / 0.05, 0, 1)
shore = LAKE_ICE - 0.4 + np.clip(lake_r - 1.0, 0, None) ** 2.0 * 120
h = np.where(lake_r < 1.7, np.minimum(h, shore) * (1 - np.clip((lake_r - 1.45) / 0.25, 0, 1)) + h * np.clip((lake_r - 1.45) / 0.25, 0, 1), h)
h = h * (1 - lake_mask) + (LAKE_ICE - 0.35) * lake_mask                 # landscape sits 35 cm under the ice mesh
# castle plateau (castle box 46 x 34.5 m + yard): flat with a 5 m soft edge
pd = np.maximum(np.abs(xx - CASTLE[0]) / 48.0, np.abs(yy - CASTLE[1]) / 42.0)
pk = np.clip((pd - 1.0) * 8, 0, 1)
h = np.where(pd < 1.15, CASTLE_TOP * (1 - pk) + np.maximum(h, CASTLE_TOP - 3) * pk, h)

def grade_road(h, pts, width, maxgrade, deep):
    """Cut / fill a road along a polyline: a smooth longitudinal profile, a crowned cross-section, soft verges."""
    d, t = poly_dist(pts)
    pts_a = np.array(pts, np.float32)
    seg = np.linalg.norm(pts_a[1:] - pts_a[:-1], axis=1); L = float(seg.sum())
    nS = int(L) + 1; sx = np.interp(np.linspace(0, L, nS), np.concatenate([[0], np.cumsum(seg)]), pts_a[:, 0])
    sy = np.interp(np.linspace(0, L, nS), np.concatenate([[0], np.cumsum(seg)]), pts_a[:, 1])
    iy_, ix_ = np.clip(sy.astype(int), 0, N - 1), np.clip(sx.astype(int), 0, N - 1)
    terr = smooth(h, 4)[iy_, ix_].astype(np.float64)
    span = rd[iy_, ix_] < river_w[iy_, ix_] + 20                     # bridge span over the carved banks: deck mesh, not fill
    idx = np.arange(nS); prof = terr.copy()
    if span.any() and (~span).any():                                 # level deck at the mean of the two abutments
        i0, i1 = idx[span].min(), idx[span].max()
        ends = [terr[j] for j in (i0 - 1, i1 + 1) if 0 <= j < nS]
        prof[span] = float(np.mean(ends))
    r = 10; k = np.ones(2 * r + 1) / (2 * r + 1)
    for _ in range(2): prof = np.convolve(np.pad(prof, r, mode='edge'), k, 'valid')
    fw = prof.copy(); bw = prof.copy()                               # grade limit both ways, then average (no drag)
    for i in range(1, nS): fw[i] = np.clip(fw[i], fw[i - 1] - maxgrade, fw[i - 1] + maxgrade)
    for i in range(nS - 2, -1, -1): bw[i] = np.clip(bw[i], bw[i + 1] - maxgrade, bw[i + 1] + maxgrade)
    prof = 0.5 * (fw + bw)
    near_br = np.exp(-(np.hypot(sx - BRIDGE[0], sy - BRIDGE[1]) / 60.0) ** 2)  # a short stone causeway is allowed at the bridge only
    prof = np.where(span, prof, np.clip(prof, terr - 8.0, terr + 2.5 + 5.0 * near_br))   # cut <= 8 m (hollow way into the rock), fill <= 2.5 m: no embankments
    road_h = np.interp(t * L, np.arange(nS), prof).astype(np.float32) - deep * np.clip(1 - d / width, 0, 1) ** 2 * 0.0
    crown = -0.12 * (d / width) ** 2
    w = np.clip((d - width) / 9.0, 0, 1); w = w * w * (3 - 2 * w)
    return np.where(d < width + 9, (road_h + crown) * (1 - w) + h * w, h), d, t, sx, sy, prof

h, road_d, road_t, road_sx, road_sy, road_prof = grade_road(h, ROAD, 3.5, 0.11, 0)
h, mine_d2, _, mine_sx, mine_sy, mine_prof = grade_road(h, MINE_ROAD, 2.6, 0.13, 0)
# the bridge: road deck is a mesh; keep the riverbed under it, abutments on both banks
h = np.where((rd < river_w + 1) & (road_d < 6), np.minimum(h, river_bed + 0.3), h)
# farms: small flat yards
for (fx_, fy_) in FARMS.values():
    fdist = np.hypot(xx - fx_, yy - fy_); fk = np.clip((fdist - 18) / 30, 0, 1); fk = fk * fk * (3 - 2 * fk)
    base = float(np.median(h[int(fy_) - 5:int(fy_) + 5, int(fx_) - 5:int(fx_) + 5]))
    h = np.where(fdist < 48, (base + 0.15 * (h - base)) * (1 - fk) + h * fk, h)

# ---------------------------------------------------------------- 4. wind: exposure + Winstral Sx shelter -> snow depth
log('wind shelter (Winstral Sx) and snow depth')
ground = h.copy()
def sx_index(hh, dmax=220, n=22):
    """Max upwind horizon angle (deg). > 0 = sheltered (deposition), < 0 = exposed (scour). Winstral et al. 2002."""
    best = np.full((N, N), -90.0, np.float32)
    for k in range(1, n + 1):
        dist = dmax * k / n; o = int(round(dist / math.sqrt(2)))
        up = shift(hh, o, o)                                         # the cell upwind (NW) at this distance
        best = np.maximum(best, np.degrees(np.arctan((up - hh) / (o * math.sqrt(2)))))
    return best
Sx = sx_index(smooth(ground, 3))
Sx_far = sx_index(smooth(ground, 8), 900, 18)
gx, gy = grad(ground)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
# facing: >0 when the slope faces into the wind (windward, NW-facing)
facing = -(gx * -WIND[0] + gy * -WIND[1]) / (np.hypot(gx, gy) + 1e-4) * np.clip(np.hypot(gx, gy) * 4, 0, 1)
tpi = ground - smooth(ground, 40)                                    # topographic position: ridges > 0, hollows < 0
exposure = np.clip(0.5 - Sx / 18.0 + 0.35 * facing + tpi / 30.0 - Sx_far / 30.0, 0, 1).astype(np.float32)
shelter = np.clip(Sx / 14.0 + 0.2 * np.clip(-tpi / 10, -1, 1), 0, 1).astype(np.float32)
base_snow = 0.65                                                    # metres of settled snow on open flat ground
snow = base_snow * (1 - 0.95 * exposure) + 2.4 * shelter * (1 - exposure)   # drifts up to ~3 m on lee sides
snow *= np.clip((48 - slope) / 18.0, 0, 1)                         # snow slides off slopes > ~45 deg
snow = smooth(snow, 2) * (1 - lake_mask)                           # wind-smoothed surface; lake ice has its own thin layer
snow = np.where(road_d < 4.5, np.minimum(snow, 0.12), snow)        # packed road: thin compacted layer
snow = np.where(mine_d2 < 3.4, np.minimum(snow, 0.18), snow)
snow = np.where(rd < river_w, snow * 0.15, snow)                   # river ice: thin wind-scoured snow
snow = np.where(pd < 1.0, np.minimum(snow, 0.25), snow)            # castle yard: cleared
realm_d = np.hypot(xx - REALM[0], yy - REALM[1])
melt = np.clip(1 - (realm_d - REALM[2] * 0.55) / (REALM[2] * 0.45), 0, 1).astype(np.float32)
melt = np.clip(melt + 0.25 * vnoise(18, 3, 0.5, 11) * (melt > 0.05) * (melt < 0.95), 0, 1)
snow *= (1 - melt)                                                 # the realm melts everything: wet black ground
h = (ground + snow).astype(np.float32)

# ---------------------------------------------------------------- 5. weight layers (sum to 255) + dressing masks
log('weight layers')
gx, gy = grad(smooth(h, 1)); slope_s = np.degrees(np.arctan(np.hypot(gx, gy)))
curv = smooth(h, 2) - smooth(h, 6)                                 # > 0 convex edges, < 0 hollows
n1 = vnoise(55, 4, 0.55, 21) * 0.5 + 0.5; n2 = vnoise(14, 3, 0.5, 22) * 0.5 + 0.5
forest = np.clip((ground - 22) / 8, 0, 1) * np.clip((260 - ground) / 40, 0, 1) * np.clip((33 - slope) / 8, 0, 1)
forest *= np.clip((n1 - 0.38) / 0.12, 0, 1) * np.clip(1 - exposure * 1.3, 0, 1)
for dd, wdt in ((road_d, 14), (mine_d2, 10), (rd, 26), (realm_d - REALM[2], 60)):
    forest *= np.clip((dd - wdt) / 10, 0, 1)
forest *= np.clip((pd - 2.2) / 0.6, 0, 1) * (1 - lake_mask) * np.clip((lake_r - 1.12) / 0.1, 0, 1)
for (fx_, fy_) in FARMS.values(): forest *= np.clip((np.hypot(xx - fx_, yy - fy_) - 70) / 20, 0, 1)
birch = np.clip(1 - np.abs(forest - 0.25) / 0.25, 0, 1) * (n2 > 0.45) + np.clip(1 - (rd - 18) / 25, 0, 1) * (rd > 14) * (n2 > 0.55) * (1 - exposure)
W = {}
W['Rock_Scoured'] = np.clip((slope_s - 34) / 10, 0, 1) + np.clip((exposure - 0.84) / 0.12, 0, 1) * np.clip((slope_s - 18) / 10, 0, 1) * (n2 > 0.4) + np.clip(curv * 1.5, 0, 1) * np.clip((slope_s - 22) / 10, 0, 1)
W['Rock_Scoured'] = np.clip(W['Rock_Scoured'] + cliff * 0.8, 0, 1) * (1 - melt)
W['Ice'] = np.maximum(lake_mask, (rd < river_w).astype(np.float32) * np.clip(1 - rd / river_w, 0.6, 1))
W['Ice'] = np.maximum(W['Ice'], np.exp(-(fd / 22.0) ** 2) * (slope_s > 30))                    # frozen waterfall face
W['Road'] = np.clip(1 - (road_d - 2.6) / 1.8, 0, 1) + np.clip(1 - (mine_d2 - 2.0) / 1.4, 0, 1) * 0.9
W['FrozenMud'] = np.clip(1 - np.abs(road_d - 3.8) / 1.6, 0, 1) * np.clip(n2 * 1.4, 0, 1) + np.clip(1 - (np.hypot(xx - GATE[0], yy - GATE[1]) - 18) / 16, 0, 1) * 0.7
for (fx_, fy_) in FARMS.values(): W['FrozenMud'] = np.maximum(W['FrozenMud'], np.clip(1 - (np.hypot(xx - fx_, yy - fy_) - 10) / 14, 0, 1) * n2)
W['RealmMelt'] = melt
W['ForestFloor'] = np.clip(forest * 1.2 - 0.2, 0, 1) * 0.8
W['Snow_Packed'] = (np.clip(exposure * 1.2 - 0.3, 0, 1) * 0.7 + np.clip(1 - (road_d - 4.5) / 6, 0, 1) * 0.6 + np.clip(1 - (pd - 1.0) / 0.4, 0, 1) * 0.8)
W['Snow_Fresh'] = np.ones((N, N), np.float32) * 0.35 + shelter * 0.65
ORDER = ['Snow_Fresh', 'Snow_Packed', 'Rock_Scoured', 'Ice', 'FrozenMud', 'ForestFloor', 'Road', 'RealmMelt']
# priority: higher layers eat the ones below (road over mud over snow), then normalise to 255
rem = np.ones((N, N), np.float32); final = {}
for k in ['RealmMelt', 'Ice', 'Road', 'Rock_Scoured', 'FrozenMud', 'ForestFloor', 'Snow_Packed']:
    v = np.clip(W[k], 0, 1) * rem; final[k] = v; rem = rem - v
final['Snow_Fresh'] = rem
total = sum(final.values()) + 1e-6
q = {k: np.round(final[k] / total * 255).astype(np.int32) for k in ORDER}
q['Snow_Fresh'] += 255 - sum(q.values())                           # exact sum 255 per pixel
masks = {'Forest': forest, 'Birch': np.clip(birch, 0, 1), 'Drift': np.clip(snow / 3.0, 0, 1), 'WindExposure': exposure,
         'Shelter': shelter, 'SnowDepth': np.clip(snow / 3.0, 0, 1), 'Rocks': np.clip((slope_s - 28) / 12, 0, 1) * (1 - lake_mask)}

# ---------------------------------------------------------------- 6. write files
def png(path, arr, bits):
    hgt, wid = arr.shape
    if bits == 16: raw = b''.join(b'\x00' + arr[y].astype('>u2').tobytes() for y in range(hgt)); ct = 0
    else: raw = b''.join(b'\x00' + arr[y].astype(np.uint8).tobytes() for y in range(hgt)) if arr.ndim == 2 else None; ct = 0
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', wid, hgt, bits, ct, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
def png_rgb(path, rgb):
    hgt, wid, _ = rgb.shape; raw = b''.join(b'\x00' + rgb[y].astype(np.uint8).tobytes() for y in range(hgt))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', wid, hgt, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))

log('writing files')
grey = np.clip(np.round(32768 + (h - Z_CENTRE_M) * 100 * 128 / Z_SCALE), 0, 65535).astype(np.uint16)
clip_lo, clip_hi = int((grey == 0).sum()), int((grey == 65535).sum())
png(os.path.join(OUT, 'WinterKeep_Height_2017.png'), grey, 16)
grey.astype('<u2').tofile(os.path.join(OUT, 'WinterKeep_Height_2017.r16'))
np.save(os.path.join(OUT, 'height_m.npy'), h); np.save(os.path.join(OUT, 'ground_m.npy'), ground)
for k in ORDER: png(os.path.join(OUT, 'WL_%s.png' % k), q[k], 8)
for k, v in masks.items(): png(os.path.join(OUT, 'M_%s.png' % k), np.round(np.clip(v, 0, 1) * 255), 8)
np.savez_compressed(os.path.join(OUT, 'layers.npz'), **{k: q[k].astype(np.uint8) for k in ORDER}, **{'M_' + k: (np.clip(v, 0, 1) * 255).astype(np.uint8) for k, v in masks.items()})

def ue(p, z=None):
    """image metres -> UE world cm (origin = map centre)."""
    x, y = p[0], p[1]
    if z is None: z = float(h[int(np.clip(y, 0, N - 1)), int(np.clip(x, 0, N - 1))])
    return [round((x - HALF) * 100, 1), round((y - HALF) * 100, 1), round(z * 100, 1)]
def spline(sx, sy, prof, every):
    return [ue((float(sx[i]), float(sy[i])), float(prof[i]) + 0.05) for i in range(0, len(sx), every)] + [ue((float(sx[-1]), float(sy[-1])), float(prof[-1]) + 0.05)]
river_pts = [ue(p, float(np.interp(i / (len(RIVER) - 1), [0, 1], [0, 1])) * 0 + float(ground[int(np.clip(p[1], 0, N - 1)), int(np.clip(p[0], 0, N - 1))]) + 0.3) for i, p in enumerate(RIVER)]
layout = {
    'card': 390, 'seed': SEED, 'size_vertices': N, 'metres_per_vertex': 1.0,
    'import': {'location_cm': [-(N - 1) / 2 * 100, -(N - 1) / 2 * 100, Z_CENTRE_M * 100], 'scale': [100, 100, Z_SCALE],
               'section_size_quads': 63, 'sections_per_component': '2x2', 'components': '16x16',
               'note': 'world Z (m) = grey -> exact metres with these numbers. Clipped pixels: %d low, %d high' % (clip_lo, clip_hi)},
    'height_range_m': [float(h.min()), float(h.max())],
    'lake_ice_z_cm': LAKE_ICE * 100, 'lake': {'centre': ue(LAKE[:2], LAKE_ICE), 'semi_axes_m': [LAKE[2], LAKE[3]], 'yaw_deg': math.degrees(LAKE[4])},
    'castle_centre': ue(CASTLE, CASTLE_TOP), 'castle_plateau_m': [96, 84], 'gate': ue(GATE, CASTLE_TOP),
    'bridge': ue(BRIDGE, float(road_prof[np.argmin(np.hypot(road_sx - BRIDGE[0], road_sy - BRIDGE[1]))])),
    'mine_portal': ue(MINE), 'frozen_falls': ue(FALLS), 'avalanche_gully': [ue(p) for p in AVALANCHE],
    'farms': {k: ue(v) for k, v in FARMS.items()}, 'realm_melt': {'centre': ue(REALM[:2]), 'radius_m': REALM[2]},
    'first_view': {'from': ue(FIRST_VIEW['from'][:2], FIRST_VIEW['from'][2]), 'look_at': ue(FIRST_VIEW['look_at'][:2], FIRST_VIEW['look_at'][2])},
    'road_spline_cm': spline(road_sx, road_sy, road_prof, 25), 'mine_road_spline_cm': spline(mine_sx, mine_sy, mine_prof, 25),
    'river_spline_cm': river_pts, 'river_width_m': [7, 16],
    'wind_from_deg': 315, 'layers': ORDER,
    'zombie_routes': {'east_from_realm': [ue(REALM[:2]), ue((1420, 1000)), ue((1200, 980)), ue(GATE, CASTLE_TOP)],
                      'north_river_ice': [ue((1240, 360)), ue((1180, 640)), ue((1150, 860)), ue(GATE, CASTLE_TOP)],
                      'lake_ice': [ue((420, 1640)), ue((620, 1520)), ue((830, 1300)), ue((1030, 1160)), ue(BRIDGE)],
                      'road_south_east': [ue(ROAD[1]), ue(ROAD[4]), ue(BRIDGE), ue(GATE, CASTLE_TOP)]},
}
with open(os.path.join(OUT, 'layout.json'), 'w') as f: json.dump(layout, f, indent=1)

# previews: hillshade + layer colours (1008 px)
log('previews')
s = 2; hs_h = h[::s, ::s]; gx, gy = np.gradient(hs_h, s)
L = np.array([-0.6, -0.6, 0.55]); L /= np.linalg.norm(L)
nrm = np.dstack([-gx, -gy, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
shade = np.clip(nrm @ L, 0, 1)
COL = {'Snow_Fresh': (232, 236, 242), 'Snow_Packed': (205, 211, 220), 'Rock_Scoured': (70, 72, 76), 'Ice': (60, 86, 104),
       'FrozenMud': (98, 86, 74), 'ForestFloor': (150, 160, 165), 'Road': (150, 140, 126), 'RealmMelt': (22, 20, 22)}
alb = sum(q[k][::s, ::s, None] / 255.0 * np.array(COL[k], np.float32) for k in ORDER)
fo = masks['Forest'][::s, ::s, None]; alb = alb * (1 - 0.65 * fo) + np.array([38, 52, 46]) * 0.65 * fo
img = alb * (0.35 + 0.75 * shade[..., None])
png_rgb(os.path.join(OUT, 'preview_map.png'), np.clip(img, 0, 255))
png_rgb(os.path.join(OUT, 'preview_hillshade.png'), np.clip(np.repeat(shade[..., None] * 255, 3, 2), 0, 255))
log('done. height %.1f .. %.1f m, clipped %d/%d' % (h.min(), h.max(), clip_lo, clip_hi))

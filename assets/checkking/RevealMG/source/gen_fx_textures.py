# HUD effect textures for the motion graphics cards (checkking 2026-10-30), procedural (numpy), no external assets.
#   blender -b --factory-startup -P gen_fx_textures.py -- <out_dir>
# T_FX_RevealRays.png    1024^2  gold light rays + a soft core, drawn additive behind the spinning book / bag (achievement burst)
# T_FX_Sparkles.png      1024^2  scattered star sparkles, drawn additive and rotated against the rays
# T_FX_ToxinVignette.png 2048x1024  green toxic clouds at the screen edges, clear centre (#141)
# T_FX_ToxinVeins.png    1024x256   branching toxin veins spreading out from a horizontal centre line (#141, around the bar)
# All white/green on transparent: the HUD tints and fades them with DrawTexture's TintColor.
import bpy, os, sys, math
import numpy as np

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.getcwd()
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

def save(rgba, name):
    h, w = rgba.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(np.flipud(np.clip(rgba, 0, 1)).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(OUT, name); img.file_format = 'PNG'; img.save()
    print('wrote', name, w, h)

def fbm(h, w, octaves=6, base=4, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((h, w)); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o + 1, int(base * 2 ** o * w / h) + 1
        g = r.random((gh, gw))
        yi = np.linspace(0, gh - 1, h); xi = np.linspace(0, gw - 1, w)
        y0 = np.floor(yi).astype(int).clip(0, gh - 2); x0 = np.floor(xi).astype(int).clip(0, gw - 2)
        fy = (yi - y0)[:, None]; fx = (xi - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        acc += amp * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy); tot += amp; amp *= 0.5
    return acc / tot

# ---- rays: 28 rays of varying width/length, soft core, radial falloff
N = 1024; y, x = np.mgrid[0:N, 0:N]; cx = cy = (N - 1) / 2
dx, dy = (x - cx) / cx, (y - cy) / cy; r = np.sqrt(dx * dx + dy * dy); th = np.arctan2(dy, dx)
rays = np.zeros((N, N))
for k in range(28):
    a0 = rng.uniform(-np.pi, np.pi); wdt = rng.uniform(0.012, 0.05); ln = rng.uniform(0.55, 1.0)
    d = np.angle(np.exp(1j * (th - a0)))
    rays += np.exp(-(d / wdt) ** 2) * np.clip(1 - r / ln, 0, 1) ** 1.6 * rng.uniform(0.4, 1.0)
core = np.exp(-(r / 0.22) ** 2)
v = np.clip(rays * 0.8 + core * 1.1, 0, 1) * np.clip(1 - r, 0, 1) ** 0.5
save(np.dstack([np.ones_like(v), np.ones_like(v), np.ones_like(v), v]), 'T_FX_RevealRays.png')

# ---- sparkles: four-point stars with a soft halo
sp = np.zeros((N, N))
for k in range(70):
    px, py = rng.uniform(0.08, 0.92, 2) * N; s = rng.uniform(3, 11); b = rng.uniform(0.35, 1.0)
    ddx, ddy = np.abs(x - px), np.abs(y - py)
    star = np.exp(-ddx / s * 0.9) * np.exp(-(ddy / (s * 0.12)) ** 2) + np.exp(-ddy / s * 0.9) * np.exp(-(ddx / (s * 0.12)) ** 2)
    sp += b * (star + 0.6 * np.exp(-((ddx ** 2 + ddy ** 2) / (s * 0.6) ** 2)))
sp = np.clip(sp, 0, 1) * np.clip(1.15 - r, 0, 1)
save(np.dstack([np.ones_like(sp), np.ones_like(sp), np.ones_like(sp), sp]), 'T_FX_Sparkles.png')

# ---- toxin vignette: fBm clouds masked to the edges (screen aspect 2:1 texture, stretched to the screen)
H, W = 1024, 2048; yy, xx = np.mgrid[0:H, 0:W]
u, v = (xx / (W - 1)) * 2 - 1, (yy / (H - 1)) * 2 - 1
d = (np.abs(u) ** 4 + np.abs(v) ** 4) ** 0.25                            # rounded-rectangle distance: no corner seams
cloud = fbm(H, W, 6, 3, 11); cloud2 = fbm(H, W, 5, 6, 12)
d = d + 0.22 * (cloud - 0.5)                                              # cloudy, uneven inner border
t = np.clip((d - 0.62) / (1.02 - 0.62), 0, 1); edge = t * t * (3 - 2 * t)
m = np.clip(edge * (0.55 + 0.6 * cloud2), 0, 0.85)
g = np.dstack([0.22 + 0.18 * cloud2, 0.55 + 0.25 * cloud, 0.12 + 0.1 * cloud2])   # murky toxic green, not neon
save(np.dstack([g, m]), 'T_FX_ToxinVignette.png')

# ---- toxin veins: random-walk branches from the centre line outward (up and down), thick at the root
VH, VW = 256, 1024; veins = np.zeros((VH, VW))
def walk(x0, y0, ang, life, width):
    px, py = x0, y0
    for i in range(life):
        ang += rng.normal(0, 0.18); px += math.cos(ang) * 2.0; py += math.sin(ang) * 2.0
        if not (0 <= px < VW and 0 <= py < VH): return
        w = width * (1 - i / life) + 0.6
        x0i, x1i = int(max(px - w - 2, 0)), int(min(px + w + 3, VW)); y0i, y1i = int(max(py - w - 2, 0)), int(min(py + w + 3, VH))
        sy, sx = np.mgrid[y0i:y1i, x0i:x1i]
        veins[y0i:y1i, x0i:x1i] = np.maximum(veins[y0i:y1i, x0i:x1i], np.clip(1 - np.hypot(sx - px, sy - py) / w, 0, 1))
        if rng.random() < 0.035 and life - i > 20: walk(px, py, ang + rng.choice([-0.7, 0.7]), int((life - i) * 0.6), w * 0.7)
for k in range(46):
    side = -1 if k % 2 else 1
    walk(rng.uniform(30, VW - 30), VH / 2 + side * rng.uniform(4, 14), side * np.pi / 2 + rng.normal(0, 0.5), int(rng.uniform(40, 110)), rng.uniform(2.0, 4.5))
glow = np.clip(veins * 1.2, 0, 1)
vc = np.dstack([0.45 + 0.4 * glow, 0.95 * np.ones_like(glow), 0.3 + 0.2 * glow])
save(np.dstack([vc, glow]), 'T_FX_ToxinVeins.png')

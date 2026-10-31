# Torn cape (#256, checkking 2026-10-31): packed wear masks for the hero cape, procedural (numpy), no external assets.
#   blender -b --factory-startup -P gen_cape_masks.py -- <out_dir>
# T_CapeWear_Masks.png (2048^2, linear, UV v = 0 at the hem, 1 at the shoulders, as on a standard cape unwrap):
#   R  tear threshold: a pixel is cut away when CapeWear > R. Low near the hem and in a few slash lines, so holes grow from
#      the hem up and along cuts (4 readable stages at CapeWear 0.25 / 0.5 / 0.75 / 1.0). Never below 0.12 above the
#      shoulder band (the cape never falls off).
#   G  dirt / mud amount: from the hem up, splashy (multiplies BaseColor darker + rougher)
#   B  blood threshold: drops appear when CapeWear > B (sprays + drips, darker red-brown, wet-gloss)
#   A  fray: thin noisy band around every tear edge (a darker, thinner, ragged threshold ring)
# Also preview_stages.png: a cloth-red cape tinted with the masks at wear 0, 0.25, 0.5, 0.75, 1.0.
import bpy, os, sys, math
import numpy as np

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else os.getcwd()
os.makedirs(OUT, exist_ok=True)
N = 2048; rng = np.random.default_rng(256)
v, u = np.mgrid[0:N, 0:N] / (N - 1)            # v: 0 hem .. 1 shoulders (row 0 = hem in this array)

def fbm(oct=6, base=4, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((N, N)); amp = 1.0; tot = 0.0
    for o in range(oct):
        g = base * 2 ** o + 1; grid = r.random((g, g))
        x = np.linspace(0, g - 1, N); i0 = np.floor(x).astype(int).clip(0, g - 2); f = x - i0; f = f * f * (3 - 2 * f)
        a = grid[i0][:, i0]; b = grid[i0][:, i0 + 1]; c = grid[i0 + 1][:, i0]; d = grid[i0 + 1][:, i0 + 1]
        fy, fx = f[:, None], f[None, :]
        acc += amp * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy); tot += amp; amp *= 0.5
    return acc / tot

n1, n2, n3 = fbm(6, 3, 1), fbm(5, 8, 2), fbm(4, 20, 3)
# ---- R: tear threshold. Base = height from the hem with ragged noise; slash lines cut lower values; shoulder band safe.
strips = (0.5 + 0.5 * np.sin(u * 2 * math.pi * (11 + 6 * n2) + 14 * (n1 - 0.5))) * (0.4 + 1.2 * n3)   # uneven tatters            # vertical tatter strips along the hem
tear = 0.30 + 1.25 * v + 0.30 * (n1 - 0.5) + 0.10 * (n3 - 0.5) - 0.22 * strips * np.clip(1 - v * 2.2, 0, 1)
for k in range(9):                               # scattered holes higher up (arrow / blade punctures that grow)
    cx, cy, rad = rng.uniform(0.12, 0.88), rng.uniform(0.3, 0.75), rng.uniform(0.012, 0.035)
    dd = np.hypot(u - cx, (v - cy) * 1.4) / rad + 2.2 * (n3 - 0.5) + 1.2 * (n2 - 0.5)
    tear = np.minimum(tear, rng.uniform(0.45, 0.95) + 0.25 * np.clip(dd - 1, 0, 9) + 9 * (dd > 3))
for k in range(5):                               # diagonal sword slashes
    a = rng.uniform(-0.9, 0.9); c = rng.uniform(0.15, 0.85); h = rng.uniform(0.15, 0.7)
    d = np.abs((u - c) * math.cos(a) - (v - h) * math.sin(a)); along = np.abs((u - c) * math.sin(a) + (v - h) * math.cos(a))
    cut = np.exp(-(d / 0.006) ** 2) * (along < rng.uniform(0.06, 0.16))
    tear = np.minimum(tear, 1.0 - 0.75 * cut + 0.2 * (n2 - 0.5) * cut + 10 * (1 - cut))
tear = np.where(v > 0.86, np.maximum(tear, 1.12), tear)      # shoulder band never tears
R = np.clip(tear, 0, 1)
# ---- G: dirt from the hem up, splashy
G = np.clip((0.55 - v) * 1.8 + 0.6 * (n2 - 0.5) + 0.3 * (n3 - 0.4), 0, 1) ** 1.3
# ---- B: blood threshold (sprays + drips downward)
bl = np.ones((N, N))
for k in range(70):
    cx, cy, rad, th = rng.uniform(0.05, 0.95), rng.uniform(0.1, 0.8), rng.uniform(0.003, 0.016), rng.uniform(0.15, 0.95)
    blob = np.hypot(u - cx, (v - cy) * 1.2) / rad + 1.2 * (n2 - 0.5)
    drip = (np.abs(u - cx) < rad * 0.08) * (v < cy) * (v > cy - rng.uniform(0.0, 0.05)) * (rng.random() < 0.35)
    m = np.clip(1 - blob + 0.4 * (n3 - 0.5), 0, 1) + drip
    bl = np.where(m > 0.15, np.minimum(bl, th), bl)
B = bl
# ---- A: fray ring: a pixel is fray where its tear threshold is just above the current wear (material does the compare);
#      here we store a noisy width so frays are ragged and thin
A = np.clip(0.02 + 0.05 * n3 + 0.03 * n2, 0, 1)

def save(arr, name, srgb=False):
    h, w = arr.shape[:2]; img = bpy.data.images.new(name, w, h, alpha=arr.shape[2] == 4)
    if not srgb: img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel()); img.filepath_raw = os.path.join(OUT, name); img.file_format = 'PNG'; img.save()
save(np.dstack([R, G, B, A]), 'T_CapeWear_Masks.png')

# ---- preview: the mask logic as the material will do it, on a cloth-red cape (sRGB ~110/22/20)
base = np.array([0.155, 0.008, 0.007]); dirt = np.array([0.06, 0.045, 0.03]); blood = np.array([0.03, 0.002, 0.001])
tiles = []
for w in (0.0, 0.25, 0.5, 0.75, 1.0):
    col = np.broadcast_to(base, (N, N, 3)).copy()
    col = col * (1 - 0.7 * (G * w)[..., None]) + dirt * (0.7 * G * w)[..., None]
    bm = (w > B)[..., None]; col = np.where(bm, blood, col)
    cut = w > R; fray = (~cut) & (w + A > R)
    col = np.where(fray[..., None], col * 0.55, col)
    rgb = np.where(cut[..., None], np.array([0.05, 0.05, 0.05]), col)
    tiles.append(np.flipud(rgb[::4, ::4]))
strip = np.concatenate(tiles, axis=1)
srgbc = np.where(strip <= 0.0031308, strip * 12.92, 1.055 * np.power(np.clip(strip, 0, 1), 1 / 2.4) - 0.055)
save(np.dstack([np.flipud(srgbc), np.ones(strip.shape[:2])]), 'preview_stages.png', srgb=False)
print('CAPE MASKS DONE')

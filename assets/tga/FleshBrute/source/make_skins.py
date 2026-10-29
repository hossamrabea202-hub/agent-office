# Flesh Brute skin variants (TGA, 2026-10-29). Source: CGTrader "Flesh Mutant Monster" (andrey-ryzhko), Royalty Free
# licence: the textures stay private (owner's PC), never in the public repo.
#   blender -b -P make_skins.py -- <Monster_001_Textures dir> <out dir>
# Out, per part (01, 02) and skin: T_FleshBrute_<Skin>_P<n>_BC.png (sRGB), _ORM.png (R AO, G rough, B metal),
# plus the shared _N.png (DirectX). Skins: Clean + Bloody (the artist's 01 / 02), and three derived here:
#   Rotten  - grey-green necrotic: desaturated, olive shift, mottled dark patches, cavities rot black, a bit wetter
#   Charred - burnt: convex skin turns black char, cracks/cavities stay raw red flesh, dry and rough
#   Drowned - pale blue-grey bloat: desaturated, cold, lighter, glossy wet
# Masks come from the textures themselves (AO, luminance, curvature from the normal map), so nothing breaks at UV seams.
import sys, os
import bpy, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = a[0], a[1]; os.makedirs(OUT, exist_ok=True)

def to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)
def load(path, srgb):
    """8-bit pixels come back as stored (sRGB-encoded); colour maps are converted to linear so the grading below is in
    linear light, like the shader."""
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
    w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im)
    px = px.reshape(h, w, 4)
    if srgb: px[..., :3] = to_lin(px[..., :3])
    return px
def save(arr, name, srgb):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False); im.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), np.float32); rgba[..., :3] = to_srgb(arr[..., :3]) if srgb else np.clip(arr[..., :3], 0, 1)
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'
    im.save(); bpy.data.images.remove(im)
def lum(c): return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722
def blur(x, r):
    """cheap box blur (separable, via cumulative sums), r in pixels."""
    for ax in (0, 1):
        c = np.cumsum(np.pad(x, [(r + 1, r) if i == ax else (0, 0) for i in range(x.ndim)], mode='edge'), axis=ax)
        x = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return x
def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def mix(a, b, t): return a + (b - a) * t[..., None]

for part in ('01', '02'):
    f = lambda skin, ch, ext='png': os.path.join(SRC, f'skin_{skin}', f'Monster_001_Skin_{skin}_part_{part}_{ch}_4K.{ext}')
    bc1 = load(f('01', 'BaseColor'), True)[..., :3]          # pixels come back linear for sRGB images
    bc2 = load(f('02', 'BaseColor'), True)[..., :3]
    ao = load(f('01', 'AO'), False)[..., 0]
    rg1 = load(f('01', 'Roughness'), False)[..., 0]; rg2 = load(f('02', 'Roughness'), False)[..., 0]
    nrm = load(f('01', 'Normal_DirectX'), False)[..., :3]
    # curvature from the normal map: divergence of the tangent-space xy (DirectX: green is flipped, so negate dy)
    nx, ny = nrm[..., 0] * 2 - 1, -(nrm[..., 1] * 2 - 1)
    curv = np.gradient(nx, axis=1) + np.gradient(ny, axis=0)
    curv = blur(curv, 2); curv = curv / (curv.std() + 1e-6)  # in std units: > 0 convex ridges, < 0 cracks / folds
    cav = np.clip(1 - ao, 0, 1)
    L = lum(bc1)
    # low-frequency mottling taken from the artist's own colour variation (seam-safe)
    mott = blur(L, 48); mott = (mott - mott.mean()) / (mott.std() + 1e-6)
    detail = (L - blur(L, 6)) / (L.std() + 1e-6)
    zero = np.zeros_like(ao)
    skins = {'Clean': (bc1, rg1), 'Bloody': (bc2, rg2)}

    # Rotten: desaturate 70 %, push to olive / grey-green, rot in the cavities, mottled necrosis
    g = L[..., None]
    rot = mix(bc1, g * np.array([0.85, 0.95, 0.62]), np.full_like(L, 0.7))
    rot = mix(rot, np.array([0.035, 0.040, 0.018]), ss(0.15, 0.6, cav) * 0.8)
    rot = mix(rot, np.array([0.10, 0.11, 0.05]), ss(0.4, 1.6, mott) * 0.45)
    rot = mix(rot, np.array([0.055, 0.025, 0.030]), ss(0.8, 2.0, -mott) * 0.35)     # bruised purple-brown patches
    rot = rot * (1 + 0.15 * np.clip(detail, -2, 2)[..., None])
    skins['Rotten'] = (rot, np.clip(rg1 * 0.85, 0.2, 1))

    # Charred: ridges burn to black char with ash grey on the highest points; cracks stay raw red, glossy
    ridge = ss(0.2, 1.4, curv); crack = ss(0.9, 2.2, -curv) * ss(0.1, 0.5, cav)    # burn cracks in the deeper folds
    burn = np.clip(0.88 + 0.12 * ss(-1.0, 1.0, mott), 0, 1)
    # char: near-black, with grey-white ash crusting the raised skin in patches
    ash = np.clip(ridge * 0.6 + ss(0.3, 1.6, detail) * 0.5, 0, 1) * ss(-0.6, 0.8, mott)
    char = mix(np.array([0.012, 0.010, 0.009]), np.array([0.20, 0.19, 0.18]), ash * 0.85)
    chd = mix(bc1 * np.array([0.35, 0.16, 0.10]), char, burn)
    raw = bc2 * np.array([1.25, 0.45, 0.32])                 # raw, glistening flesh in the burn cracks
    chd = mix(chd, raw, np.clip(crack * 1.2, 0, 0.95))
    skins['Charred'] = (chd, np.clip(mix(np.full_like(L, 0.88)[..., None], np.full_like(L, 0.38)[..., None], crack)[..., 0], 0, 1))

    # Drowned: pale, cold, waterlogged; veins and folds darker blue-purple, very wet
    pale = mix(bc1, (0.16 + 0.50 * g) * np.array([0.74, 0.80, 0.90]), np.full_like(L, 0.75))
    pale = mix(pale, np.array([0.10, 0.10, 0.17]), ss(0.2, 0.7, cav) * 0.6)
    pale = mix(pale, np.array([0.22, 0.20, 0.26]), ss(0.5, 1.8, -mott) * 0.35)
    skins['Drowned'] = (pale, np.clip(rg1 * 0.55, 0.12, 1))

    for name, (bc, rg) in skins.items():
        save(bc, f'T_FleshBrute_{name}_P{part}_BC', True)
        save(np.stack([ao, rg, zero], -1), f'T_FleshBrute_{name}_P{part}_ORM', False)
        print('SKIN', name, part, flush=True)
    save(nrm, f'T_FleshBrute_P{part}_N', False)
print('SKINS OK', flush=True)

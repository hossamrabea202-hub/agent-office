# Main gate polish (i5, 2026-11-02): new textures only, values per the office realism rules.
#   blender -b --factory-startup -P make_gate_tex.py -- <tex_dir> <out_dir>
# 1) T_GateOak_ORM_v2: roughness from the oak's own grain (dark grain/end-grain rougher, worn faces smoother), std >= 0.07
#    instead of the flat 0.73-0.80; AO kept; metallic 0.
# 2) T_GateIron_D_v2 + T_GateIron_ARM_v2: forged gate iron = blackened oxide (dielectric, ~55 sRGB, rough ~0.65) with
#    bare metal only where the steel texture is brightest / already metallic (worn edges, rivet heads): metallic 1,
#    ~190 sRGB, rough ~0.35. No in-between metallic except a thin transition. (KNOWLEDGE_LOG 10-30: dark metal = black plastic.)
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
TEX, OUT = a[0], a[1]
os.makedirs(OUT, exist_ok=True)


def load(name, linear=True):
    im = bpy.data.images.load(os.path.join(TEX, name + '.png'))
    im.colorspace_settings.name = 'Non-Color'
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)


def save(name, arr):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=True)
    im.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), np.float32); rgba[..., :arr.shape[2]] = arr
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = os.path.join(OUT, name + '.png'); im.file_format = 'PNG'; im.save()
    print('saved', name, w, h)


def blur(x, r):
    """box blur via cumulative sums (separable), wraps edges"""
    k = 2 * r + 1
    for ax in (0, 1):
        c = np.cumsum(np.concatenate([x.take(range(-r - 1, 0), ax), x, x.take(range(0, r), ax)], ax), ax)
        x = (c.take(range(k, c.shape[ax]), ax) - c.take(range(0, c.shape[ax] - k), ax)) / k
    return x


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


# ---- 1) oak roughness ----
bc = load('T_GateOak_BC'); orm = load('T_GateOak_ORM')
if orm.shape[:2] != bc.shape[:2]:
    raise SystemExit('size mismatch oak')
lum = srgb_to_lin(bc[..., :3]) @ np.array([0.2126, 0.7152, 0.0722])
lo_f = blur(lum, max(2, lum.shape[0] // 64))            # broad tone (weathered vs worn boards)
hp = lum - blur(lum, 3)                                 # grain detail
n_lo = (lo_f - np.percentile(lo_f, 5)) / max(np.percentile(lo_f, 95) - np.percentile(lo_f, 5), 1e-4)
n_hp = hp / max(np.percentile(np.abs(hp), 95), 1e-4)
rough = 0.86 - 0.16 * np.clip(n_lo, 0, 1) - 0.06 * np.clip(n_hp, -1.5, 1.5) + 0.25 * (orm[..., 1] - orm[..., 1].mean())
rough = np.clip(rough, 0.55, 0.96)
orm2 = np.stack([orm[..., 0], rough, np.zeros_like(rough)], -1)
save('T_GateOak_ORM_v2', orm2)
print('oak roughness p5/p50/p95/std %.2f/%.2f/%.2f/%.3f (was std %.3f)' % (np.percentile(rough, 5), np.median(rough), np.percentile(rough, 95), rough.std(), orm[..., 1].std()))

# ---- 2) forged iron ----
sd = load('T_Metal_Steel_D'); arm = load('T_GateIron_ARM')
if arm.shape[:2] != sd.shape[:2]:
    # resample the ARM to the steel size (nearest) so both maps share a UV grid
    yi = (np.arange(sd.shape[0]) * arm.shape[0] // sd.shape[0]); xi = (np.arange(sd.shape[1]) * arm.shape[1] // sd.shape[1])
    arm = arm[yi][:, xi]
sl = srgb_to_lin(sd[..., :3]) @ np.array([0.2126, 0.7152, 0.0722])
var = sl / max(np.median(sl), 1e-4)                         # keep the steel's own mottling as variation
bright = blur(sl, 2)
thr = np.percentile(bright, 86)
bare = np.clip((bright - thr) / max(np.percentile(bright, 97) - thr, 1e-4), 0, 1)
bare = np.maximum(bare, np.clip((arm[..., 2] - 0.75) / 0.2, 0, 1))
bare = blur(bare, 1)
metal = np.clip((bare - 0.35) / 0.3, 0, 1)                 # mostly 0 or 1, thin ramp
oxide_lin = srgb_to_lin(np.full_like(sl, 55 / 255.0)) * np.clip(var, 0.7, 1.3)
bare_lin = srgb_to_lin(np.full_like(sl, 192 / 255.0)) * np.clip(var, 0.9, 1.1)
y = oxide_lin * (1 - metal) + bare_lin * metal
tint_ox = np.array([1.0, 0.97, 0.93]); tint_bare = np.array([1.0, 0.99, 0.97])   # oxide slightly warm, steel neutral
col = y[..., None] * (tint_ox * (1 - metal[..., None]) + tint_bare * metal[..., None])
save('T_GateIron_D_v2', lin_to_srgb(col))
r_ox = np.clip(0.66 + 0.10 * (1 - np.clip(var, 0, 2) / 2) + 0.05 * (arm[..., 1] - arm[..., 1].mean()), 0.5, 0.85)
r = r_ox * (1 - metal) + 0.34 * metal
save('T_GateIron_ARM_v2', np.stack([arm[..., 0], r, metal], -1))
mid = ((metal > 0.1) & (metal < 0.9)).mean()
print('iron: bare metal %.1f%%, in-between %.1f%%, oxide sRGB ~55, bare sRGB ~192' % (100 * (metal > 0.5).mean(), 100 * mid))

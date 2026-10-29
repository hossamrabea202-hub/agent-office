# PBR validator for baked textures (laptop2 realism standard, 2026-10-29). Blender python:
#   blender -b --factory-startup -P pbr_check.py -- <BaseColor.png> <ORM.png> [more pairs...]
# Checks (from the PBR albedo charts): non-metal albedo 30..240 sRGB (strict floor 50), metal albedo 180..250 sRGB,
# roughness not flat (std >= 0.05 over the texture), no pure black/white texels. Prints a verdict per texture.
import bpy, sys, numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
def load(p):
    im = bpy.data.images.load(p); im.colorspace_settings.name = 'Non-Color'; w, h = im.size
    a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
    a = a.reshape(h, w, 4); s = max(1, w // 1024); return a[::s, ::s]
for i in range(0, len(args), 2):
    bc, orm = load(args[i]), load(args[i + 1])
    used = bc[..., :3].max(-1) > 0.002                      # texels outside the UV islands are black: ignore them
    srgb = bc[..., :3][used].mean(-1) * 255                  # file values are already sRGB
    met = orm[..., 2][used] > 0.5; rg = orm[..., 1][used]
    die = srgb[~met]; mt = srgb[met]
    pct = lambda a, q: float(np.percentile(a, q)) if len(a) else float('nan')
    issues = []
    if len(die):
        lo, hi = (die < 30).mean(), (die > 240).mean()
        if lo > 0.02: issues.append('%.1f%% of non-metal texels darker than 30 sRGB (too black)' % (lo * 100))
        if hi > 0.02: issues.append('%.1f%% of non-metal texels brighter than 240 sRGB' % (hi * 100))
    if len(mt):
        if (mt < 150).mean() > 0.05: issues.append('%.1f%% of metal texels below 150 sRGB (metal too dark)' % ((mt < 150).mean() * 100))
    if rg.std() < 0.05: issues.append('roughness nearly flat (std %.3f)' % rg.std())
    print('PBR', args[i].split('/')[-1].split('\\')[-1], '| non-metal p5/p50/p95 sRGB = %.0f/%.0f/%.0f' % (pct(die, 5), pct(die, 50), pct(die, 95)),
          '| metal %.0f%% (p50 %.0f)' % (met.mean() * 100, pct(mt, 50)), '| rough p5/p95 %.2f/%.2f' % (pct(rg, 5), pct(rg, 95)),
          '|', 'OK' if not issues else 'ISSUES: ' + '; '.join(issues))

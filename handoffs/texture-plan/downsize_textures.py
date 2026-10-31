# #262 step 2 (TGA, 2026-10-31): downsize the repo texture sources to the budget in audit.json (texture_audit.py).
#   blender -b --factory-startup -P downsize_textures.py -- [--apply] [--kit owner/Kit]
# Without --apply: prints what it would do. Names and formats stay the same, so no import script changes.
# Filtering: box (area) average in powers of two. Colour / emissive maps are averaged in LINEAR light (sRGB decode -> mean ->
# encode) so they do not darken; ORM / masks keep every channel as data; normal maps are decoded, averaged, RENORMALISED and
# re-encoded (DirectX and GL alike). Alpha is averaged as data.
# Exception E1 (keep the look): a 1K-budget kit whose median texel density would drop below 256 px/m stays at 2K.
import bpy, os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
APPLY = '--apply' in args; ONLY = args[args.index('--kit') + 1] if '--kit' in args else None
A = json.load(open(os.path.join(HERE, 'audit.json')))
cap = {}
for k, v in A['kits'].items():
    c = v['cap']
    ms = [m['pxm_after'] for m in v['meshes']]
    if c == 1024 and ms and float(np.median(ms)) < 256: c = 2048; print('E1 keep 2K:', k, 'median after %.0f px/m' % float(np.median(ms)))
    cap[k] = c
to_lin = lambda s: np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
to_srgb = lambda l: np.where(l <= 0.0031308, l * 12.92, 1.055 * np.power(np.clip(l, 0, 1), 1 / 2.4) - 0.055)
done, saved = [], 0.0
for r in A['rows']:
    if ONLY and r['kit'] != ONLY: continue
    c = cap[r['kit']]
    if c == 0 or max(r['w'], r['h']) <= c: continue
    f = 1
    while max(r['w'], r['h']) // f > c: f *= 2
    path = os.path.join(REPO, r['file'])
    if not APPLY: print('would', r['file'], '%dx%d -> %dx%d' % (r['w'], r['h'], r['w'] // f, r['h'] // f)); continue
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    W, H = img.size; ch = img.channels
    px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
    w2, h2 = W // f, H // f; px = px[:h2 * f, :w2 * f]
    role = r['role']
    if role in ('colour', 'colour+alpha', 'emissive'): px[..., :3] = to_lin(px[..., :3])
    if role.startswith('normal'): px[..., :3] = px[..., :3] * 2 - 1
    out = px.reshape(h2, f, w2, f, 4).mean(axis=(1, 3))
    if role in ('colour', 'colour+alpha', 'emissive'): out[..., :3] = to_srgb(out[..., :3])
    if role.startswith('normal'):
        n = out[..., :3]; n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8; out[..., :3] = n * 0.5 + 0.5
    fmt, alpha = img.file_format, ch == 4
    bpy.data.images.remove(img)
    im = bpy.data.images.new('ds', w2, h2, alpha=alpha); im.colorspace_settings.name = 'Non-Color'
    if not alpha: out[..., 3] = 1.0
    im.pixels.foreach_set(np.clip(out, 0, 1).ravel()); im.filepath_raw = path; im.file_format = fmt
    sc = bpy.context.scene.render.image_settings; sc.color_mode = 'RGBA' if alpha else 'RGB'; sc.compression = 100
    old = os.path.getsize(path); im.save(); bpy.data.images.remove(im)
    saved += (old - os.path.getsize(path)) / 1048576; done.append(r['file'])
    print('DS', r['file'], '%dx%d -> %dx%d' % (W, H, w2, h2), flush=True)
json.dump(dict(cap=cap, done=done), open(os.path.join(HERE, 'downsized.json' if not ONLY else 'downsized_%s.json' % ONLY.replace('/', '_')), 'w'), indent=1)
print('DOWNSIZE %s: %d files, %.0f MB smaller on disk' % ('APPLIED' if APPLY else 'DRY', len(done), saved), flush=True)

# #262 before/after sheets (TGA, 2026-10-31): per kit, the biggest downsized colour map, centre close-up (a quarter of the
# texture width), before (git HEAD~ original) | after (current), both shown at 384 px. One PNG per owner (rows in kit order,
# two kits per row). blender -b --factory-startup -P before_after.py -- <HEAD-originals dir>
#   The originals dir holds files named like 'assets__tga__Feast__textures__T_Feast_BC.png' (git show of the old blob).
import bpy, os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ORIG = sys.argv[sys.argv.index('--') + 1]
A = json.load(open(os.path.join(HERE, 'audit.json'))); D = json.load(open(os.path.join(HERE, 'downsized.json')))
done = set(D['done']); T = 384
def load(p):
    im = bpy.data.images.load(p); W, H = im.size; px = np.empty(W * H * 4, np.float32); im.pixels.foreach_get(px); bpy.data.images.remove(im)
    return px.reshape(H, W, 4)
def crop(px):
    H, W = px.shape[:2]; s = max(W // 4, 8); y0, x0 = H // 2 - s // 2, W // 2 - s // 2; c = px[y0:y0 + s, x0:x0 + s]
    yi = (np.arange(T) * s // T); return c[yi][:, yi]                                     # nearest: shows the real pixels
sheets = {}
for kit in sorted(A['kits']):
    cands = [r for r in A['rows'] if r['kit'] == kit and r['file'] in done and r['role'] in ('colour', 'colour+alpha')]
    if not cands: continue
    r = max(cands, key=lambda r: r['w'] * r['h']); o = os.path.join(ORIG, r['file'].replace('/', '__'))
    if not os.path.exists(o): print('no original', r['file']); continue
    pair = np.concatenate([crop(load(o)), np.ones((T, 6, 4), np.float32), crop(load(os.path.join(REPO, r['file'])))], 1)
    sheets.setdefault(kit.split('/')[0], []).append((kit, pair))
out = {}
for owner, rows in sheets.items():
    cells = [p for _, p in rows]
    if len(cells) % 2: cells.append(np.zeros_like(cells[0]))
    gap = np.zeros((T, 24, 4), np.float32)
    lines = [np.concatenate([cells[i], gap, cells[i + 1]], 1) for i in range(0, len(cells), 2)]
    sh = np.concatenate([np.concatenate([l, np.zeros((16, l.shape[1], 4), np.float32)], 0) for l in lines], 0); sh[..., 3] = 1
    Hh, Ww = sh.shape[:2]; im = bpy.data.images.new('ba', Ww, Hh); im.pixels.foreach_set(sh.ravel())
    p = os.path.join(HERE, 'before_after_%s.png' % owner); im.filepath_raw = p; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    out[owner] = [k for k, _ in rows]; print('SHEET', p, len(rows), 'kits', flush=True)
json.dump(out, open(os.path.join(HERE, 'before_after_order.json'), 'w'), indent=1)

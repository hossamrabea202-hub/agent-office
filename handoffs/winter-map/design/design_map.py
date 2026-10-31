"""WinterKeep #390: design map = top-down render + measured sight lines from the towers + labels and routes.

Blender's Python:  python.exe -I design_map.py      (needs terrain/out and lookdev/shots/top_overcast.png)
Writes design/viewshed.png (RGBA), design/design_map.html, and with Edge headless design/design_map.png.
"""
import json, math, os, struct, subprocess, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); TER = os.path.join(HERE, '..', 'terrain', 'out')
H = np.load(os.path.join(TER, 'height_m.npy')); N = H.shape[0]; HALF = (N - 1) / 2
L = json.load(open(os.path.join(TER, 'layout.json')))
S = 4; h = H[::S, ::S]; n = h.shape[0]
def img(p): return (p[0] / 100 + HALF, p[1] / 100 + HALF)

# viewshed from the 4 tower tops (castle 46 x 34.5 m, towers 20 m over the plateau, eye 1.7 m over the merlons)
cx, cy = img(L['castle_centre']); cz = L['castle_centre'][2] / 100
towers = [(cx + dx, cy + dy, cz + 18 + 1.7) for dx in (-23, 23) for dy in (-17, 17)]
ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) * S
vis = np.zeros((n, n), np.uint8)
for ox, oy, oz in towers:
    tz = h + 1.8                                                     # can the tower see a 1.8 m figure standing there?
    blocked = np.zeros((n, n), bool)
    for t in np.linspace(0.02, 0.98, 90):
        px = ox + (xs - ox) * t; py = oy + (ys - oy) * t
        ground = h[np.clip((py / S).astype(int), 0, n - 1), np.clip((px / S).astype(int), 0, n - 1)]
        blocked |= ground > oz + (tz - oz) * t + 0.3
    vis = np.maximum(vis, (~blocked).astype(np.uint8))
# forest canopy hides the ground below it (trees ~20 m): seen = terrain visible and not under dense forest
lay = np.load(os.path.join(TER, 'layers.npz')); forest = lay['M_Forest'][::S, ::S] > 140
dist = np.hypot(xs - cx, ys - cy)
seen = vis.astype(bool) & ~forest & (dist < 1400)
print('visible from towers (open ground within 1.4 km): %.0f %%' % (100 * seen[dist < 1400].mean()))

def png_rgba(path, a):
    hh, ww, _ = a.shape; raw = b''.join(b'\x00' + a[y].astype(np.uint8).tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', ww, hh, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 6)) + ch(b'IEND', b''))
ov = np.zeros((n, n, 4), np.uint8)
ov[seen] = (255, 196, 64, 48)                                       # amber = the walls see it
ov[vis.astype(bool) & forest] = (255, 196, 64, 22)
ov[~vis.astype(bool) & (dist < 1400)] = (30, 20, 60, 85)             # dead ground: the approach the walls cannot see
png_rgba(os.path.join(HERE, 'viewshed.png'), ov)

# ---- html with svg labels, in image metres (0..2016) scaled to 1000 px
K = 1000 / (N - 1)
def P(p): x, y = img(p); return x * K, y * K
def poly(pts, cls): return '<polyline class="%s" points="%s"/>' % (cls, ' '.join('%.1f,%.1f' % P(p) for p in pts))
def lab(p, text, dx=8, dy=-8, cls='lab'): x, y = P(p); return '<circle cx="%.1f" cy="%.1f" r="4" class="pin"/><text x="%.1f" y="%.1f" class="%s">%s</text>' % (x, y, x + dx, y + dy, cls, text)
r = L['realm_melt']; rx, ry = P(r['centre']); lk = L['lake']; lx, ly = P(lk['centre'])
svg = [poly(L['river_spline_cm'], 'river'), poly(L['road_spline_cm'], 'road'), poly(L['mine_road_spline_cm'], 'road mine')]
for k, pts in L['zombie_routes'].items(): svg.append(poly(pts, 'zed'))
svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" class="realm"/>' % (rx, ry, r['radius_m'] * K))
svg += [lab(L['castle_centre'], 'WINTERKEEP (castle, 62 m)', 10, -12, 'lab big'), lab(L['bridge'], 'Bridge: chokepoint 1', 10, 16),
        lab(lk['centre'], 'Frozen lake: chokepoint 2 (ice)', -120, 4), lab(L['mine_portal'], 'Mine in the iced cliff (#201)', 8, -10),
        lab(L['frozen_falls'], 'Frozen waterfall', 10, 4), lab(L['avalanche_gully'][0], 'Avalanche gully', 10, 4),
        lab(L['realm_melt']['centre'], 'Tentacle realm: melt zone, steam', -150, 72, 'lab red')]
for k, v in L['farms'].items(): svg.append(lab(v, k.replace('_', ' ') + ' (survivors #11)', 8, 14))
fv = L['first_view']; x0, y0 = P(fv['from']); x1, y1 = P(fv['look_at'])
a = math.atan2(y1 - y0, x1 - x0)
svg.append('<path class="fov" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>' % (x0, y0, x0 + 260 * math.cos(a - 0.5), y0 + 260 * math.sin(a - 0.5), x0 + 260 * math.cos(a + 0.5), y0 + 260 * math.sin(a + 0.5)))
svg.append('<text x="%.1f" y="%.1f" class="lab">Player first view</text>' % (x0 + 120 * math.cos(a) + 8, y0 + 120 * math.sin(a)))
# drift field label: lee of the castle rise toward the realm
svg.append('<text x="%.1f" y="%.1f" class="lab drift">Deep-drift field: chokepoint 3 (slow)</text>' % P((cx * 100 - HALF * 100 + 26000, cy * 100 - HALF * 100 + 9000)))
# wind arrow + north + scale
svg.append('<g class="wind"><line x1="60" y1="60" x2="130" y2="130"/><polygon points="130,130 112,126 126,112"/><text x="40" y="48">Wind from NW (315°)</text></g>')
svg.append('<g class="scale"><line x1="760" y1="970" x2="959.2" y2="970"/><text x="790" y="960">400 m</text><text x="960" y="40">N ↑</text></g>')
html = '''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#11151a;font:13px system-ui,Segoe UI,sans-serif}
.map{position:relative;width:1000px;height:1000px}
.map img{position:absolute;inset:0;width:1000px;height:1000px;image-rendering:auto}
svg{position:absolute;inset:0}
.river{fill:none;stroke:#7fb4d8;stroke-width:3;stroke-dasharray:1 0;opacity:.85}
.road{fill:none;stroke:#c9a46a;stroke-width:3}.mine{stroke-dasharray:6 4}
.zed{fill:none;stroke:#e0464e;stroke-width:2.5;stroke-dasharray:8 6;marker-end:url(#arr)}
.realm{fill:rgba(20,0,10,.35);stroke:#e0464e;stroke-width:2}
.pin{fill:#fff;stroke:#000;stroke-width:1.5}
.lab{fill:#fff;font-weight:600;paint-order:stroke;stroke:#000;stroke-width:3px}.big{font-size:16px}.red{fill:#ff8a8f}.drift{fill:#cfe6ff}
.fov{fill:rgba(255,255,255,.12);stroke:#fff;stroke-width:1.5}
.wind line,.scale line{stroke:#fff;stroke-width:3}.wind polygon{fill:#fff}.wind text,.scale text{fill:#fff;font-weight:700;paint-order:stroke;stroke:#000;stroke-width:3px}
.key{position:absolute;left:12px;bottom:12px;background:rgba(0,0,0,.6);color:#fff;padding:8px 10px;border-radius:6px;line-height:1.5}
.key i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px}
</style></head><body><div class="map"><img src="BASE"><img src="viewshed.png">
<svg viewBox="0 0 1000 1000"><defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e0464e"/></marker></defs>SVG</svg>
<div class="key"><b>WinterKeep 2 × 2 km</b> (#390)<br><i style="background:#c9a46a"></i>gate road / mine road<br><i style="background:#7fb4d8"></i>frozen river<br>
<i style="background:#e0464e"></i>zombie approach routes<br><i style="background:rgba(255,196,64,.8)"></i>seen from the towers<br><i style="background:#28283c"></i>dead ground (walls blind)</div>
</div></body></html>'''.replace('SVG', '\n'.join(svg)).replace('BASE', os.environ.get('BASE', '../lookdev/shots/top_overcast.png'))
open(os.path.join(HERE, 'design_map.html'), 'w', encoding='utf-8').write(html)
edge = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if os.path.exists(edge):
    subprocess.run([edge, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                    '--screenshot=' + os.path.join(HERE, 'design_map.png'), '--window-size=1000,1000',
                    'file:///' + os.path.join(HERE, 'design_map.html').replace('\\', '/')], timeout=120)
    print('wrote design_map.png')

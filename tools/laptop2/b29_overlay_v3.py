# #29: owner's blue fog zones (perspective screenshot) -> clean v3 top map, plus the v2 play-zone border.
import numpy as np, zlib, struct, json, sys
D = r'C:/Users/hossam.rabea/ckw/b29/v3/'
def bmp(p):
    b = open(p, 'rb').read(); off, w, h, bpp = struct.unpack_from('<I', b, 10)[0], *struct.unpack_from('<iiH', b, 18)[:2], struct.unpack_from('<H', b, 28)[0]
    w, h = struct.unpack_from('<ii', b, 18); bpp = struct.unpack_from('<H', b, 28)[0]; c = bpp // 8; row = (w * c + 3) & ~3
    a = np.frombuffer(b, np.uint8, row * abs(h), off).reshape(abs(h), row)[:, :w * c].reshape(abs(h), w, c)[..., 2::-1]
    return (a[::-1] if h > 0 else a).astype(np.float32) / 255
def png(p, im):
    a = (np.clip(im, 0, 1) * 255).astype(np.uint8); H, W, _ = a.shape
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(p, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(b''.join(b'\x00' + a[r].tobytes() for r in range(H)), 6)) + ch(b'IEND', b''))
top = bmp(D + 'top.bmp'); own = bmp(D + 'owner.bmp')
TH, TW, _ = top.shape
M = json.load(open(r'C:/Users/hossam.rabea/agent-office/handoffs/exports/laptop2/bounds29/v3/meta3.json'))['full']
cx, cy = M['center']; WY, HX = M['width_y'], M['height_x']
w2p = lambda X, Y: ((np.asarray(Y) - (cy - WY / 2)) / WY * TW, (0.5 - (np.asarray(X) - cx) / HX) * TH)   # -> (px, py)
# owner screenshot -> world: similarity from two anchors (screen px -> world X,Y)
A = [((185, 170), (-800, -24000)),      # tunnel portal E (the small building on the hill)
     ((590, 80), (-5, -5259))]           # Env_CorruptedTentacle_Fog1 body
(s0, w0), (s1, w1) = A
zs = complex(s1[0] - s0[0], -(s1[1] - s0[1]))          # screen right/up
zw = complex(w1[1] - w0[1], w1[0] - w0[0])             # world  +Y/+X
k = zw / zs
print('scale cm/px %.1f  rot deg %.1f' % (abs(k), np.degrees(np.angle(k))))
r, g, b = own[..., 0], own[..., 1], own[..., 2]
blue = (b > 0.62) & (r < 0.35) & (g > 0.45) & (b - r > 0.4)
blue[600:] = False                                      # viewer toolbar
ys, xs = np.nonzero(blue)
z = complex(w0[1], w0[0]) + k * ((xs - s0[0]) - 1j * (ys - s0[1]))
px, py = w2p(z.imag, z.real)
out = top.copy() * 0.85
# play zone (v2) border
d = np.load(r'C:/Users/hossam.rabea/ckw/b29/border.npz'); lo, cell = d['lo'], float(d['cell'])
for m, col in ((d['edge'], (1, .85, .15)), (d['cliff'], (1, .15, .1))):
    jj, ii = np.nonzero(m); X = lo[0] + (ii + .5) * cell; Y = lo[1] + (jj + .5) * cell
    qx, qy = w2p(X, Y)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            a, bb = np.clip((qy + dy).astype(int), 0, TH - 1), np.clip((qx + dx).astype(int), 0, TW - 1); out[a, bb] = col
clean = out.copy()
# owner strokes
for dx in range(-2, 3):
    for dy in range(-2, 3):
        a, bb = (py + dy).astype(int), (px + dx).astype(int); ok = (a >= 0) & (a < TH) & (bb >= 0) & (bb < TW)
        out[a[ok], bb[ok]] = (0.0, 0.85, 1.0)
def deco(im):
    for X in range(-60000, 30001, 5000):          # 50 m grid
        q = int(w2p(X, 0)[1])
        if 0 <= q < TH: im[q, :] = im[q, :] * 0.6 + 0.4
    for Y in range(-40000, 25001, 5000):
        q = int(w2p(0, Y)[0])
        if 0 <= q < TW: im[:, q] = im[:, q] * 0.6 + 0.4
    for X, Y in ((1500, 1750), (-800, -24000), (-17800, -16200)):   # castle, tunnel E, tunnel W
        qx, qy = w2p(X, Y); t = np.linspace(0, 2 * np.pi, 400)
        for rr in (40, 43, 46):
            im[np.clip((qy + rr * np.sin(t)).astype(int), 0, TH - 1), np.clip((qx + rr * np.cos(t)).astype(int), 0, TW - 1)] = (1, 0.2, 1)
jj, ii = np.nonzero(d['zone']); X = lo[0] + ii * cell; Y = lo[1] + jj * cell
qx, qy = w2p(X, Y); x0, x1 = int(max(qx.min() - 160, 0)), int(min(qx.max() + 160, TW)); y0, y1 = int(max(qy.min() - 160, 0)), int(min(qy.max() + 160, TH))
for im, n in ((out, 'overlay_v3.png'), (clean, 'mark_here_v3.png')):
    deco(im); png(D + n, im[y0:y1, x0:x1])
json.dump({'crop_px': [x0, y0], 'map_px_size': [TW, TH], 'center': [cx, cy], 'width_y': WY, 'height_x': HX}, open(D + 'mark_here_v3.json', 'w'))
print('crop', x0, x1, y0, y1, 'blue px', len(xs))

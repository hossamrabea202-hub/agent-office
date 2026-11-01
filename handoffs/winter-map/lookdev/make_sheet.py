"""Contact sheet: blender -b --factory-startup -P make_sheet.py -- <out.png> <cols> <img1> <img2> ... (each cell 800 px wide)."""
import bpy, sys, struct, zlib
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]; OUT, COLS, IMGS = A[0], int(A[1]), A[2:]
CW = 800
def load(p):
    im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1, :, :3]; s = w / CW; ys = (np.arange(int(h / s)) * s).astype(int); xs = (np.arange(CW) * s).astype(int)
    return a[ys][:, xs]
cells = [load(p) for p in IMGS]; ch = max(c.shape[0] for c in cells); rows = (len(cells) + COLS - 1) // COLS
sheet = np.zeros((rows * ch, COLS * CW, 3), np.float32)
for i, c in enumerate(cells): r, k = divmod(i, COLS); sheet[r * ch:r * ch + c.shape[0], k * CW:(k + 1) * CW] = c
d = (np.clip(sheet, 0, 1) * 255 + 0.5).astype(np.uint8); hh, ww = d.shape[:2]
raw = b''.join(b'\x00' + d[y].tobytes() for y in range(hh))
chunk = lambda t, x: struct.pack('>I', len(x)) + t + x + struct.pack('>I', zlib.crc32(t + x) & 0xffffffff)
open(OUT, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', ww, hh, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
print('sheet', OUT, ww, hh)

# #390 offline check of SNOWFALL_HLSL (winterkeep_ue.py): numpy port, one camera, 4 slabs -> PNG.
#   "<blender python>" -I preview_snowfall.py <SnowFall 0..1> <WindSpeed m/s> <out.png>
import sys, zlib, struct
import numpy as np
snow, spd, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
W, H, FOV, T = 960, 540, 90.0, 37.3
yaw = np.radians(135.0)                           # camera looks SE (downwind); X east, Y south
fwd = np.array([np.sin(yaw), -np.cos(yaw), 0.0]); right = np.array([np.cos(yaw), np.sin(yaw), 0.0]); up = np.array([0, 0, 1.0])
f = np.tan(np.radians(FOV) / 2)
xs, ys = np.meshgrid((np.arange(W) + 0.5) / W * 2 - 1, 1 - (np.arange(H) + 0.5) / H * 2)
d = fwd[None, None] + xs[..., None] * f * right + ys[..., None] * f * H / W * up
d /= np.linalg.norm(d, axis=-1, keepdims=True)
cam = np.array([1234.0, -5678.0, 6200.0])
b = np.radians(315.0 + 180.0); V = np.array([np.sin(b) * spd * 100, -np.cos(b) * spd * 100, -110.0])
O = cam - V * T; Vs = V / 60.0; p = min(max(snow, 0), 1)
A = np.zeros((H, W))
fr = lambda x: x - np.floor(x)
for R in (100, 200, 400, 800):
    hl = np.maximum(np.linalg.norm(d[..., :2], axis=-1), 0.15); t0, t1 = R / hl, 2 * R / hl
    c = R / 6.0; rv = max(0.8, R * 0.0025)
    a = np.zeros((H, W))
    for i in range(6):
        q = O + d * (t0 + (t1 - t0) * (i + 0.5) / 6)[..., None]
        cell = np.floor(q / c)
        h1 = fr(np.sin(cell @ np.array([127.1, 311.7, 74.7])) * 43758.5453)
        h2 = fr(np.sin(cell @ np.array([269.5, 183.3, 246.1])) * 43758.5453)
        h3 = fr(np.sin(cell @ np.array([113.5, 271.9, 124.6])) * 43758.5453)
        h4 = fr(h1 * 91.7 + h2 * 13.3 + h3 * 7.1)
        ph = T * (1.3 + 2 * h4) + h1 * 6.2831
        F = (cell + 0.15 + 0.7 * np.stack([h1, h2, h3], -1)) * c + np.stack([np.sin(ph), np.cos(ph * 0.8), 0 * ph], -1) * 4
        w = F - O; tt = (w * d).sum(-1)
        dp = w - d * tt[..., None]; vp = Vs - d * (d @ Vs)[..., None]
        k = np.clip(-(dp * vp).sum(-1) / np.maximum((vp * vp).sum(-1), 1e-4), 0, 1)
        dd = np.linalg.norm(dp + vp * k[..., None], axis=-1); e = 2 * rv / (2 * rv + np.linalg.norm(vp, axis=-1))
        x = np.clip((dd - rv) / (rv * 0.4 - rv), 0, 1); sm = x * x * (3 - 2 * x)
        ok = (h4 <= p) & (tt >= t0) & (tt <= t1)
        a = 1 - (1 - a) * (1 - np.where(ok, sm * e, 0))
    A = 1 - (1 - A) * (1 - a * 0.9)              # back-to-front order does not matter for a grey-scale check
sky = 0.62 + 0.18 * ys.clip(0, 1); ground = 0.55
bg = np.where(ys > 0.05, sky, np.where(ys > -0.15, 0.07, ground)); flake = 0.84 * 0.80        # lit flake ~ albedo x overcast light, vs sky radiance
img = bg * (1 - A) + flake * A
px = (np.clip(img, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
raw = b''.join(b'\x00' + px[y].tobytes() for y in range(H))
png = b'\x89PNG\r\n\x1a\n' + b''.join(struct.pack('>I', len(dd_)) + t + dd_ + struct.pack('>I', zlib.crc32(t + dd_)) for t, dd_ in
      ((b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 0, 0, 0, 0)), (b'IDAT', zlib.compress(raw, 9)), (b'IEND', b'')))
open(out, 'wb').write(png); print(out, 'coverage %.3f' % A.mean())

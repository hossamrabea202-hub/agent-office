# #268 storyboard preview (adjustedfilm, 2026-10-31). A MOCK for judging the look before the Master pastes, not an
# in-engine capture: the stand-in book / satchel are checkking's procedural v1 models (the game uses the pickups' own
# meshes), the title font is Georgia Bold (the game uses Cinzel), and the background is a real in-game screenshot.
#   blender -b --factory-startup -P preview_reveal268.py -- <book|bag> <background.jpg> <out.png>
# Same numbers as the game: 30 deg capture FOV, key 3600 K / rim 8500 K / fill 6000 K at 13 : 30 : 2.5, the reveal
# timeline of gen_reveal268.py, and a numpy copy of M_RevealScreen / M_RevealBlur (setup_reveal268_ue.py).
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
WHICH, BG, OUTP = argv[0], argv[1], argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.join(HERE, '..', '..', '..', 'checkking', 'RevealMG', 'source', 'build_reveal.py')
TMP = os.path.join(os.path.dirname(OUTP), '_tmp268'); os.makedirs(TMP, exist_ok=True)

# ---- the v1 stand-in model (only its model part)
src = open(V1, encoding='utf-8').read().split('# ---------------------------------------------------------------- lights + camera')[0]
sys.argv = ['blender', '--', WHICH, TMP]
exec(compile(src, V1, 'exec'))
sc = bpy.context.scene
root = bpy.data.objects['Root']


def kelvin(k):
    """rough blackbody -> linear RGB (Tanner Helland fit, then linearised)."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    return tuple((min(255, max(0, c)) / 255.0) ** 2.2 for c in (r, g, b))


def spot(name, loc_ue, cd, k, size):
    # UE (cm, X forward, Y right, Z up; capture looks +X) -> Blender (m, camera looks +Y): x_b = y_ue, y_b = x_ue
    loc = Vector((loc_ue[1] / 100.0 * 0.6, loc_ue[0] / 100.0 * 0.6, loc_ue[2] / 100.0 * 0.6))
    d = bpy.data.lights.new(name, 'AREA'); d.size = size; d.color = kelvin(k); d.energy = cd * 4.0
    o = bpy.data.objects.new(name, d); col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - loc).to_track_quat('-Z', 'Y').to_euler()


spot('Key', (-120, -110, 95), 13.0, 3600, 0.35)
spot('Rim', (110, 95, 70), 30.0, 8500, 0.12)
spot('Fill', (-105, 130, -15), 2.5, 6000, 0.8)
cam_d = bpy.data.cameras.new('Cap'); cam_d.sensor_fit = 'VERTICAL'; cam_d.angle_y = math.radians(30)
cam = bpy.data.objects.new('Cap', cam_d); col.objects.link(cam); sc.camera = cam
R = max(o.dimensions.length for o in bpy.data.objects if o.type == 'MESH') * 0.5
dist = R * 1.25 / math.tan(math.radians(15))
cam.location = (0, -dist, 0); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'CYCLES'
try:
    cp = bpy.context.preferences.addons['cycles'].preferences
    cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
    for d in cp.devices: d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
except Exception: pass
sc.cycles.samples = 40; sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 384
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'


def load(path):
    im = bpy.data.images.load(path); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(im); return a


def render_item(yaw_deg, i):
    root.rotation_euler = (0, 0, math.radians(-yaw_deg))   # UE yaw (Z up, left-handed) -> Blender
    root.scale = (1, 1, 1); root.location = (0, 0, 0)
    sc.render.filepath = os.path.join(TMP, 'item_%s_%d.png' % (WHICH, i))
    bpy.ops.render.render(write_still=True)
    return load(sc.render.filepath)


# ---- the title (Georgia Bold stand-in for Cinzel), one strip + per-letter column ranges
def render_text(txt, tag):
    for o in list(bpy.data.objects):
        o.hide_render = True
    fnt = bpy.data.fonts.load(r'C:\Windows\Fonts\georgiab.ttf')
    objs, x = [], 0.0
    for ch in txt:
        cu = bpy.data.curves.new('L', 'FONT'); cu.body = ch if ch != ' ' else '.'; cu.font = fnt; cu.size = 1.0
        o = bpy.data.objects.new('L', cu); col.objects.link(o)
        m = bpy.data.materials.new('W'); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear(); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
        out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0]); cu.materials.append(m)
        bpy.context.view_layer.update()
        w = o.dimensions.x if ch != ' ' else 0.32
        o.location = (x, 0, 0); o.rotation_euler = (math.radians(90), 0, 0)
        if ch == ' ': o.hide_render = True
        objs.append((x, w)); x += w + 0.06
    tw = x - 0.06
    tc = bpy.data.cameras.new('T'); tc.type = 'ORTHO'; tc.ortho_scale = tw * 1.04
    to = bpy.data.objects.new('T', tc); col.objects.link(to); to.location = (tw / 2, -5, 0.36); to.rotation_euler = (math.radians(90), 0, 0)
    old = sc.camera; sc.camera = to
    rx = 1400; sc.render.resolution_x, sc.render.resolution_y = rx, int(rx / 1.04 / tw * 1.0 * 1.25) if tw > 0 else 200
    sc.cycles.samples = 8
    sc.render.filepath = os.path.join(TMP, 'title_%s.png' % tag); bpy.ops.render.render(write_still=True)
    img = load(sc.render.filepath)
    sc.camera = old; sc.render.resolution_x = sc.render.resolution_y = 384; sc.cycles.samples = 40
    left = (tw / 2 - tw * 1.04 / 2)
    cols = [(int((x0 - left) / (tw * 1.04) * rx), int((x0 + w - left) / (tw * 1.04) * rx)) for x0, w in objs]
    for o in list(bpy.data.objects):
        if o.name.startswith('L') or o.name.startswith('T'): bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects: o.hide_render = False
    return img, cols


TITLE = 'BOOK OF SKILLS' if WHICH == 'book' else 'SATCHEL OF HOLDING'
LINE, KEY = ('Open the skill tree', 'T') if WHICH == 'book' else ('Open your pack', 'I')

# ---- the timeline (same as gen_reveal268.py)
sat = lambda v: min(1.0, max(0.0, v))
def curves(tl):
    pa = sat(tl / 0.12); p = sat((tl - 0.12) / 0.35); e = 1 - 2 ** (-10 * p); q = sat((tl - 0.30) / 0.6)
    over = 0.104 * math.sin(math.pi * q) * (1 - q)
    s_in = 0.5 - 0.06 * pa if tl < 0.12 else 0.44 + 0.56 * e + over
    xo = sat((tl - 1.85) / 0.4); ein = xo * xo * (3 - 2 * xo)
    burst = sat((tl - 0.40) / 0.07) if tl < 0.47 else math.exp(-(tl - 0.47) * 6)
    return dict(S=s_in * (1 - 0.9 * ein), itemA=sat(tl / 0.06) * (1 - sat((tl - 2.15) / 0.1)), ein=ein, burst=burst,
                ring=sat((tl - 0.47) / 0.6) if tl > 0.47 else 0.0, bg=sat(tl / 0.3) * (1 - xo),
                yaw=25 - 160 * (1 - e) + 7 * math.sin(1.3 * (tl - 0.47)) * sat((tl - 0.47) / 0.6) + 120 * ein,
                ta=1 - sat((tl - 1.85) / 0.2), la=sat((tl - 0.95) / 0.25) * (1 - sat((tl - 1.85) / 0.2)),
                dockA=sat((tl - 2.2) / 0.08) * (1 - sat((tl - 2.5) / 0.6)), dockR=0.012 + 0.03 * sat((tl - 2.2) / 0.5))


# ---- numpy versions of the materials
def to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def blur(img, amt, H):
    if amt < 0.002: return img
    s = 22.0 * amt * H / 1080.0
    acc = np.zeros_like(img)
    for i in range(28):
        k = (i + 0.5) / 28; an = i * 2.39996323
        dx, dy = int(round(math.cos(an) * math.sqrt(k) * s)), int(round(math.sin(an) * math.sqrt(k) * s))
        acc += np.roll(np.roll(img, dy, 0), dx, 1)
    col_ = acc / 28
    lum = (col_ * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    col_ = col_ + (lum * np.array([1.03, 0.98, 0.90]) - col_) * 0.5 * amt
    col_ = col_ * (1 - 0.4 * amt)
    w = min(1, amt / 0.35); w = w * w * (3 - 2 * w)
    return img + (col_ - img) * w


def screen(Hh, Ww, layer, T, c, rad, bg, glow, burst, ring, dust_amt, itemA, dock, dockR):
    v, u = np.mgrid[0:Hh, 0:Ww].astype(np.float32); u = (u + 0.5) / Ww; v = (v + 0.5) / Hh
    asp = Ww / Hh; dxy_x = (u - c[0]) * asp; dxy_y = v - c[1]; r = np.sqrt(dxy_x ** 2 + dxy_y ** 2)
    gold = np.array([1.0, 0.70, 0.32]); add = np.zeros((Hh, Ww, 3), np.float32); scrim = np.zeros((Hh, Ww), np.float32)
    dust = np.zeros_like(add)
    for l in ((0, 1) if layer == 0 else (2,)):
        sc_ = 4.5 if l == 2 else 12.0 + l * 9.0
        px = u * asp * sc_; py = v * sc_ + T * (0.016 + 0.010 * l) * sc_
        px = px + np.sin(T * 0.35 + l * 1.7 + py * 0.15) * 0.35
        idx, idy = np.floor(px), np.floor(py); fx, fy = px - idx - 0.5, py - idy - 0.5
        h = np.modf(np.abs(np.sin((idx + l * 19.13) * 127.1 + (idy + l * 19.13) * 311.7) * 43758.5453))[0]
        h2 = np.modf(h * 13.37 + 0.71)[0]; h3 = np.modf(h2 * 7.77 + 0.13)[0]
        dd = np.sqrt((fx - (h2 - 0.5) * 0.6) ** 2 + (fy - (h3 - 0.5) * 0.6) ** 2)
        sz = 0.10 + 0.10 * h3 if l == 2 else 0.035 + 0.05 * h3
        tw = 0.55 + 0.45 * np.sin(T * (1.5 + 3.0 * h2) + h * 50.0)
        m = np.clip(1 - dd / sz, 0, 1); m = m * m if l == 2 else m ** 3
        tint = gold + (np.array([1.0, 0.92, 0.75]) - gold) * h3[..., None]
        dust += (m * (h > 0.62) * tw)[..., None] * tint * (0.30 if l == 2 else 0.9)
    add += dust * dust_amt * (np.exp(-r * r * 2.2) * 0.85 + 0.15)[..., None]
    if layer == 0:
        vv = np.sqrt(((u - 0.5) * asp) ** 2 + (v - 0.5) ** 2)
        t_ = np.clip((vv - 0.25) / 0.75, 0, 1); vig = 0.62 + 0.38 * t_ * t_ * (3 - 2 * t_)
        scrim = bg * 0.55 * vig
        add += gold * (np.exp(-(r * r) / max(rad * rad * 1.4, 1e-4)) * glow * 0.55)[..., None]
        sdx = (u - c[0]) * asp / max(rad * 0.95, 1e-4); sdy = (v - (c[1] + rad * 0.92)) / max(rad * 0.11, 1e-4)
        sh = np.exp(-(sdx ** 2 + sdy ** 2)) * 0.6 * itemA
        scrim = 1 - (1 - scrim) * (1 - sh)
    else:
        an = np.arctan2(dxy_y, dxy_x)
        rays = np.clip(0.5 + 0.5 * np.sin(an * 13 + T * 0.5), 0, 1) ** 6 * 0.6 + np.clip(0.5 + 0.5 * np.sin(an * 21 - T * 0.8 + 1.3), 0, 1) ** 10 * 0.4
        fall = np.exp(-r / max(rad * 1.6, 1e-3)); core = np.exp(-r * r / max(rad * rad * 0.12, 1e-5))
        streak = np.exp(-np.abs(dxy_y) / max(rad * 0.018, 1e-4)) * np.exp(-np.abs(dxy_x) / max(rad * 2.2, 1e-3))
        add += (gold * (rays * fall * 0.55)[..., None] + np.array([1, 0.9, 0.75]) * (core * 0.8)[..., None] + np.array([1, 0.8, 0.55]) * (streak * 0.55)[..., None]) * burst
        rr = rad * (0.6 + 2.2 * ring)
        add += gold * (np.exp(-((r - rr) / max(rad * 0.035, 1e-4)) ** 2) * (1 - ring) * (ring > 0.001) * 0.7)[..., None]
        dk = np.sqrt(((u - dock[0]) * asp) ** 2 + (v - dock[1]) ** 2)
        add += gold * ((np.exp(-((dk - dockR) / 0.004) ** 2) * 0.9 + np.exp(-dk * dk / 0.0009) * 0.6) * dock[2])[..., None]
    la = add.max(-1); a = np.clip(np.maximum(scrim, la), 0, 1)
    colr = np.where(a[..., None] > 1e-4, add / np.maximum(a, 1e-4)[..., None], 0)
    return np.clip(colr, 0, 1), a


def over(dst, col_, a): return dst * (1 - a[..., None]) + col_ * a[..., None]


def paste(dst, img, x, y, alpha=1.0, tint=None):
    """alpha-blend an RGBA (linear) image at (x, y), clipped."""
    h, w = img.shape[:2]; H_, W_ = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W_, x + w), min(H_, y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x]
    rgb = sub[..., :3] if tint is None else (sub[..., :3] * np.array(tint))
    dst[y0:y1, x0:x1] = over(dst[y0:y1, x0:x1], rgb, sub[..., 3] * alpha)


def resize(img, w, h):
    ys = (np.arange(h) * img.shape[0] / h).astype(int); xs = (np.arange(w) * img.shape[1] / w).astype(int)
    return img[ys][:, xs]


# ---- frames
CW, CH = 800, 450
bg_full = load(BG)[..., :3]
bg_img = to_lin(resize(bg_full, CW, CH))
beats = [(0.06, 'anticipation 0.06 s'), (0.30, 'reveal 0.30 s'), (0.47, 'peak 0.47 s (burst, hit-stop)'),
         (1.05, 'title 1.05 s'), (1.60, 'hold 1.60 s (shine done)'), (2.05, 'exit 2.05 s (flies to the dock)')]
title_img, title_cols = render_text(TITLE, 'title')
line_img, _ = render_text(LINE, 'line')
key_img, _ = render_text(KEY, 'key')
cells = []
for i, (tl, label) in enumerate(beats):
    c = curves(tl)
    item = render_item(c['yaw'], i)
    frame = blur(bg_img.copy(), c['bg'], CH)
    itemH = CH * 0.56 * c['S']; half = itemH / 2
    cx = CW * (0.5 + (0.93 - 0.5) * c['ein']); cy = CH * (0.45 + (0.88 - 0.45) * c['ein']) - CH * 0.10 * math.sin(math.pi * c['ein'])
    rad = half / CH; cen = (cx / CW, cy / CH)
    col_, a = screen(CH, CW, 0, tl, cen, rad, c['bg'], c['bg'] * (0.6 + 0.8 * c['burst']), 0, 0, c['bg'], c['itemA'], (0, 0, 0), 0.02)
    frame = over(frame, col_, a)
    n = max(2, int(itemH))
    it_ = resize(item, n, n).copy(); it_[..., :3] = to_lin(it_[..., :3])
    it_[..., :3] = it_[..., :3] + (np.array([1.0, 0.86, 0.62]) - it_[..., :3]) * min(1, c['burst']) * 0.35
    paste(frame, it_, int(cx - n / 2), int(cy - n / 2), c['itemA'])
    col_, a = screen(CH, CW, 1, tl, cen, rad, 0, 0, c['burst'], c['ring'], c['bg'], 0, (0.93, 0.88, c['dockA']), c['dockR'])
    frame = over(frame, col_, a)
    # title: width 34 % of the screen, per-letter slide + shine
    tw = int(CW * 0.34); th = int(title_img.shape[0] * tw / title_img.shape[1])
    tim = resize(title_img, tw, th); scale = tw / title_img.shape[1]
    tx0, ty = int(CW * 0.5 - tw / 2), int(CH * 0.755)
    nL = len(TITLE)
    for k, (a0, a1) in enumerate(title_cols):
        ai = sat((tl - 0.55 - 0.035 * k) / 0.25); dy = int((1 - ai) ** 3 * 22 * CH / 1080)
        sx = (tl - 1.0) / 0.6; sh = math.exp(-(((k / max(1, nL - 1)) - sx) * 5) ** 2)
        g = tuple(gc + (sc_ - gc) * sh for gc, sc_ in zip((1.0, 0.72, 0.30), (1.0, 0.95, 0.80)))
        c0, c1 = max(0, int(a0 * scale) - 1), min(tw, int(a1 * scale) + 2)
        piece = tim[:, c0:c1]
        paste(frame, piece * np.array([0, 0, 0, 1]) + np.array([0, 0, 0, 0]), tx0 + c0 + 2, ty + dy + 2, ai * c['ta'] * 0.55)
        paste(frame, piece, tx0 + c0, ty + dy, ai * c['ta'], tint=tuple(to_lin(np.array(g))))
    # how-to line with a key cap
    lh = max(6, int(th * 0.45)); lw = int(line_img.shape[1] * lh / line_img.shape[0])
    lim = resize(line_img, lw, lh); kh = int(lh * 1.45); gap = int(12 * CH / 1080)
    kx = int(CW * 0.5 - (kh + gap + lw) / 2); ky = ty + th + int(16 * CH / 1080)
    if c['la'] > 0.01:
        b_ = max(1, int(2 * CH / 1080))
        frame[ky - b_:ky + kh + b_, kx - b_:kx + kh + b_] = over(frame[ky - b_:ky + kh + b_, kx - b_:kx + kh + b_], to_lin(np.array([1.0, 0.72, 0.30])), np.full((kh + 2 * b_, kh + 2 * b_), 0.9 * c['la']))
        frame[ky:ky + kh, kx:kx + kh] = over(frame[ky:ky + kh, kx:kx + kh], to_lin(np.array([0.07, 0.055, 0.04])), np.full((kh, kh), 0.88 * c['la']))
        kim = resize(key_img, int(key_img.shape[1] * lh / key_img.shape[0]), lh)
        paste(frame, kim, kx + (kh - kim.shape[1]) // 2, ky + (kh - lh) // 2, c['la'], tint=tuple(to_lin(np.array([1.0, 0.95, 0.80]))))
        paste(frame, lim, kx + kh + gap, ky + (kh - lh) // 2, c['la'], tint=tuple(to_lin(np.array([0.92, 0.86, 0.74]))))
    cells.append((to_srgb(frame), label))

# ---- 3 x 2 sheet with labels (labels drawn as a dark band; the text goes in the caption)
GAP = 8
sheet = np.full((CH * 2 + GAP * 3, CW * 3 + GAP * 4, 3), 0.08, np.float32)
for i, (f, _l) in enumerate(cells):
    r_, c_ = divmod(i, 3)
    y, x = GAP + r_ * (CH + GAP), GAP + c_ * (CW + GAP)
    sheet[y:y + CH, x:x + CW] = f
    # beat number as small gold ticks in the top-left corner (1..6)
    for k in range(i + 1): sheet[y + 10:y + 22, x + 10 + k * 8:x + 14 + k * 8] = (1.0, 0.72, 0.30)
img = bpy.data.images.new('sheet', sheet.shape[1], sheet.shape[0], alpha=True)
sheet = np.nan_to_num(sheet); print('SHEET stats', float(sheet.min()), float(sheet.max()), float(sheet.mean()))
rgba = np.concatenate([sheet[::-1], np.ones(sheet.shape[:2] + (1,), np.float32)], -1)
img.pixels.foreach_set(rgba.ravel()); img.filepath_raw = OUTP; img.file_format = 'PNG'
img.save()
print('PREVIEW', OUTP, [l for _f, l in cells])

# #424: bundle icons for Vesna's list, her EQUIPMENT doll and the inventory doll (i9 helper, 2026-11-02).
#   python make_bundle_icons.py  ->  ../textures/T_VT_Bundles_424.png (1024 x 256, four 256 px cells, transparent)
# Cells: 0 Helm (empty: no helmet art yet, the game draws the atlas helm glyph), 1 Torso, 2 Gauntlets, 3 Legs.
# Built from the front frame (frame 0) of the real Cycles turntables in assets/tga/VesnaTrade/textures, so the bundle
# icons have the same light, metal and gold trim as the piece icons Vesna already shows.
import os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'tga', 'VesnaTrade', 'textures'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'textures', 'T_VT_Bundles_424.png'))
CELL = 256


def front(art):
    """frame 0 (512 x 340) of T_VT_Turn_<art>, cropped to its alpha."""
    im = Image.open(os.path.join(TEX, 'T_VT_Turn_%s.png' % art)).convert('RGBA').crop((0, 0, 512, 340))
    return im.crop(im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox())


def split(im):
    """an L/R pair rendered side by side -> (left, right), split at the emptiest column in the middle third."""
    a = im.getchannel('A'); w, h = im.size
    cols = [sum(a.crop((x, 0, x + 1, h)).histogram()[k] * k for k in range(256)) for x in range(w)]
    lo, hi = w // 3, 2 * w // 3
    cut = min(range(lo, hi), key=lambda x: cols[x])
    l, r = im.crop((0, 0, cut, h)), im.crop((cut, 0, w, h))
    return [p.crop(p.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()) for p in (l, r)]


def fit(im, w=None, h=None):
    s = min((w or 1e9) / im.width, (h or 1e9) / im.height)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def paste(cell, im, cx, cy):
    cell.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def shadowed(cell):
    """soft contact shadow under the group so stacked plates read as one set."""
    a = cell.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.45))
    sh = Image.new('RGBA', cell.size, (0, 0, 0, 0)); sh.putalpha(a)
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 3)); out.alpha_composite(cell)
    return out


def torso():
    c = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    chest = fit(front('Chest'), 170, 214)
    pl, pr = [fit(p, 78, 78) for p in split(front('Shoulders'))]
    ul, ur = [fit(p, 46, 70) for p in split(front('UpperArms'))]
    cx, top = CELL / 2, (CELL - chest.height) / 2 + 6
    paste(c, ul, cx - chest.width / 2 - 8, top + 92)          # rerebraces hang under the pauldrons, behind
    paste(c, ur, cx + chest.width / 2 + 8, top + 92)
    paste(c, chest, cx, top + chest.height / 2)
    paste(c, pl, cx - chest.width / 2 + 10, top + 30)
    paste(c, pr, cx + chest.width / 2 - 10, top + 30)
    return shadowed(c)


def gauntlets():
    c = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    vl, vr = [fit(p, 70, 150) for p in split(front('Forearms'))]
    g = fit(front('Gauntlets'), 130, 190)
    paste(c, vl, 72, 92); paste(c, vr, 184, 92)
    paste(c, g, 128, 150)
    return shadowed(c)


def legs():
    c = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    fauld = fit(front('Waist'), 150, 86)
    tl, tr = [fit(p, 60, 70) for p in split(front('Thighs'))]
    sl, sr = [fit(p, 50, 74) for p in split(front('Shins'))]
    boots = fit(front('Boots'), 156, 58)                     # the sabaton pair stays as rendered (the toes overlap)
    lx, rx = 128 - 32, 128 + 32
    paste(c, boots, 128, 222)
    paste(c, sl, lx, 166); paste(c, sr, rx, 166)
    paste(c, tl, lx, 110); paste(c, tr, rx, 110)
    paste(c, fauld, 128, 50)
    return shadowed(c)


sheet = Image.new('RGBA', (CELL * 4, CELL), (0, 0, 0, 0))
for k, fn in ((1, torso), (2, gauntlets), (3, legs)):
    sheet.alpha_composite(fn(), (k * CELL, 0))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sheet.save(OUT)
prev = Image.new('RGBA', sheet.size, (30, 28, 26, 255)); prev.alpha_composite(sheet)
prev.convert('RGB').save(os.path.join(os.path.dirname(OUT), '..', 'renders', 'bundle_icons_424.png'))
print('wrote', OUT)

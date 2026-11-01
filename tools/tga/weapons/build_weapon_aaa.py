# #397 weapon kit AAA polish (TGA, 2026-11-01): checkking's generator (assets/checkking/Weapons/source/build_weapon.py)
# run with the AAA recipe (handoffs/weapon-kit-aaa/RESEARCH.md). Nothing of the live kit is edited: this patches a copy
# of the source text in memory and writes NEW assets with the SAME names, pivots and Z-along axis.
#   blender -b --factory-startup -P build_weapon_aaa.py -- <weapon> <out_root> [tex=2048] [samples=32]
# Patches:
#   1. materials -> aaa_mats.mat (forge scale vs ground edge, grind streaks, stoned bevel, hand zones, binary metal)
#   2. loft(): a secondary edge bevel (grind line ~3.5 mm from the edge) on every blade section; point attributes
#      gf (|x| / half-width) on blades and gf (eye -> edge) + fg = 1 on forged axe / halberd / mace heads
#   3. after the bake: ORM metallic thresholded to 0 / 1, metal border texels lifted to the KB floor (150 sRGB luminance),
#      the haft ZMIN set for the butt dirt; the preview render is replaced by lookdev_weapon.py (locked rig).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'checkking', 'Weapons', 'source', 'build_weapon.py'))
s = open(SRC, encoding='utf-8').read()
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['arming_sword', os.getcwd()]
GRIPS_BY = {'arming_sword': [(-0.06, 0.045)], 'longsword': [(-0.17, 0.052)], 'war_axe': [(-0.30, -0.14)],
            'flanged_mace': [(-0.30, -0.15)], 'halberd': [(-0.16, 0.12), (-0.82, -0.52)], 'war_hammer': [(-0.33, -0.18)],
            'falchion': [(-0.06, 0.045)], 'viking_sword': [(-0.06, 0.045)], 'messer': [(-0.06, 0.045)]}
GRIPS = GRIPS_BY.get(argv[0], [(-0.16, 0.12), (-0.8, -0.5)])

def rep(a, b, count=1):
    global s
    if s.count(a) < count: raise SystemExit('build_weapon.py changed, patch not found: ' + a[:70])
    s = s.replace(a, b)

# 1. materials
i0 = s.index('def mat(name, base, rough, metal, kind):'); i1 = s.index('STEEL = mat(')
s = s[:i0] + "exec(open(%r, encoding='utf-8').read())\n\n" % os.path.join(HERE, 'aaa_mats.py') + s[i1:]
# 2. secondary edge bevel + attributes on blades
rep("""        ring.append([(xo - w, -e, z), (xo - fw, -t, z), (xo, -t + d, z), (xo + fw, -t, z), (xo + w, -e, z),
                     (xo + w, e, z), (xo + fw, t, z), (xo, t - d, z), (xo - fw, t, z), (xo - w, e, z)])""",
    """        gb = min(0.0035, (w - fw) * 0.45); tb = e + (t - e) * 0.42                      # AAA: stoned secondary bevel (grind line)
        ring.append([(xo - w, -e, z), (xo - w + gb, -tb, z), (xo - fw, -t, z), (xo, -t + d, z), (xo + fw, -t, z), (xo + w - gb, -tb, z), (xo + w, -e, z),
                     (xo + w, e, z), (xo + w - gb, tb, z), (xo + fw, t, z), (xo, t - d, z), (xo - fw, t, z), (xo - w + gb, tb, z), (xo - w, e, z)])
        across.append([abs(v[0] - xo) / max(w, 1e-6) for v in ring[-1]])""")
rep("    ring = []\n    for s in stations:", "    ring = []; across = []\n    for s in stations:")
rep("    verts = [v for r in ring for v in r]; faces = []\n    n = 10", "    verts = [v for r in ring for v in r]; faces = []\n    n = 14")
rep("    o = mesh_obj(name, verts, faces, m)\n    bev = o.modifiers.new('wn', 'WEIGHTED_NORMAL')",
    "    o = mesh_obj(name, verts, faces, m); point_attr(o, 'gf', [a for r in across for a in r]); point_attr(o, 'fg', [0.0] * len(verts))\n    bev = o.modifiers.new('wn', 'WEIGHTED_NORMAL')")
rep("    o = mesh_obj(name, verts, faces, m)\n    wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL')",
    "    o = mesh_obj(name, verts, faces, m); point_attr(o, 'gf', [i / NX for i in range(NX + 1) for _ in range(n)]); point_attr(o, 'fg', [1.0] * len(verts))\n    wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL')")
rep("def mesh_obj(name, verts, faces, m, smooth=True):",
    "def point_attr(o, nm, vals):\n    a = o.data.attributes.new(nm, 'FLOAT', 'POINT')\n    for k, v in enumerate(vals[:len(a.data)]): a.data[k].value = v\n\ndef mesh_obj(name, verts, faces, m, smooth=True):")
# 3. bake post-process + no preview render (the locked lookdev renders it)
rep("b_ = px(bc); b_[..., 3] = 1; ", """mt_ = px(mt)[..., 0] > 0.5
b_ = px(bc); b_[..., 3] = 1
lin_ = np.where(b_[..., :3] <= 0.04045, b_[..., :3] / 12.92, ((b_[..., :3] + 0.055) / 1.055) ** 2.4)   # byte image: sRGB-encoded
Y_ = lin_ @ np.array([0.2126, 0.7152, 0.0722]); low_ = mt_ & (Y_ > 1e-4) & (Y_ < 0.32)
lin_[low_] = np.clip(lin_[low_] * (0.32 / Y_[low_])[:, None], 0, 1)
b_[..., :3] = np.where(lin_ <= 0.0031308, lin_ * 12.92, 1.055 * lin_ ** (1 / 2.4) - 0.055); print('LIFTED', int(low_.sum()))
""")
rep("orm = np.dstack([px(aoi)[..., 0], px(rg)[..., 0], px(mt)[..., 0], np.ones((TEX, TEX))])",
    "orm = np.dstack([px(aoi)[..., 0], px(rg)[..., 0], mt_.astype(np.float32), np.ones((TEX, TEX))])")
# ZMIN for the butt dirt: set right before the bake (after the join)
rep("sc.cycles.samples = SPP\n", "sc.cycles.samples = SPP\n_zmin = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)\nfor _m in obj.data.materials:\n    if _m and 'ZMIN' in _m.node_tree.nodes: _m.node_tree.nodes['ZMIN'].outputs[0].default_value = _zmin\n")
i2 = s.index('zs = [ (obj.matrix_world @ v.co).z for v in obj.data.vertices ]')
s = s[:i2] + "print('WEAPON DONE', NAME, 'tris', tris)\n"
exec(compile(s, SRC + ' (AAA patched)', 'exec'))

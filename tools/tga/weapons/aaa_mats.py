# #397 weapon kit AAA (TGA): the layered material recipe (handoffs/weapon-kit-aaa/RESEARCH.md §3). Exec'd by
# build_weapon_aaa.py inside Blender in place of checkking's mat(); same signature mat(name, base, rough, metal, kind).
# Masks every material shares:
#   edge   = convex curvature (pointiness)            -> polish / worn-through
#   cav    = 1 - AO                                    -> grime, rust, tarnish in junctions and fuller bottoms
#   gf     = mesh attribute: blades |x|/half-width (1 = edge), heads 0 at the eye -> 1 at the cutting edge
#   fg     = mesh attribute: 1 on forged heads (forge scale body + ground edge strip), 0 on ground blades
#   grip   = object-Z windows from GRIPS (hand zones)  -> darker, smoother wood / leather, polished iron
#   butt   = object Z near the bottom (ZMIN value node, set after the build) -> dirt on polearm butts
# Metallic is strictly 0 / 1: every non-metal layer (scale, rust, tarnish) switches the colour hard.
import bpy, math
GRIPS = globals().get('GRIPS', [(-0.15, 0.10)])

def _srgb(c): return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 for x in c)

class _T:
    def __init__(s, m):
        s.nt = m.node_tree; s.N = s.nt.nodes; s.L = s.nt.links
    def node(s, t, **kv):
        n = s.N.new(t)
        for k, v in kv.items(): setattr(n, k, v)
        return n
    def link(s, a, b):
        if isinstance(a, (int, float)): b.default_value = a
        elif isinstance(a, tuple): b.default_value = a if len(a) == 4 else (*a, 1.0)
        else: s.L.new(a, b)
    def math(s, op, a, b=0.0, clamp=False):
        n = s.node('ShaderNodeMath', operation=op, use_clamp=clamp); s.link(a, n.inputs[0]); s.link(b, n.inputs[1]); return n.outputs[0]
    def ramp(s, x, lo, hi):
        n = s.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP'); s.link(x, n.inputs['Value'])
        n.inputs['From Min'].default_value = lo; n.inputs['From Max'].default_value = hi; return n.outputs['Result']
    def mixc(s, f, a, b):
        n = s.node('ShaderNodeMix', data_type='RGBA'); s.link(f, n.inputs[0]); s.link(a, n.inputs[6]); s.link(b, n.inputs[7]); return n.outputs[2]
    def mixf(s, f, a, b):
        n = s.node('ShaderNodeMix', data_type='FLOAT'); s.link(f, n.inputs[0]); s.link(a, n.inputs[2]); s.link(b, n.inputs[3]); return n.outputs[0]
    def noise(s, scale, detail=4.0, rough=0.55, dist=0.0, out='Fac'):
        mp = s.node('ShaderNodeMapping'); s.L.new(s.tc.outputs['Object'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = scale
        n = s.node('ShaderNodeTexNoise'); s.L.new(mp.outputs['Vector'], n.inputs['Vector'])
        n.inputs['Scale'].default_value = 1.0; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist; return n.outputs[out]
    def vor(s, scale, feature='F1'):
        mp = s.node('ShaderNodeMapping'); s.L.new(s.tc.outputs['Object'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = scale
        n = s.node('ShaderNodeTexVoronoi', feature=feature); s.L.new(mp.outputs['Vector'], n.inputs['Vector']); n.inputs['Scale'].default_value = 1.0
        return n.outputs['Distance']
    def attr(s, name):
        n = s.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name); return n.outputs['Fac']

def mat(name, base, rough, metal, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = _T(m); b = t.N['Principled BSDF']
    t.tc = t.node('ShaderNodeTexCoord'); geo = t.node('ShaderNodeNewGeometry')
    sep = t.node('ShaderNodeSeparateXYZ'); t.L.new(t.tc.outputs['Object'], sep.inputs[0]); Z = sep.outputs['Z']
    edge = t.ramp(geo.outputs['Pointiness'], 0.515, 0.58)
    ao = t.node('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.008; ao.samples = 16
    cav = t.ramp(t.math('SUBTRACT', 1.0, ao.outputs['AO']), 0.28, 0.7)
    gf, fg = t.attr('gf'), t.attr('fg')
    grip = None
    for z0, z1 in GRIPS:
        w = t.math('MULTIPLY', t.ramp(Z, z0 - 0.01, z0 + 0.025), t.ramp(t.math('MULTIPLY', Z, -1.0), -(z1 + 0.01), -(z1 - 0.025)))
        grip = w if grip is None else t.math('MAXIMUM', grip, w)
    zmin = t.node('ShaderNodeValue', label='ZMIN', name='ZMIN'); zmin.outputs[0].default_value = -1.0
    butt = t.ramp(t.math('MULTIPLY', t.math('SUBTRACT', Z, zmin.outputs[0]), -1.0), -0.16, -0.02)     # 1 at the very bottom
    bump_h = 0.0
    if kind in ('steel', 'iron'):
        streak = t.noise((150.0, 150.0, 1.2), 8.0, 0.62)                         # grind lines run ALONG the weapon (Z)
        smudge = t.noise((6.0, 6.0, 6.0), 3.0, 0.5)
        scratch = t.ramp(t.noise((420.0, 420.0, 9.0), 2.0, 0.5), 0.71, 0.735)  # fine scratch lines, mostly along the length
        n_sc = t.noise((22.0, 22.0, 22.0), 5.0, 0.62, dist=0.4)
        if kind == 'steel':
            bevel = t.math('MULTIPLY', t.ramp(gf, 0.78, 0.84), t.math('SUBTRACT', 1.0, fg))      # stoned edge band of a blade
            ground = t.ramp(t.math('ADD', gf, t.math('MULTIPLY', n_sc, 0.10)), 0.74, 0.77)       # forged head: ground strip, wavy boundary
            scale = t.math('MULTIPLY', t.math('MULTIPLY', fg, t.math('SUBTRACT', 1.0, ground)), t.ramp(n_sc, 0.30, 0.36))
            bevel = t.math('MAXIMUM', bevel, t.math('MULTIPLY', fg, ground))
            c_base = (0.56, 0.565, 0.578); r0, r1 = 0.16, 0.30
        else:
            bevel = t.math('MULTIPLY', fg, t.ramp(t.math('ADD', gf, t.math('MULTIPLY', n_sc, 0.10)), 0.74, 0.77))
            scale = t.math('MULTIPLY', t.math('SUBTRACT', 1.0, bevel), t.ramp(n_sc, 0.42, 0.47))  # forged fittings: scale patches
            scale = t.math('MULTIPLY', scale, t.math('SUBTRACT', 1.0, t.math('MULTIPLY', edge, 0.9)))   # worn through on high points
            scale = t.math('MAXIMUM', scale, t.math('MULTIPLY', fg, t.math('SUBTRACT', 1.0, bevel)))
            c_base = (0.52, 0.522, 0.53); r0, r1 = 0.30, 0.50
        rust = t.math('MULTIPLY', t.ramp(cav, 0.6, 0.8), t.ramp(t.noise((90.0, 90.0, 90.0), 4.0, 0.6), 0.56, 0.6))
        pit_w = 0.8 if kind == 'iron' else t.math('MULTIPLY', fg, 0.8)                     # pin-head pitting: forged parts only, never on a ground blade
        rust = t.math('MAXIMUM', rust, t.math('MULTIPLY', t.ramp(t.noise((260.0, 260.0, 260.0), 3.0, 0.6), 0.69, 0.71), pit_w))
        nm = t.math('GREATER_THAN', t.math('MAXIMUM', scale, rust), 0.5)
        is_rust = t.math('GREATER_THAN', rust, 0.5)
        mcol = t.mixc(t.math('MULTIPLY', smudge, 0.5), c_base, tuple(x * 0.95 for x in c_base))
        mcol = t.mixc(t.math('MAXIMUM', bevel, t.math('MULTIPLY', edge, 0.6)), mcol, (0.60, 0.602, 0.61))
        scol = t.mixc(n_sc, (0.033, 0.035, 0.041), (0.048, 0.047, 0.05))                      # blue-black forge scale
        rcol = t.mixc(n_sc, _srgb((118, 68, 35)), _srgb((96, 58, 34)))
        col = t.mixc(nm, mcol, t.mixc(is_rust, scol, rcol))
        rm = t.math('ADD', r0, t.math('MULTIPLY', streak, r1 - r0)); rm = t.math('ADD', rm, t.math('MULTIPLY', smudge, 0.08))
        rm = t.mixf(t.math('MULTIPLY', scratch, 0.7), rm, t.math('ADD', rm, 0.1))
        rm = t.mixf(bevel, rm, t.math('ADD', 0.10, t.math('MULTIPLY', streak, 0.06)))
        rm = t.mixf(t.math('MULTIPLY', grip, 0.6), rm, 0.2)
        rn = t.mixf(is_rust, t.math('ADD', 0.58, t.math('MULTIPLY', n_sc, 0.17)), 1.0)
        rgh = t.mixf(nm, rm, rn)
        met = t.math('SUBTRACT', 1.0, nm)
        pits = t.ramp(t.vor((60.0, 60.0, 60.0)), 0.0, 0.25)                                   # hammer dimples under the scale
        bump_h = t.math('ADD', t.math('MULTIPLY', streak, 0.25), t.math('MULTIPLY', t.math('MULTIPLY', scale, pits), 0.8))
        bump_h = t.math('SUBTRACT', bump_h, t.math('MULTIPLY', rust, 0.6))
    elif kind == 'bronze':
        n1 = t.noise((40.0, 40.0, 40.0), 5.0, 0.6)
        tar = t.math('GREATER_THAN', t.math('ADD', cav, t.math('MULTIPLY', n1, 0.35)), 0.72)
        mcol = t.mixc(edge, (0.82, 0.70, 0.38), (0.88, 0.76, 0.42))
        col = t.mixc(tar, mcol, (0.11, 0.09, 0.055)); met = t.math('SUBTRACT', 1.0, tar)
        rgh = t.mixf(tar, t.mixf(edge, t.math('ADD', 0.28, t.math('MULTIPLY', n1, 0.1)), 0.2), 0.72)
        bump_h = t.math('MULTIPLY', n1, 0.2)
    elif kind == 'wood':
        oak = 'Oak' in name
        c0 = _srgb((100, 72, 50)) if oak else _srgb((128, 96, 64))                              # oiled ash: amber-brown (linseed darkens)
        grain = t.noise((70.0, 70.0, 0.8), 6.0, 0.62, dist=1.2)                                # long grain along the haft
        pores = t.ramp(t.noise((700.0, 700.0, 25.0), 2.0, 0.6), 0.6, 0.7)
        rays = t.ramp(t.noise((45.0, 45.0, 5.0), 3.0, 0.6), 0.66, 0.7) if oak else 0.0
        col = t.mixc(grain, tuple(x * 0.78 for x in c0), c0)
        col = t.mixc(t.math('MULTIPLY', pores, 0.55 if oak else 0.35), col, tuple(x * 0.55 for x in c0))
        if oak: col = t.mixc(t.math('MULTIPLY', rays, 0.5), col, tuple(min(1, x * 1.3) for x in c0))
        col = t.mixc(t.math('MULTIPLY', grip, 0.85), col, tuple(x * 0.68 for x in c0))         # hands: oil + sweat
        col = t.mixc(t.math('MULTIPLY', butt, 0.8), col, _srgb((70, 56, 44)))                  # dirt at the butt
        col = t.mixc(t.math('MULTIPLY', cav, 0.6), col, tuple(x * 0.6 for x in c0))
        col = t.mixc(t.math('MULTIPLY', edge, 0.5), col, tuple(min(1, x * 1.15) for x in c0))  # dings and rubbed arrises
        met = 0.0
        rgh = t.math('ADD', 0.56, t.math('MULTIPLY', grain, 0.12)); rgh = t.math('ADD', rgh, t.math('MULTIPLY', pores, 0.08))
        rgh = t.mixf(grip, rgh, 0.38); rgh = t.mixf(butt, rgh, 0.82)
        bump_h = t.math('ADD', t.math('MULTIPLY', grain, 0.3), t.math('MULTIPLY', pores, -0.5))
    else:                                                                                       # leather grip
        c0 = _srgb((66, 44, 30))
        crack = t.ramp(t.noise((160.0, 160.0, 160.0), 6.0, 0.65, dist=1.5), 0.62, 0.7)
        n1 = t.noise((30.0, 30.0, 30.0), 4.0, 0.6)
        col = t.mixc(n1, tuple(x * 0.88 for x in c0), c0)
        col = t.mixc(t.math('MULTIPLY', grip, 0.9), col, _srgb((46, 31, 22)))                   # palm: sweat-darkened, polished
        col = t.mixc(t.math('MULTIPLY', cav, 0.7), col, _srgb((38, 27, 20)))
        col = t.mixc(t.math('MULTIPLY', crack, 0.6), col, _srgb((84, 64, 48)))                  # dry cracks at the wrap edges
        met = 0.0
        rgh = t.math('ADD', 0.66, t.math('MULTIPLY', n1, 0.08)); rgh = t.mixf(grip, rgh, 0.42); rgh = t.mixf(crack, rgh, 0.85)
        bump_h = t.math('ADD', t.math('MULTIPLY', crack, -0.6), t.math('MULTIPLY', n1, 0.2))
    t.link(col, b.inputs['Base Color']); t.link(rgh, b.inputs['Roughness']); t.link(met, b.inputs['Metallic'])
    bm = t.node('ShaderNodeBump'); bm.inputs['Distance'].default_value = 0.0004; bm.inputs['Strength'].default_value = 0.35
    t.link(bump_h, bm.inputs['Height']); t.L.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m

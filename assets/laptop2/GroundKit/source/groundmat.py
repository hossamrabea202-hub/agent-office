# Ground tile materials. Everything is seamless: colour noise is sampled on a 4D torus of the UV (Blender's noise can take
# a 4D input, and a torus wraps both ways), the masks come from the heightfield's attributes (h, id, gap, wet, veg, glow).
# Knowledge-base standard: non-metal albedo 30-240 sRGB, roughness at three scales, wet darkening per Lagarde, moss and
# puddles only where water would sit. The height goes out through OUT_EM (baked as T_Ground_X_Height).
import bpy
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange
from shieldmat import _sep, _mul_col
from swordmat import _finish

def _attr(nt, name): return _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs['Fac']
def _uv(nt): return _n(nt, 'ShaderNodeTexCoord').outputs['UV']
def _torus(nt, uv, reps=1.0):
    """4D torus coordinate of the uv so any noise on it tiles; reps = how many times the noise pattern repeats per tile."""
    s = _sep(nt, uv)
    def ang(x):
        return _math(nt, 'MULTIPLY', x, 6.2831853 * reps)
    au, av = ang(s[0]), ang(s[1])
    cu, su = _math(nt, 'COSINE', au), _math(nt, 'SINE', au); cv, sv = _math(nt, 'COSINE', av), _math(nt, 'SINE', av)
    cb = _n(nt, 'ShaderNodeCombineXYZ'); nt.links.new(cu, cb.inputs[0]); nt.links.new(su, cb.inputs[1]); nt.links.new(cv, cb.inputs[2])
    return cb.outputs[0], sv
def _tn(nt, uv, reps, scale, detail=4, rough=0.55, dist=0.0):
    """seamless noise: Noise Texture in 4D on the torus; scale sets the feature size (bigger = finer)."""
    vec, w = _torus(nt, uv, reps)
    n = _n(nt, 'ShaderNodeTexNoise', noise_dimensions='4D', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    nt.links.new(vec, n.inputs['Vector']); nt.links.new(w, n.inputs['W']); return n.outputs['Fac']

def _common(nt):
    uv = _uv(nt); g = _n(nt, 'ShaderNodeNewGeometry')
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', samples=16, only_local=True); ao.inputs['Distance'].default_value = 0.05
    cav = _math(nt, 'SUBTRACT', 1.0, ao.outputs['AO'], True)
    return uv, g, cav, ao.outputs['AO'], _attr(nt, 'ht'), _attr(nt, 'sid'), _attr(nt, 'gap'), _attr(nt, 'wet'), _attr(nt, 'veg'), _attr(nt, 'glow')

def _wet(nt, col, rg, wet):
    """Lagarde wetness for porous ground: darken per channel, gloss up, damped."""
    wm = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); _link(nt, wet, wm.inputs[0]); nt.links.new(col, wm.inputs[6])
    wm.inputs[7].default_value = (0.55, 0.45, 0.35, 1)
    rg = _mix_f(nt, wet, rg, 0.22)
    return wm.outputs[2], rg

def _moss(nt, uv, col, rg, veg, strength=1.0):
    mc = _mix_col(nt, _tn(nt, uv, 1, 90, 3, 0.6), (0.06, 0.11, 0.03), (0.14, 0.20, 0.05))
    mc = _mix_col(nt, _math(nt, 'MULTIPLY', _tn(nt, uv, 1, 400, 2, 0.6), 0.3), mc, (0.20, 0.24, 0.08))        # lit tips
    m = _math(nt, 'MULTIPLY', veg, strength)
    return _mix_col(nt, m, col, mc), _mix_f(nt, m, rg, 0.86)

def cobble(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv, g, cav, ao, h, sid, gap, wet, veg, glow = _common(nt)
    # stone: each cobble its own tone (grey, tan, blue-grey), speckle, polished tops from feet, dirt in the joints
    tone = _mix_col(nt, sid, (0.30, 0.28, 0.25), (0.42, 0.37, 0.30))
    tone = _mix_col(nt, _maprange(nt, sid, 0.6, 0.62), tone, (0.27, 0.29, 0.32))
    tone = _mix_col(nt, _maprange(nt, sid, 0.85, 0.87), tone, (0.46, 0.42, 0.34))
    spk = _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 700, 2, 0.6), 0.55, 0.9), 0.35)
    col = _mix_col(nt, spk, tone, (0.16, 0.15, 0.14))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 30, 4, 0.6), 0.3, 0.7), 0.3), col, _mul_col(nt, col, 0.7))     # mottle
    top = _maprange(nt, h, 0.55, 0.9)                                                          # worn tops
    col = _mix_col(nt, _math(nt, 'MULTIPLY', top, 0.35), col, (0.50, 0.47, 0.42))
    earth = _mix_col(nt, _tn(nt, uv, 1, 60, 4, 0.6), (0.11, 0.085, 0.06), (0.20, 0.16, 0.11))
    col = _mix_col(nt, gap, col, earth)
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.6), col, (0.05, 0.04, 0.03))
    col, rg = _moss(nt, uv, col, _mix_f(nt, top, 0.82, 0.55), veg, 0.9)
    rg = _mix_f(nt, gap, rg, 0.95)
    rg = _mix_f(nt, _maprange(nt, _tn(nt, uv, 1, 250, 2, 0.6), 0.3, 0.7), _math(nt, 'SUBTRACT', rg, 0.05), _math(nt, 'ADD', rg, 0.05))
    col, rg = _wet(nt, col, rg, wet)
    _finish(nt, col, rg, 0.0, ao, _mix_col(nt, h, (0, 0, 0), (1, 1, 1)))

def mud(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv, g, cav, ao, h, sid, gap, wet, veg, glow = _common(nt)
    col = _mix_col(nt, _tn(nt, uv, 1, 8, 5, 0.6), (0.10, 0.075, 0.05), (0.21, 0.16, 0.11))                   # wet-brown earth
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 120, 3, 0.6), 0.55, 0.85), 0.4), col, (0.28, 0.23, 0.17))   # dry crumbs on the ridges
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, h, 0.7, 1.0), 0.5), col, (0.30, 0.25, 0.19))     # drier, paler high spots
    col = _mix_col(nt, _math(nt, 'MULTIPLY', gap, 0.5), col, (0.08, 0.06, 0.04))                              # pressed boot prints darker
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.5), col, (0.05, 0.04, 0.03))
    rg = _mix_f(nt, _tn(nt, uv, 1, 40, 3, 0.6), 0.75, 0.92); rg = _mix_f(nt, _maprange(nt, h, 0.7, 1.0), rg, 0.95)
    col, rg = _moss(nt, uv, col, rg, veg, 0.8)
    col, rg = _wet(nt, col, rg, wet)
    _finish(nt, col, rg, 0.0, ao, _mix_col(nt, h, (0, 0, 0), (1, 1, 1)))

def grassdirt(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv, g, cav, ao, h, sid, gap, wet, veg, glow = _common(nt)
    dirt = _mix_col(nt, _tn(nt, uv, 1, 10, 5, 0.6), (0.17, 0.13, 0.09), (0.30, 0.24, 0.17))                  # dry path earth
    dirt = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 300, 2, 0.6), 0.5, 0.9), 0.3), dirt, (0.38, 0.33, 0.25))
    peb = _mix_col(nt, sid, (0.30, 0.29, 0.27), (0.45, 0.40, 0.33))
    col = _mix_col(nt, gap, dirt, peb)
    grass = _mix_col(nt, _tn(nt, uv, 1, 150, 3, 0.6), (0.08, 0.14, 0.03), (0.16, 0.24, 0.06))
    grass = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 20, 3, 0.5), 0.55, 0.8), 0.5), grass, (0.26, 0.24, 0.10))   # dry straw tips
    col = _mix_col(nt, veg, col, grass)
    col = _mix_col(nt, _maprange(nt, cav, 0.25, 0.8, 0, 0.5), col, (0.05, 0.05, 0.03))
    rg = _mix_f(nt, veg, _mix_f(nt, _tn(nt, uv, 1, 60, 3, 0.6), 0.85, 0.95), 0.80)
    rg = _mix_f(nt, gap, rg, 0.7)
    col, rg = _wet(nt, col, rg, wet)
    _finish(nt, col, rg, 0.0, ao, _mix_col(nt, h, (0, 0, 0), (1, 1, 1)))

def corrupt(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv, g, cav, ao, h, sid, gap, wet, veg, glow = _common(nt)
    crust = _mix_col(nt, _tn(nt, uv, 1, 12, 5, 0.6), (0.09, 0.06, 0.07), (0.19, 0.12, 0.13))                 # dead purple-brown crust
    crust = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 200, 3, 0.6), 0.55, 0.9), 0.4), crust, (0.26, 0.20, 0.19))   # ash
    flesh = _mix_col(nt, _tn(nt, uv, 1, 40, 4, 0.55), (0.30, 0.10, 0.13), (0.48, 0.17, 0.20))
    col = _mix_col(nt, wet, crust, flesh)                                                                     # veins and bulbs are raw flesh
    col = _mix_col(nt, _math(nt, 'MULTIPLY', gap, 0.8), col, (0.06, 0.015, 0.03))                              # the cracks, dark then glowing
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.5), col, (0.04, 0.02, 0.03))
    rg = _mix_f(nt, wet, _mix_f(nt, _tn(nt, uv, 1, 50, 3, 0.6), 0.75, 0.9), 0.30)
    em = _mix_col(nt, _maprange(nt, glow, 0.1, 1.0), (0, 0, 0), (0.95, 0.12, 0.45))
    em = _mix_col(nt, _maprange(nt, _math(nt, 'MULTIPLY', gap, glow), 0.5, 1.0), em, (1.0, 0.35, 0.15))
    # the height still has to come out somewhere: the realm tile packs it into the emissive's alpha-less blue channel? No:
    # keep the emissive as the glow and bake the height into a separate pass via the 'HT' key (see bake_shield GRD).
    _finish(nt, col, rg, 0.0, ao, em)
    rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_HT'; nt.links.new(_mix_col(nt, h, (0, 0, 0), (1, 1, 1)), rr.inputs[0])

def cobblemud(m):
    """the transition strip: cobble look where 'gap'/'sid' live (left), mud where 'wet' is high (right); blended by u."""
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv, g, cav, ao, h, sid, gap, wet, veg, glow = _common(nt)
    s = _sep(nt, uv); bl = _maprange(nt, _math(nt, 'ADD', s[0], _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', _tn(nt, uv, 1, 4, 4, 0.6), 0.5), 0.24)), 0.3, 0.75)
    tone = _mix_col(nt, sid, (0.30, 0.28, 0.25), (0.42, 0.37, 0.30)); tone = _mix_col(nt, _maprange(nt, sid, 0.6, 0.62), tone, (0.27, 0.29, 0.32))
    stone = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 700, 2, 0.6), 0.55, 0.9), 0.35), tone, (0.16, 0.15, 0.14))
    stone = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, h, 0.55, 0.9), 0.35), stone, (0.50, 0.47, 0.42))
    earth = _mix_col(nt, _tn(nt, uv, 1, 60, 4, 0.6), (0.11, 0.085, 0.06), (0.20, 0.16, 0.11))
    cob = _mix_col(nt, gap, stone, earth)
    mudc = _mix_col(nt, _tn(nt, uv, 1, 8, 5, 0.6), (0.10, 0.075, 0.05), (0.21, 0.16, 0.11))
    mudc = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _tn(nt, uv, 1, 120, 3, 0.6), 0.55, 0.85), 0.4), mudc, (0.28, 0.23, 0.17))
    col = _mix_col(nt, bl, cob, mudc)
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.6), col, (0.05, 0.04, 0.03))
    col, rg = _moss(nt, uv, col, _mix_f(nt, bl, _mix_f(nt, gap, 0.6, 0.95), 0.85), veg, 0.8)
    col, rg = _wet(nt, col, rg, wet)
    _finish(nt, col, rg, 0.0, ao, _mix_col(nt, h, (0, 0, 0), (1, 1, 1)))

KIND = {'Ground': None}
def build_all():
    import os
    f = {'Cobble': cobble, 'Mud': mud, 'GrassDirt': grassdirt, 'Corrupt': corrupt, 'CobbleMud': cobblemud}[os.environ.get('VARIANT', 'Cobble')]
    for m in bpy.data.materials:
        if m.name.split('.')[0] == 'Ground': f(m)

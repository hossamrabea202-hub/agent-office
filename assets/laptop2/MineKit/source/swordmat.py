# Procedural PBR for Emberoath's high poly. Same contract as shieldmat (OUT_BC / OUT_RG / OUT_MT / OUT_AO reroutes,
# BSDF + EMIT), plus OUT_EM: the emissive colour baked into T_Emberoath_Emissive (runes and the amber's inner fire).
#   Blade    pattern-welded steel: folded-layer waves, a mirror-bright edge bevel, lengthwise polish, glowing runes
#   Gold     gilded bronze guard and pommel (matlib gold)
#   Leather  dark grip leather (matlib leather)
#   Gem      amber cabochons: deep honey colour, glassy, a warm glow in the middle
import os, json
import bpy
import matlib
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _img, _mul_col
D = os.path.dirname(os.path.abspath(__file__))
EMBER = (1.0, 0.28, 0.03)

def _finish(nt, col, rg, mt, ao, em=None):
    for key, sock in (('BC', col), ('RG', rg), ('MT', mt), ('AO', ao), ('EM', em if em is not None else (0.0, 0.0, 0.0))):
        rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_' + key; rr.label = key
        if isinstance(sock, tuple):
            c = _n(nt, 'ShaderNodeRGB'); c.outputs[0].default_value = (*sock, 1); nt.links.new(c.outputs[0], rr.inputs[0])
        elif isinstance(sock, (int, float)):
            v = _n(nt, 'ShaderNodeValue'); v.outputs[0].default_value = sock; nt.links.new(v.outputs[0], rr.inputs[0])
        else:
            nt.links.new(sock, rr.inputs[0])
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled'); bsdf.name = 'BSDF'
    nt.links.new(nt.nodes['OUT_BC'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(nt.nodes['OUT_RG'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(nt.nodes['OUT_MT'].outputs[0], bsdf.inputs['Metallic'])
    nt.links.new(nt.nodes['OUT_EM'].outputs[0], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = 1.6
    em_ = _n(nt, 'ShaderNodeEmission'); em_.name = 'EMIT'
    out = _n(nt, 'ShaderNodeOutputMaterial'); out.name = 'OUT'
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])

def _add_em_reroute(nt):
    rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_EM'
    c = _n(nt, 'ShaderNodeRGB'); c.outputs[0].default_value = (0, 0, 0, 1); nt.links.new(c.outputs[0], rr.inputs[0])

def blade(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0006); cav, ao = _cav(nt, 0.002)
    s = _sep(nt, co)
    # folded layers: bands that run along the blade and ripple, as if ground through a twisted billet
    lay = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=380.0, in_Distortion=6.0, in_Detail=5.0, in_Detail_Roughness=0.65)
    nt.links.new(_vec(nt, _math(nt, 'ADD', s[0], _math(nt, 'MULTIPLY', _noise(nt, _scale(nt, co, 1, 1, 0.3), 30, 3, 0.5), 0.004)), s[1], _math(nt, 'MULTIPLY', s[2], 0.08)), lay.inputs['Vector'])
    lm = _maprange(nt, lay.outputs['Fac'], 0.3, 0.8)
    col = _mix_col(nt, lm, (0.44, 0.45, 0.47), (0.62, 0.63, 0.65))
    # the edge bevel is ground and polished brighter; the fuller is a touch darker and duller
    xe = _math(nt, 'ABSOLUTE', s[0])
    col = _mix_col(nt, _maprange(nt, edge, 0.02, 0.12, 0, 0.6), col, (0.78, 0.78, 0.80))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.7), col, (0.18, 0.18, 0.19))
    # a faint heat-blue bloom around the runes: the blade remembers the forge
    mj = json.load(open(os.path.join(D, 'masks_sword', 'masks.json')))
    uv = _vec(nt, _maprange(nt, s[0], mj['x0'], mj['x1']), _maprange(nt, s[2], mj['z0'], mj['z1']), 0.0)
    rn = _img(nt, 'runes', uv, 'masks_sword')
    inside = _math(nt, 'MULTIPLY', _maprange(nt, xe, 0.008, 0.006), _math(nt, 'MULTIPLY', _maprange(nt, s[2], 0.07, 0.09), _maprange(nt, s[2], 0.39, 0.37)))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', inside, 0.35), col, (0.22, 0.26, 0.42))
    col = _mix_col(nt, rn[0], col, (0.55, 0.18, 0.04))                               # the rune grooves: ember-hot inlay
    pol = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.02), 900, 3, 0.6)
    rg = _mix_f(nt, pol, 0.10, 0.20)
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', lm, 0.5), rg, 0.30)
    rg = _mix_f(nt, _maprange(nt, edge, 0.02, 0.12), rg, 0.09)
    rg = _mix_f(nt, rn[0], rg, 0.45)
    mt = _mix_f(nt, rn[0], 1.0, 0.0)
    em = _mix_col(nt, rn[0], (0, 0, 0), EMBER)
    _finish(nt, col, rg, mt, ao, em)

def gem(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); cav, ao = _cav(nt, 0.002)
    fr = _n(nt, 'ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.35
    core = _math(nt, 'SUBTRACT', 1.0, fr.outputs['Facing'], True)                       # facing the viewer = the deep middle
    inc = _noise(nt, co, 900, 4, 0.6)                                                   # tiny inclusions
    col = _mix_col(nt, core, (0.30, 0.09, 0.01), (0.72, 0.33, 0.03))
    col = _mix_col(nt, _maprange(nt, inc, 0.62, 0.72, 0, 0.4), col, (0.15, 0.05, 0.01))
    rg = _mix_f(nt, inc, 0.03, 0.08)
    em = _mix_col(nt, _math(nt, 'MULTIPLY', core, 0.22), (0, 0, 0), EMBER)
    _finish(nt, col, rg, 0.0, ao, em)

def gold(m):
    matlib.build(m, 'gold'); _add_em_reroute(m.node_tree)
def leather(m):
    matlib.LEATHER_TONE = 1.1; matlib.build(m, 'leather'); _add_em_reroute(m.node_tree)

KIND = {'Blade': blade, 'Gem': gem, 'Gold': gold, 'Leather': leather}
def build_all():
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

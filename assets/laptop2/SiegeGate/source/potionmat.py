# Procedural PBR for the potions' baked parts (same contract as shieldmat/swordmat). Glass and liquid are not here:
# they get translucent UE materials (M_PotionGlass, M_PotionLiquid) made by the import script.
#   Cork      porous bark cork, darker pores and a stained band where it meets the glass
#   WaxRed / WaxGreen   sealing wax: deep colour, glossy, lighter where it's thin at the edges and drips
#   Twine     two-ply jute (woodmat rope)
#   Tag       old paper with foxing, hand-inked symbol and script (masks_potion/tag_<variant>.png)
import os, json, math
import bpy
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _img, _mul_col, _finish
D = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get('VARIANT', 'Health')

def cork(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0006); cav, ao = _cav(nt, 0.002)
    pores = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=900.0); nt.links.new(co, pores.inputs['Vector'])
    pm = _maprange(nt, pores.outputs['Distance'], 0.0, 0.25, 1.0, 0.0)
    col = _mix_col(nt, _noise(nt, co, 120, 5, 0.6), (0.36, 0.24, 0.13), (0.52, 0.37, 0.22))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', pm, 0.7), col, (0.12, 0.07, 0.035))
    s = _sep(nt, co)
    col = _mix_col(nt, _maprange(nt, s[2], 0.098, 0.104, 0.5, 0.0), col, (0.20, 0.12, 0.07))      # stained by the potion
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.6), col, (0.08, 0.05, 0.03))
    rg = _mix_f(nt, pm, 0.75, 0.92)
    _finish(nt, col, rg, 0.0, ao)

def wax(m, deep, light):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0008); cav, ao = _cav(nt, 0.0015)
    n = _noise(nt, co, 60, 4, 0.55)
    col = _mix_col(nt, n, deep, tuple(c * 1.15 for c in deep))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.15), 0.6), col, light)      # thin edges glow lighter
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.7), col, tuple(c * 0.4 for c in deep))
    dust = _maprange(nt, _noise(nt, co, 25, 4, 0.6), 0.55, 0.75, 0, 0.25)
    col = _mix_col(nt, dust, col, (0.25, 0.22, 0.18))
    rg = _mix_f(nt, n, 0.22, 0.34); rg = _mix_f(nt, dust, rg, 0.6)
    _finish(nt, col, rg, 0.0, ao)

def tag(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0003); cav, ao = _cav(nt, 0.001)
    j = json.load(open(os.path.join(D, 'masks_potion', 'tag_%s.json' % VAR)))
    tuv = _sep(nt, _n(nt, 'ShaderNodeTexCoord').outputs['UV'])              # the tag's own UV: x = U * w / 2, y = -V * h
    uv = _vec(nt, _maprange(nt, tuv[0], -j['w'] / 2, j['w'] / 2), _maprange(nt, tuv[1], 0.0, -j['h']), 0.0)
    ink = _img(nt, 'tag_%s' % VAR, uv, 'masks_potion')
    front = _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='front').outputs['Fac']
    fib = _noise(nt, co, 1400, 3, 0.6)
    col = _mix_col(nt, fib, (0.55, 0.47, 0.33), (0.66, 0.58, 0.43))
    fox = _maprange(nt, _noise(nt, co, 220, 4, 0.6), 0.58, 0.72, 0, 0.6)
    col = _mix_col(nt, fox, col, (0.36, 0.24, 0.12))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.2), 0.6), col, (0.28, 0.20, 0.12))   # handled edges
    inkc = (0.06, 0.012, 0.01) if VAR == 'Health' else (0.025, 0.05, 0.02)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', ink[0], front), col, inkc)
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', ink[0], front), 0.86, 0.55)
    _finish(nt, col, rg, 0.0, ao)

def twine(m):
    """jute twine (not woodmat's rope: that one adds the barricade kit's mud splash near the ground)."""
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); cav, ao = _cav(nt, 0.001)
    st = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=900.0, in_Distortion=2.0, in_Detail=4.0)
    nt.links.new(co, st.inputs['Vector'])
    fuzz = _noise(nt, co, 2500, 4, 0.7)
    col = _mix_col(nt, fuzz, (0.36, 0.28, 0.16), (0.52, 0.42, 0.27))
    col = _mix_col(nt, _maprange(nt, st.outputs['Fac'], 0.6, 1.0, 0, 0.5), col, (0.18, 0.13, 0.07))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.6), col, (0.08, 0.06, 0.035))
    rg = _mix_f(nt, fuzz, 0.86, 0.96)
    _finish(nt, col, rg, 0.0, ao)

KIND = {'Cork': cork, 'WaxRed': lambda m: wax(m, (0.32, 0.02, 0.015), (0.62, 0.10, 0.06)),
        'WaxGreen': lambda m: wax(m, (0.04, 0.16, 0.05), (0.18, 0.42, 0.14)), 'Tag': tag, 'Twine': twine}
def build_all():
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

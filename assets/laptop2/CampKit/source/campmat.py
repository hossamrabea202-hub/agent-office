# Materials for the camp kit: shared Plank / Iron / Bark / WoodCut / Rope / Coal / Shaft / Twine, plus Stone (fieldstone
# with lichen, moss low down, soot from a 'soot' attribute), Mortar and Hay (straw). Knowledge-base standard: non-metal
# albedo 30-240 sRGB, roughness varied at three scales, wear in physical order (weathering -> lichen -> moss -> soot).
import bpy
import woodmat, shieldmat, gatemat, potionmat, ballistamat
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col
from swordmat import _finish

def _attr(nt, name): return _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs['Fac']

def stone(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.003); cav, ao = _cav(nt, 0.02)
    g = _n(nt, 'ShaderNodeNewGeometry'); nz = _sep(nt, g.outputs['Normal'])[2]
    s = _sep(nt, co); z = s[2]
    # fieldstone: grey-brown body, mineral speckle, a few darker veins
    tone = _noise(nt, co, 5, 4, 0.55)
    col = _mix_col(nt, tone, (0.26, 0.24, 0.21), (0.42, 0.38, 0.33))                      # 135-165 sRGB
    spk = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=420.0); nt.links.new(co, spk.inputs['Vector'])
    sp = _maprange(nt, spk.outputs['Distance'], 0.0, 0.5)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', sp, 0.35), col, (0.16, 0.15, 0.14))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, co, 900, 2, 0.6), 0.6, 0.9), 0.3), col, (0.55, 0.52, 0.48))   # quartz glints
    vein = _maprange(nt, _noise(nt, _scale(nt, co, 1.0, 1.0, 4.0), 7, 5, 0.7, 0.4), 0.70, 0.78, 0, 0.6)
    col = _mix_col(nt, vein, col, (0.19, 0.17, 0.15))
    # weathering: pale sun-bleached top faces, grime in the cavities
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, nz, 0.3, 0.9), 0.3), col, (0.48, 0.46, 0.42))
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.7, 0, 0.75), col, (0.07, 0.06, 0.05))
    # lichen: crusty grey-green patches on the upper, outer faces
    lic = _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, co, 9, 5, 0.65), 0.58, 0.70), _maprange(nt, nz, -0.2, 0.5))
    licc = _mix_col(nt, _noise(nt, co, 120, 3, 0.6), (0.30, 0.33, 0.18), (0.42, 0.44, 0.30))
    col = _mix_col(nt, lic, col, licc)
    # moss where it stays damp: low down, in the cracks
    mos = _math(nt, 'MULTIPLY', _maprange(nt, _math(nt, 'ADD', z, _math(nt, 'MULTIPLY', _noise(nt, co, 6, 3, 0.5), 0.15)), 0.30, 0.02),
                _maprange(nt, _noise(nt, co, 30, 4, 0.6), 0.45, 0.65))
    mos = _math(nt, 'MAXIMUM', mos, _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.4, 0.8), _maprange(nt, _noise(nt, co, 20, 3, 0.6), 0.5, 0.7)))
    col = _mix_col(nt, mos, col, _mix_col(nt, _noise(nt, co, 200, 3, 0.6), (0.06, 0.11, 0.03), (0.12, 0.19, 0.05)))
    # soot (campfire stones: the inner faces), last
    soot = _math(nt, 'MULTIPLY', _attr(nt, 'soot'), _maprange(nt, _noise(nt, co, 14, 4, 0.6), 0.25, 0.75))
    col = _mix_col(nt, soot, col, (0.025, 0.023, 0.022))
    rg = _mix_f(nt, tone, 0.72, 0.88); rg = _mix_f(nt, _math(nt, 'MULTIPLY', sp, 0.5), rg, 0.95)
    rg = _mix_f(nt, lic, rg, 0.92); rg = _mix_f(nt, mos, rg, 0.80); rg = _mix_f(nt, soot, rg, 0.75)
    rg = _mix_f(nt, _maprange(nt, _noise(nt, co, 300, 2, 0.6), 0.3, 0.7), _math(nt, 'SUBTRACT', rg, 0.04), _math(nt, 'ADD', rg, 0.04))
    _finish(nt, col, rg, 0.0, ao)

def mortar(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); cav, ao = _cav(nt, 0.015); s = _sep(nt, co); z = s[2]
    col = _mix_col(nt, _noise(nt, co, 40, 4, 0.6), (0.33, 0.31, 0.28), (0.46, 0.44, 0.40))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, co, 600, 2, 0.6), 0.55, 0.9), 0.4), col, (0.22, 0.20, 0.18))   # sand grains
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.7, 0, 0.6), col, (0.08, 0.07, 0.06))
    damp = _math(nt, 'MULTIPLY', _maprange(nt, z, 0.35, 0.05), _maprange(nt, _noise(nt, co, 5, 3, 0.5), 0.3, 0.7))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', damp, 0.6), col, (0.09, 0.09, 0.07))
    rg = _mix_f(nt, damp, 0.95, 0.7)
    _finish(nt, col, rg, 0.0, ao)

def hay(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _n(nt, 'ShaderNodeTexCoord').outputs['UV']; cav, ao = _cav(nt, 0.015)
    g = _n(nt, 'ShaderNodeNewGeometry'); nz = _sep(nt, g.outputs['Normal'])[2]
    # straw: bundled stalks along u (wave bands, 2-3 mm), each stalk its own tone
    st = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=360.0, in_Distortion=3.0, in_Detail=3.0, in_Detail_Scale=2.0); nt.links.new(uv, st.inputs['Vector'])
    stalk = _maprange(nt, st.outputs['Fac'], 0.15, 0.85)
    tone = _noise(nt, _scale(nt, co, 1.0, 1.0, 1.0), 90, 3, 0.6)
    col = _mix_col(nt, tone, (0.50, 0.36, 0.13), (0.72, 0.56, 0.24))                       # straw 0.35-0.6 linear
    col = _mix_col(nt, _math(nt, 'MULTIPLY', stalk, 0.55), col, _mul_col(nt, col, 0.45))   # the gaps between stalks
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, co, 3, 3, 0.5), 0.55, 0.75), 0.4), col, (0.36, 0.30, 0.16))   # greener, newer patches
    # weathering: grey on the top, damp dark at the bottom, dust in the hollows
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, nz, 0.3, 0.9), _maprange(nt, _noise(nt, co, 10, 4, 0.6), 0.3, 0.8)), col, (0.40, 0.37, 0.30))
    s = _sep(nt, co); z = s[2]
    damp = _math(nt, 'MULTIPLY', _maprange(nt, z, 0.12, 0.0), _maprange(nt, _noise(nt, co, 8, 3, 0.5), 0.3, 0.7))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', damp, 0.7), col, (0.12, 0.09, 0.04))
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.6), col, (0.14, 0.10, 0.05))
    rg = _mix_f(nt, stalk, 0.92, 0.78); rg = _mix_f(nt, damp, rg, 0.62)
    _finish(nt, col, rg, 0.0, ao)

def canvas(m):
    """market awning: woven cotton duck, red and cream stripes along u, sun-faded on top, dirt and mildew at the hem."""
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _n(nt, 'ShaderNodeTexCoord').outputs['UV']; cav, ao = _cav(nt, 0.01)
    g = _n(nt, 'ShaderNodeNewGeometry'); nz = _sep(nt, g.outputs['Normal'])[2]
    w1 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=900.0, in_Distortion=0.3, in_Detail=1.0); nt.links.new(uv, w1.inputs['Vector'])
    w2 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=900.0, in_Distortion=0.3, in_Detail=1.0); nt.links.new(uv, w2.inputs['Vector'])
    weave = _math(nt, 'MULTIPLY', _maprange(nt, w1.outputs['Fac'], 0.3, 0.7), _maprange(nt, w2.outputs['Fac'], 0.3, 0.7))
    stripe = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', wave_profile='SAW', in_Scale=3.3, in_Distortion=0.0, in_Detail=0.0); nt.links.new(uv, stripe.inputs['Vector'])
    st = _maprange(nt, stripe.outputs['Fac'], 0.48, 0.52)
    cream = _mix_col(nt, _noise(nt, co, 20, 3, 0.6), (0.62, 0.56, 0.44), (0.72, 0.66, 0.52))
    red = _mix_col(nt, _noise(nt, co, 20, 3, 0.6), (0.38, 0.07, 0.05), (0.50, 0.11, 0.07))
    col = _mix_col(nt, st, cream, red)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', weave, 0.35), col, _mul_col(nt, col, 0.7))
    fade = _math(nt, 'MULTIPLY', _maprange(nt, nz, 0.2, 0.9), _maprange(nt, _noise(nt, co, 2, 3, 0.5), 0.3, 0.8))      # sun on the top
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fade, 0.45), col, (0.66, 0.62, 0.55))
    z = _sep(nt, co)[2]
    hem = _math(nt, 'MULTIPLY', _maprange(nt, z, 2.25, 2.05), _maprange(nt, _noise(nt, co, 9, 4, 0.6), 0.35, 0.7))   # mildew / dirt low on the valance
    col = _mix_col(nt, _math(nt, 'MULTIPLY', hem, 0.7), col, (0.12, 0.11, 0.08))
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.5), col, _mul_col(nt, col, 0.5))
    rg = _mix_f(nt, weave, 0.88, 0.72); rg = _mix_f(nt, hem, rg, 0.65)
    _finish(nt, col, rg, 0.0, ao)

KIND = {'Plank': gatemat.plank, 'Iron': shieldmat.iron, 'Coal': ballistamat.coal, 'Shaft': ballistamat.shaft, 'Twine': potionmat.twine,
        'Stone': stone, 'Mortar': mortar, 'Hay': hay, 'Canvas': canvas}
def build_all():
    woodmat.build_all()
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

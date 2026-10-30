# Materials for the barracks props: shared Plank (gatemat), Iron (shieldmat, calibrated), Bark/WoodCut/Rope (woodmat),
# plus Burlap, Twine and Grain. Knowledge-base standard.
import bpy
import woodmat, shieldmat, gatemat, potionmat
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col, _finish

def burlap(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _n(nt, 'ShaderNodeTexCoord').outputs['UV']; edge = _edge(nt, 0.002); cav, ao = _cav(nt, 0.01)
    g = _n(nt, 'ShaderNodeNewGeometry'); nz = _sep(nt, g.outputs['Normal'])[2]
    # the weave: two crossed band sets in UV space (~2 mm threads), fuzz on top
    w1 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=520.0, in_Distortion=0.6, in_Detail=2.0); nt.links.new(uv, w1.inputs['Vector'])
    w2 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=520.0, in_Distortion=0.6, in_Detail=2.0); nt.links.new(uv, w2.inputs['Vector'])
    weave = _math(nt, 'MULTIPLY', _maprange(nt, w1.outputs['Fac'], 0.2, 0.8), _maprange(nt, w2.outputs['Fac'], 0.2, 0.8))
    fuzz = _noise(nt, co, 900, 3, 0.7)
    tone = _noise(nt, co, 6, 4, 0.55)
    col = _mix_col(nt, tone, (0.24, 0.19, 0.12), (0.34, 0.28, 0.18))        # jute: ~0.2-0.3 linear
    col = _mix_col(nt, _math(nt, 'MULTIPLY', weave, 0.5), col, _mul_col(nt, col, 0.6))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fuzz, 0.15), col, (0.45, 0.40, 0.30))
    # stains: damp bottom, a dark spill, dust on top faces, grime in folds
    s = _sep(nt, co); z = s[2]
    damp = _maprange(nt, _math(nt, 'ADD', z, _math(nt, 'MULTIPLY', _noise(nt, co, 4, 3, 0.5), 0.12)), 0.22, 0.02)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', damp, 0.7), col, (0.09, 0.07, 0.045))
    spill = _maprange(nt, _noise(nt, co, 2.5, 4, 0.6), 0.60, 0.80)       # a soft old stain, not a hole
    col = _mix_col(nt, _math(nt, 'MULTIPLY', spill, 0.35), col, (0.15, 0.11, 0.065))
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.7, 0, 0.7), col, (0.05, 0.04, 0.025))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, nz, 0.5, 0.95), 0.35), col, (0.33, 0.30, 0.25))
    rg = _mix_f(nt, fuzz, 0.82, 0.95); rg = _mix_f(nt, damp, rg, 0.62)
    _finish(nt, col, rg, 0.0, ao)

def grain(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); cav, ao = _cav(nt, 0.004)
    vor = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=700.0); nt.links.new(co, vor.inputs['Vector'])
    k = _maprange(nt, vor.outputs['Distance'], 0.0, 0.45)
    col = _mix_col(nt, _noise(nt, co, 300, 3, 0.6), (0.40, 0.28, 0.12), (0.55, 0.40, 0.18))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', k, 0.6), col, (0.20, 0.13, 0.05))
    rg = _mix_f(nt, k, 0.45, 0.7)
    _finish(nt, col, rg, 0.0, ao)

KIND = {'Plank': gatemat.plank, 'Iron': shieldmat.iron, 'Burlap': burlap, 'Grain': grain, 'Twine': potionmat.twine}
def build_all():
    woodmat.build_all()
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

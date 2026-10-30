# Materials for the fire-spear launcher: shared Plank / Iron / Bark / WoodCut / Rope / Shaft, plus Coal (glowing embers,
# 'glow' attribute -> EM) and the spear's pitch-soaked tow wrap ('wrap' attribute on the Shaft).
import bpy
import woodmat, shieldmat, gatemat, swordmat
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col
from swordmat import _finish

def _attr(nt, name): return _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs['Fac']

def coal(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.002); cav, ao = _cav(nt, 0.01); glow = _attr(nt, 'glow')
    crack = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', in_Scale=90.0); nt.links.new(co, crack.inputs['Vector'])
    cm = _maprange(nt, crack.outputs['Distance'], 0.0, 0.03, 1.0, 0.0)
    ash = _maprange(nt, _noise(nt, co, 25, 4, 0.6), 0.5, 0.75)
    col = _mix_col(nt, ash, (0.022, 0.020, 0.019), (0.14, 0.135, 0.13))          # charcoal 0.02, ash grey on top
    col = _mix_col(nt, _math(nt, 'MULTIPLY', cm, 0.6), col, (0.012, 0.01, 0.01))
    heat = _math(nt, 'MULTIPLY', glow, _math(nt, 'MAXIMUM', cm, _maprange(nt, _noise(nt, co, 40, 3, 0.6), 0.55, 0.8)))
    heat = _math(nt, 'MULTIPLY', heat, _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', ash, 0.6), True))
    em = _mix_col(nt, _maprange(nt, heat, 0.0, 1.0), (0, 0, 0), (1.0, 0.30, 0.05))
    em = _mix_col(nt, _maprange(nt, heat, 0.75, 1.0), em, (1.0, 0.65, 0.25))     # the hottest cores go yellow
    rg = _mix_f(nt, ash, 0.85, 0.95)
    _finish(nt, col, rg, 0.0, ao, em)

def shaft(m):
    shieldmat.shaft(m); nt = m.node_tree
    # the tow wrap: hemp fibre soaked black with pitch, glossy and lumpy, over the 'wrap' section
    wrap = _attr(nt, 'wrap'); co = _co(nt)
    fib = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', in_Scale=260.0, in_Distortion=2.0, in_Detail=3.0); nt.links.new(co, fib.inputs['Vector'])
    pitch = _mix_col(nt, _maprange(nt, fib.outputs['Fac'], 0.3, 0.9), (0.020, 0.016, 0.012), (0.045, 0.035, 0.022))
    pitch = _mix_col(nt, _maprange(nt, _noise(nt, co, 60, 3, 0.6), 0.55, 0.75, 0, 0.4), pitch, (0.09, 0.07, 0.04))   # dry tow showing through
    bc = nt.nodes['OUT_BC']; src = bc.inputs[0].links[0].from_socket
    col = _mix_col(nt, wrap, src, pitch); nt.links.new(col, bc.inputs[0])
    rgn = nt.nodes['OUT_RG']; rsrc = rgn.inputs[0].links[0].from_socket
    rg = _mix_f(nt, wrap, rsrc, _mix_f(nt, _noise(nt, co, 200, 3, 0.6), 0.28, 0.45)); nt.links.new(rg, rgn.inputs[0])

KIND = {'Plank': gatemat.plank, 'Iron': shieldmat.iron, 'Coal': coal, 'Shaft': shaft}
def build_all():
    woodmat.build_all()
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

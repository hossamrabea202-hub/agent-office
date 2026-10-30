# Procedural PBR for the siege barricade kit (#29): weathered pine bark, axe-cut sapwood, fire-hardened char, hemp rope.
# Same contract as the Obsidian kit's materials.py: every material exposes OUT_BC / OUT_RG / OUT_MT / OUT_AO reroutes, a
# BSDF for previews and an EMIT node, and set_output() routes one channel for the EMIT bakes.
# Texture space is the mesh UV, which build_kit.py lays out in real-world metres: u = around the log, v = along it,
# so the grain and bark fissures always run along each log.
import bpy
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge, _cavity, set_output

def _uv(nt):
    m = _n(nt, 'ShaderNodeTexCoord').outputs['UV']
    return m
def _stretch(nt, co, su, sv):
    """scale UV (u around, v along) -> 3D vector for the noise nodes, stretched along the grain."""
    sep = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(co, sep.inputs[0])
    com = _n(nt, 'ShaderNodeCombineXYZ')
    _link(nt, _math(nt, 'MULTIPLY', sep.outputs[0], su), com.inputs[0])
    _link(nt, _math(nt, 'MULTIPLY', sep.outputs[1], sv), com.inputs[1])
    return com.outputs[0]
def _noise(nt, vec, scale, detail=6, rough=0.55, dist=0.0):
    t = _n(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    nt.links.new(vec, t.inputs['Vector']); return t.outputs['Fac']
def _attr(nt, name):
    a = _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name); return a.outputs['Fac']
def _worldz(nt):
    g = _n(nt, 'ShaderNodeNewGeometry'); s = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(g.outputs['Position'], s.inputs[0]); return s.outputs[2]

def _char(nt, co, col, rg, tip):
    """fire-hardened ends: charcoal with alligator cracks, ash grey on the raised scales, a soft scorched fringe."""
    vor = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', in_Scale=55.0)
    nt.links.new(_stretch(nt, co, 1.0, 0.6), vor.inputs['Vector'])
    crack = _maprange(nt, vor.outputs['Distance'], 0.0, 0.06, 1.0, 0.0)
    full = _maprange(nt, tip, 0.35, 0.75)
    fringe = _maprange(nt, tip, 0.05, 0.45)
    ash = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 18, 5, 0.6), 0.55, 0.75, 0, 0.5)
    charcol = _mix_col(nt, ash, (0.018, 0.016, 0.015), (0.10, 0.095, 0.09))
    charcol = _mix_col(nt, crack, charcol, (0.006, 0.005, 0.005))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fringe, 0.65), col, (0.035, 0.024, 0.016))   # scorched, not yet charcoal
    col = _mix_col(nt, full, col, charcol)
    rg = _mix_f(nt, full, rg, _mix_f(nt, crack, 0.78, 0.55))     # char scales are a little satin, cracks glossier
    return col, rg

def _bark(nt, co, edge, cav, z):
    grain = _stretch(nt, co, 1.0, 0.18)
    plates = _noise(nt, grain, 22, 8, 0.62, 0.6)
    tone = _noise(nt, _stretch(nt, co, 1, 0.4), 2.5, 3, 0.5)
    col = _mix_col(nt, tone, (0.052, 0.038, 0.028), (0.100, 0.074, 0.054))
    # weathering: the raised plates bleach silver-grey, the fissures stay dark and damp
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.2), 0.6), col, (0.17, 0.15, 0.13))
    col = _mix_col(nt, _maprange(nt, plates, 0.55, 0.75, 0, 0.45), col, (0.17, 0.155, 0.135))
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.7), col, (0.018, 0.013, 0.010))
    # lichen: grey-green crusts in patches, more on the lower half
    lich = _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 6, 6, 0.65), 0.62, 0.72),
                 _maprange(nt, z, 2.6, 0.6))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', lich, 0.8), col, (0.22, 0.24, 0.18))
    rg = _mix_f(nt, plates, 0.82, 0.93)
    rg = _mix_f(nt, lich, rg, 0.96)
    return col, rg

def _cutwood(nt, co, edge, cav, z):
    grainv = _stretch(nt, co, 1.0, 0.04)
    rings = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=26.0, in_Distortion=3.0, in_Detail=6.0)
    nt.links.new(grainv, rings.inputs['Vector'])
    fib = _noise(nt, _stretch(nt, co, 1.0, 0.05), 160, 4, 0.6)
    col = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.3, 0.8), (0.36, 0.27, 0.17), (0.47, 0.36, 0.23))
    # old cuts go grey; the axe facets catch dirt in the fibre
    col = _mix_col(nt, _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 4, 3, 0.5), 0.35, 0.65, 0.25, 0.7), col, (0.27, 0.25, 0.22))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fib, 0.35), col, (0.14, 0.10, 0.06))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6), col, (0.05, 0.035, 0.022))
    rg = _mix_f(nt, fib, 0.72, 0.86)
    return col, rg

def _rope(nt, co, edge, cav, z):
    strands = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=110.0, in_Distortion=1.5, in_Detail=4.0)
    nt.links.new(_stretch(nt, co, 1.0, 1.0), strands.inputs['Vector'])
    fuzz = _noise(nt, _stretch(nt, co, 1, 1), 240, 4, 0.7)
    col = _mix_col(nt, fuzz, (0.25, 0.20, 0.13), (0.38, 0.31, 0.20))
    col = _mix_col(nt, _maprange(nt, strands.outputs['Fac'], 0.6, 1.0, 0, 0.6), col, (0.10, 0.08, 0.05))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6), col, (0.05, 0.04, 0.025))
    rg = _mix_f(nt, fuzz, 0.88, 0.97)
    return col, rg

def build(m, kind):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _uv(nt)
    edge = _edge(nt, 0.004)
    cav, ao = _cavity(nt, 0.03)
    tip = _attr(nt, 'tip')
    z = _worldz(nt)
    mud = _maprange(nt, z, 0.6, 0.0)                          # splash line: wet earth up the first 0.6 m
    mudn = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 9, 5, 0.6), 0.35, 0.65)
    mud = _math(nt, 'MULTIPLY', mud, _mix_f(nt, mudn, 0.55, 1.0))
    if kind == 'rope':
        col, rg = _rope(nt, co, edge, cav, z)
    else:
        col, rg = _cutwood(nt, co, edge, cav, z)
        if kind == 'bark':   # bark with the axe-cut faces blended in by the mesh's smooth 'cut' weight
            cb, rb = _bark(nt, co, edge, cav, z)
            cw = _maprange(nt, _attr(nt, 'cut'), 0.0, 1.0)
            col = _mix_col(nt, cw, cb, col); rg = _mix_f(nt, cw, rb, rg)
    if kind != 'rope':
        col, rg = _char(nt, co, col, rg, tip)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', mud, 0.85), col, (0.045, 0.034, 0.024))
    rg = _mix_f(nt, mud, rg, 0.70)
    mt = 0.0
    for key, sock in (('BC', col), ('RG', rg), ('MT', mt), ('AO', ao)):
        rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_' + key; rr.label = key
        if isinstance(sock, (int, float)):
            v = _n(nt, 'ShaderNodeValue'); v.outputs[0].default_value = sock; nt.links.new(v.outputs[0], rr.inputs[0])
        else:
            nt.links.new(sock, rr.inputs[0])
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled'); bsdf.name = 'BSDF'
    nt.links.new(nt.nodes['OUT_BC'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(nt.nodes['OUT_RG'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(nt.nodes['OUT_MT'].outputs[0], bsdf.inputs['Metallic'])
    em = _n(nt, 'ShaderNodeEmission'); em.name = 'EMIT'
    out = _n(nt, 'ShaderNodeOutputMaterial'); out.name = 'OUT'
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])

KIND = {'Bark': 'bark', 'WoodCut': 'cut', 'Rope': 'rope'}
def build_all():
    for m in bpy.data.materials:
        base = m.name.split('.')[0]
        if base in KIND: build(m, KIND[base])

# Procedural PBR layers for the high poly. Each material computes BC / RG / MT; set_output() routes one of them
# (or the full BSDF) to the Material Output so the same tree serves preview renders and EMIT bakes.
import bpy

def _n(nt, t, loc=(0, 0), **kw):
    n = nt.nodes.new(t); n.location = loc
    for k, v in kw.items():
        if k.startswith('in_'): n.inputs[k[3:].replace('_', ' ')].default_value = v
        else: setattr(n, k, v)
    return n

def _mix_col(nt, fac, a, b):
    m = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MIX')
    _link(nt, fac, m.inputs[0]); _set(nt, a, m.inputs[6]); _set(nt, b, m.inputs[7]); return m.outputs[2]
def _mix_f(nt, fac, a, b):
    m = _n(nt, 'ShaderNodeMix', data_type='FLOAT')
    _link(nt, fac, m.inputs[0]); _set(nt, a, m.inputs[2]); _set(nt, b, m.inputs[3]); return m.outputs[0]
def _link(nt, out, inp):
    if isinstance(out, (int, float)): inp.default_value = out
    else: nt.links.new(out, inp)
def _set(nt, v, inp):
    if isinstance(v, tuple): inp.default_value = (*v, 1) if len(v) == 3 else v
    elif isinstance(v, (int, float)): inp.default_value = v
    else: nt.links.new(v, inp)
def _math(nt, op, a, b=None, clamp=False):
    m = _n(nt, 'ShaderNodeMath', operation=op, use_clamp=clamp)
    _link(nt, a, m.inputs[0])
    if b is not None: _link(nt, b, m.inputs[1])
    return m.outputs[0]
def _maprange(nt, v, a, b, c=0.0, d=1.0):
    m = _n(nt, 'ShaderNodeMapRange', clamp=True)
    _link(nt, v, m.inputs['Value']); m.inputs['From Min'].default_value = a; m.inputs['From Max'].default_value = b
    m.inputs['To Min'].default_value = c; m.inputs['To Max'].default_value = d
    return m.outputs[0]
def _noise(nt, scale, detail=6, rough=0.55, coord=None, dist=0.0):
    t = _n(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    if coord is not None: nt.links.new(coord, t.inputs['Vector'])
    return t
def _coord(nt):
    return _n(nt, 'ShaderNodeTexCoord').outputs['Object']

def _edge(nt, radius=0.0016):
    bev = _n(nt, 'ShaderNodeBevel', samples=8); bev.inputs['Radius'].default_value = radius
    geo = _n(nt, 'ShaderNodeNewGeometry')
    d = _n(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(bev.outputs[0], d.inputs[0]); nt.links.new(geo.outputs['Normal'], d.inputs[1])
    return _math(nt, 'SUBTRACT', 1.0, d.outputs['Value'], True)
def _cavity(nt, dist=0.004):
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', samples=16, only_local=True); ao.inputs['Distance'].default_value = dist
    return _math(nt, 'SUBTRACT', 1.0, ao.outputs['AO'], True), ao.outputs['AO']

def build(m, kind):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _coord(nt)
    edge = _edge(nt)
    cav, ao = _cavity(nt)
    wear_n = _noise(nt, 55, 10, 0.65, co).outputs['Fac']
    smudge = _noise(nt, 4.0, 4, 0.5, co).outputs['Fac']
    if kind in ('steel', 'buckle', 'etch'):
        base = (0.011, 0.011, 0.014) if kind == 'steel' else (0.11, 0.11, 0.115) if kind == 'buckle' else (0.009, 0.009, 0.010)
        temper = _noise(nt, 2.2, 3, 0.5, co).outputs['Fac']
        tint = _mix_col(nt, temper, (0.016, 0.019, 0.034), (0.032, 0.020, 0.036))
        col = _mix_col(nt, 0.45 if kind == 'steel' else 0.15, base, tint)
        hammer = _n(nt, 'ShaderNodeTexVoronoi', feature='SMOOTH_F1', in_Scale=160.0)
        nt.links.new(co, hammer.inputs['Vector'])
        col = _mix_col(nt, _maprange(nt, hammer.outputs['Distance'], 0.0, 0.6, 0.0, 0.18), col, (0.045, 0.045, 0.05))
        # exposed bright steel on worn edges, broken up by noise
        chip = _maprange(nt, _math(nt, 'MULTIPLY', edge, _maprange(nt, wear_n, 0.50, 0.64)), 0.05, 0.13)
        exposed = (0.36, 0.36, 0.38) if kind != 'etch' else (0.08, 0.08, 0.085)
        col = _mix_col(nt, chip, col, exposed)
        # fine scratches
        scr = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=420.0, in_Distortion=14.0, in_Detail=4.0)
        nt.links.new(co, scr.inputs['Vector'])
        scr_m = _math(nt, 'MULTIPLY', _maprange(nt, scr.outputs['Fac'], 0.93, 1.0), _maprange(nt, _noise(nt, 9, 2, 0.5, co).outputs['Fac'], 0.55, 0.7))
        col = _mix_col(nt, _math(nt, 'MULTIPLY', scr_m, 0.5), col, (0.16, 0.16, 0.17))
        # grime in cavities
        grime = _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.35, 0.85), _maprange(nt, smudge, 0.3, 0.7, 0.3, 0.9))
        col = _mix_col(nt, grime, col, (0.018, 0.013, 0.009))
        rg = _mix_f(nt, smudge, 0.22, 0.38) if kind != 'etch' else _mix_f(nt, smudge, 0.62, 0.8)
        rg = _mix_f(nt, chip, rg, 0.2)
        rg = _mix_f(nt, scr_m, rg, 0.18)
        rg = _mix_f(nt, grime, rg, 0.85)
        mt = _mix_f(nt, grime, 1.0, 0.55)
    elif kind == 'gold':
        n2 = _noise(nt, 30, 6, 0.6, co).outputs['Fac']
        col = _mix_col(nt, n2, (0.86, 0.60, 0.28), (1.0, 0.76, 0.40))
        col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.7), col, (0.25, 0.15, 0.06))
        rg = _mix_f(nt, n2, 0.20, 0.34)
        rg = _mix_f(nt, _maprange(nt, cav, 0.1, 0.6), rg, 0.6)
        mt = 1.0
    else:  # leather
        grain = _n(nt, 'ShaderNodeTexVoronoi', in_Scale=900.0); nt.links.new(co, grain.inputs['Vector'])
        g = _maprange(nt, grain.outputs['Distance'], 0.0, 0.5)
        col = _mix_col(nt, _noise(nt, 18, 6, 0.6, co).outputs['Fac'], (0.022, 0.011, 0.006), (0.042, 0.021, 0.010))
        col = _mix_col(nt, _math(nt, 'MULTIPLY', g, 0.25), col, (0.018, 0.009, 0.005))
        col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.03, 0.14), 0.6), col, (0.075, 0.042, 0.022))
        col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.6), col, (0.012, 0.007, 0.004))
        rg = _mix_f(nt, g, 0.52, 0.70)
        rg = _mix_f(nt, _maprange(nt, edge, 0.02, 0.12), rg, 0.42)
        mt = 0.0
    m['BC'], m['RG'], m['MT'] = 0, 0, 0
    # keep handles to the three outputs via reroutes
    for key, sock in (('BC', col), ('RG', rg), ('MT', mt), ('AO', ao)):
        rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_' + key; rr.label = key
        _link(nt, sock, rr.inputs[0]) if not isinstance(sock, (int, float)) else None
        if isinstance(sock, (int, float)):
            v = _n(nt, 'ShaderNodeValue'); v.outputs[0].default_value = sock; nt.links.new(v.outputs[0], rr.inputs[0])
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled'); bsdf.name = 'BSDF'
    nt.links.new(nt.nodes['OUT_BC'].outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(nt.nodes['OUT_RG'].outputs[0], bsdf.inputs['Roughness'])
    nt.links.new(nt.nodes['OUT_MT'].outputs[0], bsdf.inputs['Metallic'])
    em = _n(nt, 'ShaderNodeEmission'); em.name = 'EMIT'
    out = _n(nt, 'ShaderNodeOutputMaterial'); out.name = 'OUT'
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])

def set_output(m, what):
    """what: 'BSDF' or 'BC' / 'RG' / 'MT' / 'AO' (emission of that channel)."""
    nt = m.node_tree; out = nt.nodes['OUT']; em = nt.nodes['EMIT']
    if what == 'BSDF':
        nt.links.new(nt.nodes['BSDF'].outputs[0], out.inputs['Surface']); return
    nt.links.new(nt.nodes['OUT_' + what].outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])

KIND = {'Steel': 'steel', 'Gold': 'gold', 'Leather': 'leather', 'Buckle': 'buckle', 'Etch': 'etch'}
def build_all():
    for m in bpy.data.materials:
        base = m.name.split('.')[0]
        if base in KIND: build(m, KIND[base])



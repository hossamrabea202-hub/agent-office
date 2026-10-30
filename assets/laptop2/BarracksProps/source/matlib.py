# Procedural PBR layers for the high poly. Each material computes BC / RG / MT; set_output() routes one of them
# (or the full BSDF) to the Material Output so the same tree serves preview renders and EMIT bakes.
import bpy
LEATHER_TONE = 1.0

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
        # v2 (#64): blackened steel is a dark oxide over metal, not black paint: reflectance ~0.06-0.10, not 0.01,
        # or UE renders it as matte black plastic. Temper shifts blue -> violet -> faint straw over the plate.
        base = (0.026, 0.027, 0.032) if kind == 'steel' else (0.30, 0.30, 0.31) if kind == 'buckle' else (0.020, 0.020, 0.022)
        temper = _noise(nt, 1.6, 4, 0.55, co, 0.4).outputs['Fac']
        tint = _mix_col(nt, _maprange(nt, temper, 0.35, 0.55), (0.018, 0.024, 0.056), (0.046, 0.024, 0.054))
        tint = _mix_col(nt, _maprange(nt, temper, 0.62, 0.75, 0, 0.6), tint, (0.060, 0.044, 0.030))
        col = _mix_col(nt, 0.6 if kind == 'steel' else 0.12, base, tint)
        col = _mix_col(nt, _maprange(nt, _noise(nt, 14, 6, 0.6, co).outputs['Fac'], 0.3, 0.7, 0, 0.35), col, (0.014, 0.014, 0.017))
        hammer = _n(nt, 'ShaderNodeTexVoronoi', feature='SMOOTH_F1', in_Scale=160.0)
        nt.links.new(co, hammer.inputs['Vector'])
        hm = _maprange(nt, hammer.outputs['Distance'], 0.0, 0.6)
        col = _mix_col(nt, _math(nt, 'MULTIPLY', hm, 0.12), col, (0.06, 0.06, 0.066))
        # polishing streaks: long thin bands, mostly a roughness break-up
        pol = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', in_Scale=160.0, in_Distortion=2.0, in_Detail=6.0)
        nt.links.new(co, pol.inputs['Vector'])
        polm = _maprange(nt, pol.outputs['Fac'], 0.35, 0.9)
        # exposed bright steel on worn edges and high points, broken up by noise
        chip = _maprange(nt, _math(nt, 'MULTIPLY', edge, _maprange(nt, wear_n, 0.42, 0.62)), 0.03, 0.10)
        exposed = (0.56, 0.56, 0.58) if kind != 'etch' else (0.10, 0.10, 0.105)
        col = _mix_col(nt, chip, col, exposed)
        # scratches in two directions, only in patches
        scr = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=420.0, in_Distortion=14.0, in_Detail=4.0)
        nt.links.new(co, scr.inputs['Vector'])
        scr2 = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=300.0, in_Distortion=22.0, in_Detail=5.0)
        nt.links.new(co, scr2.inputs['Vector'])
        patch = _maprange(nt, _noise(nt, 9, 2, 0.5, co).outputs['Fac'], 0.5, 0.68)
        scr_m = _math(nt, 'MULTIPLY', _math(nt, 'MAXIMUM', _maprange(nt, scr.outputs['Fac'], 0.92, 1.0), _maprange(nt, scr2.outputs['Fac'], 0.95, 1.0)), patch)
        col = _mix_col(nt, _math(nt, 'MULTIPLY', scr_m, 0.7), col, (0.30, 0.30, 0.32))
        # grime and old oil in cavities and around rivets
        grime = _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.25, 0.8), _maprange(nt, smudge, 0.25, 0.7, 0.4, 1.0))
        col = _mix_col(nt, grime, col, (0.014, 0.010, 0.007))
        rg = _mix_f(nt, smudge, 0.20, 0.36) if kind != 'etch' else _mix_f(nt, smudge, 0.62, 0.8)
        rg = _mix_f(nt, _math(nt, 'MULTIPLY', polm, 0.25), rg, 0.16)
        rg = _mix_f(nt, _math(nt, 'MULTIPLY', hm, 0.3), rg, 0.34)
        rg = _mix_f(nt, chip, rg, 0.14)
        rg = _mix_f(nt, scr_m, rg, 0.30)
        rg = _mix_f(nt, grime, rg, 0.88)
        mt = _mix_f(nt, chip, 0.85 if kind != 'etch' else 0.6, 1.0)
        mt = _mix_f(nt, grime, mt, 0.3)
    elif kind == 'gold':
        # v2 (#64): inlaid gold: polished on the high points, antique (dark, rough) down in the recess walls
        n2 = _noise(nt, 30, 6, 0.6, co).outputs['Fac']
        col = _mix_col(nt, n2, (0.80, 0.56, 0.25), (1.0, 0.77, 0.37))
        col = _mix_col(nt, _maprange(nt, cav, 0.05, 0.5, 0, 0.85), col, (0.20, 0.11, 0.04))
        col = _mix_col(nt, _maprange(nt, edge, 0.02, 0.10, 0, 0.6), col, (1.0, 0.86, 0.58))
        rg = _mix_f(nt, n2, 0.16, 0.30)
        rg = _mix_f(nt, _maprange(nt, cav, 0.05, 0.5), rg, 0.65)
        rg = _mix_f(nt, _maprange(nt, edge, 0.02, 0.10), rg, 0.10)
        mt = 1.0
    else:  # leather (LEATHER_TONE < 1 darkens it, e.g. the gauntlet glove)
        t = LEATHER_TONE
        sc3 = lambda c: tuple(v * t for v in c)
        grain = _n(nt, 'ShaderNodeTexVoronoi', in_Scale=900.0); nt.links.new(co, grain.inputs['Vector'])
        g = _maprange(nt, grain.outputs['Distance'], 0.0, 0.5)
        col = _mix_col(nt, _noise(nt, 18, 6, 0.6, co).outputs['Fac'], sc3((0.022, 0.011, 0.006)), sc3((0.042, 0.021, 0.010)))
        col = _mix_col(nt, _math(nt, 'MULTIPLY', g, 0.25), col, sc3((0.018, 0.009, 0.005)))
        col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.03, 0.14), 0.6), col, sc3((0.075, 0.042, 0.022)))
        col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.6), col, sc3((0.012, 0.007, 0.004)))
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
    if 'OUT_' + what not in nt.nodes and what == 'EM':   # materials without emission (bark, rope, iron...) bake black
        rr = _n(nt, 'NodeReroute'); rr.name = 'OUT_EM'; c = _n(nt, 'ShaderNodeRGB'); c.outputs[0].default_value = (0, 0, 0, 1); nt.links.new(c.outputs[0], rr.inputs[0])
    nt.links.new(nt.nodes['OUT_' + what].outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])

KIND = {'Steel': 'steel', 'Gold': 'gold', 'Leather': 'leather', 'Buckle': 'buckle', 'Etch': 'etch'}
def build_all():
    for m in bpy.data.materials:
        base = m.name.split('.')[0]
        if base in KIND: build(m, KIND[base])



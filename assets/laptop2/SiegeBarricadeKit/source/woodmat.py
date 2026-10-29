# Procedural PBR for the siege barricade kit (#29), v2 for #135 (owner: "the wooden wall needs AAA textures").
# v1 read flat: one bark colour on every post, one grey, no moisture. v2 keeps the v1 contract and layers, and adds:
#   - per-log variation ('logvar' attribute, 0..1 per post): warm pine, grey weathered, dark umber
#   - three-tone bark: weathered silver crowns, rust-red flaked layers on the plate walls, near-black damp fissures
#   - moss in the fissures and on up-facing surfaces near the ground, grey-green lichen higher up
#   - rain streaks running down from the tips and the lashings
#   - a damp base (darker, glossier) with mud splashes and a soil band where the posts enter the ground
#   - roughness that follows all of the above (wet 0.45 .. moss 0.97), so the wood stops reading as one plastic
# Same contract as the Obsidian kit's materials.py: every material exposes OUT_BC / OUT_RG / OUT_MT / OUT_AO reroutes, a
# BSDF for previews and an EMIT node, and set_output() routes one channel for the EMIT bakes.
# Texture space is the mesh UV, which build_kit.py lays out in real-world metres: u = around the log, v = along it,
# so the grain and bark fissures always run along each log.
import bpy
from matlib import _n, _mix_col, _mix_f, _link, _set, _math, _maprange, _edge, _cavity, set_output

def _uv(nt):
    return _n(nt, 'ShaderNodeTexCoord').outputs['UV']
def _stretch(nt, co, su, sv):
    """scale UV (u around, v along) -> 3D vector for the noise nodes, stretched along the grain."""
    sep = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(co, sep.inputs[0])
    com = _n(nt, 'ShaderNodeCombineXYZ')
    _link(nt, _math(nt, 'MULTIPLY', sep.outputs[0], su), com.inputs[0])
    _link(nt, _math(nt, 'MULTIPLY', sep.outputs[1], sv), com.inputs[1])
    return com.outputs[0]
def _offset(nt, vec, var, k):
    """shift a noise lookup per log so two posts never share the same pattern."""
    add = _n(nt, 'ShaderNodeVectorMath', operation='ADD'); nt.links.new(vec, add.inputs[0])
    com = _n(nt, 'ShaderNodeCombineXYZ'); _link(nt, _math(nt, 'MULTIPLY', var, k), com.inputs[0])
    _link(nt, _math(nt, 'MULTIPLY', var, k * 0.7), com.inputs[2]); nt.links.new(com.outputs[0], add.inputs[1])
    return add.outputs[0]
def _noise(nt, vec, scale, detail=6, rough=0.55, dist=0.0):
    t = _n(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    nt.links.new(vec, t.inputs['Vector']); return t.outputs['Fac']
def _attr(nt, name):
    a = _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name); return a.outputs['Fac']
def _worldz(nt):
    g = _n(nt, 'ShaderNodeNewGeometry'); s = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(g.outputs['Position'], s.inputs[0]); return s.outputs[2]
def _normalz(nt):
    g = _n(nt, 'ShaderNodeNewGeometry'); s = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(g.outputs['Normal'], s.inputs[0]); return s.outputs[2]
def _mul_col(nt, fac, a, b):
    m = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    _link(nt, fac, m.inputs[0]); _set(nt, a, m.inputs[6]); _set(nt, b, m.inputs[7]); return m.outputs[2]
def _clamp(nt, v):
    return _math(nt, 'MINIMUM', _math(nt, 'MAXIMUM', v, 0.0), 1.0)

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
    # embers once glowed in the deepest cracks: a faint rust-brown ring between char and wood
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fringe, 0.65), col, (0.040, 0.022, 0.012))
    col = _mix_col(nt, full, col, charcol)
    rg = _mix_f(nt, full, rg, _mix_f(nt, crack, 0.78, 0.55))
    return col, rg

def _bark(nt, co, edge, cav, z, var, nz):
    co = _offset(nt, co, var, 13.7)
    grain = _stretch(nt, co, 1.0, 0.18)
    plates = _noise(nt, grain, 22, 8, 0.62, 0.6)
    tone = _noise(nt, _stretch(nt, co, 1, 0.4), 2.5, 3, 0.5)
    fine = _noise(nt, _stretch(nt, co, 1, 0.3), 150, 4, 0.6)
    # per log: warm pine (var 0) -> grey weathered (0.5) -> dark umber (1)
    warm_a, warm_b = (0.078, 0.046, 0.026), (0.140, 0.086, 0.050)
    grey_a, grey_b = (0.070, 0.064, 0.056), (0.135, 0.124, 0.108)
    dark_a, dark_b = (0.032, 0.022, 0.015), (0.060, 0.041, 0.028)
    w1 = _maprange(nt, var, 0.0, 0.5); w2 = _maprange(nt, var, 0.5, 1.0)
    lo = _mix_col(nt, w2, _mix_col(nt, w1, warm_a, grey_a), dark_a)
    hi = _mix_col(nt, w2, _mix_col(nt, w1, warm_b, grey_b), dark_b)
    col = _mix_col(nt, tone, lo, hi)
    col = _mul_col(nt, _math(nt, 'MULTIPLY', fine, 0.35), col, (0.55, 0.55, 0.55))
    # flaked inner layers: the rust-red of fresh pine bark where outer flakes have fallen off. Patches across the plates
    # (not a thin line round every plate, which read as cartoon outlines in the first preview)
    flake = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 0.35), 14, 5, 0.6, 0.4), 0.55, 0.72)
    redn = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 0.5), 3, 3, 0.5), 0.3, 0.7, 0.25, 0.75)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', flake, redn), col, (0.150, 0.068, 0.034))
    # weathering: raised crowns bleach silver; grey logs (var ~0.5) weather the most
    wamt = _mix_f(nt, _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', var, 0.5)), 0.75, 0.35)
    crown = _clamp(nt, _math(nt, 'ADD', _maprange(nt, edge, 0.02, 0.2), _maprange(nt, plates, 0.58, 0.78, 0, 0.6)))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', crown, wamt), col, (0.205, 0.190, 0.168))
    # deep fissures: near black, damp
    fis = _maprange(nt, cav, 0.38, 0.85, 0.0, 0.85)
    col = _mix_col(nt, fis, col, (0.022, 0.015, 0.010))   # dark umber, not ink: black lines read as cartoon outlines
    # grey-green lichen crusts, mid height (0.6 - 2.4 m)
    lich = _math(nt, 'MULTIPLY', _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 6, 6, 0.65), 0.60, 0.70),
                 _math(nt, 'MULTIPLY', _maprange(nt, z, 2.6, 1.6), _maprange(nt, z, 0.4, 0.9)))
    lichc = _mix_col(nt, fine, (0.20, 0.215, 0.165), (0.30, 0.31, 0.25))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', lich, 0.85), col, lichc)
    # moss: low down, in the fissures and on anything facing up, in clumps
    clump = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 0.6), 5, 6, 0.65), 0.46, 0.62)
    where = _clamp(nt, _math(nt, 'ADD', _maprange(nt, z, 1.1, 0.15), _maprange(nt, nz, 0.35, 0.85)))
    moss = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', clump, where), _mix_f(nt, _maprange(nt, cav, 0.05, 0.4), 0.45, 1.0))
    mossc = _mix_col(nt, _noise(nt, _stretch(nt, co, 1, 1), 60, 5, 0.6), (0.032, 0.052, 0.014), (0.085, 0.120, 0.030))
    col = _mix_col(nt, moss, col, mossc)
    rg = _mix_f(nt, plates, 0.80, 0.92)
    rg = _mix_f(nt, fis, rg, 0.74)
    rg = _mix_f(nt, lich, rg, 0.94)
    rg = _mix_f(nt, moss, rg, 0.97)
    # micro height for the normal bake (finer than the bake mesh can carry): horizontal flake layers, flake edges
    # stepping down, pitting; flat in the fissures and under moss (moss gets its own soft fuzz)
    lam = _noise(nt, _stretch(nt, co, 1.0, 9.0), 28, 4, 0.55)
    pits = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=420.0); nt.links.new(co, pits.inputs['Vector'])
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', lam, 0.7), _math(nt, 'MULTIPLY', flake, -0.35))
    h = _math(nt, 'ADD', h, _math(nt, 'MULTIPLY', _maprange(nt, pits.outputs['Distance'], 0.0, 0.25), 0.25))
    h = _math(nt, 'MULTIPLY', h, _math(nt, 'SUBTRACT', 1.0, fis))
    h = _mix_f(nt, moss, h, _math(nt, 'MULTIPLY', _noise(nt, co, 900, 2, 0.5), 0.5))
    return col, rg, h

def _cutwood(nt, co, edge, cav, z, var):
    co = _offset(nt, co, var, 7.3)
    grainv = _stretch(nt, co, 1.0, 0.04)
    rings = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=26.0, in_Distortion=3.0, in_Detail=6.0)
    nt.links.new(grainv, rings.inputs['Vector'])
    fib = _noise(nt, _stretch(nt, co, 1.0, 0.05), 160, 4, 0.6)
    young = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.3, 0.8), (0.36, 0.26, 0.15), (0.50, 0.37, 0.22))
    old = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.3, 0.8), (0.22, 0.20, 0.17), (0.31, 0.29, 0.25))
    # cuts age per log: fresh honey on a few posts, silver-grey on most
    age = _clamp(nt, _math(nt, 'ADD', _math(nt, 'MULTIPLY', var, 0.9), _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 4, 3, 0.5), 0.3, 0.7, -0.2, 0.3)))
    col = _mix_col(nt, age, young, old)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', fib, 0.40), col, (0.12, 0.085, 0.05))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6), col, (0.04, 0.028, 0.018))
    # dark weather checks (drying cracks) along the grain
    chk = _maprange(nt, _noise(nt, _stretch(nt, co, 1.0, 0.02), 40, 3, 0.5), 0.70, 0.78)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', chk, 0.8), col, (0.03, 0.022, 0.015))
    rg = _mix_f(nt, fib, 0.70, 0.86)
    h = _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', fib, 0.6), _math(nt, 'MULTIPLY', chk, 0.8))   # raised fibre, sunken checks
    return col, rg, h

def _rope(nt, co, edge, cav, z, var):
    strands = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', in_Scale=110.0, in_Distortion=1.5, in_Detail=4.0)
    nt.links.new(_stretch(nt, co, 1.0, 1.0), strands.inputs['Vector'])
    fuzz = _noise(nt, _stretch(nt, co, 1, 1), 240, 4, 0.7)
    dirt = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 7, 4, 0.6), 0.35, 0.7)
    col = _mix_col(nt, fuzz, (0.22, 0.17, 0.11), (0.34, 0.27, 0.17))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', dirt, 0.7), col, (0.09, 0.075, 0.05))   # old hemp, weathered and soiled
    col = _mix_col(nt, _maprange(nt, strands.outputs['Fac'], 0.6, 1.0, 0, 0.6), col, (0.08, 0.06, 0.04))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6), col, (0.035, 0.028, 0.018))
    rg = _mix_f(nt, fuzz, 0.88, 0.97)
    return col, rg

def build(m, kind):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _uv(nt)
    edge = _edge(nt, 0.004)
    cav, ao = _cavity(nt, 0.03)
    tip = _attr(nt, 'tip')
    var = _attr(nt, 'logvar')
    z = _worldz(nt)
    nz = _normalz(nt)
    h = None
    if kind == 'rope':
        col, rg = _rope(nt, co, edge, cav, z, var)
    else:
        col, rg, h = _cutwood(nt, co, edge, cav, z, var)
        if kind == 'bark':   # bark with the axe-cut faces blended in by the mesh's smooth 'cut' weight
            cb, rb, hb = _bark(nt, co, edge, cav, z, var, nz)
            cw = _maprange(nt, _attr(nt, 'cut'), 0.0, 1.0)
            col = _mix_col(nt, cw, cb, col); rg = _mix_f(nt, cw, rb, rg); h = _mix_f(nt, cw, hb, h)
    if kind != 'rope':
        col, rg = _char(nt, co, col, rg, tip)
    # rain streaks: long dark runs down the posts, strongest under the tips and the lashings
    streak = _maprange(nt, _noise(nt, _offset(nt, _stretch(nt, co, 1.0, 0.035), var, 5.1), 11, 4, 0.6), 0.56, 0.74, 0, 0.55)
    col = _mul_col(nt, streak, col, (0.55, 0.52, 0.48))
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', streak, 0.5), rg, 0.70)
    # damp base: darker and glossier up to ~0.7 m with a ragged edge
    edgew = _maprange(nt, _noise(nt, _stretch(nt, co, 1, 1), 6, 5, 0.6), 0.3, 0.7, -0.18, 0.18)
    damp = _maprange(nt, _math(nt, 'ADD', z, edgew), 0.75, 0.2)
    col = _mul_col(nt, _math(nt, 'MULTIPLY', damp, 0.8), col, (0.55, 0.52, 0.50))
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', damp, 0.75), rg, 0.46)
    # mud splashes: droplets thrown up to ~0.45 m, then a solid soil band where the post enters the ground
    drops = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=38.0)
    nt.links.new(_offset(nt, _stretch(nt, co, 1, 1), var, 3.3), drops.inputs['Vector'])
    dm = _math(nt, 'MULTIPLY', _maprange(nt, drops.outputs['Distance'], 0.22, 0.12), _maprange(nt, z, 0.45, 0.05))
    soil = _maprange(nt, _math(nt, 'ADD', z, _math(nt, 'MULTIPLY', edgew, 0.4)), 0.14, 0.02)
    mud = _clamp(nt, _math(nt, 'ADD', dm, soil))
    mudc = _mix_col(nt, _noise(nt, _stretch(nt, co, 1, 1), 30, 4, 0.6), (0.040, 0.030, 0.021), (0.075, 0.058, 0.040))
    col = _mix_col(nt, mud, col, mudc)
    rg = _mix_f(nt, mud, rg, 0.62)
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
    if h is not None:   # #135: micro detail rides on the BSDF normal, so the Normal bake (BSDF stage) carries it
        bump = _n(nt, 'ShaderNodeBump', in_Strength=0.55, in_Distance=0.0015)
        _link(nt, h, bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    em = _n(nt, 'ShaderNodeEmission'); em.name = 'EMIT'
    out = _n(nt, 'ShaderNodeOutputMaterial'); out.name = 'OUT'
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])

KIND = {'Bark': 'bark', 'WoodCut': 'cut', 'Rope': 'rope'}
def build_all():
    for m in bpy.data.materials:
        base = m.name.split('.')[0]
        if base in KIND: build(m, KIND[base])

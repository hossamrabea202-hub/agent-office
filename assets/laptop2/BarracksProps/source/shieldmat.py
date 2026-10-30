# Procedural PBR for the heater shield's high poly. Same contract as matlib/woodmat: every material exposes
# OUT_BC / OUT_RG / OUT_MT / OUT_AO reroutes, a BSDF for previews and an EMIT node; set_output() routes one channel.
#   Paint   tempera heraldry on gesso (masks/herald|damage|weather.png, planar x/z), craquelure, chips, rust bleed
#   Wood    the bare lime planks of the back, the grip blocks; per-plank tone from the 'plank' attribute
#   Iron    wrought iron: hammered, rusty in the hollows, rubbed bright on the high points
#   Leather veg-tan straps and pad (matlib leather, lighter tone)
#   Shaft   ash arrow shaft, fresh fibres at the break ('brk' attribute)
import os, json
import bpy
import matlib
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge, set_output
D = os.path.dirname(os.path.abspath(__file__))
SHIELD = os.environ.get('SHIELD', 'Heater')
GRIP_OIL = {'Heater': (0.11, 0.06, 0.49), 'Round': (0.0, 0.03, 0.40)}.get(SHIELD, (0.11, 0.06, 0.49))   # hand oil darkens the wood around the grip

def _co(nt): return _n(nt, 'ShaderNodeTexCoord').outputs['Object']
def _sep(nt, v):
    s = _n(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(v, s.inputs[0]); return s.outputs
def _vec(nt, x, y, z):
    c = _n(nt, 'ShaderNodeCombineXYZ'); _link(nt, x, c.inputs[0]); _link(nt, y, c.inputs[1]); _link(nt, z, c.inputs[2]); return c.outputs[0]
def _scale(nt, co, sx, sy, sz):
    s = _sep(nt, co); return _vec(nt, _math(nt, 'MULTIPLY', s[0], sx), _math(nt, 'MULTIPLY', s[1], sy), _math(nt, 'MULTIPLY', s[2], sz))
def _noise(nt, vec, scale, detail=6, rough=0.55, dist=0.0):
    t = _n(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough, in_Distortion=dist)
    nt.links.new(vec, t.inputs['Vector']); return t.outputs['Fac']
def _attr(nt, name):
    return _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs['Fac']
def _cav(nt, dist):
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', samples=16, only_local=True); ao.inputs['Distance'].default_value = dist
    return _math(nt, 'SUBTRACT', 1.0, ao.outputs['AO'], True), ao.outputs['AO']
def _img(nt, name, vec, folder='masks'):
    t = _n(nt, 'ShaderNodeTexImage', interpolation='Linear', extension='EXTEND')
    p = os.path.join(D, folder, name + '.png')
    im = next((i for i in bpy.data.images if os.path.normpath(bpy.path.abspath(i.filepath)) == os.path.normpath(p)), None) or bpy.data.images.load(p)
    im.colorspace_settings.name = 'Non-Color'
    t.image = im; nt.links.new(vec, t.inputs['Vector'])
    s = _n(nt, 'ShaderNodeSeparateColor'); nt.links.new(t.outputs['Color'], s.inputs[0]); return s.outputs
def _mul_col(nt, col, f):
    m = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); m.inputs[0].default_value = 1.0
    _link(nt, col, m.inputs[6]); c = _n(nt, 'ShaderNodeCombineColor'); _link(nt, f, c.inputs[0]); _link(nt, f, c.inputs[1]); _link(nt, f, c.inputs[2])
    nt.links.new(c.outputs[0], m.inputs[7]); return m.outputs[2]

def _finish(nt, col, rg, mt, ao):
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

def paint(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0012); cav, ao = _cav(nt, 0.006)
    mj = json.load(open(os.path.join(D, 'masks', 'masks.json')))
    s = _sep(nt, co)
    uv = _vec(nt, _maprange(nt, s[0], mj['x0'], mj['x1']), _maprange(nt, s[2], mj['z0'], mj['z1']), 0.0)
    hz = _img(nt, 'herald', uv); dm = _img(nt, 'damage', uv); we = _img(nt, 'weather', uv)
    tone = _noise(nt, co, 7, 4, 0.5)
    brush = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.22), 38, 4, 0.6)      # tempera brush strokes run across the board
    azure = _mix_col(nt, tone, (0.010, 0.026, 0.078), (0.020, 0.046, 0.118))
    red = _mix_col(nt, tone, (0.20, 0.016, 0.012), (0.31, 0.032, 0.020))
    gold = _mix_col(nt, tone, (0.31, 0.19, 0.045), (0.45, 0.29, 0.075))
    col = _mix_col(nt, hz[1], azure, red)
    col = _mix_col(nt, hz[0], col, gold)
    col = _mix_col(nt, hz[2], col, (0.016, 0.014, 0.013))
    col = _mul_col(nt, col, _maprange(nt, brush, 0.3, 0.7, 0.88, 1.10))
    # sun-faded, dusty: the pigment has gone chalky in patches
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 3.5, 4, 0.55), 0.45, 0.70, 0.0, 0.22), col, (0.26, 0.24, 0.20))
    # craquelure: fine cracks in the old paint film, dirt in them
    cq = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', in_Scale=260.0, in_Randomness=1.0)
    cqv = _n(nt, 'ShaderNodeVectorMath', operation='ADD'); nt.links.new(_scale(nt, co, 1.0, 1.0, 0.6), cqv.inputs[0])
    dn = _n(nt, 'ShaderNodeTexNoise', in_Scale=90.0, in_Detail=3.0); nt.links.new(co, dn.inputs['Vector'])
    sc_ = _n(nt, 'ShaderNodeVectorMath', operation='SCALE'); nt.links.new(dn.outputs['Color'], sc_.inputs[0]); sc_.inputs['Scale'].default_value = 0.004
    nt.links.new(sc_.outputs[0], cqv.inputs[1]); nt.links.new(cqv.outputs[0], cq.inputs['Vector'])
    crq = _math(nt, 'MULTIPLY', _maprange(nt, cq.outputs['Distance'], 0.0, 0.012, 1.0, 0.0), _maprange(nt, _noise(nt, co, 4, 3, 0.5), 0.55, 0.72))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', crq, 0.32), col, (0.020, 0.016, 0.012))
    # old dirt and smoke worked into the paint, heavier low down and in blotches
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 2.2, 5, 0.6), 0.45, 0.75, 0.0, 0.45), col, (0.045, 0.036, 0.026))
    # worn high points of the paint, a lighter rubbed sheen
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.15), 0.35), col, (0.30, 0.27, 0.22))
    # under the paint: gesso, then the lime wood, and the fresh wood in the sword cuts
    gesso = _mix_col(nt, _noise(nt, co, 60, 4, 0.6), (0.22, 0.19, 0.14), (0.33, 0.29, 0.21))
    gesso = _mix_col(nt, _maprange(nt, _noise(nt, co, 9, 4, 0.6), 0.4, 0.7, 0, 0.6), gesso, (0.12, 0.10, 0.07))
    grain = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.05), 140, 5, 0.6)
    wood = _mix_col(nt, grain, (0.13, 0.085, 0.045), (0.24, 0.16, 0.09))
    fresh = _mix_col(nt, _noise(nt, _scale(nt, co, 1.0, 1.0, 0.08), 260, 4, 0.6), (0.36, 0.26, 0.14), (0.52, 0.40, 0.24))
    chipped = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0.0, 0.7), gesso, (0.12, 0.10, 0.07))
    col = _mix_col(nt, dm[0], col, chipped)
    col = _mix_col(nt, dm[1], col, wood)
    col = _mix_col(nt, dm[2], col, _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.6), fresh, (0.10, 0.07, 0.04)))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', we[0], 0.85), col, (0.13, 0.045, 0.016))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', we[1], 0.55), col, (0.030, 0.024, 0.016))
    col = _mix_col(nt, we[2], col, (0.018, 0.013, 0.009))
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.75, 0, 0.75), col, (0.022, 0.017, 0.012))
    rg = _mix_f(nt, _noise(nt, co, 22, 4, 0.5), 0.50, 0.66)
    rg = _mix_f(nt, hz[0], rg, 0.46)
    rg = _mix_f(nt, crq, rg, 0.75)
    rg = _mix_f(nt, dm[0], rg, 0.86); rg = _mix_f(nt, dm[1], rg, 0.80); rg = _mix_f(nt, dm[2], rg, 0.74)
    rg = _mix_f(nt, we[0], rg, 0.90); rg = _mix_f(nt, _math(nt, 'MULTIPLY', we[1], 0.6), rg, 0.88)
    _finish(nt, col, rg, 0.0, ao)

def wood(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.002); cav, ao = _cav(nt, 0.02)
    # lime wood: pale, fine and even-grained; the grain runs up the planks with gentle waves, few rings
    warp = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.25), 6, 3, 0.5)
    gv = _vec(nt, _math(nt, 'ADD', _sep(nt, co)[0], _math(nt, 'MULTIPLY', warp, 0.02)), 0.0, _math(nt, 'MULTIPLY', _sep(nt, co)[2], 0.03))
    rings = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=9.0, in_Distortion=7.0, in_Detail=8.0, in_Detail_Roughness=0.6)
    nt.links.new(gv, rings.inputs['Vector'])
    fib = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.04), 260, 4, 0.6)
    col = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.2, 0.9, 0.0, 0.45), (0.33, 0.25, 0.15), (0.24, 0.17, 0.10))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, fib, 0.45, 0.7), 0.30), col, (0.16, 0.11, 0.065))
    pl = _attr(nt, 'plank')
    ptone = _maprange(nt, _math(nt, 'FRACT', _math(nt, 'MULTIPLY', pl, 7.31)), 0.0, 1.0, 0.78, 1.18)
    col = _mul_col(nt, col, ptone)
    # age: grey on the exposed grain, grime in the hollows and along the rim, hand oil darkening near the grip
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 4, 3, 0.5), 0.40, 0.70, 0.0, 0.35), col, (0.17, 0.15, 0.13))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.7, 0, 0.85), col, (0.020, 0.015, 0.010))
    gd = _n(nt, 'ShaderNodeVectorMath', operation='DISTANCE'); nt.links.new(co, gd.inputs[0]); gd.inputs[1].default_value = GRIP_OIL
    oil = _maprange(nt, gd.outputs['Value'], 0.16, 0.05, 0.0, 0.55)
    col = _mix_col(nt, oil, col, (0.07, 0.045, 0.025))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.2), 0.4), col, (0.30, 0.24, 0.16))
    rg = _mix_f(nt, fib, 0.74, 0.86)
    rg = _mix_f(nt, oil, rg, 0.48)
    rg = _mix_f(nt, _maprange(nt, cav, 0.2, 0.8), rg, 0.92)
    _finish(nt, col, rg, 0.0, ao)

def iron(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0010); cav, ao = _cav(nt, 0.005)
    n1 = _noise(nt, co, 24, 6, 0.6)
    # calibrated: wrought iron reflects ~45-55 % (linear), so bare metal sits at 180-200 sRGB; the darkness of old iron comes
    # from oxide and grime (non-metal layers), never from a dark metal base
    col = _mix_col(nt, n1, (0.40, 0.385, 0.36), (0.52, 0.50, 0.47))
    ham = _n(nt, 'ShaderNodeTexVoronoi', feature='SMOOTH_F1', in_Scale=180.0); nt.links.new(co, ham.inputs['Vector'])
    hm = _maprange(nt, ham.outputs['Distance'], 0.0, 0.6)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', hm, 0.25), col, (0.34, 0.33, 0.31))
    shine = _maprange(nt, _math(nt, 'MULTIPLY', edge, _maprange(nt, _noise(nt, co, 60, 6, 0.65), 0.40, 0.62)), 0.03, 0.12)
    col = _mix_col(nt, shine, col, (0.62, 0.61, 0.58))
    # dark mill-scale / oxide film over most of it (a non-metal layer: metallic drops where it sits)
    scale_ = _maprange(nt, _noise(nt, co, 14, 5, 0.6), 0.30, 0.55, 0.55, 0.95)
    scale_ = _math(nt, 'MULTIPLY', scale_, _math(nt, 'SUBTRACT', 1.0, shine, True))
    col = _mix_col(nt, scale_, col, (0.055, 0.050, 0.046))
    s = _sep(nt, co)
    rlow = _maprange(nt, s[2], 0.35, 0.0, 0.0, 0.35)       # the bottom of the rim sat in the mud more
    rmask = _math(nt, 'ADD', _maprange(nt, cav, 0.15, 0.6), _math(nt, 'ADD', _maprange(nt, _noise(nt, co, 9, 5, 0.6), 0.52, 0.68, 0, 0.8), rlow))
    rmask = _math(nt, 'MULTIPLY', _math(nt, 'MINIMUM', rmask, 1.0), _math(nt, 'SUBTRACT', 1.0, shine, True))
    pit = _noise(nt, co, 320, 3, 0.6)
    rust = _mix_col(nt, pit, (0.075, 0.028, 0.010), (0.19, 0.075, 0.025))
    col = _mix_col(nt, rmask, col, rust)
    rg = _mix_f(nt, n1, 0.36, 0.52)
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', hm, 0.4), rg, 0.6)
    rg = _mix_f(nt, shine, rg, 0.24)
    rg = _mix_f(nt, scale_, rg, 0.62)
    rg = _mix_f(nt, rmask, rg, 0.90)
    mt = _mix_f(nt, rmask, _mix_f(nt, scale_, 1.0, 0.35), 0.0)
    _finish(nt, col, rg, mt, ao)

def shaft(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0008); cav, ao = _cav(nt, 0.004)
    f = _noise(nt, co, 220, 4, 0.6)
    col = _mix_col(nt, f, (0.20, 0.145, 0.085), (0.29, 0.21, 0.125))
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 6, 4, 0.5), 0.4, 0.7, 0, 0.5), col, (0.10, 0.075, 0.05))
    col = _mix_col(nt, _maprange(nt, _attr(nt, 'brk'), 0.1, 0.6), col, (0.50, 0.40, 0.26))
    col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.7), col, (0.05, 0.035, 0.02))
    rg = _mix_f(nt, f, 0.68, 0.82)
    _finish(nt, col, rg, 0.0, ao)

def leather(m):
    matlib.LEATHER_TONE = 3.4
    matlib.build(m, 'leather')

def woodfront(m):
    """round shield front: bare linden, sun-greyed, scratched; masks_round/damage (gash, char, grime) + wood (plank, crack, scratch)."""
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); edge = _edge(nt, 0.0015); cav, ao = _cav(nt, 0.01)
    mj = json.load(open(os.path.join(D, 'masks_round', 'masks.json')))
    s = _sep(nt, co)
    uv = _vec(nt, _maprange(nt, s[0], mj['x0'], mj['x1']), _maprange(nt, s[2], mj['z0'], mj['z1']), 0.0)
    dm = _img(nt, 'damage', uv, 'masks_round'); wd = _img(nt, 'wood', uv, 'masks_round')
    warp = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.25), 6, 3, 0.5)
    gv = _vec(nt, _math(nt, 'ADD', s[0], _math(nt, 'MULTIPLY', warp, 0.02)), 0.0, _math(nt, 'MULTIPLY', s[2], 0.03))
    rings = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=10.0, in_Distortion=7.0, in_Detail=8.0, in_Detail_Roughness=0.6)
    nt.links.new(gv, rings.inputs['Vector'])
    fib = _noise(nt, _scale(nt, co, 1.0, 1.0, 0.04), 280, 4, 0.6)
    col = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.2, 0.9, 0.0, 0.5), (0.30, 0.20, 0.11), (0.15, 0.095, 0.05))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, fib, 0.42, 0.7), 0.55), col, (0.07, 0.045, 0.025))
    col = _mul_col(nt, col, _maprange(nt, _math(nt, 'FRACT', _math(nt, 'MULTIPLY', wd[0], 5.37)), 0.0, 1.0, 0.70, 1.25))
    # weathered: sun-greyed silver on the open face, broken by blotches; old oil darker in patches
    grey = _maprange(nt, _noise(nt, co, 3.0, 5, 0.55), 0.40, 0.72, 0.0, 0.42)
    col = _mix_col(nt, grey, col, (0.25, 0.235, 0.21))
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 5.5, 4, 0.6), 0.55, 0.75, 0.0, 0.5), col, (0.09, 0.065, 0.04))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', wd[2], 0.8), col, (0.36, 0.30, 0.22))                # fresh scratches
    col = _mix_col(nt, wd[1], col, (0.02, 0.015, 0.01))                                           # seam gaps
    fresh = _mix_col(nt, _noise(nt, _scale(nt, co, 1.0, 1.0, 0.08), 260, 4, 0.6), (0.40, 0.30, 0.17), (0.56, 0.44, 0.27))
    col = _mix_col(nt, dm[0], col, _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.6), fresh, (0.10, 0.07, 0.04)))
    cq = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', in_Scale=70.0); nt.links.new(_scale(nt, co, 1.0, 1.0, 0.5), cq.inputs['Vector'])
    charc = _mix_col(nt, _maprange(nt, _noise(nt, co, 40, 4, 0.6), 0.5, 0.75, 0, 0.6), (0.016, 0.014, 0.013), (0.09, 0.085, 0.08))
    charc = _mix_col(nt, _maprange(nt, cq.outputs['Distance'], 0.0, 0.05, 1.0, 0.0), charc, (0.005, 0.004, 0.004))
    col = _mix_col(nt, _maprange(nt, dm[1], 0.0, 0.35, 0, 0.75), col, (0.05, 0.035, 0.022))       # scorched fringe
    col = _mix_col(nt, _maprange(nt, dm[1], 0.35, 0.8), col, charc)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', dm[2], 0.8), col, (0.03, 0.022, 0.015))
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.75, 0, 0.8), col, (0.02, 0.015, 0.01))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.02, 0.2), 0.35), col, (0.34, 0.29, 0.22))
    rg = _mix_f(nt, fib, 0.78, 0.90)
    rg = _mix_f(nt, dm[0], rg, 0.72); rg = _mix_f(nt, dm[1], rg, 0.80); rg = _mix_f(nt, wd[1], rg, 0.95)
    _finish(nt, col, rg, 0.0, ao)

KIND = {'WoodFront': woodfront, 'Paint': paint, 'Wood': wood, 'Iron': iron, 'Shaft': shaft, 'Leather': leather}
def build_all():
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

# Procedural PBR for the flora kit's high polys (knowledge-base standard: calibrated albedo, 3-scale roughness,
# physical wear). Same contract as the other *mat modules (OUT_BC/RG/MT/AO/EM reroutes). Petals and leaves are
# two-sided in UE with subsurface, so BaseColor carries the pigment only; translucency comes from the UE material.
#   Stem / Leaf                 green plant tissue: waxy cuticle, veins lighter, edges drying brown
#   PetalWhite / PetalRed / PetalPink   pigment with a translucent look, darker base, veins
#   Pollen / PollenDark         pollen heads
#   Flesh / FleshLeaf / FleshPetal / Core / Sac / Corrupt   realm: wet corrupted tissue, bioluminescent veins ('glow' attribute -> EM)
import bpy
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col, _finish as _finish_plain
from swordmat import _finish
GLOW = {'Flesh': (0.9, 0.08, 0.35), 'Sac': (0.25, 0.95, 0.55), 'Core': (1.0, 0.25, 0.12), 'FleshLeaf': (0.5, 0.9, 0.6), 'FleshPetal': (0.95, 0.15, 0.4), 'Corrupt': (0.85, 0.1, 0.5)}

def _attr(nt, name):
    return _n(nt, 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs['Fac']
def _uv(nt): return _n(nt, 'ShaderNodeTexCoord').outputs['UV']

def green(m, kind):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _uv(nt); edge = _edge(nt, 0.0008); cav, ao = _cav(nt, 0.004)
    s = _sep(nt, uv); along = s[1]
    # chlorophyll green, calibrated (grass ~0.21 linear reflectance => leaf 0.08-0.16 linear with the green bias)
    tone = _noise(nt, co, 12, 4, 0.55)
    col = _mix_col(nt, tone, (0.055, 0.115, 0.030), (0.090, 0.165, 0.045))
    vein = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=90.0, in_Distortion=4.0, in_Detail=3.0)
    nt.links.new(uv, vein.inputs['Vector'])
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, vein.outputs['Fac'], 0.85, 1.0), 0.5), col, (0.14, 0.20, 0.07))
    # drying: edges and tips go yellow then brown
    dry = _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.03, 0.2), _maprange(nt, _noise(nt, co, 25, 3, 0.6), 0.45, 0.7))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', dry, 0.7), col, (0.22, 0.16, 0.05))
    if kind == 'stem': col = _mix_col(nt, _maprange(nt, _noise(nt, _scale(nt, co, 1, 1, 0.15), 40, 3, 0.6), 0.5, 0.75, 0, 0.5), col, (0.14, 0.09, 0.05))   # reddish stem streaks
    col = _mix_col(nt, _maprange(nt, cav, 0.15, 0.7, 0, 0.6), col, (0.025, 0.045, 0.015))
    rg = _mix_f(nt, _noise(nt, co, 300, 3, 0.6), 0.42, 0.58)
    rg = _mix_f(nt, _maprange(nt, tone, 0.3, 0.7), rg, 0.50)
    rg = _mix_f(nt, dry, rg, 0.8)
    _finish(nt, col, rg, 0.0, ao)

def petal(m, base, tip, veinc, dark_base=True):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _uv(nt); edge = _edge(nt, 0.0006); cav, ao = _cav(nt, 0.003)
    s = _sep(nt, uv); along = _maprange(nt, s[1], 0.0, 0.03)       # 0 at the base, 1 at 3 cm
    col = _mix_col(nt, along, base, tip)
    col = _mix_col(nt, _maprange(nt, _noise(nt, co, 60, 4, 0.55), 0.35, 0.65, 0.0, 0.25), col, _mul_col(nt, col, 0.75))
    vein = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=140.0, in_Distortion=5.0, in_Detail=3.0)
    nt.links.new(uv, vein.inputs['Vector'])
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, vein.outputs['Fac'], 0.88, 1.0), 0.45), col, veinc)
    # bruising/browning at the edges, dew-wet gloss in the cup
    brown = _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.03, 0.25), _maprange(nt, _noise(nt, co, 40, 3, 0.6), 0.5, 0.72))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', brown, 0.6), col, (0.18, 0.09, 0.04))
    col = _mix_col(nt, _maprange(nt, cav, 0.2, 0.8, 0, 0.5), col, _mul_col(nt, col, 0.5))
    rg = _mix_f(nt, _noise(nt, co, 400, 3, 0.6), 0.48, 0.66)
    rg = _mix_f(nt, _maprange(nt, cav, 0.1, 0.5), rg, 0.35)
    rg = _mix_f(nt, brown, rg, 0.85)
    _finish(nt, col, rg, 0.0, ao)

def pollen(m, c1, c2):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); cav, ao = _cav(nt, 0.002)
    vor = _n(nt, 'ShaderNodeTexVoronoi', feature='F1', in_Scale=1400.0); nt.links.new(co, vor.inputs['Vector'])
    gm = _maprange(nt, vor.outputs['Distance'], 0.0, 0.5)
    col = _mix_col(nt, gm, c1, c2); col = _mix_col(nt, _maprange(nt, cav, 0.1, 0.6, 0, 0.6), col, _mul_col(nt, col, 0.4))
    rg = _mix_f(nt, gm, 0.55, 0.8)
    _finish(nt, col, rg, 0.0, ao)

def flesh(m, kind):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    co = _co(nt); uv = _uv(nt); edge = _edge(nt, 0.0008); cav, ao = _cav(nt, 0.004)
    glow = _attr(nt, 'glow'); gc = GLOW[kind]
    tone = _noise(nt, co, 18, 4, 0.55)
    # albedo kept in the 45-200 sRGB band (knowledge base): flesh is pinkish-red, never near-black
    base = {'Flesh': ((0.16, 0.06, 0.08), (0.30, 0.12, 0.14)), 'FleshLeaf': ((0.07, 0.11, 0.06), (0.16, 0.08, 0.12)), 'FleshPetal': ((0.22, 0.05, 0.09), (0.42, 0.10, 0.15)),
            'Core': ((0.40, 0.12, 0.06), (0.65, 0.24, 0.10)), 'Sac': ((0.12, 0.22, 0.12), (0.22, 0.36, 0.19)), 'Corrupt': ((0.07, 0.05, 0.06), (0.14, 0.09, 0.10))}[kind]
    col = _mix_col(nt, tone, *base)
    # veins: dark branching lines; the glow runs inside them
    vein = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', in_Scale=(140.0 if kind in ('Flesh', 'FleshLeaf') else 70.0) if kind != 'Corrupt' else 6.0); nt.links.new(_scale(nt, co, 1, 1, 0.5), vein.inputs['Vector'])
    vm = _maprange(nt, vein.outputs['Distance'], 0.0, (0.008 if kind in ('Flesh', 'FleshLeaf') else 0.014) if kind != 'Corrupt' else 0.06, 1.0, 0.0)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', vm, 0.45), col, (0.06, 0.02, 0.035))
    # mottling, pale sickly patches, and the wet sheen
    mot = _maprange(nt, _noise(nt, co, 55, 3, 0.6), 0.55, 0.72)
    col = _mix_col(nt, _math(nt, 'MULTIPLY', mot, 0.5), col, (0.30, 0.26, 0.22))
    col = _mix_col(nt, _maprange(nt, cav, 0.35, 0.85, 0, 0.45), col, (0.07, 0.025, 0.035))      # grime only in real folds, never black blotches
    if kind == 'Corrupt':   # earth and ash between the flesh, cracks glowing
        earth = _maprange(nt, _noise(nt, co, 3, 4, 0.6), 0.35, 0.6)
        col = _mix_col(nt, earth, col, _mix_col(nt, _noise(nt, co, 90, 4, 0.6), (0.045, 0.035, 0.028), (0.075, 0.06, 0.045)))
        glow = _math(nt, 'MAXIMUM', _math(nt, 'MULTIPLY', vm, _maprange(nt, _noise(nt, co, 2.0, 3, 0.5), 0.3, 0.6)), _math(nt, 'MULTIPLY', glow, 0.6))
    em_m = _math(nt, 'MULTIPLY', glow, _math(nt, 'ADD', 0.35, _math(nt, 'MULTIPLY', vm, 0.65)))
    if kind in ('Core', 'Sac'): em_m = _math(nt, 'MAXIMUM', em_m, _math(nt, 'MULTIPLY', glow, _maprange(nt, _noise(nt, co, 30, 3, 0.6), 0.3, 0.8, 0.2, 0.7)))
    em = _mix_col(nt, em_m, (0, 0, 0), gc)
    rg = _mix_f(nt, _noise(nt, co, 250, 3, 0.6), 0.30, 0.50)      # moist, not lacquered
    rg = _mix_f(nt, _maprange(nt, _noise(nt, co, 20, 3, 0.6), 0.35, 0.65), rg, _math(nt, 'ADD', rg, 0.12))
    rg = _mix_f(nt, mot, rg, 0.62); rg = _mix_f(nt, _maprange(nt, edge, 0.02, 0.2), rg, 0.30)
    if kind == 'Corrupt': rg = _mix_f(nt, earth, rg, 0.85)
    _finish(nt, col, rg, 0.0, ao, em)

KIND = {'Stem': lambda m: green(m, 'stem'), 'Leaf': lambda m: green(m, 'leaf'),
        'PetalWhite': lambda m: petal(m, (0.55, 0.55, 0.42), (0.82, 0.82, 0.78), (0.70, 0.70, 0.62)),
        'PetalRed': lambda m: petal(m, (0.08, 0.005, 0.01), (0.55, 0.035, 0.02), (0.30, 0.02, 0.015)),
        'PetalPink': lambda m: petal(m, (0.45, 0.10, 0.25), (0.60, 0.22, 0.40), (0.35, 0.06, 0.18)),
        'Pollen': lambda m: pollen(m, (0.55, 0.38, 0.06), (0.75, 0.55, 0.10)), 'PollenDark': lambda m: pollen(m, (0.03, 0.03, 0.04), (0.10, 0.08, 0.06)),
        'Flesh': lambda m: flesh(m, 'Flesh'), 'FleshLeaf': lambda m: flesh(m, 'FleshLeaf'), 'FleshPetal': lambda m: flesh(m, 'FleshPetal'),
        'Core': lambda m: flesh(m, 'Core'), 'Sac': lambda m: flesh(m, 'Sac'), 'Corrupt': lambda m: flesh(m, 'Corrupt')}
def build_all():
    for m in bpy.data.materials:
        f = KIND.get(m.name.split('.')[0])
        if f: f(m)

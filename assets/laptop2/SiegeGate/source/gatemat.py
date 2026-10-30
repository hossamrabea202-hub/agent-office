# Materials for the water-worn siege gate, built to the laptop2 realism standard (handoffs/laptop2-realism/STANDARD.md):
# calibrated albedo (weathered wood 0.10-0.20 linear), roughness varied at 3 scales, wear layered in physical order:
# base -> grain -> sun-greying (faces) -> edge wear (curvature) -> water (height: wet band, tide lines, algae, rot)
# -> gravity streaks (rain from the top, rust below iron) -> cavity grime -> one shared dust/dirt pass.
#   Plank     sawn boards of the leaves, ledges, brace, bar, lever arm
#   Bark / WoodCut / Rope   the siege kit's woodmat (posts, lintel, lashings, lever post)
#   Iron      shieldmat's calibrated wrought iron, with extra rust runs low down
import bpy
import woodmat, shieldmat
from matlib import _n, _mix_col, _mix_f, _link, _math, _maprange, _edge
from shieldmat import _co, _sep, _vec, _scale, _noise, _cav, _mul_col, _finish

def plank(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    uv = _n(nt, 'ShaderNodeTexCoord').outputs['UV']; co = _co(nt)
    edge = _edge(nt, 0.004); cav, ao = _cav(nt, 0.03)
    s = _sep(nt, co); z = s[2]
    g = _n(nt, 'ShaderNodeNewGeometry'); ns = _sep(nt, g.outputs['Normal'])
    # --- base + grain (UV: u across the board, v along it) ---
    gv = woodmat._stretch(nt, uv, 1.0, 0.035)
    rings = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=11.0, in_Distortion=6.0, in_Detail=0.0, in_Detail_Roughness=0.5)
    nt.links.new(gv, rings.inputs['Vector'])
    # fibre streaks at ~200/m along the board: a 4K gate has ~800 texels/m, so finer noise aliased into a grid moire
    fib = woodmat._noise(nt, woodmat._stretch(nt, uv, 1.0, 0.3), 60, 3, 0.6)
    macro = woodmat._noise(nt, woodmat._stretch(nt, uv, 1.0, 0.3), 1.6, 3, 0.5)            # board-to-board tone
    col = _mix_col(nt, _maprange(nt, rings.outputs['Fac'], 0.2, 0.9, 0.0, 0.45), (0.145, 0.105, 0.065), (0.085, 0.060, 0.036))   # soft annual rings, no harmonics (they baked as corduroy)
    col = _mul_col(nt, col, _maprange(nt, macro, 0.3, 0.7, 0.82, 1.16))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', _maprange(nt, fib, 0.45, 0.72), 0.45), col, (0.075, 0.055, 0.035))
    # --- sun-greying on the outside faces (silver-grey, strongest high up where it dries) ---
    sun = _math(nt, 'MULTIPLY', _maprange(nt, woodmat._noise(nt, co, 2.2, 4, 0.55), 0.3, 0.75, 0.45, 0.9), _maprange(nt, z, 0.6, 2.2, 0.3, 1.0))
    col = _mix_col(nt, sun, col, (0.125, 0.122, 0.115))                 # silver-grey, not pink
    # --- edge wear: worn, splintery lighter edges ---
    # threshold above the micro-facets of the displaced high poly (slopes < 20 deg), so only real board corners wear
    ew = _math(nt, 'MULTIPLY', _maprange(nt, edge, 0.10, 0.35), _maprange(nt, woodmat._noise(nt, co, 40, 4, 0.6), 0.4, 0.65))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', ew, 0.55), col, (0.27, 0.22, 0.16))
    # --- water: a capillary wet band, tide lines, algae and moss low down ---
    wetn = woodmat._noise(nt, co, 3.0, 4, 0.55)
    wet = _maprange(nt, _math(nt, 'ADD', z, _math(nt, 'MULTIPLY', wetn, 0.30)), 1.25, 0.35)
    # Lagarde wetness for porous wood: diffuse darkens per channel (wet/dry ~ 0.82, 0.58, 0.38), gloss gain damped by 0.5
    wm = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); _link(nt, wet, wm.inputs[0]); nt.links.new(col, wm.inputs[6])
    wm.inputs[7].default_value = (0.82, 0.58, 0.38, 1); col = wm.outputs[2]
    # tide lines: horizontal bands from noise stretched flat (the Wave texture baked fine regular lines, see the knowledge log)
    tide = woodmat._noise(nt, _scale(nt, co, 0.25, 0.25, 5.0), 7.0, 2, 0.5)
    tl = _math(nt, 'MULTIPLY', _maprange(nt, tide, 0.60, 0.70), _maprange(nt, z, 1.3, 0.45))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', tl, 0.7), col, (0.045, 0.040, 0.030))
    alg = _math(nt, 'MULTIPLY', _maprange(nt, woodmat._noise(nt, co, 7, 5, 0.65), 0.38, 0.65), _maprange(nt, z, 0.95, 0.10))
    alg = _math(nt, 'MAXIMUM', alg, _math(nt, 'MULTIPLY', _maprange(nt, cav, 0.4, 0.85), _maprange(nt, z, 1.4, 0.2)))
    # transition band at the algae edge (Naughty Dog's blend seam): a thin darker, damper rim before the green
    band = _math(nt, 'MULTIPLY', _maprange(nt, alg, 0.0, 0.35), _maprange(nt, alg, 0.6, 0.35))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', band, 0.5), col, (0.05, 0.045, 0.03))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', alg, 0.8), col, _mix_col(nt, woodmat._noise(nt, co, 30, 3, 0.6), (0.040, 0.055, 0.018), (0.075, 0.090, 0.030)))
    # --- gravity: rain streaks running down the boards from the top ---
    streak = woodmat._noise(nt, _scale(nt, co, 14.0, 14.0, 0.7), 3.0, 4, 0.6)
    st = _math(nt, 'MULTIPLY', _maprange(nt, streak, 0.55, 0.75), _maprange(nt, z, 3.3, 1.2, 0.8, 0.1))
    col = _mix_col(nt, _math(nt, 'MULTIPLY', st, 0.5), col, (0.06, 0.05, 0.04))
    # --- cavity grime, then one shared dust pass on up-facing surfaces ---
    col = _mix_col(nt, _maprange(nt, cav, 0.35, 0.85, 0, 0.6), col, (0.035, 0.028, 0.020))      # grime only in real hollows: the 6 mm erosion ridges of the high poly read as AO lines below 0.3
    dust = _math(nt, 'MULTIPLY', _maprange(nt, ns[2], 0.5, 0.95), 0.5)
    col = _mix_col(nt, dust, col, (0.21, 0.19, 0.16))
    # --- roughness: 3 scales, wet glossier, algae slick, dust dry ---
    rg = _mix_f(nt, fib, 0.78, 0.92)
    rg = _mix_f(nt, _maprange(nt, macro, 0.3, 0.7), rg, 0.86)
    rg = _mix_f(nt, _math(nt, 'MULTIPLY', wet, 0.5), rg, 0.30)          # wet gloss, damped by 0.5 (Lagarde)
    rg = _mix_f(nt, alg, rg, 0.45)
    rg = _mix_f(nt, dust, rg, 0.95)
    _finish(nt, col, rg, 0.0, ao)

KIND = {'Plank': plank}
def build_all():
    woodmat.build_all()          # Bark, WoodCut, Rope
    for m in bpy.data.materials:
        base = m.name.split('.')[0]
        if base in KIND: KIND[base](m)
        elif base == 'Iron': shieldmat.iron(m)

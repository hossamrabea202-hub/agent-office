# #296 Cave rock (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run. Rules: handoffs/cave-296-297/RESEARCH.md.
#   py "<repo>/handoffs/cave-296-297/setup_caverock296_ue.py" --dry-run                  (only reports)
#   py "<repo>/handoffs/cave-296-297/setup_caverock296_ue.py"                            (makes the assets, swaps nothing)
#   py ".../setup_caverock296_ue.py" --apply <ActorLabelPrefix> <MI name> [--dry-run]     (ONLY after the owner's OK)
#   py ".../setup_caverock296_ue.py" --revert                                             (puts every logged material back)
# Makes in /Game/CastleDefender/Environment/Cave:
#   M_CaveRock          fully procedural 3D rock: no textures, so no tiling, no UV stretching, no licence questions.
#                       Height = fbm + ridged fractures + limestone strata bands, normal from 4 height taps (world space).
#                       Layers in physical order: cavity dirt -> calcite bloom on drip lines -> iron runs under seams ->
#                       soot on ceilings (mine) -> moss near the mouth only -> wetness (darker x0.5 on porous rock, gloss
#                       first) -> flat puddles in low spots on the floor (roughness 0.06, normal flattened 0.95).
#                       Albedo clamped to >= 30 sRGB (KB rule 1); metallic 0; specular 0.5.
#   MI_CaveRock_Natural natural cave: sharp fractures, strata, iron + calcite, moss at the mouth (set MossOrigin)
#   MI_CaveRock_Mine    medieval fire-set mine: rounded smooth walls (low bumpiness), lamp soot on the ceiling, drier walls
#   MI_CaveRock_Floor   tunnel floor: more puddles, more grit
import os, sys, unreal

A = sys.argv[1:]
DRY, APPLY, REVERT = '--dry-run' in A, '--apply' in A, '--revert' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\cave-296-297'
DST = '/Game/CastleDefender/Environment/Cave'
SWAPLOG = os.path.join(HERE, 'caverock296_swaps.txt')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#296 cave rock' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


# ------------------------------------------------------------------------------------------------ HLSL (struct trick = functions)
LIB = r'''
struct CRk {
  float h1(float3 p) { p = frac(p * 0.3183099 + 0.1); p *= 17.0; return frac(p.x * p.y * p.z * (p.x + p.y + p.z)); }
  float vn(float3 x) {
    float3 i = floor(x); float3 f = frac(x); f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(lerp(h1(i), h1(i + float3(1,0,0)), f.x), lerp(h1(i + float3(0,1,0)), h1(i + float3(1,1,0)), f.x), f.y),
                lerp(lerp(h1(i + float3(0,0,1)), h1(i + float3(1,0,1)), f.x), lerp(h1(i + float3(0,1,1)), h1(i + float3(1,1,1)), f.x), f.y), f.z);
  }
  float fbm(float3 p) { float a = 0.5, s = 0.0; for (int o = 0; o < 4; o++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s / 0.9375; }
  float ridge(float3 p) { float a = 0.5, s = 0.0; for (int o = 0; o < 3; o++) { float r = 1.0 - abs(vn(p) * 2.0 - 1.0); s += a * r * r; p = p * 2.11 + 5.3; a *= 0.5; } return s / 0.875; }
  float cell(float3 x, out float id) {
    float3 i = floor(x); float3 f = frac(x); float d1 = 8.0, d2 = 8.0; id = 0.0;
    for (int a = -1; a <= 1; a++) for (int b = -1; b <= 1; b++) for (int c = -1; c <= 1; c++) {
      float3 o = float3(a, b, c); float3 q = i + o;
      float3 r = o + float3(h1(q), h1(q + 19.19), h1(q + 47.3)) - f; float d = dot(r, r);
      if (d < d1) { d2 = d1; d1 = d; id = h1(q + 71.7); } else if (d < d2) { d2 = d; }
    }
    return sqrt(d2) - sqrt(d1);
  }
  float bed(float3 w, float sc, float strataCm) { return w.z / max(strataCm, 1.0) + fbm(w / sc * 0.4) * 1.6; }
  float height(float3 w, float sc, float strataCm, float sharp) {
    float3 p = w / sc;
    float big = fbm(p);
    float lay = bed(w, sc, strataCm);
    float ledge = frac(lay);                                           // sawtooth = each bed overhangs the one below
    ledge = smoothstep(0.0, 0.12, ledge) * (1.0 - ledge * 0.6);
    float bid; float e1 = cell(p * 2.2 + vn(p * 3.0) * 0.35, bid);   // angular fracture blocks
    float fid; float e2 = cell(p * 7.0 + 11.3, fid);                  // finer cracks
    float crk = ((1.0 - smoothstep(0.0, 0.035, e1)) + (1.0 - smoothstep(0.0, 0.02, e2)) * 0.3) * smoothstep(0.45, 0.62, vn(p * 1.3 + 2.2));   // broken, not closed polygons
    float block = (bid - 0.5) * 0.22 + smoothstep(0.0, 0.25, e1) * 0.1;   // each block its own plane, edges rounded
    float grain = fbm(w / 2.2);                                        // centimetre grain
    return big * 0.55 + ledge * 0.25 * sharp + block * 0.6 * sharp - crk * 0.18 * sharp + grain * 0.12;
  }
};
CRk k;
'''
# A: perturbed world normal (xyz) + height (w)
CODE_A = LIB + r'''
float e = 0.5;                                                   // cm: fine enough for the grain
float h0 = k.height(WP, Scale, Strata, Sharp);
float3 g = float3(k.height(WP + float3(e,0,0), Scale, Strata, Sharp) - h0,
                  k.height(WP + float3(0,e,0), Scale, Strata, Sharp) - h0,
                  k.height(WP + float3(0,0,e), Scale, Strata, Sharp) - h0) / e;
g -= dot(g, N) * N;
float3 n = normalize(N - g * Bump * 6.0);                        // 1.0 height = 6 cm relief
return float4(n, h0);
'''
# B: wet, puddle, soot, iron
CODE_B = LIB + r'''
float hb = saturate((WP.z - (OP.z - OB.z * 0.5)) / max(OB.z, 1.0));
float up = saturate(N.z), dn = saturate(-N.z), side = 1.0 - max(up, dn);
float streak = smoothstep(0.58, 0.8, k.vn(float3(WP.x / 35.0, WP.y / 35.0, WP.z / 700.0)));
float band = saturate(1.0 - hb / max(WetHeight, 0.01)) * side; band *= band;
float puddle = smoothstep(0.55, 0.62, k.vn(WP / 260.0) * 0.6 + (1.0 - H) * 0.55) * up * PuddleAmt;
float wet = saturate(max(max(band, up * 0.45), (streak * side + dn * 0.35) * DripAmt)) * Wetness;
wet = max(wet, puddle);
float soot = saturate(dn * 1.2 + side * smoothstep(0.65, 1.0, hb) * 0.6) * Soot * (0.7 + 0.3 * k.vn(WP / 90.0));
float iron = smoothstep(0.72, 0.86, k.vn(float3(WP.x / 22.0, WP.y / 22.0, WP.z / 500.0) + 3.7)) * side * Iron;
return float4(wet, puddle, soot, iron);
'''
# C: calcite, moss
CODE_C = LIB + r'''
float up = saturate(N.z), side = 1.0 - max(up, saturate(-N.z));
float streak = smoothstep(0.58, 0.8, k.vn(float3(WP.x / 35.0, WP.y / 35.0, WP.z / 700.0)));
float calcite = streak * side * Calcite * smoothstep(0.3, 0.7, k.vn(WP / 120.0 + 9.1));
float near = saturate(1.0 - distance(WP, MossOrigin.xyz) / max(MossRadius, 1.0));
float moss = near * saturate(N.z + 0.35) * Moss * smoothstep(0.42, 0.6, k.vn(WP / 55.0) * 0.6 + H * 0.5);
return float2(calcite, moss);
'''
# D: base colour (linear)
CODE_D = LIB + r'''
float t = saturate(H * 1.5 - 0.25);
float3 c = lerp(RockA.xyz, RockB.xyz, t);
c *= lerp(0.82, 1.15, k.h1(float3(floor(k.bed(WP, Scale, Strata)), 3.1, 7.7)));   // each bed its own tone
float bid2; float ee = k.cell(WP / Scale * 2.2 + k.vn(WP / Scale * 3.0) * 0.35, bid2);
c *= lerp(0.86, 1.12, bid2);                                    // blocks differ slightly in tone
c *= lerp(0.75, 1.0, smoothstep(0.0, 0.04, ee));                // grit / dirt in the cracks
c *= lerp(0.72, 1.0, saturate(H * 2.2));                       // dirt / shade in cavities
c = lerp(c, float3(0.45, 0.43, 0.39), MC.x);                    // calcite bloom (pale, ~180 sRGB)
c = lerp(c, float3(0.16, 0.065, 0.022), MB.w);                  // iron runs
c = lerp(c, float3(0.035, 0.05, 0.014), MC.y);                  // moss
c = lerp(c, float3(0.014, 0.013, 0.012), MB.z);                 // soot
c *= lerp(1.0, 0.5, saturate(Porosity * MB.x));                 // wet porous rock ~x0.5 (Lagarde)
return max(c, 0.0127);                                          // never below 30 sRGB
'''
# E: roughness
CODE_E = r'''
float r = lerp(0.9, 0.68, saturate(H));
r = lerp(r, 0.6, MC.y * 0.5);
r = lerp(r, 0.95, MB.z);
r = lerp(r, r * 0.42, MB.x);                                   // gloss comes first when wet
return lerp(r, 0.06, MB.y);                                    // puddles
'''
# F: final normal (puddles read flat)
CODE_F = r'''
return normalize(lerp(NA.xyz, float3(0, 0, 1), MB.y * 0.95));
'''
CODE_AO = r'''return lerp(0.55, 1.0, saturate(H * 1.8));'''

SCALARS = [('Scale', 140.0), ('Strata', 38.0), ('Sharp', 1.0), ('Bump', 1.0), ('Wetness', 1.0), ('WetHeight', 0.35),
           ('DripAmt', 0.6), ('PuddleAmt', 0.8), ('Porosity', 0.9), ('Soot', 0.0), ('Iron', 0.3), ('Calcite', 0.3),
           ('Moss', 0.0), ('MossRadius', 1500.0)]
VECTORS = [('RockA', (0.075, 0.068, 0.058, 1)), ('RockB', (0.24, 0.215, 0.18, 1)), ('MossOrigin', (0, 0, 0, 0))]
INSTANCES = {
    'MI_CaveRock_Natural': {'Sharp': 1.0, 'Bump': 1.1, 'Iron': 0.35, 'Calcite': 0.35, 'Moss': 0.6, 'Soot': 0.0},
    'MI_CaveRock_Mine': {'Sharp': 0.35, 'Bump': 0.55, 'Scale': 110.0, 'Soot': 0.6, 'Iron': 0.2, 'Calcite': 0.1, 'Wetness': 0.7, 'DripAmt': 0.4},
    'MI_CaveRock_Floor': {'Sharp': 0.5, 'Bump': 0.6, 'Scale': 90.0, 'PuddleAmt': 1.0, 'Wetness': 1.0, 'Iron': 0.0, 'Calcite': 0.0},
}


def build():
    path = DST + '/M_CaveRock'
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); log.append('rebuild ' + path)
        if DRY: return None
        MEL.delete_all_material_expressions(m)
    else:
        log.append('create ' + path)
        if DRY: return None
        m = AT.create_asset('M_CaveRock', DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('tangent_space_normal', False)          # the normal is computed in world space
    X = -2400
    E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    par = {}
    for i, (n, v) in enumerate(SCALARS):
        e = E(unreal.MaterialExpressionScalarParameter, X, -900 + i * 70); e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', v); par[n] = e
    for i, (n, v) in enumerate(VECTORS):
        e = E(unreal.MaterialExpressionVectorParameter, X, 200 + i * 160); e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', unreal.LinearColor(*v)); par[n] = e
    wp = E(unreal.MaterialExpressionWorldPosition, X, 700)
    nv = E(unreal.MaterialExpressionVertexNormalWS, X, 800)
    op = E(unreal.MaterialExpressionObjectPositionWS, X, 900)
    ob = E(unreal.MaterialExpressionObjectBounds, X, 1000)
    src = dict(par, WP=wp, N=nv, OP=op, OB=ob)

    def custom(name, code, ins, otype, x, y):
        e = E(unreal.MaterialExpressionCustom, x, y)
        e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', name)
        cis = []
        for n in ins:
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); cis.append(ci)
        e.set_editor_property('inputs', cis)
        for n in ins: MEL.connect_material_expressions(src[n], '', e, n)
        src[name] = e
        return e

    def mask(s, chans, name, x, y):
        e = E(unreal.MaterialExpressionComponentMask, x, y)
        for c in 'rgba': e.set_editor_property(c, c in chans)
        MEL.connect_material_expressions(s, '', e, ''); src[name] = e; return e

    F1, F2, F3, F4 = (enum(unreal.CustomMaterialOutputType, n) for n in ('CMOT_FLOAT1', 'CMOT_FLOAT2', 'CMOT_FLOAT3', 'CMOT_FLOAT4'))
    a = custom('NA', CODE_A, ['WP', 'N', 'Scale', 'Strata', 'Sharp', 'Bump'], F4, -1700, -400)
    mask(a, 'a', 'H', -1450, -300)
    b = custom('MB', CODE_B, ['WP', 'N', 'OP', 'OB', 'H', 'WetHeight', 'PuddleAmt', 'Wetness', 'DripAmt', 'Soot', 'Iron'], F4, -1200, 0)
    c = custom('MC', CODE_C, ['WP', 'N', 'H', 'Calcite', 'Moss', 'MossOrigin', 'MossRadius'], F2, -1200, 300)
    d = custom('Col', CODE_D, ['WP', 'H', 'MB', 'MC', 'RockA', 'RockB', 'Porosity', 'Scale', 'Strata'], F3, -700, -300)
    r = custom('Rough', CODE_E, ['H', 'MB', 'MC'], F1, -700, 0)
    n = custom('Nrm', CODE_F, ['NA', 'MB'], F3, -700, 300)
    ao = custom('AO', CODE_AO, ['H'], F1, -700, 500)
    MEL.connect_material_property(d, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(n, '', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(ao, '', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(m); EAL.save_asset(path)
    return m


def instances(base):
    for name, vals in INSTANCES.items():
        p = DST + '/' + name
        log.append(('update ' if EAL.does_asset_exist(p) else 'create ') + p + '  ' + ', '.join('%s=%s' % kv for kv in vals.items()))
        if DRY or not base: continue
        mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', base)
        for k_, v in vals.items(): MEL.set_material_instance_scalar_parameter_value(mi, k_, float(v))
        EAL.save_asset(p)


def apply(prefix, miname):
    mi = None if DRY else unreal.load_asset(DST + '/' + miname)
    if not DRY and not mi: raise SystemExit('missing ' + miname + ': run the script once without --apply first')
    rows = []
    for a in EAS.get_all_level_actors():
        if not a.get_actor_label().startswith(prefix): continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(c.get_num_materials()):
                old = c.get_material(i)
                rows.append('%s|%s|%d|%s' % (a.get_name(), c.get_name(), i, old.get_path_name() if old else ''))
                if mi: c.set_material(i, mi)
    log.append('apply %s -> %d slots on actors "%s*"' % (miname, len(rows), prefix))
    if rows and not DRY:
        open(SWAPLOG, 'a').write('\n'.join(rows) + '\n'); unreal.EditorLevelLibrary.save_current_level()


def revert():
    if not os.path.exists(SWAPLOG): raise SystemExit('nothing to revert')
    rows = [l.split('|') for l in open(SWAPLOG).read().splitlines() if l]
    want = {(r[0], r[1], int(r[2])): r[3] for r in rows}
    n = 0
    for a in EAS.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(c.get_num_materials()):
                old = want.get((a.get_name(), c.get_name(), i))
                if old is None: continue
                n += 1
                if not DRY and old: c.set_material(i, unreal.load_asset(old))
    log.append('revert %d slots' % n)
    if not DRY: os.rename(SWAPLOG, SWAPLOG + '.reverted'); unreal.EditorLevelLibrary.save_current_level()


if REVERT: revert()
elif APPLY:
    rest = [x for x in A[A.index('--apply') + 1:] if not x.startswith('--')]
    if len(rest) < 2: raise SystemExit('usage: --apply <ActorLabelPrefix> <MI name>')
    apply(rest[0], rest[1])
else:
    instances(build())
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_caverock296.txt'), 'w').write(out)
unreal.log(out)

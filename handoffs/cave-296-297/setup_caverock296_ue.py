# #296 Cave rock (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run. Rules: handoffs/cave-296-297/RESEARCH.md.
# Owner decision (2026-10-31): the rock base is a Megascans scan from the Master's PC; my procedural layers go on top
# (a fully procedural rock stayed stylised in 4 lookdev rounds, see KNOWLEDGE_LOG).
#   py "<repo>/handoffs/cave-296-297/setup_caverock296_ue.py" --list-scans                 READ-ONLY: every scanned surface in
#        the project (folders with BaseColor + Normal + ORM-type textures) -> scan_list.txt (push it / paste it on #296)
#   py ".../setup_caverock296_ue.py" --scan <folder> [--dry-run]                         makes the assets with that scan, swaps
#        nothing.  <folder> = a content path from scan_list.txt, e.g. /Game/Megascans/Surfaces/Rough_Rock_xyz
#   py ".../setup_caverock296_ue.py" --apply <ActorLabelPrefix> <MI name> [--dry-run]   ONLY after the owner's before/after OK
#   py ".../setup_caverock296_ue.py" --swap-entrance [--dry-run]   ONLY after the owner's OK: Mine_01's entrance mesh -> the
#        split mesh (scan rock + original timber), logged; removes the CaveRockLookdev copy
#   py ".../setup_caverock296_ue.py" --revert                                            puts every logged material / mesh back
#   py ".../setup_caverock296_ue.py" --auto [--dry-run]   ONE STEP (owner: "do it yourself"): picks the best rock scan in the
#        project, builds the materials, imports the rock/timber split entrance with the scan on the rock slot only, and places
#        a side-by-side copy (CaveRockLookdev) 11 m beside Mine_01 for the before/after. Swaps nothing live.
# Makes in /Game/CastleDefender/Environment/Cave:
#   M_CaveRock  the scan, world-projected on 3 axes (no UV stretching; whiteout normal blend), sampled twice (1x and 0.37x,
#               blended by noise) so it doesn't repeat; procedural limestone beds and large forms add relief and a tone shift
#               per bed; then, in physical order: calcite bloom on drip lines -> iron runs -> soot on ceilings (mine) -> moss
#               near the mouth only -> wetness (porous rock x0.5 darker, gloss first) -> flat puddles in low floor spots
#               (roughness 0.06, normal flattened 0.95). Albedo kept >= 30 sRGB (KB rule 1); metallic 0; specular 0.5.
#   MI_CaveRock_Natural / MI_CaveRock_Mine (fire-set: smoother, soot on the ceiling, drier) / MI_CaveRock_Floor (puddles)
import os, sys, unreal

A = sys.argv[1:]
DRY, APPLY, REVERT, LIST, AUTO = '--dry-run' in A, '--apply' in A, '--revert' in A, '--list-scans' in A, '--auto' in A
SCAN = A[A.index('--scan') + 1] if '--scan' in A and A.index('--scan') + 1 < len(A) else None
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\cave-296-297'
DST = '/Game/CastleDefender/Environment/Cave'
SWAPLOG = os.path.join(HERE, 'caverock296_swaps.txt')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
log = ['#296 cave rock' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


# ------------------------------------------------------------------------------------------------ scans
def role(name):
    n = name.lower()
    for suf, r in (('_b', 'B'), ('_basecolor', 'B'), ('_d', 'B'), ('_albedo', 'B'), ('_diffuse', 'B'), ('_n', 'N'), ('_normal', 'N'),
                   ('_orm', 'ORM'), ('_arm', 'ORM'), ('_ordp', 'ORM'), ('_ord', 'ORM')):
        if n.endswith(suf): return r
    return None


def scans():
    """{folder: {'B': tex, 'N': tex, 'ORM': tex}} for every folder that has all three."""
    out = {}
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')], package_paths=['/Game'], recursive_paths=True)
    for ad in AR.get_assets(flt):
        r = role(str(ad.asset_name))
        if r: out.setdefault(str(ad.package_path), {})[r] = '%s.%s' % (ad.package_name, ad.asset_name)
    return {k: v for k, v in out.items() if len(v) == 3}


def list_scans():
    rows = sorted(scans().items(), key=lambda kv: (not any(w in kv[0].lower() for w in ('rock', 'cliff', 'cave', 'stone', 'boulder', 'lime')), kv[0]))
    lines = ['%s | %s' % (f, ', '.join('%s=%s' % (k, v.split('.')[-1]) for k, v in sorted(t.items()))) for f, t in rows]
    open(os.path.join(HERE, 'scan_list.txt'), 'w').write('#296 scanned surfaces (rock-like first)\n' + '\n'.join(lines) + '\n')
    log.append('%d scanned surfaces -> scan_list.txt (push it, or paste it on card #296)' % len(lines))


def stype(tex):
    cs = str(tex.get_editor_property('compression_settings')).upper()
    if 'NORMAL' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if 'MASK' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    if 'GRAYSCALE' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE if tex.get_editor_property('srgb') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property('srgb') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR


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
  float bed(float3 w, float sc, float strataCm) { return w.z / max(strataCm, 1.0) + fbm(w / sc * 0.4) * 1.6; }
  float macro(float3 w, float sc, float strataCm, float sharp) {      // large forms + limestone ledges only; the scan has the detail
    float lay = frac(bed(w, sc, strataCm));
    float ledge = smoothstep(0.0, 0.12, lay) * (1.0 - lay * 0.6);
    return fbm(w / sc) * 0.7 + ledge * 0.3 * sharp;
  }
  float3 blendw(float3 n) { float3 b = pow(abs(n), 4.0); return b / (b.x + b.y + b.z); }
};
CRk k;
'''
# triplanar sample of a texture object T at scale s (cm per tile): returns the blended float4
TRI = r'''
#define TRI(T, S, w, bw, s) (Texture2DSample(T, S, (w).zy / (s)) * (bw).x + Texture2DSample(T, S, (w).xz / (s)) * (bw).y + Texture2DSample(T, S, (w).xy / (s)) * (bw).z)
'''
# A: world normal (scan whiteout triplanar + procedural macro relief) and H (0..1 "how high / exposed" for cavities + puddles)
CODE_A = LIB + r'''
float3 bw = k.blendw(N);
float3 nx = Texture2DSample(TexN, TexNSampler, WP.zy / ScanCm).xyz * 2.0 - 1.0;
float3 ny = Texture2DSample(TexN, TexNSampler, WP.xz / ScanCm).xyz * 2.0 - 1.0;
float3 nz = Texture2DSample(TexN, TexNSampler, WP.xy / ScanCm).xyz * 2.0 - 1.0;
nx.y *= FlipY; ny.y *= FlipY; nz.y *= FlipY;
nx.z = sqrt(saturate(1.0 - dot(nx.xy, nx.xy))); ny.z = sqrt(saturate(1.0 - dot(ny.xy, ny.xy))); nz.z = sqrt(saturate(1.0 - dot(nz.xy, nz.xy)));
nx.xy *= ScanBump; ny.xy *= ScanBump; nz.xy *= ScanBump;
nx = float3(nx.xy + N.zy, abs(nx.z) * N.x);                        // whiteout blend (Golus)
ny = float3(ny.xy + N.xz, abs(ny.z) * N.y);
nz = float3(nz.xy + N.xy, abs(nz.z) * N.z);
float3 ns = normalize(nx.zyx * bw.x + ny.xzy * bw.y + nz.xyz * bw.z);
float e = 2.0;
float h0 = k.macro(WP, Scale, Strata, Sharp);
float3 g = float3(k.macro(WP + float3(e,0,0), Scale, Strata, Sharp) - h0,
                  k.macro(WP + float3(0,e,0), Scale, Strata, Sharp) - h0,
                  k.macro(WP + float3(0,0,e), Scale, Strata, Sharp) - h0) / e;
g -= dot(g, ns) * ns;
float3 n = normalize(ns - g * Bump * 8.0);                          // 1.0 macro height = 8 cm relief
float ao = TRI(TexORM, TexORMSampler, WP, bw, ScanCm).r;
return float4(n, saturate(h0 * 0.6 + ao * 0.4));
'''
# S: scan base colour (rgb, two scales blended by noise = no visible repeat) + scan roughness (a)
CODE_S = LIB + r'''
float3 bw = k.blendw(N);
float3 c1 = TRI(TexB, TexBSampler, WP, bw, ScanCm).rgb;
float3 c2 = TRI(TexB, TexBSampler, WP, bw, ScanCm * 2.7).rgb;
float m = smoothstep(0.35, 0.65, k.vn(WP / (ScanCm * 3.0)));
float r1 = TRI(TexORM, TexORMSampler, WP, bw, ScanCm).g;
float r2 = TRI(TexORM, TexORMSampler, WP, bw, ScanCm * 2.7).g;
return float4(lerp(c1, c2, m), lerp(r1, r2, m));
'''
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
CODE_C = LIB + r'''
float up = saturate(N.z), side = 1.0 - max(up, saturate(-N.z));
float streak = smoothstep(0.58, 0.8, k.vn(float3(WP.x / 35.0, WP.y / 35.0, WP.z / 700.0)));
float calcite = streak * side * Calcite * smoothstep(0.3, 0.7, k.vn(WP / 120.0 + 9.1));
float near = saturate(1.0 - distance(WP, MossOrigin.xyz) / max(MossRadius, 1.0));
float moss = near * saturate(N.z + 0.35) * Moss * smoothstep(0.42, 0.6, k.vn(WP / 55.0) * 0.6 + H * 0.5);
return float2(calcite, moss);
'''
CODE_D = LIB + r'''
float3 c = SC.rgb * Tint.rgb;
c *= lerp(0.85, 1.12, k.h1(float3(floor(k.bed(WP, Scale, Strata)), 3.1, 7.7)));   // each limestone bed its own tone
c = lerp(c, float3(0.45, 0.43, 0.39), MC.x);                    // calcite bloom
c = lerp(c, float3(0.16, 0.065, 0.022), MB.w);                  // iron runs
c = lerp(c, float3(0.035, 0.05, 0.014), MC.y);                  // moss
c = lerp(c, float3(0.014, 0.013, 0.012), MB.z);                 // soot
c *= lerp(1.0, 0.5, saturate(Porosity * MB.x));                 // wet porous rock ~x0.5 (Lagarde)
return max(c, 0.0127);                                          // never below 30 sRGB
'''
CODE_E = r'''
float r = saturate(SC.a * RoughMul);
r = lerp(r, 0.6, MC.y * 0.5);
r = lerp(r, 0.95, MB.z);
r = lerp(r, r * 0.42, MB.x);                                   // gloss comes first when wet
return lerp(r, 0.06, MB.y);                                    // puddles
'''
CODE_F = r'''return normalize(lerp(NA.xyz, float3(0, 0, 1), MB.y * 0.95));'''
CODE_AO = r'''return lerp(0.55, 1.0, saturate(H * 1.6));'''

SCALARS = [('ScanCm', 220.0), ('ScanBump', 1.0), ('FlipY', 1.0), ('RoughMul', 1.0), ('Scale', 160.0), ('Strata', 38.0),
           ('Sharp', 1.0), ('Bump', 1.0), ('Wetness', 1.0), ('WetHeight', 0.35), ('DripAmt', 0.6), ('PuddleAmt', 0.8),
           ('Porosity', 0.9), ('Soot', 0.0), ('Iron', 0.3), ('Calcite', 0.3), ('Moss', 0.0), ('MossRadius', 1500.0)]
VECTORS = [('Tint', (1, 1, 1, 1)), ('MossOrigin', (0, 0, 0, 0))]
INSTANCES = {
    'MI_CaveRock_Natural': {'Sharp': 1.0, 'Bump': 1.0, 'Iron': 0.35, 'Calcite': 0.35, 'Moss': 0.6, 'Soot': 0.0},
    'MI_CaveRock_Mine': {'Sharp': 0.2, 'Bump': 0.5, 'ScanBump': 0.6, 'Soot': 0.6, 'Iron': 0.2, 'Calcite': 0.1, 'Wetness': 0.7, 'DripAmt': 0.4},
    'MI_CaveRock_Floor': {'Sharp': 0.3, 'Bump': 0.4, 'ScanCm': 160.0, 'PuddleAmt': 1.0, 'Wetness': 1.0, 'Iron': 0.0, 'Calcite': 0.0},
}


def build(tex):
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
    src = {}
    for i, (n, v) in enumerate(SCALARS):
        e = E(unreal.MaterialExpressionScalarParameter, X, -1200 + i * 70); e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', v); src[n] = e
    for i, (n, v) in enumerate(VECTORS):
        e = E(unreal.MaterialExpressionVectorParameter, X, 200 + i * 160); e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', unreal.LinearColor(*v)); src[n] = e
    for i, (n, key) in enumerate((('TexB', 'B'), ('TexN', 'N'), ('TexORM', 'ORM'))):
        t = unreal.load_asset(tex[key])
        e = E(unreal.MaterialExpressionTextureObjectParameter, X, 600 + i * 220)
        e.set_editor_property('parameter_name', n); e.set_editor_property('texture', t); e.set_editor_property('sampler_type', stype(t)); src[n] = e
    src['WP'] = E(unreal.MaterialExpressionWorldPosition, X, 1400)
    src['N'] = E(unreal.MaterialExpressionVertexNormalWS, X, 1500)
    src['OP'] = E(unreal.MaterialExpressionObjectPositionWS, X, 1600)
    src['OB'] = E(unreal.MaterialExpressionObjectBounds, X, 1700)

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
    a = custom('NA', CODE_A.replace('CRk k;', 'CRk k;' + TRI), ['WP', 'N', 'TexN', 'TexORM', 'ScanCm', 'ScanBump', 'FlipY', 'Scale', 'Strata', 'Sharp', 'Bump'], F4, -1700, -500)
    mask(a, 'a', 'H', -1450, -400)
    custom('SC', CODE_S.replace('CRk k;', 'CRk k;' + TRI), ['WP', 'N', 'TexB', 'TexORM', 'ScanCm'], F4, -1700, -150)
    custom('MB', CODE_B, ['WP', 'N', 'OP', 'OB', 'H', 'WetHeight', 'PuddleAmt', 'Wetness', 'DripAmt', 'Soot', 'Iron'], F4, -1200, 0)
    custom('MC', CODE_C, ['WP', 'N', 'H', 'Calcite', 'Moss', 'MossOrigin', 'MossRadius'], F2, -1200, 300)
    d = custom('Col', CODE_D, ['WP', 'SC', 'MB', 'MC', 'Tint', 'Porosity', 'Scale', 'Strata'], F3, -700, -300)
    r = custom('Rough', CODE_E, ['SC', 'MB', 'MC', 'RoughMul'], F1, -700, 0)
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
    if not DRY and not mi: raise SystemExit('missing ' + miname + ': run --scan first')
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


MESHLOG = os.path.join(HERE, 'caverock296_meshswaps.txt')
ME_DIR = '/Game/CastleDefender/Environment/Mine/MineEntrance'


def swap_entrance():
    """after the owner's OK: every SM_Camp_MineEntrance component in the level -> SM_Camp_MineEntrance_Split (same pivot /
    size), logged for --revert; the CaveRockLookdev copy is removed."""
    new = unreal.load_asset(ME_DIR + '/SM_Camp_MineEntrance_Split')
    if not new: raise SystemExit('missing SM_Camp_MineEntrance_Split: run --auto first')
    rows = []
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == 'CaveRockLookdev': continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if m and m.get_name() == 'SM_Camp_MineEntrance':
                rows.append('%s|%s|%s' % (a.get_name(), c.get_name(), m.get_path_name()))
                log.append('swap mesh on %s (%s)' % (a.get_actor_label(), c.get_name()))
                if not DRY:
                    c.set_static_mesh(new)
                    for i in range(c.get_num_materials()): c.set_material(i, None)   # use the Split mesh's own slots
    log.append('swap-entrance: %d components' % len(rows))
    if not DRY:
        if rows: open(MESHLOG, 'a').write('\n'.join(rows) + '\n')
        for a in EAS.get_all_level_actors():
            if a.get_actor_label() == 'CaveRockLookdev': EAS.destroy_actor(a); log.append('removed CaveRockLookdev')
        unreal.EditorLevelLibrary.save_current_level()


def revert():
    if os.path.exists(MESHLOG):
        want = {(r[0], r[1]): r[2] for r in (l.split('|') for l in open(MESHLOG).read().splitlines() if l)}
        k = 0
        for a in EAS.get_all_level_actors():
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                old = want.get((a.get_name(), c.get_name()))
                if old:
                    k += 1
                    if not DRY: c.set_static_mesh(unreal.load_asset(old))
        log.append('revert %d entrance meshes' % k)
        if not DRY: os.rename(MESHLOG, MESHLOG + '.reverted')
        if not os.path.exists(SWAPLOG):
            if not DRY: unreal.EditorLevelLibrary.save_current_level()
            return
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


if LIST: list_scans()
elif REVERT: revert()
elif '--swap-entrance' in A: swap_entrance()
elif APPLY:
    rest = [x for x in A[A.index('--apply') + 1:] if not x.startswith('--')]
    if len(rest) < 2: raise SystemExit('usage: --apply <ActorLabelPrefix> <MI name>')
    apply(rest[0], rest[1])
elif AUTO:
    # owner 2026-10-31: "do the megascans yourself" -> pick the scan, build, and set up the entrance lookdev in one go
    found = scans()
    def score(f):
        n = f.lower(); sc = 0
        for w, pts in (('cave', 6), ('limestone', 6), ('rock', 5), ('cliff', 5), ('boulder', 4), ('stone', 3), ('rough', 1), ('wet', 1), ('mossy', -2),
                       ('brick', -6), ('wall', -4), ('plaster', -6), ('tile', -6), ('wood', -8), ('metal', -8), ('ground', -2), ('soil', -3), ('sand', -3)):
            if w in n: sc += pts
        return sc
    ranked = sorted(found, key=lambda f: (-score(f), f))
    for f in ranked[:8]: log.append('  candidate %3d  %s' % (score(f), f))
    if not ranked or score(ranked[0]) <= 0: raise SystemExit('no rock-like scan found (see the candidates above): run --scan <folder> by hand')
    SCAN = ranked[0]; tex = found[SCAN]
    log.append('AUTO picked %s: %s' % (SCAN, ', '.join('%s=%s' % (k_, v.split('.')[-1]) for k_, v in sorted(tex.items()))))
    instances(build(tex))
    # the split mine entrance (rock slot 0 / timber slot 1) and a side-by-side lookdev copy next to Mine_01
    fbx = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'adjustedfilm', 'MineEntranceSplit296', 'SM_Camp_MineEntrance_Split.fbx'))
    ME = '/Game/CastleDefender/Environment/Mine/MineEntrance'
    log.append('import ' + ME + '/SM_Camp_MineEntrance_Split' + ('' if os.path.exists(fbx) else ' (MISSING ' + fbx + ')'))
    if not DRY and os.path.exists(fbx):
        t = unreal.AssetImportTask()
        for k_, v in (('filename', fbx), ('destination_path', ME), ('destination_name', 'SM_Camp_MineEntrance_Split'), ('replace_existing', True), ('automated', True), ('save', True)):
            t.set_editor_property(k_, v)
        o = unreal.FbxImportUI(); o.set_editor_property('import_mesh', True); o.set_editor_property('import_as_skeletal', False)
        o.set_editor_property('import_materials', False); o.set_editor_property('import_textures', False)
        o.static_mesh_import_data.set_editor_property('combine_meshes', True)
        o.static_mesh_import_data.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
        t.set_editor_property('options', o); AT.import_asset_tasks([t])
        sm = unreal.load_asset(ME + '/SM_Camp_MineEntrance_Split')
        old = unreal.load_asset(ME + '/SM_Camp_MineEntrance')
        if sm and old:
            bs = old.get_editor_property('body_setup'); nb = sm.get_editor_property('body_setup')
            if bs and nb: nb.set_editor_property('collision_trace_flag', bs.get_editor_property('collision_trace_flag'))
            sm.set_material(0, unreal.load_asset(DST + '/MI_CaveRock_Natural'))
            om = old.get_material(0)
            if om: sm.set_material(1, om)
            EAL.save_asset(ME + '/SM_Camp_MineEntrance_Split')
    mine = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Mine_01']
    if mine:
        m0 = mine[0]; loc = m0.get_actor_location() + m0.get_actor_right_vector() * 1100.0
        log.append('lookdev copy CaveRockLookdev 11 m to the side of Mine_01 at %s (same rotation)' % loc)
        if not DRY:
            for a in EAS.get_all_level_actors():
                if a.get_actor_label() == 'CaveRockLookdev': EAS.destroy_actor(a)
            act = EAS.spawn_actor_from_class(unreal.StaticMeshActor, loc, m0.get_actor_rotation()); act.set_actor_label('CaveRockLookdev')
            act.static_mesh_component.set_static_mesh(unreal.load_asset(ME + '/SM_Camp_MineEntrance_Split'))
            unreal.EditorLevelLibrary.save_current_level()
    else: log.append('Mine_01 not found: place SM_Camp_MineEntrance_Split by hand for the before/after')
elif SCAN:
    tex = scans().get(SCAN.rstrip('/'))
    if not tex: raise SystemExit('no B + N + ORM textures in %s (see --list-scans)' % SCAN)
    log.append('scan %s: %s' % (SCAN, ', '.join('%s=%s' % (k_, v.split('.')[-1]) for k_, v in sorted(tex.items()))))
    instances(build(tex))
else:
    raise SystemExit('run --list-scans first, then --scan <folder> (see the header)')
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_caverock296.txt'), 'w').write(out)
unreal.log(out)

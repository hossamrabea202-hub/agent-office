# #293 part 2: blob mine as flesh, not a pastel glowing plant (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
# Rules: handoffs/blob-realism-293/RESEARCH.md (dark organics 0.03-0.15 albedo, wet 0.05-0.15 / tacky 0.35-0.5 roughness,
# life through subsurface not emission, one faint danger pulse). Same logic as the Blender lookdev in
# assets/adjustedfilm/FleshSlime293 (3rd round), procedural on (world position - object position) (no textures, no UVs).
#   py "<repo>/handoffs/blob-realism-293/setup_flesh293_ue.py" --dry-run            only reports
#   py "<repo>/handoffs/blob-realism-293/setup_flesh293_ue.py"                      makes M_FleshSlime + MI_BlobMine_Flesh, swaps nothing
#   py ".../setup_flesh293_ue.py" --lookdev [--dry-run]                            places a copy of the blob mine beside Realm_BlobMine_04
#        with the new MI (label FleshLookdev) for the owner's before/after; --lookdev-remove deletes it again
#   py ".../setup_flesh293_ue.py" --apply [--dry-run]                              ONLY after the owner's OK: BP_BlobMine's Mine
#        component gets MI_BlobMine_Flesh (logged in flesh293_swap.txt); --revert puts MI_Flora_BlobMine back
import os, sys, unreal

A = sys.argv[1:]
DRY = '--dry-run' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\blob-realism-293'
DST = '/Game/CastleDefender/Environment/Flora/BlobMine'
BP = '/Game/CastleDefender/Realm/BP_BlobMine'
OLD = DST + '/MI_Flora_BlobMine.MI_Flora_BlobMine'
EAL, MEL, BEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#293 flesh setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


LIB = r'''
struct FS {
  float h1(float3 p) { p = frac(p * 0.3183099 + 0.1); p *= 17.0; return frac(p.x * p.y * p.z * (p.x + p.y + p.z)); }
  float vn(float3 x) { float3 i = floor(x); float3 f = frac(x); f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(lerp(h1(i), h1(i + float3(1,0,0)), f.x), lerp(h1(i + float3(0,1,0)), h1(i + float3(1,1,0)), f.x), f.y),
                lerp(lerp(h1(i + float3(0,0,1)), h1(i + float3(1,0,1)), f.x), lerp(h1(i + float3(0,1,1)), h1(i + float3(1,1,1)), f.x), f.y), f.z); }
  float fbm(float3 p) { float a = 0.5, s = 0.0; for (int o = 0; o < 4; o++) { s += a * vn(p); p = p * 2.03 + 17.1; a *= 0.5; } return s / 0.9375; }
  float veins(float3 w, float vs) { float3 p = w / vs;
    float3 q = p + float3(fbm(p * 0.7), fbm(p * 0.7 + 5.2), fbm(p * 0.7 + 9.4)) * 1.8;
    float v = 1.0 - abs(vn(q) * 2.0 - 1.0); float v2 = 1.0 - abs(vn(q * 2.3 + 3.3) * 2.0 - 1.0);
    return saturate(pow(v, 9.0) + pow(v2, 12.0) * 0.6); }
  float height(float3 w, float lump, float vs) { return fbm(w / lump) * 0.45 + veins(w, vs) * 0.55 + fbm(w / 0.7) * 0.1 + fbm(w / 12.0) * 0.4; }
};
FS k;
'''
CODE_N = LIB + r'''
float e = 0.25;
float h0 = k.height(LP, Lump, VeinCm);
float3 g = float3(k.height(LP + float3(e,0,0), Lump, VeinCm) - h0, k.height(LP + float3(0,e,0), Lump, VeinCm) - h0, k.height(LP + float3(0,0,e), Lump, VeinCm) - h0) / e;
float3 gw = g;                                             // P is world-oriented (object-anchored), so g is already world
gw -= dot(gw, N) * N;
return normalize(N - gw * Bump);
'''
CODE_C = LIB + r'''
float lump = k.fbm(LP / Lump); float vm = k.veins(LP, VeinCm);
float3 c = lerp(float3(0.055, 0.02, 0.02), float3(0.11, 0.05, 0.042), smoothstep(0.3, 0.75, lump));
float rot = smoothstep(0.55, 0.75, k.fbm(LP / 25.0 + 4.4)) * Rot;
c = lerp(c, float3(0.055, 0.06, 0.03), rot);
c = lerp(c, float3(0.03, 0.008, 0.02), vm * 0.7);
float wet = smoothstep(0.55, 0.68, k.fbm(LP / 14.0 + 1.3)) * WetAmt;
c *= lerp(1.0, 0.8, wet);
return max(c, 0.012);
'''
CODE_R = LIB + r'''
float pores = k.fbm(LP / 0.7);
float wet = smoothstep(0.55, 0.68, k.fbm(LP / 14.0 + 1.3)) * WetAmt;
return lerp(lerp(0.42, 0.48, pores), lerp(0.07, 0.12, pores), wet);
'''
CODE_S = LIB + r'''
float vm = k.veins(LP, VeinCm);
float pulse = 0.5 + 0.5 * sin(T * 6.2831853 * PulseHz);
return float3(0.55, 0.05, 0.035) * (0.55 + 0.45 * pulse * Pulse) * lerp(1.0, 1.6, vm);
'''
CODE_E = LIB + r'''
float vm = k.veins(LP, VeinCm);
float pulse = 0.5 + 0.5 * sin(T * 6.2831853 * PulseHz);
return float3(0.5, 0.04, 0.03) * vm * pulse * Danger;                 // barely there: the one danger cue
'''
SCAL = [('Lump', 3.5), ('VeinCm', 4.0), ('Rot', 0.7), ('WetAmt', 0.6), ('Bump', 1.2), ('Pulse', 1.0), ('PulseHz', 0.35), ('Danger', 0.6)]


def build():
    path = DST + '/M_FleshSlime'
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); log.append('rebuild ' + path)
        if DRY: return None
        MEL.delete_all_material_expressions(m)
    else:
        log.append('create ' + path)
        if DRY: return None
        m = AT.create_asset('M_FleshSlime', DST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', enum(unreal.MaterialShadingModel, 'MSM_SUBSURFACE'))
    m.set_editor_property('tangent_space_normal', False)
    E = lambda c, x, y: MEL.create_material_expression(m, c, x, y)
    wp, op = E(unreal.MaterialExpressionWorldPosition, -1900, 0), E(unreal.MaterialExpressionObjectPositionWS, -1900, 80)
    rel = E(unreal.MaterialExpressionSubtract, -1700, 0); MEL.connect_material_expressions(wp, '', rel, 'A'); MEL.connect_material_expressions(op, '', rel, 'B')
    src = {'LP': rel, 'N': E(unreal.MaterialExpressionVertexNormalWS, -1600, 100),
           'T': E(unreal.MaterialExpressionTime, -1600, 200)}
    for i, (n, v) in enumerate(SCAL):
        e = E(unreal.MaterialExpressionScalarParameter, -1600, 300 + i * 70); e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', v); src[n] = e

    def custom(name, code, ins, otype, x, y):
        e = E(unreal.MaterialExpressionCustom, x, y)
        e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', name)
        cis = []
        for n in ins:
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); cis.append(ci)
        e.set_editor_property('inputs', cis)
        for n in ins: MEL.connect_material_expressions(src[n], '', e, n)
        return e
    F1, F3 = enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT1'), enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3')
    nrm = custom('Nrm', CODE_N, ['LP', 'N', 'Lump', 'VeinCm', 'Bump'], F3, -900, 300)
    col = custom('Col', CODE_C, ['LP', 'Lump', 'VeinCm', 'Rot', 'WetAmt'], F3, -900, -300)
    rgh = custom('Rough', CODE_R, ['LP', 'WetAmt'], F1, -900, 0)
    sss = custom('SSS', CODE_S, ['LP', 'VeinCm', 'T', 'Pulse', 'PulseHz'], F3, -900, 600)
    ems = custom('Emis', CODE_E, ['LP', 'VeinCm', 'T', 'PulseHz', 'Danger'], F3, -900, 850)
    spec = E(unreal.MaterialExpressionConstant, -600, 150); spec.set_editor_property('r', 0.4)
    opa = E(unreal.MaterialExpressionConstant, -600, 750); opa.set_editor_property('r', 0.6)
    for e_, p in ((col, unreal.MaterialProperty.MP_BASE_COLOR), (rgh, unreal.MaterialProperty.MP_ROUGHNESS), (nrm, unreal.MaterialProperty.MP_NORMAL),
                  (sss, unreal.MaterialProperty.MP_SUBSURFACE_COLOR), (ems, unreal.MaterialProperty.MP_EMISSIVE_COLOR), (spec, unreal.MaterialProperty.MP_SPECULAR),
                  (opa, unreal.MaterialProperty.MP_OPACITY)):
        MEL.connect_material_property(e_, '', p)
    MEL.recompile_material(m); EAL.save_asset(path)
    return m


def mi(base):
    p = DST + '/MI_BlobMine_Flesh'
    log.append(('update ' if EAL.does_asset_exist(p) else 'create ') + p)
    if DRY or not base: return
    x = unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset('MI_BlobMine_Flesh', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    x.set_editor_property('parent', base); EAL.save_asset(p)


def bp_mine_comp():
    bp = unreal.load_asset(BP)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_object(sds.k2_find_subobject_data_from_handle(h))
        if isinstance(o, unreal.StaticMeshComponent) and str(lib.get_variable_name(sds.k2_find_subobject_data_from_handle(h))) == 'Mine': return bp, o
    return bp, None


if '--lookdev-remove' in A:
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == 'FleshLookdev':
            log.append('remove FleshLookdev')
            if not DRY: EAS.destroy_actor(a)
    if not DRY: unreal.EditorLevelLibrary.save_current_level()
elif '--lookdev' in A:
    src = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Realm_BlobMine_04']
    if not src: raise SystemExit('Realm_BlobMine_04 not found')
    loc = src[0].get_actor_location() + unreal.Vector(250, 0, 0)
    log.append('lookdev copy beside Realm_BlobMine_04 at %s' % loc)
    if not DRY:
        sm = unreal.load_asset(DST + '/SM_Flora_BlobMine')
        act = EAS.spawn_actor_from_class(unreal.StaticMeshActor, loc, src[0].get_actor_rotation()); act.set_actor_label('FleshLookdev')
        c = act.static_mesh_component; c.set_static_mesh(sm); c.set_material(0, unreal.load_asset(DST + '/MI_BlobMine_Flesh'))
        unreal.EditorLevelLibrary.save_current_level()
elif '--apply' in A or '--revert' in A:
    bp, c = bp_mine_comp()
    if not c: raise SystemExit('BP_BlobMine has no StaticMeshComponent named Mine')
    new = OLD if '--revert' in A else DST + '/MI_BlobMine_Flesh.MI_BlobMine_Flesh'
    log.append('BP_BlobMine.Mine slot 0 -> ' + new)
    if not DRY:
        c.set_material(0, unreal.load_asset(new)); BEL.compile_blueprint(bp); EAL.save_asset(BP)
        open(os.path.join(HERE, 'flesh293_swap.txt'), 'a').write('BP_BlobMine.Mine[0] -> %s (was %s)\n' % (new, OLD if '--apply' in A else 'MI_BlobMine_Flesh'))
else:
    mi(build())
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_flesh293.txt'), 'a').write(out + '\n')
unreal.log(out)

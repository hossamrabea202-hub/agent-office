# #293 part 1: the realm bubble as a "petrol slick" thin film, not a glowing purple shield (adjustedfilm, 2026-10-31).
#   py "<repo>/handoffs/blob-realism-293/make_realm_bubble3_ue.py" --dry-run    (only reports)
#   py "<repo>/handoffs/blob-realism-293/make_realm_bubble3_ue.py"              (makes M_RealmBubble3 + MI_RealmBubble3; nothing live changes)
#   ... --apply     after the owner's OK: puts MI_RealmBubble3 on every level actor whose mesh is SM_RealmDome (old material logged)
#   ... --revert    puts the logged old material back
# Research: RESEARCH.md (Annihilation's Shimmer, DNEG: mostly clear, interference colour only at grazing angles, fractal drift).
# Look: translucent, lit (surface forward shading: sharp sun and sky reflections like a soap film), base colour near black,
# roughness 0.04. Emissive = thin-film interference hue x fresnel, desaturated, dimmer at night (MPC_DayNight.Night).
# Opacity 0.03 head-on -> 0.35 at the rim. Dark drifting tentacle silhouettes (as #169) block the film where they pass.
# MI params: FilmGlow 0.6, OpacityHead 0.03, OpacityRim 0.35, FilmScale 1.0, TentacleScale 3.0, TentacleAmount 0.12.
import os, sys, unreal

DRY, APPLY, REVERT = '--dry-run' in sys.argv, '--apply' in sys.argv, '--revert' in sys.argv
ROOT = '/Game/CastleDefender/Realm'
MPC_DN = '/Game/CastleDefender/Environment/DayNight/MPC_DayNight'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\blob-realism-293'
LOG = os.path.join(HERE, 'realm_bubble3_swap.txt')
log = ['#293 realm bubble 3' + (' (DRY RUN)' if DRY else '')]


def vnoise(out, p, seed):
    return '''float %(o)s; { float2 q = %(p)s + %(s)s; float2 i = floor(q), f = frac(q); f = f * f * (3.0 - 2.0 * f);
  float a = frac(sin(dot(i, float2(127.1, 311.7))) * 43758.5453), b = frac(sin(dot(i + float2(1, 0), float2(127.1, 311.7))) * 43758.5453);
  float c = frac(sin(dot(i + float2(0, 1), float2(127.1, 311.7))) * 43758.5453), d = frac(sin(dot(i + float2(1, 1), float2(127.1, 311.7))) * 43758.5453);
  %(o)s = lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y); }
''' % {'o': out, 'p': p, 's': seed}

CODE = 'float2 p = UV * float2(6.0, 3.0) * FilmScale;\n' + vnoise('w1', 'p * 0.7 + T * 0.02', '5.3') \
    + vnoise('th', 'p + w1 * 1.5 + T * 0.015', '11.9') \
    + vnoise('tn', 'UV * float2(TentacleScale * 2.0, TentacleScale) + float2(T * 0.010, -T * 0.006)', '29.4') + '''
float k = th * 2.2 + F * 0.8;
float3 film = 0.5 + 0.5 * cos(6.2831853 * (k + float3(0.0, 0.33, 0.67)));
film = lerp(dot(film, float3(0.333, 0.333, 0.333)).xxx, film, 0.55);
float3 em = film * F * FilmGlow * lerp(1.0, 0.35, saturate(Night));
float tent = smoothstep(0.55, 0.75, tn);
em *= 1.0 - tent;
float op = lerp(OpacityHead, OpacityRim, F) + tent * TentacleAmount;
return float4(em, saturate(op));
'''


def swap():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if REVERT:
        if not os.path.exists(LOG): raise SystemExit('no swap log at ' + LOG)
        for line in open(LOG).read().splitlines():
            name, idx, old = line.split('|')
            for a in eas.get_all_level_actors():
                if a.get_name() == name:
                    for c in a.get_components_by_class(unreal.StaticMeshComponent):
                        if not DRY: c.set_material(int(idx), unreal.load_asset(old))
                        log.append('revert %s slot %s -> %s' % (name, idx, old))
        return
    mi = unreal.load_asset(ROOT + '/MI_RealmBubble3')
    out = []
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = c.get_editor_property('static_mesh')
            if sm and sm.get_name() == 'SM_RealmDome':
                for i in range(c.get_num_materials()):
                    old = c.get_material(i)
                    out.append('%s|%d|%s' % (a.get_name(), i, old.get_path_name() if old else ''))
                    log.append('apply %s slot %d (was %s)' % (a.get_name(), i, old.get_name() if old else 'none'))
                    if not DRY: c.set_material(i, mi)
    if not DRY and out: open(LOG, 'w').write('\n'.join(out))
    if not out: log.append('no SM_RealmDome actor in this level')


if APPLY or REVERT:
    swap()
else:
    path = ROOT + '/M_RealmBubble3'
    log.append(('rebuild ' if EAL.does_asset_exist(path) else 'create ') + path + ' + MI_RealmBubble3')
    if not DRY:
        m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset('M_RealmBubble3', ROOT, unreal.Material, unreal.MaterialFactoryNew())
        MEL.delete_all_material_expressions(m)
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property('two_sided', True)
        for v in ('TLM_SURFACE_PER_PIXEL_LIGHTING', 'TLM_SURFACE'):
            if hasattr(unreal.TranslucencyLightingMode, v): m.set_editor_property('translucency_lighting_mode', getattr(unreal.TranslucencyLightingMode, v)); break
        cu = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -400, 0)
        cu.set_editor_property('code', CODE); cu.set_editor_property('description', 'RealmBubble3')
        cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
        params = [('FilmGlow', 0.6), ('OpacityHead', 0.03), ('OpacityRim', 0.35), ('FilmScale', 1.0), ('TentacleScale', 3.0), ('TentacleAmount', 0.12)]
        ins = []
        for n in ['UV', 'T', 'F', 'Night'] + [p for p, _ in params]:
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        cu.set_editor_property('inputs', ins)
        MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, -300), '', cu, 'UV')
        MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, -200), '', cu, 'T')
        fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -900, -100); fr.set_editor_property('exponent', 3.0)
        MEL.connect_material_expressions(fr, '', cu, 'F')
        if EAL.does_asset_exist(MPC_DN):
            ni = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -900, 0)
            ni.set_editor_property('collection', unreal.load_asset(MPC_DN)); ni.set_editor_property('parameter_name', 'Night')
        else:
            ni = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 0); log.append('MPC_DayNight missing: Night = 0')
        MEL.connect_material_expressions(ni, '', cu, 'Night')
        for i, (n, v) in enumerate(params):
            s = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 120 + i * 100)
            s.set_editor_property('parameter_name', n); s.set_editor_property('default_value', v)
            MEL.connect_material_expressions(s, '', cu, n)
        rgb = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -100, 0)
        for ch, on in zip('rgba', (True, True, True, False)): rgb.set_editor_property(ch, on)
        al = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -100, 150)
        for ch, on in zip('rgba', (False, False, False, True)): al.set_editor_property(ch, on)
        MEL.connect_material_expressions(cu, '', rgb, ''); MEL.connect_material_expressions(cu, '', al, '')
        base = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -100, -200)
        base.set_editor_property('constant', unreal.LinearColor(0.015, 0.014, 0.016, 1))
        rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -100, 300); rough.set_editor_property('r', 0.04)
        MEL.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(rgb, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.connect_material_property(al, '', unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(m); EAL.save_asset(path)
        mip = ROOT + '/MI_RealmBubble3'
        mi = unreal.load_asset(mip) if EAL.does_asset_exist(mip) else AT.create_asset('MI_RealmBubble3', ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', m); EAL.save_asset(mip)
unreal.log('\n'.join(log))

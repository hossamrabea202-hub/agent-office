# #381 Realm vision v2, editor setup (adjustedfilm, 2026-10-31 late). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/realm-vision-376/setup_realmvision381_ue.py" --check          READ-ONLY: every post-process volume that touches
#                                                                                   the realm (what makes it dark), the bubble's material
#   py ".../setup_realmvision381_ue.py" [--dry-run]       NEW assets + BP_RealmVision look:
#        MPC_RealmDream (Amount, Cross, CrossDir, BreathHz), M_RealmDream + MI_RealmDream (dream post-process, tunable on the MI),
#        the jelly copy of the bubble material (*_Jelly: breathing, travelling ripples, wobble, in place), and the bright
#        pink-orange look + MI_RealmDream blendable on BP_RealmVision's Vision (and on the placed Realm_Vision)
#   py ".../setup_realmvision381_ue.py" --swap-bubble [--dry-run]     AFTER THE OWNER'S OK: the bubble shows the jelly copy (backup json)
#   py ".../setup_realmvision381_ue.py" --revert-bubble                puts the bubble's material back
#   py ".../setup_realmvision381_ue.py" --mute-old-ppv / --unmute-old-ppv   only if --check shows an old realm volume darkening it
# The owner's bubble mesh, its transform and its CURRENT material are never edited (the jelly is a copy). No decal is touched.
import os, sys, json, unreal

A = sys.argv[1:]
DRY = '--dry-run' in A
MODE = next((m for m in ('--check', '--swap-bubble', '--revert-bubble', '--mute-old-ppv', '--unmute-old-ppv') if m in A), 'setup')
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\realm-vision-376'
DEST = '/Game/CastleDefender/Gameplay/Realm'
BP, MPC = DEST + '/BP_RealmVision', DEST + '/MPC_RealmDream'
BUBBLE_LABEL, VISION_LABEL = 'Realm_Bubble_Owner', 'Realm_Vision'
BACKUP = os.path.join(HERE, 'realmvision381_backup.json')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#381 realm vision v2 %s%s' % (MODE, ' (DRY RUN)' if DRY else '')]

# the owner: "pinkish orange semi scary fantasy, comfortable yet unsettling dream" + "very very dark" -> warm, lifted, brighter
LOOK = [('auto_exposure_bias', 0.25), ('color_saturation', unreal.Vector4(1.08, 0.98, 1.02, 1.0)), ('color_contrast', unreal.Vector4(0.94, 0.94, 0.94, 1.0)),
        ('color_gain', unreal.Vector4(1.08, 0.97, 0.95, 1.0)), ('color_gamma', unreal.Vector4(1.04, 1.0, 1.0, 1.0)),
        ('color_offset', unreal.Vector4(0.015, 0.004, 0.010, 0.0)), ('scene_color_tint', unreal.LinearColor(1.0, 0.90, 0.86, 1.0)),
        ('white_temp', 7200.0), ('bloom_intensity', 2.0), ('scene_fringe_intensity', 1.2), ('vignette_intensity', 0.25), ('film_grain_intensity', 0.2)]
DREAM_PARAMS = [('Warp', 1.0), ('Ghost', 1.0), ('Glow', 1.0), ('Lift', 1.0), ('Haze', 1.0), ('Lens', 1.0), ('Chroma', 1.0), ('Heart', 1.0), ('HeartHz', 0.75)]
JELLY_PARAMS = [('JellyBreath', 0.015), ('JellyRipple', 60.0), ('JellyRippleLen', 1500.0), ('JellyRippleSpeed', 300.0), ('JellyWobble', 0.01)]

DREAM_HLSL = r'''
float2 uv = GetDefaultSceneTextureUV(Parameters, 14);
float a = saturate(Amt), c = saturate(Cross);
float3 base = SceneTextureLookup(uv, 14, false).rgb + Dummy.rgb * 0.0;
if (a < 0.002 && c < 0.002) return base;
float asp = Inv.y / max(Inv.x, 1e-6);
float2 d = uv - 0.5, da = d * float2(asp, 1.0);
float r = length(da);
float br = sin(T * 6.2831853 * Hz);
// slow sinuous dream flow, stronger towards the edges
float2 w = float2(sin(uv.y * 6.0 + T * 0.6) + 0.5 * sin(uv.y * 13.0 - T * 0.9), sin(uv.x * 5.0 - T * 0.5) + 0.5 * sin(uv.x * 11.0 + T * 0.7));
float2 off = w * 0.0045 * Warp * a * (0.35 + 1.6 * r);
off += -d * 0.008 * a * br;                                                    // the view breathes with the bubble
float lens = c * Lens * 0.10 * r * r * (Dir >= 0.0 ? 1.0 : -1.0);              // jelly lens: swallowed in / peeled out
off += -d * lens * (1.0 + 0.3 * sin(r * 25.0 - T * 8.0));
off += float2(-da.y, da.x) / float2(asp, 1.0) * (0.05 * a * Warp * r * r * sin(T * 0.23));   // slow edge swirl
float2 u2 = uv + off;
float2 ch = d * (0.002 * a + 0.012 * c) * Chroma;
float3 col = float3(SceneTextureLookup(u2 + ch, 14, true).r, SceneTextureLookup(u2, 14, true).g, SceneTextureLookup(u2 - ch, 14, true).b);
float3 gh = SceneTextureLookup(u2 + float2(sin(T * 0.37), cos(T * 0.29)) * 0.014 * Ghost, 14, true).rgb;   // drifting double image
col = lerp(col, max(col, gh), 0.35 * a * Ghost);
float rad = 0.006 * a * Glow + 0.02 * c;                                         // soft dream glow, wet blur at the crossing
float3 bl = 0;
for (int i = 0; i < 12; i++)
{
    float an = i * 2.39996323, k = (i + 0.5) / 12.0;
    bl += SceneTextureLookup(u2 + float2(cos(an) / asp, sin(an)) * sqrt(k) * rad, 14, true).rgb;
}
bl /= 12.0;
col = lerp(col, bl, saturate(0.25 * a * Haze + 0.7 * c));
col += max(bl - 0.55, 0.0) * float3(1.0, 0.62, 0.48) * 1.0 * Glow * a;          // pink-orange halation
float lum = dot(col, float3(0.2126, 0.7152, 0.0722));
float3 g = col * float3(1.07, 0.94, 0.90) + float3(0.05, 0.022, 0.03) * Lift * (1.0 - lum);   // warm, lifted shadows (not dark)
g = lerp(g, lum * float3(1.10, 0.86, 0.80), 0.08);
float vig = smoothstep(0.35, 0.95, r);
g = lerp(g, g * float3(1.0, 0.72, 0.64) + float3(0.04, 0.008, 0.015), vig * 0.45);  // rose-orange edges
float hb = pow(saturate(sin(T * 6.2831853 * HeartHz)), 12.0) * Heart;           // a slow heartbeat at the edges (unsettling)
g *= 1.0 - vig * hb * 0.18;
float close = c * smoothstep(0.75 - 0.5 * c, 1.05, r);                           // the membrane closes in, then opens
g = lerp(g, float3(0.34, 0.09, 0.11), close * 0.8);
return lerp(base, g, saturate(max(a, c)));
'''

JELLY_HLSL = r'''
float br = sin(T * 6.2831853 * Hz);
float3 wpo = Rel * JellyBreath * br;                                             // breathing, about the bubble's own centre
float ph = dot(Rel, float3(0.60, 0.50, 0.62)) / JellyRippleLen;
float rip = sin((ph - T * JellyRippleSpeed / JellyRippleLen) * 6.2831853)
          + 0.5 * sin(dot(Rel, float3(-0.40, 0.80, 0.30)) / (JellyRippleLen * 0.6) * 6.2831853 + T * 0.9);
wpo += N * rip * JellyRipple;                                                    // ripples travel over the surface
float rr = max(R, 1.0);
wpo += float3(sin(Rel.z / rr * 3.0 + T * 1.1), cos(Rel.z / rr * 2.3 + T * 0.8), 0.0) * JellyWobble * rr;   // soft sway, stays in place
return wpo;
'''


def enum(cls, *names):
    for n in names:
        if hasattr(cls, n): return getattr(cls, n)
    raise RuntimeError('%s has none of %s' % (cls.__name__, names))


def custom(m, code, inputs, otype, x, y, desc):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property('code', code); e.set_editor_property('output_type', otype); e.set_editor_property('description', desc)
    ins = []
    for n in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
    e.set_editor_property('inputs', ins); return e


def scalar(m, name, v, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', v); return e


def mpc_param(m, mpc, name, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, x, y)
    e.set_editor_property('collection', mpc); e.set_editor_property('parameter_name', name); return e


def root_of(mat):
    while isinstance(mat, unreal.MaterialInstance) and mat.get_editor_property('parent'): mat = mat.get_editor_property('parent')
    return mat


def bubble_comp():
    a = [x for x in EAS.get_all_level_actors() if x.get_actor_label() == BUBBLE_LABEL]
    cs = list(a[0].get_components_by_class(unreal.StaticMeshComponent)) if a else []
    if not cs: log.append('NO %s with a static mesh in the open level' % BUBBLE_LABEL)
    return (a[0], cs[0]) if cs else (None, None)


def realm_ppvs():
    out = []
    for a in EAS.get_all_level_actors():
        if not isinstance(a, unreal.PostProcessVolume): continue
        lab, tags = a.get_actor_label(), [str(t) for t in a.tags]
        if 'realm' in lab.lower() or 'RealmPPV' in tags or 'laptop2_realm' in tags: out.append(a)
    return out


def ppv_line(a):
    s = a.get_editor_property('settings')
    f = lambda k: s.get_editor_property(k) if s.get_editor_property('override_' + k) else '-'
    return '%s: unbound %s, priority %s, weight %s, exposure bias %s, gain %s, saturation %s, vignette %s, tint %s, blendables %d' % (
        a.get_actor_label(), a.get_editor_property('unbound'), a.get_editor_property('priority'), a.get_editor_property('blend_weight'),
        f('auto_exposure_bias'), f('color_gain'), f('color_saturation'), f('vignette_intensity'), f('scene_color_tint'),
        len(s.get_editor_property('weighted_blendables').get_editor_property('array')))


def load_backup(): return json.load(open(BACKUP)) if os.path.exists(BACKUP) else {}
def save_backup(b): json.dump(b, open(BACKUP, 'w'), indent=1)


def jelly_of(mat):
    """path of the jelly copy for this material (MI copy if the slot holds an MI, else the material copy)."""
    return mat.get_path_name().rsplit('.', 1)[0] + '_Jelly'


def build_jelly(mpc):
    a, c = bubble_comp()
    if not c: return
    cur = c.get_material(0)
    if cur is None: log.append('bubble slot 0 is empty'); return
    if cur.get_path_name().rsplit('.', 1)[0].endswith('_Jelly'):
        log.append('bubble already shows a jelly copy: %s (rebuilding from its parent chain)' % cur.get_name())
        bk = load_backup().get('bubble')
        if not bk: log.append('  no backup of the original; skip'); return
        cur = unreal.load_asset(bk['mat'])
    root = root_of(cur)
    rdst = jelly_of(root)
    log.append('jelly: %s -> %s' % (root.get_path_name(), rdst))
    if DRY: return
    if EAL.does_asset_exist(rdst): EAL.delete_asset(rdst)                 # our copy only, rebuilt from the live one
    m = EAL.duplicate_asset(root.get_path_name().rsplit('.', 1)[0], rdst)
    rel = MEL.create_material_expression(m, unreal.MaterialExpressionSubtract, -1600, 1400)
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1900, 1350), '', rel, 'A')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionObjectPositionWS, -1900, 1450), '', rel, 'B')
    cu = custom(m, JELLY_HLSL, ['Rel', 'N', 'R', 'T', 'Hz'] + [p for p, _ in JELLY_PARAMS], enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3'), -1200, 1400, 'Jelly381')
    MEL.connect_material_expressions(rel, '', cu, 'Rel')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -1900, 1550), '', cu, 'N')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionObjectRadius, -1900, 1650), '', cu, 'R')
    MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1900, 1750), '', cu, 'T')
    MEL.connect_material_expressions(mpc_param(m, mpc, 'BreathHz', -1900, 1850), '', cu, 'Hz')
    for i, (n, v) in enumerate(JELLY_PARAMS): MEL.connect_material_expressions(scalar(m, n, v, -1900, 1950 + 100 * i), '', cu, n)
    WPO = unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
    try: old = MEL.get_material_property_input_node(m, WPO)
    except Exception: old = None
    if old:                                                               # keep any WPO the bubble already had, add the jelly on top
        ad = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -800, 1400)
        MEL.connect_material_expressions(old, '', ad, 'A'); MEL.connect_material_expressions(cu, '', ad, 'B')
        MEL.connect_material_property(ad, '', WPO); log.append('  kept the existing WPO, jelly added on top')
    else:
        MEL.connect_material_property(cu, '', WPO)
    try: m.set_editor_property('max_world_position_offset_displacement', 800.0)
    except Exception as e: log.append('  (max WPO displacement not set: %s)' % e)
    MEL.recompile_material(m); EAL.save_asset(rdst)
    if isinstance(cur, unreal.MaterialInstanceConstant):
        idst = jelly_of(cur)
        if EAL.does_asset_exist(idst): EAL.delete_asset(idst)
        mi = EAL.duplicate_asset(cur.get_path_name().rsplit('.', 1)[0], idst)    # keeps every value the owner tuned on the MI
        MEL.set_material_instance_parent(mi, m); EAL.save_asset(idst)
        log.append('  instance copy %s (parent %s)' % (idst, rdst.split('/')[-1]))


def setup():
    mpc = unreal.load_asset(MPC) if EAL.does_asset_exist(MPC) else None
    log.append(('reuse ' if mpc else 'create ') + MPC)
    if not DRY:
        if not mpc: mpc = AT.create_asset('MPC_RealmDream', DEST, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
        have = [str(p.get_editor_property('parameter_name')) for p in mpc.get_editor_property('scalar_parameters')]
        ps = list(mpc.get_editor_property('scalar_parameters'))
        for n, v in (('Amount', 0.0), ('Cross', 0.0), ('CrossDir', 1.0), ('BreathHz', 0.2)):
            if n in have: continue
            p = unreal.CollectionScalarParameter(); p.set_editor_property('parameter_name', n); p.set_editor_property('default_value', v); ps.append(p)
        mpc.set_editor_property('scalar_parameters', ps); EAL.save_asset(MPC)
    # ---- M_RealmDream (post process, after tonemapping) + MI_RealmDream
    path = DEST + '/M_RealmDream'
    log.append(('rebuild ' if EAL.does_asset_exist(path) else 'create ') + path + ' + MI_RealmDream')
    if not DRY:
        m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset('M_RealmDream', DEST, unreal.Material, unreal.MaterialFactoryNew())
        MEL.delete_all_material_expressions(m)
        m.set_editor_property('material_domain', enum(unreal.MaterialDomain, 'MD_POST_PROCESS'))
        m.set_editor_property('blendable_location', enum(unreal.BlendableLocation, 'BL_AFTER_TONEMAPPING', 'BL_SCENE_COLOR_AFTER_TONEMAPPING'))
        stx = MEL.create_material_expression(m, unreal.MaterialExpressionSceneTexture, -900, -200)
        stx.set_editor_property('scene_texture_id', enum(unreal.SceneTextureId, 'PPI_POST_PROCESS_INPUT0'))
        ins = ['Dummy', 'Inv', 'T', 'Amt', 'Cross', 'Dir', 'Hz'] + [p for p, _ in DREAM_PARAMS]
        cu = custom(m, DREAM_HLSL, ins, enum(unreal.CustomMaterialOutputType, 'CMOT_FLOAT3'), -300, 0, 'RealmDream381')
        MEL.connect_material_expressions(stx, 'Color', cu, 'Dummy'); MEL.connect_material_expressions(stx, 'InvSize', cu, 'Inv')
        MEL.connect_material_expressions(MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, -50), '', cu, 'T')
        for i, (k, n) in enumerate((('Amt', 'Amount'), ('Cross', 'Cross'), ('Dir', 'CrossDir'), ('Hz', 'BreathHz'))):
            MEL.connect_material_expressions(mpc_param(m, mpc, n, -900, 50 + 100 * i), '', cu, k)
        for i, (n, v) in enumerate(DREAM_PARAMS): MEL.connect_material_expressions(scalar(m, n, v, -900, 500 + 100 * i), '', cu, n)
        MEL.connect_material_property(cu, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.recompile_material(m); EAL.save_asset(path)
        mip = DEST + '/MI_RealmDream'
        mi = unreal.load_asset(mip) if EAL.does_asset_exist(mip) else AT.create_asset('MI_RealmDream', DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', m); EAL.save_asset(mip)
    mi = unreal.load_asset(DEST + '/MI_RealmDream') if EAL.does_asset_exist(DEST + '/MI_RealmDream') else None
    # ---- the look on BP_RealmVision's Vision + the placed Realm_Vision
    def apply_look(pp, where):
        s = pp.get_editor_property('settings')
        for k, v in LOOK:
            try: s.set_editor_property('override_' + k, True); s.set_editor_property(k, v)
            except Exception as e: log.append('  (%s skipped: %s)' % (k, e))
        wb = s.get_editor_property('weighted_blendables'); arr_ = [x for x in wb.get_editor_property('array') if x.get_editor_property('object') != mi]
        if mi:
            w = unreal.WeightedBlendable(); w.set_editor_property('weight', 1.0); w.set_editor_property('object', mi); arr_.append(w)
        wb.set_editor_property('array', arr_); s.set_editor_property('weighted_blendables', wb)
        pp.set_editor_property('settings', s); log.append('  look + MI_RealmDream on %s' % where)
    if not EAL.does_asset_exist(BP): log.append('BP_RealmVision missing (#379 not pasted?)')
    elif not DRY:
        bp = unreal.load_asset(BP)
        hs = sds.k2_gather_subobject_data_for_blueprint(bp)
        for h in hs:
            o = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
            if isinstance(o, unreal.PostProcessComponent): apply_look(o, 'BP_RealmVision.' + o.get_name())
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_asset(BP)
        for a in EAS.get_all_level_actors():
            if a.get_actor_label() == VISION_LABEL:
                for c in a.get_components_by_class(unreal.PostProcessComponent): apply_look(c, VISION_LABEL)
    build_jelly(mpc)
    if not DRY: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log.append('Next: 8 BPVar lines (VARIABLES_v2_BPVar.txt), replace the EventGraph with BP_RealmVision_v2_graph.txt, Compile, Save.')


if MODE == '--check':
    for a in realm_ppvs(): log.append('PPV ' + ppv_line(a))
    if not realm_ppvs(): log.append('no realm post-process volume besides Realm_Vision')
    a, c = bubble_comp()
    if c:
        m = c.get_material(0)
        log.append('bubble material 0: %s (root %s)' % (m.get_path_name() if m else None, root_of(m).get_path_name() if m else None))
    for v in [x for x in EAS.get_all_level_actors() if x.get_actor_label() == VISION_LABEL]:
        for p in v.get_components_by_class(unreal.PostProcessComponent):
            s = p.get_editor_property('settings')
            log.append('Realm_Vision %s: exposure bias %s, gain %s' % (p.get_name(), s.get_editor_property('auto_exposure_bias'), s.get_editor_property('color_gain')))

elif MODE in ('--swap-bubble', '--revert-bubble'):
    a, c = bubble_comp()
    bk = load_backup()
    if c and MODE == '--swap-bubble':
        cur = c.get_material(0)
        new = jelly_of(cur)
        if cur.get_path_name().rsplit('.', 1)[0].endswith('_Jelly'): log.append('already the jelly copy')
        elif not EAL.does_asset_exist(new): log.append('%s missing: run the setup first' % new)
        else:
            log.append('bubble slot 0: %s -> %s' % (cur.get_name(), new.split('/')[-1]))
            if not DRY:
                bk['bubble'] = {'actor': a.get_path_name(), 'mat': cur.get_path_name()}; save_backup(bk)
                c.set_material(0, unreal.load_asset(new)); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    elif c:
        if 'bubble' not in bk: log.append('nothing to revert')
        else:
            log.append('bubble slot 0 back to %s' % bk['bubble']['mat'])
            if not DRY:
                c.set_material(0, unreal.load_asset(bk['bubble']['mat'])); bk.pop('bubble'); save_backup(bk)
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

elif MODE in ('--mute-old-ppv', '--unmute-old-ppv'):
    bk = load_backup(); old = bk.get('ppv', {})
    for a in realm_ppvs():
        k = a.get_path_name()
        if MODE == '--mute-old-ppv':
            log.append('mute %s (weight %s -> 0)' % (a.get_actor_label(), a.get_editor_property('blend_weight')))
            if not DRY: old.setdefault(k, a.get_editor_property('blend_weight')); a.set_editor_property('blend_weight', 0.0)
        elif k in old:
            log.append('unmute %s (weight -> %s)' % (a.get_actor_label(), old[k]))
            if not DRY: a.set_editor_property('blend_weight', old.pop(k))
    if not DRY:
        bk['ppv'] = old; save_backup(bk); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

else:
    setup()

out = '\n'.join(log)
open(os.path.join(HERE, 'realmvision381_%s.txt' % MODE.strip('-')), 'w').write(out)
unreal.log(out); print(out)

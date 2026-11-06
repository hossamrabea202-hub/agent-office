# #546 Chained zombie in the back room (adjustedfilm, 2026-11-06). Editor idle, not in Play, main level open. No paste. New assets only: no live asset is edited.
#   py chained_zombie_ue.py --dry-run     finds the wall and the floor by trace, checks every source asset, lists what it would build; changes nothing
#   py chained_zombie_ue.py               imports, builds materials + BP_ChainedZombie, places one actor. Then save the level
#   py chained_zombie_ue.py --revert      removes the placed actor (the assets stay). Then save the level
# Lab / test options: --root /Game/X (build there instead), --no-place, --at x,y,z,yaw (place there without traces)
import math, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('CH_ARGS', '').split()
DRY, REV, NOPLACE = '--dry-run' in A, '--revert' in A, '--no-place' in A
R_ = '/Game/CastleDefender/Characters/Enemies/Zombie'
D_ = A[A.index('--root') + 1] if '--root' in A else R_ + '/Chained546'
AT_ARG = [float(x) for x in A[A.index('--at') + 1].split(',')] if '--at' in A else None
LABEL = 'ChainedZombie_BackRoom'; BPP = D_ + '/BP_ChainedZombie'
# the room (castle_scan 11-03): inside x 3692-4108, y 1492-2008; door on the west side; he hangs on the middle of the east wall, facing the door
ROOM_PROBE = (3900.0, 1750.0, 110.0); WALL_X, WALL_TOL = 4108.0, 35.0; WALL_GAP = 50.0
EAL, AT, MEL, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools(), unreal.MaterialEditingLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
ES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
def say(*a): print('CHAIN546', ' '.join(str(x) for x in a))
if UES.get_game_world(): raise SystemExit('CHAIN546 stop Play first')
world = UES.get_editor_world()

placed = [a for a in ES.get_all_level_actors() if a.get_actor_label() == LABEL]
if REV:
    for a in placed:
        if not DRY: ES.destroy_actor(a)
    say('removed' if not DRY else 'would remove', len(placed), 'actor; save the level. Assets stay in', D_); raise SystemExit(0)

CLIPS = [('CH_Thrash', 10.0)] + [('CH_%s_%s' % (n, s), l) for n, l in (('Slice', 1.8), ('Free', 6.0), ('Claw', 1.3), ('Death', 7.0)) for s in 'LR']
STATICS = ['SM_ChainLink', 'SM_ChainCuff', 'SM_ChainAnchor', 'SM_MeltPool']
SND = {'metal1': '/Game/Audio/Kenney/SFX_impactMetal_heavy_001', 'metal2': '/Game/Audio/Kenney/SFX_impactMetal_heavy_003', 'plate': '/Game/Audio/Kenney/SFX_impactPlate_heavy_002', 'flesh': '/Game/Audio/SFX_FleshHit',
       'growl1': '/Game/MonsterRoarsAndGrowls/cues/16_Feral_Growl_Cue', 'growl2': '/Game/MonsterRoarsAndGrowls/cues/17_Bloodthirsty_Growl_Cue', 'growl3': '/Game/MonsterRoarsAndGrowls/cues/12_Ambush_Growl_Cue',
       'sizzle': '/Game/Free_Sounds_Pack/cue/Fire_Burning_Loop_2_Cue', 'att': '/Game/CastleDefender/Audio/ATT_FireLoop'}
FXP = {'sparks': '/Game/Particles/P_Sparks', 'smoke': '/Game/Particles/P_Smoke'}
def opt(p):
    if EAL.does_asset_exist(p):
        o = unreal.load_asset(p); return o.get_path_name() if o else ''
    say('note: optional asset missing, plays nothing:', p); return ''
SOUNDS = {k: opt(v) for k, v in SND.items()}; FX = {k: opt(v) for k, v in FXP.items()}
BLOOD_BP = '/Game/CastleDefender/VFX/BP_BloodBurst'
BLOOD_CLS = (unreal.load_asset(BLOOD_BP).generated_class().get_path_name() if EAL.does_asset_exist(BLOOD_BP) else '')
if '--stub-fx' in A:      # lab only: the lab has none of the game's sounds or particles, so stand-ins make every sound and FX node exist and compile
    def stub(nm, cls, fac):
        p = D_ + '/Stub/' + nm; return (unreal.load_asset(p) if EAL.does_asset_exist(p) else AT.create_asset(nm, D_ + '/Stub', cls, fac)).get_path_name()
    for k in SOUNDS:
        if k != 'att': SOUNDS[k] = stub('SC_' + k, unreal.SoundCue, unreal.SoundCueFactoryNew())
    for k in FX: FX[k] = stub('PS_' + k, unreal.ParticleSystem, unreal.ParticleSystemFactoryNew())
    _f = unreal.BlueprintFactory(); _f.set_editor_property('parent_class', unreal.Actor); _sp = D_ + '/Stub/BP_StubBlood'; _bb = unreal.load_asset(_sp) if EAL.does_asset_exist(_sp) else AT.create_asset('BP_StubBlood', D_ + '/Stub', unreal.Blueprint, _f); BEL.compile_blueprint(_bb); BLOOD_CLS = _bb.generated_class().get_path_name()
SK = R_ + '/SK_Zombie'; ABP = R_ + '/Anim/ABP_Zombie'; SKIN = R_ + '/AAA/M_Zombie_Skin_AAA'; MI_A, MI_B = R_ + '/AAA/MI_Zombie_AAA_A', R_ + '/AAA/MI_Zombie_AAA_B'
SLATE_D, SLATE_N = '/Game/CastleDefender/AssetPacks/StarterContent/Textures/T_Rock_Slate_D', '/Game/CastleDefender/AssetPacks/StarterContent/Textures/T_Rock_Slate_N'
for p in (SK, ABP, SKIN, MI_A, MI_B, SLATE_D, SLATE_N):
    if not EAL.does_asset_exist(p): raise SystemExit('CHAIN546 missing source asset ' + p)
for f in [c + '.fbx' for c, _ in CLIPS] + [s + '.fbx' for s in STATICS]:
    if not os.path.exists(os.path.join(HERE, 'fbx', f)): raise SystemExit('CHAIN546 missing FBX (git pull?): ' + f)
sk_ = unreal.load_asset(SK)
say('SK_Zombie slots', [str(m.material_interface.get_name()) for m in sk_.materials])
skin = unreal.load_asset(SKIN)
say('skin wiring on this machine: WPO <-', MEL.get_material_property_input_node(skin, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET), '| expressions', MEL.get_num_material_expressions(skin))

# ------------------------------------------------- find the wall ----------------------------------------------------
def trace(a, b):
    hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(*a), unreal.Vector(*b), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    r = []
    for h in (hits or []):   # Master: line_trace_multi returns None when nothing is hit
        t = h.to_tuple(); ac = next((v for v in t if isinstance(v, unreal.Actor)), None); vs = [v for v in t if isinstance(v, unreal.Vector)]
        if ac is not None and vs: r.append((vs[0], ac))
    return r
LOC = None
if AT_ARG: LOC = AT_ARG
elif not NOPLACE:
    wall = trace(ROOM_PROBE, (ROOM_PROBE[0] + 400, ROOM_PROBE[1], ROOM_PROBE[2]))
    wall = [w for w in wall if not w[1].get_actor_label().startswith(LABEL)]
    if not wall: raise SystemExit('CHAIN546 no wall found east of the room probe: the room changed. Nothing done; tell i5')
    wx = wall[0][0].x; say('wall hit x', round(wx, 1), 'on', wall[0][1].get_actor_label())
    if abs(wx - WALL_X) > WALL_TOL: raise SystemExit('CHAIN546 wall at x %.0f, expected %.0f: the room changed. Nothing done; tell i5' % (wx, WALL_X))
    px = wx - WALL_GAP
    floor = trace((px, ROOM_PROBE[1], 200.0), (px, ROOM_PROBE[1], -200.0))
    if not floor: raise SystemExit('CHAIN546 no floor under the spot. Nothing done; tell i5')
    fz = floor[0][0].z; say('floor z', round(fz, 1), 'on', floor[0][1].get_actor_label())
    for side in (-1, 1):                                              # arms + chains need the wall clear either side: an opening here would float an anchor
        y = ROOM_PROBE[1] + side * 110.0
        for z in (fz + 30.0, fz + 180.0):
            h = trace((ROOM_PROBE[0], y, z), (ROOM_PROBE[0] + 400, y, z))
            if not h or abs(h[0][0].x - wx) > 8.0: raise SystemExit('CHAIN546 the wall is not flat at the anchors (y %.0f z %.0f): nothing done; tell i5' % (y, z))
    head = trace((px, ROOM_PROBE[1], fz + 10.0), (px, ROOM_PROBE[1], fz + 240.0))
    if head: say('note: something above the floor at the spot:', head[0][1].get_actor_label(), 'z', round(head[0][0].z))
    LOC = [px, ROOM_PROBE[1], fz, 180.0]
say('spot', LOC)
if DRY:
    say('WOULD import', len(CLIPS), 'clips and', len(STATICS), 'meshes into', D_, ', build 4 materials + 2 skin instances, BP_ChainedZombie, place', LABEL); say('have assets already:', EAL.does_directory_exist(D_)); say('DONE dry-run, nothing changed'); raise SystemExit(0)

# ------------------------------------------------- imports -----------------------------------------------------------
skel = unreal.load_asset(R_ + '/SK_Zombie_Skeleton')
def imp_clip(name):
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False)
    ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in [('use_default_sample_rate', False), ('custom_sample_rate', 30)]:
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', name + '.fbx'); t.destination_path = D_ + '/Anims'; t.destination_name = name; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui
    return t
need = [c for c, _ in CLIPS if not EAL.does_asset_exist(D_ + '/Anims/' + c)]
if need: AT.import_asset_tasks([imp_clip(c) for c in need])
bad = [c for c, _ in CLIPS if not EAL.does_asset_exist(D_ + '/Anims/' + c)]
if bad: raise SystemExit('CHAIN546 clip import failed: %s' % bad)
for c, l in CLIPS:
    p = D_ + '/Anims/AM_' + c
    if EAL.does_asset_exist(p): continue
    s = unreal.load_asset(D_ + '/Anims/' + c); f = unreal.AnimMontageFactory(); f.set_editor_property('target_skeleton', s.get_editor_property('skeleton')); f.set_editor_property('source_animation', s)
    m = AT.create_asset('AM_' + c, D_ + '/Anims', unreal.AnimMontage, f)
    for prop, tm in (('blend_in', 0.14), ('blend_out', 0.2)):
        try: b = m.get_editor_property(prop); b.set_editor_property('blend_time', tm); m.set_editor_property(prop, b)
        except Exception as e: say('note: montage', prop, e)
    if 'Death' in c: m.set_editor_property('enable_auto_blend_out', False)     # holds his last frame under the melt
    EAL.save_loaded_asset(m); say('montage', c, round(m.get_play_length(), 2))

for nm in STATICS:
    SM = D_ + '/' + nm
    if EAL.does_asset_exist(SM): continue
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property('static_mesh_import_data'); d.set_editor_property('import_uniform_scale', 0.01); d.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE); d.set_editor_property('auto_generate_collision', False); d.set_editor_property('generate_lightmap_u_vs', False); d.set_editor_property('combine_meshes', True); d.set_editor_property('normal_import_method', unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', nm + '.fbx'); t.destination_path = D_; t.destination_name = nm; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t])
    if not EAL.does_asset_exist(SM): raise SystemExit('CHAIN546 mesh import failed: ' + nm)
    mesh = unreal.load_asset(SM); b = mesh.get_bounds(); say(nm, 'extent cm', round(b.box_extent.x, 1), round(b.box_extent.y, 1), round(b.box_extent.z, 1))

# ------------------------------------------------- materials ----------------------------------------------------------
E = MEL.create_material_expression; C = MEL.connect_material_expressions; PROP = MEL.connect_material_property; MP = unreal.MaterialProperty
def custom(m, code, inputs, otype=unreal.CustomMaterialOutputType.CMOT_FLOAT3, x=-500, y=0, desc='x'):
    n = E(m, unreal.MaterialExpressionCustom, x, y); n.set_editor_property('code', code); n.set_editor_property('output_type', otype); n.set_editor_property('description', desc)
    ins = []
    for i in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', i); ins.append(ci)
    n.set_editor_property('inputs', ins); return n
def scalar(m, name, v, x, y):
    n = E(m, unreal.MaterialExpressionScalarParameter, x, y); n.set_editor_property('parameter_name', name); n.set_editor_property('default_value', v); return n
def tcmul(m, tile, x, y):
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, x, y); tc.set_editor_property('u_tiling', tile); tc.set_editor_property('v_tiling', tile); return tc
def texs(m, path, tc, x, y, normal=False):
    n = E(m, unreal.MaterialExpressionTextureSample, x, y); n.set_editor_property('texture', unreal.load_asset(path))
    if normal: n.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    C(tc, '', n, 'UVs'); return n

# Forged iron. Three real surfaces, chosen by the vertex masks: mill scale (dark oxide, non-metal), rust (metallic 0, roughness ~1), and metal rubbed bright (metallic 1, >= 195 sRGB). No lighting in the colours.
IRON = D_ + '/M_CD_ForgedIron'
if not EAL.does_asset_exist(IRON):
    m = AT.create_asset('M_CD_ForgedIron', D_, unreal.Material, unreal.MaterialFactoryNew())
    vc = E(m, unreal.MaterialExpressionVertexColor, -1200, 0); uv = tcmul(m, 1.0, -1200, 200); d = texs(m, SLATE_D, uv, -1000, 200); n_ = texs(m, SLATE_N, uv, -1000, 420, True)
    base = custom(m, '''float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; float rust = smoothstep(0.42, 0.72, V.r + (det - 1.0) * 0.28); float bright = smoothstep(0.25, 0.7, V.g);
float3 scale_ = float3(0.046, 0.041, 0.038) * lerp(0.8, 1.25, saturate(det * 0.5));
float3 rustc = lerp(float3(0.085, 0.036, 0.018), float3(0.18, 0.057, 0.017), saturate(det - 0.6));
float3 c = lerp(scale_, rustc, rust); c = lerp(c, float3(0.56, 0.55, 0.53), bright); c *= lerp(1.0, 0.72, V.b * (1.0 - bright)); return c;''', ['V', 'D'], x=-600, y=-100, desc='iron_base')
    rough = custom(m, '''float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; float rust = smoothstep(0.42, 0.72, V.r + (det - 1.0) * 0.28); float bright = smoothstep(0.25, 0.7, V.g);
float r = lerp(0.56 + (det - 1.0) * 0.14, 0.97, rust); r = lerp(r, 0.30 + (det - 1.0) * 0.08, bright); return saturate(r + V.b * 0.08 * (1.0 - bright));''', ['V', 'D'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -600, 100, 'iron_rough')
    metal = custom(m, 'return smoothstep(0.25, 0.7, V.g);', ['V'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -600, 250, 'iron_metal')
    for nd in (base, rough): C(vc, '', nd, 'V'); C(d, 'RGB', nd, 'D')
    C(vc, '', metal, 'V'); PROP(base, '', MP.MP_BASE_COLOR); PROP(rough, '', MP.MP_ROUGHNESS); PROP(metal, '', MP.MP_METALLIC); PROP(n_, 'RGB', MP.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); say('built M_CD_ForgedIron')

# The pool: hot and wet at first (crust glowing at the rim), cools to the marbled tallow of a burnt-out candle.
POOL = D_ + '/M_CD_MeltPool546'
if not EAL.does_asset_exist(POOL):
    m = AT.create_asset('M_CD_MeltPool546', D_, unreal.Material, unreal.MaterialFactoryNew())
    vc = E(m, unreal.MaterialExpressionVertexColor, -1200, 0); uv = tcmul(m, 2.0, -1200, 200); d = texs(m, SLATE_D, uv, -1000, 200); n_ = texs(m, SLATE_N, uv, -1000, 420, True); h = scalar(m, 'PoolHeat', 1.0, -1000, -200)
    base = custom(m, '''float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; float marble = smoothstep(0.35, 0.8, V.b + (det - 1.0) * 0.5);
float3 wax = lerp(float3(0.30, 0.215, 0.115), float3(0.075, 0.030, 0.020), marble); float3 hot = float3(0.035, 0.018, 0.014); return lerp(wax, hot, saturate(H * 1.4));''', ['V', 'D', 'H'], x=-600, y=-100, desc='pool_base')
    rough = custom(m, 'float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; return saturate(lerp(0.42 + (det - 1.0) * 0.1, 0.12, saturate(H * 2.0)));', ['D', 'H'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -600, 100, 'pool_rough')
    emis = custom(m, '''float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; float crack = pow(saturate(1.0 - abs(det - 1.0) * 3.0), 3.0);
float g = (V.g * 1.1 + crack * 0.55 + (1.0 - V.r) * 0.5) * H * H; float3 c = lerp(float3(1.0, 0.13, 0.015), float3(1.0, 0.42, 0.09), saturate(H * g)); return c * g * 7.0;''', ['V', 'D', 'H'], x=-600, y=250, desc='pool_glow')
    for nd in (base, emis): C(vc, '', nd, 'V')
    for nd in (base, rough, emis): C(d, 'RGB', nd, 'D'); C(h, '', nd, 'H')
    PROP(base, '', MP.MP_BASE_COLOR); PROP(rough, '', MP.MP_ROUGHNESS); PROP(emis, '', MP.MP_EMISSIVE_COLOR); PROP(n_, 'RGB', MP.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); say('built M_CD_MeltPool546')

# Rust run down the wall under each anchor (gravity + water). A lit translucent card, no decal.
STREAK = D_ + '/M_CD_RustStreak546'
if not EAL.does_asset_exist(STREAK):
    m = AT.create_asset('M_CD_RustStreak546', D_, unreal.Material, unreal.MaterialFactoryNew()); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    try: m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    except Exception as e: say('note:', e)
    uv = E(m, unreal.MaterialExpressionTextureCoordinate, -1200, 0); uv2 = tcmul(m, 3.0, -1200, 200); d = texs(m, SLATE_D, uv2, -1000, 200)
    op = custom(m, '''float det = dot(D.rgb, float3(0.3, 0.59, 0.11)) / 0.3; float across = 1.0 - abs(UV.y - 0.5) * 2.0; float runs = 0.55 + 0.45 * sin(UV.y * 31.0 + sin(UV.y * 9.0) * 2.0);
float down = pow(1.0 - UV.x, 1.6); return saturate(pow(across, 0.8) * runs * down * (0.45 + det * 0.3)) * 0.72;''', ['UV', 'D'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -600, 100, 'streak_op')
    C(uv, '', op, 'UV'); C(d, 'RGB', op, 'D')
    c3 = E(m, unreal.MaterialExpressionConstant3Vector, -600, -100); c3.set_editor_property('constant', unreal.LinearColor(0.12, 0.045, 0.020, 1)); r1 = E(m, unreal.MaterialExpressionConstant, -600, 300); r1.set_editor_property('r', 0.92)
    PROP(c3, '', MP.MP_BASE_COLOR); PROP(r1, '', MP.MP_ROUGHNESS); PROP(op, '', MP.MP_OPACITY)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); say('built M_CD_RustStreak546')

# The zombie's own skin, duplicated, with the candle added. The live M_Zombie_Skin_AAA is not touched.
COMMON = '''float tt = saturate(T); float2 d0 = P.xy - C.xy; float r = length(d0) + 0.001; float wr = saturate((r - 34.0) / 60.0); float wilt = smoothstep(0.02, 0.42, tt);
float H = max(max(P.z - G, 0.0) - wr * wr * wilt * 95.0, 0.0);
float n1 = sin(P.x * 0.031 + P.y * 0.027) + 0.5 * sin(P.x * 0.067 - P.y * 0.053 + 1.7);
float ee = tt * tt * (2.1 - 1.1 * tt); float F = 228.0 * (1.0 - ee) + 9.0 * n1 * saturate(tt * 6.0) * saturate((1.0 - tt) * 6.0);
'''
# Wax, not spikes: the arms wilt and draw back into the trunk first, the top rounds over (a smooth minimum, not a cut), a thick collar rides just under the front, smooth sheets run down, the foot spreads into the pool.
WPO_CODE = COMMON + '''float k = 16.0; float sm = -k * log(exp(-H / k) + exp(-F / k)); float exc = max(H - F, 0.0); float comp = lerp(0.07, 0.01, tt); float newH = sm + exc * comp + k * 0.693 * saturate(1.0 - F / 40.0) * 0.0;
float band = (H < F) ? saturate((H - (F - 70.0)) / 70.0) : 1.0; float soft = saturate(tt * 9.0);
float lob = 0.5 + 0.5 * sin(atan2(d0.y, d0.x) * 5.0 + n1 * 1.5); newH -= lob * lob * band * band * 16.0 * soft;
newH = max(newH, 0.6 + 2.0 * (1.0 - tt));
float ff = (r > 34.0) ? (34.0 + (r - 34.0) * (1.0 - 0.8 * wilt)) / r : 1.0; float2 xy = d0 * ff;
xy *= lerp(1.0, 0.55, saturate(exc / 60.0)); float cdist = (H - F) / 22.0; xy *= 1.0 + 0.18 * exp(-cdist * cdist) * soft;
float sprd = saturate(1.0 - newH / 22.0) * smoothstep(0.55, 1.0, tt); xy *= 1.0 + 0.85 * sprd;
return (tt > 0.0005) ? float3(xy - d0, newH - max(P.z - G, 0.0)) : float3(0.0, 0.0, 0.0);'''
MASK_CODE = COMMON + 'return (tt > 0.0005) ? max(saturate((H - F + 24.0) / 32.0), wr * wilt) : 0.0;'
GLOW_CODE = COMMON + '''float d = H - F; float heat = exp(-(d * d) / (2.0 * 9.0 * 9.0)); float grain = 0.5 + 0.5 * sin(P.x * 0.35 + P.z * 0.27) * sin(P.y * 0.41 - P.z * 0.23);
float cap = (d > 0.0) ? 0.03 : 0.0; float below = (d < 0.0) ? exp(d / 30.0) * 0.06 * grain : 0.0; float arm = wr * wilt * (1.0 - wilt) * 0.45 * grain;
float kk = (heat * (0.6 + 0.4 * grain) + cap + below + arm) * saturate(tt * 14.0) * saturate((1.0 - tt) * 5.0);
float3 c = lerp(float3(1.0, 0.13, 0.015), float3(1.0, 0.50, 0.12), saturate(heat * heat)); return (tt > 0.0005) ? c * kk * Glow : float3(0.0, 0.0, 0.0);'''
WOUND_CODE = '''float3 a = float3(68.0, -11.5, 167.0); float3 pL = PS - a; float3 pR = PS - float3(-a.x, a.y, a.z);
float3 n = normalize(float3(0.55, 0.25, 0.8)); float3 nR = float3(-n.x, n.y, n.z);
float jag = 0.6 * sin(PS.x * 1.7) + 0.4 * sin(PS.y * 2.3 + PS.z * 1.1);
float wL = smoothstep(2.1 + jag, 0.6, abs(dot(pL, n))) * smoothstep(16.0, 11.0, length(pL)) * WL;
float wR = smoothstep(2.1 + jag, 0.6, abs(dot(pR, nR))) * smoothstep(16.0, 11.0, length(pR)) * WR; return saturate(wL + wR);'''
BASE_CODE = 'float t2 = saturate(N * 0.5 + 0.5); float3 wax = lerp(float3(0.16, 0.10, 0.055), float3(0.045, 0.019, 0.014), t2); return lerp(B, wax, M);'
SKINM = D_ + '/M_ChainedZombie_Melt'
if not EAL.does_asset_exist(SKINM):
    m = EAL.duplicate_asset(SKIN, SKINM)
    if not m: raise SystemExit('CHAIN546 could not duplicate the skin')
    old = {}
    for pr, key in ((MP.MP_BASE_COLOR, 'base'), (MP.MP_EMISSIVE_COLOR, 'emis'), (MP.MP_ROUGHNESS, 'rough')):
        old[key] = (MEL.get_material_property_input_node(m, pr), str(MEL.get_material_property_input_node_output_name(m, pr)))
    say('skin outputs', {k: (v[0].get_name() if v[0] else None, v[1]) for k, v in old.items()})
    def outn(s): return '' if s == 'None' else s
    x0 = -2400
    wp = E(m, unreal.MaterialExpressionWorldPosition, x0, 1200); wp.set_editor_property('world_position_shader_offset', unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    T = scalar(m, 'MeltT', 0.0, x0, 1350); G_ = scalar(m, 'MeltGround', 0.0, x0, 1450); Gl = scalar(m, 'MeltGlow', 3.2, x0, 1550)
    Cv = E(m, unreal.MaterialExpressionVectorParameter, x0, 1650); Cv.set_editor_property('parameter_name', 'MeltCore'); Cv.set_editor_property('default_value', unreal.LinearColor(0, 0, 0, 0))
    w_ = custom(m, WPO_CODE, ['P', 'T', 'G', 'C'], x=-1400, y=1200, desc='melt_wpo'); ms = custom(m, MASK_CODE, ['P', 'T', 'G', 'C'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -1400, 1450, 'melt_mask'); gw = custom(m, GLOW_CODE, ['P', 'T', 'G', 'C', 'Glow'], x=-1400, y=1650, desc='melt_glow')
    for nd in (w_, ms, gw): C(wp, '', nd, 'P'); C(T, '', nd, 'T'); C(G_, '', nd, 'G')
    C(Cv, '', w_, 'C'); C(Cv, '', ms, 'C'); C(Cv, '', gw, 'C'); C(Gl, '', gw, 'Glow')
    bc = custom(m, BASE_CODE, ['B', 'M', 'N'], x=-900, y=1450, desc='melt_base'); C(old['base'][0], outn(old['base'][1]), bc, 'B'); C(ms, '', bc, 'M')
    nz = custom(m, 'return sin(P.x * 0.21 + P.z * 0.13) * sin(P.y * 0.17 - P.z * 0.19);', ['P'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -1100, 1550, 'melt_noise'); C(wp, '', nz, 'P'); C(nz, '', bc, 'N')
    rg = E(m, unreal.MaterialExpressionLinearInterpolate, -900, 1650); C(old['rough'][0], outn(old['rough'][1]), rg, 'A'); k = E(m, unreal.MaterialExpressionConstant, -1100, 1700); k.set_editor_property('r', 0.16); C(k, '', rg, 'B'); C(ms, '', rg, 'Alpha')
    # the wound, on top of everything: dark wet flesh (deoxygenated blood 0.42, 0, 0 going black in the cut)
    pre = E(m, unreal.MaterialExpressionPreSkinnedPosition, x0, 2000); vi = E(m, unreal.MaterialExpressionVertexInterpolator, x0 + 300, 2000); C(pre, '', vi, '')
    wl = scalar(m, 'WoundL', 0.0, x0, 2150); wr_ = scalar(m, 'WoundR', 0.0, x0, 2250)
    wd = custom(m, WOUND_CODE, ['PS', 'WL', 'WR'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -1200, 2050, 'wound'); C(vi, '', wd, 'PS'); C(wl, '', wd, 'WL'); C(wr_, '', wd, 'WR')
    wc = E(m, unreal.MaterialExpressionConstant3Vector, -900, 2150); wc.set_editor_property('constant', unreal.LinearColor(0.20, 0.006, 0.006, 1)); bw = E(m, unreal.MaterialExpressionLinearInterpolate, -600, 1500); C(bc, '', bw, 'A'); C(wc, '', bw, 'B'); C(wd, '', bw, 'Alpha')
    kw = E(m, unreal.MaterialExpressionConstant, -900, 2300); kw.set_editor_property('r', 0.08); rw = E(m, unreal.MaterialExpressionLinearInterpolate, -600, 1700); C(rg, '', rw, 'A'); C(kw, '', rw, 'B'); C(wd, '', rw, 'Alpha')
    PROP(bw, '', MP.MP_BASE_COLOR); PROP(rw, '', MP.MP_ROUGHNESS); PROP(w_, '', MP.MP_WORLD_POSITION_OFFSET)
    if old['emis'][0]:
        ad = E(m, unreal.MaterialExpressionAdd, -900, 1850); C(old['emis'][0], outn(old['emis'][1]), ad, 'A'); C(gw, '', ad, 'B'); PROP(ad, '', MP.MP_EMISSIVE_COLOR)
    else: PROP(gw, '', MP.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m); say('built M_ChainedZombie_Melt, expressions', MEL.get_num_material_expressions(m))
MIS = []
for src, nm in ((MI_A, 'MI_ChainedZombie_A'), (MI_B, 'MI_ChainedZombie_B')):
    p = D_ + '/' + nm
    if not EAL.does_asset_exist(p):
        mi = EAL.duplicate_asset(src, p); MEL.set_material_instance_parent(mi, unreal.load_asset(SKINM)); MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
    MIS.append(unreal.load_asset(p))

# ------------------------------------------------- the Blueprint ------------------------------------------------------
# Blender (x, y, z) m -> actor (-100 y, -100 x, 100 z). Actor +X looks out of the wall into the room; the wall is at actor x = -WALL_GAP.
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def qinv(a): return (-a[0], -a[1], -a[2], a[3])
def qrot(q, v):
    r = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qinv(q)); return r[:3]
def from_xz(x, z):
    n = lambda v: (lambda l: tuple(c / l for c in v))(math.sqrt(sum(c * c for c in v)))
    cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    X = n(x); Y = n(cross(z, X)); Z = cross(X, Y); q = unreal.MathLibrary.make_rot_from_xz(unreal.Vector(*X), unreal.Vector(*Z)).quaternion(); return (q.x, q.y, q.z, q.w)
# bone frames in the mesh's bind pose (measured in the lab on SK_Zombie): quaternion, position, child position
BONE = {'LeftForeArm': ((0.7132502551615351, -0.7009094617081347, -1.0589305534510332e-8, -1.336239931822284e-7), (49.56, -11.63, 167.0), (81.24, -11.08, 167.0)),
        'RightForeArm': ((-0.7132493290981113, -0.7009104040753599, -6.042413496970176e-8, 7.884833208277993e-8), (-49.56, -11.63, 167.0), (-81.24, -11.08, 167.0)),
        'LeftLeg': ((6.128150904815912e-8, -0.7326550576478608, -0.6806001517065694, 3.087245842727256e-8), (12.3, 0.93, 64.29), (12.3, -2.76, 14.26)),
        'RightLeg': ((2.902186788088467e-7, -0.732655107113523, -0.6806000984527893, 0.0000025379835253258294), (-12.3, 0.93, 64.29), (-12.3, -2.76, 14.26))}
def cuff_rel(bone, along):
    q, p, c = BONE[bone]; d = tuple(c[i] - p[i] for i in range(3)); L = math.sqrt(sum(x * x for x in d)); world = tuple(p[i] + d[i] / L * along for i in range(3))
    rel_p = qrot(qinv(q), tuple(world[i] - p[i] for i in range(3)))
    want = from_xz(d, (0.0, 1.0, 0.0))                  # hasp and lug (-Z) on the wall side in the bind pose
    rel_q = qmul(qinv(q), want); r = unreal.Quat(*rel_q).rotator(); return unreal.Vector(*rel_p), r
CHAINS = [('LeftForeArm', 28.5, 1.0, 60.0, 7, (-50.0, -102.0, 183.8)), ('RightForeArm', 28.5, 1.0, 60.0, 7, (-50.0, 102.0, 183.8)), ('LeftLeg', 43.0, 0.72, 43.0, 5, (-50.0, -56.0, 31.8)), ('RightLeg', 43.0, 0.72, 43.0, 5, (-50.0, 56.0, 31.8))]
LUG = {1.0: 16.7, 0.72: 12.0}     # cuff centre to where the chain leaves, cm
if EAL.does_asset_exist(BPP):     # already built (a re-run or after --revert): only place it. Delete BP_ChainedZombie by hand to rebuild
    say('BP_ChainedZombie exists: not rebuilding, placing only')
    if not NOPLACE and LOC:
        for a_ in placed: ES.destroy_actor(a_)
        ac = ES.spawn_actor_from_class(unreal.load_asset(BPP).generated_class(), unreal.Vector(LOC[0], LOC[1], LOC[2]), unreal.Rotator(roll=0, pitch=0, yaw=LOC[3])); ac.set_actor_label(LABEL); ac.set_folder_path('CastleDefender/ChainedZombie'); say('placed at', LOC, '; save the level')
    say('DONE'); raise SystemExit(0)
f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Pawn)      # a pawn so ABP_Zombie's TryGetPawnOwner returns something; it never moves and nothing possesses it
bp = AT.create_asset('BP_ChainedZombie', D_, unreal.Blueprint, f)
hs = SDS.k2_gather_subobject_data_for_blueprint(bp); root_h = next(h for h in hs if str(SDL.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) == 'DefaultSceneRoot')
def comp(name, cls, parent=None):
    h, _ = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent or root_h, new_class=cls, blueprint_context=bp)); SDS.rename_subobject(h, unreal.Text(name)); return SDL.get_object(SDS.k2_find_subobject_data_from_handle(h))
IRONM = unreal.load_asset(IRON); LINK = unreal.load_asset(D_ + '/SM_ChainLink'); CUFF = unreal.load_asset(D_ + '/SM_ChainCuff'); ANC = unreal.load_asset(D_ + '/SM_ChainAnchor')
def sm(name, mesh, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), shadow=True):
    c = comp(name, unreal.StaticMeshComponent); c.set_editor_property('static_mesh', mesh); c.set_material(0, mat); c.set_collision_profile_name('NoCollision'); c.set_editor_property('generate_overlap_events', False); c.set_editor_property('can_ever_affect_navigation', False)
    c.set_editor_property('relative_location', unreal.Vector(*loc)); c.set_editor_property('relative_rotation', unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2])); c.set_editor_property('relative_scale3d', unreal.Vector(*scale)); c.set_editor_property('cast_shadow', shadow); return c
mc = comp('Mesh', unreal.SkeletalMeshComponent)
mc.set_editor_property('skeletal_mesh_asset', sk_); mc.set_editor_property('relative_rotation', unreal.Rotator(roll=0, pitch=0, yaw=-90)); mc.set_collision_profile_name('NoCollision'); mc.set_editor_property('can_ever_affect_navigation', False)
mc.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT); mc.set_editor_property('anim_class', unreal.load_asset(ABP).generated_class()); mc.set_editor_property('bounds_scale', 1.4)
mc.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ONLY_TICK_MONTAGES_WHEN_NOT_RENDERED)
for i, mi in enumerate(MIS): mc.set_material(i, mi)
hit = comp('Hit', unreal.CapsuleComponent); hit.set_editor_property('capsule_radius', 40.0); hit.set_editor_property('capsule_half_height', 100.0); hit.set_editor_property('relative_location', unreal.Vector(10.0, 0.0, 100.0)); hit.set_collision_profile_name('Pawn'); hit.set_editor_property('generate_overlap_events', True); hit.set_editor_property('can_ever_affect_navigation', False)
for i, (bn, along, sc, ln, cnt, a) in enumerate(CHAINS):
    sm('Anchor%d' % i, ANC, IRONM, a)
    rp, rr = cuff_rel(bn, along); c = sm('Cuff%d' % i, CUFF, IRONM, (rp.x, rp.y, rp.z), (rr.roll, rr.pitch, rr.yaw), (sc, sc, sc))
    pl = unreal.load_asset('/Engine/BasicShapes/Plane'); stk = unreal.load_asset(STREAK); ls = 0.72 if i < 2 else 0.30
    sm('Streak%d' % i, pl, stk, (a[0] + 0.5, a[1], a[2] - 4.0 - ls * 50.0), (0, -90, 0), (ls, 0.26, 1.0), False)
idx = 0
for i, (bn, along, sc, ln, cnt, a) in enumerate(CHAINS):
    for j in range(cnt): sm('L%02d' % idx, LINK, IRONM, a); idx += 1
NL = idx
fly = sm('FlyLink', LINK, IRONM, (0, 0, 200)); fly.set_editor_property('visible', False)
pool = sm('Pool', unreal.load_asset(D_ + '/SM_MeltPool'), unreal.load_asset(POOL), (18.0, 0.0, 0.0), (0, 0, 0), (0.02, 0.02, 0.02), False); pool.set_editor_property('visible', False)
lt = comp('HeatLight', unreal.PointLightComponent); lt.set_editor_property('relative_location', unreal.Vector(30.0, 0.0, 120.0)); lt.set_editor_property('intensity', 0.0); lt.set_editor_property('attenuation_radius', 520.0); lt.set_editor_property('light_color', unreal.Color(r=255, g=136, b=48, a=255)); lt.set_editor_property('use_temperature', False)
try: lt.set_editor_property('intensity_units', unreal.LightUnits.CANDELAS)
except Exception as e: say('note:', e)
BEL.compile_blueprint(bp)

# ---- graph helpers (same shape as wire_spit_ue.py). A value is (node, pin); plain Python numbers/strings become literals.
gr = BEL.find_event_graph(bp); ge = GE.get_graph_editor(gr)
V, D2, I_, B_ = BEL.get_struct_type(unreal.Vector.static_struct()), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('bool')
O_ = BEL.get_object_reference_type; ARR = BEL.get_array_type
VARS = [('State', I_), ('FreeSide', I_), ('Now', D2), ('Dt', D2), ('HeroDist', D2), ('LoopT', D2), ('HitLock', D2), ('MeltStart', D2), ('MeltDur', D2), ('NextGrowl', D2), ('NextClaw', D2), ('BlowT', D2), ('BlowDone', B_),
        ('Rel1', B_), ('Rel2', B_), ('StubOn', B_), ('TailP', V), ('MeltTv', D2), ('CoolT', D2), ('LoopRate', D2),
        ('LinksArr', ARR(O_(unreal.StaticMeshComponent))), ('CuffArr', ARR(O_(unreal.StaticMeshComponent))), ('Anch', ARR(V)), ('RelP', ARR(V)), ('RelT', ARR(D2)), ('ModeA', ARR(I_)), ('CLen', ARR(D2)), ('CFirst', ARR(I_)), ('CN', ARR(I_)), ('CLug', ARR(D2)),
        ('HeroP', V), ('LastLug', ARR(V)), ('NextRattle', D2), ('DropOn', B_), ('DropT', D2), ('DropP', V), ('FlyOn', B_), ('FlyT', D2), ('FlyP', V), ('FlyV', V), ('GroundZ', D2), ('Landed', B_), ('SegA', V), ('SegE', V), ('SegLen', D2), ('SegFirst', I_), ('SegN', I_), ('SegS', D2), ('Cur', I_), ('LugP', V), ('Sizzle', O_(unreal.AudioComponent)), ('SmokeC', O_(unreal.ParticleSystemComponent))]
for v, t in VARS: BEL.add_member_variable(bp, v, t)
BEL.compile_blueprint(bp); CLS = bp.generated_class().get_path_name()
ev_seg = ge.add_custom_event_node('SegRun'); ev_chain = ge.add_custom_event_node('ChainStep'); ev_loop = ge.add_custom_event_node('PlayLoop'); ev_release = ge.add_custom_event_node('ReleaseCur'); ev_slice = ge.add_custom_event_node('DoSlice'); ev_kill = ge.add_custom_event_node('DoKill'); ev_melt = ge.add_custom_event_node('MeltStep'); ev_growl = ge.add_custom_event_node('GrowlOnce'); ev_drop = ge.add_custom_event_node('DropStep')
BEL.compile_blueprint(bp)
pos = [0, 0]
def place(n):
    BEL.set_node_pos(n, unreal.IntPoint(pos[0], pos[1])); pos[0] += 320
    if pos[0] > 12000: pos[0] = 0; pos[1] += 320
    return n
for e_ in (ev_seg, ev_chain, ev_loop, ev_release, ev_slice, ev_kill, ev_melt, ev_growl, ev_drop): place(e_)
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; AI = '/Script/Engine.AnimInstance:'; AR = '/Script/Engine.KismetArrayLibrary:'; SC = '/Script/Engine.SceneComponent:'; PR = '/Script/Engine.PrimitiveComponent:'; SKM = '/Script/Engine.SkeletalMeshComponent:'; MC = '/Script/Engine.MeshComponent:'
def pin_in(n, p):
    r = BEL.find_input_pin(n, p)
    if not r: raise SystemExit('CHAIN546 no input pin %s.%s (have %s)' % (n.get_name(), p, [str(PL.get_pin_name(x)) for x in BEL.list_input_pins(n)]))
    return r
def pin_out(n, p):
    r = BEL.find_output_pin(n, p)
    if not r: raise SystemExit('CHAIN546 no output pin %s.%s (have %s)' % (n.get_name(), p, [str(PL.get_pin_name(x)) for x in BEL.list_output_pins(n)]))
    return r
def lit(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (list, tuple)): return ','.join('%.6f' % x for x in v)
    return str(v)
def wire(n, args):
    links = {k: v for k, v in args.items() if isinstance(v, tuple) and len(v) == 2 and not isinstance(v[0], (int, float))}
    for k, v in links.items():
        if not PL.try_create_connection(pin_out(v[0], v[1]), pin_in(n, k)): raise SystemExit('CHAIN546 link failed %s.%s (%s) -> %s.%s (%s)' % (v[0].get_name(), v[1], PL.get_pin_type_display_string(pin_out(v[0], v[1])), n.get_name(), k, PL.get_pin_type_display_string(pin_in(n, k))))
    for k, v in args.items():
        if k not in links: PL.set_pin_value(pin_in(n, k), lit(v))
    return n
def call(path, **a):
    n = ge.add_call_function_node(path)
    if not n: raise SystemExit('CHAIN546 no function ' + path)
    return wire(place(n), a)
def fn(op, out='ReturnValue', **a): return (call(M + op, **a), out)
def get(v): return (place(ge.add_get_member_variable_node(v, '')), v)
def setv(v, src): return wire(place(ge.add_set_member_variable_node(v, '')), {v: src})
def then(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('CHAIN546 exec failed %s -> %s' % (a.get_name(), b.get_name()))
    return ns[-1]
def out_exec(a, pa, b):
    if not PL.try_create_connection(pin_out(a, pa), BEL.find_execute_pin(b)): raise SystemExit('CHAIN546 exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
def branch(cond): return wire(place(ge.add_branch_node()), {'Condition': cond})
def add(a, b): return fn('Add_DoubleDouble', A=a, B=b)
def sub(a, b): return fn('Subtract_DoubleDouble', A=a, B=b)
def mul(a, b): return fn('Multiply_DoubleDouble', A=a, B=b)
def div(a, b): return fn('Divide_DoubleDouble', A=a, B=b)
def vadd(a, b): return fn('Add_VectorVector', A=a, B=b)
def vsub(a, b): return fn('Subtract_VectorVector', A=a, B=b)
def vmul(a, b):
    b = fn('SelectFloat', A=b, B=0.0, bPickA=True)     # a concrete double: otherwise the float's own operator gets promoted to a vector
    return fn('Multiply_VectorFloat', A=a, B=b)
def gt(a, b): return fn('Greater_DoubleDouble', A=a, B=b)
def lt_(a, b): return fn('Less_DoubleDouble', A=a, B=b)
def eqi(a, b): return fn('EqualEqual_IntInt', A=a, B=b)
def sat(a): return fn('FClamp', Value=a, Min=0.0, Max=1.0)
def agetv(arr, i): return (call(AR + 'Array_Get', TargetArray=get(arr), Index=i), 'Item')
def apush(arr, item): return call(AR + 'Array_Add', TargetArray=get(arr), NewItem=item)
def aset(arr, i, item): return call(AR + 'Array_Set', TargetArray=get(arr), Index=i, Item=item, bSizeToFit=False)
def compget(name): return get(name)
def hero(): return (call(GS + 'GetPlayerPawn', PlayerIndex=0), 'ReturnValue')
def anim(): return (call(SKM + 'GetAnimInstance', self=compget('Mesh')), 'ReturnValue')
def montage(c, rate=1.0): return call(AI + 'Montage_Play', self=anim(), MontageToPlay=unreal.load_asset(D_ + '/Anims/AM_' + c).get_path_name(), InPlayRate=rate)
def sound(key, at, vol=1.0):
    if not SOUNDS.get(key): return None
    a = {'Sound': SOUNDS[key], 'Location': at, 'VolumeMultiplier': vol}
    if SOUNDS.get('att'): a['AttenuationSettings'] = SOUNDS['att']
    return call(GS + 'PlaySoundAtLocation', **a)
def emit(key, at, sc=1.0):
    if not FX.get(key): return None
    return call(GS + 'SpawnEmitterAtLocation', EmitterTemplate=FX[key], Location=at, Scale=(sc, sc, sc), bAutoDestroy=True)
def blood(at):
    if not BLOOD_CLS: return None
    n = None
    for x in ge.list_available_nodes([]):
        if str(x).endswith('Spawn Actor from Class') or 'SpawnActorFromClass' in str(x): n = ge.create_node_from_name(str(x), unreal.Vector2D(0, 0), []); break
    if not n: say('note: no Spawn Actor node; no blood burst'); return None
    place(n); PL.set_pin_value(pin_in(n, 'Class'), BLOOD_CLS); wire(n, {'SpawnTransform': (call(M + 'MakeTransform', Location=at, Scale=(1.0, 1.0, 1.0)), 'ReturnValue')}); return n
def seq(*ns):
    ns = [n for n in ns if n is not None]; then(*ns); return ns[-1]
def on_mats(op, name, value): return {'ParameterName': name, 'ParameterValue': value}
def set_scalar(name, value): return call(MC + 'SetScalarParameterValueOnMaterials', self=compget('Mesh'), ParameterName=name, ParameterValue=value)
def macro(name):
    n = None
    for path in ('/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:' + name,):
        try: n = ge.add_macro_node(path)
        except Exception as e: say('macro try', path, e)
        if n: return place(n)
    raise SystemExit('CHAIN546 no macro ' + name)
ACT_LOC = lambda: (call(AC + 'K2_GetActorLocation'), 'ReturnValue')
ACT_FWD = lambda: (call(AC + 'GetActorForwardVector'), 'ReturnValue')
ACT_RT = lambda: (call(AC + 'GetActorRightVector'), 'ReturnValue')
def now(): return (call(GS + 'GetTimeSeconds'), 'ReturnValue')
Z = (0.0, 0.0, 1.0)

# ---- SegRun: lay SegN links from SegA to SegE, with the sag a chain of length SegLen really has between those points
d_ = fn('VSize', A=vsub(get('SegE'), get('SegA')))
slack = fn('FMax', A=sub(get('SegLen'), d_), B=0.0)
sag = fn('Sqrt', A=div(mul(mul(3.0, d_), slack), 8.0))
s_set = setv('SegS', sag); then(ev_seg, s_set)
loop = macro('ForLoop'); wire(loop, {'FirstIndex': 0, 'LastIndex': fn('Subtract_IntInt', A=get('SegN'), B=1)}); PL.try_create_connection(BEL.find_then_pin(s_set), BEL.find_execute_pin(loop))
j_ = (loop, 'Index'); nf = fn('Conv_IntToDouble', InInt=get('SegN')); jf = fn('Conv_IntToDouble', InInt=j_)
def pt(u):
    span = vsub(get('SegE'), get('SegA')); w = mul(mul(4.0, get('SegS')), mul(u, sub(1.0, u)))
    return vsub(vadd(get('SegA'), vmul(span, u)), vmul(Z_V(), w))
def Z_V(): return (place(ge.add_get_member_variable_node('ZUp', '')), 'ZUp')
BEL.add_member_variable(bp, 'ZUp', V); BEL.compile_blueprint(bp)
u0 = div(jf, nf); u1 = div(add(jf, 1.0), nf); p0 = pt(u0); p1 = pt(u1)
mid = vmul(vadd(p0, p1), 0.5); dirv = vsub(p1, p0)
odd = eqi(fn('Percent_IntInt', A=j_, B=2), 1); fwd = ACT_FWD()
zc = fn('SelectVector', A=fn('Cross_VectorVector', A=dirv, B=fwd), B=fwd, bPickA=odd)
rot = fn('MakeRotFromXZ', X=dirv, Z=zc)
item = agetv('LinksArr', fn('Add_IntInt', A=get('SegFirst'), B=j_))
sw = call(SC + 'K2_SetWorldLocationAndRotation', self=item, NewLocation=mid, NewRotation=rot, bSweep=False, bTeleport=True)
out_exec(loop, 'LoopBody', sw)

# ---- ChainStep (Cur = chain): cuff lug -> anchor, or the cut / released ends hanging and swinging
cur = lambda: get('Cur')
cuffC = lambda: agetv('CuffArr', cur())
lug = vsub((call(SC + 'K2_GetComponentLocation', self=cuffC()), 'ReturnValue'), vmul((call(SC + 'GetUpVector', self=cuffC()), 'ReturnValue'), agetv('CLug', cur())))
sl = setv('LugP', lug); then(ev_chain, sl)
mode = lambda: agetv('ModeA', cur())
rsp = fn('VSize', A=vsub(get('LugP'), agetv('LastLug', cur())))
rat = branch(fn('BooleanAND', A=gt(rsp, mul(get('Dt'), 105.0)), B=gt(get('Now'), get('NextRattle')))); rl1 = aset('LastLug', cur(), get('LugP')); then(sl, rat)
nr = setv('NextRattle', add(get('Now'), fn('RandomFloatInRange', Min=0.28, Max=0.62))); out_exec(rat, 'then', nr)
_rs = None
if SOUNDS.get('metal1'):
    _a = {'Sound': SOUNDS['metal1'], 'Location': get('LugP'), 'VolumeMultiplier': fn('RandomFloatInRange', Min=0.16, Max=0.34), 'PitchMultiplier': fn('RandomFloatInRange', Min=0.8, Max=1.25)}
    if SOUNDS.get('att'): _a['AttenuationSettings'] = SOUNDS['att']
    _rs = call(GS + 'PlaySoundAtLocation', **_a); then(nr, _rs)
then(_rs if _rs else nr, rl1); out_exec(rat, 'else', rl1)
br0 = branch(eqi(mode(), 0)); then(rl1, br0)
s1 = setv('SegA', agetv('Anch', cur())); s2 = setv('SegE', get('LugP')); s3 = setv('SegLen', agetv('CLen', cur())); s4 = setv('SegFirst', agetv('CFirst', cur())); s5 = setv('SegN', agetv('CN', cur())); runA = call(CLS + ':SegRun')
out_exec(br0, 'then', s1); then(s1, s2, s3, s4, s5, runA)
# hanging: from where the chain was, to straight down from the anchor, with a dying swing out from the wall. Mode 1 = cut: 4 of the 7 links stay on the wall. Mode 2 = whole chain let go
is1 = lambda: eqi(mode(), 1)
frac = fn('SelectFloat', A=0.571, B=1.0, bPickA=is1())
hlen = mul(agetv('CLen', cur()), frac); age = sub(get('Now'), agetv('RelT', cur()))
down = vsub(agetv('Anch', cur()), vmul(Z_V(), hlen)); al = sat(div(age, 0.38)); al2 = mul(al, al)
sw_amp = mul(mul(hlen, 0.26), mul(fn('Sin', A=mul(age, 4.7)), fn('Exp', A=mul(age, -0.62))))
endp = vadd(fn('VLerp', A=agetv('RelP', cur()), B=down, Alpha=al2), vmul(ACT_FWD(), sw_amp))
h1 = setv('SegA', agetv('Anch', cur())); h2 = setv('SegE', endp); h3 = setv('SegLen', hlen); h4 = setv('SegFirst', agetv('CFirst', cur()))
# Select for int: 5 if cut, else CN
br_n = branch(is1()); h5a = setv('SegN', 4); h5b = setv('SegN', agetv('CN', cur())); runB = call(CLS + ':SegRun')
out_exec(br0, 'else', h1); then(h1, h2, h3, h4, br_n); out_exec(br_n, 'then', h5a); out_exec(br_n, 'else', h5b); then(h5a, runB); then(h5b, runB)
# whole chain let go: the empty cuff rides the end
br_c = branch(eqi(mode(), 2)); then(runB, br_c)
cuffP = call(SC + 'K2_SetWorldLocationAndRotation', self=cuffC(), NewLocation=vadd(get('SegE'), vmul(Z_V(), mul(agetv('CLug', cur()), -1.0))), NewRotation=fn('MakeRotFromXZ', X=ACT_RT(), Z=vmul(Z_V(), -1.0)), bSweep=False, bTeleport=True); out_exec(br_c, 'then', cuffP)
# cut: the stub (2 links) dangles from the wrist with a lag
stub = branch(fn('BooleanAND', A=get('StubOn'), B=is1())); out_exec(br_c, 'else', stub)
t_ = setv('TailP', fn('VInterpTo', Current=get('TailP'), Target=vsub(get('LugP'), vmul(Z_V(), 17.0)), DeltaTime=get('Dt'), InterpSpeed=7.0))
u1_ = setv('SegA', get('LugP')); u2_ = setv('SegE', get('TailP')); u3_ = setv('SegLen', 17.5); u4_ = setv('SegFirst', fn('Add_IntInt', A=agetv('CFirst', cur()), B=5)); u5_ = setv('SegN', 2); runC = call(CLS + ':SegRun')
out_exec(stub, 'then', t_); then(t_, u1_, u2_, u3_, u4_, u5_, runC)

# ---- PlayLoop: the state's loop, at a varied rate (+-6 %), so he never repeats exactly
rate = setv('LoopRate', fn('RandomFloatInRange', Min=0.94, Max=1.06))
br_s = branch(eqi(get('State'), 0)); then(ev_loop, rate, br_s)
mT = montage('CH_Thrash', get('LoopRate')); lT = setv('LoopT', add(get('Now'), sub(div(10.0, get('LoopRate')), 0.25))); out_exec(br_s, 'then', mT); then(mT, lT)
brS = branch(eqi(get('FreeSide'), 0)); out_exec(br_s, 'else', brS)
mL = montage('CH_Free_L', get('LoopRate')); mR = montage('CH_Free_R', get('LoopRate')); lF = setv('LoopT', add(get('Now'), sub(div(6.0, get('LoopRate')), 0.25)))
out_exec(brS, 'then', mL); out_exec(brS, 'else', mR); then(mL, lF); then(mR, lF)

# ---- ReleaseCur: a chain lets go as the melt front reaches it
r1 = aset('RelP', cur(), get('LugP')); r2 = aset('RelT', cur(), get('Now')); r3 = aset('ModeA', cur(), 2); r4 = call(SC + 'K2_DetachFromComponent', self=cuffC(), LocationRule='KeepWorld', RotationRule='KeepWorld', ScaleRule='KeepWorld', bCallModify=False)
then(ev_release, r1, r2, r3, r4)

# ---- DoSlice: the first cut. The arm on the hero's side comes free
heroSide = gt(fn('Dot_VectorVector', A=vsub(get('HeroP'), ACT_LOC()), B=ACT_RT()), 0.0)     # hero on the actor's right = the zombie's RIGHT arm
a0 = setv('FreeSide', 0); a1 = setv('FreeSide', 1); brH = branch(heroSide); then(ev_slice, brH); out_exec(brH, 'then', a1); out_exec(brH, 'else', a0)
st1 = setv('State', 1); then(a0, st1); then(a1, st1)
fs = lambda: get('FreeSide')
lug2 = setv('Cur', fs()); stepL = call(CLS + ':ChainStep')      # refresh LugP for this arm
relP = aset('RelP', fs(), fn('VLerp', A=agetv('Anch', fs()), B=get('LugP'), Alpha=0.571)); relT = aset('RelT', fs(), get('Now')); modeS = aset('ModeA', fs(), 1); tailS = setv('TailP', vsub(get('LugP'), vmul(Z_V(), 17.0))); stubS = setv('StubOn', True)
cutP = lambda: fn('VLerp', A=agetv('Anch', fs()), B=get('LugP'), Alpha=0.68)
hideL = call(SC + 'SetVisibility', self=agetv('LinksArr', fn('Add_IntInt', A=agetv('CFirst', fs()), B=4)), bNewVisibility=False)
flyP = call(SC + 'K2_SetWorldLocation', self=compget('FlyLink'), NewLocation=cutP(), bSweep=False, bTeleport=True); flyV = call(SC + 'SetVisibility', self=compget('FlyLink'), bNewVisibility=True)
flyC = setv('FlyP', cutP()); flyS = setv('FlyT', get('Now'))
flyV_ = setv('FlyV', vmul(fn('RandomUnitVectorInConeInDegrees', ConeDir=ACT_FWD(), ConeHalfAngleInDegrees=50.0), 430.0)); flyI = setv('FlyOn', True); then(flyV_, flyI)
wd1 = None
sp1 = emit('sparks', cutP(), 1.0); bl1 = blood(vsub((call(SC + 'K2_GetComponentLocation', self=agetv('CuffArr', fs())), 'ReturnValue'), vmul(ACT_FWD(), -14.0)))
sn1 = sound('metal1', cutP(), 1.0); sn2 = sound('plate', cutP(), 0.7); sn3 = sound('growl3', ACT_LOC(), 1.0)
brM = branch(eqi(fs(), 0)); mSL = montage('CH_Slice_L'); mSR = montage('CH_Slice_R'); loopT1 = setv('LoopT', add(get('Now'), 1.55)); nc = setv('NextClaw', add(get('Now'), 2.4)); bd = setv('BlowDone', True)
seq(st1, lug2, stepL, relP, relT, modeS, tailS, stubS, hideL, flyP, flyV, flyC, flyS, flyV_); seq(flyI, sp1, bl1, sn1, sn2, sn3, brM)
wL_ = set_scalar('WoundL', 1.0); wR_ = set_scalar('WoundR', 1.0); out_exec(brM, 'then', wL_); out_exec(brM, 'else', wR_); then(wL_, mSL); then(wR_, mSR); then(mSL, loopT1); then(mSR, loopT1); then(loopT1, nc, bd)

# ---- DoKill: the second cut. Muscles lock, the heat takes him from the top down
st2 = setv('State', 2); ms_ = setv('MeltStart', get('Now')); lt9 = setv('LoopT', 1e9); colH = call(PR + 'SetCollisionEnabled', self=compget('Hit'), NewType='NoCollision')
core = vadd(ACT_LOC(), vmul(ACT_FWD(), 18.0))
v1 = call(MC + 'SetVectorParameterValueOnMaterials', self=compget('Mesh'), ParameterName='MeltCore', ParameterValue=core); s1g = set_scalar('MeltGround', fn('BreakVector', out='Z', InVec=ACT_LOC()))
pv = call(SC + 'SetVisibility', self=compget('Pool'), bNewVisibility=True)
brK = branch(eqi(fs(), 0)); kL = montage('CH_Death_L'); kR = montage('CH_Death_R')
then(ev_kill, st2, ms_, lt9, colH, v1, s1g, pv, brK); out_exec(brK, 'then', kL); out_exec(brK, 'else', kR)
sm1 = blood(vadd(ACT_LOC(), (0.0, 0.0, 145.0)))
gl = sound('growl2', ACT_LOC(), 1.0)
sizz = None
if SOUNDS.get('sizzle'):
    sa = call(GS + 'SpawnSoundAtLocation', Sound=SOUNDS['sizzle'], Location=ACT_LOC(), VolumeMultiplier=1.0); sizz = setv('Sizzle', (sa, 'ReturnValue')); then(sa, sizz)
smk = None
if FX.get('smoke'):
    em = call(GS + 'SpawnEmitterAttached', EmitterTemplate=FX['smoke'], AttachToComponent=compget('Mesh'), AttachPointName='Spine2', LocationType='KeepRelativeOffset', bAutoDestroy=True); smk = setv('SmokeC', (em, 'ReturnValue')); then(em, smk)
tail_nodes = [n for n in (sm1, gl) if n is not None]
first = tail_nodes[0] if tail_nodes else None
if first: then(kL, first); then(kR, first); seq(*tail_nodes); endk = tail_nodes[-1]
else: endk = None
if sizz:
    if endk: then(endk, sa)
    else: then(kL, sa); then(kR, sa)
    endk = sizz
if smk:
    if endk: then(endk, em)
    else: then(kL, em); then(kR, em)
    endk = smk

# ---- MeltStep: every frame of the melt
t_v = setv('MeltTv', div(sub(get('Now'), get('MeltStart')), get('MeltDur'))); then(ev_melt, t_v)
sm_t = set_scalar('MeltT', get('MeltTv')); then(t_v, sm_t)
tv = lambda: get('MeltTv')
sg = fn('FClamp', Value=div(sub(tv(), 0.12), 0.88), Min=0.0, Max=1.0); sgs = mul(mul(sg, sg), sub(3.0, mul(2.0, sg)))
psc = add(0.02, mul(0.95, sgs)); pscale = call(SC + 'SetRelativeScale3D', self=compget('Pool'), NewScale3D=fn('MakeVector', X=psc, Y=psc, Z=1.0)); then(sm_t, pscale)
ph = call(MC + 'SetScalarParameterValueOnMaterials', self=compget('Pool'), ParameterName='PoolHeat', ParameterValue=1.0); then(pscale, ph)
# one real light rides the melt front: 1900 K. Slow drift + a 9 Hz flutter, like the torches
fl = add(1.0, add(mul(0.12, fn('Sin', A=mul(get('Now'), 1.7))), mul(0.09, fn('Sin', A=mul(get('Now'), 56.5)))))
inten = mul(mul(28.0, fn('FClamp', Value=mul(tv(), 8.0), Min=0.0, Max=1.0)), fl)
li = call('/Script/Engine.LightComponent:SetIntensity', self=compget('HeatLight'), NewIntensity=inten); then(ph, li)
ee = mul(mul(fn('FClamp', Value=tv(), Min=0.0, Max=1.0), fn('FClamp', Value=tv(), Min=0.0, Max=1.0)), sub(2.1, mul(1.1, fn('FClamp', Value=tv(), Min=0.0, Max=1.0))))
lz = add(12.0, mul(205.0, sub(1.0, ee))); lp = call(SC + 'K2_SetRelativeLocation', self=compget('HeatLight'), NewLocation=fn('MakeVector', X=30.0, Y=0.0, Z=lz), bSweep=False, bTeleport=True); then(li, lp)
# the chains let go as the front reaches them: arms first, ankles last
b1 = branch(fn('BooleanAND', A=gt(tv(), 0.30), B=fn('Not_PreBool', A=get('Rel1')))); then(lp, b1)
rr1 = setv('Rel1', True); so = setv('StubOn', False); rs1 = setv('Cur', fn('Subtract_IntInt', A=1, B=fs())); rs2 = call(CLS + ':ChainStep'); rs3 = call(CLS + ':ReleaseCur')
fc = setv('Cur', fs()); dc = call(SC + 'K2_DetachFromComponent', self=cuffC(), LocationRule='KeepWorld', RotationRule='KeepWorld', ScaleRule='KeepWorld', bCallModify=False); dcp = setv('DropP', (call(SC + 'K2_GetComponentLocation', self=cuffC()), 'ReturnValue')); dcs = setv('DropT', get('Now')); dco = setv('DropOn', True)
h6 = call(SC + 'SetVisibility', self=agetv('LinksArr', fn('Add_IntInt', A=agetv('CFirst', fs()), B=5)), bNewVisibility=False); h7 = call(SC + 'SetVisibility', self=agetv('LinksArr', fn('Add_IntInt', A=agetv('CFirst', fs()), B=6)), bNewVisibility=False)
snm = sound('metal2', ACT_LOC(), 0.7)
out_exec(b1, 'then', rr1); seq(rr1, so, rs1, rs2, rs3, fc, dc, dcp, dcs, dco, h6, h7, snm)
b2 = branch(fn('BooleanAND', A=gt(tv(), 0.82), B=fn('Not_PreBool', A=get('Rel2')))); out_exec(b1, 'else', b2); then(snm if snm else h7, b2)
rr2 = setv('Rel2', True); c2 = setv('Cur', 2); c2s = call(CLS + ':ChainStep'); c2r = call(CLS + ':ReleaseCur'); c3 = setv('Cur', 3); c3s = call(CLS + ':ChainStep'); c3r = call(CLS + ':ReleaseCur'); snf = sound('metal1', ACT_LOC(), 0.5)
out_exec(b2, 'then', rr2); seq(rr2, c2, c2s, c2r, c3, c3s, c3r, snf)
b3 = branch(gt(tv(), 1.0)); out_exec(b2, 'else', b3); then(snf if snf else c3r, b3)
st3 = setv('State', 3); hm = call(SC + 'SetVisibility', self=compget('Mesh'), bNewVisibility=False, bPropagateToChildren=False); stm = call(AI + 'Montage_Stop', self=anim(), InBlendOutTime=0.0)
out_exec(b3, 'then', st3); then(st3, hm)
ending = hm
if sizz:
    bz = branch((call(KS + 'IsValid', Object=get('Sizzle')), 'ReturnValue')); then(ending, bz); fo = call('/Script/Engine.AudioComponent:FadeOut', self=get('Sizzle'), FadeOutDuration=6.0, FadeVolumeLevel=0.0); out_exec(bz, 'then', fo); ending = None; end_pins = [(bz, 'else'), (fo, None)]
if smk:
    bk = branch((call(KS + 'IsValid', Object=get('SmokeC')), 'ReturnValue'))
    if ending: then(ending, bk)
    else:
        out_exec(end_pins[0][0], end_pins[0][1], bk); then(end_pins[1][0], bk)
    dsm = call('/Script/Engine.ActorComponent:Deactivate', self=get('SmokeC')); out_exec(bk, 'then', dsm)

# ---- GrowlOnce: he never shuts up, and it only carries as far as a growl carries
rnd = call(M + 'RandomIntegerInRange', Min=0, Max=1)
g1 = sound('growl1', ACT_LOC()); g2 = sound('growl2', ACT_LOC())
ng = setv('NextGrowl', add(get('Now'), fn('RandomFloatInRange', Min=3.6, Max=7.5))); then(ev_growl, ng)
if g1 and g2:
    br_g = branch(fn('RandomBool')); then(ng, br_g); out_exec(br_g, 'then', g1); out_exec(br_g, 'else', g2)

# ---- DropStep: free-falling iron, until it lands
def fallz(p0, t0, zv=0.0):
    t = sub(get('Now'), t0); return t, sub(add(fn('BreakVector', out='Z', InVec=p0), mul(zv, t)), mul(490.0, mul(t, t)))
b_f = branch(get('FlyOn')); then(ev_drop, b_f)
ft = sub(get('Now'), get('FlyT')); fz = fn('FMax', A=sub(add(fn('BreakVector', out='Z', InVec=get('FlyP')), mul(fn('BreakVector', out='Z', InVec=get('FlyV')), ft)), mul(490.0, mul(ft, ft))), B=add(get('GroundZ'), 2.0))
fl_xy = lambda c: add(fn('BreakVector', out=c, InVec=get('FlyP')), mul(fn('BreakVector', out=c, InVec=get('FlyV')), fn('FMin', A=ft, B=0.55)))
fr = fn('MakeRotator', Roll=0.0, Pitch=fn('FMin', A=mul(ft, 520.0), B=270.0), Yaw=mul(fn('FMin', A=ft, B=0.55), 420.0))
fpos = call(SC + 'K2_SetWorldLocationAndRotation', self=compget('FlyLink'), NewLocation=fn('MakeVector', X=fl_xy('X'), Y=fl_xy('Y'), Z=fz), NewRotation=fr, bSweep=False, bTeleport=True); out_exec(b_f, 'then', fpos)
b_fe = branch(gt(ft, 1.6)); then(fpos, b_fe); foff = setv('FlyOn', False); out_exec(b_fe, 'then', foff)
b_d = branch(get('DropOn')); out_exec(b_f, 'else', b_d); out_exec(b_fe, 'else', b_d); then(foff, b_d)
dt_ = sub(get('Now'), get('DropT')); dz = fn('FMax', A=sub(fn('BreakVector', out='Z', InVec=get('DropP')), mul(490.0, mul(dt_, dt_))), B=add(get('GroundZ'), 5.0))
fzc = lambda: agetv('CuffArr', get('FreeSide'))
dpos = call(SC + 'K2_SetWorldLocationAndRotation', self=fzc(), NewLocation=fn('MakeVector', X=fn('BreakVector', out='X', InVec=get('DropP')), Y=fn('BreakVector', out='Y', InVec=get('DropP')), Z=dz), NewRotation=fn('MakeRotator', Roll=0.0, Pitch=fn('FMin', A=mul(dt_, 170.0), B=90.0), Yaw=25.0), bSweep=False, bTeleport=True); out_exec(b_d, 'then', dpos)
b_l = branch(gt(mul(490.0, mul(dt_, dt_)), sub(fn('BreakVector', out='Z', InVec=get('DropP')), add(get('GroundZ'), 5.0)))); then(dpos, b_l)
doff = setv('DropOn', False); out_exec(b_l, 'then', doff); snl = sound('plate', get('DropP'), 0.55)
if snl: then(doff, snl)

# ---- BeginPlay
def event(name):
    for n in ge.list_all_nodes():
        t = str(BEL.get_node_title(n))
        if name in t and n.get_class().get_name().endswith('K2Node_Event'): return n
    o = BEL.add_event_override(bp, name.replace(' ', ''), unreal.IntPoint(0, -1000)); return o
evB = event('BeginPlay')
if not evB: raise SystemExit('CHAIN546 no BeginPlay node')
chainB = [setv('ZUp', Z), setv('State', 0), setv('MeltDur', 8.5), setv('GroundZ', fn('BreakVector', out='Z', InVec=ACT_LOC())), setv('BlowDone', True), setv('NextGrowl', add(now(), 2.0))]
idx = 0
for i, (bn, along, sc, ln, cnt, a) in enumerate(CHAINS):
    chainB.append(call(SC + 'K2_AttachToComponent', self=compget('Cuff%d' % i), Parent=compget('Mesh'), SocketName=bn, LocationRule='KeepRelative', RotationRule='KeepRelative', ScaleRule='KeepRelative', bWeldSimulatedBodies=False))
    chainB.append(apush('CuffArr', compget('Cuff%d' % i)))
    anc = compget('Anchor%d' % i)
    pa = vadd(vadd((call(SC + 'K2_GetComponentLocation', self=anc), 'ReturnValue'), vmul(ACT_FWD(), 5.2)), vmul(Z_V(), -7.8))
    chainB.append(apush('Anch', pa)); chainB.append(apush('LastLug', pa)); chainB.append(apush('RelP', pa)); chainB.append(apush('RelT', 0.0)); chainB.append(apush('ModeA', 0)); chainB.append(apush('CLen', float(ln))); chainB.append(apush('CFirst', idx)); chainB.append(apush('CN', cnt)); chainB.append(apush('CLug', LUG[sc]))
    idx += cnt
for k in range(NL): chainB.append(apush('LinksArr', compget('L%02d' % k)))
chainB.append(call(CLS + ':PlayLoop'))
then(evB, chainB[0]); then(*chainB)

# ---- Any damage: a hit from anything is a slice. One blade swing can land only once in 0.5 s
evD = BEL.add_event_override(bp, 'ReceiveAnyDamage', unreal.IntPoint(0, -1400))
if not evD: raise SystemExit('CHAIN546 no ReceiveAnyDamage override')
okd = branch(fn('BooleanAND', A=gt((evD, 'Damage'), 0.0), B=gt(now(), get('HitLock')))); then(evD, okd)
hl = setv('HitLock', add(now(), 0.5)); out_exec(okd, 'then', hl)
fl1 = sound('flesh', ACT_LOC())
brA = branch(eqi(get('State'), 0))
if fl1: then(hl, fl1, brA)
else: then(hl, brA)
sNow = setv('Now', now()); out_exec(brA, 'then', sNow); doS = call(CLS + ':DoSlice'); then(sNow, doS)
brB = branch(eqi(get('State'), 1)); out_exec(brA, 'else', brB); sNow2 = setv('Now', now()); out_exec(brB, 'then', sNow2); doK = call(CLS + ':DoKill'); then(sNow2, doK)

# ---- Tick. Far away he costs nothing: the chains stop updating past 35 m (the room's walls hide him anyway)
evT = event('Tick')
tn = setv('Now', now()); td = setv('Dt', (evT, 'DeltaSeconds')); then(evT, tn, td)
hv = branch((call(KS + 'IsValid', Object=hero()), 'ReturnValue')); then(td, hv)
hp1 = setv('HeroP', (call(AC + 'K2_GetActorLocation', self=hero()), 'ReturnValue')); hp2 = setv('HeroP', vadd(ACT_LOC(), vmul(ACT_FWD(), 3000.0)))       # no pawn (respawn, cinematic): harmless, chains still move
out_exec(hv, 'then', hp1); out_exec(hv, 'else', hp2)
th = setv('HeroDist', fn('VSize', A=vsub(get('HeroP'), ACT_LOC()))); then(hp1, th); then(hp2, th)
dropc = call(CLS + ':DropStep'); then(th, dropc)
b_loop = branch(fn('BooleanAND', A=gt(get('Now'), get('LoopT')), B=fn('Less_IntInt', A=get('State'), B=2))); then(dropc, b_loop); 
do_loop = call(CLS + ':PlayLoop'); out_exec(b_loop, 'then', do_loop)
# claw: only with one arm loose, only if the hero stands within his reach
b_cl = branch(fn('BooleanAND', A=fn('BooleanAND', A=eqi(get('State'), 1), B=gt(get('Now'), get('NextClaw'))), B=lt_(get('HeroDist'), 185.0)))
out_exec(b_loop, 'else', b_cl); then(do_loop, b_cl)
cl_br = branch(eqi(fs(), 0)); out_exec(b_cl, 'then', cl_br); cL = montage('CH_Claw_L'); cR = montage('CH_Claw_R')
out_exec(cl_br, 'then', cL); out_exec(cl_br, 'else', cR); lc = setv('LoopT', add(get('Now'), 1.1)); then(cL, lc); then(cR, lc); nc2 = setv('NextClaw', add(get('Now'), fn('RandomFloatInRange', Min=2.4, Max=3.6))); btT = setv('BlowT', add(get('Now'), 0.57)); bd2 = setv('BlowDone', False); then(lc, nc2, btT, bd2)
b_bl = branch(fn('BooleanAND', A=fn('BooleanAND', A=eqi(get('State'), 1), B=fn('Not_PreBool', A=get('BlowDone'))), B=gt(get('Now'), get('BlowT'))))
out_exec(b_cl, 'else', b_bl); then(bd2, b_bl)
bd3 = setv('BlowDone', True); out_exec(b_bl, 'then', bd3); b_rc = branch(lt_(get('HeroDist'), 205.0)); then(bd3, b_rc)
dmg = call(GS + 'ApplyDamage', DamagedActor=hero(), BaseDamage=14.0, DamageCauser=(call('/Script/Engine.ActorComponent:GetOwner', self=compget('Mesh')), 'ReturnValue'))
out_exec(b_rc, 'then', dmg)
b_gr = branch(fn('BooleanAND', A=fn('Less_IntInt', A=get('State'), B=2), B=fn('BooleanAND', A=gt(get('Now'), get('NextGrowl')), B=lt_(get('HeroDist'), 2200.0))))
out_exec(b_bl, 'else', b_gr); out_exec(b_rc, 'else', b_gr); then(dmg, b_gr)
g_ = call(CLS + ':GrowlOnce'); out_exec(b_gr, 'then', g_)
b_ch = branch(lt_(get('HeroDist'), 3500.0)); out_exec(b_gr, 'else', b_ch); then(g_, b_ch)
fl_ = macro('ForLoop'); wire(fl_, {'FirstIndex': 0, 'LastIndex': 3}); PL.try_create_connection(pin_out(b_ch, 'then'), BEL.find_execute_pin(fl_))
sc_ = setv('Cur', (fl_, 'Index')); out_exec(fl_, 'LoopBody', sc_); cs_ = call(CLS + ':ChainStep'); then(sc_, cs_)
b_m2 = branch(eqi(get('State'), 2)); out_exec(fl_, 'Completed', b_m2); out_exec(b_ch, 'else', b_m2)
ms2 = call(CLS + ':MeltStep'); out_exec(b_m2, 'then', ms2)
b_m3 = branch(eqi(get('State'), 3)); out_exec(b_m2, 'else', b_m3)
ct = setv('CoolT', div(sub(sub(get('Now'), get('MeltStart')), get('MeltDur')), 30.0)); out_exec(b_m3, 'then', ct)
cool = call(MC + 'SetScalarParameterValueOnMaterials', self=compget('Pool'), ParameterName='PoolHeat', ParameterValue=fn('FClamp', Value=sub(1.0, get('CoolT')), Min=0.0, Max=1.0)); then(ct, cool)
lit2 = call('/Script/Engine.LightComponent:SetIntensity', self=compget('HeatLight'), NewIntensity=mul(28.0, fn('FClamp', Value=sub(1.0, mul(get('CoolT'), 5.0)), Min=0.0, Max=1.0))); then(cool, lit2)
b_end = branch(gt(get('CoolT'), 1.0)); then(lit2, b_end); offT = call(AC + 'SetActorTickEnabled', bEnabled=False); out_exec(b_end, 'then', offT)

ok = BEL.compile_blueprint(bp); errs = sorted(n.get_name() for n in ge.list_nodes_with_errors()); say('compile', ok, 'errors', errs, 'nodes', len(ge.list_all_nodes()))
if errs: raise SystemExit('CHAIN546 compile errors in the NEW blueprint: %s. Not saved, nothing placed; tell i5' % errs)
cdo = unreal.get_default_object(bp.generated_class())
try: cdo.set_editor_property('auto_possess_ai', unreal.AutoPossessAI.DISABLED)
except Exception as e: say('note:', e)
say('saved', EAL.save_asset(BPP, only_if_is_dirty=False))

# ------------------------------------------------- place -------------------------------------------------------------
if not NOPLACE and LOC:
    for a in placed: ES.destroy_actor(a)
    ac = ES.spawn_actor_from_class(bp.generated_class(), unreal.Vector(LOC[0], LOC[1], LOC[2]), unreal.Rotator(roll=0, pitch=0, yaw=LOC[3])); ac.set_actor_label(LABEL); ac.set_folder_path('CastleDefender/ChainedZombie')
    say('placed at', LOC, '; save the level')
say('DONE')

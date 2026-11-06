# #541 Two tentacles erupt beside the gate road, one by one, as the hero walks out (adjustedfilm, 2026-11-06). Editor idle, not in Play, main level open. Needs #540's assets.
#   py rise541_ue.py --dry-run | (no flag: build and place, then save the level) | --revert (remove the placed actors, then save the level)
# Layout (level data): gate near X -340, road along -X at Y 1700. The realm starts at X -8230 on the +Y side, so both arms stand before it.
#   Tentacle 1: north of the road at X -5200, rises when the hero passes 20 m from the gate. Tentacle 2: south of the road at X -9500, rises at 45 m, and never before the first has finished. Both come up ahead of a walking hero, in view.
# Each is a copy of a placed tentacle with everything attached to it (hitboxes, vitals, etc.). It waits underground with StrikeRange 0, rises in 3.4 s after a 1.3 s rumble, then fights normally.
import math, os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); DRY, REV = '--dry-run' in A, '--revert' in A
RIG = '/Game/CastleDefender/Environment/Tentacles/Rig'; D_ = RIG + '/Style530'; SND = D_ + '/Sound'; SB = '/Game/CastleDefender/Environment/Tentacles/SporeBase'; G = '/Game/CastleDefender/Gameplay/Tentacle/'
SRC_LABEL = 'Env_CorruptedTentacle_05'; GATE_X = -340.0; S = 1.8; H = 40.0; TOP = 80.0; HTAB = (-3.0, 1.1, 7.25)     # rig metres at H: centre x, y, trunk radius
SPOTS = [('RiseT1', -5200.0, 5300.0, 'B', 201.0), ('RiseT2', -9500.0, -1900.0, 'A', 37.0)]
ROCK, DRIP_DIR = D_ + '/BP_EruptRock_541', D_; DIRECTOR = D_ + '/BP_TentacleRiseDirector_541'; ERUPT = D_ + '/AM_Tentacle_Erupt'
EAL, AT, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools(), unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
ES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'
def say(*a): print('RISE541', ' '.join(str(x) for x in a))
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise SystemExit('RISE541 stop Play first')
actors = ES.get_all_level_actors(); PFX = ('RiseT1', 'RiseT2', 'RiseBase', 'RiseDirector')
mine = [a for a in actors if a.get_actor_label().startswith(PFX)]
if REV:
    for a in mine: ES.destroy_actor(a)
    say('removed', len(mine), 'actors; save the level'); raise SystemExit(0)
src = next((a for a in actors if a.get_actor_label() == SRC_LABEL), None)
if not src: raise SystemExit('RISE541 no actor ' + SRC_LABEL)
def family(a):
    out = []
    for c in a.get_attached_actors():
        out.append(c); out += family(c)
    return out
fam = family(src); say('source', SRC_LABEL, 'attached actors', len(fam))
def ground(x, y):
    hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, 150000.0), unreal.Vector(x, y, -60000.0), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True); best = None
    for h in (hits or []):
        t = h.to_tuple(); ha = next((v for v in t if isinstance(v, unreal.Actor)), None); v = [q for q in t if isinstance(q, unreal.Vector)]
        if ha is None or not v: continue
        if 'Landscape' in type(ha).__name__: return v[0].z, ha.get_actor_label()
        if best is None and isinstance(ha, unreal.StaticMeshActor) and not ha.get_actor_label().startswith(PFX): best = (v[0].z, ha.get_actor_label())
    return best
plan = []
for lab, x, y, shape, yaw in SPOTS:
    g = ground(x, y)
    if not g: raise SystemExit('RISE541 no ground at %s %s' % (x, y))
    final = g[0] - H * S * 100.0; start = final - (TOP - H) * S * 100.0; r = HTAB[2] * S; size = r / 30.0
    plan.append(dict(lab=lab, x=x - HTAB[0] * S * 100.0, y=y - HTAB[1] * S * 100.0, cx=x, cy=y, gz=g[0], final=final, start=start, size=size, shape=shape, yaw=yaw))
    say(lab, 'centre', x, y, 'ground', round(g[0]), 'on', g[1], 'trunk radius m', round(r, 1), 'above ground m', round((TOP - H) * S), 'base width m', round(190 * size), 'shape', shape)
if DRY:
    for s in (SB + '/SM_TentacleSporeBase_A', SB + '/SM_TentacleSporeBase_B_Col', G + 'BPC_TentacleStrike'): say('needs', s, EAL.does_asset_exist(s))
    say('DONE dry-run'); raise SystemExit(0)
for s in (SB + '/SM_TentacleSporeBase_A', SB + '/SM_TentacleSporeBase_B', SB + '/SM_TentacleSporeBase_A_Col', SB + '/SM_TentacleSporeBase_B_Col', SB + '/M_TentacleSporeBase', SND + '/SW_TentacleRumble'):
    if not EAL.does_asset_exist(s): raise SystemExit('RISE541 missing %s: run sporebase_ue.py (#540) and sfx541_ue.py first' % s)
# ---------- assets
def imp_static(fbx, path):
    if EAL.does_asset_exist(path): return
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_as_skeletal', False); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_animations', False); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property('static_mesh_import_data'); d.set_editor_property('import_uniform_scale', 0.01); d.set_editor_property('vertex_color_import_option', unreal.VertexColorImportOption.REPLACE); d.set_editor_property('generate_lightmap_u_vs', False); d.set_editor_property('combine_meshes', True); d.set_editor_property('auto_generate_collision', False)
    t = unreal.AssetImportTask(); t.filename = fbx; t.destination_path = path.rsplit('/', 1)[0]; t.destination_name = path.rsplit('/', 1)[1]; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t])
    if not EAL.does_asset_exist(path): raise SystemExit('RISE541 import failed ' + path)
imp_static(os.path.join(HERE, 'fbx', 'SM_EruptRock.fbx'), D_ + '/SM_EruptRock'); rm = unreal.load_asset(D_ + '/SM_EruptRock'); rm.set_material(0, unreal.load_asset(SB + '/M_TentacleSporeBase')); EAL.save_loaded_asset(rm)
if not EAL.does_asset_exist(D_ + '/AS_Tentacle_Erupt'):
    skel = unreal.load_asset(RIG + '/SK_CorruptedTentacle_01_Skeleton'); ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True); ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME); ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', 'Tentacle_ERUPT.fbx'); t.destination_path = D_; t.destination_name = 'AS_Tentacle_Erupt'; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t])
    f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', unreal.load_asset(D_ + '/AS_Tentacle_Erupt')); f.set_editor_property('target_skeleton', skel); m = AT.create_asset('AM_Tentacle_Erupt', D_, unreal.AnimMontage, f)
    for k, v in (('blend_in', 0.05), ('blend_out', 0.8)):
        b = m.get_editor_property(k); b.set_editor_property('blend_time', v); m.set_editor_property(k, b)
    EAL.save_loaded_asset(m)
    es = unreal.load_asset(D_ + '/AS_Tentacle_Erupt'); AL = unreal.AnimationLibrary
    if not AL.is_valid_anim_notify_track_name(es, 'SFX541'): AL.add_animation_notify_track(es, 'SFX541')
    nt = AL.add_animation_notify_event(es, 'SFX541', 0.0, unreal.AnimNotify_PlaySound); nt.set_editor_property('sound', unreal.load_asset(SND + '/SW_TentacleRoar')); nt.set_editor_property('pitch_multiplier', 0.92); nt.set_editor_property('follow', True); nt.set_editor_property('attach_name', 'seg_13'); EAL.save_loaded_asset(es)
class G_:
    def __init__(s, bp, y=0): s.bp = bp; s.ge = GE.get_graph_editor(BEL.find_event_graph(bp)); s.p = [0, y]; s.y0 = y
    def place(s, x):
        BEL.set_node_pos(x, unreal.IntPoint(s.p[0], s.p[1])); s.p[0] += 300
        if s.p[0] > 9000: s.p[0] = 0; s.p[1] += 300
        return x
    def call(s, path, **lit):
        x = s.place(s.ge.add_call_function_node(path))
        for k, v in lit.items(): PL.set_pin_value(s.i(x, k), str(v))
        return x
    def i(s, x, p):
        r = BEL.find_input_pin(x, p)
        if not r: raise SystemExit('RISE541 no input pin %s.%s' % (x.get_name(), p))
        return r
    def o(s, x, p):
        r = BEL.find_output_pin(x, p)
        if not r: raise SystemExit('RISE541 no output pin %s.%s' % (x.get_name(), p))
        return r
    def link(s, a, pa, b, pb):
        if not PL.try_create_connection(s.o(a, pa), s.i(b, pb)): raise SystemExit('RISE541 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
    def get(s, v): return s.place(s.ge.add_get_member_variable_node(v))
    def setv(s, v, src=None, pa='ReturnValue', lit=None):
        x = s.place(s.ge.add_set_member_variable_node(v))
        if src is not None: s.link(src, pa, x, v)
        if lit is not None: PL.set_pin_value(s.i(x, v), str(lit))
        return x
    def chain(s, *ns):
        for a, b in zip(ns, ns[1:]):
            if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('RISE541 exec failed %s -> %s' % (a.get_name(), b.get_name()))
    def ex(s, a, pa, b):
        if not PL.try_create_connection(s.o(a, pa), BEL.find_execute_pin(b)): raise SystemExit('RISE541 exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
    def branch(s, c, pc='ReturnValue'): x = s.place(s.ge.add_branch_node()); s.link(c, pc, x, 'Condition'); return x
    def now(s): return s.call(GS + 'GetTimeSeconds')
def new_bp(path):
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor); return AT.create_asset(path.rsplit('/', 1)[1], path.rsplit('/', 1)[0], unreal.Blueprint, f)
# the thrown rock
if not EAL.does_asset_exist(ROCK):
    b = new_bp(ROCK); sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary; root = sds.k2_gather_subobject_data_for_blueprint(b)[0]
    add = lambda cl: lib.get_object(sds.k2_find_subobject_data_from_handle(sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cl, blueprint_context=b))[0]))
    sp = add(unreal.SphereComponent); sm = add(unreal.StaticMeshComponent); pm = add(unreal.ProjectileMovementComponent)
    sp.set_editor_property('sphere_radius', 45.0); sp.set_collision_profile_name('IgnoreOnlyPawn'); sm.set_static_mesh(rm); sm.set_collision_profile_name('NoCollision')
    pm.set_editor_property('should_bounce', True); pm.set_editor_property('bounciness', 0.25); pm.set_editor_property('friction', 0.6); pm.set_editor_property('projectile_gravity_scale', 1.6)
    BEL.compile_blueprint(b); g = G_(b); ev = g.ge.find_event_node('ReceiveBeginPlay')
    if not ev: raise SystemExit('RISE541 rock graph has no BeginPlay')
    c1 = g.call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.ProjectileMovementComponent'); k1 = g.place(g.ge.create_node_from_name('Utilities|Casting|CastToProjectileMovementComponent', unreal.Vector2D(0, 0), [])); g.link(c1, 'ReturnValue', k1, 'Object')
    c2 = g.call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.SphereComponent'); k2 = g.place(g.ge.create_node_from_name('Utilities|Casting|CastToSceneComponent', unreal.Vector2D(0, 0), [])); g.link(c2, 'ReturnValue', k2, 'Object')
    upd = g.call('/Script/Engine.MovementComponent:SetUpdatedComponent'); g.link(k1, 'AsProjectile Movement Component', upd, 'self'); g.link(k2, 'AsScene Component', upd, 'NewUpdatedComponent')
    cone = g.call(M + 'RandomUnitVectorInConeInDegrees', ConeDir='0.000000,0.000000,1.000000', ConeHalfAngleInDegrees=48.0); sp_ = g.call(M + 'RandomFloatInRange', Min=2200.0, Max=6200.0); mu = g.call(M + 'Multiply_VectorFloat'); g.link(cone, 'ReturnValue', mu, 'A'); g.link(sp_, 'ReturnValue', mu, 'B')
    vel = g.call('/Script/Engine.ProjectileMovementComponent:SetVelocityInLocalSpace'); g.link(k1, 'AsProjectile Movement Component', vel, 'self'); g.link(mu, 'ReturnValue', vel, 'NewVelocity'); life = g.call(AC + 'SetLifeSpan', InLifespan=8.0); g.chain(ev, k1, k2, upd, vel, life)
    say('rock compile', BEL.compile_blueprint(b), [x.get_name() for x in g.ge.list_nodes_with_errors()]); EAL.save_asset(ROCK, only_if_is_dirty=False)
# the director
if not EAL.does_asset_exist(DIRECTOR):
    b = new_bp(DIRECTOR); ACT = BEL.get_object_reference_type(unreal.Actor); R_, I_, B_ = BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('bool')
    for v, t in [('T1', ACT), ('T2', ACT), ('B1', ACT), ('B2', ACT), ('C1', ACT), ('C2', ACT), ('V1', ACT), ('V2', ACT), ('Z1', R_), ('Z2', R_), ('GateX', R_), ('Trig1', R_), ('Trig2', R_), ('P', I_), ('Rising', B_), ('RiseT', R_), ('NextT', R_), ('CurZ0', R_), ('CurZ1', R_), ('CurT', ACT), ('CurB', ACT), ('CurC', ACT), ('CurV', ACT)]:
        BEL.add_member_variable(b, v, t)
    for v in ('T1', 'T2', 'B1', 'B2', 'C1', 'C2', 'V1', 'V2', 'Z1', 'Z2', 'GateX', 'Trig1', 'Trig2'): BEL.set_blueprint_variable_instance_editable(b, v, True)
    g = G_(b); erupt = g.place(g.ge.add_custom_event_node('Erupt')); rock_ev = g.place(g.ge.add_custom_event_node('ThrowRock')); BEL.compile_blueprint(b); CLS = b.generated_class().get_path_name(); STR = unreal.load_asset(G + 'BPC_TentacleStrike').generated_class().get_path_name()
    def strike_range(vv, val):
        c = g.call(AC + 'GetComponentByClass'); PL.set_pin_value(g.i(c, 'ComponentClass'), STR); g.link(g.get(vv), vv, c, 'self'); x = g.call(KS + 'SetDoublePropertyByName', PropertyName='StrikeRange', Value=val); g.link(c, 'ReturnValue', x, 'Object'); return x
    def show(vv, hidden):
        a_ = g.call(AC + 'SetActorHiddenInGame', bNewHidden=str(hidden).lower()); g.link(g.get(vv), vv, a_, 'self'); c_ = g.call(AC + 'SetActorEnableCollision', bNewActorEnableCollision=str(not hidden).lower()); g.link(g.get(vv), vv, c_, 'self'); g.chain(a_, c_); return a_, c_
    def loc_of(vv): x = g.call(AC + 'K2_GetActorLocation'); g.link(g.get(vv), vv, x, 'self'); return x
    def snd(name, src, vol=1.0): x = g.call(GS + 'PlaySoundAtLocation', VolumeMultiplier=vol); PL.set_pin_value(g.i(x, 'Sound'), unreal.load_asset(SND + '/' + name).get_path_name()); g.link(src, 'ReturnValue', x, 'Location'); return x
    def shake(src, inner, outer): x = g.call(GS + 'PlayWorldCameraShake', InnerRadius=inner, OuterRadius=outer); PL.set_pin_value(g.i(x, 'Shake'), unreal.load_asset('/Game/CastleDefender/Gameplay/Cannon/BP_CannonShake_Impact').generated_class().get_path_name()); g.link(src, 'ReturnValue', x, 'Epicenter'); return x
    def smoke(src, s_): x = g.call(GS + 'SpawnEmitterAtLocation', Scale='%s,%s,%s' % (s_, s_, s_)); PL.set_pin_value(g.i(x, 'EmitterTemplate'), unreal.load_asset('/Game/CastleDefender/AssetPacks/StarterContent/Particles/P_Smoke').get_path_name()); g.link(src, 'ReturnValue', x, 'Location'); return x
    # BeginPlay: bury and hide
    bp_ev = g.ge.find_event_node('ReceiveBeginPlay'); tk = g.ge.find_event_node('ReceiveTick')
    if not bp_ev or not tk: raise SystemExit('RISE541 director graph has no BeginPlay / Tick')
    seq = [strike_range('V1', 0.0), strike_range('V2', 0.0)]; last = [bp_ev] + seq; g.chain(*last); cur = seq[-1]
    for vv in ('B1', 'C1', 'B2', 'C2'):
        a_, c_ = show(vv, True); g.chain(cur, a_); cur = c_
    # Erupt: rumble, wait, ground breaks, rocks, smoke, arm starts up
    s0 = snd('SW_TentacleRumble', loc_of('CurB')); sh0 = shake(loc_of('CurB'), 2000.0, 12000.0); sm0 = smoke(loc_of('CurB'), 8.0); d0 = g.call(KS + 'Delay', Duration=1.3); g.chain(erupt, s0, sh0, sm0, d0)
    a1, c1 = show('CurB', False); a2, c2 = show('CurC', False); g.chain(d0, a1); g.chain(c1, a2); s1 = snd('SW_TentacleBurst', loc_of('CurB')); sh1 = shake(loc_of('CurB'), 4000.0, 20000.0); sm1 = smoke(loc_of('CurB'), 26.0); g.chain(c2, s1, sh1, sm1)
    xf = g.call(M + 'MakeTransform'); ra = g.call(M + 'RandomUnitVector'); rm_ = g.call(M + 'Multiply_VectorFloat', B=2500.0); g.link(ra, 'ReturnValue', rm_, 'A'); pz = g.call(M + 'Add_VectorVector'); g.link(loc_of('CurB'), 'ReturnValue', pz, 'A'); g.link(rm_, 'ReturnValue', pz, 'B'); pz2 = g.call(M + 'Add_VectorVector', B='0.000000,0.000000,1500.000000'); g.link(pz, 'ReturnValue', pz2, 'A'); g.link(pz2, 'ReturnValue', xf, 'Location')
    rs = g.call(M + 'RandomFloatInRange', Min=1.0, Max=6.0); mk = g.call(M + 'MakeVector'); [g.link(rs, 'ReturnValue', mk, q) for q in 'XYZ']; g.link(mk, 'ReturnValue', xf, 'Scale')
    bg = g.call(GS + 'BeginDeferredActorSpawnFromClass', CollisionHandlingOverride='AlwaysSpawn'); PL.set_pin_value(g.i(bg, 'ActorClass'), unreal.load_asset(ROCK).generated_class().get_path_name()); g.link(xf, 'ReturnValue', bg, 'SpawnTransform'); fs = g.call(GS + 'FinishSpawningActor'); g.link(bg, 'ReturnValue', fs, 'Actor'); g.link(xf, 'ReturnValue', fs, 'SpawnTransform'); g.chain(rock_ev, bg, fs)
    rocks = [g.call(CLS + ':ThrowRock') for _ in range(24)]; g.chain(sm1, *rocks)
    z0 = g.call(AC + 'K2_GetActorLocation'); g.link(g.get('CurT'), 'CurT', z0, 'self'); bk = g.call(M + 'BreakVector'); g.link(z0, 'ReturnValue', bk, 'InVec'); st = g.setv('CurZ0', bk, 'Z'); rt = g.setv('RiseT', g.now()); ri = g.setv('Rising', lit='true'); g.chain(rocks[-1], st, rt, ri)
    cm = g.call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.SkeletalMeshComponent'); g.link(g.get('CurT'), 'CurT', cm, 'self'); ca = g.place(g.ge.create_node_from_name('Utilities|Casting|CastToSkeletalMeshComponent', unreal.Vector2D(0, 0), [])); g.link(cm, 'ReturnValue', ca, 'Object'); g.chain(ri, ca)
    pp = g.call('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance'); g.link(ca, 'AsSkeletal Mesh Component', pp, 'self'); mp = g.call('/Script/Engine.AnimInstance:Montage_Play'); g.link(pp, 'ReturnValue', mp, 'self'); PL.set_pin_value(g.i(mp, 'MontageToPlay'), unreal.load_asset(ERUPT).get_path_name()); iv = g.call(KS + 'IsValid'); g.link(pp, 'ReturnValue', iv, 'Object'); br_p = g.branch(iv); g.chain(ca, br_p); g.ex(br_p, 'then', mp)
    # Tick: move the rising arm, or watch the hero
    br_r = g.branch(g.get('Rising'), 'Rising'); g.chain(tk, br_r)
    sb = g.call(M + 'Subtract_DoubleDouble'); g.link(g.now(), 'ReturnValue', sb, 'A'); g.link(g.get('RiseT'), 'RiseT', sb, 'B'); dv = g.call(M + 'Divide_DoubleDouble', B=3.4); g.link(sb, 'ReturnValue', dv, 'A'); cl = g.call(M + 'FClamp', Min=0.0, Max=1.0); g.link(dv, 'ReturnValue', cl, 'Value')
    om = g.call(M + 'Subtract_DoubleDouble', A=1.0); g.link(cl, 'ReturnValue', om, 'B'); m1 = g.call(M + 'Multiply_DoubleDouble'); g.link(om, 'ReturnValue', m1, 'A'); g.link(om, 'ReturnValue', m1, 'B'); m2 = g.call(M + 'Multiply_DoubleDouble'); g.link(m1, 'ReturnValue', m2, 'A'); g.link(om, 'ReturnValue', m2, 'B'); oe = g.call(M + 'Subtract_DoubleDouble', A=1.0); g.link(m2, 'ReturnValue', oe, 'B')
    lz = g.call(M + 'Lerp'); g.link(g.get('CurZ0'), 'CurZ0', lz, 'A'); g.link(g.get('CurZ1'), 'CurZ1', lz, 'B'); g.link(oe, 'ReturnValue', lz, 'Alpha')
    cur_l = g.call(AC + 'K2_GetActorLocation'); g.link(g.get('CurT'), 'CurT', cur_l, 'self'); bk2 = g.call(M + 'BreakVector'); g.link(cur_l, 'ReturnValue', bk2, 'InVec'); mv_ = g.call(M + 'MakeVector'); g.link(bk2, 'X', mv_, 'X'); g.link(bk2, 'Y', mv_, 'Y'); g.link(lz, 'ReturnValue', mv_, 'Z')
    sl = g.call(AC + 'K2_SetActorLocation', bTeleport='true'); g.link(g.get('CurT'), 'CurT', sl, 'self'); g.link(mv_, 'ReturnValue', sl, 'NewLocation'); g.ex(br_r, 'then', sl)
    done = g.call(M + 'GreaterEqual_DoubleDouble', B=1.0); g.link(cl, 'ReturnValue', done, 'A'); br_d = g.branch(done); g.chain(sl, br_d)
    fin = strike_range('CurV', 19000.0); g.ex(br_d, 'then', fin); r0 = g.setv('Rising', lit='false'); an = g.call(M + 'Add_DoubleDouble', B=0.3); g.link(g.now(), 'ReturnValue', an, 'A'); nt = g.setv('NextT', an); inc = g.call(M + 'Add_IntInt', B=1); g.link(g.get('P'), 'P', inc, 'A'); pp1 = g.setv('P', inc); g.chain(fin, r0, nt, pp1)
    def hero_past(trig):
        pw = g.call(GS + 'GetPlayerPawn'); lc = g.call(AC + 'K2_GetActorLocation'); g.link(pw, 'ReturnValue', lc, 'self'); bv = g.call(M + 'BreakVector'); g.link(lc, 'ReturnValue', bv, 'InVec'); sx = g.call(M + 'Subtract_DoubleDouble'); g.link(g.get('GateX'), 'GateX', sx, 'A'); g.link(g.get(trig), trig, sx, 'B'); lt = g.call(M + 'Less_DoubleDouble'); g.link(bv, 'X', lt, 'A'); g.link(sx, 'ReturnValue', lt, 'B'); return lt
    def p_is(v): x = g.call(M + 'EqualEqual_IntInt', B=v); g.link(g.get('P'), 'P', x, 'A'); return x
    def both(a, b_): x = g.call(M + 'BooleanAND'); g.link(a, 'ReturnValue', x, 'A'); g.link(b_, 'ReturnValue', x, 'B'); return x
    def start(tt, bb, cc, vv, zz, pv):
        ss = [g.setv('CurT', g.get(tt), tt), g.setv('CurB', g.get(bb), bb), g.setv('CurC', g.get(cc), cc), g.setv('CurV', g.get(vv), vv), g.setv('CurZ1', g.get(zz), zz), g.setv('P', lit=pv)]; ce = g.call(CLS + ':Erupt'); g.chain(*(ss + [ce])); return ss[0]
    br1 = g.branch(both(p_is(0), hero_past('Trig1'))); g.ex(br_r, 'else', br1); first = start('T1', 'B1', 'C1', 'V1', 'Z1', 1); g.ex(br1, 'then', first)
    lt_t = g.call(M + 'Greater_DoubleDouble'); g.link(g.now(), 'ReturnValue', lt_t, 'A'); g.link(g.get('NextT'), 'NextT', lt_t, 'B'); br2 = g.branch(both(both(p_is(2), hero_past('Trig2')), lt_t)); g.ex(br1, 'else', br2); second = start('T2', 'B2', 'C2', 'V2', 'Z2', 3); g.ex(br2, 'then', second)
    say('director compile', BEL.compile_blueprint(b), [x.get_name() for x in g.ge.list_nodes_with_errors()]); EAL.save_asset(DIRECTOR, only_if_is_dirty=False)
# ---------- placement
for a in mine: ES.destroy_actor(a)
sets = {}
for p in plan:
    lab = p['lab']; clones = {}
    for a in [src] + fam:
        c = ES.duplicate_actor(a); clones[a.get_name()] = c
        c.set_actor_label(lab + '_' + a.get_actor_label()); c.set_folder_path('RiseTentacles')
    for a in fam:
        par = a.get_attach_parent_actor(); sock = a.root_component.get_attach_socket_name() if a.root_component else 'None'
        if par and par.get_name() in clones: clones[a.get_name()].attach_to_actor(clones[par.get_name()], sock, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    t = clones[src.get_name()]; t.set_actor_scale3d(unreal.Vector(S, S, S)); t.set_actor_location(unreal.Vector(p['x'], p['y'], p['start']), False, True); vit = next((clones[a.get_name()] for a in fam if a.get_component_by_class(unreal.load_asset(G + 'BPC_TentacleStrike').generated_class())), None)
    mk = lambda lb, mesh: ES.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(p['cx'], p['cy'], p['gz'] - 60.0), unreal.Rotator(0, 0, p['yaw']))
    b = mk(0, 0); b.set_actor_label('RiseBase_' + lab); b.set_folder_path('RiseTentacles'); b.set_actor_scale3d(unreal.Vector(p['size'], p['size'], p['size'])); b.static_mesh_component.set_static_mesh(unreal.load_asset(SB + '/SM_TentacleSporeBase_' + p['shape'])); b.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); b.static_mesh_component.set_editor_property('can_ever_affect_navigation', False)
    k = mk(0, 0); k.set_actor_label('RiseBase_Col_' + lab); k.set_folder_path('RiseTentacles'); k.set_actor_scale3d(unreal.Vector(p['size'], p['size'], p['size'])); k.static_mesh_component.set_static_mesh(unreal.load_asset(SB + '/SM_TentacleSporeBase_%s_Col' % p['shape'])); k.static_mesh_component.set_collision_profile_name('BlockAll'); k.static_mesh_component.set_editor_property('can_ever_affect_navigation', False); k.set_actor_hidden_in_game(True)
    sets[lab] = dict(t=t, v=vit, b=b, k=k, z=p['final']); say(lab, 'placed', len(clones), 'actors, starts z', round(p['start']), 'ends z', round(p['final']), 'vitals', vit.get_actor_label() if vit else None)
d = ES.spawn_actor_from_class(unreal.load_asset(DIRECTOR).generated_class(), unreal.Vector(GATE_X, 1700, 500)); d.set_actor_label('RiseDirector'); d.set_folder_path('RiseTentacles')
for pfx, lab in (('1', 'RiseT1'), ('2', 'RiseT2')):
    s_ = sets[lab]; d.set_editor_property('T' + pfx, s_['t']); d.set_editor_property('B' + pfx, s_['b']); d.set_editor_property('C' + pfx, s_['k']); d.set_editor_property('V' + pfx, s_['v']); d.set_editor_property('Z' + pfx, s_['z'])
d.set_editor_property('GateX', GATE_X); d.set_editor_property('Trig1', 2000.0); d.set_editor_property('Trig2', 4500.0)
say('DONE placed; save the level')

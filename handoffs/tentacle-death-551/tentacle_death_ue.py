# Tentacle death: the arm collapses, its base's pods burst one after another, the base goes dark (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste.
#   py tentacle_death_ue.py --dry-run | --apply | --revert          Needs #529 (applied) and #539's sporebase_ue.py.
# 1. Writes the new fall into AS_Tentacle_CannonC in place (same 6 s, backup AS_Tentacle_CannonC_BAK551), so the montage and every check on it keep working, and stops the montage blending back to the idle at its end.
# 2. BP_TentacleVitals death chain: fires the new event BaseDeath just before the 1.6 s Delay. It finds the nearest actor tagged SporeBase within 150 m (runtime eruption bases must add that tag),
#    then 8 times, 0.4 s apart: a BP_BloodBurst (x2) with a wet splat on a random spot of the base, and the base's Dead material value steps up to 1 (dark, dull). No base nearby: nothing happens.
# 3. The 1.6 s Delay before the sink becomes 4.4 s, so the arm has fallen before it starts to go down.
# New nodes sit at y >= 17000. --revert removes them, relinks and restores the clip. The script STOPS if a node name is missing.
import os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
P_ = '/Game/CastleDefender/Environment/Tentacles/Rig/Polish457/'; CLIP, BAK, MON = P_ + 'AS_Tentacle_CannonC', P_ + 'AS_Tentacle_CannonC_BAK551', P_ + 'AM_Tentacle_CannonC'; TMP = '/Game/CastleDefender/Gameplay/Tentacle/Eruption/AS_Tentacle_DeathFall'
PATH = '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'; BURST = '/Game/CastleDefender/VFX/BP_BloodBurst'; SPLAT = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530/Sound/SW_BlobSplat'
E, BEL, PL, GE, AT = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor, unreal.AssetToolsHelpers.get_asset_tools()
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; YMIN = 17000
def say(*a): print('DEATH551', ' '.join(str(x) for x in a))
opts = unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW); LOC = unreal.AnimPoseSpaces.LOCAL
def copy_anim(src, dst):
    n = unreal.AnimationLibrary.get_num_frames(src); poses = [unreal.AnimPoseExtensions.get_anim_pose_at_frame(src, f, opts) for f in range(n + 1)]; bones = [str(b) for b in unreal.AnimPoseExtensions.get_bone_names(poses[0])]; c = dst.controller
    c.open_bracket(unreal.Text('DEATH551')); c.set_frame_rate(unreal.FrameRate(24, 1)); c.set_number_of_frames(unreal.FrameNumber(n))
    for b in bones:
        c.add_bone_curve(b); ts = [unreal.AnimPoseExtensions.get_bone_pose(p, b, LOC) for p in poses]; c.set_bone_track_keys(b, [t.translation for t in ts], [t.rotation for t in ts], [t.scale3d for t in ts])
    c.close_bracket(); return n
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); n = {x.get_name(): x for x in ge.list_all_nodes()}; mine = [x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]
if 'CX_163' not in n: raise SystemExit('DEATH551 CX_163 missing; BP_TentacleVitals changed, send i5 a fresh export')
if '--revert' in A:
    if mine:
        c = next(x for x in mine if x.get_name().startswith('K2Node_CallFunction') and PL.list_connected_pins(BEL.find_then_pin(x)) and any(PL.get_owning_node(q) == n['CX_163'] for q in PL.list_connected_pins(BEL.find_then_pin(x))))
        PL.set_pin_value(BEL.find_input_pin(n['CX_163'], 'Duration'), '1.6'); src = list(PL.list_connected_pins(BEL.find_execute_pin(c))); ge.remove_nodes(mine); say('relink', [PL.try_create_connection(p, BEL.find_execute_pin(n['CX_163'])) for p in src]); say('compile', BEL.compile_blueprint(bp)); say('saved', E.save_asset(PATH, only_if_is_dirty=False))
    if E.does_asset_exist(BAK): d = unreal.load_asset(CLIP); copy_anim(unreal.load_asset(BAK), d); E.save_loaded_asset(d); say('clip restored')
    mt = unreal.load_asset(MON); mt.set_editor_property('enable_auto_blend_out', True); E.save_loaded_asset(mt); say('DONE revert'); raise SystemExit(0)
for p in (CLIP, MON, BURST, SPLAT):
    if not E.does_asset_exist(p): raise SystemExit('DEATH551 missing ' + p)
if '--apply' not in A: say('WOULD back up and rewrite', CLIP, '; WOULD wire BaseDeath before CX_163, links in', len(list(PL.list_connected_pins(BEL.find_execute_pin(n['CX_163'])))), 'already wired:', bool(mine)); raise SystemExit(0)
# the clip
if not E.does_asset_exist(BAK): say('backup', E.duplicate_asset(CLIP, BAK) is not None); E.save_asset(BAK, only_if_is_dirty=False)
skel = unreal.load_asset('/Game/CastleDefender/Environment/Tentacles/Rig/SK_CorruptedTentacle_01_Skeleton'); ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', True); ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME); ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', 'Tentacle_DEATHFALL.fbx'); t.destination_path = TMP.rsplit('/', 1)[0]; t.destination_name = TMP.rsplit('/', 1)[1]; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; AT.import_asset_tasks([t]); s = unreal.load_asset(TMP)
if not s: raise SystemExit('DEATH551 clip import failed; nothing changed')
d = unreal.load_asset(CLIP); say('frames new', copy_anim(s, d), 'len', round(d.get_play_length(), 2)); E.save_loaded_asset(d); mt = unreal.load_asset(MON); mt.set_editor_property('enable_auto_blend_out', False); E.save_loaded_asset(mt)
if mine: say('graph already wired', len(mine)); say('DONE'); raise SystemExit(0)
# the graph
BEL.compile_blueprint(bp); before = sorted(x.get_name() for x in ge.list_nodes_with_errors())
BEL.add_member_variable(bp, 'DeadBase', BEL.get_object_reference_type(unreal.Actor)); BEL.add_member_variable(bp, 'DeadStep', BEL.get_basic_type_by_name('real')); ev = ge.add_custom_event_node('BaseDeath'); ev2 = ge.add_custom_event_node('PodBurst'); BEL.compile_blueprint(bp); CLS = bp.generated_class().get_path_name(); pos = [0, YMIN]
def place(x):
    BEL.set_node_pos(x, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300
    if pos[0] > 6000: pos[0] = 0; pos[1] += 300
    return x
place(ev); place(ev2)
def ip(x, p):
    r = BEL.find_input_pin(x, p)
    if not r: raise SystemExit('DEATH551 no input pin %s.%s' % (x.get_name(), p))
    return r
def call(path, **lit):
    x = place(ge.add_call_function_node(path))
    for k, v in lit.items(): PL.set_pin_value(ip(x, k), str(v))
    return x
def link(a, pa, b, pb):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), ip(b, pb)): raise SystemExit('DEATH551 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def chain(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('DEATH551 exec failed %s -> %s' % (a.get_name(), b.get_name()))
def get(v): return place(ge.add_get_member_variable_node(v))
def setv(v, src=None, pa='ReturnValue', lit=None):
    x = place(ge.add_set_member_variable_node(v))
    if src is not None: link(src, pa, x, v)
    if lit is not None: PL.set_pin_value(ip(x, v), str(lit))
    return x
# BaseDeath: find the base, then burst pods
all_ = call(GS + 'GetAllActorsWithTag', Tag='SporeBase'); me = call(AC + 'K2_GetActorLocation'); near = call(GS + 'FindNearestActor'); link(me, 'ReturnValue', near, 'Origin'); link(all_, 'OutActors', near, 'ActorsToCheck'); chain(ev, all_)
iv = call(KS + 'IsValid'); link(near, 'ReturnValue', iv, 'Object'); cl = call(M + 'Less_DoubleDouble', B=15000.0); link(near, 'Distance', cl, 'A'); an = call(M + 'BooleanAND'); link(iv, 'ReturnValue', an, 'A'); link(cl, 'ReturnValue', an, 'B'); br = place(ge.add_branch_node()); link(an, 'ReturnValue', br, 'Condition'); chain(all_, br)
s1 = setv('DeadBase', near); s0 = setv('DeadStep', lit=0.0); PL.try_create_connection(BEL.find_output_pin(br, 'then'), BEL.find_execute_pin(s1)); chain(s1, s0); seq = [s0]
for _ in range(8):
    d_ = call(KS + 'Delay', Duration=0.4); c_ = call(CLS + ':PodBurst'); seq += [d_, c_]
chain(*seq)
# PodBurst: one burst on the base, one step darker
base_l = call(AC + 'K2_GetActorLocation'); link(get('DeadBase'), 'DeadBase', base_l, 'self'); sca = call(AC + 'GetActorScale3D'); link(get('DeadBase'), 'DeadBase', sca, 'self'); bv = call(M + 'BreakVector'); link(sca, 'ReturnValue', bv, 'InVec')
rr = call(M + 'RandomFloatInRange', Min=3300.0, Max=5400.0); rs = call(M + 'Multiply_DoubleDouble'); link(rr, 'ReturnValue', rs, 'A'); link(bv, 'X', rs, 'B'); ra = call(M + 'RandomFloatInRange', Min=0.0, Max=360.0); mr = call(M + 'MakeRotator'); link(ra, 'ReturnValue', mr, 'Yaw'); fw = call(M + 'GetForwardVector'); link(mr, 'ReturnValue', fw, 'InRot'); of = call(M + 'Multiply_VectorFloat'); link(fw, 'ReturnValue', of, 'A'); link(rs, 'ReturnValue', of, 'B')
pt = call(M + 'Add_VectorVector'); link(base_l, 'ReturnValue', pt, 'A'); link(of, 'ReturnValue', pt, 'B'); up = call(M + 'Add_VectorVector', B='0.000000,0.000000,250.000000'); link(pt, 'ReturnValue', up, 'A')
xf = call(M + 'MakeTransform', Scale='2.000000,2.000000,2.000000'); link(up, 'ReturnValue', xf, 'Location'); bg = call(GS + 'BeginDeferredActorSpawnFromClass', CollisionHandlingOverride='AlwaysSpawn'); PL.set_pin_value(ip(bg, 'ActorClass'), unreal.load_asset(BURST).generated_class().get_path_name()); link(xf, 'ReturnValue', bg, 'SpawnTransform'); fs = call(GS + 'FinishSpawningActor'); link(bg, 'ReturnValue', fs, 'Actor'); link(xf, 'ReturnValue', fs, 'SpawnTransform')
snd = call(GS + 'PlaySoundAtLocation'); PL.set_pin_value(ip(snd, 'Sound'), unreal.load_asset(SPLAT).get_path_name()); link(up, 'ReturnValue', snd, 'Location'); rp = call(M + 'RandomFloatInRange', Min=0.8, Max=1.2); link(rp, 'ReturnValue', snd, 'PitchMultiplier')
inc = call(M + 'Add_DoubleDouble', B=0.125); link(get('DeadStep'), 'DeadStep', inc, 'A'); st = setv('DeadStep', inc); gc = call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.StaticMeshComponent'); link(get('DeadBase'), 'DeadBase', gc, 'self'); ca = place(ge.create_node_from_name('Utilities|Casting|CastToStaticMeshComponent', unreal.Vector2D(0, YMIN), [])); link(gc, 'ReturnValue', ca, 'Object')
pm = call('/Script/Engine.MeshComponent:SetScalarParameterValueOnMaterials', ParameterName='Dead'); link(ca, 'AsStatic Mesh Component', pm, 'self'); link(get('DeadStep'), 'DeadStep', pm, 'ParameterValue'); chain(ev2, bg, fs, snd, st, ca, pm)
# fire it in the death chain, right before the Delay
src = list(PL.list_connected_pins(BEL.find_execute_pin(n['CX_163']))); PL.break_pin_links(BEL.find_execute_pin(n['CX_163'])); fire = call(CLS + ':BaseDeath')
for p in src:
    if not PL.try_create_connection(p, BEL.find_execute_pin(fire)): raise SystemExit('DEATH551 exec failed into BaseDeath')
chain(fire, n['CX_163']); say('delay was', PL.get_pin_value(ip(n['CX_163'], 'Duration'))); PL.set_pin_value(ip(n['CX_163'], 'Duration'), '4.4'); ok = BEL.compile_blueprint(bp); now = sorted(x.get_name() for x in ge.list_nodes_with_errors()); say('compile', ok, 'errors before', before, 'after', now, 'links in', len(src))
if set(now) - set(before): raise SystemExit('DEATH551 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(now) - set(before)))
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN])); say('DONE')

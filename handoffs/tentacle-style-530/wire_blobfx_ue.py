# #533 blob trail + landing splat (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste, no Niagara. Run after wire_spit_ue.py.
#   py wire_blobfx_ue.py --dry-run | --apply | --revert
# Only thrown blobs are affected (spawn scale 3, tested as VSize(actor scale) > 2.5); every other blob behaves as before.
# TRAIL: every 0.1 s in flight (speed > 500 cm/s) the blob sheds BP_BlobDrip_533: a wet streak with no physics and no collision, falls, shrinks, gone in 0.8 s.
# LANDING: on the blob's existing landing branch: the game's BP_BloodBurst (chunks, x3) + a 5.2 m self-drying splat (MI_BloodDecal_337: random shape, wet to dry in 30 s).
# New nodes sit at y >= 12000 in BP_JellyBlob. --revert removes them and NextDripT and relinks. The drip asset stays, unused. STOPS if a node name is missing.
import os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
G = '/Game/CastleDefender/Gameplay/Tentacle/Jelly/'; PATH = G + 'BP_JellyBlob'; V = '/Game/CastleDefender/VFX/'
DIR = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530'; DRIP = DIR + '/BP_BlobDrip_533'
BURST = V + 'BP_BloodBurst'; DECAL = V + 'Blood337/MI_BloodDecal_337'; WET = V + 'Blood337/M_BloodDroplet_Mesh_337'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'
YMIN = 12000
def say(*a): print('BLOBFX533', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y >= YMIN]
missing = [k for k in ('CX_11', 'CX_12', 'CX_24', 'CX_26', 'CX_18') if k not in nodes]
if missing: raise SystemExit('BLOBFX533 nodes missing: %s; BP_JellyBlob changed, send i5 a fresh export' % missing)
def errs(g=None): return sorted(n.get_name() for n in (g or ge).list_nodes_with_errors())
if '--revert' in A:
    if not mine: say('nothing to revert')
    else:
        ge.remove_nodes(mine); n = nodes
        say('relink', PL.try_create_connection(BEL.find_then_pin(n['CX_11']), BEL.find_execute_pin(n['CX_12'])), PL.try_create_connection(BEL.find_then_pin(n['CX_24']), BEL.find_execute_pin(n['CX_26'])))
        ge.remove_member_variable('NextDripT'); say('compile', BEL.compile_blueprint(bp), 'errors', errs()); say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'removed', len(mine), 'nodes')
    raise SystemExit(0)
if mine: say('already wired,', len(mine), 'nodes'); raise SystemExit(0)
for p in (BURST, DECAL, WET):
    if not E.does_asset_exist(p): raise SystemExit('BLOBFX533 missing asset ' + p)
if '--apply' not in A:
    say('WOULD make', DRIP, '(exists: %s)' % E.does_asset_exist(DRIP)); say('WOULD add NextDripT and rewire CX_11.then (trail) and CX_24.then (landing) in BP_JellyBlob'); raise SystemExit(0)
def builder(g, ymin):
    pos = [0, ymin]
    def place(n):
        BEL.set_node_pos(n, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300
        if pos[0] > 6000: pos[0] = 0; pos[1] += 300
        return n
    def call(path, **lit):
        n = place(g.add_call_function_node(path))
        for k, v in lit.items(): PL.set_pin_value(BEL.find_input_pin(n, k), str(v))
        return n
    return place, call
def link(a, pa, b, pb):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), BEL.find_input_pin(b, pb)): raise SystemExit('BLOBFX533 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def chain(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('BLOBFX533 exec failed %s -> %s' % (a.get_name(), b.get_name()))
def out_exec(a, pa, b):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), BEL.find_execute_pin(b)): raise SystemExit('BLOBFX533 exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
# ---------- the drip actor
if not E.does_asset_exist(DRIP):
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    d = unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_BlobDrip_533', DIR, unreal.Blueprint, f)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    root = sds.k2_gather_subobject_data_for_blueprint(d)[0]
    h1, w1 = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=d))
    h2, w2 = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.ProjectileMovementComponent, blueprint_context=d))
    sm = lib.get_object(sds.k2_find_subobject_data_from_handle(h1)); pm = lib.get_object(sds.k2_find_subobject_data_from_handle(h2))
    sm.set_editor_property('static_mesh', unreal.load_asset('/Engine/BasicShapes/Sphere')); sm.set_material(0, unreal.load_asset(WET))
    sm.set_editor_property('relative_scale3d', unreal.Vector(0.75, 0.26, 0.26)); sm.set_collision_profile_name('NoCollision'); sm.set_editor_property('cast_shadow', False)
    pm.set_editor_property('rotation_follows_velocity', True); pm.set_editor_property('projectile_gravity_scale', 1.0)
    g2 = GE.get_graph_editor(BEL.find_event_graph(d)); place2, call2 = builder(g2, 0)
    bp_ev = g2.find_event_node('ReceiveBeginPlay') if hasattr(g2, 'find_event_node') else None
    tk_ev = g2.find_event_node('ReceiveTick') if hasattr(g2, 'find_event_node') else None
    if not bp_ev or not tk_ev: raise SystemExit('BLOBFX533 drip graph has no BeginPlay / Tick event node')
    life = call2(AC + 'SetLifeSpan', InLifespan=0.8); chain(bp_ev, life)
    age = call2(AC + 'GetGameTimeSinceCreation'); fr = call2(M + 'Divide_DoubleDouble', B=0.9); link(age, 'ReturnValue', fr, 'A')
    om = call2(M + 'Subtract_DoubleDouble', A=1.0); link(fr, 'ReturnValue', om, 'B')
    sc = call2(M + 'Multiply_VectorFloat', A='1.000000,1.000000,1.000000'); link(om, 'ReturnValue', sc, 'B')
    st = call2(AC + 'SetActorScale3D'); link(sc, 'ReturnValue', st, 'NewScale3D'); chain(tk_ev, st)
    say('drip compile', BEL.compile_blueprint(d), 'errors', errs(g2)); say('drip saved', E.save_asset(DRIP, only_if_is_dirty=False))
# ---------- the blob
BEL.compile_blueprint(bp); base = errs()
BEL.add_member_variable(bp, 'NextDripT', BEL.get_basic_type_by_name('real'))
place, call = builder(ge, YMIN); n = nodes
def get(v): return place(ge.add_get_member_variable_node(v))
def thrown():
    s = call(AC + 'GetActorScale3D'); l = call(M + 'VSize'); link(s, 'ReturnValue', l, 'A'); g = call(M + 'Greater_DoubleDouble', B=2.5); link(l, 'ReturnValue', g, 'A'); return g
def spawn(path, scale):
    loc = call(AC + 'K2_GetActorLocation'); x = call(M + 'MakeTransform', Scale='%s,%s,%s' % (scale, scale, scale)); link(loc, 'ReturnValue', x, 'Location')
    b = call(GS + 'BeginDeferredActorSpawnFromClass', CollisionHandlingOverride='AlwaysSpawn'); PL.set_pin_value(BEL.find_input_pin(b, 'ActorClass'), path); link(x, 'ReturnValue', b, 'SpawnTransform')
    e = call(GS + 'FinishSpawningActor'); link(b, 'ReturnValue', e, 'Actor'); link(x, 'ReturnValue', e, 'SpawnTransform'); chain(b, e); return b, e
PL.break_pin_links(BEL.find_then_pin(n['CX_11'])); PL.break_pin_links(BEL.find_then_pin(n['CX_24']))
# trail, at the top of Tick
sp = call(M + 'VSize'); link(n['CX_18'], 'Velocity', sp, 'A'); fast = call(M + 'Greater_DoubleDouble', B=500.0); link(sp, 'ReturnValue', fast, 'A')
now = call(GS + 'GetTimeSeconds'); due = call(M + 'Greater_DoubleDouble'); link(now, 'ReturnValue', due, 'A'); link(get('NextDripT'), 'NextDripT', due, 'B')
a1 = call(M + 'BooleanAND'); link(fast, 'ReturnValue', a1, 'A'); link(due, 'ReturnValue', a1, 'B'); a2 = call(M + 'BooleanAND'); link(a1, 'ReturnValue', a2, 'A'); link(thrown(), 'ReturnValue', a2, 'B')
br = place(ge.add_branch_node()); link(a2, 'ReturnValue', br, 'Condition'); chain(n['CX_11'], br); out_exec(br, 'else', n['CX_12'])
nx = call(M + 'Add_DoubleDouble', B=0.1); link(call(GS + 'GetTimeSeconds'), 'ReturnValue', nx, 'A')
sn = place(ge.add_set_member_variable_node('NextDripT')); link(nx, 'ReturnValue', sn, 'NextDripT'); out_exec(br, 'then', sn)
b1, e1 = spawn(unreal.load_asset(DRIP).generated_class().get_path_name(), 1.0); chain(sn, b1); chain(e1, n['CX_12'])
# landing, on the existing landing branch, before LandT is written
br2 = place(ge.add_branch_node()); link(thrown(), 'ReturnValue', br2, 'Condition'); chain(n['CX_24'], br2); out_exec(br2, 'else', n['CX_26'])
b2, e2 = spawn(unreal.load_asset(BURST).generated_class().get_path_name(), 3.0); out_exec(br2, 'then', b2)
loc = call(AC + 'K2_GetActorLocation')
dc = call(GS + 'SpawnDecalAtLocation', DecalSize='150.000000,260.000000,260.000000', Rotation='-90.000000,0.000000,0.000000', LifeSpan=33.0); PL.set_pin_value(BEL.find_input_pin(dc, 'DecalMaterial'), unreal.load_asset(DECAL).get_path_name()); link(loc, 'ReturnValue', dc, 'Location'); chain(e2, dc)
mi = call('/Script/Engine.DecalComponent:CreateDynamicMaterialInstance'); link(dc, 'ReturnValue', mi, 'self'); chain(dc, mi)
ri = call(M + 'RandomIntegerInRange', Min=0, Max=7); i2 = call(M + 'Conv_IntToDouble'); link(ri, 'ReturnValue', i2, 'InInt')
s1 = call('/Script/Engine.MaterialInstanceDynamic:SetScalarParameterValue', ParameterName='Index'); link(mi, 'ReturnValue', s1, 'self'); link(i2, 'ReturnValue', s1, 'Value')
s2 = call('/Script/Engine.MaterialInstanceDynamic:SetScalarParameterValue', ParameterName='SpawnT'); link(mi, 'ReturnValue', s2, 'self'); link(call(GS + 'GetTimeSeconds'), 'ReturnValue', s2, 'Value')
chain(mi, s1, s2); chain(s2, n['CX_26'])
ok = BEL.compile_blueprint(bp); say('compile', ok, 'errors before', base, 'after', errs())
if set(errs()) - set(base): raise SystemExit('BLOBFX533 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(errs()) - set(base)))
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]))

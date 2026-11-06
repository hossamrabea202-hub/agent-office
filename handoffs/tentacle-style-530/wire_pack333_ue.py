# #333 scorpion strike on a packed soldier formation (adjustedfilm, 2026-11-06), BPC_TentacleStrike. Editor idle, not in Play. No paste. Run after #532.
#   py wire_pack333_ue.py --dry-run | --apply | --revert
# TryStrike: at most every 1.5 s, looks for a soldier in StrikeRange with PackMin (5) soldiers within 4 m, counting itself, and a zombie within 10 m (= fighting).
#   Found: a hidden TargetPoint is locked on that spot and becomes the strike's target, so scattering during the 3.8 s wind-up dodges it. Next pack strike 20 s later.
#   Not found: the old cannon logic runs, unchanged. The hero is never targeted or hurt. Soldiers include crossbowmen and commanders (children of BP_SoldierSword).
# Hit: every soldier within 4.5 m takes StrikeDamage at the centre falling to 35 % at the edge (commanders half) and, once ragdolled by his own death logic, the cannon's
#   radial impulse (900 cm, 1300, velocity change). Plus the cannon's camera shake, smoke, and the strike's existing HitFX and HitSound.
# New nodes sit at y >= 13000. --revert removes them and the new variables and relinks. The script STOPS if a node name is missing.
import os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
PATH = '/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleStrike'; K = '/Game/CastleDefender/Characters/Knight/'; Z = '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie'
SWORD, CMD = K + 'BP_SoldierSword', K + 'BP_SoldierCommander'; SHAKE = '/Game/CastleDefender/Gameplay/Cannon/BP_CannonShake_Impact'; SMOKE = '/Game/CastleDefender/AssetPacks/StarterContent/Particles/P_Smoke'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'
LOOP = '/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoopWithBreak'; LOOP2 = '/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop'
YMIN = 13000
def say(*a): print('PACK333', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
n = {x.get_name(): x for x in ge.list_all_nodes()}
mine = [x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]
missing = [k for k in ('K2Node_IfThenElse_2', 'CX_47', 'K2Node_CallArrayFunction_1', 'K2Node_VariableSet_23', 'K2Node_CallFunction_74', 'K2Node_VariableGet_3') if k not in n]
if missing: raise SystemExit('PACK333 nodes missing: %s; BPC_TentacleStrike changed, send i5 a fresh export' % missing)
V, D, I, B = BEL.get_struct_type(unreal.Vector.static_struct()), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('bool')
VARS = [('NextPackT', D), ('PackN', I), ('PackFound', B), ('PackSpot', V), ('PackStrike', B), ('PackMin', I)]
def errs(): return sorted(x.get_name() for x in ge.list_nodes_with_errors())
if '--revert' in A:
    if not mine: say('nothing to revert')
    else:
        ge.remove_nodes(mine)
        say('relink', PL.try_create_connection(BEL.find_then_pin(n['K2Node_IfThenElse_2']), BEL.find_execute_pin(n['CX_47'])), PL.try_create_connection(BEL.find_then_pin(n['K2Node_VariableSet_23']), BEL.find_execute_pin(n['K2Node_CallFunction_74'])))
        for v, _ in VARS: ge.remove_member_variable(v)
        say('compile', BEL.compile_blueprint(bp), 'errors', errs()); say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'removed', len(mine), 'nodes')
    raise SystemExit(0)
if mine: say('already wired,', len(mine), 'nodes'); raise SystemExit(0)
for p in (SWORD, CMD, Z, SHAKE, SMOKE):
    if not E.does_asset_exist(p): raise SystemExit('PACK333 missing asset ' + p)
if '--apply' not in A:
    say('WOULD add', len(VARS), 'variables, the pack search on K2Node_IfThenElse_2.then and the blast on K2Node_VariableSet_23.then'); raise SystemExit(0)
BEL.compile_blueprint(bp); before = errs()
for v, t in VARS: BEL.add_member_variable(bp, v, t)
BEL.compile_blueprint(bp)
pos = [0, YMIN]
def place(x):
    BEL.set_node_pos(x, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300
    if pos[0] > 9000: pos[0] = 0; pos[1] += 300
    return x
def pin_in(x, p):
    r = BEL.find_input_pin(x, p)
    if not r: raise SystemExit('PACK333 no input pin %s.%s' % (x.get_name(), p))
    return r
def pin_out(x, p):
    r = BEL.find_output_pin(x, p)
    if not r: raise SystemExit('PACK333 no output pin %s.%s' % (x.get_name(), p))
    return r
def call(path, **lit):
    x = place(ge.add_call_function_node(path))
    for k, v in lit.items(): PL.set_pin_value(pin_in(x, k), str(v))
    return x
def link(a, pa, b, pb):
    if not PL.try_create_connection(pin_out(a, pa), pin_in(b, pb)): raise SystemExit('PACK333 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def get(v, cls=''): return place(ge.add_get_member_variable_node(v, cls))
def setv(v, src=None, pa='ReturnValue', lit=None):
    x = place(ge.add_set_member_variable_node(v))
    if src is not None: link(src, pa, x, v)
    if lit is not None: PL.set_pin_value(pin_in(x, v), str(lit))
    return x
def chain(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('PACK333 exec failed %s -> %s' % (a.get_name(), b.get_name()))
def ex(a, pa, b, pb=None):
    q = pin_in(b, pb) if pb else BEL.find_execute_pin(b)
    if not PL.try_create_connection(pin_out(a, pa), q): raise SystemExit('PACK333 exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
def branch(c, pc='ReturnValue'):
    x = place(ge.add_branch_node()); link(c, pc, x, 'Condition'); return x
def loc(src, pa): x = call(AC + 'K2_GetActorLocation'); link(src, pa, x, 'self'); return x
def dist(a, pa, b, pb):
    x = call(M + 'Vector_Distance'); link(a, pa, x, 'V1'); link(b, pb, x, 'V2'); return x
def less(a, pa, val, pv='ReturnValue'):
    x = call(M + 'Less_DoubleDouble'); link(a, pa, x, 'A')
    if isinstance(val, (int, float)): PL.set_pin_value(pin_in(x, 'B'), str(val))
    else: link(val, pv, x, 'B')
    return x
def now(): return call(GS + 'GetTimeSeconds')
def add_now(s): x = call(M + 'Add_DoubleDouble', B=s); link(now(), 'ReturnValue', x, 'A'); return x
def soldiers():
    x = call(GS + 'GetAllActorsOfClass'); PL.set_pin_value(pin_in(x, 'ActorClass'), unreal.load_asset(SWORD).generated_class().get_path_name()); return x
def base():
    s = call('/Script/Engine.SceneComponent:GetSocketLocation', InSocketName='seg_00'); link(get('Mesh'), 'Mesh', s, 'self'); return s
# ---------- the search, in front of the cannon logic
g = call(M + 'Greater_DoubleDouble'); link(now(), 'ReturnValue', g, 'A'); link(get('NextPackT'), 'NextPackT', g, 'B'); br0 = branch(g)
PL.break_pin_links(BEL.find_then_pin(n['K2Node_IfThenElse_2'])); chain(n['K2Node_IfThenElse_2'], br0); ex(br0, 'else', n['CX_47'])
s0 = setv('NextPackT', add_now(1.5)); s1 = setv('PackFound', lit='false'); all1 = soldiers(); ex(br0, 'then', s0); chain(s0, s1, all1)
outer = place(ge.add_macro_node(LOOP)); link(all1, 'OutActors', outer, 'Array'); ex_all = BEL.find_then_pin(all1)
if not PL.try_create_connection(ex_all, pin_in(outer, 'Exec')): raise SystemExit('PACK333 exec failed into the outer loop')
in_range = less(dist(loc(outer, 'Array Element'), 'ReturnValue', base(), 'ReturnValue'), 'ReturnValue', get('StrikeRange'), 'StrikeRange'); br1 = branch(in_range); ex(outer, 'LoopBody', br1)
s2 = setv('PackN', lit=0); ex(br1, 'then', s2); all2 = soldiers(); chain(s2, all2)
inner = place(ge.add_macro_node(LOOP2)); link(all2, 'OutActors', inner, 'Array')
if not PL.try_create_connection(BEL.find_then_pin(all2), pin_in(inner, 'Exec')): raise SystemExit('PACK333 exec failed into the inner loop')
near = less(dist(loc(outer, 'Array Element'), 'ReturnValue', loc(inner, 'Array Element'), 'ReturnValue'), 'ReturnValue', 400.0); br2 = branch(near); ex(inner, 'LoopBody', br2)
inc = call(M + 'Add_IntInt', B=1); link(get('PackN'), 'PackN', inc, 'A'); s3 = setv('PackN', inc); ex(br2, 'then', s3)
ge_ = call(M + 'GreaterEqual_IntInt'); link(get('PackN'), 'PackN', ge_, 'A'); link(get('PackMin'), 'PackMin', ge_, 'B'); br3 = branch(ge_); ex(inner, 'Completed', br3)
s4 = setv('PackSpot', loc(outer, 'Array Element')); s5 = setv('PackFound', lit='true'); ex(br3, 'then', s4); chain(s4, s5)
if not PL.try_create_connection(BEL.find_then_pin(s5), pin_in(outer, 'Break')): raise SystemExit('PACK333 exec failed into Break')
# ---------- found and fighting? lock the hidden target and join the strike after the cannon range test
br4 = branch(get('PackFound'), 'PackFound'); ex(outer, 'Completed', br4); ex(br4, 'else', n['CX_47'])
zs = call(GS + 'GetAllActorsOfClass'); PL.set_pin_value(pin_in(zs, 'ActorClass'), unreal.load_asset(Z).generated_class().get_path_name()); ex(br4, 'then', zs)
fn = call(GS + 'FindNearestActor'); link(get('PackSpot'), 'PackSpot', fn, 'Origin'); link(zs, 'OutActors', fn, 'ActorsToCheck')
iv = call(KS + 'IsValid'); link(fn, 'ReturnValue', iv, 'Object'); cl = less(fn, 'Distance', 1000.0); a1 = call(M + 'BooleanAND'); link(iv, 'ReturnValue', a1, 'A'); link(cl, 'ReturnValue', a1, 'B')
br5 = branch(a1); chain(zs, br5); ex(br5, 'else', n['CX_47'])
xf = call(M + 'MakeTransform'); link(get('PackSpot'), 'PackSpot', xf, 'Location')
sp = call(GS + 'BeginDeferredActorSpawnFromClass', CollisionHandlingOverride='AlwaysSpawn'); PL.set_pin_value(pin_in(sp, 'ActorClass'), '/Script/Engine.TargetPoint'); link(xf, 'ReturnValue', sp, 'SpawnTransform')
fs = call(GS + 'FinishSpawningActor'); link(sp, 'ReturnValue', fs, 'Actor'); link(xf, 'ReturnValue', fs, 'SpawnTransform')
ls = call(AC + 'SetLifeSpan', InLifespan=15.0); link(fs, 'ReturnValue', ls, 'self'); s6 = setv('TargetCannon', fs); s7 = setv('PackStrike', lit='true'); s8 = setv('NextPackT', add_now(20.0))
ex(br5, 'then', sp); chain(sp, fs, ls, s6, s7, s8, n['K2Node_CallArrayFunction_1'])
# ---------- the blast, at the moment of the hit, then the strike's own damage, FX and sound
PL.break_pin_links(BEL.find_then_pin(n['K2Node_VariableSet_23'])); br6 = branch(get('PackStrike'), 'PackStrike'); chain(n['K2Node_VariableSet_23'], br6); ex(br6, 'else', n['K2Node_CallFunction_74'])
s9 = setv('PackStrike', lit='false'); s10 = setv('PackSpot', loc(get('TargetCannon'), 'TargetCannon')); all3 = soldiers(); ex(br6, 'then', s9); chain(s9, s10, all3)
each = place(ge.add_macro_node(LOOP2)); link(all3, 'OutActors', each, 'Array')
if not PL.try_create_connection(BEL.find_then_pin(all3), pin_in(each, 'Exec')): raise SystemExit('PACK333 exec failed into the blast loop')
d3 = dist(loc(each, 'Array Element'), 'ReturnValue', get('PackSpot'), 'PackSpot'); br7 = branch(less(d3, 'ReturnValue', 450.0)); ex(each, 'LoopBody', br7)
fr = call(M + 'Divide_DoubleDouble', B=450.0); link(d3, 'ReturnValue', fr, 'A'); lp = call(M + 'Lerp', A=1.0, B=0.35); link(fr, 'ReturnValue', lp, 'Alpha')
cc = call('/Script/Engine.GameplayStatics:GetObjectClass'); link(each, 'Array Element', cc, 'Object'); ch = call('/Script/Engine.KismetMathLibrary:ClassIsChildOf'); link(cc, 'ReturnValue', ch, 'TestClass'); PL.set_pin_value(pin_in(ch, 'ParentClass'), unreal.load_asset(CMD).generated_class().get_path_name())
sel = call(M + 'SelectFloat', A=0.5, B=1.0); link(ch, 'ReturnValue', sel, 'bPickA')
m1 = call(M + 'Multiply_DoubleDouble'); link(get('StrikeDamage'), 'StrikeDamage', m1, 'A'); link(lp, 'ReturnValue', m1, 'B'); m2 = call(M + 'Multiply_DoubleDouble'); link(m1, 'ReturnValue', m2, 'A'); link(sel, 'ReturnValue', m2, 'B')
ow = call('/Script/Engine.ActorComponent:GetOwner')
ad = call(GS + 'ApplyDamage'); link(each, 'Array Element', ad, 'DamagedActor'); link(m2, 'ReturnValue', ad, 'BaseDamage'); link(ow, 'ReturnValue', ad, 'DamageCauser'); ex(br7, 'then', ad)
ms = get('Mesh', '/Script/Engine.Character'); link(each, 'Array Element', ms, 'self')
imp = call('/Script/Engine.PrimitiveComponent:AddRadialImpulse', Radius=900.0, Strength=1300.0, Falloff='RIF_Constant', bVelChange='true'); link(ms, 'Mesh', imp, 'self'); link(get('PackSpot'), 'PackSpot', imp, 'Origin'); chain(ad, imp)
shk = call(GS + 'PlayWorldCameraShake', InnerRadius=1500.0, OuterRadius=9000.0); PL.set_pin_value(pin_in(shk, 'Shake'), unreal.load_asset(SHAKE).generated_class().get_path_name()); link(get('PackSpot'), 'PackSpot', shk, 'Epicenter'); ex(each, 'Completed', shk)
smk = call(GS + 'SpawnEmitterAtLocation', Scale='6.000000,6.000000,6.000000'); PL.set_pin_value(pin_in(smk, 'EmitterTemplate'), unreal.load_asset(SMOKE).get_path_name()); link(get('PackSpot'), 'PackSpot', smk, 'Location'); chain(shk, smk, n['K2Node_CallFunction_74'])
ok = BEL.compile_blueprint(bp); say('compile', ok, 'errors before', before, 'after', errs())
if set(errs()) - set(before): raise SystemExit('PACK333 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(errs()) - set(before)))
unreal.get_default_object(bp.generated_class()).set_editor_property('PackMin', 5)
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]))

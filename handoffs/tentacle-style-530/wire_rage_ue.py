# Enraged behaviour (owner, after #533): a tentacle under attack does not idle (adjustedfilm, 2026-11-06), BPC_TentacleSpit. Editor idle, not in Play. Run after wire_spit_ue.py.
#   py wire_rage_ue.py --dry-run | --apply | --revert
# Any hit: enraged for 8 s (each new hit restarts the 8 s). While enraged, whenever no other montage plays, it loops AM_Tentacle_Enraged at a random 0.85-1.15 rate, or
#   AM_Tentacle_EnragedHurt below 35 % health; the head leans at the attacker by IK (alpha 0.3); it spits faster (every 2 hits, 3 s cooldown).
# Hits stop for 8 s: the rage clip blends out over 1 s, IK eases off, spit timing returns to normal. Below 35 % health it then plays AM_Tentacle_Wounded, otherwise the hunting idle.
# Reactions, spit, catapult, strike and the death clip all keep priority. Nothing plays at Health <= 0.
# New nodes sit at y >= 14000. --revert removes them and the new variables and relinks. The script STOPS if a node name is missing.
import os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
G = '/Game/CastleDefender/Gameplay/Tentacle/'; PATH = G + 'BPC_TentacleSpit'; VITALS = G + 'BP_TentacleVitals'; D_ = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530/'
AM_R, AM_H, AM_W = D_ + 'AM_Tentacle_Enraged', D_ + 'AM_Tentacle_EnragedHurt', D_ + 'AM_Tentacle_Wounded'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; AI = '/Script/Engine.AnimInstance:'
LOOP = '/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop'; YMIN = 14000
def say(*a): print('RAGE', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
n = {x.get_name(): x for x in ge.list_all_nodes()}
mine = [x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]
missing = [k for k in ('OnHit', 'IsBall', 'Tick') if k not in n]
if missing: raise SystemExit('RAGE nodes missing: %s; BPC_TentacleSpit changed, send i5 a fresh export' % missing)
if not [x for x in ge.list_all_nodes() if 11000 <= BEL.get_node_pos(x).y < YMIN]: raise SystemExit('RAGE run wire_spit_ue.py --apply first')
def next_of(node):
    r = PL.list_connected_pins(BEL.find_then_pin(node)); return list(r)
def owner_of(pin): return PL.get_owning_node(pin)
tick_next = next_of(n['Tick'])
if len(tick_next) != 1: raise SystemExit('RAGE Tick.then has %d links, expected 1' % len(tick_next))
br_t = owner_of(tick_next[0])
VT = unreal.load_asset(VITALS).generated_class()
VARS = [('RageUntil', BEL.get_basic_type_by_name('real')), ('RageAim', BEL.get_struct_type(unreal.Vector.static_struct())), ('RageIK', BEL.get_basic_type_by_name('bool')), ('RageLowHP', BEL.get_basic_type_by_name('real')), ('RageMaxHP', BEL.get_basic_type_by_name('real')), ('VitalsT', BEL.get_object_reference_type(VT))]
def errs(): return sorted(x.get_name() for x in ge.list_nodes_with_errors())
if '--revert' in A:
    if not mine: say('nothing to revert'); raise SystemExit(0)
    # the first-node links tell where the two chains continue: mine carry the old targets on their last exec
    tick_after = next(q for x in mine for q in (PL.list_connected_pins(BEL.find_then_pin(x)) if BEL.find_then_pin(x) else []) if owner_of(q).get_name() not in [m.get_name() for m in mine] and owner_of(q).get_name() != 'IsBall')
    cond = BEL.find_input_pin(owner_of(tick_after), 'Condition'); orn = owner_of(list(PL.list_connected_pins(cond))[0]); src = list(PL.list_connected_pins(BEL.find_input_pin(orn, 'A')))[0]
    ge.remove_nodes(mine)
    say('relink', PL.try_create_connection(BEL.find_then_pin(n['Tick']), BEL.find_execute_pin(owner_of(tick_after))), PL.try_create_connection(BEL.find_then_pin(n['OnHit']), BEL.find_execute_pin(n['IsBall'])), PL.try_create_connection(src, cond))
    for v, _ in VARS: ge.remove_member_variable(v)
    say('compile', BEL.compile_blueprint(bp), 'errors', errs()); say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'removed', len(mine), 'nodes'); raise SystemExit(0)
if mine: say('already wired,', len(mine), 'nodes'); raise SystemExit(0)
for p in (AM_R, AM_H, AM_W):
    if not E.does_asset_exist(p): raise SystemExit('RAGE missing %s (run import_spit_ue.py)' % p)
if '--apply' not in A: say('WOULD add', len(VARS), 'variables, the hit block on OnHit.then and the rage block on Tick.then'); raise SystemExit(0)
BEL.compile_blueprint(bp); before = errs(); cdo0 = unreal.get_default_object(bp.generated_class()); EV0, CD0 = cdo0.get_editor_property('SpitEvery'), cdo0.get_editor_property('SpitCooldown')
say('spit defaults', EV0, CD0)
for v, t in VARS: BEL.add_member_variable(bp, v, t)
BEL.compile_blueprint(bp)
pos = [0, YMIN]
def place(x):
    BEL.set_node_pos(x, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300
    if pos[0] > 9000: pos[0] = 0; pos[1] += 300
    return x
def pin_in(x, p):
    r = BEL.find_input_pin(x, p)
    if not r: raise SystemExit('RAGE no input pin %s.%s' % (x.get_name(), p))
    return r
def pin_out(x, p):
    r = BEL.find_output_pin(x, p)
    if not r: raise SystemExit('RAGE no output pin %s.%s' % (x.get_name(), p))
    return r
def call(path, **lit):
    x = place(ge.add_call_function_node(path))
    for k, v in lit.items(): PL.set_pin_value(pin_in(x, k), str(v))
    return x
def link(a, pa, b, pb):
    if not PL.try_create_connection(pin_out(a, pa), pin_in(b, pb)): raise SystemExit('RAGE link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def get(v, cls=''): return place(ge.add_get_member_variable_node(v, cls))
def setv(v, src=None, pa='ReturnValue', lit=None):
    x = place(ge.add_set_member_variable_node(v))
    if src is not None: link(src, pa, x, v)
    if lit is not None: PL.set_pin_value(pin_in(x, v), str(lit))
    return x
def chain(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('RAGE exec failed %s -> %s' % (a.get_name(), b.get_name()))
def ex(a, pa, b):
    if not PL.try_create_connection(pin_out(a, pa), BEL.find_execute_pin(b)): raise SystemExit('RAGE exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
def branch(c, pc='ReturnValue'):
    x = place(ge.add_branch_node()); link(c, pc, x, 'Condition'); return x
def valid(src, pa): x = call(KS + 'IsValid'); link(src, pa, x, 'Object'); return x
def both(a, b): x = call(M + 'BooleanAND'); link(a, 'ReturnValue', x, 'A'); link(b, 'ReturnValue', x, 'B'); return x
def nt(a, pa='ReturnValue'): x = call(M + 'Not_PreBool'); link(a, pa, x, 'A'); return x
def now(): return call(GS + 'GetTimeSeconds')
def pp(): m = get('MeshT'); x = call('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance'); link(m, 'MeshT', x, 'self'); return x
def health(): v = get('Health', VT.get_path_name()); link(get('VitalsT'), 'VitalsT', v, 'self'); return v
def low(): x = call(M + 'Less_DoubleDouble'); link(health(), 'Health', x, 'A'); link(get('RageLowHP'), 'RageLowHP', x, 'B'); return x
def play(path, rnd):
    p = pp(); x = call(AI + 'Montage_Play'); link(p, 'ReturnValue', x, 'self'); PL.set_pin_value(pin_in(x, 'MontageToPlay'), unreal.load_asset(path).get_path_name())
    if rnd: r = call(M + 'RandomFloatInRange', Min=0.85, Max=1.15); link(r, 'ReturnValue', x, 'InPlayRate')
    return x
def stop(path, t):
    p = pp(); x = call(AI + 'Montage_Stop', InBlendOutTime=t); link(p, 'ReturnValue', x, 'self'); PL.set_pin_value(pin_in(x, 'Montage'), unreal.load_asset(path).get_path_name()); return x
def idle_now(): p = pp(); x = call(AI + 'IsAnyMontagePlaying'); link(p, 'ReturnValue', x, 'self'); return nt(x)
# ---------- every hit
PL.break_pin_links(BEL.find_then_pin(n['OnHit']))
add8 = call(M + 'Add_DoubleDouble', B=8.0); link(now(), 'ReturnValue', add8, 'A'); h1 = setv('RageUntil', add8); chain(n['OnHit'], h1)
br_c = branch(valid(n['OnHit'], 'DamageCauser')); chain(h1, br_c)
cl = call(AC + 'K2_GetActorLocation'); link(n['OnHit'], 'DamageCauser', cl, 'self'); h2 = setv('RageAim', cl); ex(br_c, 'then', h2)
h3 = setv('SpitEvery', lit=2); h4 = setv('SpitCooldown', lit=3.0); chain(h2, h3, h4); ex(br_c, 'else', h3)
o1 = call('/Script/Engine.ActorComponent:GetOwner'); ap = call(AC + 'GetAttachParentActor'); link(o1, 'ReturnValue', ap, 'self')
c1 = call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.SkeletalMeshComponent'); link(ap, 'ReturnValue', c1, 'self')
cast = place(ge.create_node_from_name('Utilities|Casting|CastToSkeletalMeshComponent', unreal.Vector2D(0, YMIN), [])); link(c1, 'ReturnValue', cast, 'Object'); chain(h4, cast); ex(cast, 'CastFailed', n['IsBall'])
h5 = setv('MeshT', cast, 'AsSkeletal Mesh Component'); chain(cast, h5)
br_v = branch(valid(get('VitalsT'), 'VitalsT')); chain(h5, br_v)
all_v = call(GS + 'GetAllActorsOfClass'); PL.set_pin_value(pin_in(all_v, 'ActorClass'), VT.get_path_name()); ex(br_v, 'else', all_v)
fe = place(ge.add_macro_node(LOOP)); link(all_v, 'OutActors', fe, 'Array')
if not PL.try_create_connection(BEL.find_then_pin(all_v), pin_in(fe, 'Exec')): raise SystemExit('RAGE exec failed into the loop')
same = call(M + 'EqualEqual_ObjectObject'); link(fe, 'Array Element', same, 'A'); link(call('/Script/Engine.ActorComponent:GetOwner'), 'ReturnValue', same, 'B'); br_s = branch(same); ex(fe, 'LoopBody', br_s)
h6 = setv('VitalsT', fe, 'Array Element'); ex(br_s, 'then', h6)
# Health is set at runtime, so the 35 % line follows the highest health seen (health + this hit's damage)
br_v2 = branch(valid(get('VitalsT'), 'VitalsT')); ex(fe, 'Completed', br_v2); ex(br_v, 'then', br_v2)
hd_ = call(M + 'Add_DoubleDouble'); link(health(), 'Health', hd_, 'A'); link(n['OnHit'], 'Damage', hd_, 'B')
mx = call(M + 'FMax'); link(get('RageMaxHP'), 'RageMaxHP', mx, 'A'); link(hd_, 'ReturnValue', mx, 'B'); h7 = setv('RageMaxHP', mx); ex(br_v2, 'then', h7)
pc = call(M + 'Multiply_DoubleDouble', B=0.35); link(get('RageMaxHP'), 'RageMaxHP', pc, 'A'); h8 = setv('RageLowHP', pc); chain(h7, h8)
w1 = stop(AM_W, 0.3); chain(h8, w1); ex(br_v2, 'else', w1); chain(w1, n['IsBall'])
# ---------- every tick, in front of the IK block
PL.break_pin_links(BEL.find_then_pin(n['Tick']))
alive = call(M + 'Greater_DoubleDouble', B=0.0); br_a = None
v_ok = both(valid(get('MeshT'), 'MeshT'), valid(get('VitalsT'), 'VitalsT')); br_ok = branch(v_ok); chain(n['Tick'], br_ok); ex(br_ok, 'else', br_t)
link(health(), 'Health', alive, 'A'); br_a = branch(alive); ex(br_ok, 'then', br_a); ex(br_a, 'else', br_t)
lt = call(M + 'Less_DoubleDouble'); link(now(), 'ReturnValue', lt, 'A'); link(get('RageUntil'), 'RageUntil', lt, 'B'); br_r = branch(lt); ex(br_a, 'then', br_r)
# enraged: lean at the attacker unless spit or catapult own the IK, keep the loop running
na = nt(get('CatActive'), 'CatActive'); br_i = branch(na); ex(br_r, 'then', br_i)
hd = call('/Script/Engine.SceneComponent:GetSocketLocation', InSocketName='seg_13'); link(get('MeshT'), 'MeshT', hd, 'self')
to = call(M + 'Subtract_VectorVector'); link(get('RageAim'), 'RageAim', to, 'A'); link(hd, 'ReturnValue', to, 'B'); nr = call(M + 'Normal'); link(to, 'ReturnValue', nr, 'A')
sc = call(M + 'Multiply_VectorFloat', B=2200.0); link(nr, 'ReturnValue', sc, 'A'); ad = call(M + 'Add_VectorVector'); link(hd, 'ReturnValue', ad, 'A'); link(sc, 'ReturnValue', ad, 'B')
t1 = setv('CatAimGoal', ad); t2 = setv('CatAlphaGoal', lit=0.3); t3 = setv('CatSpeed', lit=2.0); t4 = setv('RageIK', lit='true'); ex(br_i, 'then', t1); chain(t1, t2, t3, t4)
br_m = branch(idle_now()); chain(t4, br_m); ex(br_i, 'else', br_m); ex(br_m, 'else', br_t)
br_l = branch(low()); ex(br_m, 'then', br_l); p_h = play(AM_H, True); p_r = play(AM_R, True); ex(br_l, 'then', p_h); ex(br_l, 'else', p_r); chain(p_h, br_t); chain(p_r, br_t)
# calm: stop the rage clips, ease the IK off, spit timing back, then the wounded idle if low
br_k = branch(get('RageIK'), 'RageIK'); ex(br_r, 'else', br_k)
c0 = setv('SpitEvery', lit=EV0); c0b = setv('SpitCooldown', lit=CD0); s_r = stop(AM_R, 1.0); s_h = stop(AM_H, 1.0); ex(br_k, 'then', c0); chain(c0, c0b, s_r, s_h)
br_n = branch(nt(get('CatActive'), 'CatActive')); chain(s_h, br_n)
g1 = setv('CatAlphaGoal', lit=0.0); g2 = setv('CatSpeed', lit=1.5); ex(br_n, 'then', g1); chain(g1, g2)
sm = call(M + 'Less_DoubleDouble', B=0.02); link(get('CatAlpha'), 'CatAlpha', sm, 'A'); br_z = branch(sm); chain(g2, br_z)
p0 = pp(); z0 = call(KS + 'SetDoublePropertyByName', PropertyName='StrikeAlpha', Value=0.0); link(p0, 'ReturnValue', z0, 'Object'); ca0 = setv('CatAlpha', lit=0.0); ri = setv('RageIK', lit='false'); ex(br_z, 'then', z0); chain(z0, ca0, ri)
cond_w = both(idle_now(), low()); br_w = branch(cond_w); chain(ri, br_w); ex(br_z, 'else', br_t); ex(br_n, 'else', br_t); ex(br_k, 'else', br_w); ex(br_w, 'else', br_t)
p_w = play(AM_W, False); ex(br_w, 'then', p_w); chain(p_w, br_t)
# the IK block also runs while RageIK is on
cnd = BEL.find_input_pin(br_t, 'Condition'); old = list(PL.list_connected_pins(cnd))[0]; PL.break_pin_links(cnd); orn = call(M + 'BooleanOR')
if not PL.try_create_connection(old, pin_in(orn, 'A')): raise SystemExit('RAGE could not move the condition')
link(get('RageIK'), 'RageIK', orn, 'B'); link(orn, 'ReturnValue', br_t, 'Condition')
ok = BEL.compile_blueprint(bp); say('compile', ok, 'errors before', before, 'after', errs())
if set(errs()) - set(before): raise SystemExit('RAGE NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(errs()) - set(before)))
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]))

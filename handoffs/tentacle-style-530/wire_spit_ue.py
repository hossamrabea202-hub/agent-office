# #533 tentacle spit + catapult, BPC_TentacleSpit (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste.
#   py wire_spit_ue.py --dry-run | --apply | --revert      (needs import_spit_ue.py first)
# SPIT (non-cannon hits, same SpitEvery / SpitCooldown): the arm rears and spits; 3 blobs, 3x bigger, fly from the head and land 4.5-12 m in FRONT of the
#   hero (+-60 deg of the hero's facing). Before: 2 tiny blobs appeared out of thin air 2.5 m above the ground.
# CATAPULT (cannonball hit, at most once per CatCooldown = 10 s; the #529 reaction plays otherwise): FABRIK leans the arm back AWAY from a random 'Cannon'
#   tagged actor (the castle side) for 2.5 s, whips it over, 3 blobs fly to within 4-25 m of that cannon. Skipped during a strike and during the death clip.
# New nodes sit at y >= 11000. --revert removes them and the new variables and relinks the old graph. The script STOPS if a node name is missing.
import os, sys, unreal
A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
G = '/Game/CastleDefender/Gameplay/Tentacle/'; PATH = A[A.index('--bp') + 1] if '--bp' in A else G + 'BPC_TentacleSpit'
RIG = '/Game/CastleDefender/Environment/Tentacles/Rig/'; AM_SPIT = RIG + 'Style530/AM_Tentacle_Spit'; AM_CAT = RIG + 'Style530/AM_Tentacle_Catapult'; AM_DIE = RIG + 'Polish457/AM_Tentacle_CannonC'
BLOB = G + 'Jelly/BP_JellyBlob.BP_JellyBlob_C'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
YMIN = 11000
def say(*a): print('SPIT533', ' '.join(str(x) for x in a))
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y >= YMIN]
need = ['IsBall', 'SetNext', 'Spawn1', 'SetArmed1', 'Spawn2', 'Xf1', 'Loc1', 'Rot1', 'Tick', 'IfWobble']
missing = [k for k in need if k not in nodes]
if missing: raise SystemExit('SPIT533 nodes missing: %s; BPC_TentacleSpit changed, send i5 a fresh export' % missing)
V = BEL.get_struct_type(unreal.Vector.static_struct()); D = BEL.get_basic_type_by_name('real'); B = BEL.get_basic_type_by_name('bool')
VARS = [('AimCentre', V), ('AimFwd', V), ('AimCone', D), ('AimMin', D), ('AimMax', D), ('ThrowT', V), ('ThrowS', V), ('NextCatT', D), ('CatCooldown', D), ('CatActive', B),
        ('CatAlpha', D), ('CatAlphaGoal', D), ('CatSpeed', D), ('CatAim', V), ('CatAimGoal', V), ('MeshT', BEL.get_object_reference_type(unreal.SkeletalMeshComponent))]
def errs(): return sorted(n.get_name() for n in ge.list_nodes_with_errors())
def pin_in(n, p):
    r = BEL.find_input_pin(n, p)
    if not r: raise SystemExit('SPIT533 no input pin %s.%s' % (n.get_name(), p))
    return r
def pin_out(n, p):
    r = BEL.find_output_pin(n, p)
    if not r: raise SystemExit('SPIT533 no output pin %s.%s' % (n.get_name(), p))
    return r
if '--revert' in A:
    if not mine: say('nothing to revert')
    else:
        ge.remove_nodes(mine); n = nodes
        say('relink', PL.try_create_connection(BEL.find_then_pin(n['SetNext']), BEL.find_execute_pin(n['Spawn1'])), PL.try_create_connection(BEL.find_then_pin(n['SetArmed1']), BEL.find_execute_pin(n['Spawn2'])),
            PL.try_create_connection(BEL.find_then_pin(n['Tick']), BEL.find_execute_pin(n['IfWobble'])),
            PL.try_create_connection(pin_out(n['Loc1'], 'ReturnValue'), pin_in(n['Xf1'], 'Location')), PL.try_create_connection(pin_out(n['Rot1'], 'ReturnValue'), pin_in(n['Xf1'], 'Rotation')))
        PL.set_pin_value(pin_in(n['Xf1'], 'Scale'), '1.000000,1.000000,1.000000')
        for v, _ in VARS: ge.remove_member_variable(v)
        say('compile', BEL.compile_blueprint(bp), 'errors', errs()); say('saved', E.save_asset(PATH, only_if_is_dirty=False)); say('removed', len(mine), 'nodes')
    raise SystemExit(0)
if mine: say('already wired,', len(mine), 'nodes'); raise SystemExit(0)
for m in (AM_SPIT, AM_CAT, AM_DIE):
    if not E.does_asset_exist(m): raise SystemExit('SPIT533 missing %s (run import_spit_ue.py; the cannon set is #529)' % m)
if '--apply' not in A:
    say('WOULD add', len(VARS), 'variables and the spit + catapult chains; WOULD rewire SetNext.then, SetArmed1.then, Tick.then, Xf1 Location/Rotation/Scale'); raise SystemExit(0)
base = errs()
have = [str(v) for v in BEL.list_member_variable_names(bp)]
for v, t in VARS:
    if v not in have: BEL.add_member_variable(bp, v, t)
ev_one = ge.add_custom_event_node('ThrowOne'); ev_burst = ge.add_custom_event_node('ThrowBurst')
BEL.compile_blueprint(bp); CLS = bp.generated_class().get_path_name()
pos = [0, YMIN]
def place(n):
    BEL.set_node_pos(n, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300
    if pos[0] > 9000: pos[0] = 0; pos[1] += 300
    return n
place(ev_one); place(ev_burst)
def call(path, **lit):
    n = place(ge.add_call_function_node(path))
    for k, v in lit.items(): PL.set_pin_value(pin_in(n, k), str(v))
    return n
M = '/Script/Engine.KismetMathLibrary:'; GS = '/Script/Engine.GameplayStatics:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; AI = '/Script/Engine.AnimInstance:'
def get(v, cls=''): return place(ge.add_get_member_variable_node(v, cls))
def link(a, pa, b, pb):
    if not PL.try_create_connection(pin_out(a, pa), pin_in(b, pb)): raise SystemExit('SPIT533 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def setv(v, src=None, pa='ReturnValue', lit=None):
    n = place(ge.add_set_member_variable_node(v))
    if src is not None: link(src, pa if pa else v, n, v)
    if lit is not None: PL.set_pin_value(pin_in(n, v), str(lit))
    return n
def chain(*ns):
    for a, b in zip(ns, ns[1:]):
        if not PL.try_create_connection(BEL.find_then_pin(a), BEL.find_execute_pin(b)): raise SystemExit('SPIT533 exec failed %s -> %s' % (a.get_name(), b.get_name()))
def out_exec(a, pa, b):
    if not PL.try_create_connection(pin_out(a, pa), BEL.find_execute_pin(b)): raise SystemExit('SPIT533 exec failed %s.%s -> %s' % (a.get_name(), pa, b.get_name()))
def delay(s): return call(KS + 'Delay', Duration=s)
def vbin(op, a, b, pa='ReturnValue', pb='ReturnValue'):
    n = call(M + op); link(a, pa, n, 'A'); link(b, pb, n, 'B'); return n
def scale(v, f, pv='ReturnValue', pf='ReturnValue'):
    n = call(M + 'Multiply_VectorFloat'); link(v, pv, n, 'A')
    if isinstance(f, (int, float)): PL.set_pin_value(pin_in(n, 'B'), str(f))
    else: link(f, pf, n, 'B')
    return n
def norm(v, pv='ReturnValue'):
    n = call(M + 'Normal'); link(v, pv, n, 'A'); return n
def sock(name):
    m = get('MeshT'); n = call('/Script/Engine.SceneComponent:GetSocketLocation', InSocketName=name); link(m, 'MeshT', n, 'self'); return n
def pp():
    m = get('MeshT'); n = call('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance'); link(m, 'MeshT', n, 'self'); return n
def branch(cond, pc='ReturnValue'):
    n = place(ge.add_branch_node()); link(cond, pc, n, 'Condition'); return n
def montage(path):
    p = pp(); n = call(AI + 'Montage_Play'); link(p, 'ReturnValue', n, 'self'); PL.set_pin_value(pin_in(n, 'MontageToPlay'), unreal.load_asset(path).get_path_name()); return n
def resolve_mesh():              # owner -> attach parent -> skeletal mesh -> MeshT; returns (first exec node, cast node, set node)
    o = call('/Script/Engine.ActorComponent:GetOwner'); ap = call(AC + 'GetAttachParentActor'); link(o, 'ReturnValue', ap, 'self')
    c = call(AC + 'GetComponentByClass', ComponentClass='/Script/Engine.SkeletalMeshComponent'); link(ap, 'ReturnValue', c, 'self')
    cast = place(ge.create_node_from_name('Utilities|Casting|CastToSkeletalMeshComponent', unreal.Vector2D(0, YMIN), [])); link(c, 'ReturnValue', cast, 'Object')
    s = setv('MeshT', cast, 'AsSkeletal Mesh Component'); chain(cast, s); return cast, s
n = nodes
# ---- ThrowOne: pick the landing point, spawn at the head (reuses Spawn1 and SetArmed1, 3x scale, no rotation), launch on an arc
fwd = get('AimFwd'); cone = get('AimCone'); neg = call(M + 'Multiply_DoubleDouble', B=-1.0); link(cone, 'AimCone', neg, 'A')
rd = call(M + 'RandomFloatInRange'); link(neg, 'ReturnValue', rd, 'Min'); link(get('AimCone'), 'AimCone', rd, 'Max')
rot = call(M + 'RotateAngleAxis', Axis='0.000000,0.000000,1.000000'); link(fwd, 'AimFwd', rot, 'InVect'); link(rd, 'ReturnValue', rot, 'AngleDeg')
dist = call(M + 'RandomFloatInRange'); link(get('AimMin'), 'AimMin', dist, 'Min'); link(get('AimMax'), 'AimMax', dist, 'Max')
target = vbin('Add_VectorVector', get('AimCentre'), scale(rot, dist), 'AimCentre')
set_t = setv('ThrowT', target)
head = sock('seg_13'); to = vbin('Subtract_VectorVector', get('ThrowT'), head, 'ThrowT')
start = vbin('Add_VectorVector', sock('seg_13'), scale(norm(to), 800.0))        # 8 m out of the head, clear of the arm's hitboxes
set_s = setv('ThrowS', start)
PL.break_pin_links(pin_in(n['Xf1'], 'Location')); PL.break_pin_links(pin_in(n['Xf1'], 'Rotation'))
link(get('ThrowS'), 'ThrowS', n['Xf1'], 'Location'); PL.set_pin_value(pin_in(n['Xf1'], 'Scale'), '3.000000,3.000000,3.000000')
PL.break_pin_links(BEL.find_then_pin(n['SetNext'])); PL.break_pin_links(BEL.find_then_pin(n['SetArmed1']))
sug = call(GS + 'SuggestProjectileVelocity_CustomArc', ArcParam=0.6); link(get('ThrowS'), 'ThrowS', sug, 'StartPos'); link(get('ThrowT'), 'ThrowT', sug, 'EndPos')
mv = get('Move', BLOB); link(n['Spawn1'], 'ReturnValue', mv, 'self')
vel = call('/Script/Engine.ProjectileMovementComponent:SetVelocityInLocalSpace'); link(mv, 'Move', vel, 'self'); link(sug, 'OutLaunchVelocity', vel, 'NewVelocity')
chain(ev_one, set_t, set_s, n['Spawn1']); chain(n['SetArmed1'], sug, vel)
# ---- ThrowBurst: 3 blobs, staggered like a retch, not a salvo
c1 = call(CLS + ':ThrowOne'); d1 = delay(0.16); c2 = call(CLS + ':ThrowOne'); d2 = delay(0.24); c3 = call(CLS + ':ThrowOne')
chain(ev_burst, c1, d1, c2, d2, c3)
# ---- Spit: SetNext -> (skip while the catapult runs) -> aim in front of the hero, head leans at the hero by IK, montage, blobs on the thrust
active = get('CatActive'); not_a = call(M + 'Not_PreBool'); link(active, 'CatActive', not_a, 'A'); br_spit = branch(not_a)
chain(n['SetNext'], br_spit)
cast1, set_m1 = resolve_mesh(); out_exec(br_spit, 'then', cast1)
pawn = call(GS + 'GetPlayerPawn'); ploc = call(AC + 'K2_GetActorLocation'); link(pawn, 'ReturnValue', ploc, 'self')
feet = call(M + 'Subtract_VectorVector', B='0.000000,0.000000,90.000000'); link(ploc, 'ReturnValue', feet, 'A')
pawn2 = call(GS + 'GetPlayerPawn'); pf = call(AC + 'GetActorForwardVector'); link(pawn2, 'ReturnValue', pf, 'self')
s1 = setv('AimCentre', feet); s2 = setv('AimFwd', pf); s3 = setv('AimCone', lit=60.0); s4 = setv('AimMin', lit=450.0); s5 = setv('AimMax', lit=1200.0)
hd = sock('seg_13'); to_h = vbin('Subtract_VectorVector', get('AimCentre'), hd, 'AimCentre')
aim_h = vbin('Add_VectorVector', sock('seg_13'), scale(norm(to_h), 2500.0))
s6 = setv('CatAim', sock('seg_13')); s7 = setv('CatAimGoal', aim_h); s8 = setv('CatAlphaGoal', lit=0.45); s9 = setv('CatSpeed', lit=5.0); s10 = setv('CatActive', lit='true')
m_sp = montage(AM_SPIT); d3 = delay(0.5); burst = call(CLS + ':ThrowBurst'); d4 = delay(0.9); s11 = setv('CatAlphaGoal', lit=0.0); s12 = setv('CatSpeed', lit=2.5); d5 = delay(1.5)
s13 = setv('CatAlpha', lit=0.0); d6 = delay(0.1); s14 = setv('CatActive', lit='false')
chain(set_m1, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, m_sp, d3, burst, d4, s11, s12, d5, s13, d6, s14)
# ---- Catapult: IsBall success -> cooldown -> a cannon to aim at -> load, whip, throw, settle. The 0.1 s Delay lets the #529 reaction start first, so this montage wins
now = call(GS + 'GetTimeSeconds'); gt = call(M + 'Greater_DoubleDouble'); link(now, 'ReturnValue', gt, 'A'); link(get('NextCatT'), 'NextCatT', gt, 'B')
not_c = call(M + 'Not_PreBool'); link(get('CatActive'), 'CatActive', not_c, 'A'); and1 = vbin('BooleanAND', gt, not_c); br_cat = branch(and1)
if not PL.try_create_connection(BEL.find_then_pin(n['IsBall']), BEL.find_execute_pin(br_cat)): raise SystemExit('SPIT533 IsBall.then link failed')
all_t = call(GS + 'GetAllActorsWithTag', Tag='Cannon'); arr = call('/Script/Engine.KismetArrayLibrary:Array_Random'); link(all_t, 'OutActors', arr, 'TargetArray')
iv = call(KS + 'IsValid'); link(arr, 'OutItem', iv, 'Object'); br_any = branch(iv); out_exec(br_cat, 'then', all_t); chain(all_t, br_any)
cloc = call(AC + 'K2_GetActorLocation'); link(arr, 'OutItem', cloc, 'self'); sA = setv('AimCentre', cloc)
now2 = call(GS + 'GetTimeSeconds'); nx = vbin('Add_DoubleDouble', now2, get('CatCooldown'), 'ReturnValue', 'CatCooldown'); sB = setv('NextCatT', nx)
out_exec(br_any, 'then', sA); chain(sA, sB)
d0 = delay(0.1); cast2, set_m2 = resolve_mesh(); chain(sB, d0, cast2)
def dying():
    p = pp(); c = call(AI + 'Montage_IsPlaying'); link(p, 'ReturnValue', c, 'self'); PL.set_pin_value(pin_in(c, 'Montage'), unreal.load_asset(AM_DIE).get_path_name())
    k = call(M + 'Not_PreBool'); link(c, 'ReturnValue', k, 'A'); return branch(k)
def lean(up, along):             # Base + Up * R * up + Dir * R * along, with Dir = flat direction to the target and R = 1.15 x base-to-head
    dv = vbin('Subtract_VectorVector', sock('seg_13'), sock('seg_00')); ln = call(M + 'VSize'); link(dv, 'ReturnValue', ln, 'A')
    r = call(M + 'Multiply_DoubleDouble', B=1.15); link(ln, 'ReturnValue', r, 'A')
    flat = call(M + 'ProjectVectorOnToPlane', PlaneNormal='0.000000,0.000000,1.000000'); link(vbin('Subtract_VectorVector', get('AimCentre'), sock('seg_00'), 'AimCentre'), 'ReturnValue', flat, 'V')
    ru = call(M + 'Multiply_DoubleDouble', B=up); link(r, 'ReturnValue', ru, 'A'); ra = call(M + 'Multiply_DoubleDouble', B=along); link(r, 'ReturnValue', ra, 'A')
    upv = call(M + 'Multiply_VectorFloat', A='0.000000,0.000000,1.000000'); link(ru, 'ReturnValue', upv, 'B')
    return vbin('Add_VectorVector', vbin('Add_VectorVector', sock('seg_00'), upv), scale(norm(flat), ra))
br_d1 = dying(); chain(set_m2, br_d1)
sC = setv('AimFwd', lit='1.000000,0.000000,0.000000'); sD = setv('AimCone', lit=180.0); sE = setv('AimMin', lit=400.0); sF = setv('AimMax', lit=2500.0)
sG = setv('CatAim', sock('seg_13')); sH = setv('CatAimGoal', lean(0.85, -0.5)); sI = setv('CatAlphaGoal', lit=0.85); sJ = setv('CatSpeed', lit=1.5); sK = setv('CatActive', lit='true')
m_c = montage(AM_CAT); d7 = delay(2.3); out_exec(br_d1, 'then', sC)
sL = setv('CatAimGoal', lean(0.55, 0.75)); sM = setv('CatAlphaGoal', lit=1.0); sN = setv('CatSpeed', lit=16.0); d8 = delay(0.2); br_d2 = dying()
burst2 = call(CLS + ':ThrowBurst'); d9 = delay(0.6); sO = setv('CatAlphaGoal', lit=0.0); sP = setv('CatSpeed', lit=1.2); d10 = delay(3.5); sQ = setv('CatAlpha', lit=0.0); d11 = delay(0.1); sR = setv('CatActive', lit='false')
chain(sC, sD, sE, sF, sG, sH, sI, sJ, sK, m_c, d7, sL, sM, sN, d8, br_d2); out_exec(br_d2, 'then', burst2); out_exec(br_d2, 'else', sO); chain(burst2, d9, sO, sP, d10, sQ, d11, sR)
# ---- Tick: while CatActive, ease the IK and feed the post-process ABP. A running strike (tag CannonStriker) wins.
PL.break_pin_links(BEL.find_then_pin(n['Tick']))
br_t = branch(get('CatActive'), 'CatActive'); chain(n['Tick'], br_t); out_exec(br_t, 'else', n['IfWobble'])
fi = call(M + 'FInterpTo'); link(get('CatAlpha'), 'CatAlpha', fi, 'Current'); link(get('CatAlphaGoal'), 'CatAlphaGoal', fi, 'Target'); link(n['Tick'], 'DeltaSeconds', fi, 'DeltaTime'); link(get('CatSpeed'), 'CatSpeed', fi, 'InterpSpeed')
vi = call(M + 'VInterpTo'); link(get('CatAim'), 'CatAim', vi, 'Current'); link(get('CatAimGoal'), 'CatAimGoal', vi, 'Target'); link(n['Tick'], 'DeltaSeconds', vi, 'DeltaTime'); link(get('CatSpeed'), 'CatSpeed', vi, 'InterpSpeed')
sT = setv('CatAlpha', fi); sU = setv('CatAim', vi); out_exec(br_t, 'then', sT); chain(sT, sU)
ow = call('/Script/Engine.ActorComponent:GetOwner'); tag = call(AC + 'ActorHasTag', Tag='CannonStriker'); link(ow, 'ReturnValue', tag, 'self')
br_s = branch(tag); chain(sU, br_s); out_exec(br_s, 'then', n['IfWobble'])
# the editor offers no cast to the ABP from Python, so the IK values are set by property name
p_t = pp(); iv_t = call(KS + 'IsValid'); link(p_t, 'ReturnValue', iv_t, 'Object'); br_p = branch(iv_t); out_exec(br_s, 'else', br_p); out_exec(br_p, 'else', n['IfWobble'])
sV = call(KS + 'SetVectorPropertyByName', PropertyName='StrikeTarget'); link(p_t, 'ReturnValue', sV, 'Object'); link(get('CatAim'), 'CatAim', sV, 'Value')
sW = call(KS + 'SetDoublePropertyByName', PropertyName='StrikeAlpha'); link(p_t, 'ReturnValue', sW, 'Object'); link(get('CatAlpha'), 'CatAlpha', sW, 'Value')
out_exec(br_p, 'then', sV); chain(sV, sW); chain(sW, n['IfWobble'])
ok = BEL.compile_blueprint(bp); say('compile', ok, 'errors before', base, 'after', errs())
if set(errs()) - set(base): raise SystemExit('SPIT533 NEW compile errors %s: NOT saved. Close without saving, tell i5' % sorted(set(errs()) - set(base)))
unreal.get_default_object(bp.generated_class()).set_editor_property('CatCooldown', 10.0)
say('saved', E.save_asset(PATH, only_if_is_dirty=False), 'new nodes', len([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]))
